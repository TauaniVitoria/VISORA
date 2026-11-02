import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Cliente, ClienteMovimentacao, Veiculo } from '../../core/models/models';

type SortColumn = 'codigo' | 'nome' | 'telefone' | 'plano_tipo' | 'veiculos';
type SortDirection = 'asc' | 'desc';

@Component({
  selector: 'app-customers',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="customers-page">
      <div class="page-header">
        <div>
          <h2>Gestão de Clientes e Veículos</h2>
          <p class="subtitle">Controle de motoristas, planos de contratação e histórico operacional</p>
        </div>
        <button class="btn-primary" (click)="openNewCustomerModal()">
          <span>+ Novo Cliente</span>
        </button>
      </div>

      <!-- Search & Filters -->
      <div class="filter-bar">
        <input
          type="text"
          [(ngModel)]="searchQuery"
          placeholder="Buscar por código, nome, telefone, plano ou placa..."
          class="search-input"
        />
      </div>

      <!-- Notification Banners -->
      <div class="notification-banner success" *ngIf="successMessage">
        {{ successMessage }}
      </div>
      <div class="notification-banner error" *ngIf="errorMessage">
        {{ errorMessage }}
      </div>

      <!-- Customers Table -->
      <div class="content-card">
        <div class="table-container" *ngIf="filteredCustomers.length > 0; else emptyState">
          <table class="data-table">
            <thead>
              <tr>
                <th (click)="setSort('codigo')" class="sortable-th">
                  Código
                  <span class="sort-indicator" *ngIf="sortColumn === 'codigo'">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th (click)="setSort('nome')" class="sortable-th">
                  Nome
                  <span class="sort-indicator" *ngIf="sortColumn === 'nome'">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th (click)="setSort('telefone')" class="sortable-th">
                  Telefone
                  <span class="sort-indicator" *ngIf="sortColumn === 'telefone'">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th (click)="setSort('plano_tipo')" class="sortable-th">
                  Plano
                  <span class="sort-indicator" *ngIf="sortColumn === 'plano_tipo'">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th (click)="setSort('veiculos')" class="sortable-th">
                  Veículos Cadastrados
                  <span class="sort-indicator" *ngIf="sortColumn === 'veiculos'">
                    {{ sortDirection === 'asc' ? '▲' : '▼' }}
                  </span>
                </th>
                <th>Outros dados</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let c of filteredCustomers">
                <td>
                  <span class="code-badge">{{ c.codigo || '—' }}</span>
                </td>
                <td>
                  <strong>{{ c.nome }}</strong>
                </td>
                <td>
                  <span>{{ c.telefone || '—' }}</span>
                </td>
                <td>
                  <span class="plan-badge" [ngClass]="'plan-' + c.plano_tipo">
                    {{ formatPlan(c.plano_tipo) }}
                  </span>
                </td>
                <td>
                  <!-- Exibe exclusivamente as placas -->
                  <div class="vehicles-list" *ngIf="c.veiculos && c.veiculos.length > 0; else noVehicles">
                    <span class="vehicle-chip" *ngFor="let v of c.veiculos">
                      {{ v.placa }}
                    </span>
                  </div>
                  <ng-template #noVehicles>
                    <span class="text-muted">Nenhum</span>
                  </ng-template>
                </td>
                <td>
                  <button class="btn-details" (click)="openCustomerDetails(c)">
                    Outros dados
                  </button>
                </td>
                <td>
                  <div class="action-buttons">
                    <button class="btn-action" (click)="openAddVehicleModal(c)">
                      + Veículo
                    </button>
                    <button class="btn-action" *ngIf="!c.acesso_portal" (click)="openAccessModal(c)">
                      Criar acesso
                    </button>
                    <ng-container *ngIf="c.acesso_portal">
                      <span class="portal-badge">Portal ativo</span>
                      <button class="btn-action danger" (click)="revokeAccess(c)">Revogar</button>
                    </ng-container>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <ng-template #emptyState>
          <div class="empty-state">
            <p>Nenhum cliente cadastrado ou localizado pelo filtro.</p>
          </div>
        </ng-template>
      </div>

      <!-- Modal / Painel de Detalhes: Outros dados e Histórico de Movimentações -->
      <div class="modal-backdrop" *ngIf="showDetailsModal && selectedCustomerDetails">
        <div class="modal-content modal-large">
          <div class="modal-header">
            <div>
              <h3>Detalhes do Cliente</h3>
              <p class="modal-subtitle">{{ selectedCustomerDetails.nome }} ({{ selectedCustomerDetails.codigo }})</p>
            </div>
            <button class="btn-close" (click)="closeCustomerDetails()">&times;</button>
          </div>

          <div class="modal-body">
            <!-- Dados Cadastrais Completos -->
            <div class="details-section">
              <h4 class="section-title">Informações Cadastrais</h4>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">Código Identificador</span>
                  <span class="info-value"><strong>{{ selectedCustomerDetails.codigo }}</strong></span>
                </div>
                <div class="info-item">
                  <span class="info-label">Nome Completo</span>
                  <span class="info-value">{{ selectedCustomerDetails.nome }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">CPF</span>
                  <span class="info-value doc-value">{{ selectedCustomerDetails.documento }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Telefone</span>
                  <span class="info-value">{{ selectedCustomerDetails.telefone || 'Não informado' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">E-mail</span>
                  <span class="info-value">{{ selectedCustomerDetails.email || 'Não informado' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Plano Contratado</span>
                  <span class="info-value">
                    <span class="plan-badge" [ngClass]="'plan-' + selectedCustomerDetails.plano_tipo">
                      {{ formatPlan(selectedCustomerDetails.plano_tipo) }}
                    </span>
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">Data de Cadastro Inicial</span>
                  <span class="info-value">{{ selectedCustomerDetails.criado_em | date:'dd/MM/yyyy HH:mm' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">Acesso ao Portal</span>
                  <span class="info-value">{{ selectedCustomerDetails.acesso_portal ? 'Ativo' : 'Não configurado' }}</span>
                </div>
              </div>

              <!-- Veículos Vinculados Detalhados -->
              <div class="sub-section">
                <span class="info-label">Veículos Vinculados</span>
                <div class="vehicles-detailed-list" *ngIf="selectedCustomerDetails.veiculos.length > 0; else noVehiclesDetailed">
                  <div class="vehicle-card" *ngFor="let v of selectedCustomerDetails.veiculos">
                    <span class="vehicle-chip-lg">{{ v.placa }}</span>
                    <span class="vehicle-meta">
                      {{ v.tipo | uppercase }}
                      <span *ngIf="v.marca || v.modelo">• {{ v.marca }} {{ v.modelo }}</span>
                      <span *ngIf="v.cor">• Cor: {{ v.cor }}</span>
                    </span>
                  </div>
                </div>
                <ng-template #noVehiclesDetailed>
                  <p class="text-muted">Nenhum veículo vinculado a este cliente.</p>
                </ng-template>
              </div>
            </div>

            <!-- Histórico de Movimentações -->
            <div class="details-section">
              <div class="section-header-flex">
                <h4 class="section-title">Histórico de Movimentações dos Veículos</h4>
              </div>

              <!-- Filtros de Movimentação -->
              <div class="movement-filters-bar">
                <div class="filter-field">
                  <label>Veículo</label>
                  <select [(ngModel)]="movementFilterPlate" class="form-control-sm">
                    <option value="">Todos os veículos</option>
                    <option *ngFor="let v of selectedCustomerDetails.veiculos" [value]="v.placa">
                      {{ v.placa }}
                    </option>
                  </select>
                </div>
                <div class="filter-field">
                  <label>Data Início</label>
                  <input type="date" [(ngModel)]="movementFilterDateStart" class="form-control-sm" />
                </div>
                <div class="filter-field">
                  <label>Data Fim</label>
                  <input type="date" [(ngModel)]="movementFilterDateEnd" class="form-control-sm" />
                </div>
                <div class="filter-actions">
                  <button class="btn-filter" (click)="loadMovementsForSelected()">Filtrar</button>
                  <button class="btn-clear-filter" (click)="clearMovementFilters()">Limpar</button>
                </div>
              </div>

              <!-- Tabela de Movimentações -->
              <div *ngIf="loadingMovements" class="loading-state">
                <p>Carregando movimentações do cliente...</p>
              </div>

              <div class="table-container movements-table-container" *ngIf="!loadingMovements && customerMovements.length > 0">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Placa</th>
                      <th>Data Entrada</th>
                      <th>Hora Entrada</th>
                      <th>Data Saída</th>
                      <th>Hora Saída</th>
                      <th>Permanência</th>
                      <th>Valor Calculado</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let m of customerMovements" [class.row-parked]="m.esta_estacionado">
                      <td>
                        <strong>{{ m.placa }}</strong>
                      </td>
                      <td>{{ m.entrada_em | date:'dd/MM/yyyy' }}</td>
                      <td>{{ m.entrada_em | date:'HH:mm' }}</td>
                      <td>{{ m.saida_em ? (m.saida_em | date:'dd/MM/yyyy') : '—' }}</td>
                      <td>{{ m.saida_em ? (m.saida_em | date:'HH:mm') : '—' }}</td>
                      <td>{{ formatStay(m.permanencia_minutos) }}</td>
                      <td>
                        <span *ngIf="m.valor_calculado != null; else noValor">
                          {{ m.valor_calculado | currency:'BRL':'symbol':'1.2-2' }}
                        </span>
                        <ng-template #noValor>—</ng-template>
                      </td>
                      <td>
                        <span class="status-badge" [class.badge-parked]="m.esta_estacionado" [class.badge-finished]="!m.esta_estacionado">
                          {{ m.esta_estacionado ? 'Estacionado' : 'Concluído' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="empty-movements" *ngIf="!loadingMovements && customerMovements.length === 0">
                <p>Nenhuma movimentação registrada para os veículos deste cliente no período selecionado.</p>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" (click)="closeCustomerDetails()">Fechar</button>
          </div>
        </div>
      </div>

      <!-- Modal: Novo Cliente com Veículo Inicial Obrigatório -->
      <div class="modal-backdrop" *ngIf="showCustomerModal">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <h3>Cadastrar Novo Cliente</h3>
              <p class="modal-subtitle">Identificação obrigatória, plano contratado e veículo inicial</p>
            </div>
            <button class="btn-close" (click)="showCustomerModal = false">&times;</button>
          </div>

          <form (ngSubmit)="saveCustomer()">
            <div class="modal-body">
              <div class="form-section-title">Identificação do Cliente</div>

              <div class="form-group mb-3">
                <label>Código Identificador</label>
                <input
                  type="text"
                  value="Gerado automaticamente pelo sistema (ex: CLI-0011)"
                  disabled
                  class="form-control disabled-input"
                />
                <small class="text-muted">Código único e permanente atribuído automaticamente ao salvar.</small>
              </div>

              <div class="form-row">
                <div class="form-group flex-2">
                  <label>Nome Completo *</label>
                  <input
                    type="text"
                    [(ngModel)]="newCustomer.nome"
                    name="nome"
                    required
                    class="form-control"
                    placeholder="Ex: Carlos Silva"
                  />
                </div>
                <div class="form-group flex-1">
                  <label>CPF *</label>
                  <input
                    type="text"
                    [(ngModel)]="newCustomer.documento"
                    name="doc"
                    required
                    maxlength="14"
                    class="form-control"
                    placeholder="000.000.000-00"
                    (input)="formatCpfInput()"
                  />
                  <small class="field-error" *ngIf="newCustomer.documento && !isCpfValid(newCustomer.documento)">
                    CPF inválido (11 dígitos)
                  </small>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Telefone / WhatsApp *</label>
                  <input
                    type="text"
                    [(ngModel)]="newCustomer.telefone"
                    name="telefone"
                    required
                    class="form-control"
                    placeholder="(11) 98888-0000"
                    (input)="formatPhoneInput()"
                  />
                  <small class="field-error" *ngIf="newCustomer.telefone && !isPhoneValid(newCustomer.telefone)">
                    Telefone obrigatório (mín. 10 dígitos)
                  </small>
                </div>
                <div class="form-group flex-1">
                  <label>E-mail (Opcional)</label>
                  <input
                    type="email"
                    [(ngModel)]="newCustomer.email"
                    name="email"
                    class="form-control"
                    placeholder="cliente@exemplo.com"
                  />
                </div>
              </div>

              <div class="form-group mb-3">
                <label>Plano Contratado *</label>
                <select [(ngModel)]="newCustomer.plano_tipo" name="plano_tipo" required class="form-control">
                  <option value="">Selecione a modalidade do plano...</option>
                  <option value="diario">Diário</option>
                  <option value="mensal">Mensal</option>
                  <option value="anual">Anual</option>
                </select>
                <small class="text-muted">A seleção do plano é obrigatória para conclusão do cadastro.</small>
              </div>

              <div class="form-section-title">
                Veículo Inicial Obrigatório
              </div>
              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Placa do Veículo *</label>
                  <input
                    type="text"
                    [(ngModel)]="initialVehicle.placa"
                    name="v_placa"
                    required
                    class="form-control uppercase"
                    placeholder="Ex: ABC1D23"
                    maxlength="10"
                  />
                </div>
                <div class="form-group flex-1">
                  <label>Tipo de Veículo</label>
                  <select [(ngModel)]="initialVehicle.tipo" name="v_tipo" class="form-control">
                    <option value="carro">Carro</option>
                    <option value="moto">Moto</option>
                    <option value="caminhao">Caminhão</option>
                    <option value="onibus">Ônibus</option>
                  </select>
                </div>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Marca / Fabricante</label>
                  <input
                    type="text"
                    [(ngModel)]="initialVehicle.marca"
                    name="v_marca"
                    class="form-control"
                    placeholder="Ex: Toyota"
                  />
                </div>
                <div class="form-group flex-1">
                  <label>Modelo</label>
                  <input
                    type="text"
                    [(ngModel)]="initialVehicle.modelo"
                    name="v_modelo"
                    class="form-control"
                    placeholder="Ex: Corolla"
                  />
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="showCustomerModal = false">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="!isCustomerValid()">
                Salvar Cliente e Veículo
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal: Acesso ao Portal do Cliente -->
      <div class="modal-backdrop" *ngIf="showAccessModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Acesso ao portal: {{ accessCustomer?.nome }}</h3>
            <button class="btn-close" (click)="showAccessModal = false">&times;</button>
          </div>
          <form (ngSubmit)="saveAccess()">
            <div class="modal-body">
              <div class="form-group mb-3">
                <label>E-mail de login *</label>
                <input type="email" [(ngModel)]="accessForm.email" name="ac_email" required class="form-control" />
              </div>
              <div class="form-group mb-3">
                <label>Senha provisória * (mín. 8 caracteres)</label>
                <input
                  type="password"
                  [(ngModel)]="accessForm.senha"
                  name="ac_senha"
                  required
                  minlength="8"
                  autocomplete="new-password"
                  class="form-control"
                />
                <small class="text-muted">Informe a senha ao cliente por um canal seguro. Ele poderá alterá-la no primeiro acesso.</small>
              </div>
              <div class="notification-banner error" *ngIf="accessError">{{ accessError }}</div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="showAccessModal = false">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="!accessForm.email || accessForm.senha.length < 8">
                Criar acesso
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal: Adicionar Veículo a Cliente Existente -->
      <div class="modal-backdrop" *ngIf="showVehicleModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Adicionar Veículo para {{ selectedCustomer?.nome }}</h3>
            <button class="btn-close" (click)="showVehicleModal = false">&times;</button>
          </div>

          <form (ngSubmit)="saveAdditionalVehicle()">
            <div class="modal-body">
              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Placa *</label>
                  <input
                    type="text"
                    [(ngModel)]="newVehicle.placa"
                    name="av_placa"
                    required
                    class="form-control uppercase"
                    placeholder="Ex: BRA2E19"
                    maxlength="10"
                  />
                </div>
                <div class="form-group flex-1">
                  <label>Tipo</label>
                  <select [(ngModel)]="newVehicle.tipo" name="av_tipo" class="form-control">
                    <option value="carro">Carro</option>
                    <option value="moto">Moto</option>
                    <option value="caminhao">Caminhão</option>
                    <option value="onibus">Ônibus</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Marca</label>
                  <input
                    type="text"
                    [(ngModel)]="newVehicle.marca"
                    name="av_marca"
                    class="form-control"
                    placeholder="Ex: Honda"
                  />
                </div>
                <div class="form-group flex-1">
                  <label>Modelo</label>
                  <input
                    type="text"
                    [(ngModel)]="newVehicle.modelo"
                    name="av_modelo"
                    class="form-control"
                    placeholder="Ex: Civic"
                  />
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="showVehicleModal = false">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="!newVehicle.placa">Cadastrar Veículo</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .customers-page { padding: 1.5rem 2rem; }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
    }
    h2 { margin: 0; color: #0f172a; font-size: 1.5rem; font-weight: 700; }
    .subtitle { margin: 0.25rem 0 0; color: #64748b; font-size: 0.875rem; }
    .btn-primary {
      background: #0284c7;
      color: #fff;
      border: none;
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.875rem;
      transition: background 0.2s;
    }
    .btn-primary:hover:not(:disabled) { background: #0369a1; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .btn-secondary {
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      padding: 0.6rem 1.25rem;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-secondary:hover { background: #e2e8f0; }
    .filter-bar { margin-bottom: 1.25rem; }
    .search-input {
      width: 100%;
      max-width: 480px;
      padding: 0.65rem 1rem;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      outline: none;
      font-size: 0.875rem;
    }
    .search-input:focus { border-color: #0284c7; }
    .content-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .table-container { overflow-x: auto; }
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
      user-select: none;
    }
    .sortable-th {
      cursor: pointer;
      transition: color 0.15s, background 0.15s;
    }
    .sortable-th:hover {
      background: #f1f5f9;
      color: #0f172a;
    }
    .sort-indicator {
      display: inline-block;
      margin-left: 0.35rem;
      font-size: 0.7rem;
      color: #0284c7;
    }
    .data-table td {
      padding: 0.85rem 1rem;
      border-bottom: 1px solid #f1f5f9;
      font-size: 0.875rem;
      color: #1e293b;
      vertical-align: middle;
    }
    .code-badge {
      background: #0f172a;
      color: #f8fafc;
      font-family: monospace;
      padding: 0.25rem 0.55rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .plan-badge {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
    }
    .plan-diario { background: #fef3c7; color: #b45309; }
    .plan-mensal { background: #dbeafe; color: #1d4ed8; }
    .plan-anual { background: #dcfce7; color: #15803d; }
    .vehicles-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .vehicle-chip {
      background: #f8fafc;
      color: #0f172a;
      border: 1px solid #cbd5e1;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-family: monospace;
      font-weight: 700;
      letter-spacing: 0.05em;
    }
    .btn-details {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      color: #166534;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-details:hover {
      background: #dcfce7;
      border-color: #86efac;
    }
    .action-buttons {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .btn-action {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #0284c7;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-action:hover { background: #e0f2fe; }
    .btn-action.danger { color: #dc2626; }
    .btn-action.danger:hover { background: #fee2e2; }
    .portal-badge {
      font-size: 0.7rem;
      font-weight: 600;
      color: #15803d;
      background: #dcfce7;
      padding: 0.2rem 0.45rem;
      border-radius: 4px;
    }

    /* Modal Styling */
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.65);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 1rem;
    }
    .modal-content {
      background: #ffffff;
      border-radius: 14px;
      width: 100%;
      max-width: 650px;
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.25);
    }
    .modal-content.modal-large {
      max-width: 900px;
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid #e2e8f0;
      position: sticky;
      top: 0;
      background: #ffffff;
      z-index: 10;
    }
    .modal-header h3 { margin: 0; font-size: 1.2rem; color: #0f172a; font-weight: 700; }
    .modal-subtitle { margin: 0.2rem 0 0; font-size: 0.8rem; color: #64748b; }
    .btn-close {
      background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #64748b; line-height: 1;
    }
    .modal-body { padding: 1.5rem; }
    .modal-footer {
      padding: 1rem 1.5rem;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      background: #f8fafc;
      position: sticky;
      bottom: 0;
    }

    /* Details Grid & History Styling */
    .details-section {
      margin-bottom: 1.75rem;
    }
    .details-section:last-child {
      margin-bottom: 0;
    }
    .section-title {
      font-size: 0.95rem;
      font-weight: 700;
      color: #0f172a;
      margin: 0 0 1rem;
      padding-bottom: 0.4rem;
      border-bottom: 2px solid #e2e8f0;
    }
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      background: #f8fafc;
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      margin-bottom: 1rem;
    }
    .info-item {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }
    .info-label {
      font-size: 0.75rem;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .info-value {
      font-size: 0.9rem;
      color: #0f172a;
    }
    .doc-value {
      font-family: monospace;
      font-weight: 600;
    }
    .sub-section {
      margin-top: 1rem;
    }
    .vehicles-detailed-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-top: 0.5rem;
    }
    .vehicle-card {
      display: flex;
      align-items: center;
      gap: 1rem;
      background: #f1f5f9;
      padding: 0.6rem 0.85rem;
      border-radius: 6px;
      border: 1px solid #e2e8f0;
    }
    .vehicle-chip-lg {
      background: #0f172a;
      color: #ffffff;
      font-family: monospace;
      padding: 0.25rem 0.6rem;
      border-radius: 4px;
      font-size: 0.85rem;
      font-weight: 700;
    }
    .vehicle-meta {
      font-size: 0.8rem;
      color: #475569;
    }

    /* Movements Section in Details */
    .movement-filters-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-end;
      gap: 0.75rem;
      background: #f8fafc;
      padding: 0.85rem;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      margin-bottom: 1rem;
    }
    .filter-field {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .filter-field label {
      font-size: 0.72rem;
      font-weight: 600;
      color: #64748b;
      text-transform: uppercase;
    }
    .form-control-sm {
      padding: 0.4rem 0.65rem;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.8rem;
      outline: none;
      background: #ffffff;
    }
    .filter-actions {
      display: flex;
      gap: 0.5rem;
    }
    .btn-filter {
      background: #0284c7;
      color: #fff;
      border: none;
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-filter:hover { background: #0369a1; }
    .btn-clear-filter {
      background: #ffffff;
      color: #64748b;
      border: 1px solid #cbd5e1;
      padding: 0.45rem 0.75rem;
      border-radius: 6px;
      font-size: 0.8rem;
      cursor: pointer;
    }
    .movements-table-container {
      max-height: 280px;
      overflow-y: auto;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
    }
    .row-parked {
      background: #f0fdf4 !important;
    }
    .status-badge {
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .badge-parked {
      background: #dcfce7;
      color: #15803d;
      border: 1px solid #86efac;
    }
    .badge-finished {
      background: #f1f5f9;
      color: #475569;
      border: 1px solid #cbd5e1;
    }
    .loading-state, .empty-movements {
      text-align: center;
      padding: 2rem;
      color: #64748b;
      font-size: 0.85rem;
      background: #f8fafc;
      border-radius: 8px;
      border: 1px dashed #cbd5e1;
    }

    /* Forms */
    .form-section-title {
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #0284c7;
      letter-spacing: 0.05em;
      margin: 1rem 0 0.75rem;
      padding-bottom: 0.25rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .form-section-title:first-child { margin-top: 0; }
    .form-row {
      display: flex;
      gap: 1rem;
      margin-bottom: 1rem;
    }
    .flex-1 { flex: 1; }
    .flex-2 { flex: 2; }
    .mb-3 { margin-bottom: 1rem; }
    .form-group label {
      display: block;
      font-size: 0.75rem;
      font-weight: 600;
      color: #475569;
      margin-bottom: 0.25rem;
    }
    .form-control {
      width: 100%;
      box-sizing: border-box;
      padding: 0.55rem 0.75rem;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 0.85rem;
      outline: none;
    }
    .form-control:focus { border-color: #0284c7; }
    .disabled-input {
      background: #f1f5f9;
      color: #64748b;
      cursor: not-allowed;
    }
    .field-error {
      color: #dc2626;
      font-size: 0.72rem;
      margin-top: 0.2rem;
      display: block;
    }
    .uppercase { text-transform: uppercase; }
    .notification-banner {
      padding: 0.75rem 1rem;
      border-radius: 8px;
      margin-bottom: 1rem;
      font-size: 0.85rem;
    }
    .notification-banner.success { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .notification-banner.error { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
    .empty-state { padding: 3rem; text-align: center; color: #94a3b8; }
    .text-muted { color: #64748b; font-size: 0.75rem; }
  `],
})
export class CustomersComponent implements OnInit {
  private api = inject(ApiService);

  customers: Cliente[] = [];
  searchQuery = '';
  successMessage = '';
  errorMessage = '';

  // Ordenação
  sortColumn: SortColumn = 'codigo';
  sortDirection: SortDirection = 'asc';

  // Modal Novo Cliente
  showCustomerModal = false;
  newCustomer = {
    nome: '',
    documento: '',
    tipo_documento: 'CPF' as 'CPF' | 'CNPJ',
    email: '',
    telefone: '',
    plano_tipo: '',
  };
  initialVehicle = {
    placa: '',
    marca: '',
    modelo: '',
    cor: '',
    tipo: 'carro' as 'carro' | 'moto' | 'caminhao' | 'onibus',
  };

  // Modal Adicionar Veículo
  showVehicleModal = false;
  selectedCustomer: Cliente | null = null;
  newVehicle = {
    placa: '',
    marca: '',
    modelo: '',
    cor: '',
    tipo: 'carro' as 'carro' | 'moto' | 'caminhao' | 'onibus',
  };

  // Modal Acesso Portal
  showAccessModal = false;
  accessCustomer: Cliente | null = null;
  accessForm = { email: '', senha: '' };
  accessError = '';

  // Painel / Modal de Detalhes ("Outros dados")
  showDetailsModal = false;
  selectedCustomerDetails: Cliente | null = null;
  customerMovements: ClienteMovimentacao[] = [];
  loadingMovements = false;
  movementFilterPlate = '';
  movementFilterDateStart = '';
  movementFilterDateEnd = '';

  ngOnInit(): void {
    this.loadCustomers();
  }

  loadCustomers(): void {
    this.api.getCustomers().subscribe({
      next: (res) => {
        this.customers = res;
        this.errorMessage = '';
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao carregar clientes do servidor.';
      },
    });
  }

  // --- Ordenação ---
  setSort(col: SortColumn): void {
    if (this.sortColumn === col) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = col;
      this.sortDirection = 'asc';
    }
  }

  get filteredCustomers(): Cliente[] {
    let result = [...this.customers];

    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          (c.codigo && c.codigo.toLowerCase().includes(q)) ||
          c.nome.toLowerCase().includes(q) ||
          c.documento.includes(q) ||
          (c.telefone && c.telefone.toLowerCase().includes(q)) ||
          (c.plano_tipo && c.plano_tipo.toLowerCase().includes(q)) ||
          c.veiculos.some((v) => v.placa.toLowerCase().includes(q))
      );
    }

    // Aplica ordenação
    result.sort((a, b) => {
      let valA = '';
      let valB = '';

      switch (this.sortColumn) {
        case 'codigo':
          valA = a.codigo || '';
          valB = b.codigo || '';
          break;
        case 'nome':
          valA = a.nome || '';
          valB = b.nome || '';
          break;
        case 'telefone':
          valA = a.telefone || '';
          valB = b.telefone || '';
          break;
        case 'plano_tipo':
          valA = a.plano_tipo || '';
          valB = b.plano_tipo || '';
          break;
        case 'veiculos':
          // Ordena pela quantidade de veículos ou primeira placa
          valA = a.veiculos?.[0]?.placa || '';
          valB = b.veiculos?.[0]?.placa || '';
          break;
      }

      const cmp = valA.localeCompare(valB, 'pt-BR', { numeric: true, sensitivity: 'base' });
      return this.sortDirection === 'asc' ? cmp : -cmp;
    });

    return result;
  }

  formatPlan(plan?: string): string {
    if (!plan) return '—';
    const map: Record<string, string> = {
      diario: 'Diário',
      mensal: 'Mensal',
      anual: 'Anual',
    };
    return map[plan.toLowerCase()] || plan.toUpperCase();
  }

  formatStay(minutes?: number): string {
    if (minutes == null || minutes < 0) return '—';
    if (minutes < 60) return `${minutes} min`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h}h ${m}m`;
  }

  // --- Painel Detalhes ("Outros dados") ---
  openCustomerDetails(customer: Cliente): void {
    this.selectedCustomerDetails = customer;
    this.movementFilterPlate = '';
    this.movementFilterDateStart = '';
    this.movementFilterDateEnd = '';
    this.showDetailsModal = true;
    this.loadMovementsForSelected();
  }

  closeCustomerDetails(): void {
    this.showDetailsModal = false;
    this.selectedCustomerDetails = null;
    this.customerMovements = [];
  }

  loadMovementsForSelected(): void {
    if (!this.selectedCustomerDetails) return;
    this.loadingMovements = true;

    const params: { placa?: string; data_inicio?: string; data_fim?: string } = {};
    if (this.movementFilterPlate) params.placa = this.movementFilterPlate;
    if (this.movementFilterDateStart) params.data_inicio = this.movementFilterDateStart;
    if (this.movementFilterDateEnd) params.data_fim = this.movementFilterDateEnd;

    this.api.getCustomerMovements(this.selectedCustomerDetails.id, params).subscribe({
      next: (movs) => {
        this.customerMovements = movs;
        this.loadingMovements = false;
      },
      error: () => {
        this.customerMovements = [];
        this.loadingMovements = false;
      },
    });
  }

  clearMovementFilters(): void {
    this.movementFilterPlate = '';
    this.movementFilterDateStart = '';
    this.movementFilterDateEnd = '';
    this.loadMovementsForSelected();
  }

  // --- Validações de Formulário ---
  isCpfValid(cpf: string): boolean {
    const clean = cpf.replace(/\D/g, '');
    if (clean.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(clean)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += parseInt(clean.charAt(i), 10) * (10 - i);
    }
    let rest = (sum * 10) % 11;
    if (rest === 10 || rest === 11) rest = 0;
    if (rest !== parseInt(clean.charAt(9), 10)) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) {
      sum += parseInt(clean.charAt(i), 10) * (11 - i);
    }
    rest = (sum * 10) % 11;
    if (rest === 10 || rest === 11) rest = 0;
    if (rest !== parseInt(clean.charAt(10), 10)) return false;

    return true;
  }

  isPhoneValid(phone: string): boolean {
    const clean = phone.replace(/\D/g, '');
    return clean.length >= 10 && clean.length <= 15;
  }

  formatCpfInput(): void {
    let v = this.newCustomer.documento.replace(/\D/g, '').slice(0, 11);
    if (v.length > 9) {
      v = v.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    } else if (v.length > 6) {
      v = v.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
    } else if (v.length > 3) {
      v = v.replace(/(\d{3})(\d{1,3})/, '$1.$2');
    }
    this.newCustomer.documento = v;
  }

  formatPhoneInput(): void {
    let v = this.newCustomer.telefone.replace(/\D/g, '').slice(0, 11);
    if (v.length > 10) {
      v = v.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (v.length > 6) {
      v = v.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    } else if (v.length > 2) {
      v = v.replace(/(\d{2})(\d{0,5})/, '($1) $2');
    }
    this.newCustomer.telefone = v;
  }

  isCustomerValid(): boolean {
    return (
      !!this.newCustomer.nome.trim() &&
      this.isCpfValid(this.newCustomer.documento) &&
      this.isPhoneValid(this.newCustomer.telefone) &&
      !!this.newCustomer.plano_tipo &&
      ['diario', 'mensal', 'anual'].includes(this.newCustomer.plano_tipo) &&
      this.initialVehicle.placa.trim().length >= 7
    );
  }

  // --- Cadastro de Cliente ---
  openNewCustomerModal(): void {
    this.clearMessages();
    this.newCustomer = {
      nome: '',
      documento: '',
      tipo_documento: 'CPF',
      email: '',
      telefone: '',
      plano_tipo: '',
    };
    this.initialVehicle = {
      placa: '',
      marca: '',
      modelo: '',
      cor: '',
      tipo: 'carro',
    };
    this.showCustomerModal = true;
  }

  saveCustomer(): void {
    if (!this.isCustomerValid()) return;
    this.clearMessages();

    const payload = {
      nome: this.newCustomer.nome.trim(),
      documento: this.newCustomer.documento.replace(/\D/g, ''),
      tipo_documento: this.newCustomer.tipo_documento,
      telefone: this.newCustomer.telefone.trim(),
      email: this.newCustomer.email.trim() || undefined,
      plano_tipo: this.newCustomer.plano_tipo,
      veiculos_iniciais: [
        {
          ...this.initialVehicle,
          placa: this.initialVehicle.placa.trim().toUpperCase(),
        },
      ],
    };

    this.api.createCustomer(payload).subscribe({
      next: (res) => {
        this.successMessage = `Cliente ${res.nome} cadastrado com sucesso! Código gerado: ${res.codigo}.`;
        this.showCustomerModal = false;
        this.loadCustomers();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao cadastrar cliente.';
      },
    });
  }

  // --- Veículo Adicional ---
  openAddVehicleModal(cliente: Cliente): void {
    this.clearMessages();
    this.selectedCustomer = cliente;
    this.newVehicle = { placa: '', marca: '', modelo: '', cor: '', tipo: 'carro' };
    this.showVehicleModal = true;
  }

  saveAdditionalVehicle(): void {
    if (!this.selectedCustomer || !this.newVehicle.placa) return;
    this.clearMessages();

    const vehicleData = {
      ...this.newVehicle,
      placa: this.newVehicle.placa.trim().toUpperCase(),
    };

    this.api.addVehicle(this.selectedCustomer.id, vehicleData).subscribe({
      next: (v) => {
        this.successMessage = `Veículo ${v.placa} adicionado a ${this.selectedCustomer?.nome}!`;
        this.showVehicleModal = false;
        this.loadCustomers();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao adicionar veículo.';
      },
    });
  }

  // --- Acesso ao Portal ---
  openAccessModal(customer: Cliente): void {
    this.accessCustomer = customer;
    this.accessForm = { email: customer.email ?? '', senha: '' };
    this.accessError = '';
    this.showAccessModal = true;
  }

  saveAccess(): void {
    if (!this.accessCustomer) return;
    this.api.createPortalAccess(this.accessCustomer.id, this.accessForm).subscribe({
      next: () => {
        this.showAccessModal = false;
        this.accessForm = { email: '', senha: '' };
        this.loadCustomers();
      },
      error: (err) => {
        const detail = err.error?.detail;
        this.accessError = typeof detail === 'string' ? detail : 'Não foi possível criar o acesso.';
      },
    });
  }

  revokeAccess(customer: Cliente): void {
    if (!confirm(`Revogar o acesso de ${customer.nome} ao portal?`)) return;
    this.api.revokePortalAccess(customer.id).subscribe({
      next: () => this.loadCustomers(),
      error: () => {},
    });
  }

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
  }
}
