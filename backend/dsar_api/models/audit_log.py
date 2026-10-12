from __future__ import annotations
import json

from sqlalchemy import event

from ..errors import ForbiddenError
from ..extensions import db
from .data_subject import utcnow


class AuditLog(db.Model):
    """Bitácora de auditoría. Es append-only: no admite UPDATE ni DELETE desde la aplicación.

    No guarda datos personales en claro: el titular se referencia con un HMAC
    del documento (`subject_ref`).
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    actor = db.Column(db.String(50), nullable=False)       # service | dpo | system
    action = db.Column(db.String(60), nullable=False, index=True)
    entity_type = db.Column(db.String(40), nullable=True)
    entity_id = db.Column(db.String(64), nullable=True)
    subject_ref = db.Column(db.String(64), nullable=True, index=True)
    ticket_id = db.Column(db.String(20), nullable=True, index=True)
    outcome = db.Column(db.String(20), nullable=False, default="success")  # success | denied | error
    detail = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self) -> dict:
        ts = self.timestamp
        return {
            "id": self.id,
            "timestamp": (ts.isoformat() if ts.tzinfo else ts.isoformat() + "+00:00"),
            "actor": self.actor,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "subject_ref": self.subject_ref,
            "ticket_id": self.ticket_id,
            "outcome": self.outcome,
            "detail": json.loads(self.detail) if self.detail else None,
            "ip_address": self.ip_address,
        }


@event.listens_for(AuditLog, "before_update")
def _block_update(mapper, connection, target):
    raise ForbiddenError("La bitácora de auditoría es inmutable.", code="audit_immutable")


@event.listens_for(AuditLog, "before_delete")
def _block_delete(mapper, connection, target):
    raise ForbiddenError("La bitácora de auditoría es inmutable.", code="audit_immutable")
