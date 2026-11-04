"""Altas y consultas del corpus normativo."""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from sqlalchemy.exc import IntegrityError

from ..errors import ConflictError, NotFoundError, ValidationError
from ..extensions import db
from ..models import LegalProvision, LegalSource
from .validators import require_json

SOURCE_TYPES = {"law", "regulation", "iso", "institutional", "jurisprudence", "guidance"}
STATUSES = {"draft", "active", "repealed", "superseded"}


def _text(data, name, maximum, required=True):
    value = data.get(name)
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()) or len(value.strip()) > maximum:
        raise ValidationError(f"{name} debe ser texto de 1 a {maximum} caracteres.")
    return value.strip() or None


def _date(data, name):
    value = data.get(name)
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} debe usar el formato AAAA-MM-DD.") from exc


def create_source(payload):
    data = require_json(payload)
    source_type = _text(data, "source_type", 30)
    status = _text(data, "status", 20, False) or "active"
    if source_type not in SOURCE_TYPES:
        raise ValidationError("source_type no es válido.")
    if status not in STATUSES:
        raise ValidationError("status no es válido.")
    official_url = _text(data, "official_url", 1000, False)
    if official_url and urlparse(official_url).scheme not in ("http", "https"):
        raise ValidationError("official_url debe ser una URL HTTP(S).")
    source = LegalSource(
        code=_text(data, "code", 80), title=_text(data, "title", 300),
        source_type=source_type, issuing_body=_text(data, "issuing_body", 200),
        jurisdiction=_text(data, "jurisdiction", 100, False) or "Perú",
        publication_date=_date(data, "publication_date"), effective_from=_date(data, "effective_from"),
        effective_to=_date(data, "effective_to"), official_url=official_url, status=status,
        notes=_text(data, "notes", 10000, False),
    )
    db.session.add(source)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Ya existe una fuente con ese código.") from exc
    return source.to_dict()


def add_provision(source_id, payload):
    data = require_json(payload)
    source = db.session.get(LegalSource, source_id)
    if not source:
        raise NotFoundError("Fuente normativa no encontrada.")
    verified = data.get("verified", False)
    if type(verified) is not bool:
        raise ValidationError("verified debe ser booleano.")
    sort_order = data.get("sort_order", 0)
    if type(sort_order) is not int or sort_order < 0:
        raise ValidationError("sort_order debe ser un entero no negativo.")
    provision = LegalProvision(
        source=source, provision_code=_text(data, "provision_code", 100),
        heading=_text(data, "heading", 500, False), content=_text(data, "content", 50000),
        topic=_text(data, "topic", 100, False), right_type=_text(data, "right_type", 40, False),
        applies_to=_text(data, "applies_to", 300, False), keywords=_text(data, "keywords", 2000, False),
        sort_order=sort_order, verified=verified,
    )
    db.session.add(provision)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Ese código de disposición ya existe en la fuente.") from exc
    return provision.to_dict()


def list_sources():
    return [source.to_dict() for source in LegalSource.query.order_by(LegalSource.code).all()]


def get_source(source_id):
    source = db.session.get(LegalSource, source_id)
    if not source:
        raise NotFoundError("Fuente normativa no encontrada.")
    return source.to_dict(include_provisions=True)


def update_provision(provision_id, payload):
    data = require_json(payload)
    provision = db.session.get(LegalProvision, provision_id)
    if not provision:
        raise NotFoundError("Disposición normativa no encontrada.")
    allowed_text = {
        "provision_code": 100, "heading": 500, "content": 50000, "topic": 100,
        "right_type": 40, "applies_to": 300, "keywords": 2000,
    }
    if not any(name in data for name in (*allowed_text, "verified", "sort_order")):
        raise ValidationError("No se recibió ningún campo actualizable.")
    for name, maximum in allowed_text.items():
        if name in data:
            required = name in ("provision_code", "content")
            setattr(provision, name, _text(data, name, maximum, required))
    if "verified" in data:
        if type(data["verified"]) is not bool:
            raise ValidationError("verified debe ser booleano.")
        provision.verified = data["verified"]
    if "sort_order" in data:
        if type(data["sort_order"]) is not int or data["sort_order"] < 0:
            raise ValidationError("sort_order debe ser un entero no negativo.")
        provision.sort_order = data["sort_order"]
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("Ese código de disposición ya existe en la fuente.") from exc
    return provision.to_dict()
