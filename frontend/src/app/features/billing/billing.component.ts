import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Cobranca } from '../../core/models/models';

@Component({
  selector: 'app-billing',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="billing-page">
      <header class="page-header">
        <div>
          <h2>Gestão Financeira & Cobranças</h2>
          <p class="subtitle">Controle de receitas, títulos a receber e liquidação de pagamentos</p>
        </div>
      </header>

      <!-- KPI Summary Cards -->
      <div class="stats-grid">
        <div class="stat-card">
          <span class="stat-label">Total em Aberto</span>
          <span class="stat-value text-warning">{{ totalPendente | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
          <span class="stat-sub">{{ countPendente }} cobrança(s) pendente(s)</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Total Liquidado</span>
          <span class="stat-value text-success">{{ totalPago | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
          <span class="stat-sub">{{ countPago }} pagamento(s) confirmado(s)</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Total Geral Emitido</span>
          <span class="stat-value">{{ (totalPendente + totalPago) | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
          <span class="stat-sub">{{ charges.length }} registro(s)</span>
        </div>
      </div>

      <!-- Filters & Toolbar -->
      <div class="toolbar-card">
        <div class="filter-group">
          <label>Filtrar por Status:</label>
          <div class="pill-group">
            <button 
              type="button" 
              class="pill-btn" 
              [class.active]="selectedStatus === ''" 
              (click)="filterStatus('')">
              Todos ({{ charges.length }})
            </button>
            <button 
              type="button" 
              class="pill-btn" 
              [class.active]="selectedStatus === 'pendente'" 
              (click)="filterStatus('pendente')">
              Pendentes
            </button>
            <button 
              type="button" 
              class="pill-btn" 
              [class.active]="selectedStatus === 'pago'" 
              (click)="filterStatus('pago')">
              Pagos
            </button>
          </div>
        </div>
        <button class="btn-refresh" (click)="loadCharges()">Atualizar</button>
      </div>

      <!-- Messages -->
      <div *ngIf="successMessage" class="alert alert-success">{{ successMessage }}</div>
      <div *ngIf="errorMessage" class="alert alert-danger">{{ errorMessage }}</div>

      <!-- Charges Table -->
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID da Cobrança</th>
              <th>Emissão</th>
              <th>Vencimento</th>
              <th>Valor Bruto</th>
              <th>Desconto</th>
              <th>Valor Líquido</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let charge of filteredCharges">
              <td class="font-mono text-xs">{{ charge.id.substring(0, 8) }}...</td>
              <td>{{ charge.criado_em | date:'dd/MM/yyyy HH:mm' }}</td>
              <td>{{ charge.data_vencimento | date:'dd/MM/yyyy' }}</td>
              <td>{{ charge.valor_bruto | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
              <td>{{ charge.desconto | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
              <td class="font-bold">{{ charge.valor_liquido | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
              <td>
                <span class="status-badge" [ngClass]="charge.status">
                  {{ charge.status | uppercase }}
                </span>
              </td>
              <td>
                <button 
                  *ngIf="charge.status === 'pendente'" 
                  class="btn-pay" 
                  (click)="openPaymentModal(charge)">
                  Liquidar
                </button>
                <span *ngIf="charge.status === 'pago'" class="text-muted text-xs">Liquidado</span>
              </td>
            </tr>
            <tr *ngIf="filteredCharges.length === 0">
              <td colspan="8" class="text-center py-6 text-muted">Nenhuma cobrança localizada.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Payment Registration Modal -->
      <div *ngIf="showModal" class="modal-backdrop">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Registrar Pagamento</h3>
            <button class="btn-close" (click)="closeModal()">×</button>
          </div>
          <form (ngSubmit)="submitPayment()" class="modal-body">
            <div class="form-group">
              <label>ID da Cobrança</label>
              <input type="text" [value]="selectedCharge?.id" disabled class="input-disabled" />
            </div>

            <div class="form-group">
              <label>Valor a Liquidar (R$)</label>
              <input 
                type="number" 
                step="0.01" 
                [(ngModel)]="paymentData.valor_pago" 
                name="valor_pago" 
                required />
            </div>

            <div class="form-group">
              <label>Método de Pagamento</label>
              <select [(ngModel)]="paymentData.metodo" name="metodo" required>
                <option value="pix">PIX (Instantâneo)</option>
                <option value="dinheiro">Dinheiro em Espécie</option>
                <option value="cartao_credito">Cartão de Crédito</option>
                <option value="cartao_debito">Cartão de Débito</option>
                <option value="boleto">Boleto Bancário</option>
              </select>
            </div>

            <div class="form-group">
              <label>Identificador / Comprovante (Opcional)</label>
              <input 
                type="text" 
                [(ngModel)]="paymentData.comprovante_transacao" 
                name="comprovante" 
                placeholder="Ex: NSU 984920 ou ID Pix" />
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="closeModal()">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="loading">
                {{ loading ? 'Processando...' : 'Confirmar Recebimento' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .billing-page {
      padding: 1.5rem;
      max-width: 1300px;
      margin: 0 auto;
    }
    .page-header {
      margin-bottom: 1.5rem;
      h2 { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin: 0; }
      .subtitle { color: #64748b; margin-top: 0.25rem; font-size: 0.875rem; }
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1.25rem;
      margin-bottom: 1.5rem;
    }
    .stat-card {
      background: #ffffff;
      padding: 1.25rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      display: flex;
      flex-direction: column;
      .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
      .stat-value { font-size: 1.75rem; font-weight: 700; color: #0f172a; margin: 0.25rem 0; }
      .stat-sub { font-size: 0.8rem; color: #94a3b8; }
      .text-warning { color: #d97706; }
      .text-success { color: #16a34a; }
    }
    .toolbar-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 1rem 1.25rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .filter-group {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      label { font-size: 0.875rem; color: #475569; font-weight: 500; }
    }
    .pill-group {
      display: flex;
      gap: 0.5rem;
    }
    .pill-btn {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      border-radius: 9999px;
      padding: 0.35rem 0.85rem;
      font-size: 0.8rem;
      cursor: pointer;
      color: #475569;
      font-weight: 500;
      &.active {
        background: #0284c7;
        color: #ffffff;
        border-color: #0284c7;
      }
    }
    .btn-refresh {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      padding: 0.45rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      color: #334155;
      cursor: pointer;
      &:hover { background: #f8fafc; }
    }
    .table-card {
      background: #ffffff;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      overflow-x: auto;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
      th {
        background: #f8fafc;
        color: #475569;
        font-weight: 600;
        text-align: left;
        padding: 0.85rem 1rem;
        border-bottom: 1px solid #e2e8f0;
      }
      td {
        padding: 0.85rem 1rem;
        border-bottom: 1px solid #f1f5f9;
        color: #1e293b;
      }
      tr:last-child td { border-bottom: none; }
    }
    .font-mono { font-family: monospace; }
    .text-xs { font-size: 0.75rem; }
    .font-bold { font-weight: 600; }
    .status-badge {
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      &.pendente { background: #fef3c7; color: #b45309; }
      &.pago { background: #dcfce7; color: #15803d; }
      &.cancelado { background: #fee2e2; color: #b91c1c; }
      &.estornado { background: #e0e7ff; color: #4338ca; }
    }
    .btn-pay {
      background: #0284c7;
      color: #ffffff;
      border: none;
      padding: 0.35rem 0.75rem;
      border-radius: 4px;
      font-size: 0.8rem;
      cursor: pointer;
      font-weight: 500;
      &:hover { background: #0369a1; }
    }
    .alert {
      padding: 0.75rem 1rem;
      border-radius: 6px;
      margin-bottom: 1rem;
      font-size: 0.875rem;
      &.alert-success { background: #dcfce7; color: #166534; }
      &.alert-danger { background: #fee2e2; color: #991b1b; }
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 50;
      padding: 1rem;
    }
    .modal-card {
      background: #ffffff;
      border-radius: 8px;
      max-width: 480px;
      width: 100%;
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
      overflow: hidden;
    }
    .modal-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      h3 { margin: 0; font-size: 1.15rem; color: #0f172a; }
      .btn-close { background: none; border: none; font-size: 1.25rem; cursor: pointer; color: #64748b; }
    }
    .modal-body {
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      label { font-size: 0.85rem; font-weight: 500; color: #334155; }
      input, select {
        padding: 0.55rem 0.75rem;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        font-size: 0.9rem;
      }
      .input-disabled { background: #f8fafc; color: #64748b; }
    }
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 0.5rem;
    }
    .btn-secondary {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
    }
    .btn-primary {
      background: #16a34a;
      color: #ffffff;
      border: none;
      padding: 0.5rem 1.2rem;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 500;
      font-size: 0.875rem;
      &:hover { background: #15803d; }
      &:disabled { opacity: 0.6; cursor: not-allowed; }
    }
  `]
})
export class BillingComponent implements OnInit {
  charges: Cobranca[] = [];
  filteredCharges: Cobranca[] = [];
  selectedStatus: string = '';

  totalPendente = 0;
  totalPago = 0;
  countPendente = 0;
  countPago = 0;

  showModal = false;
  selectedCharge: Cobranca | null = null;
  paymentData = {
    valor_pago: 0,
    metodo: 'pix',
    comprovante_transacao: ''
  };

  loading = false;
  successMessage = '';
  errorMessage = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadCharges();
  }

  loadCharges(): void {
    this.api.getCharges().subscribe({
      next: (data) => {
        this.charges = data;
        this.computeStats();
        this.applyFilter();
      },
      error: (err) => {
        this.errorMessage = 'Erro ao carregar lista de cobranças.';
      }
    });
  }

  computeStats(): void {
    this.totalPendente = 0;
    this.totalPago = 0;
    this.countPendente = 0;
    this.countPago = 0;

    for (const c of this.charges) {
      if (c.status === 'pendente') {
        this.totalPendente += Number(c.valor_liquido);
        this.countPendente++;
      } else if (c.status === 'pago') {
        this.totalPago += Number(c.valor_liquido);
        this.countPago++;
      }
    }
  }

  filterStatus(status: string): void {
    this.selectedStatus = status;
    this.applyFilter();
  }

  applyFilter(): void {
    if (!this.selectedStatus) {
      this.filteredCharges = [...this.charges];
    } else {
      this.filteredCharges = this.charges.filter(c => c.status === this.selectedStatus);
    }
  }

  openPaymentModal(charge: Cobranca): void {
    this.selectedCharge = charge;
    this.paymentData = {
      valor_pago: Number(charge.valor_liquido),
      metodo: 'pix',
      comprovante_transacao: ''
    };
    this.showModal = true;
    this.successMessage = '';
    this.errorMessage = '';
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedCharge = null;
  }

  submitPayment(): void {
    if (!this.selectedCharge) return;

    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.api.registerPayment({
      cobranca_id: this.selectedCharge.id,
      valor_pago: this.paymentData.valor_pago,
      metodo: this.paymentData.metodo,
      comprovante_transacao: this.paymentData.comprovante_transacao || undefined
    }).subscribe({
      next: () => {
        this.loading = false;
        this.successMessage = 'Pagamento registrado e cobrança liquidada com sucesso!';
        this.closeModal();
        this.loadCharges();
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Erro ao registrar liquidação do pagamento.';
      }
    });
  }
}
