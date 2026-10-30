import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../core/services/api.service';
import {
  Cobranca,
  Pagamento,
  Plano,
  PortalAssinatura,
  PortalMovimentacao,
  PortalPerfil,
  PortalResumo,
} from '../../core/models/models';

type Tab = 'resumo' | 'veiculos' | 'historico' | 'planos' | 'financeiro';

@Component({
  selector: 'app-portal',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="portal">
      <header class="page-header">
        <h2>Olá, {{ perfil?.nome || 'cliente' }}</h2>
        <p class="subtitle" *ngIf="perfil">
          {{ perfil.estacionamento }} · {{ perfil.tipo_documento }} {{ perfil.documento_mascarado }}
        </p>
      </header>

      <div class="alert" *ngIf="errorMessage">{{ errorMessage }}</div>

      <nav class="tabs">
        <button *ngFor="let t of tabs" class="tab" [class.active]="tab === t.key" (click)="select(t.key)">
          {{ t.label }}
        </button>
      </nav>

      <!-- RESUMO -->
      <section *ngIf="tab === 'resumo' && resumo">
        <div class="kpis">
          <div class="kpi"><span class="kpi-value">{{ resumo.veiculos_cadastrados }}</span><span>Veículos</span></div>
          <div class="kpi"><span class="kpi-value">{{ resumo.veiculos_estacionados.length }}</span><span>No estacionamento agora</span></div>
          <div class="kpi"><span class="kpi-value">{{ resumo.assinaturas_ativas }}</span><span>Planos ativos</span></div>
          <div class="kpi warn">
            <span class="kpi-value">{{ resumo.cobrancas_pendentes_valor | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</span>
            <span>{{ resumo.cobrancas_pendentes_quantidade }} cobrança(s) pendente(s)</span>
          </div>
        </div>

        <h3>Veículos no estacionamento agora</h3>
        <div class="table-card" *ngIf="resumo.veiculos_estacionados.length; else nobody">
          <table>
            <thead><tr><th>Placa</th><th>Entrada</th><th>Permanência</th></tr></thead>
            <tbody>
              <tr *ngFor="let m of resumo.veiculos_estacionados">
                <td class="plate">{{ m.placa }}</td>
                <td>{{ m.entrada_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>{{ duration(m.permanencia_minutos) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #nobody><p class="empty">Nenhum dos seus veículos está no estacionamento agora.</p></ng-template>
      </section>

      <!-- VEÍCULOS -->
      <section *ngIf="tab === 'veiculos' && perfil">
        <div class="table-card" *ngIf="perfil.veiculos.length; else noVehicles">
          <table>
            <thead><tr><th>Placa</th><th>Marca / Modelo</th><th>Cor</th><th>Tipo</th><th>Situação</th></tr></thead>
            <tbody>
              <tr *ngFor="let v of perfil.veiculos">
                <td class="plate">{{ v.placa }}</td>
                <td>{{ v.marca || '—' }} {{ v.modelo || '' }}</td>
                <td>{{ v.cor || '—' }}</td>
                <td>{{ v.tipo | titlecase }}</td>
                <td><span class="badge" [class.ok]="v.ativo">{{ v.ativo ? 'Ativo' : 'Inativo' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #noVehicles><p class="empty">Nenhum veículo cadastrado.</p></ng-template>
        <p class="hint">Para incluir ou alterar veículos, fale com a administração do estacionamento.</p>
      </section>

      <!-- HISTÓRICO -->
      <section *ngIf="tab === 'historico'">
        <div class="table-card" *ngIf="movements.length; else noMovs">
          <table>
            <thead>
              <tr><th>Placa</th><th>Entrada</th><th>Saída</th><th>Permanência</th><th>Situação</th><th>Valor</th></tr>
            </thead>
            <tbody>
              <tr *ngFor="let m of movements">
                <td class="plate">{{ m.placa }}</td>
                <td>{{ m.entrada_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>{{ m.saida_em ? (m.saida_em | date:'dd/MM/yyyy HH:mm') : '—' }}</td>
                <td>{{ duration(m.permanencia_minutos) }}<small *ngIf="m.em_andamento"> (em andamento)</small></td>
                <td><span class="badge" [ngClass]="m.status">{{ statusLabel(m.status) }}</span></td>
                <td>
                  <ng-container *ngIf="m.cobranca; else planOrNone">
                    {{ m.cobranca.valor_liquido | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
                  </ng-container>
                  <ng-template #planOrNone>{{ m.tipo_cobranca === 'plano' ? 'Incluso no plano' : '—' }}</ng-template>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #noMovs><p class="empty">Nenhuma passagem registrada.</p></ng-template>
      </section>

      <!-- PLANOS -->
      <section *ngIf="tab === 'planos'">
        <h3>Minhas assinaturas</h3>
        <div class="table-card" *ngIf="subscriptions.length; else noSubs">
          <table>
            <thead><tr><th>Plano</th><th>Veículos</th><th>Vigência</th><th>Valor</th><th>Situação</th></tr></thead>
            <tbody>
              <tr *ngFor="let s of subscriptions">
                <td>{{ s.plano_nome }} <small>({{ s.tipo_recorrencia }})</small></td>
                <td class="plate">{{ s.placas.join(', ') || '—' }}</td>
                <td>{{ s.data_inicio | date:'dd/MM/yyyy' }} a {{ s.data_fim | date:'dd/MM/yyyy' }}</td>
                <td>{{ s.valor_total | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
                <td><span class="badge" [class.ok]="s.status === 'ativa'">{{ s.status | titlecase }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #noSubs><p class="empty">Você não possui assinaturas.</p></ng-template>

        <h3>Planos disponíveis</h3>
        <div class="plans" *ngIf="plans.length; else noPlans">
          <div class="plan" *ngFor="let p of plans">
            <strong>{{ p.nome }}</strong>
            <span class="price">{{ p.valor_base | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}
              <small>/{{ p.tipo_recorrencia === 'anual' ? 'ano' : 'mês' }}</small></span>
            <small>Até {{ p.limite_veiculos }} veículo(s)</small>
            <small *ngIf="p.descricao">{{ p.descricao }}</small>
          </div>
        </div>
        <ng-template #noPlans><p class="empty">Nenhum plano disponível no momento.</p></ng-template>
        <p class="hint">Para contratar ou alterar um plano, fale com a administração do estacionamento.</p>
      </section>

      <!-- FINANCEIRO -->
      <section *ngIf="tab === 'financeiro'">
        <h3>Cobranças</h3>
        <div class="table-card" *ngIf="charges.length; else noCharges">
          <table>
            <thead><tr><th>Emissão</th><th>Vencimento</th><th>Valor</th><th>Situação</th></tr></thead>
            <tbody>
              <tr *ngFor="let c of charges">
                <td>{{ c.criado_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>{{ c.data_vencimento | date:'dd/MM/yyyy' }}</td>
                <td>{{ c.valor_liquido | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
                <td><span class="badge" [ngClass]="c.status">{{ c.status | titlecase }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #noCharges><p class="empty">Nenhuma cobrança.</p></ng-template>

        <h3>Pagamentos</h3>
        <div class="table-card" *ngIf="payments.length; else noPayments">
          <table>
            <thead><tr><th>Data</th><th>Valor</th><th>Forma</th><th>Comprovante</th></tr></thead>
            <tbody>
              <tr *ngFor="let p of payments">
                <td>{{ p.pago_em | date:'dd/MM/yyyy HH:mm' }}</td>
                <td>{{ p.valor_pago | currency:'BRL':'symbol':'1.2-2':'pt-BR' }}</td>
                <td>{{ methodLabel(p.metodo) }}</td>
                <td>{{ p.comprovante_transacao || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <ng-template #noPayments><p class="empty">Nenhum pagamento registrado.</p></ng-template>
        <p class="hint">Os pagamentos são registrados pela administração do estacionamento.</p>
      </section>

      <p class="loading" *ngIf="loading">Carregando...</p>
    </div>
  `,
  styles: [`
    .portal { padding: 1.5rem 2rem; max-width: 1100px; margin: 0 auto; }
    .page-header h2 { margin: 0; color: #0f172a; font-size: 1.5rem; }
    .subtitle { margin: 0.25rem 0 1.25rem; color: #64748b; font-size: 0.875rem; }
    .alert { background: #fee2e2; color: #991b1b; padding: 0.7rem 1rem; border-radius: 8px; margin-bottom: 1rem; }
    .tabs { display: flex; gap: 0.25rem; flex-wrap: wrap; border-bottom: 2px solid #e2e8f0; margin-bottom: 1.25rem; }
    .tab { background: none; border: none; padding: 0.65rem 1.1rem; color: #64748b; font-weight: 500;
      border-bottom: 3px solid transparent; margin-bottom: -2px; cursor: pointer; }
    .tab.active { color: #0284c7; border-bottom-color: #0284c7; }
    h3 { font-size: 1.05rem; color: #1e293b; margin: 1.5rem 0 0.75rem; }
    .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
    .kpi { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;
      display: flex; flex-direction: column; gap: 0.25rem; color: #64748b; font-size: 0.8rem; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: #0f172a; }
    .kpi.warn .kpi-value { color: #b45309; }
    .table-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th { background: #f8fafc; color: #475569; text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid #e2e8f0; }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
    tr:last-child td { border-bottom: none; }
    .plate { font-family: monospace; font-weight: 600; letter-spacing: 0.05em; }
    .badge { display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.75rem;
      font-weight: 600; background: #f1f5f9; color: #475569; }
    .badge.ok, .badge.pago, .badge.concluida { background: #dcfce7; color: #166534; }
    .badge.pendente, .badge.aberta { background: #fef3c7; color: #b45309; }
    .badge.cancelado, .badge.estornado, .badge.inconsistente { background: #fee2e2; color: #991b1b; }
    .plans { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 1rem; }
    .plan { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem;
      display: flex; flex-direction: column; gap: 0.3rem; }
    .price { font-size: 1.3rem; font-weight: 700; color: #0284c7; }
    .empty, .hint, .loading { color: #94a3b8; font-size: 0.875rem; }
    .hint { margin-top: 1rem; }
  `],
})
export class PortalComponent implements OnInit {
  private api = inject(ApiService);

  readonly tabs: { key: Tab; label: string }[] = [
    { key: 'resumo', label: 'Resumo' },
    { key: 'veiculos', label: 'Meus veículos' },
    { key: 'historico', label: 'Entradas e saídas' },
    { key: 'planos', label: 'Planos' },
    { key: 'financeiro', label: 'Cobranças e pagamentos' },
  ];

  tab: Tab = 'resumo';
  loading = false;
  errorMessage = '';

  perfil: PortalPerfil | null = null;
  resumo: PortalResumo | null = null;
  movements: PortalMovimentacao[] = [];
  subscriptions: PortalAssinatura[] = [];
  plans: Plano[] = [];
  charges: Cobranca[] = [];
  payments: Pagamento[] = [];

  ngOnInit(): void {
    this.api.getPortalProfile().subscribe({
      next: (p) => (this.perfil = p),
      error: () => this.fail('Não foi possível carregar o seu perfil.'),
    });
    this.select('resumo');
  }

  select(tab: Tab): void {
    this.tab = tab;
    this.errorMessage = '';
    this.loading = true;
    const done = () => (this.loading = false);
    const fail = () => {
      this.loading = false;
      this.fail('Não foi possível carregar os dados. Tente novamente.');
    };

    switch (tab) {
      case 'resumo':
        this.api.getPortalSummary().subscribe({ next: (r) => { this.resumo = r; done(); }, error: fail });
        break;
      case 'veiculos':
        this.api.getPortalProfile().subscribe({ next: (p) => { this.perfil = p; done(); }, error: fail });
        break;
      case 'historico':
        this.api.getPortalMovements().subscribe({ next: (m) => { this.movements = m; done(); }, error: fail });
        break;
      case 'planos':
        this.api.getPortalSubscriptions().subscribe({
          next: (s) => {
            this.subscriptions = s;
            this.api.getPortalPlans().subscribe({ next: (p) => { this.plans = p; done(); }, error: fail });
          },
          error: fail,
        });
        break;
      case 'financeiro':
        this.api.getPortalCharges().subscribe({
          next: (c) => {
            this.charges = c;
            this.api.getPortalPayments().subscribe({ next: (p) => { this.payments = p; done(); }, error: fail });
          },
          error: fail,
        });
        break;
    }
  }

  duration(minutes?: number | null): string {
    if (minutes === undefined || minutes === null) return '—';
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return h > 0 ? `${h}h ${m.toString().padStart(2, '0')}min` : `${m}min`;
  }

  statusLabel(status: string): string {
    const labels: Record<string, string> = {
      aberta: 'No estacionamento',
      concluida: 'Concluída',
      inconsistente: 'Em verificação',
      cancelada: 'Cancelada',
    };
    return labels[status] ?? status;
  }

  methodLabel(method: string): string {
    const labels: Record<string, string> = {
      pix: 'Pix',
      dinheiro: 'Dinheiro',
      cartao_credito: 'Cartão de crédito',
      cartao_debito: 'Cartão de débito',
      boleto: 'Boleto',
    };
    return labels[method] ?? method;
  }

  private fail(message: string): void {
    this.errorMessage = message;
  }
}
