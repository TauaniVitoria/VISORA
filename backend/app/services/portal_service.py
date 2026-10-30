"""
Serviço do Portal do Cliente.

Todas as consultas recebem o `Cliente` já resolvido a partir do usuário autenticado
(ver `deps.get_current_cliente`) e filtram SEMPRE por estacionamento_id + dados do próprio
cliente. Nenhum identificador de cliente ou tenant é aceito vindo do request.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import (
    Assinatura,
    AssinaturaStatus,
    Cliente,
    Cobranca,
    CobrancaStatus,
    Estacionamento,
    Movimentacao,
    MovimentacaoStatus,
    Pagamento,
    Plano,
    Usuario,
    UsuarioPerfil,
)
from app.schemas.schemas import (
    PortalAccessCreate,
    PortalAssinaturaOut,
    PortalMovimentacaoOut,
    PortalPerfilOut,
    PortalResumoOut,
    UsuarioCreate,
)
from app.services.business_services import AuditService, AuthService, ensure_utc


def mask_document(documento: str) -> str:
    """Minimização de dados (LGPD): mantém só os 4 últimos caracteres do documento."""
    if len(documento) <= 4:
        return "*" * len(documento)
    return "*" * (len(documento) - 4) + documento[-4:]


class PortalAccessService:
    """Administração do acesso ao portal pelo administrador do estacionamento."""

    @staticmethod
    def _get_cliente(db: Session, tenant_id: uuid.UUID, client_id: uuid.UUID) -> Cliente:
        cliente = db.scalar(
            select(Cliente).where(Cliente.id == client_id, Cliente.estacionamento_id == tenant_id)
        )
        if not cliente:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")
        return cliente

    @staticmethod
    def create_access(
        db: Session,
        tenant_id: uuid.UUID,
        client_id: uuid.UUID,
        access_in: PortalAccessCreate,
        actor_id: Optional[uuid.UUID] = None,
    ) -> Usuario:
        cliente = PortalAccessService._get_cliente(db, tenant_id, client_id)
        if cliente.usuario is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este cliente já possui acesso ao portal.",
            )

        user = AuthService.create_user(
            db,
            UsuarioCreate(
                nome=cliente.nome,
                email=access_in.email,
                senha=access_in.senha,
                perfil=UsuarioPerfil.CLIENTE,
                estacionamento_id=tenant_id,
            ),
            cliente_id=cliente.id,
        )
        AuditService.log(
            db,
            acao="CRIACAO_ACESSO_PORTAL",
            tabela="usuarios",
            registro_id=str(user.id),
            tenant_id=tenant_id,
            usuario_id=actor_id,
            dados_novos={"cliente_id": str(cliente.id), "email": user.email},
        )
        return user

    @staticmethod
    def revoke_access(
        db: Session,
        tenant_id: uuid.UUID,
        client_id: uuid.UUID,
        actor_id: Optional[uuid.UUID] = None,
    ) -> None:
        cliente = PortalAccessService._get_cliente(db, tenant_id, client_id)
        user = cliente.usuario
        if user is None or not user.ativo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acesso ao portal não encontrado.")
        user.ativo = False
        db.commit()
        AuditService.log(
            db,
            acao="REVOGACAO_ACESSO_PORTAL",
            tabela="usuarios",
            registro_id=str(user.id),
            tenant_id=tenant_id,
            usuario_id=actor_id,
            dados_anteriores={"ativo": True},
            dados_novos={"ativo": False},
        )


class PortalService:
    """Consultas somente leitura do cliente autenticado."""

    @staticmethod
    def _movement_filter(cliente: Cliente):
        vehicle_ids = [v.id for v in cliente.veiculos]
        plates = [v.placa for v in cliente.veiculos]
        conditions = []
        if vehicle_ids:
            conditions.append(Movimentacao.veiculo_id.in_(vehicle_ids))
        if plates:
            conditions.append(Movimentacao.placa.in_(plates))
        if not conditions:
            return None
        return (Movimentacao.estacionamento_id == cliente.estacionamento_id) & or_(*conditions)

    @staticmethod
    def _to_movement_out(mov: Movimentacao, now: datetime) -> PortalMovimentacaoOut:
        em_andamento = mov.status == MovimentacaoStatus.ABERTA.value
        permanencia = mov.permanencia_minutos
        if em_andamento:
            entrada = ensure_utc(mov.entrada_em)
            permanencia = max(0, int((now - entrada).total_seconds() // 60)) if entrada else None
        return PortalMovimentacaoOut(
            id=mov.id,
            placa=mov.placa,
            entrada_em=mov.entrada_em,
            saida_em=mov.saida_em,
            permanencia_minutos=permanencia,
            em_andamento=em_andamento,
            status=mov.status,
            tipo_cobranca=mov.tipo_cobranca,
            cobranca=mov.cobranca,
        )

    @staticmethod
    def get_profile(db: Session, cliente: Cliente) -> PortalPerfilOut:
        parking = db.get(Estacionamento, cliente.estacionamento_id)
        return PortalPerfilOut(
            nome=cliente.nome,
            documento_mascarado=mask_document(cliente.documento),
            tipo_documento=cliente.tipo_documento,
            telefone=cliente.telefone,
            email=cliente.email,
            estacionamento=parking.nome_fantasia if parking else "",
            veiculos=list(cliente.veiculos),
        )

    @staticmethod
    def list_movements(
        db: Session,
        cliente: Cliente,
        skip: int = 0,
        limit: int = 50,
    ) -> List[PortalMovimentacaoOut]:
        condition = PortalService._movement_filter(cliente)
        if condition is None:
            return []
        movs = db.scalars(
            select(Movimentacao)
            .options(selectinload(Movimentacao.cobranca))
            .where(condition)
            .order_by(Movimentacao.entrada_em.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        now = datetime.now().astimezone()
        return [PortalService._to_movement_out(m, now) for m in movs]

    @staticmethod
    def list_subscriptions(db: Session, cliente: Cliente) -> List[PortalAssinaturaOut]:
        subs = db.scalars(
            select(Assinatura)
            .options(selectinload(Assinatura.veiculos_vinculados), selectinload(Assinatura.plano))
            .where(
                Assinatura.cliente_id == cliente.id,
                Assinatura.estacionamento_id == cliente.estacionamento_id,
            )
            .order_by(Assinatura.data_inicio.desc())
        ).all()
        plates_by_vehicle = {v.id: v.placa for v in cliente.veiculos}
        return [
            PortalAssinaturaOut(
                id=s.id,
                plano_id=s.plano_id,
                plano_nome=s.plano.nome,
                tipo_recorrencia=s.plano.tipo_recorrencia,
                data_inicio=s.data_inicio,
                data_fim=s.data_fim,
                status=s.status,
                valor_total=s.valor_total,
                placas=[
                    plates_by_vehicle[av.veiculo_id]
                    for av in s.veiculos_vinculados
                    if av.veiculo_id in plates_by_vehicle
                ],
            )
            for s in subs
        ]

    @staticmethod
    def list_plans(db: Session, cliente: Cliente) -> List[Plano]:
        return list(
            db.scalars(
                select(Plano).where(
                    Plano.estacionamento_id == cliente.estacionamento_id,
                    Plano.ativo == True,  # noqa: E712
                )
            ).all()
        )

    @staticmethod
    def _charge_filter(cliente: Cliente):
        sub_ids = select(Assinatura.id).where(
            Assinatura.cliente_id == cliente.id,
            Assinatura.estacionamento_id == cliente.estacionamento_id,
        )
        conditions = [Cobranca.cliente_id == cliente.id, Cobranca.assinatura_id.in_(sub_ids)]
        mov_condition = PortalService._movement_filter(cliente)
        if mov_condition is not None:
            conditions.append(Cobranca.movimentacao_id.in_(select(Movimentacao.id).where(mov_condition)))
        return (Cobranca.estacionamento_id == cliente.estacionamento_id) & or_(*conditions)

    @staticmethod
    def list_charges(
        db: Session,
        cliente: Cliente,
        status_filter: Optional[CobrancaStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Cobranca]:
        stmt = select(Cobranca).where(PortalService._charge_filter(cliente))
        if status_filter:
            stmt = stmt.where(Cobranca.status == status_filter.value)
        stmt = stmt.order_by(Cobranca.criado_em.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    @staticmethod
    def list_payments(db: Session, cliente: Cliente, skip: int = 0, limit: int = 50) -> List[Pagamento]:
        charge_ids = select(Cobranca.id).where(PortalService._charge_filter(cliente))
        return list(
            db.scalars(
                select(Pagamento)
                .where(
                    Pagamento.estacionamento_id == cliente.estacionamento_id,
                    Pagamento.cobranca_id.in_(charge_ids),
                )
                .order_by(Pagamento.pago_em.desc())
                .offset(skip)
                .limit(limit)
            ).all()
        )

    @staticmethod
    def get_summary(db: Session, cliente: Cliente) -> PortalResumoOut:
        now = datetime.now().astimezone()
        condition = PortalService._movement_filter(cliente)
        parked: List[PortalMovimentacaoOut] = []
        if condition is not None:
            open_movs = db.scalars(
                select(Movimentacao)
                .where(condition, Movimentacao.status == MovimentacaoStatus.ABERTA.value)
                .order_by(Movimentacao.entrada_em.desc())
            ).all()
            parked = [PortalService._to_movement_out(m, now) for m in open_movs]

        today = now.date()
        active_subs = db.scalars(
            select(Assinatura).where(
                Assinatura.cliente_id == cliente.id,
                Assinatura.estacionamento_id == cliente.estacionamento_id,
                Assinatura.status == AssinaturaStatus.ATIVA.value,
                Assinatura.data_fim >= today,
            )
        ).all()

        pending = db.scalars(
            select(Cobranca).where(
                PortalService._charge_filter(cliente),
                Cobranca.status == CobrancaStatus.PENDENTE.value,
            )
        ).all()

        return PortalResumoOut(
            veiculos_cadastrados=len(cliente.veiculos),
            veiculos_estacionados=parked,
            assinaturas_ativas=len(active_subs),
            cobrancas_pendentes_quantidade=len(pending),
            cobrancas_pendentes_valor=sum((c.valor_liquido for c in pending), Decimal("0.00")),
        )
