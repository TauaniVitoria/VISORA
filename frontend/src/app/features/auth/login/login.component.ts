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
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <div class="logo-circle">🚗</div>
          <h1>Parking SaaS ALPR</h1>
          <p>Automação e Gestão de Estacionamentos</p>
        </div>

        <form (ngSubmit)="onSubmit()" class="login-form">
          <div class="error-banner" *ngIf="errorMessage">
            {{ errorMessage }}
          </div>

          <div class="form-group">
            <label for="email">E-mail</label>
            <input
              type="email"
              id="email"
              name="email"
              [(ngModel)]="email"
              required
              placeholder="seu.email@exemplo.com"
              class="form-control"
            />
          </div>

          <div class="form-group">
            <label for="password">Senha de acesso</label>
            <input
              type="password"
              id="password"
              name="password"
              [(ngModel)]="password"
              required
              placeholder="••••••••"
              class="form-control"
            />
          </div>

          <button type="submit" class="btn-primary" [disabled]="loading">
            <span *ngIf="!loading">Acessar Plataforma</span>
            <span *ngIf="loading">Autenticando...</span>
          </button>
        </form>

        <div class="forgot-link">
          <a routerLink="/forgot-password">Esqueci minha senha</a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0b0f17 0%, #1e293b 100%);
      padding: 1.5rem;
    }
    .login-card {
      width: 100%;
      max-width: 420px;
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 16px;
      padding: 2.5rem 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
      color: #f3f4f6;
    }
    .login-header {
      text-align: center;
      margin-bottom: 2rem;
    }
    .logo-circle {
      font-size: 2.5rem;
      margin-bottom: 0.75rem;
    }
    .login-header h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #38bdf8;
      margin: 0;
    }
    .login-header p {
      font-size: 0.85rem;
      color: #9ca3af;
      margin: 0.4rem 0 0;
    }
    .form-group {
      margin-bottom: 1.25rem;
    }
    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: #d1d5db;
      margin-bottom: 0.4rem;
    }
    .form-control {
      width: 100%;
      box-sizing: border-box;
      padding: 0.75rem 1rem;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 8px;
      color: #ffffff;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-control:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .btn-primary {
      width: 100%;
      padding: 0.85rem;
      background: #0284c7;
      color: #ffffff;
      border: none;
      border-radius: 8px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
      margin-top: 0.5rem;
    }
    .btn-primary:hover:not(:disabled) {
      background: #0369a1;
    }
    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .error-banner {
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid #ef4444;
      color: #fca5a5;
      padding: 0.75rem;
      border-radius: 8px;
      font-size: 0.85rem;
      margin-bottom: 1.25rem;
    }
    .forgot-link {
      text-align: center;
      margin-top: 1.25rem;
      font-size: 0.85rem;
    }
    .forgot-link a { color: #60a5fa; text-decoration: none; }
    .forgot-link a:hover { text-decoration: underline; }
  `],
})
export class LoginComponent {
  email = '';
  password = '';
  loading = false;
  errorMessage = '';

  private authService = inject(AuthService);
  private router = inject(Router);

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

