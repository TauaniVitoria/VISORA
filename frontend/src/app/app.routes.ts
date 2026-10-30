import { Routes } from '@angular/router';
import { clienteGuard, staffGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/auth/login/login.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { CustomersComponent } from './features/customers/customers.component';
import { TariffsPlansComponent } from './features/tariffs-plans/tariffs-plans.component';
import { MovementsComponent } from './features/movements/movements.component';
import { BillingComponent } from './features/billing/billing.component';
import { AuditComponent } from './features/audit/audit.component';
import { AlprComponent } from './features/alpr/alpr.component';
import { PortalComponent } from './features/portal/portal.component';
import { PasswordRecoveryComponent } from './features/auth/password-recovery/password-recovery.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'forgot-password',
    component: PasswordRecoveryComponent,
  },
  {
    path: 'reset-password',
    component: PasswordRecoveryComponent,
  },
  {
    path: 'portal',
    component: PortalComponent,
    canActivate: [clienteGuard],
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'alpr',
    component: AlprComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'customers',
    component: CustomersComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'tariffs-plans',
    component: TariffsPlansComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'history',
    component: MovementsComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'billing',
    component: BillingComponent,
    canActivate: [staffGuard],
  },
  {
    path: 'audit',
    component: AuditComponent,
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
