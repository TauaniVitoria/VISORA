import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <header class="app-navbar">
      <a routerLink="/apresentacao" class="brand" title="Ver Página Inicial / Apresentação do VISORA">
        <div class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="4"></rect>
            <path d="M7 7l5 10 5-10"></path>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-title">VISORA</span>
          <span class="brand-subtitle">Inteligência em Estacionamentos</span>
        </div>
      </a>

      <div class="user-section" *ngIf="authService.currentUser() as user">
        <div class="role-badge" [ngClass]="user.perfil.toLowerCase()">
          {{ user.perfil }}
        </div>
        <div class="user-info">
          <span class="user-name">{{ user.nome }}</span>
          <span class="user-email">{{ user.email }}</span>
        </div>
        <button class="btn-logout" (click)="logout()">
          <span>Sair</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
    </header>
  `,
  styles: [`
    .app-navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.75rem 2rem;
      background: #18181b;
      color: #fafafa;
      border-bottom: 1px solid #27272a;
      box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
    }
    .logo-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #27272a;
      border: 1px solid rgba(245, 158, 11, 0.25);
      padding: 0.35rem;
      border-radius: 8px;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: #f59e0b;
      display: block;
      line-height: 1.2;
    }
    .brand-subtitle {
      font-size: 0.75rem;
      color: #a1a1aa;
      letter-spacing: 0.05em;
    }
    .user-section {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .role-badge {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      text-transform: uppercase;
      background: #27272a;
      color: #e4e4e7;
    }
    .role-badge.saas_admin {
      background: #b45309;
      color: #fff;
    }
    .role-badge.estacionamento_admin {
      background: #d97706;
      color: #fff;
    }
    .user-info {
      display: flex;
      flex-direction: column;
      text-align: right;
    }
    .user-name {
      font-size: 0.875rem;
      font-weight: 600;
    }
    .user-email {
      font-size: 0.75rem;
      color: #a1a1aa;
    }
    .btn-logout {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      background: #27272a;
      border: 1px solid #f59e0b;
      color: #f59e0b;
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 500;
      transition: all 0.2s;
    }
    .btn-logout:hover {
      background: rgba(245, 158, 11, 0.15);
      border-color: #fbbf24;
      color: #fbbf24;
    }
  `],
})
export class NavbarComponent {
  authService = inject(AuthService);
  private router = inject(Router);

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}

