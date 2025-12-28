"""

"""

from dataclasses import dataclass
from typing import Dict, List
from django.conf import settings
import re


# ============================
# Config base
# ============================

TEMPLATES_SETTINGS = getattr(settings, "TEMPLATE_SETTINGS", {})


@dataclass(frozen=True)
class Colors:
    BACKGROUND: str = TEMPLATES_SETTINGS.get("colors", {}).get("background", "#f9fafb")
    PRIMARY: str    = TEMPLATES_SETTINGS.get("colors", {}).get("primary", "#4f46e5")
    TEXT: str       = TEMPLATES_SETTINGS.get("colors", {}).get("text", "#374151")
    WHITE: str      = TEMPLATES_SETTINGS.get("colors", {}).get("white", "#ffffff")

@dataclass(frozen=True)
class Company:
    name: str    = TEMPLATES_SETTINGS.get("company", {}).get("name", "Congrats")
    email: str   = TEMPLATES_SETTINGS.get("company", {}).get("email", "info@compania.com")
    eslogan: str = TEMPLATES_SETTINGS.get("company", {}).get("eslogan", "Eslogan sin definir")
    footer: str  = TEMPLATES_SETTINGS.get("company", {}).get("footer", "¡Nos vemos pronto!<br><em>El equipo de Congrats 🥳</em>")



# ============================
# Grupper (envoltorio HTML)
# ============================

def wrap_html(content: str) -> str:
    return f"""
    <div style="font-family: Arial, Helvetica, sans-serif; background-color: {Colors.BACKGROUND}; padding: 24px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background: {Colors.WHITE}; border-radius: 8px; overflow: hidden;">
            <tr>
                <td style="background: {Colors.PRIMARY}; padding: 20px 24px; text-align: center;">
                    <h1 style="color: {Colors.WHITE}; margin: 0; font-size: 24px;">{Company.name} 🎉</h1>
                </td>
            </tr>
            <tr>
                <td style="padding: 32px 24px;">
                    {content}
                </td>
            </tr>
        </table>
    </div>
    """


# ============================
# Tipos
# ============================

@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    plain: str
    html: str

@dataclass(frozen=True)
class EmailTemplate:
    subject: str
    plain_body: str
    html_body: str
    required_vars: List[str]

    def render(self, context: Dict[str, str]) -> RenderedEmail:
        missing = [v for v in self.required_vars if v not in context]
        if missing:
            raise ValueError(f"Faltan llaves en contexto: {missing}")
        return RenderedEmail(
            subject=self.subject.format(**context),
            plain=self.plain_body.format(**context),
            html=self.html_body.format(**context),
        )
        
        
# ============================
# Registro dinámico
# ============================

class TemplateRegistry:
    def __init__(self):
        self._templates: Dict[str, EmailTemplate] = {}
    
    def _html_to_plain(self, html: str) -> str:
        return re.sub(r"<[^>]*>", "", html).strip()

    def register_template(self, key: str, subject: str, html_body: str, required_vars: List[str], plain_body: str | None = None) -> None:
        if key in self._templates:
            raise ValueError(f"Template con clave '{key}' ya está registrado.")
        plain = plain_body or self._html_to_plain(html_body)
        wrapped_html = wrap_html(html_body)
        self._templates[key] = EmailTemplate(
            subject=subject,
            plain_body=plain,
            html_body=wrapped_html,
            required_vars=required_vars
        )
    
    @property
    def templates(self) -> Dict[str, EmailTemplate]:
        return self._templates

registry = TemplateRegistry()

# ============================
# Registrar plantillas base usando el mismo builder
# ============================

registry.register_template(
    key="password_reset",
    subject=f"🔑 Restablecimiento de Contraseña – {Company.name}",
    html_body=(
        "<p style='font-size:16px;'>¡Hola <strong>{name}</strong>! 🎉</p>"
        "<p style='font-size:16px;margin:24px 0;'>Haz clic en el botón para restablecer tu contraseña:</p>"
        "<p style='text-align:center;margin:24px 0;'>"
        f"<a href='{{reset_link}}' style='display:inline-block;padding:12px 24px;font-size:16px;color:{Colors.WHITE};background-color:{Colors.PRIMARY};text-decoration:none;border-radius:5px;'>🔒 Restablecer Contraseña 🎊</a>"
        "</p>"
        "<p style='font-size:16px;'>Si no funciona, copia este enlace:<br>"
        "<span style='word-break:break-all;font-size:14px;'>{reset_link}</span></p>"
        f"<p style='font-size:16px;margin-top:24px;'>{Company.footer}</p>"
    ),
    required_vars=["name", "reset_link"]
)

registry.register_template(
    key="welcome",
    subject=f"🎉 Bienvenido a {Company.name}, {{name}}",
    html_body=(
        "<p style='font-size:16px;'>¡Hola <strong>{name}</strong>! 🎈</p>"
        "<p style='font-size:16px;margin:24px 0;'>Gracias por unirte a <strong>{Company.name}</strong>.</p>"
        f"<p style='font-size:16px;margin-top:24px;'>{Company.footer}</p>"
    ),
    required_vars=["name"]
)

registry.register_template(
    key="password_reset_success",
    subject=f"🔑 Contraseña restablecida – {Company.name}",
    html_body=(
        "<p style='font-size:16px;'>¡Hola <strong>{name}</strong>! 🔑</p>"
        "<p style='font-size:16px;margin:24px 0;'>Tu contraseña ha sido restablecida con éxito 🎉</p>"
        f"<p style='font-size:16px;margin-top:24px;'>{Company.footer}</p>"
    ),
    required_vars=["name"]
)

registry.register_template(
    key="test_app_running",
    subject=f"🚀 Test OK – {Company.name}",
    html_body=(
        "<p style='font-size:16px;'>¡Hola <strong>{name}</strong>! 🚀</p>"
        "<p style='font-size:16px;margin:24px 0;'>La prueba de funcionamiento pasó. Tu app está lista para rockear. 🎉</p>"
        f"<p style='font-size:16px;margin-top:24px;'>{Company.footer}</p>"
    ),
    required_vars=["name"]
)

# ============================
# Catálogo final
# ============================

TEMPLATES: Dict[str, EmailTemplate] = {
    **registry.templates,
}