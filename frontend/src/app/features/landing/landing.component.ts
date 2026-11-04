import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

interface ModulePreview {
  id: 'central' | 'dashboard' | 'clientes';
  title: string;
  tag: string;
  summary: string;
  highlights: string[];
}

interface RealPassageSample {
  plate: string;
  format: 'MERCOSUL' | 'ANTIGO';
  vehicleDesc: string;
  frameImg: string;
  cropImg: string;
  vehImg: string;
  eventLabel: string;
  chargeType: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="landing-root" id="inicio">
      <!-- ====== TOP NAVIGATION BAR ====== -->
      <header class="landing-header">
        <div class="header-container">
          <a class="brand-logo" (click)="scrollToSection('inicio')" role="button" tabindex="0">
            <span class="logo-mark">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="4"></rect>
                <path d="M7 7l5 10 5-10"></path>
              </svg>
            </span>
            <span class="logo-name">VISORA</span>
          </a>

          <nav class="header-nav" [class.mobile-open]="mobileMenuOpen">
            <a (click)="scrollToSection('sobre')" role="button" tabindex="0">Sobre</a>
            <a (click)="scrollToSection('modulos')" role="button" tabindex="0">Módulos</a>
            <a (click)="scrollToSection('beneficios')" role="button" tabindex="0">Benefícios</a>
            <a (click)="scrollToSection('capturas')" role="button" tabindex="0">Processamento</a>
            <a (click)="scrollToSection('contato')" role="button" tabindex="0">Contato</a>
            <a
              [routerLink]="authService.isAuthenticated() ? authService.homeRoute() : '/login'"
              class="nav-cta-pill"
            >
              <span>{{ authService.isAuthenticated() ? 'Ir ao Painel' : 'Acessar Sistema' }}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </a>
          </nav>

          <button
            type="button"
            class="mobile-menu-btn"
            (click)="mobileMenuOpen = !mobileMenuOpen"
            aria-label="Alternar menu de navegação"
          >
            <svg *ngIf="!mobileMenuOpen" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
            <svg *ngIf="mobileMenuOpen" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </header>

      <!-- ====== SEÇÃO 1: HERO MINIMALISTA & FUTURISTA ====== -->
      <section class="hero-section" id="sobre">
        <div class="hero-container">
          <div class="hero-copy">
            <h1 class="hero-headline">
              <span>Visão,</span>
              <span>Controle,</span>
              <span class="emerald-accent-text">Eficiência.</span>
            </h1>

            <p class="hero-slogan">
              VISORA — Seu estacionamento mais inteligente.
            </p>

            <p class="hero-description">
              Centralize e simplifique a administração do seu pátio integrando visão computacional,
              acompanhamento de veículos, entradas, saídas, clientes, movimentações e cobranças em um único ambiente.
            </p>
          </div>

          <div class="hero-studio-visual">
            <img
              src="assets/alpr/hero_car_dark.jpg"
              alt="VISORA — Gestão Inteligente de Estacionamentos"
              class="hero-studio-img"
            />
          </div>
        </div>

        <div class="scroll-down-wrap">
          <button
            type="button"
            class="scroll-chevron-btn"
            (click)="scrollToSection('modulos')"
            aria-label="Rolar para os módulos da plataforma"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
      </section>

      <!-- ====== SEÇÃO 2: MÓDULOS DA PLATAFORMA ====== -->
      <section class="modules-section" id="modulos">
        <div class="section-container">
          <div class="section-heading">
            <span class="section-eyebrow">ARQUITETURA OPERACIONAL</span>
            <h2>Módulos da Plataforma</h2>
            <p>Recursos integrados para portaria, visão computacional e faturamento</p>
          </div>

          <div class="models-grid">
            <article
              *ngFor="let mod of modules"
              class="model-card"
              [class.selected]="selectedModule.id === mod.id"
              (click)="selectModule(mod)"
              tabindex="0"
              role="button"
              (keydown.enter)="selectModule(mod)"
            >
              <span class="model-card-tag">{{ mod.tag }}</span>
              <div class="model-card-bottom">
                <h3>{{ mod.title }}</h3>
                <span class="model-card-arrow" aria-hidden="true">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </span>
              </div>
            </article>
          </div>

          <div class="module-detail-bar">
            <div class="module-detail-info">
              <span class="detail-badge">{{ selectedModule.tag }}</span>
              <h4>{{ selectedModule.title }}</h4>
              <p>{{ selectedModule.summary }}</p>
              <ul class="detail-chips">
                <li *ngFor="let item of selectedModule.highlights">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <!-- ====== SEÇÃO 3: BENEFÍCIOS ("MAIS CONTROLE. MAIS ORGANIZAÇÃO. MAIS EFICIÊNCIA.") ====== -->
      <section class="spotlight-section" id="beneficios">
        <div class="section-container">
          <div class="spotlight-dark-card">
            <span class="dark-card-eyebrow">BENEFÍCIOS OPERACIONAIS</span>
            <h3>Mais controle. Mais organização. Mais eficiência.</h3>
            <p class="dark-card-intro">
              O VISORA unifica a leitura automática de placas nas câmeras com o controle financeiro e cadastral do estacionamento:
            </p>

            <ul class="benefits-list">
              <li *ngFor="let benefit of benefits">
                <span class="benefit-check" aria-hidden="true">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                </span>
                <span>{{ benefit }}</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- ====== SEÇÃO 4: PROCESSO DE IDENTIFICAÇÃO ====== -->
      <section class="captures-section" id="capturas">
        <div class="section-container">
          <div class="section-heading">
            <span class="section-eyebrow">VISÃO COMPUTACIONAL EM TEMPO REAL</span>
            <h2>Processo de identificação</h2>
            <p>Passagens reais processadas por visão computacional do VISORA e convertidas em movimentações</p>
          </div>

          <div class="vehicle-stage">
            <div class="alpr-live-frame">
              <img
                [src]="activeSample.frameImg"
                [alt]="'Reconhecimento da placa ' + activeSample.plate"
                class="hero-capture-img"
              />
              <div class="alpr-hud-badge top-left">
                <span class="pulse-dot"></span>
                <span>PIPELINE • YOLOv8 + CRNN</span>
              </div>

              <div class="alpr-hud-plate-card">
                <div class="hud-crop-box">
                  <img [src]="activeSample.cropImg" [alt]="'Recorte da placa ' + activeSample.plate" />
                </div>
                <div class="hud-plate-meta">
                  <span class="hud-plate-label">PLACA RECONHECIDA ({{ activeSample.format }})</span>
                  <strong class="hud-plate-number">{{ activeSample.plate }}</strong>
                  <span class="hud-plate-status">{{ activeSample.eventLabel }} • {{ activeSample.chargeType }}</span>
                </div>
              </div>
            </div>

            <!-- Seletor rápido de passagens reais -->
            <div class="sample-switcher" role="group" aria-label="Alternar amostra real de reconhecimento">
              <button
                *ngFor="let sample of realSamples; let idx = index"
                type="button"
                class="sample-pill"
                [class.active]="selectedSampleIndex === idx"
                (click)="selectSample(idx)"
              >
                <span class="sample-plate">{{ sample.plate }}</span>
                <span class="sample-fmt">{{ sample.format }}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- ====== SEÇÃO 5: FORMULÁRIO HORIZONTAL DE INTERESSE / CONTATO ====== -->
      <section class="inquiry-section" id="contato">
        <div class="section-container">
          <div class="inquiry-header">
            <span class="section-eyebrow">DEMONSTRAÇÃO COMERCIAL</span>
            <h2>Você está procurando modernizar a operação do seu estacionamento?</h2>
            <p>Deixe os dados do seu pátio e nossa equipe entrará em contato com uma demonstração guiada</p>
          </div>

          <div class="inquiry-card">
            <form (ngSubmit)="submitLeadForm()" class="inquiry-form">
              <div class="inquiry-inputs-row">
                <input
                  type="text"
                  name="leadName"
                  [(ngModel)]="leadForm.nome"
                  placeholder="Seu nome"
                  required
                  class="inquiry-input"
                />
                <input
                  type="text"
                  name="leadCompany"
                  [(ngModel)]="leadForm.estacionamento"
                  placeholder="Estacionamento / Empresa"
                  required
                  class="inquiry-input"
                />
                <input
                  type="email"
                  name="leadEmail"
                  [(ngModel)]="leadForm.email"
                  placeholder="E-mail"
                  required
                  class="inquiry-input"
                />
                <input
                  type="text"
                  name="leadPhone"
                  [(ngModel)]="leadForm.telefone"
                  placeholder="Telefone / WhatsApp"
                  required
                  class="inquiry-input"
                />
                <button type="submit" class="btn-inquiry-submit">
                  Enviar
                </button>
              </div>

              <label class="inquiry-consent">
                <input
                  type="checkbox"
                  name="leadConsent"
                  [(ngModel)]="leadForm.consentimento"
                />
                <span>
                  De acordo com a LGPD, concordo em fornecer os dados acima para que a equipe comercial do VISORA
                  entre em contato para apresentar a plataforma e esclarecer dúvidas operacionais.
                </span>
              </label>

              <div *ngIf="leadFeedback" class="inquiry-feedback" [class.error]="leadError">
                {{ leadFeedback }}
              </div>
            </form>
          </div>
        </div>
      </section>

      <!-- ====== SEÇÃO 6: RODAPÉ INSTITUCIONAL ====== -->
      <footer class="landing-footer">
        <div class="footer-container">
          <!-- Coluna 1: Logotipo, descrição e redes sociais -->
          <div class="footer-col brand-col">
            <div class="footer-logo">
              <span class="logo-mark">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                  <rect x="3" y="3" width="18" height="18" rx="4"></rect>
                  <path d="M7 7l5 10 5-10"></path>
                </svg>
              </span>
              <span class="logo-name">VISORA</span>
            </div>

            <p class="footer-desc">
              Plataforma SaaS de gestão de estacionamentos através do reconhecimento automático de placas por visão computacional.
            </p>

            <div class="footer-socials" aria-label="Redes sociais do VISORA">
              <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" aria-label="Instagram @visoraoficial" title="Instagram: @visoraoficial">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                  <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                  <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                </svg>
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn VISORA" title="LinkedIn: /company/visora-tech">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect x="2" y="9" width="4" height="12"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
              </a>
              <a href="https://youtube.com" target="_blank" rel="noopener noreferrer" aria-label="YouTube VISORA" title="YouTube: @visoraoficial">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z"></path>
                  <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02"></polygon>
                </svg>
              </a>
              <a href="https://wa.me/5514988429100" target="_blank" rel="noopener noreferrer" aria-label="WhatsApp Suporte VISORA" title="WhatsApp: (14) 98842-9100">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                </svg>
              </a>
            </div>
          </div>

          <!-- Coluna 2: Contato & Suporte -->
          <div class="footer-col contact-col">
            <h4>Contato & Suporte</h4>
            <div class="footer-contact-details">
              <p><strong>Comercial:</strong> contato&#64;visora.com.br</p>
              <p><strong>Suporte Técnico:</strong> suporte&#64;visora.com.br</p>
              <p><strong>Telefone / WhatsApp:</strong> (14) 3234-9100 • 0800 774 2026</p>
              <p><strong>Endereço:</strong> Av. Getúlio Vargas, 18-45, Sala 804 — Jardim América, Bauru - SP</p>
            </div>
          </div>

          <!-- Coluna 3: Newsletter -->
          <div class="footer-col newsletter-col">
            <h4>Inscreva-se</h4>
            <p>
              Informe seu e-mail para receber novidades sobre atualizações e recursos do VISORA.
            </p>
            <form (ngSubmit)="submitNewsletter()" class="newsletter-form">
              <input
                type="email"
                name="newsletterEmail"
                [(ngModel)]="newsletterEmail"
                placeholder="E-mail"
                required
                class="newsletter-input"
              />
              <button type="submit" class="btn-newsletter-ok">OK</button>
            </form>
            <span *ngIf="newsletterMessage" class="newsletter-feedback">
              {{ newsletterMessage }}
            </span>
          </div>
        </div>

        <div class="footer-bottom">
          <span>&copy; 2026 VISORA — Todos os direitos reservados.</span>
        </div>
      </footer>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
      background: #030304;
      color: #f4f4f5;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .landing-root {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: #030304;
      color: #f4f4f5;
      overflow-x: hidden;
    }

    /* ====== HEADER MINIMALISTA ESCURO ====== */
    .landing-header {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(3, 3, 4, 0.88);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .header-container {
      max-width: 1120px;
      margin: 0 auto;
      padding: 1.05rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .brand-logo {
      display: inline-flex;
      align-items: center;
      gap: 0.65rem;
      cursor: pointer;
      user-select: none;
    }

    .logo-mark {
      width: 34px;
      height: 34px;
      border-radius: 9px;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.3);
      color: #f59e0b;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .logo-name {
      font-size: 1.05rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      color: #fafafa;
    }

    .header-nav {
      display: flex;
      align-items: center;
      gap: 2rem;
    }

    .header-nav a {
      font-size: 0.84rem;
      font-weight: 500;
      color: #a1a1aa;
      cursor: pointer;
      text-decoration: none;
      transition: color 0.2s ease;
    }

    .header-nav a:hover {
      color: #f59e0b;
    }

    .nav-cta-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.38);
      color: #f59e0b !important;
      padding: 0.5rem 1.15rem;
      border-radius: 999px;
      font-size: 0.8rem !important;
      font-weight: 600 !important;
      transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }

    .nav-cta-pill:hover {
      background: #f59e0b;
      border-color: #f59e0b;
      color: #030304 !important;
    }

    .mobile-menu-btn {
      display: none;
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      padding: 0.4rem;
      color: #fafafa;
    }

    /* ====== HERO SECTION (FUNDO ESCURO ESTÚDIO + DETALHES AMARELO ÂMBAR) ====== */
    .hero-section {
      max-width: 1120px;
      width: 100%;
      margin: 0 auto;
      padding: 4rem 1.5rem 2rem;
    }

    .hero-container {
      display: grid;
      grid-template-columns: 1fr 1.15fr;
      gap: 2rem;
      align-items: center;
    }

    .hero-headline {
      display: flex;
      flex-direction: column;
      font-size: clamp(2.65rem, 4.8vw, 4rem);
      font-weight: 800;
      line-height: 1.05;
      letter-spacing: -0.035em;
      color: #fafafa;
      margin: 0 0 1.25rem;
    }

    .emerald-accent-text {
      color: #f59e0b;
    }

    .hero-slogan {
      font-size: 1rem;
      font-weight: 600;
      color: #e4e4e7;
      margin: 0 0 0.85rem;
      letter-spacing: -0.01em;
    }

    .hero-description {
      font-size: 0.925rem;
      line-height: 1.65;
      color: #9ca3af;
      margin: 0;
      max-width: 490px;
    }

    .hero-studio-visual {
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .hero-studio-img {
      width: 100%;
      max-width: 600px;
      height: auto;
      display: block;
      object-fit: contain;
      mix-blend-mode: lighten;
    }

    .scroll-down-wrap {
      display: flex;
      justify-content: center;
      margin-top: 2rem;
    }

    .scroll-chevron-btn {
      background: none;
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #71717a;
      width: 38px;
      height: 38px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      cursor: pointer;
      transition: color 0.2s ease, border-color 0.2s ease;
    }

    .scroll-chevron-btn:hover {
      color: #f59e0b;
      border-color: rgba(245, 158, 11, 0.38);
    }

    /* ====== SECTIONS SHARED ====== */
    .section-container {
      max-width: 1120px;
      margin: 0 auto;
      padding: 3.25rem 1.5rem;
    }

    .section-heading {
      margin-bottom: 1.65rem;
    }

    .section-eyebrow {
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #f59e0b;
      text-transform: uppercase;
      margin-bottom: 0.45rem;
    }

    .section-heading h2 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #fafafa;
      letter-spacing: -0.02em;
      margin: 0 0 0.3rem;
    }

    .section-heading p {
      font-size: 0.875rem;
      color: #9ca3af;
      margin: 0;
    }

    /* ====== SEÇÃO 2: MÓDULOS MINIMALISTAS ====== */
    .models-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.15rem;
    }

    .model-card {
      padding: 1.45rem;
      border-radius: 14px;
      cursor: pointer;
      background: #0a0b0e;
      color: #fafafa;
      border: 1px solid rgba(255, 255, 255, 0.07);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 135px;
      transition: border-color 0.2s ease, background 0.2s ease;
    }

    .model-card:hover {
      border-color: rgba(245, 158, 11, 0.35);
      background: #0f0e0c;
    }

    .model-card.selected {
      border-color: #f59e0b;
      background: #12100b;
    }

    .model-card-tag {
      align-self: flex-start;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.28);
      color: #fbbf24;
      font-size: 0.66rem;
      font-weight: 600;
      padding: 0.22rem 0.65rem;
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .model-card-bottom {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-top: 1.35rem;
    }

    .model-card-bottom h3 {
      font-size: 1rem;
      font-weight: 600;
      margin: 0;
      color: #fafafa;
    }

    .model-card-arrow {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.05);
      color: #a1a1aa;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: background 0.2s, color 0.2s;
    }

    .model-card.selected .model-card-arrow,
    .model-card:hover .model-card-arrow {
      background: rgba(245, 158, 11, 0.18);
      color: #fbbf24;
    }

    .module-detail-bar {
      margin-top: 1.15rem;
      background: #0a0b0e;
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 14px;
      padding: 1.5rem 1.65rem;
    }

    .detail-badge {
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      text-transform: uppercase;
      color: #f59e0b;
      letter-spacing: 0.08em;
      margin-bottom: 0.3rem;
    }

    .module-detail-info h4 {
      font-size: 1.1rem;
      font-weight: 700;
      color: #fafafa;
      margin: 0 0 0.4rem;
    }

    .module-detail-info p {
      font-size: 0.875rem;
      color: #9ca3af;
      margin: 0 0 0.9rem;
      line-height: 1.55;
    }

    .detail-chips {
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      padding: 0;
      margin: 0;
    }

    .detail-chips li {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: #d4d4d8;
      font-size: 0.75rem;
      font-weight: 500;
      padding: 0.28rem 0.75rem;
      border-radius: 999px;
    }

    /* ====== SEÇÃO 3: BENEFÍCIOS ====== */
    .spotlight-dark-card {
      background: #0a0b0e;
      color: #fafafa;
      border-radius: 16px;
      padding: 2.4rem;
      border: 1px solid rgba(255, 255, 255, 0.07);
    }

    .dark-card-eyebrow {
      display: inline-block;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #f59e0b;
      text-transform: uppercase;
      margin-bottom: 0.45rem;
    }

    .spotlight-dark-card h3 {
      font-size: 1.5rem;
      font-weight: 700;
      line-height: 1.25;
      color: #ffffff;
      letter-spacing: -0.02em;
      margin: 0 0 0.55rem;
    }

    .dark-card-intro {
      font-size: 0.875rem;
      color: #9ca3af;
      line-height: 1.55;
      margin: 0 0 1.4rem;
    }

    .benefits-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.85rem 1.75rem;
    }

    .benefits-list li {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      font-size: 0.86rem;
      color: #e4e4e7;
    }

    .benefit-check {
      width: 22px;
      height: 22px;
      border-radius: 6px;
      background: rgba(245, 158, 11, 0.14);
      color: #f59e0b;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    /* ====== SEÇÃO 4: PROCESSO DE IDENTIFICAÇÃO ====== */
    .vehicle-stage {
      position: relative;
      z-index: 1;
      max-width: 760px;
      margin: 0 auto;
    }

    .alpr-live-frame {
      position: relative;
      border-radius: 20px;
      overflow: hidden;
      background: #18181b;
      box-shadow: 0 22px 45px -12px rgba(24, 24, 27, 0.22);
      border: 1px solid #27272a;
    }

    .hero-capture-img {
      width: 100%;
      height: 360px;
      object-fit: cover;
      display: block;
    }

    .alpr-hud-badge {
      position: absolute;
      top: 14px;
      left: 14px;
      background: rgba(9, 9, 11, 0.82);
      backdrop-filter: blur(8px);
      color: #fafafa;
      border: 1px solid rgba(245, 158, 11, 0.4);
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
    }

    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #f59e0b;
      box-shadow: 0 0 8px #f59e0b;
    }

    .alpr-hud-plate-card {
      position: absolute;
      bottom: 14px;
      right: 14px;
      left: 14px;
      background: rgba(9, 9, 11, 0.88);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 14px;
      padding: 0.75rem 1rem;
      display: flex;
      align-items: center;
      gap: 0.9rem;
    }

    .hud-crop-box {
      background: #ffffff;
      padding: 0.2rem;
      border-radius: 6px;
      flex-shrink: 0;
    }

    .hud-crop-box img {
      height: 36px;
      width: auto;
      display: block;
      border-radius: 4px;
    }

    .hud-plate-meta {
      display: flex;
      flex-direction: column;
      color: #ffffff;
    }

    .hud-plate-label {
      font-size: 0.65rem;
      color: #a1a1aa;
      font-weight: 600;
      letter-spacing: 0.05em;
    }

    .hud-plate-number {
      font-family: monospace;
      font-size: 1.2rem;
      color: #f59e0b;
      letter-spacing: 0.1em;
    }

    .hud-plate-status {
      font-size: 0.72rem;
      color: #d4d4d8;
    }

    .sample-switcher {
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
      margin-top: 0.75rem;
    }

    .sample-pill {
      background: #ffffff;
      border: 1px solid #e7e5e4;
      border-radius: 999px;
      padding: 0.35rem 0.75rem;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.75rem;
      color: #52525b;
      cursor: pointer;
    }

    .sample-pill.active {
      background: #18181b;
      color: #ffffff;
      border-color: #18181b;
    }

    .sample-plate {
      font-family: monospace;
      font-weight: 700;
    }

    .sample-fmt {
      font-size: 0.65rem;
      opacity: 0.8;
    }

    /* ====== SEÇÃO 5: FORMULÁRIO HORIZONTAL DE INTERESSE ====== */
    .inquiry-header {
      margin-bottom: 1.35rem;
    }

    .inquiry-header h2 {
      font-size: 1.4rem;
      font-weight: 700;
      color: #fafafa;
      margin: 0 0 0.3rem;
      max-width: 560px;
      line-height: 1.3;
      letter-spacing: -0.02em;
    }

    .inquiry-header p {
      font-size: 0.85rem;
      color: #9ca3af;
      margin: 0;
    }

    .inquiry-card {
      background: #0a0b0e;
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 16px;
      padding: 1.85rem;
    }

    .inquiry-inputs-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr) auto;
      gap: 0.75rem;
      margin-bottom: 1rem;
    }

    .inquiry-input {
      width: 100%;
      box-sizing: border-box;
      padding: 0.7rem 0.9rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      font-size: 0.825rem;
      background: #030304;
      color: #fafafa;
      outline: none;
      transition: border-color 0.2s;
    }

    .inquiry-input::placeholder {
      color: #71717a;
    }

    .inquiry-input:focus {
      border-color: #f59e0b;
    }

    .btn-inquiry-submit {
      background: #f59e0b;
      color: #030304;
      border: none;
      border-radius: 8px;
      padding: 0.7rem 1.75rem;
      font-size: 0.825rem;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
    }

    .btn-inquiry-submit:hover {
      background: #fbbf24;
    }

    .inquiry-consent {
      display: flex;
      align-items: flex-start;
      gap: 0.55rem;
      font-size: 0.74rem;
      color: #9ca3af;
      line-height: 1.45;
      cursor: pointer;
    }

    .inquiry-consent input {
      margin-top: 0.15rem;
      accent-color: #f59e0b;
    }

    .inquiry-feedback {
      margin-top: 0.9rem;
      padding: 0.65rem 0.95rem;
      border-radius: 8px;
      font-size: 0.8rem;
      font-weight: 500;
      background: rgba(245, 158, 11, 0.12);
      border: 1px solid rgba(245, 158, 11, 0.35);
      color: #fbbf24;
    }

    .inquiry-feedback.error {
      background: rgba(239, 68, 68, 0.12);
      border-color: rgba(239, 68, 68, 0.3);
      color: #fca5a5;
    }

    /* ====== SEÇÃO 6: RODAPÉ ====== */
    .landing-footer { margin-top: auto; background: #050507; border-top: 1px solid rgba(255, 255, 255, 0.06); padding: 3.25rem 1.5rem 1.5rem; }
    .footer-container { max-width: 1120px; margin: 0 auto; display: grid; grid-template-columns: 1.1fr 1.1fr 1fr; gap: 2.25rem; padding-bottom: 2.25rem; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
    .footer-logo { display: inline-flex; align-items: center; gap: 0.6rem; margin-bottom: 0.8rem; }
    .footer-tagline { font-size: 0.825rem; font-weight: 600; color: #e4e4e7; margin: 0 0 0.45rem; }
    .footer-desc { font-size: 0.78rem; color: #9ca3af; line-height: 1.55; margin: 0 0 1.15rem; }
    .footer-socials { display: flex; align-items: center; gap: 0.65rem; }
    .footer-socials a { width: 34px; height: 34px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.09); color: #a1a1aa; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
    .footer-socials a:hover { border-color: #f59e0b; color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
    .footer-col h4 { font-size: 0.875rem; font-weight: 600; color: #fafafa; margin: 0 0 0.85rem; }
    .footer-contact-details p { font-size: 0.78rem; color: #9ca3af; margin: 0 0 0.4rem; line-height: 1.45; }
    .footer-contact-details strong { color: #d4d4d8; }
    .newsletter-col p { font-size: 0.78rem; color: #9ca3af; line-height: 1.5; margin: 0 0 0.85rem; }
    .newsletter-form { display: flex; gap: 0.45rem; }
    .newsletter-input { flex: 1; padding: 0.55rem 0.75rem; background: #0a0b0e; color: #fafafa; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; font-size: 0.8rem; outline: none; }
    .newsletter-input:focus { border-color: #f59e0b; }
    .btn-newsletter-ok { background: #f59e0b; color: #030304; border: none; border-radius: 8px; padding: 0 1rem; font-size: 0.78rem; font-weight: 700; cursor: pointer; }
    .btn-newsletter-ok:hover { background: #fbbf24; }
    .newsletter-feedback { display: block; margin-top: 0.5rem; font-size: 0.75rem; color: #fbbf24; font-weight: 500; }
    .footer-bottom { max-width: 1120px; margin: 1.25rem auto 0; text-align: center; font-size: 0.72rem; color: #71717a; }

    @media (max-width: 960px) {
      .hero-container, .models-grid, .benefits-list { grid-template-columns: 1fr; }
      .inquiry-inputs-row { grid-template-columns: 1fr 1fr; }
      .btn-inquiry-submit { grid-column: 1 / -1; padding: 0.75rem; }
      .footer-container { grid-template-columns: 1fr; gap: 1.75rem; }
    }
    @media (max-width: 680px) {
      .mobile-menu-btn { display: inline-flex; }
      .header-nav { display: none; position: absolute; top: 100%; left: 0; right: 0; background: #07080a; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding: 1rem 1.5rem; flex-direction: column; align-items: flex-start; gap: 0.9rem; }
      .header-nav.mobile-open { display: flex; }
      .inquiry-inputs-row { grid-template-columns: 1fr; }
      .hero-capture-img { height: 240px; }
    }
  `],
})
export class LandingComponent {
  authService = inject(AuthService);

  mobileMenuOpen = false;
  selectedSampleIndex = 0;

  // Amostras reais extraídas da pipeline de visão computacional do VISORA
  readonly realSamples: RealPassageSample[] = [
    {
      plate: 'TEK3J37',
      format: 'MERCOSUL',
      vehicleDesc: 'SUV Executivo • Faixa Direita',
      frameImg: 'assets/alpr/frame_tek3j37.jpg',
      cropImg: 'assets/alpr/crop_tek3j37.jpg',
      vehImg: 'assets/alpr/raw_tek3j37.jpg',
      eventLabel: 'Entrada Registrada Automaticamente',
      chargeType: 'Controle de Pátio Ativo',
    },
    {
      plate: 'EZV0448',
      format: 'ANTIGO',
      vehicleDesc: 'Passeio • Cancela Principal',
      frameImg: 'assets/alpr/frame_ezv0448.jpg',
      cropImg: 'assets/alpr/crop_ezv0448.jpg',
      vehImg: 'assets/alpr/veh_ezv0448.jpg',
      eventLabel: 'Leitura Validada em 3 Quadros',
      chargeType: 'Tarifação Horária / Diária',
    },
    {
      plate: 'FTN1F16',
      format: 'MERCOSUL',
      vehicleDesc: 'Sedan • Leitura em Movimento',
      frameImg: 'assets/alpr/frame_ftn1f16.jpg',
      cropImg: 'assets/alpr/crop_ftn1f16.jpg',
      vehImg: 'assets/alpr/veh_ftn1f16.jpg',
      eventLabel: 'Movimentação Auditada no Histórico',
      chargeType: 'Registro Instantâneo',
    },
  ];

  // Módulos reais do VISORA
  readonly modules: ModulePreview[] = [
    {
      id: 'central',
      title: 'Central de Monitoramento',
      tag: 'Visão Computacional',
      summary:
        'Gerenciamento de câmeras de entrada e saída, ingestão de vídeos gravados e reconhecimento automático de placas nos padrões Mercosul e Antigo.',
      highlights: [
        'Cadastro de câmeras RTSP e cancelas',
        'Processamento automatizado de vídeo',
        'Detecção YOLOv8 + OCR com validação brasileira',
      ],
    },
    {
      id: 'dashboard',
      title: 'Dashboard & Portaria',
      tag: 'Operação em Tempo Real',
      summary:
        'Acompanhamento ao vivo dos veículos estacionados no pátio, indicadores de entradas e saídas do dia e ações rápidas de portaria.',
      highlights: [
        'Monitoramento em tempo real do pátio',
        'Ações rápidas de entrada e saída',
        'Histórico de movimentações com correção auditada',
      ],
    },
    {
      id: 'clientes',
      title: 'Clientes, Tarifas & Portal',
      tag: 'Gestão Comercial & Motorista',
      summary:
        'Cadastro centralizado de clientes e múltiplos veículos, configuração de tarifa vigente (1ª hora, hora adicional, diária e tolerância) e portal exclusivo do cliente.',
      highlights: [
        'Vínculo de veículos e histórico individual',
        'Tarifação avulsa e plano diário configurável',
        'Portal do cliente para consulta de passagens',
      ],
    },
  ];

  selectedModule: ModulePreview = this.modules[0];

  // Seção Benefícios operacionais
  readonly benefits: string[] = [
    'Redução de registros manuais.',
    'Centralização das informações operacionais.',
    'Gestão simplificada de clientes e tarifas.',
    'Melhor experiência para os clientes do estacionamento.',
  ];

  // Formulário comercial de interesse
  leadForm = {
    nome: '',
    estacionamento: '',
    email: '',
    telefone: '',
    consentimento: true,
  };
  leadFeedback = '';
  leadError = false;

  // Newsletter no rodapé
  newsletterEmail = '';
  newsletterMessage = '';

  get activeSample(): RealPassageSample {
    return this.realSamples[this.selectedSampleIndex] || this.realSamples[0];
  }

  selectSample(index: number): void {
    this.selectedSampleIndex = index;
  }

  selectModule(mod: ModulePreview): void {
    this.selectedModule = mod;
  }

  scrollToSection(sectionId: string): void {
    this.mobileMenuOpen = false;
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  submitLeadForm(): void {
    if (!this.leadForm.nome.trim() || !this.leadForm.email.trim() || !this.leadForm.telefone.trim()) {
      this.leadError = true;
      this.leadFeedback = 'Por favor, preencha nome, e-mail e telefone para solicitar o contato.';
      return;
    }
    if (!this.leadForm.consentimento) {
      this.leadError = true;
      this.leadFeedback = 'Confirme o consentimento LGPD para prosseguir com o envio.';
      return;
    }
    this.leadError = false;
    this.leadFeedback = `Obrigado, ${this.leadForm.nome}! Recebemos os dados do estacionamento "${this.leadForm.estacionamento || 'sua operação'}" e entraremos em contato pelo e-mail ${this.leadForm.email}.`;
    this.leadForm = {
      nome: '',
      estacionamento: '',
      email: '',
      telefone: '',
      consentimento: true,
    };
  }

  submitNewsletter(): void {
    if (!this.newsletterEmail.trim()) return;
    this.newsletterMessage = `E-mail ${this.newsletterEmail} cadastrado com sucesso para receber novidades do VISORA!`;
    this.newsletterEmail = '';
  }
}
