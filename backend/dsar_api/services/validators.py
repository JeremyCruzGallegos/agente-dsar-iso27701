"""Validación de entradas (sin dependencias externas)."""
from __future__ import annotations

import re

from ..errors import ValidationError

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DOC_RE = re.compile(r"^[A-Za-z0-9\-]{4,32}$")


def require_json(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValidationError("El cuerpo debe ser un objeto JSON.")
    return payload


def clean_document_id(value) -> str:
    value = str(value or "").strip()
    if not _DOC_RE.match(value):
        raise ValidationError("user_id inválido: use 4-32 caracteres alfanuméricos o guiones.")
    return value


def clean_email(value) -> str:
    value = str(value or "").strip().lower()
    if len(value) > 254 or not _EMAIL_RE.match(value):
        raise ValidationError("Correo electrónico inválido.")
    return value


def clean_text(value, *, field: str, max_len: int, required: bool = False) -> str | None:
    value = (str(value).strip() if value is not None else "")
    if not value:
        if required:
            raise ValidationError(f"{field} es obligatorio.")
        return None
    if len(value) > max_len:
        raise ValidationError(f"{field} supera los {max_len} caracteres.")
    return value


def clean_pagination(args, *, default: int, maximum: int) -> tuple[int, int]:
    try:
        limit = int(args.get("limit", default))
        offset = int(args.get("offset", 0))
    except ValueError:
        raise ValidationError("limit y offset deben ser enteros.")
    if limit < 1 or offset < 0:
        raise ValidationError("limit debe ser >= 1 y offset >= 0.")
    return min(limit, maximum), offset
