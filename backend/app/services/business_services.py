"""
Serviços de regras de negócio da plataforma SaaS de Estacionamentos ALPR.
Implementa tarifação, permanência, validações multi-tenant, auditoria e bilhetagem.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from jose import JWTError

from app.core.security import (
    PASSWORD_RESET_PURPOSE,
    create_password_reset_token,
    decode_access_token,
    get_password_hash,
    password_fingerprint,
    verify_password,
)
from app.services.notification_service import send_password_reset_email
from app.models.entities import (
    Assinatura,
    AssinaturaStatus,
    AssinaturaVeiculo,
    Auditoria,
    Camera,
    CameraTipo,
    Cliente,
    Cobranca,
    CobrancaStatus,
    Estacionamento,
    EstacionamentoStatus,
    Movimentacao,
    MovimentacaoStatus,
    Pagamento,
    PagamentoMetodo,
    Plano,
    PlanoRecorrencia,
    Tarifa,
    TipoCobranca,
    Usuario,
    UsuarioPerfil,
    Veiculo,
    VeiculoTipo,
)
from app.schemas.schemas import (
    CameraCreate,
    CameraUpdate,
    ClienteCreate,
    EstacionamentoCreate,
    MovimentacaoCorrecaoManual,
    MovimentacaoEntrada,
    MovimentacaoSaida,
    PagamentoCreate,
    PlanoCreate,
    TarifaCreate,
    UsuarioCreate,
    VeiculoCreate,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Garante que o datetime possua fuso horário UTC consistente."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AuthService:
    """Gerenciamento de usuários, autenticação e senhas."""

    @staticmethod
    def authenticate_user(db: Session, email: str, senha: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.email == email.lower().strip())
        user = db.scalar(stmt)
        if not user or not user.ativo:
            return None
        if not verify_password(senha, user.senha_hash):
            return None
        return user

    @staticmethod
    def create_user(
        db: Session,
        user_in: UsuarioCreate,
        cliente_id: Optional[uuid.UUID] = None,
    ) -> Usuario:
        """Criação de baixo nível. A política de quem pode criar o quê fica em `register_user`."""
        email = user_in.email.lower().strip()
        if db.scalar(select(Usuario).where(Usuario.email == email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado na plataforma.",
            )

        if user_in.perfil in [UsuarioPerfil.ESTACIONAMENTO_ADMIN, UsuarioPerfil.CLIENTE]:
            if not user_in.estacionamento_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="estacionamento_id é obrigatório para este perfil.",
                )

        new_user = Usuario(
            nome=user_in.nome,
            email=email,
            senha_hash=get_password_hash(user_in.senha),
            perfil=user_in.perfil.value if isinstance(user_in.perfil, UsuarioPerfil) else user_in.perfil,
            estacionamento_id=user_in.estacionamento_id,
            cliente_id=cliente_id,
            ativo=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def register_user(db: Session, actor: Usuario, user_in: UsuarioCreate) -> Usuario:
        """
        Cadastro de usuários administrativos por um usuário autenticado:
        - SAAS_ADMIN cria SAAS_ADMIN ou ESTACIONAMENTO_ADMIN (de qualquer estacionamento existente).
        - ESTACIONAMENTO_ADMIN cria apenas ESTACIONAMENTO_ADMIN, sempre no próprio estacionamento.
        - Usuários CLIENTE só nascem via acesso ao portal (vinculados a um cliente).
        """
        if user_in.perfil == UsuarioPerfil.CLIENTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Acesso de cliente deve ser criado pelo cadastro do cliente (acesso ao portal).",
            )

        if actor.perfil == UsuarioPerfil.ESTACIONAMENTO_ADMIN.value:
            if user_in.perfil != UsuarioPerfil.ESTACIONAMENTO_ADMIN:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Perfil não permitido.")
            if user_in.estacionamento_id not in (None, actor.estacionamento_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Não é permitido criar usuários em outro estacionamento.",
                )
            user_in = user_in.model_copy(update={"estacionamento_id": actor.estacionamento_id})
        elif actor.perfil != UsuarioPerfil.SAAS_ADMIN.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado.")

        if user_in.estacionamento_id and not db.get(Estacionamento, user_in.estacionamento_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estacionamento não encontrado.")

        user = AuthService.create_user(db, user_in)
        AuditService.log(
            db,
            acao="CRIACAO_USUARIO",
            tabela="usuarios",
            registro_id=str(user.id),
            tenant_id=user.estacionamento_id,
            usuario_id=actor.id,
            dados_novos={"email": user.email, "perfil": user.perfil},
        )
        return user

    @staticmethod
    def request_password_reset(db: Session, email: str) -> None:
        """
        Gera e envia o token de redefinição. Não revela se o e-mail existe:
        quem chama deve responder sempre com a mesma mensagem.
        """
        user = db.scalar(select(Usuario).where(Usuario.email == email.lower().strip()))
        if not user or not user.ativo:
            return
        token = create_password_reset_token(user.id, user.senha_hash)
        send_password_reset_email(user.email, token)

    @staticmethod
    def reset_password(db: Session, token: str, nova_senha: str) -> None:
        """Valida o token (finalidade, expiração, uso único) e troca a senha."""
        invalid = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado.",
        )
        try:
            payload = decode_access_token(token)
            if payload.get("purpose") != PASSWORD_RESET_PURPOSE:
                raise invalid
            user = db.get(Usuario, uuid.UUID(payload["sub"]))
        except (JWTError, ValueError, KeyError):
            raise invalid

        if not user or not user.ativo or payload.get("pwd") != password_fingerprint(user.senha_hash):
            raise invalid

        user.senha_hash = get_password_hash(nova_senha)
        db.commit()
        AuditService.log(
            db,
            acao="REDEFINICAO_SENHA",
            tabela="usuarios",
            registro_id=str(user.id),
            tenant_id=user.estacionamento_id,
            usuario_id=user.id,
        )


class TenantService:
    """Gestão de estacionamentos (tenants)."""

    @staticmethod
    def create_parking(db: Session, tenant_in: EstacionamentoCreate) -> Estacionamento:
        stmt = select(Estacionamento).where(Estacionamento.cnpj == tenant_in.cnpj)
        if db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ já cadastrado para outro estacionamento.",
            )

        parking = Estacionamento(
            nome_fantasia=tenant_in.nome_fantasia,
            razao_social=tenant_in.razao_social,
            cnpj=tenant_in.cnpj,
            email_contato=tenant_in.email_contato,
            telefone=tenant_in.telefone,
            status=EstacionamentoStatus.ATIVO.value,
        )
        db.add(parking)
        db.commit()
        db.refresh(parking)
        return parking

    @staticmethod
    def list_parkings(db: Session, skip: int = 0, limit: int = 100) -> List[Estacionamento]:
        stmt = select(Estacionamento).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())


class CustomerVehicleService:
    """Regras de negócio para clientes e veículos."""

    @staticmethod
    def create_customer_with_vehicles(
        db: Session,
        tenant_id: uuid.UUID,
        customer_in: ClienteCreate,
    ) -> Cliente:
        # Regra 1: Cadastro inicial deve ter ao menos 1 veículo
        if not customer_in.veiculos_iniciais:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O cadastro inicial de um cliente deve incluir pelo menos um veículo.",
            )

        # Regra 2: Documento único por estacionamento
        doc_stmt = select(Cliente).where(
            Cliente.estacionamento_id == tenant_id,
            Cliente.documento == customer_in.documento.strip(),
        )
        if db.scalar(doc_stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cliente com este documento já cadastrado neste estacionamento.",
            )

        # Regra 3: Não permitir placas duplicadas ativas no mesmo estacionamento
        for v in customer_in.veiculos_iniciais:
            norm_plate = v.placa.strip().upper().replace("-", "")
            plate_stmt = select(Veiculo).where(
                Veiculo.estacionamento_id == tenant_id,
                Veiculo.placa == norm_plate,
                Veiculo.ativo == True,
            )
            if db.scalar(plate_stmt):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A placa {norm_plate} já está cadastrada e ativa neste estacionamento.",
                )

        # Geração automática de código único permanente
        codigo = customer_in.codigo
        if not codigo:
            total_clientes = db.scalar(select(func.count()).select_from(Cliente)) or 0
            seq = total_clientes + 1
            candidate = f"CLI-{seq:04d}"
            while db.scalar(select(Cliente.id).where(Cliente.codigo == candidate)):
                seq += 1
                candidate = f"CLI-{seq:04d}"
            codigo = candidate

        # Criação do cliente
        cliente = Cliente(
            codigo=codigo,
            estacionamento_id=tenant_id,
            nome=customer_in.nome.strip(),
            documento=customer_in.documento.strip(),
            tipo_documento=customer_in.tipo_documento.value if hasattr(customer_in.tipo_documento, "value") else str(customer_in.tipo_documento),
            telefone=customer_in.telefone.strip() if customer_in.telefone else None,
            email=str(customer_in.email).strip().lower() if customer_in.email else None,
            plano_tipo=customer_in.plano_tipo.strip().lower(),
        )
        db.add(cliente)
        db.flush()

        # Criação dos veículos associados
        for v in customer_in.veiculos_iniciais:
            norm_plate = v.placa.strip().upper().replace("-", "")
            veiculo = Veiculo(
                cliente_id=cliente.id,
                estacionamento_id=tenant_id,
                placa=norm_plate,
                marca=v.marca,
                modelo=v.modelo,
                cor=v.cor,
                tipo=v.tipo.value if isinstance(v.tipo, VeiculoTipo) else v.tipo,
                ativo=True,
            )
            db.add(veiculo)

        db.commit()
        db.refresh(cliente)
        return cliente

    @staticmethod
    def add_vehicle(
        db: Session,
        tenant_id: uuid.UUID,
        cliente_id: uuid.UUID,
        vehicle_in: VeiculoCreate,
    ) -> Veiculo:
        # Validação do cliente pertencer ao tenant
        client_stmt = select(Cliente).where(Cliente.id == cliente_id, Cliente.estacionamento_id == tenant_id)
        if not db.scalar(client_stmt):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

        norm_plate = vehicle_in.placa.strip().upper().replace("-", "")
        # Valida unicidade de placa ativa no tenant
        plate_stmt = select(Veiculo).where(
            Veiculo.estacionamento_id == tenant_id,
            Veiculo.placa == norm_plate,
            Veiculo.ativo == True,
        )
        if db.scalar(plate_stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Placa {norm_plate} já cadastrada neste estacionamento.",
            )

        veiculo = Veiculo(
            cliente_id=cliente_id,
            estacionamento_id=tenant_id,
            placa=norm_plate,
            marca=vehicle_in.marca,
            modelo=vehicle_in.modelo,
            cor=vehicle_in.cor,
            tipo=vehicle_in.tipo.value,
            ativo=True,
        )
        db.add(veiculo)
        db.commit()
        db.refresh(veiculo)
        return veiculo

    @staticmethod
    def get_customer_movements(
        db: Session,
        tenant_id: uuid.UUID,
        cliente_id: uuid.UUID,
        placa: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        client_stmt = select(Cliente).where(Cliente.id == cliente_id, Cliente.estacionamento_id == tenant_id)
        cliente = db.scalar(client_stmt)
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

        # Veículos do cliente
        veiculos_stmt = select(Veiculo).where(Veiculo.cliente_id == cliente_id, Veiculo.estacionamento_id == tenant_id)
        veiculos = list(db.scalars(veiculos_stmt).all())
        v_ids = [v.id for v in veiculos]
        v_placas = [v.placa for v in veiculos]

        if not v_ids and not v_placas:
            return []

        conds = [
            Movimentacao.estacionamento_id == tenant_id,
            or_(Movimentacao.veiculo_id.in_(v_ids), Movimentacao.placa.in_(v_placas)),
        ]

        if placa and placa.strip():
            norm_p = placa.strip().upper().replace("-", "")
            conds.append(Movimentacao.placa == norm_p)

        if data_inicio:
            conds.append(Movimentacao.entrada_em >= data_inicio)

        if data_fim:
            conds.append(Movimentacao.entrada_em <= data_fim)

        mov_stmt = (
            select(Movimentacao)
            .options(selectinload(Movimentacao.cobranca))
            .where(and_(*conds))
            .order_by(Movimentacao.entrada_em.desc())
        )
        movements = list(db.scalars(mov_stmt).all())

        results = []
        for m in movements:
            esta_estacionado = (m.saida_em is None and m.status in (MovimentacaoStatus.ABERTA.value, MovimentacaoStatus.INCONSISTENTE.value))
            valor = None
            if m.cobranca:
                valor = m.cobranca.valor_liquido
            elif esta_estacionado:
                try:
                    res_charge = TariffPlanService.calculate_stay_charge(
                        db=db,
                        tenant_id=tenant_id,
                        entrada_em=m.entrada_em,
                        saida_em=utc_now(),
                        placa=m.placa,
                    )
                    valor = res_charge.get("valor_final")
                except Exception:
                    valor = None

            results.append({
                "id": m.id,
                "placa": m.placa,
                "entrada_em": m.entrada_em,
                "saida_em": m.saida_em,
                "permanencia_minutos": m.permanencia_minutos,
                "status": m.status,
                "tipo_cobranca": m.tipo_cobranca,
                "valor_calculado": valor,
                "esta_estacionado": esta_estacionado,
            })
        return results


class TariffPlanService:
    """Configuração de planos, assinaturas e tarifação avulsa."""

    @staticmethod
    def create_tariff(db: Session, tenant_id: uuid.UUID, tariff_in: TarifaCreate) -> Tarifa:
        tarifa = Tarifa(
            estacionamento_id=tenant_id,
            descricao=tariff_in.descricao,
            valor_primeira_hora=tariff_in.valor_primeira_hora,
            valor_hora_adicional=tariff_in.valor_hora_adicional,
            valor_diaria=tariff_in.valor_diaria,
            tolerancia_minutos=tariff_in.tolerancia_minutos,
            vigente_desde=utc_now(),
        )
        db.add(tarifa)
        db.commit()
        db.refresh(tarifa)
        return tarifa

    @staticmethod
    def get_active_tariff(db: Session, tenant_id: uuid.UUID) -> Tarifa:
        stmt = (
            select(Tarifa)
            .where(
                Tarifa.estacionamento_id == tenant_id,
                or_(Tarifa.vigente_ate == None, Tarifa.vigente_ate > utc_now()),
            )
            .order_by(Tarifa.vigente_desde.desc())
        )
        tarifa = db.scalar(stmt)
        if not tarifa:
            # Tarifa padrão se não houver configurada
            tarifa = Tarifa(
                estacionamento_id=tenant_id,
                descricao="Tarifa Padrão Inicial",
                valor_primeira_hora=Decimal("15.00"),
                valor_hora_adicional=Decimal("5.00"),
                valor_diaria=Decimal("50.00"),
                tolerancia_minutos=15,
                vigente_desde=utc_now(),
            )
            db.add(tarifa)
            db.commit()
            db.refresh(tarifa)
        return tarifa

    @staticmethod
    def create_plan(db: Session, tenant_id: uuid.UUID, plan_in: PlanoCreate) -> Plano:
        plano = Plano(
            estacionamento_id=tenant_id,
            nome=plan_in.nome,
            descricao=plan_in.descricao,
            tipo_recorrencia=plan_in.tipo_recorrencia.value,
            valor_base=plan_in.valor_base,
            limite_veiculos=plan_in.limite_veiculos,
            valor_veiculo_adicional=plan_in.valor_veiculo_adicional,
            ativo=True,
        )
        db.add(plano)
        db.commit()
        db.refresh(plano)
        return plano


class MovementService:
    """Controle de entradas, saídas, permanência e bilhetagem."""

    @staticmethod
    def register_entry(
        db: Session,
        tenant_id: uuid.UUID,
        entry_in: MovimentacaoEntrada,
    ) -> Movimentacao:
        norm_plate = entry_in.placa.strip().upper().replace("-", "")

        # 1. Regra: Não permitir 2 permanências abertas para a mesma placa no mesmo estacionamento
        open_stmt = select(Movimentacao).where(
            Movimentacao.estacionamento_id == tenant_id,
            Movimentacao.placa == norm_plate,
            Movimentacao.status == MovimentacaoStatus.ABERTA.value,
        )
        existing_open = db.scalar(open_stmt)
        if existing_open:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Veículo com placa {norm_plate} já possui permanência aberta neste estacionamento.",
            )

        # 2. Localiza veículo cadastrado e verifica assinatura ativa
        veiculo_stmt = select(Veiculo).where(
            Veiculo.estacionamento_id == tenant_id,
            Veiculo.placa == norm_plate,
            Veiculo.ativo == True,
        )
        veiculo = db.scalar(veiculo_stmt)

        tipo_cobranca = TipoCobranca.AVULSA.value
        if veiculo:
            # Verifica se está vinculado a uma assinatura ativa válida hoje
            hoje = date.today()
            sub_stmt = (
                select(Assinatura)
                .join(AssinaturaVeiculo, AssinaturaVeiculo.assinatura_id == Assinatura.id)
                .where(
                    AssinaturaVeiculo.veiculo_id == veiculo.id,
                    Assinatura.estacionamento_id == tenant_id,
                    Assinatura.status == AssinaturaStatus.ATIVA.value,
                    Assinatura.data_inicio <= hoje,
                    Assinatura.data_fim >= hoje,
                )
            )
            active_sub = db.scalar(sub_stmt)
            if active_sub:
                tipo_cobranca = TipoCobranca.PLANO.value

        entry_time = ensure_utc(entry_in.timestamp) if entry_in.timestamp else utc_now()

        movimentacao = Movimentacao(
            estacionamento_id=tenant_id,
            veiculo_id=veiculo.id if veiculo else None,
            placa=norm_plate,
            camera_entrada_id=entry_in.camera_id,
            entrada_em=entry_time,
            status=MovimentacaoStatus.ABERTA.value,
            tipo_cobranca=tipo_cobranca,
        )
        db.add(movimentacao)
        db.commit()
        db.refresh(movimentacao)
        return movimentacao

    @staticmethod
    def register_exit(
        db: Session,
        tenant_id: uuid.UUID,
        exit_in: MovimentacaoSaida,
    ) -> Tuple[Movimentacao, Cobranca]:
        norm_plate = exit_in.placa.strip().upper().replace("-", "")
        exit_time = ensure_utc(exit_in.timestamp) if exit_in.timestamp else utc_now()

        # 1. Localiza permanência aberta
        open_stmt = select(Movimentacao).where(
            Movimentacao.estacionamento_id == tenant_id,
            Movimentacao.placa == norm_plate,
            Movimentacao.status == MovimentacaoStatus.ABERTA.value,
        )
        mov = db.scalar(open_stmt)

        # 2. Quando não houver entrada correspondente, registra inconsistência
        if not mov:
            inconsistente = Movimentacao(
                estacionamento_id=tenant_id,
                placa=norm_plate,
                camera_saida_id=exit_in.camera_id,
                entrada_em=exit_time,
                saida_em=exit_time,
                permanencia_minutos=0,
                status=MovimentacaoStatus.INCONSISTENTE.value,
                observacao="Saída detectada sem registro prévio de entrada aberta.",
            )
            db.add(inconsistente)
            db.commit()
            db.refresh(inconsistente)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhuma entrada aberta localizada para a placa {norm_plate}. Inconsistência registrada.",
            )

        # 3. Calcula tempo de permanência em minutos
        entrada_em = ensure_utc(mov.entrada_em) or exit_time
        if exit_time < entrada_em:
            exit_time = entrada_em

        delta = exit_time - entrada_em
        permanencia_min = max(0, int(delta.total_seconds() // 60))
        mov.saida_em = exit_time
        mov.permanencia_minutos = permanencia_min
        mov.camera_saida_id = exit_in.camera_id
        mov.status = MovimentacaoStatus.CONCLUIDA.value

        # 4. Cálculo de cobrança conforme tipo
        valor_devido = Decimal("0.00")

        if mov.tipo_cobranca == TipoCobranca.PLANO.value:
            # Isento na cancela pois já é mensalista
            valor_devido = Decimal("0.00")
        else:
            # Cobrança avulsa baseada em tarifa
            tarifa = TariffPlanService.get_active_tariff(db, tenant_id)

            if permanencia_min <= tarifa.tolerancia_minutos:
                valor_devido = Decimal("0.00")
            elif permanencia_min <= 60:
                valor_devido = tarifa.valor_primeira_hora
            elif permanencia_min >= 720:  # Acima de 12 horas aplica diária
                diarias = max(1, math.ceil(permanencia_min / (24 * 60)))
                valor_devido = Decimal(str(diarias)) * tarifa.valor_diaria
            else:
                horas_adicionais = math.ceil((permanencia_min - 60) / 60)
                calculado = tarifa.valor_primeira_hora + (Decimal(str(horas_adicionais)) * tarifa.valor_hora_adicional)
                # Teto na diária
                valor_devido = min(calculado, tarifa.valor_diaria)

        # 5. Determina o cliente se o veículo estiver cadastrado
        cliente_id = None
        if mov.veiculo_id:
            veic = db.scalar(select(Veiculo).where(Veiculo.id == mov.veiculo_id))
            if veic:
                cliente_id = veic.cliente_id

        # 6. Gera registro de cobrança
        cobranca = Cobranca(
            estacionamento_id=tenant_id,
            movimentacao_id=mov.id,
            cliente_id=cliente_id,
            valor_bruto=valor_devido,
            desconto=Decimal("0.00"),
            valor_liquido=valor_devido,
            status=CobrancaStatus.PAGO.value if valor_devido == Decimal("0.00") else CobrancaStatus.PENDENTE.value,
            data_vencimento=date.today(),
        )
        db.add(cobranca)
        db.commit()
        db.refresh(mov)
        db.refresh(cobranca)

        return mov, cobranca

    @staticmethod
    def manual_correction(
        db: Session,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        movimentacao_id: uuid.UUID,
        correction: MovimentacaoCorrecaoManual,
        ip_origem: Optional[str] = None,
    ) -> Movimentacao:
        stmt = select(Movimentacao).where(
            Movimentacao.id == movimentacao_id,
            Movimentacao.estacionamento_id == tenant_id,
        )
        mov = db.scalar(stmt)
        if not mov:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimentação não encontrada.")

        dados_anteriores = {
            "placa": mov.placa,
            "status": mov.status,
            "observacao": mov.observacao,
        }

        if correction.placa:
            mov.placa = correction.placa.strip().upper().replace("-", "")
        if correction.status:
            mov.status = correction.status.value
        mov.observacao = f"[CORREÇÃO MANUAL]: {correction.observacao}"

        dados_novos = {
            "placa": mov.placa,
            "status": mov.status,
            "observacao": mov.observacao,
        }

        # Registro obrigatório de auditoria
        audit = Auditoria(
            estacionamento_id=tenant_id,
            usuario_id=user_id,
            acao="CORRECAO_MANUAL_MOVIMENTACAO",
            tabela="movimentacoes",
            registro_id=str(mov.id),
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip_origem=ip_origem,
        )
        db.add(audit)
        db.commit()
        db.refresh(mov)
        return mov


class BillingPaymentService:
    """Gestão de pagamentos e liquidação de cobranças."""

    @staticmethod
    def register_payment(
        db: Session,
        tenant_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        payment_in: PagamentoCreate,
    ) -> Pagamento:
        stmt = select(Cobranca).where(
            Cobranca.id == payment_in.cobranca_id,
            Cobranca.estacionamento_id == tenant_id,
        )
        cobranca = db.scalar(stmt)
        if not cobranca:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cobrança não encontrada.")

        if cobranca.status == CobrancaStatus.PAGO.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cobrança já se encontra liquidada.")

        pagamento = Pagamento(
            cobranca_id=cobranca.id,
            estacionamento_id=tenant_id,
            valor_pago=payment_in.valor_pago,
            metodo=payment_in.metodo.value if isinstance(payment_in.metodo, PagamentoMetodo) else payment_in.metodo,
            pago_em=utc_now(),
            registrado_por_usuario_id=user_id,
            comprovante_transacao=payment_in.comprovante_transacao,
        )
        db.add(pagamento)

        # Se valor pago cobre o líquido, marca como paga
        if payment_in.valor_pago >= cobranca.valor_liquido:
            cobranca.status = CobrancaStatus.PAGO.value

        db.commit()
        db.refresh(pagamento)
        return pagamento


class DashboardService:
    """Agregação de indicadores executivos em tempo real para o estacionamento."""

    @staticmethod
    def get_metrics(db: Session, tenant_id: uuid.UUID) -> Dict[str, Any]:
        hoje_inicio = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        bind = db.get_bind()
        if bind and bind.dialect.name == "sqlite":
            hoje_inicio = hoje_inicio.replace(tzinfo=None)

        # Veículos atualmente no estacionamento
        veiculos_estacionados = db.scalar(
            select(func.count(Movimentacao.id)).where(
                Movimentacao.estacionamento_id == tenant_id,
                Movimentacao.status == MovimentacaoStatus.ABERTA.value,
            )
        ) or 0

        # Entradas do dia
        entradas_hoje = db.scalar(
            select(func.count(Movimentacao.id)).where(
                Movimentacao.estacionamento_id == tenant_id,
                Movimentacao.entrada_em >= hoje_inicio,
            )
        ) or 0

        # Saídas do dia
        saidas_hoje = db.scalar(
            select(func.count(Movimentacao.id)).where(
                Movimentacao.estacionamento_id == tenant_id,
                Movimentacao.saida_em >= hoje_inicio,
            )
        ) or 0

        # Clientes cadastrados
        clientes_total = db.scalar(
            select(func.count(Cliente.id)).where(Cliente.estacionamento_id == tenant_id)
        ) or 0

        # Veículos cadastrados
        veiculos_total = db.scalar(
            select(func.count(Veiculo.id)).where(Veiculo.estacionamento_id == tenant_id)
        ) or 0

        # Assinaturas ativas
        hoje_data = date.today()
        assinaturas_ativas = db.scalar(
            select(func.count(Assinatura.id)).where(
                Assinatura.estacionamento_id == tenant_id,
                Assinatura.status == AssinaturaStatus.ATIVA.value,
                Assinatura.data_fim >= hoje_data,
            )
        ) or 0

        # Receita total de pagamentos realizados
        receita_total = db.scalar(
            select(func.coalesce(func.sum(Pagamento.valor_pago), Decimal("0.00"))).where(
                Pagamento.estacionamento_id == tenant_id
            )
        ) or Decimal("0.00")

        # Cobranças pendentes
        cobrancas_pendentes = db.scalars(
            select(Cobranca).where(
                Cobranca.estacionamento_id == tenant_id,
                Cobranca.status == CobrancaStatus.PENDENTE.value,
            )
        ).all()

        pendentes_valor = sum((c.valor_liquido for c in cobrancas_pendentes), Decimal("0.00"))
        pendentes_qtd = len(cobrancas_pendentes)

        # Movimentações mais recentes (últimas 10)
        recentes_stmt = (
            select(Movimentacao)
            .where(Movimentacao.estacionamento_id == tenant_id)
            .order_by(Movimentacao.entrada_em.desc())
            .limit(10)
        )
        movimentacoes_recentes = list(db.scalars(recentes_stmt).all())

        return {
            "veiculos_estacionados_agora": veiculos_estacionados,
            "entradas_hoje": entradas_hoje,
            "saidas_hoje": saidas_hoje,
            "clientes_cadastrados": clientes_total,
            "veiculos_cadastrados": veiculos_total,
            "assinaturas_ativas": assinaturas_ativas,
            "receita_total_registrada": receita_total,
            "cobrancas_pendentes_valor": pendentes_valor,
            "cobrancas_pendentes_quantidade": pendentes_qtd,
            "movimentacoes_recentes": movimentacoes_recentes,
        }


class AuditService:
    """Utilitário centralizado para registro na trilha de auditoria."""

    @staticmethod
    def log(
        db: Session,
        acao: str,
        tabela: str,
        registro_id: str,
        tenant_id: Optional[uuid.UUID] = None,
        usuario_id: Optional[uuid.UUID] = None,
        dados_anteriores: Optional[Dict[str, Any]] = None,
        dados_novos: Optional[Dict[str, Any]] = None,
        ip_origem: Optional[str] = None,
    ) -> Auditoria:
        audit = Auditoria(
            estacionamento_id=tenant_id,
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip_origem=ip_origem,
        )
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit


class CameraService:
    """Gestão de Câmeras para leitura de placas e monitoramento de cancelas."""

    @staticmethod
    def create_camera(
        db: Session,
        tenant_id: uuid.UUID,
        camera_in: CameraCreate,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> Camera:
        # Validação: identificador único por estacionamento
        stmt = select(Camera).where(
            Camera.estacionamento_id == tenant_id,
            Camera.identificador == camera_in.identificador,
        )
        if db.scalar(stmt):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma câmera com o identificador '{camera_in.identificador}' neste estacionamento.",
            )

        camera = Camera(
            estacionamento_id=tenant_id,
            identificador=camera_in.identificador,
            tipo=camera_in.tipo.value if isinstance(camera_in.tipo, CameraTipo) else camera_in.tipo,
            rtsp_url=camera_in.rtsp_url,
            localizacao=camera_in.localizacao,
            ativa=camera_in.ativa,
        )
        db.add(camera)
        db.commit()
        db.refresh(camera)

        AuditService.log(
            db,
            acao="CRIACAO_CAMERA",
            tabela="cameras",
            registro_id=str(camera.id),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            dados_novos={
                "identificador": camera.identificador,
                "tipo": camera.tipo,
                "localizacao": camera.localizacao,
            },
        )
        return camera

    @staticmethod
    def list_cameras(
        db: Session,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Camera]:
        stmt = (
            select(Camera)
            .where(Camera.estacionamento_id == tenant_id)
            .order_by(Camera.identificador.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_camera(
        db: Session,
        tenant_id: uuid.UUID,
        camera_id: uuid.UUID,
    ) -> Camera:
        stmt = select(Camera).where(
            Camera.id == camera_id,
            Camera.estacionamento_id == tenant_id,
        )
        cam = db.scalar(stmt)
        if not cam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Câmera não encontrada para este estacionamento.",
            )
        return cam

    @staticmethod
    def update_camera(
        db: Session,
        tenant_id: uuid.UUID,
        camera_id: uuid.UUID,
        camera_in: CameraUpdate,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> Camera:
        camera = CameraService.get_camera(db, tenant_id, camera_id)
        antigos = {
            "identificador": camera.identificador,
            "tipo": camera.tipo,
            "localizacao": camera.localizacao,
            "ativa": camera.ativa,
        }

        if camera_in.identificador is not None:
            camera.identificador = camera_in.identificador
        if camera_in.tipo is not None:
            camera.tipo = camera_in.tipo.value if isinstance(camera_in.tipo, CameraTipo) else camera_in.tipo
        if camera_in.rtsp_url is not None:
            camera.rtsp_url = camera_in.rtsp_url
        if camera_in.localizacao is not None:
            camera.localizacao = camera_in.localizacao
        if camera_in.ativa is not None:
            camera.ativa = camera_in.ativa

        db.commit()
        db.refresh(camera)

        AuditService.log(
            db,
            acao="ATUALIZACAO_CAMERA",
            tabela="cameras",
            registro_id=str(camera.id),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            dados_anteriores=antigos,
            dados_novos={
                "identificador": camera.identificador,
                "tipo": camera.tipo,
                "localizacao": camera.localizacao,
                "ativa": camera.ativa,
            },
        )
        return camera

    @staticmethod
    def delete_camera(
        db: Session,
        tenant_id: uuid.UUID,
        camera_id: uuid.UUID,
        usuario_id: Optional[uuid.UUID] = None,
    ) -> None:
        camera = CameraService.get_camera(db, tenant_id, camera_id)
        db.delete(camera)
        db.commit()

        AuditService.log(
            db,
            acao="EXCLUSAO_CAMERA",
            tabela="cameras",
            registro_id=str(camera_id),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
        )


