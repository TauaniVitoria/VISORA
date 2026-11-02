import { Routes } from '@angular/router';
import { clienteGuard, staffGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'forgot-password',
    loadComponent: () =>
      import('./features/auth/password-recovery/password-recovery.component').then(
        (m) => m.PasswordRecoveryComponent
      ),
  },
  {
    path: 'reset-password',
    loadComponent: () =>
      import('./features/auth/password-recovery/password-recovery.component').then(
        (m) => m.PasswordRecoveryComponent
      ),
  },
  {
    path: 'portal',
    loadComponent: () =>
      import('./features/portal/portal.component').then((m) => m.PortalComponent),
    canActivate: [clienteGuard],
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    canActivate: [staffGuard],
  },
  {
    path: 'alpr',
    loadComponent: () =>
      import('./features/alpr/alpr.component').then((m) => m.AlprComponent),
    canActivate: [staffGuard],
  },
  {
    path: 'customers',
    loadComponent: () =>
      import('./features/customers/customers.component').then((m) => m.CustomersComponent),
    canActivate: [staffGuard],
  },
  {
    path: 'tariffs-plans',
    loadComponent: () =>
      import('./features/tariffs-plans/tariffs-plans.component').then(
        (m) => m.TariffsPlansComponent
      ),
    canActivate: [staffGuard],
  },
  {
    path: 'history',
    loadComponent: () =>
      import('./features/movements/movements.component').then((m) => m.MovementsComponent),
    canActivate: [staffGuard],
  },
  {
    path: 'billing',
    loadComponent: () =>
      import('./features/billing/billing.component').then((m) => m.BillingComponent),
    canActivate: [staffGuard],
  },
  {
    path: 'audit',
    loadComponent: () =>
      import('./features/audit/audit.component').then((m) => m.AuditComponent),
    canActivate: [staffGuard],
  },
  {
    path: '',
    redirectTo: 'dashboard',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: 'dashboard',
  },
];
