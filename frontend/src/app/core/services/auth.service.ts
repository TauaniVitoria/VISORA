import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { AuthResponse } from '../models/models';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly apiUrl = 'http://localhost:8000/api/v1/auth';
  private readonly TOKEN_KEY = 'alpr_saas_token';
  private readonly USER_KEY = 'alpr_saas_user';
  private readonly TENANT_OVERRIDE_KEY = 'alpr_saas_tenant_override';

  currentUser = signal<AuthResponse | null>(this.getStoredUser());
  selectedTenantId = signal<string | null>(localStorage.getItem(this.TENANT_OVERRIDE_KEY));

  constructor(private http: HttpClient) {}

  login(email: string, senha: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, { email, senha }).pipe(
      tap((res) => {
        localStorage.setItem(this.TOKEN_KEY, res.access_token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(res));
        this.currentUser.set(res);
        if (res.estacionamento_id) {
          this.selectedTenantId.set(res.estacionamento_id);
        }
      })
    );
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.TENANT_OVERRIDE_KEY);
    this.currentUser.set(null);
    this.selectedTenantId.set(null);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  isSaaSAdmin(): boolean {
    return this.currentUser()?.perfil === 'SAAS_ADMIN';
  }

  setTenantOverride(tenantId: string): void {
    localStorage.setItem(this.TENANT_OVERRIDE_KEY, tenantId);
    this.selectedTenantId.set(tenantId);
  }

  private getStoredUser(): AuthResponse | null {
    const raw = localStorage.getItem(this.USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }
}

