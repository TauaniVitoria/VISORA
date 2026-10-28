import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Movimentacao } from '../../core/models/models';

@Component({
  selector: 'app-movements',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="movements-page">
      <div class="page-header">
        <div>
          <h2>Histórico de Movimentações ALPR</h2>
          <p class="subtitle">Auditoria de passagens capturadas pelas câmeras, tempos de permanência e bilhetagem</p>
        </div>
      </div>

      <!-- Filters Bar -->
      <div class="filter-card">
        <div class="filter-group">
          <label>Buscar por Placa</label>
          <input
            type="text"
            [(ngModel)]="plateFilter"
            placeholder="Ex: BRA2E19"
            class="form-control uppercase"
            (keyup.enter)="loadHistory()"
          />
        </div>

        <div class="filter-group">
          <label>Filtrar por Status</label>
          <select [(ngModel)]="statusFilter" (change)="loadHistory()" class="form-control">
            <option value="">Todos os Status</option>
            <option value="aberta">Aberta</option>
            <option value="concluida">Concluída</option>
            <option value="inconsistente">Inconsistente</option>
          </select>
        </div>

        <button class="btn-filter" (click)="loadHistory()">Filtrar</button>
      </div>

      <!-- Notification Banners -->
      <div class="notification-banner success" *ngIf="successMessage">{{ successMessage }}</div>
      <div class="notification-banner error" *ngIf="errorMessage">{{ errorMessage }}</div>

      <!-- Table Card -->
      <div class="content-card">
        <div class="table-container" *ngIf="movements.length > 0; else emptyState">
          <table class="data-table">
            <thead>
              <tr>
                <th>Placa</th>
                <th>Entrada</th>
                <th>Saída</th>
                <th>Permanência</th>
                <th>Tipo</th>
                <th>Valor Devido</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let m of movements">
                <td>
                  <span class="plate-badge">{{ m.placa }}</span>
                </td>
                <td>{{ m.entrada_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>{{ m.saida_em ? (m.saida_em | date:'dd/MM/yyyy HH:mm') : '—' }}</td>
                <td>{{ m.permanencia_minutos !== null && m.permanencia_minutos !== undefined ? m.permanencia_minutos + ' min' : 'Em curso' }}</td>
                <td>
                  <span class="charge-type-badge" [ngClass]="m.tipo_cobranca || 'avulsa'">
                    {{ m.tipo_cobranca?.toUpperCase() || 'AVULSA' }}
                  </span>
                </td>
                <td>
                  <strong>R$ {{ (m.cobranca?.valor_liquido ?? 0) | number:'1.2-2' }}</strong>
                </td>
                <td>
                  <span class="status-badge" [ngClass]="m.status">
                    {{ m.status.toUpperCase() }}
                  </span>
                </td>
                <td>
                  <button class="btn-action-edit" (click)="openCorrectionModal(m)">
                    Corrigir
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #emptyState>
          <div class="empty-state">
            Nenhuma movimentação localizada com os filtros selecionados.
          </div>
        </ng-template>
      </div>

      <!-- Modal de Correção Manual com Registro de Auditoria -->
      <div class="modal-backdrop" *ngIf="showCorrectionModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Correção Manual com Auditoria</h3>
            <button class="btn-close" (click)="showCorrectionModal = false">✕</button>
          </div>

          <form (ngSubmit)="saveCorrection()">
            <div class="modal-body">
              <p class="audit-warning">
                ⚠️ Qualquer alteração manual nesta movimentação será permanentemente registrada na tabela de auditoria com seu usuário e IP.
              </p>

              <div class="form-group">
                <label>Placa Corrigida *</label>
                <input
                  type="text"
                  [(ngModel)]="correctionForm.placa"
                  name="c_placa"
                  required
                  class="form-control uppercase"
                  maxlength="10"
                />
              </div>

              <div class="form-group">
                <label>Status</label>
                <select [(ngModel)]="correctionForm.status" name="c_status" class="form-control">
                  <option value="aberta">Aberta</option>
                  <option value="concluida">Concluída</option>
                  <option value="inconsistente">Inconsistente</option>
                  <option value="cancelada">Cancelada</option>
                </select>
              </div>

              <div class="form-group">
                <label>Justificativa Obrigatória *</label>
                <textarea
                  [(ngModel)]="correctionForm.observacao"
                  name="c_obs"
                  required
                  rows="3"
                  class="form-control"
                  placeholder="Explique o motivo da correção (ex: 'Reflexo no leitor OCR causou leitura incorreta de B como 8')..."
                ></textarea>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="showCorrectionModal = false">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="!correctionForm.observacao">Salvar Correção</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .movements-page { padding: 1.5rem 2rem; }
    .page-header { margin-bottom: 1.5rem; }
    h2 { margin: 0; color: #0f172a; font-size: 1.5rem; font-weight: 700; }
    .subtitle { margin: 0.25rem 0 0; color: #64748b; font-size: 0.875rem; }
    .filter-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 1rem 1.25rem;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: flex-end;
      gap: 1.25rem;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .filter-group { flex: 1; max-width: 280px; }
    .filter-group label {
      display: block; font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 0.3rem;
    }
    .form-control {
      width: 100%; box-sizing: border-box; padding: 0.55rem 0.75rem;
      border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.85rem; outline: none;
    }
    .uppercase { text-transform: uppercase; }
    .btn-filter {
      background: #0284c7; color: white; border: none; padding: 0.6rem 1.25rem;
      border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 0.85rem;
    }
    .content-card {
      background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
      padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .data-table { width: 100%; border-collapse: collapse; text-align: left; }
    .data-table th {
      background: #f8fafc; color: #64748b; font-size: 0.75rem; font-weight: 700;
      text-transform: uppercase; padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0;
    }
    .data-table td {
      padding: 0.85rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.875rem; color: #1e293b;
    }
    .plate-badge {
      background: #f1f5f9; border: 1px solid #cbd5e1; padding: 0.2rem 0.5rem;
      border-radius: 6px; font-weight: 700; font-family: monospace;
    }
    .charge-type-badge { font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 4px; }
    .charge-type-badge.plano { background: #dbeafe; color: #1d4ed8; }
    .charge-type-badge.avulsa { background: #fef3c7; color: #b45309; }
    .status-badge { font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 4px; }
    .status-badge.aberta { background: #dcfce7; color: #15803d; }
    .status-badge.concluida { background: #f1f5f9; color: #475569; }
    .status-badge.inconsistente { background: #fee2e2; color: #b91c1c; }
    .status-badge.cancelada { background: #f3f4f6; color: #9ca3af; }
    .btn-action-edit {
      background: #f1f5f9; border: 1px solid #cbd5e1; color: #0284c7;
      padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; cursor: pointer;
    }
    .btn-action-edit:hover { background: #e0f2fe; }

    /* Modais */
    .modal-backdrop {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.6); display: flex; align-items: center; justify-content: center; z-index: 1000;
    }
    .modal-content {
      background: #ffffff; border-radius: 12px; width: 100%; max-width: 500px; overflow: hidden;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    }
    .modal-header {
      display: flex; justify-content: space-between; align-items: center; padding: 1.25rem; border-bottom: 1px solid #e2e8f0;
    }
    .modal-header h3 { margin: 0; font-size: 1.1rem; color: #0f172a; }
    .btn-close { background: none; border: none; font-size: 1.2rem; cursor: pointer; color: #64748b; }
    .modal-body { padding: 1.25rem; }
    .audit-warning {
      background: #fef3c7; border: 1px solid #fde68a; color: #92400e;
      padding: 0.75rem; border-radius: 6px; font-size: 0.8rem; margin: 0 0 1rem;
    }
    .form-group { margin-bottom: 1rem; }
    .form-group label { display: block; font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 0.25rem; }
    .modal-footer {
      padding: 1rem 1.25rem; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 0.75rem; background: #f8fafc;
    }
    .btn-primary {
      background: #0284c7; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 6px; font-weight: 600; cursor: pointer;
    }
    .btn-secondary {
      background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; padding: 0.55rem 1.2rem; border-radius: 6px; font-weight: 600; cursor: pointer;
    }
    .notification-banner {
      padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.85rem;
    }
    .notification-banner.success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .notification-banner.error { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
    .empty-state { padding: 3rem; text-align: center; color: #94a3b8; }
  `],
})
export class MovementsComponent implements OnInit {
  private api = inject(ApiService);

  movements: Movimentacao[] = [];
  plateFilter = '';
  statusFilter = '';

  showCorrectionModal = false;
  selectedMovement: Movimentacao | null = null;
  correctionForm = {
    placa: '',
    status: 'aberta',
    observacao: '',
  };

  successMessage = '';
  errorMessage = '';

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.api
      .getMovementsHistory({
        placa: this.plateFilter || undefined,
        status_filter: this.statusFilter || undefined,
      })
      .subscribe({
        next: (res) => (this.movements = res),
        error: () => {},
      });
  }

  openCorrectionModal(m: Movimentacao): void {
    this.clearMessages();
    this.selectedMovement = m;
    this.correctionForm = {
      placa: m.placa,
      status: m.status,
      observacao: '',
    };
    this.showCorrectionModal = true;
  }

  saveCorrection(): void {
    if (!this.selectedMovement || !this.correctionForm.observacao) return;
    this.clearMessages();

    this.api.manualCorrection(this.selectedMovement.id, this.correctionForm).subscribe({
      next: (m) => {
        this.successMessage = `Movimentação da placa ${m.placa} corrigida com sucesso e auditada!`;
        this.showCorrectionModal = false;
        this.loadHistory();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao salvar correção manual.';
      },
    });
  }

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
  }
}
