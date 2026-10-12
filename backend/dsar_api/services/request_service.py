"""Ciclo de vida de las solicitudes DSAR (tickets, estados y SLA)."""
import secrets

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..errors import ConflictError, NotFoundError, ValidationError
from ..extensions import db
from ..models import DataSubject, DsarRequest, RequestStatus, RequestType
from ..models.data_subject import utcnow
from ..models.dsar_request import ALLOWED_TRANSITIONS, CLOSED_STATUSES
from . import audit_service
from .validators import clean_document_id, clean_email, clean_text, require_json


def _parse_enum(enum_cls, value, field: str):
    try:
        return enum_cls(value)
    except ValueError:
        valid = ", ".join(e.value for e in enum_cls)
        raise ValidationError(f"{field} inválido. Valores permitidos: {valid}.")


def _new_ticket_id() -> str:
    return "DSAR-" + secrets.token_hex(4).upper()


def create_request(payload) -> DsarRequest:
    """Registra la solicitud enviada por el frontend/n8n y calcula su fecha límite (SLA)."""
    payload = require_json(payload)
    document_id = clean_document_id(payload.get("user_id"))
    email = clean_email(payload.get("email"))
    request_type = _parse_enum(RequestType, payload.get("request_type"), "request_type")
    details = clean_text(payload.get("details"), field="details", max_len=2000)

    subject = DataSubject.query.filter_by(document_id=document_id).first()
    received = utcnow()

    for _ in range(5):  # reintento ante colisión de ticket (improbable)
        req = DsarRequest(
            ticket_id=_new_ticket_id(),
            subject_id=subject.id if subject else None,
            document_id=document_id,
            email=email,
            request_type=request_type,
            details=details,
            received_at=received,
            due_at=DsarRequest.compute_due_date(received, current_app.config["DSAR_SLA_DAYS"]),
        )
        db.session.add(req)
        try:
            db.session.flush()
        except IntegrityError:
            db.session.rollback()
            continue
        audit_service.record(
            "REQUEST_CREATED", entity_type="dsar_request", entity_id=str(req.id),
            document_id=document_id, ticket_id=req.ticket_id,
            detail={"request_type": request_type.value, "subject_found": subject is not None},
            commit=False,
        )
        db.session.commit()
        return req
    raise ConflictError("No se pudo generar un ticket único; reintenta.", code="ticket_collision")


def get_request(ticket_id: str) -> DsarRequest:
    req = DsarRequest.query.filter_by(ticket_id=ticket_id).first()
    if req is None:
        raise NotFoundError("Ticket no encontrado.")
    return req


def list_requests(*, status=None, request_type=None, overdue_only=False, limit=50, offset=0):
    q = DsarRequest.query
    if status:
        q = q.filter(DsarRequest.status == _parse_enum(RequestStatus, status, "status"))
    if request_type:
        q = q.filter(DsarRequest.request_type == _parse_enum(RequestType, request_type, "request_type"))
    if overdue_only:
        q = q.filter(DsarRequest.due_at < utcnow(), DsarRequest.status.notin_(CLOSED_STATUSES))
    total = q.count()
    rows = q.order_by(DsarRequest.received_at.desc()).offset(offset).limit(limit).all()
    return total, rows


def update_status(ticket_id: str, payload) -> DsarRequest:
    payload = require_json(payload)
    req = get_request(ticket_id)
    new_status = _parse_enum(RequestStatus, payload.get("status"), "status")
    note = clean_text(payload.get("resolution_note"), field="resolution_note", max_len=500)

    if new_status not in ALLOWED_TRANSITIONS[req.status]:
        audit_service.record(
            "REQUEST_STATUS_CHANGE", entity_type="dsar_request", entity_id=str(req.id),
            ticket_id=req.ticket_id, outcome="denied",
            detail={"from": req.status.value, "to": new_status.value},
        )
        raise ConflictError(
            f"Transición no permitida: {req.status.value} → {new_status.value}.",
            code="invalid_transition",
        )

    previous = req.status
    req.status = new_status
    if note:
        req.resolution_note = note
    if new_status in CLOSED_STATUSES:
        req.completed_at = utcnow()
    audit_service.record(
        "REQUEST_STATUS_CHANGE", entity_type="dsar_request", entity_id=str(req.id),
        ticket_id=req.ticket_id, detail={"from": previous.value, "to": new_status.value},
        commit=False,
    )
    db.session.commit()
    return req
