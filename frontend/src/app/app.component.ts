import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { NavbarComponent } from './shared/navbar/navbar.component';
import { SidebarComponent } from './shared/sidebar/sidebar.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, NavbarComponent, SidebarComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  authService = inject(AuthService);
  private router = inject(Router);

  showInternalShell(): boolean {
    if (!this.authService.isAuthenticated()) {
      return false;
    }
    const cleanUrl = this.router.url.split('?')[0].split('#')[0];
    const publicRoutes = ['/', '/apresentacao', '/login', '/forgot-password', '/reset-password'];
    return !publicRoutes.includes(cleanUrl);
  }
}
