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
      <div class="sidebar-menu" *ngIf="authService.isCliente()">
        <div class="menu-label">MEU PORTAL</div>
        <a routerLink="/portal" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </span>
          <span>Minha Conta</span>
        </a>
      </div>

      <div class="sidebar-menu" *ngIf="!authService.isCliente()">
        <div class="menu-label">OPERAÇÃO</div>
        <a routerLink="/dashboard" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="20" x2="18" y2="10"></line>
              <line x1="12" y1="20" x2="12" y2="4"></line>
              <line x1="6" y1="20" x2="6" y2="14"></line>
            </svg>
          </span>
          <span>Dashboard</span>
        </a>
        <a routerLink="/central" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 7l-7 5 7 5V7z"></path>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
            </svg>
          </span>
          <span>Central</span>
        </a>
        <a routerLink="/historico" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </span>
          <span>Histórico</span>
        </a>

        <div class="menu-label">CADASTROS</div>
        <a routerLink="/clientes" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </span>
          <span>Clientes e Veículos</span>
        </a>
        <a routerLink="/tarifas" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
              <line x1="7" y1="7" x2="7.01" y2="7"></line>
            </svg>
          </span>
          <span>Tarifas e Planos</span>
        </a>
      </div>
    </aside>
  `,
  styles: [`
    .app-sidebar {
      width: 250px;
      background: #18181b;
      color: #a1a1aa;
      border-right: 1px solid #27272a;
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
      color: #71717a;
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
      color: #a1a1aa;
      text-decoration: none;
      font-size: 0.875rem;
      font-weight: 500;
      border-radius: 8px;
      transition: all 0.2s ease;
      margin-bottom: 0.2rem;
    }
    .menu-item:hover {
      background: #27272a;
      color: #fafafa;
    }
    .menu-item.active {
      background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
      color: #ffffff;
      font-weight: 600;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.35);
    }
    .menu-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
    }
  `],
})
export class SidebarComponent {
  authService = inject(AuthService);
}

