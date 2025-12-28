"""
notifications/method/email_engine.py
Motor de envío de correos basado en plantillas del catálogo TEMPLATES.
La vista sólo indica qué plantilla usar, el contexto y el destinatario.
"""

from typing import Dict
from django.core.mail import send_mail
from django.conf import settings

from .templates import TEMPLATES, EmailTemplate, RenderedEmail


class EmailEngine:
    """
    Ejemplo de uso:

        engine = EmailEngine()
        engine.send(
            template_key="password_reset",
            context={"name": "Fer", "reset_link": "https://app.congrats.mx/#/reset/abc"},
            recipient="fer@example.com",
        )
    """

    def __init__(self, templates: Dict[str, EmailTemplate] = TEMPLATES, backend=send_mail):
        self.templates = templates
        self.backend = backend

    # --------------------------------------------------------------------- #
    # API pública
    # --------------------------------------------------------------------- #
    def send(
        self,
        template_key: "str", # TODO: PONER CLASE VALIDADOR DE TEMPLATE EVITAR INYECCION 
        context: Dict[str, str],
        recipient: str,
        attachments: Dict[str, bytes] | None = None,
    ) -> None:
        """
        Envía un correo usando la plantilla indicada.
        - `context` debe contener todas las llaves declaradas en `required_vars`.
        - `attachments` puede ser un dict {filename: bytes} para adjuntar PDFs u otros ficheros.
        """
        # Verificar plantilla
        if template_key not in self.templates:
            raise KeyError(f"Plantilla '{template_key}' no existe en TEMPLATES.") # TODO: PONER CUALES SI SON VALIDAS

        # Renderizar cuerpo
        rendered: RenderedEmail = self.templates[template_key].render(context)

        # Crear e‑mail multipart (texto + HTML)
        from django.core.mail import EmailMultiAlternatives

        message = EmailMultiAlternatives(
            subject=rendered.subject,
            body=rendered.plain,
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient],
        )
        message.attach_alternative(rendered.html, "text/html")

        # Adjuntos opcionales
        if attachments:
            for name, data in attachments.items():
                message.attach(name, data, "application/pdf")

        # Enviar
        message.send(fail_silently=False)