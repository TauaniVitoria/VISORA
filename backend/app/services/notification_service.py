"""
Serviço de notificações por e-mail (recuperação de senha).

Com SMTP configurado (SMTP_HOST), o e-mail é enviado via smtplib com STARTTLS.
Sem SMTP, nada é enviado: em desenvolvimento/testes o link é registrado no log para
facilitar o uso local; em produção o token NUNCA é registrado em log.
"""

from email.message import EmailMessage
import logging
import smtplib

from app.core.config import settings

logger = logging.getLogger("alpr.notifications")

_LOCAL_ENVIRONMENTS = {"development", "testing"}


def build_reset_link(token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"


def send_password_reset_email(to_email: str, token: str) -> None:
    """Entrega o link de redefinição. Falhas de envio são registradas, nunca propagadas ao cliente."""
    link = build_reset_link(token)

    if not settings.SMTP_HOST:
        if settings.ENVIRONMENT in _LOCAL_ENVIRONMENTS:
            logger.warning("[DEV] SMTP não configurado. Link de redefinição para %s: %s", to_email, link)
        else:
            logger.error("SMTP não configurado: e-mail de recuperação para %s não foi enviado.", to_email)
        return

    msg = EmailMessage()
    msg["Subject"] = "Recuperação de senha"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        "Recebemos um pedido para redefinir a sua senha.\n\n"
        f"Acesse o link (válido por {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutos):\n{link}\n\n"
        "Se você não fez este pedido, ignore esta mensagem."
    )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception:
        logger.exception("Falha ao enviar e-mail de recuperação de senha.")
