"""
Esquemas Pydantic para validação, serialização de entrada e resposta da API REST.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.entities import (
    AssinaturaStatus,
    CameraTipo,
    CobrancaStatus,
    DocumentoTipo,
    EstacionamentoStatus,
    MovimentacaoStatus,
    PagamentoMetodo,
    PlanoRecorrencia,
    TipoCobranca,
    UsuarioPerfil,
    VeiculoTipo,
)


# --- Autenticação e Usuários ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    perfil: str
    nome: str
    email: str
    estacionamento_id: Optional[uuid.UUID] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    perfil: Optional[str] = None
    estacionamento_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class PasswordRecoveryRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=20)
    nova_senha: str = Field(..., min_length=8, max_length=128)


class MessageOut(BaseModel):
    detail: str


class PortalAccessCreate(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=8, max_length=128, description="Senha provisória do cliente")


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    perfil: UsuarioPerfil = UsuarioPerfil.ESTACIONAMENTO_ADMIN
    estacionamento_id: Optional[uuid.UUID] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    email: str
    perfil: str
    ativo: bool
    estacionamento_id: Optional[uuid.UUID] = None
    cliente_id: Optional[uuid.UUID] = None
    criado_em: datetime


# --- Estacionamento (Tenant) ---
class EstacionamentoCreate(BaseModel):
    nome_fantasia: str = Field(..., min_length=2, max_length=120)
    razao_social: str = Field(..., min_length=2, max_length=150)
    cnpj: str = Field(..., min_length=14, max_length=18)
    email_contato: EmailStr
    telefone: Optional[str] = None


class EstacionamentoUpdate(BaseModel):
    nome_fantasia: Optional[str] = None
    razao_social: Optional[str] = None
    email_contato: Optional[EmailStr] = None
    telefone: Optional[str] = None
    status: Optional[EstacionamentoStatus] = None


class EstacionamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome_fantasia: str
    razao_social: str
    cnpj: str
    email_contato: str
    telefone: Optional[str] = None
    status: str
    criado_em: datetime


# --- Veículos e Clientes ---
class VeiculoCreate(BaseModel):
    placa: str = Field(..., min_length=7, max_length=10)
    marca: Optional[str] = None
    modelo: Optional[str] = None
    cor: Optional[str] = None
    tipo: VeiculoTipo = VeiculoTipo.CARRO


class VeiculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cliente_id: uuid.UUID
    estacionamento_id: uuid.UUID
    placa: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    cor: Optional[str] = None
    tipo: str
    ativo: bool
    criado_em: datetime


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    documento: str = Field(..., min_length=11, max_length=20)
    tipo_documento: DocumentoTipo = DocumentoTipo.CPF
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    # Requisito: O cadastro inicial de um cliente deverá incluir pelo menos um veículo
    veiculos_iniciais: List[VeiculoCreate] = Field(..., min_length=1)


class ClienteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    nome: str
    documento: str
    tipo_documento: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    criado_em: datetime
    acesso_portal: bool = False
    veiculos: List[VeiculoOut] = []


# --- Planos e Tarifas ---
class TarifaCreate(BaseModel):
    descricao: str = Field(..., max_length=80)
    valor_primeira_hora: Decimal = Field(..., ge=0)
    valor_hora_adicional: Decimal = Field(..., ge=0)
    valor_diaria: Decimal = Field(..., ge=0)
    tolerancia_minutos: int = Field(default=15, ge=0)


class TarifaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    descricao: str
    valor_primeira_hora: Decimal
    valor_hora_adicional: Decimal
    valor_diaria: Decimal
    tolerancia_minutos: int
    vigente_desde: datetime


class PlanoCreate(BaseModel):
    nome: str = Field(..., max_length=80)
    descricao: Optional[str] = None
    tipo_recorrencia: PlanoRecorrencia = PlanoRecorrencia.MENSAL
    valor_base: Decimal = Field(..., ge=0)
    limite_veiculos: int = Field(default=1, ge=1)
    valor_veiculo_adicional: Decimal = Field(default=Decimal("0.00"), ge=0)


class PlanoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    nome: str
    descricao: Optional[str] = None
    tipo_recorrencia: str
    valor_base: Decimal
    limite_veiculos: int
    valor_veiculo_adicional: Decimal
    ativo: bool


class AssinaturaCreate(BaseModel):
    cliente_id: uuid.UUID
    plano_id: uuid.UUID
    veiculos_ids: List[uuid.UUID] = Field(..., min_length=1)
    data_inicio: date


class AssinaturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cliente_id: uuid.UUID
    plano_id: uuid.UUID
    estacionamento_id: uuid.UUID
    data_inicio: date
    data_fim: date
    status: str
    valor_total: Decimal
    criado_em: datetime


# --- Movimentação e ALPR ---
class MovimentacaoEntrada(BaseModel):
    placa: str = Field(..., min_length=7, max_length=10)
    camera_id: Optional[uuid.UUID] = None
    timestamp: Optional[datetime] = None


class MovimentacaoSaida(BaseModel):
    placa: str = Field(..., min_length=7, max_length=10)
    camera_id: Optional[uuid.UUID] = None
    timestamp: Optional[datetime] = None


class MovimentacaoCorrecaoManual(BaseModel):
    placa: Optional[str] = None
    status: Optional[MovimentacaoStatus] = None
    observacao: str = Field(..., min_length=3, description="Justificativa da alteração manual para auditoria")


class CobrancaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    movimentacao_id: Optional[uuid.UUID] = None
    assinatura_id: Optional[uuid.UUID] = None
    cliente_id: Optional[uuid.UUID] = None
    valor_bruto: Decimal
    desconto: Decimal
    valor_liquido: Decimal
    status: str
    data_vencimento: date
    criado_em: datetime


class MovimentacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    veiculo_id: Optional[uuid.UUID] = None
    placa: str
    entrada_em: datetime
    saida_em: Optional[datetime] = None
    permanencia_minutos: Optional[int] = None
    status: str
    tipo_cobranca: Optional[str] = None
    observacao: Optional[str] = None
    cobranca: Optional[CobrancaOut] = None


# --- Pagamento ---
class PagamentoCreate(BaseModel):
    cobranca_id: uuid.UUID
    valor_pago: Decimal = Field(..., ge=0)
    metodo: PagamentoMetodo = PagamentoMetodo.PIX
    comprovante_transacao: Optional[str] = None


class PagamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cobranca_id: uuid.UUID
    estacionamento_id: uuid.UUID
    valor_pago: Decimal
    metodo: str
    pago_em: datetime
    comprovante_transacao: Optional[str] = None


# --- Dashboard ---
class DashboardMetricsOut(BaseModel):
    veiculos_estacionados_agora: int
    entradas_hoje: int
    saidas_hoje: int
    clientes_cadastrados: int
    veiculos_cadastrados: int
    assinaturas_ativas: int
    receita_total_registrada: Decimal
    cobrancas_pendentes_valor: Decimal
    cobrancas_pendentes_quantidade: int
    movimentacoes_recentes: List[MovimentacaoOut] = []


# --- Auditoria ---
class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: Optional[uuid.UUID] = None
    usuario_id: Optional[uuid.UUID] = None
    acao: str
    tabela: str
    registro_id: str
    dados_anteriores: Optional[Dict[str, Any]] = None
    dados_novos: Optional[Dict[str, Any]] = None
    ip_origem: Optional[str] = None
    criado_em: datetime


# --- Câmeras ---
class CameraCreate(BaseModel):
    identificador: str = Field(..., min_length=2, max_length=50)
    tipo: CameraTipo = CameraTipo.AMBOS
    rtsp_url: Optional[str] = Field(None, max_length=255)
    localizacao: Optional[str] = Field(None, max_length=100)
    ativa: bool = True


class CameraUpdate(BaseModel):
    identificador: Optional[str] = Field(None, min_length=2, max_length=50)
    tipo: Optional[CameraTipo] = None
    rtsp_url: Optional[str] = Field(None, max_length=255)
    localizacao: Optional[str] = Field(None, max_length=100)
    ativa: Optional[bool] = None


class CameraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estacionamento_id: uuid.UUID
    identificador: str
    tipo: str
    rtsp_url: Optional[str] = None
    localizacao: Optional[str] = None
    ativa: bool
    criado_em: datetime


# --- Processamento ALPR & Pipeline ---
class ALPRConfirmedPassageEventOut(BaseModel):
    track_id: int
    plate: str
    pattern: str
    vehicle_class: str
    timestamp_sec: float
    ocr_confidence: float
    det_confidence: float
    tipo_evento: str  # 'entrada' | 'saida' | 'inconsistente'
    movement_id: Optional[uuid.UUID] = None
    status_movimentacao: Optional[str] = None


class ALPRProcessVideoResponse(BaseModel):
    video_source: str
    total_frames_processed: int
    processing_time_seconds: float
    average_fps: float
    vehicles_detected_count: int
    plates_detected_count: int
    valid_plates_count: int
    invalid_plates_count: int
    confirmed_passages_count: int
    movements_registered: int
    passages: List[ALPRConfirmedPassageEventOut] = []


class ALPRSimulateDetectionRequest(BaseModel):
    placa: str = Field(..., min_length=7, max_length=10)
    camera_id: Optional[uuid.UUID] = None
    tipo_evento: Optional[str] = Field("auto", description="'entrada', 'saida' ou 'auto'")
    ocr_confidence: float = Field(0.95, ge=0.0, le=1.0)
    det_confidence: float = Field(0.90, ge=0.0, le=1.0)
    timestamp: Optional[datetime] = None




# --- Portal do Cliente ---
class PortalPerfilOut(BaseModel):
    nome: str
    documento_mascarado: str
    tipo_documento: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    estacionamento: str
    veiculos: List[VeiculoOut] = []


class PortalMovimentacaoOut(BaseModel):
    """Visão do cliente sobre uma passagem. Não expõe observações internas nem câmeras."""
    id: uuid.UUID
    placa: str
    entrada_em: datetime
    saida_em: Optional[datetime] = None
    permanencia_minutos: Optional[int] = None
    em_andamento: bool = False
    status: str
    tipo_cobranca: Optional[str] = None
    cobranca: Optional[CobrancaOut] = None


class PortalAssinaturaOut(BaseModel):
    id: uuid.UUID
    plano_id: uuid.UUID
    plano_nome: str
    tipo_recorrencia: str
    data_inicio: date
    data_fim: date
    status: str
    valor_total: Decimal
    placas: List[str] = []


class PortalResumoOut(BaseModel):
    veiculos_cadastrados: int
    veiculos_estacionados: List[PortalMovimentacaoOut] = []
    assinaturas_ativas: int
    cobrancas_pendentes_quantidade: int
    cobrancas_pendentes_valor: Decimal
