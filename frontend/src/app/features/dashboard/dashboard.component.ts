import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { DashboardMetrics, Movimentacao } from '../../core/models/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="dashboard-page">
      <div class="page-header">
        <div>
          <h2>Dashboard Operacional</h2>
          <p class="subtitle">Monitoramento em tempo real do pátio e inteligência ALPR</p>
        </div>
        <button class="btn-refresh" (click)="loadData()">
          <span>Atualizar Dados</span>
        </button>
      </div>

      <!-- KPI Cards Grid -->
      <div class="kpi-grid">
        <div class="kpi-card highlight">
          <div class="kpi-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="4"></rect>
              <path d="M9 17V7h4a3 3 0 0 1 0 6H9"></path>
            </svg>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">Veículos Estacionados</span>
            <span class="kpi-value">{{ metrics?.veiculos_estacionados_agora ?? 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">Entradas Hoje</span>
            <span class="kpi-value text-green">{{ metrics?.entradas_hoje ?? 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2">
              <line x1="19" y1="12" x2="5" y2="12"></line>
              <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">Saídas Hoje</span>
            <span class="kpi-value text-blue">{{ metrics?.saidas_hoje ?? 0 }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
              <line x1="12" y1="1" x2="12" y2="23"></line>
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
            </svg>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">Receita Registrada</span>
            <span class="kpi-value text-emerald">R$ {{ (metrics?.receita_total_registrada ?? 0) | number:'1.2-2' }}</span>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </div>
          <div class="kpi-data">
            <span class="kpi-label">Cobranças Pendentes</span>
            <span class="kpi-value text-amber">R$ {{ (metrics?.cobrancas_pendentes_valor ?? 0) | number:'1.2-2' }}</span>
          </div>
        </div>
      </div>

      <!-- Quick Actions for ALPR / Manual Simulation -->
      <div class="actions-card">
        <h3>Ações Rápidas de Portaria e Reconhecimento ALPR</h3>
        <div class="actions-form">
          <div class="action-box">
            <label>Registrar Entrada (Veículo)</label>
            <div class="input-action-group">
              <input
                type="text"
                [(ngModel)]="entryPlate"
                placeholder="Ex: BRA2E19"
                class="plate-input"
                maxlength="10"
              />
              <button class="btn-action-in" (click)="onRegisterEntry()" [disabled]="!entryPlate">
                Registrar Entrada
              </button>
            </div>
          </div>

          <div class="action-box">
            <label>Registrar Saída (Cancela)</label>
            <div class="input-action-group">
              <input
                type="text"
                [(ngModel)]="exitPlate"
                placeholder="Ex: BRA2E19"
                class="plate-input"
                maxlength="10"
              />
              <button class="btn-action-out" (click)="onRegisterExit()" [disabled]="!exitPlate">
                Registrar Saída
              </button>
            </div>
          </div>
        </div>

        <div class="notification-banner success" *ngIf="actionSuccess">
          {{ actionSuccess }}
        </div>
        <div class="notification-banner error" *ngIf="actionError">
          {{ actionError }}
        </div>
      </div>

      <!-- Active Vehicles in Parking Table -->
      <div class="content-card">
        <div class="card-header">
          <h3>Veículos no Pátio (Permanência em Aberto)</h3>
          <span class="badge-count">{{ activeMovements.length }} veículos</span>
        </div>

        <div class="table-container" *ngIf="activeMovements.length > 0; else noVehicles">
          <table class="data-table">
            <thead>
              <tr>
                <th>Placa</th>
                <th>Tipo Cobrança</th>
                <th>Horário de Entrada</th>
                <th>Status</th>
                <th>Ação</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let m of activeMovements">
                <td>
                  <span class="plate-badge">{{ m.placa }}</span>
                </td>
                <td>
                  <span class="charge-type-badge" [ngClass]="m.tipo_cobranca || 'avulsa'">
                    {{ m.tipo_cobranca?.toUpperCase() || 'AVULSA' }}
                  </span>
                </td>
                <td>{{ m.entrada_em | date:'dd/MM/yyyy HH:mm:ss' }}</td>
                <td>
                  <span class="status-badge open">ABERTA</span>
                </td>
                <td>
                  <button class="btn-table-action" (click)="quickExit(m.placa)">
                    Dar Saída
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #noVehicles>
          <div class="empty-state">
            <p>Nenhum veículo estacionado no momento.</p>
          </div>
        </ng-template>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-page {
      padding: 1.5rem 2rem;
    }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
    }
    h2 {
      margin: 0;
      color: #0f172a;
      font-size: 1.5rem;
      font-weight: 700;
    }
    .subtitle {
      margin: 0.25rem 0 0;
      color: #64748b;
      font-size: 0.875rem;
    }
    .btn-refresh {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      color: #334155;
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.85rem;
      transition: all 0.2s;
    }
    .btn-refresh:hover {
      background: #e2e8f0;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 1.25rem;
      margin-bottom: 1.75rem;
    }
    .kpi-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.25rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-card.highlight {
      border-left: 4px solid #0284c7;
    }
    .kpi-icon {
      font-size: 2rem;
      background: #f8fafc;
      width: 50px;
      height: 50px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 10px;
    }
    .kpi-data {
      display: flex;
      flex-direction: column;
    }
    .kpi-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .kpi-value {
      font-size: 1.45rem;
      font-weight: 700;
      color: #0f172a;
      margin-top: 0.2rem;
    }
    .text-green { color: #16a34a; }
    .text-blue { color: #0284c7; }
    .text-emerald { color: #059669; }
    .text-amber { color: #d97706; }

    .actions-card, .content-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.5rem;
      margin-bottom: 1.75rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .actions-card h3, .content-card h3 {
      margin: 0 0 1rem;
      font-size: 1.05rem;
      font-weight: 700;
      color: #1e293b;
    }
    .actions-form {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 768px) {
      .actions-form { grid-template-columns: 1fr; }
    }
    .action-box label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: #475569;
      margin-bottom: 0.35rem;
    }
    .input-action-group {
      display: flex;
      gap: 0.5rem;
    }
    .plate-input {
      flex: 1;
      padding: 0.65rem 0.85rem;
      border: 2px solid #cbd5e1;
      border-radius: 8px;
      font-weight: 700;
      font-size: 1rem;
      text-transform: uppercase;
      outline: none;
      letter-spacing: 0.1em;
    }
    .plate-input:focus {
      border-color: #0284c7;
    }
    .btn-action-in {
      background: #16a34a;
      color: white;
      border: none;
      padding: 0 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-action-in:hover { background: #15803d; }
    .btn-action-out {
      background: #dc2626;
      color: white;
      border: none;
      padding: 0 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-action-out:hover { background: #b91c1c; }

    .notification-banner {
      margin-top: 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 500;
    }
    .notification-banner.success {
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #bbf7d0;
    }
    .notification-banner.error {
      background: #fee2e2;
      color: #b91c1c;
      border: 1px solid #fecaca;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .badge-count {
      background: #e0f2fe;
      color: #0369a1;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .table-container {
      overflow-x: auto;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }
    .data-table th {
      background: #f8fafc;
      color: #64748b;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .data-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid #f1f5f9;
      color: #1e293b;
      font-size: 0.875rem;
    }
    .plate-badge {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      font-weight: 700;
      letter-spacing: 0.05em;
    }
    .charge-type-badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }
    .charge-type-badge.plano {
      background: #dbeafe;
      color: #1d4ed8;
    }
    .charge-type-badge.avulsa {
      background: #fef3c7;
      color: #b45309;
    }
    .status-badge.open {
      background: #dcfce7;
      color: #15803d;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
    }
    .btn-table-action {
      background: #fee2e2;
      color: #dc2626;
      border: 1px solid #fca5a5;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .btn-table-action:hover {
      background: #fecaca;
    }
    .empty-state {
      padding: 2rem;
      text-align: center;
      color: #94a3b8;
      font-size: 0.9rem;
    }
  `],
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  metrics: DashboardMetrics | null = null;
  activeMovements: Movimentacao[] = [];

  entryPlate = '';
  exitPlate = '';
  actionSuccess = '';
  actionError = '';

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.api.getDashboardMetrics().subscribe({
      next: (m) => (this.metrics = m),
      error: () => {},
    });

    this.api.getActiveMovements().subscribe({
      next: (movs) => (this.activeMovements = movs),
      error: () => {},
    });
  }

  onRegisterEntry(): void {
    if (!this.entryPlate) return;
    this.clearNotifications();

    this.api.registerEntry({ placa: this.entryPlate }).subscribe({
      next: (mov) => {
        this.actionSuccess = `Entrada registrada com sucesso para o veículo placa ${mov.placa}!`;
        this.entryPlate = '';
        this.loadData();
      },
      error: (err) => {
        this.actionError = err.error?.detail || 'Erro ao registrar entrada.';
      },
    });
  }

  onRegisterExit(): void {
    if (!this.exitPlate) return;
    this.clearNotifications();

    this.api.registerExit({ placa: this.exitPlate }).subscribe({
      next: (mov) => {
        const val = mov.cobranca ? `R$ ${mov.cobranca.valor_liquido}` : 'R$ 0.00';
        this.actionSuccess = `Saída concluída para placa ${mov.placa}! Permanência: ${mov.permanencia_minutos} min. Valor: ${val}.`;
        this.exitPlate = '';
        this.loadData();
      },
      error: (err) => {
        this.actionError = err.error?.detail || 'Erro ao registrar saída.';
      },
    });
  }

  quickExit(placa: string): void {
    this.exitPlate = placa;
    this.onRegisterExit();
  }

  private clearNotifications(): void {
    this.actionSuccess = '';
    this.actionError = '';
  }
}
