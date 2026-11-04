import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import { AuditoriaLog } from '../../core/models/models';

@Component({
  selector: 'app-audit',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="audit-page">
      <header class="page-header">
        <div>
          <h2>Trilha de Auditoria & Segurança</h2>
          <p class="subtitle">Registro cronológico de operações sensíveis, alterações cadastrais e correções manuais</p>
        </div>
        <button class="btn-refresh" (click)="loadLogs()">Atualizar Registros</button>
      </header>

      <!-- Search & Filters -->
      <div class="search-card">
        <input 
          type="text" 
          [(ngModel)]="searchTerm" 
          (input)="filterLogs()" 
          placeholder="Filtrar por ação, tabela ou ID do registro..." 
          class="search-input" />
      </div>

      <!-- Logs Table -->
      <div class="table-card">
        <table class="data-table">
          <thead>
            <tr>
              <th>Data/Hora</th>
              <th>Ação</th>
              <th>Tabela</th>
              <th>Registro ID</th>
              <th>IP Origem</th>
              <th>Detalhes</th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let log of filteredLogs">
              <td>{{ log.criado_em | date:'dd/MM/yyyy HH:mm:ss' }}</td>
              <td>
                <span class="action-tag" [ngClass]="getActionClass(log.acao)">
                  {{ log.acao }}
                </span>
              </td>
              <td class="font-mono text-sm">{{ log.tabela }}</td>
              <td class="font-mono text-xs">{{ log.registro_id.substring(0, 10) }}...</td>
              <td class="text-xs text-muted">{{ log.ip_origem || '127.0.0.1' }}</td>
              <td>
                <button class="btn-details" (click)="viewPayload(log)">Ver Dados</button>
              </td>
            </tr>
            <tr *ngIf="filteredLogs.length === 0">
              <td colspan="6" class="text-center py-6 text-muted">
                {{ loading ? 'Carregando trilha de auditoria...' : 'Nenhum registro de auditoria encontrado.' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modal Payload Viewer -->
      <div *ngIf="selectedLog" class="modal-backdrop">
        <div class="modal-card">
          <div class="modal-header">
            <h3>Detalhes da Operação: {{ selectedLog.acao }}</h3>
            <button class="btn-close" (click)="selectedLog = null">×</button>
          </div>
          <div class="modal-body">
            <div class="info-row">
              <span class="info-label">Tabela Afetada:</span>
              <span class="font-mono">{{ selectedLog.tabela }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Registro ID:</span>
              <span class="font-mono">{{ selectedLog.registro_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Timestamp:</span>
              <span>{{ selectedLog.criado_em | date:'dd/MM/yyyy HH:mm:ss' }}</span>
            </div>

            <div *ngIf="selectedLog.dados_anteriores" class="json-box">
              <h4>Dados Anteriores:</h4>
              <pre>{{ formatJson(selectedLog.dados_anteriores) }}</pre>
            </div>

            <div *ngIf="selectedLog.dados_novos" class="json-box">
              <h4>Novos Dados:</h4>
              <pre>{{ formatJson(selectedLog.dados_novos) }}</pre>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" (click)="selectedLog = null">Fechar</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .audit-page {
      padding: 1.5rem;
      max-width: 1300px;
      margin: 0 auto;
    }
    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      h2 { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin: 0; }
      .subtitle { color: #64748b; margin-top: 0.25rem; font-size: 0.875rem; }
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
    .search-card {
      margin-bottom: 1rem;
      .search-input {
        width: 100%;
        padding: 0.65rem 1rem;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        font-size: 0.875rem;
      }
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
    .action-tag {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      &.action-create { background: #dcfce7; color: #166534; }
      &.action-update { background: #fef3c7; color: #b45309; }
      &.action-correction { background: #fef3c7; color: #b45309; }
      &.action-delete { background: #fee2e2; color: #991b1b; }
      &.action-default { background: #f5f5f4; color: #52525b; }
    }
    .font-mono { font-family: monospace; }
    .text-xs { font-size: 0.75rem; }
    .text-sm { font-size: 0.825rem; }
    .text-muted { color: #71717a; }
    .btn-details {
      background: #fafaf9;
      border: 1px solid #d6d3d1;
      padding: 0.25rem 0.65rem;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
      &:hover { background: #f5f5f4; }
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(9, 9, 11, 0.55);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 50;
      padding: 1rem;
    }
    .modal-card {
      background: #ffffff;
      border-radius: 8px;
      max-width: 600px;
      width: 100%;
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
      overflow: hidden;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
    }
    .modal-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid #e7e5e4;
      display: flex;
      justify-content: space-between;
      align-items: center;
      h3 { margin: 0; font-size: 1.15rem; color: #18181b; }
      .btn-close { background: none; border: none; font-size: 1.25rem; cursor: pointer; color: #71717a; }
    }
    .modal-body {
      padding: 1.25rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .info-row {
      display: flex;
      gap: 0.5rem;
      font-size: 0.875rem;
      .info-label { font-weight: 600; color: #52525b; width: 130px; }
    }
    .json-box {
      margin-top: 0.5rem;
      h4 { font-size: 0.825rem; color: #52525b; margin: 0 0 0.25rem 0; }
      pre {
        background: #18181b;
        color: #f59e0b;
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 0.75rem;
        overflow-x: auto;
      }
    }
    .modal-footer {
      padding: 1rem 1.25rem;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: flex-end;
    }
    .btn-secondary {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      padding: 0.45rem 1rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
    }
  `]
})
export class AuditComponent implements OnInit {
  logs: AuditoriaLog[] = [];
  filteredLogs: AuditoriaLog[] = [];
  searchTerm = '';
  loading = false;
  selectedLog: AuditoriaLog | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading = true;
    this.api.getAuditLogs().subscribe({
      next: (data) => {
        this.logs = data;
        this.filterLogs();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      }
    });
  }

  filterLogs(): void {
    if (!this.searchTerm.trim()) {
      this.filteredLogs = [...this.logs];
      return;
    }
    const term = this.searchTerm.toLowerCase();
    this.filteredLogs = this.logs.filter(log => 
      log.acao.toLowerCase().includes(term) ||
      log.tabela.toLowerCase().includes(term) ||
      log.registro_id.toLowerCase().includes(term)
    );
  }

  getActionClass(acao: string): string {
    const a = acao.toUpperCase();
    if (a.includes('CORRECAO') || a.includes('MANUAL')) return 'action-correction';
    if (a.includes('CRIACAO') || a.includes('ENTRADA')) return 'action-create';
    if (a.includes('UPDATE') || a.includes('ALTERACAO')) return 'action-update';
    if (a.includes('EXCLUSAO') || a.includes('CANCEL')) return 'action-delete';
    return 'action-default';
  }

  viewPayload(log: AuditoriaLog): void {
    this.selectedLog = log;
  }

  formatJson(val: any): string {
    if (!val) return '';
    if (typeof val === 'string') {
      try {
        return JSON.stringify(JSON.parse(val), null, 2);
      } catch {
        return val;
      }
    }
    return JSON.stringify(val, null, 2);
  }
}
