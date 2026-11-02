/**
 * Modelos de dados e interfaces TypeScript da aplicação SaaS de Estacionamentos ALPR.
 */

export type UsuarioPerfil = 'SAAS_ADMIN' | 'ESTACIONAMENTO_ADMIN' | 'CLIENTE';

export interface Usuario {
  id: string;
  nome: string;
  email: string;
  perfil: UsuarioPerfil;
  ativo: boolean;
  estacionamento_id?: string;
  cliente_id?: string;
  criado_em: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  perfil: UsuarioPerfil;
  nome: string;
  email: string;
  estacionamento_id?: string;
}

export interface Estacionamento {
  id: string;
  nome_fantasia: string;
  razao_social: string;
  cnpj: string;
  email_contato: string;
  telefone?: string;
  status: 'ativo' | 'inativo' | 'bloqueado';
  criado_em: string;
}

export interface Veiculo {
  id: string;
  cliente_id: string;
  estacionamento_id: string;
  placa: string;
  marca?: string;
  modelo?: string;
  cor?: string;
  tipo: 'carro' | 'moto' | 'caminhao' | 'onibus';
  ativo: boolean;
  criado_em: string;
}

export interface Cliente {
  id: string;
  codigo: string;
  estacionamento_id: string;
  nome: string;
  documento: string;
  tipo_documento: 'CPF' | 'CNPJ';
  telefone: string;
  email?: string;
  plano_tipo: 'diario' | 'mensal' | 'anual' | string;
  criado_em: string;
  acesso_portal?: boolean;
  veiculos: Veiculo[];
}

export interface ClienteMovimentacao {
  id: string;
  placa: string;
  entrada_em: string;
  saida_em?: string;
  permanencia_minutos?: number;
  status: string;
  tipo_cobranca?: string;
  valor_calculado?: number;
  esta_estacionado: boolean;
}

export interface Tarifa {
  id: string;
  estacionamento_id: string;
  descricao: string;
  valor_primeira_hora: number;
  valor_hora_adicional: number;
  valor_diaria: number;
  tolerancia_minutos: number;
  vigente_desde: string;
}

export interface Plano {
  id: string;
  estacionamento_id: string;
  nome: string;
  descricao?: string;
  tipo_recorrencia: 'mensal' | 'anual';
  valor_base: number;
  limite_veiculos: number;
  valor_veiculo_adicional: number;
  ativo: boolean;
}

export interface Cobranca {
  id: string;
  estacionamento_id: string;
  movimentacao_id?: string;
  assinatura_id?: string;
  cliente_id?: string;
  valor_bruto: number;
  desconto: number;
  valor_liquido: number;
  status: 'pendente' | 'pago' | 'cancelado' | 'estornado';
  data_vencimento: string;
  criado_em: string;
}

export interface Movimentacao {
  id: string;
  estacionamento_id: string;
  veiculo_id?: string;
  placa: string;
  camera_entrada_id?: string;
  camera_saida_id?: string;
  entrada_em: string;
  saida_em?: string;
  permanencia_minutos?: number;
  status: 'aberta' | 'concluida' | 'inconsistente' | 'cancelada';
  tipo_cobranca?: 'avulsa' | 'plano' | 'isento';
  observacao?: string;
  cobranca?: Cobranca;
  tem_plano?: boolean;
}

export interface Pagamento {
  id: string;
  cobranca_id: string;
  estacionamento_id: string;
  valor_pago: number;
  metodo: 'dinheiro' | 'pix' | 'cartao_credito' | 'cartao_debito' | 'boleto';
  pago_em: string;
  comprovante_transacao?: string;
}

export interface DashboardMetrics {
  veiculos_estacionados_agora: number;
  entradas_hoje: number;
  saidas_hoje: number;
  clientes_cadastrados: number;
  veiculos_cadastrados: number;
  assinaturas_ativas: number;
  receita_total_registrada: number;
  cobrancas_pendentes_valor: number;
  cobrancas_pendentes_quantidade: number;
  movimentacoes_recentes?: Movimentacao[];
}

export interface AuditoriaLog {
  id: string;
  estacionamento_id?: string;
  usuario_id?: string;
  acao: string;
  tabela: string;
  registro_id: string;
  dados_anteriores?: any;
  dados_novos?: any;
  ip_origem?: string;
  criado_em: string;
}

export interface Camera {
  id: string;
  estacionamento_id: string;
  identificador: string;
  tipo: 'entrada' | 'saida' | 'ambos';
  rtsp_url?: string;
  localizacao?: string;
  ativa: boolean;
  criado_em: string;
}

export interface ALPRPassageEvent {
  track_id: number;
  plate: string;
  pattern: string;
  vehicle_class: string;
  timestamp_sec: number;
  ocr_confidence: number;
  det_confidence: number;
  tipo_evento: 'entrada' | 'saida' | 'inconsistente';
  movement_id?: string;
  status_movimentacao?: string;
}

export interface ALPRProcessVideoResponse {
  video_source: string;
  total_frames_processed: number;
  processing_time_seconds: number;
  average_fps: number;
  vehicles_detected_count: number;
  plates_detected_count: number;
  valid_plates_count: number;
  invalid_plates_count: number;
  confirmed_passages_count: number;
  movements_registered: number;
  passages: ALPRPassageEvent[];
}

// --- Portal do Cliente ---
export interface PortalPerfil {
  nome: string;
  documento_mascarado: string;
  tipo_documento: string;
  telefone?: string;
  email?: string;
  estacionamento: string;
  veiculos: Veiculo[];
}

export interface PortalMovimentacao {
  id: string;
  placa: string;
  entrada_em: string;
  saida_em?: string;
  permanencia_minutos?: number;
  em_andamento: boolean;
  status: 'aberta' | 'concluida' | 'inconsistente' | 'cancelada';
  tipo_cobranca?: string;
  cobranca?: Cobranca;
}

export interface PortalAssinatura {
  id: string;
  plano_id: string;
  plano_nome: string;
  tipo_recorrencia: 'mensal' | 'anual';
  data_inicio: string;
  data_fim: string;
  status: string;
  valor_total: number;
  placas: string[];
}

export interface PortalResumo {
  veiculos_cadastrados: number;
  veiculos_estacionados: PortalMovimentacao[];
  assinaturas_ativas: number;
  cobrancas_pendentes_quantidade: number;
  cobrancas_pendentes_valor: number;
}
