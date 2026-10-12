from __future__ import annotations
import enum
from datetime import datetime, timedelta, timezone

from ..extensions import db
from .data_subject import utcnow


class RequestType(str, enum.Enum):
    """Valores idénticos a los del <select> del frontend."""

    ACCESO = "Acceso"
    SUPRESION = "Supresion"
    RECTIFICACION = "Rectificacion"
    PORTABILIDAD = "Portabilidad"


class RequestStatus(str, enum.Enum):
    RECIBIDO = "Recibido"
    EN_VERIFICACION = "En verificacion"
    EN_PROCESO = "En proceso"
    COMPLETADO = "Completado"
    RECHAZADO = "Rechazado"


CLOSED_STATUSES = {RequestStatus.COMPLETADO, RequestStatus.RECHAZADO}

# Transiciones permitidas (evita saltos inconsistentes en el flujo n8n).
ALLOWED_TRANSITIONS = {
    RequestStatus.RECIBIDO: {RequestStatus.EN_VERIFICACION, RequestStatus.EN_PROCESO, RequestStatus.RECHAZADO},
    RequestStatus.EN_VERIFICACION: {RequestStatus.EN_PROCESO, RequestStatus.RECHAZADO},
    RequestStatus.EN_PROCESO: {RequestStatus.COMPLETADO, RequestStatus.RECHAZADO},
    RequestStatus.COMPLETADO: set(),
    RequestStatus.RECHAZADO: set(),
}


class DsarRequest(db.Model):
    """Solicitud de ejercicio de derechos."""

    __tablename__ = "dsar_requests"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey("data_subjects.id"), nullable=True, index=True)
    document_id = db.Column(db.String(32), nullable=False, index=True)
    email = db.Column(db.String(254), nullable=False)
    request_type = db.Column(db.Enum(RequestType, native_enum=False, length=20), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum(RequestStatus, native_enum=False, length=20),
        nullable=False,
        default=RequestStatus.RECIBIDO,
        index=True,
    )
    resolution_note = db.Column(db.String(500), nullable=True)

    received_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    due_at = db.Column(db.DateTime(timezone=True), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    subject = db.relationship("DataSubject", back_populates="requests")

    @staticmethod
    def compute_due_date(received: datetime, sla_days: int) -> datetime:
        return received + timedelta(days=sla_days)

    @staticmethod
    def _aware(value: datetime) -> datetime:
        # SQLite devuelve datetimes sin zona; los tratamos como UTC.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    @property
    def is_closed(self) -> bool:
        return self.status in CLOSED_STATUSES

    def sla_days_remaining(self, now: datetime | None = None) -> int | None:
        """Días restantes del SLA (negativo = vencido). None si la solicitud ya se cerró."""
        if self.is_closed:
            return None
        now = now or utcnow()
        delta = self._aware(self.due_at) - now
        return delta.days if delta.total_seconds() >= 0 else -((-delta).days + 1)

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.document_id,
            "request_type": self.request_type.value,
            "status": self.status.value,
            "details": self.details,
            "resolution_note": self.resolution_note,
            "received_at": self._aware(self.received_at).isoformat(),
            "due_at": self._aware(self.due_at).isoformat(),
            "completed_at": self._aware(self.completed_at).isoformat() if self.completed_at else None,
            "sla_days_remaining": self.sla_days_remaining(),
        }
