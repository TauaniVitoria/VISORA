import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
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
  return next(authReq);
};

