from __future__ import annotations

import logging
import smtplib
from celery import shared_task, states
from celery.exceptions import Ignore
from .engine import EmailEngine

log = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(smtplib.SMTPException, ConnectionError, TimeoutError),
    retry_backoff=True,       # 2, 4, 8, 16… s
    retry_jitter=True,        # +- aleatorio
    max_retries=3,
    ignore_result=True,       # <-- ¡importante!
)
def send_email_async(self, template_key, context, recipient, attachments=None):
    try:
        engine = EmailEngine()
        engine.send(
            template_key=template_key,
            context=context,
            recipient=recipient,
            attachments=attachments,
        )
        # No retornamos nada; evitamos que Celery/Redis serialice blobs.
    except smtplib.SMTPSenderRefused as exc:
        # 552 => el servidor rechaza tamaño. No vale la pena reintentar.
        if exc.smtp_code == 552:
            log.error("SMTP 552 – tamaño excedido; abortando reintentos: %s", exc)
            # Marcamos la tarea como FAILURE, pero NO reintentamos.
            self.update_state(state=states.FAILURE, meta=str(exc))
            raise Ignore()    # Detiene la cadena Celery sin más
        # Otros códigos (550, 451, etc.) siguen flujo normal de retry
        raise

def send_email(template_key, context, recipient, attachments=None):
    send_email_async.delay(template_key, context, recipient, attachments) # type: ignore