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
  estacionamento_id: string;
  nome: string;
  documento: string;
  tipo_documento: 'CPF' | 'CNPJ';
  telefone?: string;
  email?: string;
  criado_em: string;
  veiculos: Veiculo[];
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

