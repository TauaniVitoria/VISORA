"""
Modelos ORM de entidades do banco de dados (SQLAlchemy 2.0).
Implementa todas as 13 entidades do modelo SaaS multi-tenant com integridade referencial.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID, JSONType


def utc_now() -> datetime:
    """Retorna timestamp UTC atual consciente de fuso horário."""
    return datetime.now(timezone.utc)


class EstacionamentoStatus(str, Enum):
    ATIVO = "ativo"
    INATIVO = "inativo"
    BLOQUEADO = "bloqueado"


class UsuarioPerfil(str, Enum):
    SAAS_ADMIN = "SAAS_ADMIN"
    ESTACIONAMENTO_ADMIN = "ESTACIONAMENTO_ADMIN"
    CLIENTE = "CLIENTE"


class DocumentoTipo(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class VeiculoTipo(str, Enum):
    CARRO = "carro"
    MOTO = "moto"
    CAMINHAO = "caminhao"
    ONIBUS = "onibus"


class PlanoRecorrencia(str, Enum):
    MENSAL = "mensal"
    ANUAL = "anual"


class AssinaturaStatus(str, Enum):
    ATIVA = "ativa"
    CANCELADA = "cancelada"
    SUSPENSA = "suspensa"
    VENCIDA = "vencida"


class CameraTipo(str, Enum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AMBOS = "ambos"


class MovimentacaoStatus(str, Enum):
    ABERTA = "aberta"
    CONCLUIDA = "concluida"
    INCONSISTENTE = "inconsistente"
    CANCELADA = "cancelada"


class TipoCobranca(str, Enum):
    AVULSA = "avulsa"
    PLANO = "plano"
    ISENTO = "isento"


class CobrancaStatus(str, Enum):
    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"
    ESTORNADO = "estornado"


class PagamentoMetodo(str, Enum):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    BOLETO = "boleto"


# 1. Estacionamento (Tenant)
class Estacionamento(Base):
    __tablename__ = "estacionamentos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    nome_fantasia: Mapped[str] = mapped_column(String(120), nullable=False)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(18), unique=True, nullable=False, index=True)
    email_contato: Mapped[str] = mapped_column(String(100), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=EstacionamentoStatus.ATIVO.value, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    usuarios: Mapped[List["Usuario"]] = relationship("Usuario", back_populates="estacionamento", cascade="all, delete-orphan")
    clientes: Mapped[List["Cliente"]] = relationship("Cliente", back_populates="estacionamento", cascade="all, delete-orphan")
    veiculos: Mapped[List["Veiculo"]] = relationship("Veiculo", back_populates="estacionamento", cascade="all, delete-orphan")
    planos: Mapped[List["Plano"]] = relationship("Plano", back_populates="estacionamento", cascade="all, delete-orphan")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="estacionamento", cascade="all, delete-orphan")
    tarifas: Mapped[List["Tarifa"]] = relationship("Tarifa", back_populates="estacionamento", cascade="all, delete-orphan")


# 2. Usuário (Autenticação e RBAC)
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=True, index=True)
    cliente_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    estacionamento: Mapped[Optional["Estacionamento"]] = relationship("Estacionamento", back_populates="usuarios")
    cliente: Mapped[Optional["Cliente"]] = relationship("Cliente", back_populates="usuario")


# 3. Cliente
class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("estacionamento_id", "documento", name="uq_cliente_estacionamento_documento"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    documento: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo_documento: Mapped[str] = mapped_column(String(10), default=DocumentoTipo.CPF.value, nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    plano_tipo: Mapped[str] = mapped_column(String(20), default="mensal", nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    estacionamento: Mapped["Estacionamento"] = relationship("Estacionamento", back_populates="clientes")
    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", back_populates="cliente", uselist=False)
    veiculos: Mapped[List["Veiculo"]] = relationship("Veiculo", back_populates="cliente", cascade="all, delete-orphan")
    assinaturas: Mapped[List["Assinatura"]] = relationship("Assinatura", back_populates="cliente")

    @property
    def acesso_portal(self) -> bool:
        """Indica se o cliente possui login ativo no portal."""
        return self.usuario is not None and self.usuario.ativo


# 4. Veículo
class Veiculo(Base):
    __tablename__ = "veiculos"
    __table_args__ = (
        UniqueConstraint("estacionamento_id", "placa", name="uq_veiculo_estacionamento_placa"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    marca: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    modelo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cor: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20), default=VeiculoTipo.CARRO.value, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="veiculos")
    estacionamento: Mapped["Estacionamento"] = relationship("Estacionamento", back_populates="veiculos")
    assinaturas_vinculadas: Mapped[List["AssinaturaVeiculo"]] = relationship("AssinaturaVeiculo", back_populates="veiculo")


# 5. Plano (Mensal / Anual)
class Plano(Base):
    __tablename__ = "planos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(80), nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo_recorrencia: Mapped[str] = mapped_column(String(20), default=PlanoRecorrencia.MENSAL.value, nullable=False)
    valor_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    limite_veiculos: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    valor_veiculo_adicional: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    estacionamento: Mapped["Estacionamento"] = relationship("Estacionamento", back_populates="planos")
    assinaturas: Mapped[List["Assinatura"]] = relationship("Assinatura", back_populates="plano")


# 6. Assinatura
class Assinatura(Base):
    __tablename__ = "assinaturas"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False, index=True)
    plano_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("planos.id", ondelete="RESTRICT"), nullable=False, index=True)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AssinaturaStatus.ATIVA.value, nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="assinaturas")
    plano: Mapped["Plano"] = relationship("Plano", back_populates="assinaturas")
    veiculos_vinculados: Mapped[List["AssinaturaVeiculo"]] = relationship("AssinaturaVeiculo", back_populates="assinatura", cascade="all, delete-orphan")


# 7. AssinaturaVeiculo (Vínculo n:n com auditoria)
class AssinaturaVeiculo(Base):
    __tablename__ = "assinatura_veiculos"
    __table_args__ = (
        UniqueConstraint("assinatura_id", "veiculo_id", name="uq_assinatura_veiculo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    assinatura_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("assinaturas.id", ondelete="CASCADE"), nullable=False, index=True)
    veiculo_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("veiculos.id", ondelete="CASCADE"), nullable=False, index=True)
    vinculado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    assinatura: Mapped["Assinatura"] = relationship("Assinatura", back_populates="veiculos_vinculados")
    veiculo: Mapped["Veiculo"] = relationship("Veiculo", back_populates="assinaturas_vinculadas")


# 8. Câmera
class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    identificador: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default=CameraTipo.AMBOS.value, nullable=False)
    rtsp_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    localizacao: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    estacionamento: Mapped["Estacionamento"] = relationship("Estacionamento", back_populates="cameras")


# 9. Tarifa (Avulsa)
class Tarifa(Base):
    __tablename__ = "tarifas"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(80), nullable=False)
    valor_primeira_hora: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_hora_adicional: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_diaria: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tolerancia_minutos: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    vigente_desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    vigente_ate: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    estacionamento: Mapped["Estacionamento"] = relationship("Estacionamento", back_populates="tarifas")


# 10. Movimentação (Eventos ALPR e Permanência)
class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    veiculo_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("veiculos.id", ondelete="SET NULL"), nullable=True)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    camera_entrada_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    camera_saida_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    entrada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    saida_em: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    permanencia_minutos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=MovimentacaoStatus.ABERTA.value, nullable=False, index=True)
    tipo_cobranca: Mapped[Optional[str]] = mapped_column(String(20), default=TipoCobranca.AVULSA.value, nullable=True)
    observacao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    veiculo: Mapped[Optional["Veiculo"]] = relationship("Veiculo")
    cobranca: Mapped[Optional["Cobranca"]] = relationship("Cobranca", back_populates="movimentacao", uselist=False)


# 11. Cobrança
class Cobranca(Base):
    __tablename__ = "cobrancas"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    movimentacao_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("movimentacoes.id", ondelete="SET NULL"), nullable=True)
    assinatura_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("assinaturas.id", ondelete="SET NULL"), nullable=True)
    cliente_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("clientes.id", ondelete="SET NULL"), nullable=True)
    valor_bruto: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    desconto: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    valor_liquido: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=CobrancaStatus.PENDENTE.value, nullable=False, index=True)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    movimentacao: Mapped[Optional["Movimentacao"]] = relationship("Movimentacao", back_populates="cobranca")
    pagamentos: Mapped[List["Pagamento"]] = relationship("Pagamento", back_populates="cobranca", cascade="all, delete-orphan")


# 12. Pagamento
class Pagamento(Base):
    __tablename__ = "pagamentos"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    cobranca_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("cobrancas.id", ondelete="CASCADE"), nullable=False, index=True)
    estacionamento_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=False, index=True)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metodo: Mapped[str] = mapped_column(String(30), nullable=False)
    pago_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    registrado_por_usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    comprovante_transacao: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    cobranca: Mapped["Cobranca"] = relationship("Cobranca", back_populates="pagamentos")


# 13. Auditoria
class Auditoria(Base):
    __tablename__ = "auditorias"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    estacionamento_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("estacionamentos.id", ondelete="CASCADE"), nullable=True, index=True)
    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    acao: Mapped[str] = mapped_column(String(60), nullable=False)
    tabela: Mapped[str] = mapped_column(String(50), nullable=False)
    registro_id: Mapped[str] = mapped_column(String(50), nullable=False)
    dados_anteriores: Mapped[Optional[dict]] = mapped_column(JSONType(), nullable=True)
    dados_novos: Mapped[Optional[dict]] = mapped_column(JSONType(), nullable=True)
    ip_origem: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

