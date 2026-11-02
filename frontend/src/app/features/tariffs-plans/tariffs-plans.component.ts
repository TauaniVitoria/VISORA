import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-tariffs-plans',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="tariffs-page">
      <div class="page-header">
        <div>
          <h2>Planos e Tarifas</h2>
          <p class="subtitle">Configuração de precificação avulsa, regras de tolerância e planos de assinatura</p>
        </div>
      </div>

      <!-- Notification Banners -->
      <div class="notification-banner success" *ngIf="successMessage">{{ successMessage }}</div>
      <div class="notification-banner error" *ngIf="errorMessage">{{ errorMessage }}</div>

      <div class="grid-layout">
        <!-- Tarifa Avulsa Vigente -->
        <div class="card">
          <div class="card-header">
            <h3>Tarifação Avulsa (Horária / Diária)</h3>
            <span class="badge-active">Vigente</span>
          </div>

          <form (ngSubmit)="saveTariff()" class="form-tariff">
            <div class="form-group">
              <label>Descrição da Tabela</label>
              <input type="text" [(ngModel)]="tariffForm.descricao" name="descricao" class="form-control" />
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>1ª Hora (R$) *</label>
                <input type="number" step="0.5" [(ngModel)]="tariffForm.valor_primeira_hora" name="v_1h" required class="form-control" />
              </div>
              <div class="form-group flex-1">
                <label>Hora Adicional (R$) *</label>
                <input type="number" step="0.5" [(ngModel)]="tariffForm.valor_hora_adicional" name="v_h_add" required class="form-control" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group flex-1">
                <label>Diária Completa (R$) *</label>
                <input type="number" step="1.0" [(ngModel)]="tariffForm.valor_diaria" name="v_diaria" required class="form-control" />
              </div>
              <div class="form-group flex-1">
                <label>Tolerância Gratuita (Minutos)</label>
                <input type="number" [(ngModel)]="tariffForm.tolerancia_minutos" name="tolerancia" required class="form-control" />
              </div>
            </div>

            <button type="submit" class="btn-primary">Atualizar Tarifa Vigente</button>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .tariffs-page { padding: 1.5rem 2rem; }
    .page-header { margin-bottom: 1.5rem; }
    h2 { margin: 0; color: #0f172a; font-size: 1.5rem; font-weight: 700; }
    .subtitle { margin: 0.25rem 0 0; color: #64748b; font-size: 0.875rem; }
    .grid-layout {
      display: grid;
      grid-template-columns: 1fr;
      max-width: 680px;
      gap: 1.5rem;
    }
    .card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }
    .card-header h3 { margin: 0; font-size: 1.05rem; color: #0f172a; font-weight: 700; }
    .badge-active {
      background: #dcfce7;
      color: #15803d;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
    }
    .form-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
    .flex-1 { flex: 1; }
    .form-group label {
      display: block; font-size: 0.75rem; font-weight: 600; color: #475569; margin-bottom: 0.3rem;
    }
    .form-control {
      width: 100%; box-sizing: border-box; padding: 0.6rem 0.8rem;
      border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.875rem; outline: none;
    }
    .form-control:focus { border-color: #0284c7; }
    .btn-primary {
      background: #0284c7; color: white; border: none; padding: 0.65rem 1.25rem;
      border-radius: 8px; font-weight: 600; cursor: pointer; width: 100%; margin-top: 0.5rem;
    }
    .btn-primary:hover { background: #0369a1; }
    .notification-banner {
      padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.85rem;
    }
    .notification-banner.success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .notification-banner.error { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
  `],
})
export class TariffsPlansComponent implements OnInit {
  private api = inject(ApiService);

  tariffForm = {
    descricao: 'Tarifa Padrão Comercial',
    valor_primeira_hora: 15.0,
    valor_hora_adicional: 5.0,
    valor_diaria: 50.0,
    tolerancia_minutos: 15,
  };

  successMessage = '';
  errorMessage = '';

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.api.getActiveTariff().subscribe({
      next: (t) => {
        if (t) {
          this.tariffForm = {
            descricao: t.descricao,
            valor_primeira_hora: Number(t.valor_primeira_hora),
            valor_hora_adicional: Number(t.valor_hora_adicional),
            valor_diaria: Number(t.valor_diaria),
            tolerancia_minutos: t.tolerancia_minutos,
          };
        }
      },
      error: () => {},
    });
  }

  saveTariff(): void {
    this.clearMessages();
    this.api.createTariff(this.tariffForm).subscribe({
      next: () => {
        this.successMessage = 'Tabela de tarifas atualizada com sucesso!';
        this.loadData();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao atualizar tarifa.';
      },
    });
  }

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
  }
}
