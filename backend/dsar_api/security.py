"""Autenticación por API key con roles (`service` = n8n/servicios, `dpo` = panel DPO)."""
import hashlib
import hmac
from functools import wraps

from flask import current_app, g, request

from .errors import ForbiddenError, UnauthorizedError


def _match(candidate: str, expected: str) -> bool:
    # Si la clave del servidor no está configurada, nunca autentica (fail closed).
    if not expected or not candidate:
        return False
    return hmac.compare_digest(candidate.encode(), expected.encode())


def authenticate() -> str:
    key = request.headers.get("X-API-Key", "")
    if _match(key, current_app.config["DPO_API_KEY"]):
        return "dpo"
    if _match(key, current_app.config["SERVICE_API_KEY"]):
        return "service"
    raise UnauthorizedError("API key ausente o inválida.", code="invalid_api_key")


def require_role(*allowed: str):
    """Decorador: exige que el rol autenticado esté en `allowed`."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            role = authenticate()
            g.actor = role
            if role not in allowed:
                raise ForbiddenError("Tu rol no tiene permiso para este recurso.", code="insufficient_role")
            return view(*args, **kwargs)

        return wrapper

    return decorator


def subject_reference(document_id: str) -> str:
    """HMAC del documento: permite correlacionar eventos sin guardar el dato en claro."""
    key = current_app.config["AUDIT_HASH_KEY"]
    if not key:
        raise RuntimeError("AUDIT_HASH_KEY no está configurada.")
    return hmac.new(key.encode(), document_id.encode(), hashlib.sha256).hexdigest()
