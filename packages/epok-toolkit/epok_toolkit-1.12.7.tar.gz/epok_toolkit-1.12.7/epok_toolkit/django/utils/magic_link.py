from datetime import timedelta
import jwt
from django.utils import timezone
from django.conf import settings

def generate_login_magic_token(user, minutes_valid=10):
    """
    Genera un token JWT válido por X minutos para login sin contraseña.
    Incluye un propósito específico para distinguirlo de otros tipos de token.
    """
    payload = {
        "user_id": str(user.id),
        "exp": timezone.now() + timedelta(minutes=minutes_valid),
        "purpose": "magic_login",
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def build_login_magic_link(token):
    """
    Construye el enlace completo hacia tu frontend.
    Ajusta la ruta a donde quieras que el frontend reciba el token.
    """
    return f"{settings.FRONTEND_URL}#/magic-login?token={token}"