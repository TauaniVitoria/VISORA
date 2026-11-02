import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ALPRPassageEvent,
  ALPRProcessVideoResponse,
  AuditoriaLog,
  Camera,
  Cliente,
  ClienteMovimentacao,
  Cobranca,
  DashboardMetrics,
  Estacionamento,
  Movimentacao,
  Pagamento,
  Plano,
  PortalAssinatura,
  PortalMovimentacao,
  PortalPerfil,
  PortalResumo,
  Tarifa,
  Veiculo,
} from '../models/models';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000/api/v1';

  constructor(private http: HttpClient) {}

  // --- Dashboard ---
  getDashboardMetrics(): Observable<DashboardMetrics> {
    return this.http.get<DashboardMetrics>(`${this.baseUrl}/dashboard/metrics`);
  }

  // --- Clientes e Veículos ---
  getCustomers(): Observable<Cliente[]> {
    return this.http.get<Cliente[]>(`${this.baseUrl}/customers/`);
  }

  createCustomer(data: {
    codigo?: string;
    nome: string;
    documento: string;
    tipo_documento: string;
    telefone: string;
    email?: string;
    plano_tipo: string;
    veiculos_iniciais: { placa: string; marca?: string; modelo?: string; cor?: string; tipo: string }[];
  }): Observable<Cliente> {
    return this.http.post<Cliente>(`${this.baseUrl}/customers/`, data);
  }

  getCustomerMovements(
    clientId: string,
    params?: { placa?: string; data_inicio?: string; data_fim?: string }
  ): Observable<ClienteMovimentacao[]> {
    let httpParams = new HttpParams();
    if (params?.placa) httpParams = httpParams.set('placa', params.placa);
    if (params?.data_inicio) httpParams = httpParams.set('data_inicio', params.data_inicio);
    if (params?.data_fim) httpParams = httpParams.set('data_fim', params.data_fim);
    return this.http.get<ClienteMovimentacao[]>(`${this.baseUrl}/customers/${clientId}/movements`, { params: httpParams });
  }

  addVehicle(clientId: string, data: { placa: string; marca?: string; modelo?: string; cor?: string; tipo: string }): Observable<Veiculo> {
    return this.http.post<Veiculo>(`${this.baseUrl}/customers/${clientId}/vehicles`, data);
  }

  // --- Tarifas e Planos ---
  getActiveTariff(): Observable<Tarifa> {
    return this.http.get<Tarifa>(`${this.baseUrl}/tariffs-plans/tariffs/active`);
  }

  createTariff(data: {
    descricao: string;
    valor_primeira_hora: number;
    valor_hora_adicional: number;
    valor_diaria: number;
    tolerancia_minutos: number;
  }): Observable<Tarifa> {
    return this.http.post<Tarifa>(`${this.baseUrl}/tariffs-plans/tariffs`, data);
  }

  getPlans(): Observable<Plano[]> {
    return this.http.get<Plano[]>(`${this.baseUrl}/tariffs-plans/plans`);
  }

  createPlan(data: {
    nome: string;
    descricao?: string;
    tipo_recorrencia: string;
    valor_base: number;
    limite_veiculos: number;
    valor_veiculo_adicional: number;
  }): Observable<Plano> {
    return this.http.post<Plano>(`${this.baseUrl}/tariffs-plans/plans`, data);
  }

  // --- Movimentações ALPR ---
  getActiveMovements(): Observable<Movimentacao[]> {
    return this.http.get<Movimentacao[]>(`${this.baseUrl}/movements/active`);
  }

  getMovementsHistory(filters?: {
    placa?: string;
    status_filter?: string;
    skip?: number;
    limit?: number;
  }): Observable<Movimentacao[]> {
    let params = new HttpParams();
    if (filters?.placa) params = params.set('placa', filters.placa);
    if (filters?.status_filter) params = params.set('status_filter', filters.status_filter);
    if (filters?.skip !== undefined) params = params.set('skip', filters.skip.toString());
    if (filters?.limit !== undefined) params = params.set('limit', filters.limit.toString());

    return this.http.get<Movimentacao[]>(`${this.baseUrl}/movements/history`, { params });
  }

  registerEntry(data: { placa: string; camera_id?: string; timestamp?: string }): Observable<Movimentacao> {
    return this.http.post<Movimentacao>(`${this.baseUrl}/movements/entry`, data);
  }

  registerExit(data: { placa: string; camera_id?: string; timestamp?: string }): Observable<Movimentacao> {
    return this.http.post<Movimentacao>(`${this.baseUrl}/movements/exit`, data);
  }

  manualCorrection(movementId: string, data: { placa?: string; status?: string; observacao: string }): Observable<Movimentacao> {
    return this.http.patch<Movimentacao>(`${this.baseUrl}/movements/${movementId}/correction`, data);
  }

  // --- Cobranças e Pagamentos ---
  getCharges(statusFilter?: string): Observable<Cobranca[]> {
    let params = new HttpParams();
    if (statusFilter) params = params.set('status_filter', statusFilter);
    return this.http.get<Cobranca[]>(`${this.baseUrl}/billing/charges`, { params });
  }

  registerPayment(data: {
    cobranca_id: string;
    valor_pago: number;
    metodo: string;
    comprovante_transacao?: string;
  }): Observable<Pagamento> {
    return this.http.post<Pagamento>(`${this.baseUrl}/billing/payments`, data);
  }

  // --- Tenants (SaaS Admin) ---
  getTenants(): Observable<Estacionamento[]> {
    return this.http.get<Estacionamento[]>(`${this.baseUrl}/tenants/`);
  }

  createTenant(data: {
    nome_fantasia: string;
    razao_social: string;
    cnpj: string;
    email_contato: string;
    telefone?: string;
  }): Observable<Estacionamento> {
    return this.http.post<Estacionamento>(`${this.baseUrl}/tenants/`, data);
  }

  // --- Auditoria ---
  getAuditLogs(): Observable<AuditoriaLog[]> {
    return this.http.get<AuditoriaLog[]>(`${this.baseUrl}/audit/`);
  }

  // --- Câmeras ALPR ---
  getCameras(): Observable<Camera[]> {
    return this.http.get<Camera[]>(`${this.baseUrl}/cameras/`);
  }

  createCamera(data: {
    identificador: string;
    tipo: string;
    rtsp_url?: string;
    localizacao?: string;
    ativa?: boolean;
  }): Observable<Camera> {
    return this.http.post<Camera>(`${this.baseUrl}/cameras/`, data);
  }

  updateCamera(cameraId: string, data: {
    identificador?: string;
    tipo?: string;
    rtsp_url?: string;
    localizacao?: string;
    ativa?: boolean;
  }): Observable<Camera> {
    return this.http.put<Camera>(`${this.baseUrl}/cameras/${cameraId}`, data);
  }

  deleteCamera(cameraId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/cameras/${cameraId}`);
  }

  // --- Processamento ALPR ---
  alprSimulateDetection(data: {
    placa: string;
    camera_id?: string;
    tipo_evento?: string;
    ocr_confidence?: number;
    det_confidence?: number;
  }): Observable<ALPRPassageEvent> {
    return this.http.post<ALPRPassageEvent>(`${this.baseUrl}/alpr/simulate-detection`, data);
  }

  alprProcessVideoByPath(data: {
    video_path: string;
    camera_id?: string;
    sentido_default?: string;
    max_frames?: number;
    save_annotated_video?: boolean;
  }): Observable<ALPRProcessVideoResponse> {
    const formData = new FormData();
    formData.append('video_path', data.video_path);
    if (data.camera_id) formData.append('camera_id', data.camera_id);
    if (data.sentido_default) formData.append('sentido_default', data.sentido_default);
    if (data.max_frames !== undefined) formData.append('max_frames', data.max_frames.toString());
    if (data.save_annotated_video !== undefined) formData.append('save_annotated_video', String(data.save_annotated_video));
    return this.http.post<ALPRProcessVideoResponse>(`${this.baseUrl}/alpr/process-video`, formData);
  }

  alprProcessVideoUpload(
    file: File,
    opts?: { camera_id?: string; sentido_default?: string; max_frames?: number }
  ): Observable<ALPRProcessVideoResponse> {
    const formData = new FormData();
    formData.append('video_file', file, file.name);
    if (opts?.camera_id) formData.append('camera_id', opts.camera_id);
    if (opts?.sentido_default) formData.append('sentido_default', opts.sentido_default);
    if (opts?.max_frames !== undefined) formData.append('max_frames', opts.max_frames.toString());
    return this.http.post<ALPRProcessVideoResponse>(`${this.baseUrl}/alpr/process-video`, formData);
  }

  // --- Acesso ao portal (administrador) ---
  createPortalAccess(clientId: string, data: { email: string; senha: string }): Observable<unknown> {
    return this.http.post(`${this.baseUrl}/customers/${clientId}/portal-access`, data);
  }

  revokePortalAccess(clientId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/customers/${clientId}/portal-access`);
  }

  // --- Recuperação de senha (público) ---
  forgotPassword(email: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${this.baseUrl}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, novaSenha: string): Observable<{ detail: string }> {
    return this.http.post<{ detail: string }>(`${this.baseUrl}/auth/reset-password`, {
      token,
      nova_senha: novaSenha,
    });
  }

  // --- Portal do Cliente ---
  getPortalProfile(): Observable<PortalPerfil> {
    return this.http.get<PortalPerfil>(`${this.baseUrl}/portal/me`);
  }

  getPortalSummary(): Observable<PortalResumo> {
    return this.http.get<PortalResumo>(`${this.baseUrl}/portal/summary`);
  }

  getPortalMovements(skip = 0, limit = 50): Observable<PortalMovimentacao[]> {
    const params = new HttpParams().set('skip', skip).set('limit', limit);
    return this.http.get<PortalMovimentacao[]>(`${this.baseUrl}/portal/movements`, { params });
  }

  getPortalSubscriptions(): Observable<PortalAssinatura[]> {
    return this.http.get<PortalAssinatura[]>(`${this.baseUrl}/portal/subscriptions`);
  }

  getPortalPlans(): Observable<Plano[]> {
    return this.http.get<Plano[]>(`${this.baseUrl}/portal/plans`);
  }

  getPortalCharges(statusFilter?: string): Observable<Cobranca[]> {
    let params = new HttpParams();
    if (statusFilter) params = params.set('status_filter', statusFilter);
    return this.http.get<Cobranca[]>(`${this.baseUrl}/portal/charges`, { params });
  }

  getPortalPayments(): Observable<Pagamento[]> {
    return this.http.get<Pagamento[]>(`${this.baseUrl}/portal/payments`);
  }
}
