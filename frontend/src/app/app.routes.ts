import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { LoginComponent } from './features/auth/login/login.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { CustomersComponent } from './features/customers/customers.component';
import { TariffsPlansComponent } from './features/tariffs-plans/tariffs-plans.component';
import { MovementsComponent } from './features/movements/movements.component';
import { BillingComponent } from './features/billing/billing.component';
import { AuditComponent } from './features/audit/audit.component';
import { AlprComponent } from './features/alpr/alpr.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard],
  },
  {
    path: 'alpr',
    component: AlprComponent,
    canActivate: [authGuard],
  },
  {
    path: 'customers',
    component: CustomersComponent,
    canActivate: [authGuard],
  },
  {
    path: 'tariffs-plans',
    component: TariffsPlansComponent,
    canActivate: [authGuard],
  },
  {
    path: 'history',
    component: MovementsComponent,
    canActivate: [authGuard],
  },
  {
    path: 'billing',
    component: BillingComponent,
    canActivate: [authGuard],
  },
  {
    path: 'audit',
    component: AuditComponent,
    canActivate: [authGuard],
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
