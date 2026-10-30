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
        <a routerLink="/alpr" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 7l-7 5 7 5V7z"></path>
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect>
            </svg>
          </span>
          <span>Central ALPR</span>
        </a>
        <a routerLink="/history" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
          </span>
          <span>Histórico ALPR</span>
        </a>

        <div class="menu-label">CADASTROS</div>
        <a routerLink="/customers" routerLinkActive="active" class="menu-item">
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
        <a routerLink="/tariffs-plans" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path>
              <line x1="7" y1="7" x2="7.01" y2="7"></line>
            </svg>
          </span>
          <span>Tarifas e Planos</span>
        </a>

        <div class="menu-label">FINANCEIRO & GOVERNANÇA</div>
        <a routerLink="/billing" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
              <line x1="1" y1="10" x2="23" y2="10"></line>
            </svg>
          </span>
          <span>Cobranças e Pagamentos</span>
        </a>
        <a routerLink="/audit" routerLinkActive="active" class="menu-item">
          <span class="menu-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </span>
          <span>Auditoria</span>
        </a>
      </div>

      <div class="sidebar-footer" *ngIf="!authService.isCliente()">
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
      display: flex;
      align-items: center;
      justify-content: center;
      width: 20px;
      height: 20px;
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

