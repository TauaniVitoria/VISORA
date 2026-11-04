import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="visora-login-layout">
      <!-- Área esquerda: Apresentação (50%) -->
      <section class="presentation-pane">
        <div class="presentation-content">
          <a routerLink="/apresentacao" class="brand-badge" title="Voltar para a Página Inicial do VISORA">
            <div class="logo-box">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="4"></rect>
                <path d="M7 7l5 10 5-10"></path>
              </svg>
            </div>
            <span class="brand-title">VISORA</span>
          </a>

          <div class="hero-text">
            <h1>Seja bem-vindo(a)!</h1>
            <p class="hero-description">
              Inteligência e tecnologia para uma gestão de estacionamentos mais eficiente.
            </p>
          </div>

          <div class="presentation-footer">
            <span>VISORA Intelligent Mobility &copy; 2026</span>
          </div>
        </div>
      </section>

      <!-- Área direita: Formulário de Autenticação (50%) -->
      <section class="form-pane">
        <div class="form-wrapper">
          <div class="form-header">
            <h2>Acesse sua conta</h2>
            <p>Informe suas credenciais para gerenciar a operação</p>
          </div>

          <form (ngSubmit)="onSubmit()" class="login-form">
            <div class="error-banner" *ngIf="errorMessage">
              {{ errorMessage }}
            </div>

            <div class="form-group">
              <label for="email">E-mail de acesso</label>
              <div class="input-with-icon">
                <input
                  type="email"
                  id="email"
                  name="email"
                  [(ngModel)]="email"
                  required
                  placeholder="admin@visora.com"
                  class="form-control"
                />
              </div>
            </div>

            <div class="form-group">
              <label for="password">Senha</label>
              <div class="password-input-group">
                <input
                  [type]="showPassword ? 'text' : 'password'"
                  id="password"
                  name="password"
                  [(ngModel)]="password"
                  required
                  placeholder="••••••••"
                  class="form-control password-control"
                />
                <button
                  type="button"
                  class="btn-toggle-password"
                  (click)="togglePasswordVisibility()"
                  [attr.aria-label]="showPassword ? 'Ocultar senha' : 'Ver senha'"
                  tabindex="-1"
                >
                  <!-- Eye Open / Eye Off SVG -->
                  <svg *ngIf="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                  </svg>
                  <svg *ngIf="showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                    <line x1="1" y1="1" x2="23" y2="23"></line>
                  </svg>
                </button>
              </div>
            </div>

            <div class="form-extras">
              <label class="remember-label">
                <input type="checkbox" [(ngModel)]="rememberMe" name="rememberMe" />
                <span>Lembrar de mim</span>
              </label>
              <a routerLink="/forgot-password" class="forgot-link">Esqueci minha senha</a>
            </div>

            <button type="submit" class="btn-submit" [disabled]="loading">
              <span *ngIf="!loading">Entrar no VISORA</span>
              <span *ngIf="loading">Autenticando...</span>
            </button>

            <div class="back-to-landing">
              <a routerLink="/apresentacao" class="back-link">
                ← Conhecer a plataforma VISORA (Página Inicial)
              </a>
            </div>
          </form>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .visora-login-layout {
      min-height: 100vh;
      display: flex;
      width: 100%;
      background: #09090b;
      color: #f4f4f5;
    }

    /* ====== Lado Esquerdo: Apresentação (50%) ====== */
    .presentation-pane {
      width: 50%;
      background: linear-gradient(to top, rgba(217, 119, 6, 0.24) 0%, rgba(69, 26, 3, 0.45) 30%, #18181b 70%, #09090b 100%);
      padding: 4.5rem 4rem;
      display: flex;
      flex-direction: column;
      justify-content: center;
      position: relative;
      border-right: 1px solid #27272a;
      box-sizing: border-box;
    }

    .presentation-content {
      max-width: 500px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 460px;
      gap: 2.5rem;
    }

    .brand-badge {
      display: flex;
      align-items: center;
      gap: 0.85rem;
      text-decoration: none;
    }

    .back-to-landing {
      margin-top: 1.35rem;
      text-align: center;
    }

    .back-link {
      color: #a1a1aa;
      font-size: 0.82rem;
      text-decoration: none;
      transition: color 0.2s;
    }

    .back-link:hover {
      color: #f59e0b;
    }

    .logo-box {
      width: 48px;
      height: 48px;
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.35);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .brand-title {
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      color: #ffffff;
    }

    .hero-text h1 {
      font-size: 2.35rem;
      font-weight: 800;
      color: #ffffff;
      line-height: 1.15;
      margin: 0 0 0.85rem;
      letter-spacing: -0.02em;
    }

    .hero-description {
      font-size: 1.05rem;
      color: #a1a1aa;
      line-height: 1.55;
      margin: 0;
    }

    .presentation-footer {
      font-size: 0.75rem;
      color: #71717a;
      letter-spacing: 0.05em;
    }

    /* ====== Lado Direito: Formulário (50%) ====== */
    .form-pane {
      width: 50%;
      background: #09090b;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2rem;
      box-sizing: border-box;
    }

    .form-wrapper {
      width: 100%;
      max-width: 400px;
    }

    .form-header {
      margin-bottom: 2rem;
    }

    .form-header h2 {
      font-size: 1.65rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 0.4rem;
    }

    .form-header p {
      font-size: 0.875rem;
      color: #a1a1aa;
      margin: 0;
    }

    .form-group {
      margin-bottom: 1.25rem;
    }

    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: #d4d4d8;
      margin-bottom: 0.45rem;
    }

    .form-control {
      width: 100%;
      box-sizing: border-box;
      padding: 0.75rem 1rem;
      background: #18181b;
      border: 1px solid #27272a;
      border-radius: 8px;
      color: #ffffff;
      font-size: 0.9rem;
      outline: none;
      transition: all 0.2s ease;
    }

    .form-control:focus {
      border-color: #d97706;
      box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.2);
      background: #18181b;
    }

    .password-input-group {
      position: relative;
      display: flex;
      align-items: center;
    }

    .password-control {
      padding-right: 2.75rem;
    }

    .btn-toggle-password {
      position: absolute;
      right: 0.65rem;
      background: none;
      border: none;
      color: #71717a;
      cursor: pointer;
      padding: 0.35rem;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
      transition: color 0.2s;
    }

    .btn-toggle-password:hover {
      color: #f59e0b;
    }

    .form-extras {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.5rem;
      font-size: 0.825rem;
    }

    .remember-label {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      color: #a1a1aa;
      cursor: pointer;
      margin: 0;
      font-weight: normal;
    }

    .remember-label input[type="checkbox"] {
      cursor: pointer;
      accent-color: #d97706;
    }

    .forgot-link {
      color: #f59e0b;
      text-decoration: none;
      font-weight: 500;
      transition: color 0.2s;
    }

    .forgot-link:hover {
      color: #fbbf24;
      text-decoration: underline;
    }

    .btn-submit {
      width: 100%;
      padding: 0.85rem;
      background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
      color: #ffffff;
      border: none;
      border-radius: 8px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: filter 0.2s, transform 0.1s;
    }

    .btn-submit:hover:not(:disabled) {
      filter: brightness(1.08);
    }

    .btn-submit:active:not(:disabled) {
      transform: scale(0.99);
    }

    .btn-submit:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .error-banner {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid #ef4444;
      color: #fca5a5;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      font-size: 0.85rem;
      margin-bottom: 1.25rem;
    }

    /* ====== Responsividade: Mobile e Tablets ====== */
    @media (max-width: 900px) {
      .visora-login-layout {
        flex-direction: column;
      }
      .presentation-pane {
        width: 100%;
        padding: 2.5rem 1.5rem;
        border-right: none;
        border-bottom: 1px solid #1e293b;
      }
      .form-pane {
        width: 100%;
        padding: 2.5rem 1.5rem;
      }
      .hero-text h1 {
        font-size: 1.85rem;
      }
      .tech-highlights {
        display: none;
      }
    }
  `],
})
export class LoginComponent {
  email = '';
  password = '';
  showPassword = false;
  rememberMe = true;
  loading = false;
  errorMessage = '';

  private authService = inject(AuthService);
  private router = inject(Router);

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    if (!this.email || !this.password) return;
    this.loading = true;
    this.errorMessage = '';

    this.authService.login(this.email, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate([this.authService.homeRoute()]);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Falha ao autenticar. Verifique suas credenciais.';
      },
    });
  }
}
