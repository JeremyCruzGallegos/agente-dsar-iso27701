from __future__ import annotations
import json

from flask import g, has_request_context, request

from ..extensions import db
from ..models import AuditLog
from ..security import subject_reference


def record(
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    document_id: str | None = None,
    ticket_id: str | None = None,
    outcome: str = "success",
    detail: dict | None = None,
    commit: bool = True,
) -> AuditLog:
    """Registra un evento. Con `commit=False` se une a la transacción del llamador."""
    actor = "system"
    ip = None
    if has_request_context():
        actor = getattr(g, "actor", "anonymous")
        ip = request.remote_addr
    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        subject_ref=subject_reference(document_id) if document_id else None,
        ticket_id=ticket_id,
        outcome=outcome,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        ip_address=ip,
    )
    db.session.add(entry)
    if commit:
        db.session.commit()
    return entry


def query_logs(*, document_id=None, ticket_id=None, action=None, outcome=None, limit=50, offset=0):
    q = AuditLog.query
    if document_id:
        q = q.filter(AuditLog.subject_ref == subject_reference(document_id))
    if ticket_id:
        q = q.filter(AuditLog.ticket_id == ticket_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if outcome:
        q = q.filter(AuditLog.outcome == outcome)
    total = q.count()
    rows = q.order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).offset(offset).limit(limit).all()
    return total, rows
