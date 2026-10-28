import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <aside class="app-sidebar">
      <div class="sidebar-menu">
        <div class="menu-label">OPERAÇÃO</div>
        <a routerLink="/dashboard" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">📊</span>
          <span>Dashboard</span>
        </a>
        <a routerLink="/history" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">🎥</span>
          <span>Histórico ALPR</span>
        </a>

        <div class="menu-label">CADASTROS</div>
        <a routerLink="/customers" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">👥</span>
          <span>Clientes e Veículos</span>
        </a>
        <a routerLink="/tariffs-plans" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">🏷️</span>
          <span>Tarifas e Planos</span>
        </a>

        <div class="menu-label">FINANCEIRO & GOVERNANÇA</div>
        <a routerLink="/billing" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">💳</span>
          <span>Cobranças e Pagamentos</span>
        </a>
        <a routerLink="/audit" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">🛡️</span>
          <span>Auditoria</span>
        </a>
      </div>

      <div class="sidebar-footer">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span>ALPR Engine Online</span>
        </div>
      </div>
    </aside>
  `,
  styles: [`
    .app-sidebar {
      width: 250px;
      background: #111827;
      color: #9ca3af;
      border-right: 1px solid #1f2937;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: calc(100vh - 65px);
    }
    .sidebar-menu {
      padding: 1.25rem 0.75rem;
    }
    .menu-label {
      font-size: 0.65rem;
      font-weight: 700;
      color: #6b7280;
      letter-spacing: 0.08em;
      margin: 1.2rem 0.75rem 0.4rem;
    }
    .menu-label:first-child {
      margin-top: 0;
    }
    .menu-item {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.65rem 0.85rem;
      color: #9ca3af;
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      border-radius: 8px;
      transition: all 0.2s ease;
      margin-bottom: 0.2rem;
    }
    .menu-item:hover {
      background: #1f2937;
      color: #f3f4f6;
    }
    .menu-item.active {
      background: #0284c7;
      color: #ffffff;
      font-weight: 600;
      box-shadow: 0 2px 4px rgba(2, 132, 199, 0.3);
    }
    .menu-icon {
      font-size: 1.1rem;
    }
    .sidebar-footer {
      padding: 1rem 1.25rem;
      border-top: 1px solid #1f2937;
      background: #0b0f17;
    }
    .status-indicator {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #10b981;
      font-weight: 500;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
  `],
})
export class SidebarComponent {
  authService = inject(AuthService);
}
