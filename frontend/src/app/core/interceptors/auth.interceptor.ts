import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/** Endpoints públicos: um 401 aqui significa credencial inválida, não sessão expirada. */
const PUBLIC_AUTH_PATHS = ['/auth/login', '/auth/forgot-password', '/auth/reset-password'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const token = authService.getToken();
  const tenantOverride = authService.selectedTenantId();

  let headers = req.headers;

  if (token) {
    headers = headers.set('Authorization', `Bearer ${token}`);
  }

  if (tenantOverride && authService.isSaaSAdmin()) {
    headers = headers.set('X-Tenant-ID', tenantOverride);
  }

  const authReq = req.clone({ headers });
  return next(authReq).pipe(
    catchError((err: HttpErrorResponse) => {
      const isPublic = PUBLIC_AUTH_PATHS.some((p) => req.url.includes(p));
      if (err.status === 401 && !isPublic && token) {
        // Sessão expirada, revogada ou acesso desativado
        authService.logout();
        router.navigate(['/login']);
      }
      return throwError(() => err);
    })
  );
};
