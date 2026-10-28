import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="app-navbar">
      <div class="brand">
        <span class="logo-icon">🚗</span>
        <div class="brand-text">
          <span class="brand-title">Parking SaaS</span>
          <span class="brand-subtitle">ALPR Intelligent Platform</span>
        </div>
      </div>

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
      background: #111827;
      color: #f9fafb;
      border-bottom: 1px solid #1f2937;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .logo-icon {
      font-size: 1.75rem;
      background: #1f2937;
      padding: 0.25rem 0.5rem;
      border-radius: 8px;
    }
    .brand-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: #38bdf8;
      display: block;
      line-height: 1.2;
    }
    .brand-subtitle {
      font-size: 0.75rem;
      color: #9ca3af;
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
      background: #374151;
      color: #e5e7eb;
    }
    .role-badge.saas_admin {
      background: #7c3aed;
      color: #fff;
    }
    .role-badge.estacionamento_admin {
      background: #0284c7;
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
      color: #9ca3af;
    }
    .btn-logout {
      display: flex;
      align-items: center;
      gap: 0.4rem;
      background: #1f2937;
      border: 1px solid #374151;
      color: #f87171;
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 500;
      transition: background 0.2s;
    }
    .btn-logout:hover {
      background: #2d1a1e;
      border-color: #ef4444;
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
