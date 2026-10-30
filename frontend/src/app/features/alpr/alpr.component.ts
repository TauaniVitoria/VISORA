import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Camera, ALPRPassageEvent, ALPRProcessVideoResponse } from '../../core/models/models';

@Component({
  selector: 'app-alpr',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="alpr-page">
      <header class="page-header">
        <div>
          <h2>Central ALPR — Câmeras & Processamento</h2>
          <p class="subtitle">Gerenciamento de câmeras, ingestão de vídeo e detecção de placas em tempo real</p>
        </div>
      </header>

      <!-- Messages -->
      <div *ngIf="successMessage" class="alert alert-success">{{ successMessage }}</div>
      <div *ngIf="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

      <!-- Tabs -->
      <div class="tab-bar">
        <button class="tab-btn" [class.active]="activeTab === 'cameras'" (click)="activeTab = 'cameras'">
          Câmeras
        </button>
        <button class="tab-btn" [class.active]="activeTab === 'detect'" (click)="activeTab = 'detect'">
          Detecção em Tempo Real
        </button>
        <button class="tab-btn" [class.active]="activeTab === 'video'" (click)="activeTab = 'video'">
          Processar Vídeo
        </button>
      </div>

      <!-- ====== TAB: Câmeras ====== -->
      <div *ngIf="activeTab === 'cameras'" class="tab-content">
        <div class="section-header">
          <h3>Câmeras Cadastradas</h3>
          <button class="btn-primary" (click)="showCameraForm = !showCameraForm">
            {{ showCameraForm ? 'Cancelar' : '+ Nova Câmera' }}
          </button>
        </div>

        <!-- New Camera Form -->
        <div *ngIf="showCameraForm" class="form-card">
          <div class="form-grid">
            <div class="form-group">
              <label>Identificador *</label>
              <input type="text" [(ngModel)]="newCamera.identificador" placeholder="Ex: CAM-ENTRADA-01" />
            </div>
            <div class="form-group">
              <label>Tipo de Câmera</label>
              <select [(ngModel)]="newCamera.tipo">
                <option value="entrada">Entrada (Cancela)</option>
                <option value="saida">Saída (Cancela)</option>
                <option value="ambos">Bidirecional</option>
              </select>
            </div>
            <div class="form-group">
              <label>Localização</label>
              <input type="text" [(ngModel)]="newCamera.localizacao" placeholder="Ex: Cancela Norte Pista 1" />
            </div>
            <div class="form-group">
              <label>URL RTSP (Opcional)</label>
              <input type="text" [(ngModel)]="newCamera.rtsp_url" placeholder="rtsp://192.168.1.100:554/live" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-primary" (click)="createCamera()" [disabled]="!newCamera.identificador">
              Cadastrar Câmera
            </button>
          </div>
        </div>

        <!-- Camera List -->
        <div class="cards-grid">
          <div *ngFor="let cam of cameras" class="camera-card" [class.inactive]="!cam.ativa">
            <div class="cam-header">
              <span class="cam-type-pill" [ngClass]="cam.tipo">{{ cam.tipo | uppercase }}</span>
              <span class="cam-id">{{ cam.identificador }}</span>
              <span class="cam-status" [class.online]="cam.ativa" [class.offline]="!cam.ativa">
                {{ cam.ativa ? 'ATIVA' : 'INATIVA' }}
              </span>
            </div>
            <div class="cam-details">
              <div class="cam-detail"><strong>Tipo:</strong> {{ cam.tipo | uppercase }}</div>
              <div class="cam-detail" *ngIf="cam.localizacao"><strong>Local:</strong> {{ cam.localizacao }}</div>
              <div class="cam-detail" *ngIf="cam.rtsp_url"><strong>RTSP:</strong> <code>{{ cam.rtsp_url }}</code></div>
              <div class="cam-detail"><strong>Cadastro:</strong> {{ cam.criado_em | date:'dd/MM/yyyy HH:mm' }}</div>
            </div>
            <div class="cam-actions">
              <button class="btn-sm btn-toggle" (click)="toggleCamera(cam)">
                {{ cam.ativa ? 'Desativar' : 'Ativar' }}
              </button>
              <button class="btn-sm btn-delete" (click)="deleteCamera(cam)">Remover</button>
            </div>
          </div>
          <div *ngIf="cameras.length === 0" class="empty-state">
            Nenhuma câmera cadastrada. Clique em "+ Nova Câmera" para registrar seu primeiro ponto de leitura ALPR.
          </div>
        </div>
      </div>

      <!-- ====== TAB: Detecção em Tempo Real ====== -->
      <div *ngIf="activeTab === 'detect'" class="tab-content">
        <div class="section-header">
          <h3>Simular Detecção de Placa</h3>
        </div>
        <p class="description">Simula um evento de detecção de placa como se fosse uma câmera real reportando uma leitura.
          O sistema determina automaticamente se é entrada ou saída.</p>

        <div class="form-card">
          <div class="form-grid">
            <div class="form-group">
              <label>Placa do Veículo *</label>
              <input type="text" [(ngModel)]="detectForm.placa" placeholder="ABC1D23" class="input-plate"
                     maxlength="7" (input)="detectForm.placa = detectForm.placa.toUpperCase()" />
            </div>
            <div class="form-group">
              <label>Câmera Associada</label>
              <select [(ngModel)]="detectForm.camera_id">
                <option value="">Nenhuma (automático)</option>
                <option *ngFor="let cam of cameras" [value]="cam.id">
                  {{ cam.identificador }} ({{ cam.tipo }})
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Tipo do Evento</label>
              <select [(ngModel)]="detectForm.tipo_evento">
                <option value="auto">Automático (detecta pelo estado)</option>
                <option value="entrada">Forçar Entrada</option>
                <option value="saida">Forçar Saída</option>
              </select>
            </div>
            <div class="form-group">
              <label>Confiança OCR</label>
              <input type="number" [(ngModel)]="detectForm.ocr_confidence" step="0.01" min="0" max="1" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-primary btn-detect" (click)="simulateDetection()"
                    [disabled]="!detectForm.placa || detectForm.placa.length < 7 || loading">
              {{ loading ? 'Processando...' : 'Executar Detecção ALPR' }}
            </button>
          </div>
        </div>

        <!-- Detection Result -->
        <div *ngIf="lastDetection" class="result-card">
          <h4>Resultado da Detecção</h4>
          <div class="result-grid">
            <div class="result-item">
              <span class="result-label">Placa</span>
              <span class="result-value plate-value">{{ lastDetection.plate }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">Evento</span>
              <span class="result-value event-badge" [ngClass]="lastDetection.tipo_evento">
                {{ lastDetection.tipo_evento | uppercase }}
              </span>
            </div>
            <div class="result-item">
              <span class="result-label">Status Movimentação</span>
              <span class="result-value">{{ lastDetection.status_movimentacao }}</span>
            </div>
            <div class="result-item">
              <span class="result-label">Confiança OCR</span>
              <span class="result-value">{{ (lastDetection.ocr_confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== TAB: Processar Vídeo ====== -->
      <div *ngIf="activeTab === 'video'" class="tab-content">
        <div class="section-header">
          <h3>Ingestão de Vídeo ALPR</h3>
        </div>
        <p class="description">Envie um arquivo de vídeo gravado ou informe o caminho no servidor.
          O pipeline ALPR (YOLO + CRNN) processará automaticamente todos os quadros,
          identificará veículos e placas e criará movimentações.</p>

        <div class="form-card">
          <div class="form-grid">
            <div class="form-group full-width">
              <label>Upload de Arquivo de Vídeo</label>
              <input type="file" accept="video/*" (change)="onVideoFileSelected($event)" class="input-file" />
              <span class="file-hint" *ngIf="selectedVideoFile">{{ selectedVideoFile.name }} ({{ (selectedVideoFile.size / 1024 / 1024).toFixed(1) }} MB)</span>
            </div>
            <div class="form-group full-width">
              <label>— ou Caminho no Servidor —</label>
              <input type="text" [(ngModel)]="videoPathInput" placeholder="/caminho/para/video.mp4" />
            </div>
            <div class="form-group">
              <label>Câmera Associada</label>
              <select [(ngModel)]="videoOpts.camera_id">
                <option value="">Nenhuma</option>
                <option *ngFor="let cam of cameras" [value]="cam.id">
                  {{ cam.identificador }} ({{ cam.tipo }})
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Sentido Padrão</label>
              <select [(ngModel)]="videoOpts.sentido_default">
                <option value="auto">Automático</option>
                <option value="entrada">Todas como Entrada</option>
                <option value="saida">Todas como Saída</option>
              </select>
            </div>
            <div class="form-group">
              <label>Máx. Quadros (Opcional)</label>
              <input type="number" [(ngModel)]="videoOpts.max_frames" min="1" placeholder="Todos" />
            </div>
          </div>
          <div class="form-actions">
            <button class="btn-primary btn-process" (click)="processVideo()"
                    [disabled]="(!selectedVideoFile && !videoPathInput) || processingVideo">
              {{ processingVideo ? 'Pipeline ALPR em execução...' : 'Iniciar Processamento ALPR' }}
            </button>
          </div>
        </div>

        <!-- Video Processing Results -->
        <div *ngIf="videoResult" class="result-card">
          <h4>Resultado do Processamento</h4>
          <div class="metrics-grid">
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.total_frames_processed }}</span>
              <span class="metric-label">Quadros Processados</span>
            </div>
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.processing_time_seconds.toFixed(2) }}s</span>
              <span class="metric-label">Tempo Total</span>
            </div>
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.average_fps.toFixed(1) }}</span>
              <span class="metric-label">FPS Médio</span>
            </div>
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.vehicles_detected_count }}</span>
              <span class="metric-label">Veículos Detectados</span>
            </div>
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.plates_detected_count }}</span>
              <span class="metric-label">Placas Detectadas</span>
            </div>
            <div class="metric-item">
              <span class="metric-val">{{ videoResult.valid_plates_count }}</span>
              <span class="metric-label">Placas Válidas</span>
            </div>
            <div class="metric-item highlight">
              <span class="metric-val">{{ videoResult.confirmed_passages_count }}</span>
              <span class="metric-label">Passagens Confirmadas</span>
            </div>
            <div class="metric-item highlight">
              <span class="metric-val">{{ videoResult.movements_registered }}</span>
              <span class="metric-label">Movimentações Criadas</span>
            </div>
          </div>

          <!-- Passages Table -->
          <div *ngIf="videoResult.passages.length > 0" class="passages-section">
            <h4>Passagens Identificadas</h4>
            <div class="table-card">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Track</th>
                    <th>Placa</th>
                    <th>Padrão</th>
                    <th>Veículo</th>
                    <th>Evento</th>
                    <th>OCR %</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let p of videoResult.passages">
                    <td>#{{ p.track_id }}</td>
                    <td class="plate-cell">{{ p.plate }}</td>
                    <td>{{ p.pattern }}</td>
                    <td>{{ p.vehicle_class }}</td>
                    <td>
                      <span class="event-badge" [ngClass]="p.tipo_evento">{{ p.tipo_evento | uppercase }}</span>
                    </td>
                    <td>{{ (p.ocr_confidence * 100).toFixed(1) }}%</td>
                    <td>{{ p.status_movimentacao || '—' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .alpr-page { padding: 1.5rem; max-width: 1400px; margin: 0 auto; }
    .page-header {
      margin-bottom: 1.5rem;
      h2 { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin: 0; }
      .subtitle { color: #64748b; margin-top: 0.25rem; font-size: 0.875rem; }
    }
    .alert { padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.875rem;
      &.alert-success { background: #dcfce7; color: #166534; }
      &.alert-danger { background: #fee2e2; color: #991b1b; }
    }
    .tab-bar {
      display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 2px solid #e2e8f0; padding-bottom: 0;
    }
    .tab-btn {
      background: none; border: none; padding: 0.65rem 1.25rem; font-size: 0.9rem; font-weight: 500;
      color: #64748b; border-bottom: 3px solid transparent; margin-bottom: -2px; cursor: pointer;
      &.active { color: #0284c7; border-bottom-color: #0284c7; }
      &:hover { color: #0369a1; }
    }
    .tab-content { animation: fadeIn 0.2s ease; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .section-header {
      display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;
      h3 { font-size: 1.15rem; font-weight: 600; color: #1e293b; margin: 0; }
    }
    .description { color: #64748b; font-size: 0.875rem; margin-bottom: 1.25rem; line-height: 1.5; }
    .form-card {
      background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;
    }
    .form-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;
    }
    .form-group {
      display: flex; flex-direction: column; gap: 0.3rem;
      label { font-size: 0.825rem; font-weight: 500; color: #475569; }
      input, select { padding: 0.55rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.875rem; }
      &.full-width { grid-column: 1 / -1; }
    }
    .input-plate { font-family: monospace; font-size: 1.1rem; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 600; }
    .input-file { font-size: 0.85rem; }
    .file-hint { font-size: 0.75rem; color: #64748b; margin-top: 0.25rem; }
    .form-actions { margin-top: 1rem; display: flex; gap: 0.75rem; }
    .btn-primary {
      background: #0284c7; color: #fff; border: none; padding: 0.55rem 1.25rem; border-radius: 6px;
      font-size: 0.875rem; font-weight: 500; cursor: pointer;
      &:hover { background: #0369a1; }
      &:disabled { opacity: 0.5; cursor: not-allowed; }
    }
    .btn-detect { background: #7c3aed; &:hover { background: #6d28d9; } }
    .btn-process { background: #059669; &:hover { background: #047857; } }
    .cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1rem; }
    .camera-card {
      background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem;
      &.inactive { opacity: 0.6; border-color: #f1f5f9; }
    }
    .cam-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
    .cam-type-pill {
      font-size: 0.65rem; font-weight: 700; padding: 0.15rem 0.45rem; border-radius: 4px; letter-spacing: 0.05em;
      &.entrada { background: #dcfce7; color: #166534; }
      &.saida { background: #fee2e2; color: #991b1b; }
      &.ambos { background: #e0f2fe; color: #075985; }
    }
    .cam-id { font-weight: 600; font-size: 0.95rem; color: #0f172a; flex: 1; }
    .cam-status {
      font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px;
      &.online { background: #dcfce7; color: #166534; }
      &.offline { background: #fee2e2; color: #991b1b; }
    }
    .cam-details { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.75rem; }
    .cam-detail { font-size: 0.8rem; color: #475569; code { font-size: 0.75rem; background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; } }
    .cam-actions { display: flex; gap: 0.5rem; }
    .btn-sm { padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; border: 1px solid #cbd5e1; cursor: pointer; }
    .btn-toggle { background: #f8fafc; color: #475569; &:hover { background: #f1f5f9; } }
    .btn-delete { background: #fff; color: #dc2626; border-color: #fca5a5; &:hover { background: #fef2f2; } }
    .empty-state { grid-column: 1 / -1; text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.9rem; }
    .result-card {
      background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem; margin-top: 1.25rem;
      h4 { font-size: 1rem; font-weight: 600; color: #0f172a; margin: 0 0 1rem 0; }
    }
    .result-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
    .result-item {
      display: flex; flex-direction: column; gap: 0.25rem;
      .result-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
      .result-value { font-size: 1.1rem; font-weight: 600; color: #0f172a; }
      .plate-value { font-family: monospace; letter-spacing: 0.1em; font-size: 1.35rem; color: #0284c7; }
    }
    .event-badge {
      display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700;
      &.entrada { background: #dcfce7; color: #166534; }
      &.saida { background: #e0f2fe; color: #0369a1; }
      &.inconsistente { background: #fef3c7; color: #b45309; }
    }
    .metrics-grid {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem;
    }
    .metric-item {
      background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem;
      display: flex; flex-direction: column; align-items: center; text-align: center;
      .metric-val { font-size: 1.35rem; font-weight: 700; color: #0f172a; }
      .metric-label { font-size: 0.7rem; color: #64748b; margin-top: 0.2rem; }
      &.highlight { background: #eff6ff; border-color: #93c5fd; .metric-val { color: #1d4ed8; } }
    }
    .passages-section { margin-top: 1rem; h4 { margin-bottom: 0.75rem; } }
    .table-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow-x: auto; }
    .data-table {
      width: 100%; border-collapse: collapse; font-size: 0.85rem;
      th { background: #f8fafc; color: #475569; font-weight: 600; text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; }
      td { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
      tr:last-child td { border-bottom: none; }
    }
    .plate-cell { font-family: monospace; font-weight: 600; letter-spacing: 0.05em; }
  `]
})
export class AlprComponent implements OnInit {
  private api = inject(ApiService);

  activeTab: 'cameras' | 'detect' | 'video' = 'cameras';
  cameras: Camera[] = [];
  loading = false;
  processingVideo = false;
  successMessage = '';
  errorMessage = '';

  // Camera form
  showCameraForm = false;
  newCamera = { identificador: '', tipo: 'entrada', localizacao: '', rtsp_url: '' };

  // Detection form
  detectForm = { placa: '', camera_id: '', tipo_evento: 'auto', ocr_confidence: 0.95 };
  lastDetection: ALPRPassageEvent | null = null;

  // Video processing
  selectedVideoFile: File | null = null;
  videoPathInput = '';
  videoOpts = { camera_id: '', sentido_default: 'auto', max_frames: null as number | null };
  videoResult: ALPRProcessVideoResponse | null = null;

  ngOnInit(): void {
    this.loadCameras();
  }

  loadCameras(): void {
    this.api.getCameras().subscribe({
      next: (cams: Camera[]) => { this.cameras = cams; },
      error: () => { this.errorMessage = 'Erro ao carregar câmeras.'; }
    });
  }

  createCamera(): void {
    this.clearMessages();
    this.api.createCamera({
      identificador: this.newCamera.identificador,
      tipo: this.newCamera.tipo,
      localizacao: this.newCamera.localizacao || undefined,
      rtsp_url: this.newCamera.rtsp_url || undefined,
      ativa: true,
    }).subscribe({
      next: () => {
        this.successMessage = 'Câmera cadastrada com sucesso!';
        this.showCameraForm = false;
        this.newCamera = { identificador: '', tipo: 'entrada', localizacao: '', rtsp_url: '' };
        this.loadCameras();
      },
      error: (err: any) => { this.errorMessage = err.error?.detail || 'Erro ao cadastrar câmera.'; }
    });
  }

  toggleCamera(cam: Camera): void {
    this.clearMessages();
    this.api.updateCamera(cam.id, { ativa: !cam.ativa }).subscribe({
      next: () => {
        this.successMessage = `Câmera ${cam.identificador} ${cam.ativa ? 'desativada' : 'ativada'}.`;
        this.loadCameras();
      },
      error: (err: any) => { this.errorMessage = err.error?.detail || 'Erro ao atualizar câmera.'; }
    });
  }

  deleteCamera(cam: Camera): void {
    this.clearMessages();
    this.api.deleteCamera(cam.id).subscribe({
      next: () => {
        this.successMessage = `Câmera ${cam.identificador} removida.`;
        this.loadCameras();
      },
      error: (err: any) => { this.errorMessage = err.error?.detail || 'Erro ao remover câmera.'; }
    });
  }

  simulateDetection(): void {
    this.clearMessages();
    this.loading = true;
    this.lastDetection = null;
    this.api.alprSimulateDetection({
      placa: this.detectForm.placa,
      camera_id: this.detectForm.camera_id || undefined,
      tipo_evento: this.detectForm.tipo_evento,
      ocr_confidence: this.detectForm.ocr_confidence,
    }).subscribe({
      next: (res: ALPRPassageEvent) => {
        this.loading = false;
        this.lastDetection = res;
        this.successMessage = `Detecção processada: ${res.plate} → ${res.tipo_evento.toUpperCase()}`;
      },
      error: (err: any) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Erro ao processar detecção ALPR.';
      }
    });
  }

  onVideoFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedVideoFile = input.files[0];
      this.videoPathInput = '';
    }
  }

  processVideo(): void {
    this.clearMessages();
    this.processingVideo = true;
    this.videoResult = null;

    if (this.selectedVideoFile) {
      this.api.alprProcessVideoUpload(this.selectedVideoFile, {
        camera_id: this.videoOpts.camera_id || undefined,
        sentido_default: this.videoOpts.sentido_default,
        max_frames: this.videoOpts.max_frames ?? undefined,
      }).subscribe({
        next: (res: ALPRProcessVideoResponse) => { this.handleVideoResult(res); },
        error: (err: any) => { this.handleVideoError(err); }
      });
    } else if (this.videoPathInput) {
      this.api.alprProcessVideoByPath({
        video_path: this.videoPathInput,
        camera_id: this.videoOpts.camera_id || undefined,
        sentido_default: this.videoOpts.sentido_default,
        max_frames: this.videoOpts.max_frames ?? undefined,
      }).subscribe({
        next: (res: ALPRProcessVideoResponse) => { this.handleVideoResult(res); },
        error: (err: any) => { this.handleVideoError(err); }
      });
    }
  }

  private handleVideoResult(res: ALPRProcessVideoResponse): void {
    this.processingVideo = false;
    this.videoResult = res;
    this.successMessage = `Pipeline concluído: ${res.confirmed_passages_count} passagem(ns) confirmada(s), ${res.movements_registered} movimentação(ões) criada(s).`;
  }

  private handleVideoError(err: any): void {
    this.processingVideo = false;
    this.errorMessage = err.error?.detail || 'Erro ao processar vídeo no pipeline ALPR.';
  }

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
  }
}

