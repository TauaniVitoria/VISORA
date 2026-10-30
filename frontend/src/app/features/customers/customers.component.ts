import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { Cliente } from '../../core/models/models';

@Component({
  selector: 'app-customers',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="customers-page">
      <div class="page-header">
        <div>
          <h2>Gestão de Clientes e Veículos</h2>
          <p class="subtitle">Controle de motoristas, frotas e cadastro obrigatório de veículos vinculados</p>
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
          placeholder="Buscar por nome, CPF/CNPJ ou placa..."
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
                <th>Cliente</th>
                <th>Documento</th>
                <th>Contato</th>
                <th>Veículos Cadastrados</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let c of filteredCustomers">
                <td>
                  <strong>{{ c.nome }}</strong>
                </td>
                <td>
                  <span class="doc-badge">{{ c.tipo_documento }}: {{ c.documento }}</span>
                </td>
                <td>
                  <div>{{ c.email || '—' }}</div>
                  <small class="text-muted">{{ c.telefone || '—' }}</small>
                </td>
                <td>
                  <div class="vehicles-list">
                    <span class="vehicle-chip" *ngFor="let v of c.veiculos">
                      🚗 {{ v.placa }} <small>({{ v.modelo || v.tipo }})</small>
                    </span>
                  </div>
                </td>
                <td>
                  <button class="btn-add-vehicle" (click)="openAddVehicleModal(c)">
                    + Veículo
                  </button>
                  <button class="btn-add-vehicle" *ngIf="!c.acesso_portal" (click)="openAccessModal(c)">
                    Criar acesso ao portal
                  </button>
                  <ng-container *ngIf="c.acesso_portal">
                    <span class="vehicle-chip">Portal ativo</span>
                    <button class="btn-add-vehicle" (click)="revokeAccess(c)">Revogar acesso</button>
                  </ng-container>
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

      <!-- Modal: Novo Cliente com Veículo Inicial Obrigatório -->
      <div class="modal-backdrop" *ngIf="showCustomerModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Cadastrar Novo Cliente</h3>
            <button class="btn-close" (click)="showCustomerModal = false">✕</button>
          </div>

          <form (ngSubmit)="saveCustomer()">
            <div class="modal-body">
              <div class="form-section-title">Dados do Cliente</div>
              <div class="form-row">
                <div class="form-group flex-2">
                  <label>Nome Completo *</label>
                  <input type="text" [(ngModel)]="newCustomer.nome" name="nome" required class="form-control" placeholder="Ex: Roberto Carlos" />
                </div>
                <div class="form-group flex-1">
                  <label>Tipo Doc *</label>
                  <select [(ngModel)]="newCustomer.tipo_documento" name="tipo_doc" class="form-control">
                    <option value="CPF">CPF</option>
                    <option value="CNPJ">CNPJ</option>
                  </select>
                </div>
                <div class="form-group flex-2">
                  <label>Número do Documento *</label>
                  <input type="text" [(ngModel)]="newCustomer.documento" name="doc" required class="form-control" placeholder="Apenas dígitos" />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label>E-mail</label>
                  <input type="email" [(ngModel)]="newCustomer.email" name="email" class="form-control" placeholder="cliente@exemplo.com" />
                </div>
                <div class="form-group flex-1">
                  <label>Telefone / WhatsApp</label>
                  <input type="text" [(ngModel)]="newCustomer.telefone" name="telefone" class="form-control" placeholder="(11) 99999-9999" />
                </div>
              </div>

              <div class="form-section-title">
                Veículo Inicial Obrigatório (Regra de Negócio)
              </div>
              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Placa do Veículo *</label>
                  <input type="text" [(ngModel)]="initialVehicle.placa" name="v_placa" required class="form-control uppercase" placeholder="Ex: ABC1D23" maxlength="10" />
                </div>
                <div class="form-group flex-1">
                  <label>Marca / Fabricante</label>
                  <input type="text" [(ngModel)]="initialVehicle.marca" name="v_marca" class="form-control" placeholder="Ex: Toyota" />
                </div>
                <div class="form-group flex-1">
                  <label>Modelo</label>
                  <input type="text" [(ngModel)]="initialVehicle.modelo" name="v_modelo" class="form-control" placeholder="Ex: Corolla" />
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" (click)="showCustomerModal = false">Cancelar</button>
              <button type="submit" class="btn-primary" [disabled]="!isCustomerValid()">Salvar Cliente e Veículo</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Modal: Acesso ao Portal do Cliente -->
      <div class="modal-backdrop" *ngIf="showAccessModal">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Acesso ao portal: {{ accessCustomer?.nome }}</h3>
            <button class="btn-close" (click)="showAccessModal = false">✕</button>
          </div>
          <form (ngSubmit)="saveAccess()">
            <div class="modal-body">
              <div class="form-group">
                <label>E-mail de login *</label>
                <input type="email" [(ngModel)]="accessForm.email" name="ac_email" required class="form-control" />
              </div>
              <div class="form-group">
                <label>Senha provisória * (mín. 8 caracteres)</label>
                <input type="password" [(ngModel)]="accessForm.senha" name="ac_senha" required minlength="8"
                       autocomplete="new-password" class="form-control" />
                <small class="text-muted">Informe a senha ao cliente por um canal seguro. Ele poderá trocá-la em "Esqueci minha senha".</small>
              </div>
              <div class="text-muted" *ngIf="accessError">{{ accessError }}</div>
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
            <button class="btn-close" (click)="showVehicleModal = false">✕</button>
          </div>

          <form (ngSubmit)="saveAdditionalVehicle()">
            <div class="modal-body">
              <div class="form-row">
                <div class="form-group flex-1">
                  <label>Placa *</label>
                  <input type="text" [(ngModel)]="newVehicle.placa" name="av_placa" required class="form-control uppercase" placeholder="Ex: BRA2E19" maxlength="10" />
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
                  <input type="text" [(ngModel)]="newVehicle.marca" name="av_marca" class="form-control" placeholder="Ex: Honda" />
                </div>
                <div class="form-group flex-1">
                  <label>Modelo</label>
                  <input type="text" [(ngModel)]="newVehicle.modelo" name="av_modelo" class="form-control" placeholder="Ex: Civic" />
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
    .filter-bar { margin-bottom: 1.25rem; }
    .search-input {
      width: 100%;
      max-width: 450px;
      padding: 0.65rem 1rem;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      outline: none;
      font-size: 0.875rem;
    }
    .content-card {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1rem;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
      font-size: 0.875rem;
      color: #1e293b;
    }
    .doc-badge {
      background: #f1f5f9;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-family: monospace;
      color: #475569;
    }
    .vehicles-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .vehicle-chip {
      background: #e0f2fe;
      color: #0369a1;
      border: 1px solid #bae6fd;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .btn-add-vehicle {
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      color: #0284c7;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-add-vehicle:hover { background: #e0f2fe; }

    /* Modais */
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.6);
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
      overflow: hidden;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid #e2e8f0;
    }
    .modal-header h3 { margin: 0; font-size: 1.15rem; color: #0f172a; }
    .btn-close {
      background: none; border: none; font-size: 1.25rem; cursor: pointer; color: #64748b;
    }
    .modal-body { padding: 1.5rem; }
    .modal-footer {
      padding: 1rem 1.5rem;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      background: #f8fafc;
    }
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
  `],
})
export class CustomersComponent implements OnInit {
  private api = inject(ApiService);

  customers: Cliente[] = [];
  searchQuery = '';
  successMessage = '';
  errorMessage = '';

  showCustomerModal = false;
  showVehicleModal = false;
  selectedCustomer: Cliente | null = null;

  newCustomer = {
    nome: '',
    documento: '',
    tipo_documento: 'CPF',
    email: '',
    telefone: '',
  };

  initialVehicle = {
    placa: '',
    marca: '',
    modelo: '',
    cor: '',
    tipo: 'carro',
  };

  newVehicle = {
    placa: '',
    marca: '',
    modelo: '',
    cor: '',
    tipo: 'carro',
  };

  showAccessModal = false;
  accessCustomer: Cliente | null = null;
  accessForm = { email: '', senha: '' };
  accessError = '';

  ngOnInit(): void {
    this.loadCustomers();
  }

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

  loadCustomers(): void {
    this.api.getCustomers().subscribe({
      next: (res) => (this.customers = res),
      error: () => {},
    });
  }

  get filteredCustomers(): Cliente[] {
    if (!this.searchQuery.trim()) return this.customers;
    const q = this.searchQuery.toLowerCase();
    return this.customers.filter(
      (c) =>
        c.nome.toLowerCase().includes(q) ||
        c.documento.includes(q) ||
        c.veiculos.some((v) => v.placa.toLowerCase().includes(q))
    );
  }

  openNewCustomerModal(): void {
    this.clearMessages();
    this.newCustomer = { nome: '', documento: '', tipo_documento: 'CPF', email: '', telefone: '' };
    this.initialVehicle = { placa: '', marca: '', modelo: '', cor: '', tipo: 'carro' };
    this.showCustomerModal = true;
  }

  openAddVehicleModal(cliente: Cliente): void {
    this.clearMessages();
    this.selectedCustomer = cliente;
    this.newVehicle = { placa: '', marca: '', modelo: '', cor: '', tipo: 'carro' };
    this.showVehicleModal = true;
  }

  isCustomerValid(): boolean {
    return (
      !!this.newCustomer.nome &&
      !!this.newCustomer.documento &&
      !!this.initialVehicle.placa
    );
  }

  saveCustomer(): void {
    if (!this.isCustomerValid()) return;
    this.clearMessages();

    const payload = {
      ...this.newCustomer,
      veiculos_iniciais: [this.initialVehicle],
    };

    this.api.createCustomer(payload).subscribe({
      next: (res) => {
        this.successMessage = `Cliente ${res.nome} cadastrado com sucesso com veículo ${this.initialVehicle.placa}!`;
        this.showCustomerModal = false;
        this.loadCustomers();
      },
      error: (err) => {
        this.errorMessage = err.error?.detail || 'Erro ao cadastrar cliente.';
      },
    });
  }

  saveAdditionalVehicle(): void {
    if (!this.selectedCustomer || !this.newVehicle.placa) return;
    this.clearMessages();

    this.api.addVehicle(this.selectedCustomer.id, this.newVehicle).subscribe({
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

  private clearMessages(): void {
    this.successMessage = '';
    this.errorMessage = '';
  }
}
