import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';

/**
 * Atende duas rotas públicas:
 *  - /forgot-password: solicita o link de redefinição por e-mail;
 *  - /reset-password?token=...: define a nova senha com o token recebido.
 */
@Component({
  selector: 'app-password-recovery',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="container">
      <div class="card">
        <h1>{{ resetMode ? 'Definir nova senha' : 'Recuperar senha' }}</h1>

        <div class="banner success" *ngIf="successMessage">{{ successMessage }}</div>
        <div class="banner error" *ngIf="errorMessage">{{ errorMessage }}</div>

        <!-- Solicitar link -->
        <form *ngIf="!resetMode && !done" (ngSubmit)="requestLink()">
          <p class="hint">Informe o e-mail da sua conta. Se ele estiver cadastrado, enviaremos as instruções.</p>
          <label for="email">E-mail</label>
          <input id="email" name="email" type="email" [(ngModel)]="email" required class="form-control" />
          <button type="submit" class="btn-primary" [disabled]="loading || !email">
            {{ loading ? 'Enviando...' : 'Enviar instruções' }}
          </button>
        </form>

        <!-- Definir nova senha -->
        <form *ngIf="resetMode && !done" (ngSubmit)="submitReset()">
          <label for="pwd">Nova senha (mín. 8 caracteres)</label>
          <input id="pwd" name="pwd" type="password" [(ngModel)]="password" required minlength="8"
                 autocomplete="new-password" class="form-control" />
          <label for="pwd2">Confirmar nova senha</label>
          <input id="pwd2" name="pwd2" type="password" [(ngModel)]="confirm" required
                 autocomplete="new-password" class="form-control" />
          <button type="submit" class="btn-primary" [disabled]="loading || !canSubmitReset()">
            {{ loading ? 'Salvando...' : 'Redefinir senha' }}
          </button>
        </form>

        <div class="back"><a routerLink="/login">Voltar ao login</a></div>
      </div>
    </div>
  `,
  styles: [`
    .container { min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #09090b 0%, #18181b 100%); padding: 1.5rem; width: 100%; }
    .card { width: 100%; max-width: 420px; background: #18181b; border: 1px solid #27272a;
      border-radius: 16px; padding: 2rem; color: #f4f4f5; }
    h1 { font-size: 1.35rem; margin: 0 0 1rem; }
    .hint { color: #a1a1aa; font-size: 0.875rem; margin: 0 0 1rem; }
    label { display: block; font-size: 0.85rem; margin: 0.75rem 0 0.25rem; color: #d4d4d8; }
    .form-control { width: 100%; padding: 0.65rem 0.8rem; border-radius: 8px; border: 1px solid #3f3f46;
      background: #09090b; color: #fafafa; font-size: 0.95rem; box-sizing: border-box; }
    .btn-primary { width: 100%; margin-top: 1.25rem; padding: 0.7rem; border: none; border-radius: 8px;
      background: #d97706; color: #fff; font-weight: 600; cursor: pointer; }
    .btn-primary:hover:not(:disabled) { background: #b45309; }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    .banner { padding: 0.65rem 0.85rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 1rem; }
    .banner.success { background: #052e16; color: #86efac; }
    .banner.error { background: #450a0a; color: #fca5a5; }
    .back { text-align: center; margin-top: 1.25rem; font-size: 0.85rem; }
    .back a { color: #f59e0b; text-decoration: none; }
  `],
})
export class PasswordRecoveryComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  resetMode = false;
  token = '';
  email = '';
  password = '';
  confirm = '';
  loading = false;
  done = false;
  successMessage = '';
  errorMessage = '';

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
    this.resetMode = this.router.url.startsWith('/reset-password');
    if (this.resetMode && !this.token) {
      this.errorMessage = 'Link inválido. Solicite uma nova recuperação de senha.';
      this.done = true;
    }
  }

  canSubmitReset(): boolean {
    return this.password.length >= 8 && this.password === this.confirm;
  }

  requestLink(): void {
    this.loading = true;
    this.errorMessage = '';
    this.api.forgotPassword(this.email).subscribe({
      next: (res) => {
        this.loading = false;
        this.done = true;
        this.successMessage = res.detail;
      },
      error: () => {
        this.loading = false;
        this.errorMessage = 'Não foi possível processar o pedido. Tente novamente.';
      },
    });
  }

  submitReset(): void {
    if (!this.canSubmitReset()) {
      this.errorMessage = 'As senhas devem coincidir e ter pelo menos 8 caracteres.';
      return;
    }
    this.loading = true;
    this.errorMessage = '';
    this.api.resetPassword(this.token, this.password).subscribe({
      next: (res) => {
        this.loading = false;
        this.done = true;
        this.successMessage = res.detail + ' Você já pode entrar com a nova senha.';
      },
      error: (err) => {
        this.loading = false;
        const detail = err.error?.detail;
        this.errorMessage = typeof detail === 'string' ? detail : 'Não foi possível redefinir a senha.';
      },
    });
  }
}

