import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/** Exige sessão autenticada. */
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/login']);
};

/** Telas administrativas: o perfil CLIENTE é redirecionado ao portal. */
export const staffGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  return authService.isCliente() ? router.createUrlTree(['/portal']) : true;
};

/** Portal do cliente: administradores são redirecionados ao dashboard. */
export const clienteGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  return authService.isCliente() ? true : router.createUrlTree(['/dashboard']);
};
