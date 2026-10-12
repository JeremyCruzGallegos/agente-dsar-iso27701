from __future__ import annotations
from datetime import date, datetime, timezone

from ..extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DataSubject(db.Model):
    """Titular de datos personales (tabla de Usuarios)."""

    __tablename__ = "data_subjects"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(254), nullable=True, index=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    # Criterios de borrado: el borrado se bloquea si hay retención legal vigente.
    legal_hold = db.Column(db.Boolean, nullable=False, default=False)
    legal_hold_reason = db.Column(db.String(300), nullable=True)
    retention_until = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    anonymized_at = db.Column(db.DateTime(timezone=True), nullable=True)

    requests = db.relationship("DsarRequest", back_populates="subject", lazy="dynamic")

    @property
    def is_anonymized(self) -> bool:
        return self.anonymized_at is not None

    def retention_block_reason(self, today: date | None = None) -> str | None:
        """Devuelve el motivo por el que NO se puede suprimir, o None si es posible."""
        today = today or date.today()
        if self.legal_hold:
            return self.legal_hold_reason or "Retención legal vigente (legal hold)."
        if self.retention_until and self.retention_until > today:
            return f"Plazo de retención vigente hasta {self.retention_until.isoformat()}."
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "nombre": self.full_name,
            "email": self.email,
            "activo": self.active,
            "anonimizado": self.is_anonymized,
            "creado": (
                (self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)).isoformat()
                if self.created_at
                else None
            ),
        }
