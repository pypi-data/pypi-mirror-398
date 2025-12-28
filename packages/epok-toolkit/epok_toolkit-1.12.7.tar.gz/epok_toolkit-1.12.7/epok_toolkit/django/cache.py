# utils/cacher.py
from rest_framework import viewsets
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework_extensions.cache.decorators import cache_response
from django.views.decorators.cache import cache_page
from colorstreak import log
from functools import wraps
from django.utils.decorators import method_decorator
# --- clave por usuario + params + página ----------------------
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework_extensions.key_constructor.bits import UserKeyBit, QueryParamsKeyBit, PaginationKeyBit


"""
cacher.py — utilidades de caché centralizadas
============================================

Este módulo agrupa, en un solo lugar, las dos capas de caché que aplicamos en
nuestra API DRF:

    📦  cache_get   → capa de *serialización*  (drf extensions @cache_response)
    🚀  cache_full  → capa de *vista completa* (Django @cache_page)

Para no repetir la misma lógica en cada vista, exportamos:

    •  `CachedViewSet`  ->  incluye CacheResponseMixin listo para usar.
    •  Decoradores      ->  `cache_get`,  `cache_full`.
    •  `TimeToLive`     ->  constantes de segundos ligadas a colores/emoji.

Leyenda TTL (la misma del CSV)
------------------------------
    🔴  1 min   (60 s)      | cambios frecuentes
    🟡  2 --> 5 min (~300 s)     | lecturas comunes
    🟢  10 --> 30 min (~1800 s)  | datos casi estáticos

Emojis ↔ capas
--------------
    🗄️   consultas ORM   (cacheops / get_or_set)
    📦   serialización   (cache_response)
    🚀   vista completa  (cache_page)
    🌐   CDN / navegador (Cache‑Control)

"""



class TimeToLive:
    """
    Constantes de TTL ligadas a la paleta del CSV:

        🔴 RED    | 1 min  (60 s)
        🟡 YELLOW | 5 min  (300 s)
        🟢 GREEN  | 30 min (1800 s)
    """
    RED    = 60          # 1 minuto
    YELLOW = 60 * 5      # 5 minutos
    GREEN  = 60 * 30     # 30 minutos


class UserQueryKey(DefaultKeyConstructor):
    user = UserKeyBit()
    query_params = QueryParamsKeyBit()
    pagination = PaginationKeyBit()

_DEFAULT_KEY  = UserQueryKey().get_key
_DEFAULT_TTL  = TimeToLive.RED



class CachedViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    """
    Herédame si vas a usar cache_get o cache_full.
    Nada más que eso; no impone TTL.
    """
    pass




def cache_get(ttl=_DEFAULT_TTL, key_func=_DEFAULT_KEY):
    """
    Capa: Serialización 📦
    Devuelve un decorador que cachea la serialización DRF *una sola vez*,
    evitando envolver la vista nuevamente en cada petición.

    Ejemplo:
        @cache_get(ttl=TimeToLive.RED)
        def view(...): ...
    """
    def decorator(view_fn):
        # Pre‑construimos la función cacheada UNA vez
        cached_fn = cache_response(ttl, key_func=key_func)(view_fn)

        @wraps(view_fn)
        def wrapped(*args, **kwargs):
            log.library(
                f"[📦 cache_get] {view_fn.__qualname__} | ttl={ttl}s"
            )
            # Llamamos directamente a la versión ya decorada,
            # para no crear cadenas de closures ni excepciones duplicadas.
            return cached_fn(*args, **kwargs)

        return wrapped

    return decorator


def cache_full(ttl=_DEFAULT_TTL, key_prefix=""):
    """
    Capa: Respuesta HTTP 🚀
    Devuelve un decorador que cachea la vista completa vía cache_page
    *al momento de ejecutar la vista*.

    Ejemplo:
        @cache_full(ttl=TimeToLive.GREEN, key_prefix="ticket_pdf")
        def view(...): ...
    """
    def decorator(view_fn):
        # Adapt the function-level cache_page decorator to a bound‑method
        page_deco = cache_page(ttl, key_prefix=key_prefix)
        decorated_fn = method_decorator(page_deco)(view_fn)

        @wraps(view_fn)
        def wrapped(self, request, *args, **kwargs):
            log.library(f"[🚀 cache_full] {view_fn.__qualname__} | ttl={ttl}s | prefix={key_prefix}")
            return decorated_fn(self, request, *args, **kwargs)

        return wrapped

    return decorator