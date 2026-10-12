from ..extensions import db
from .data_subject import utcnow


class RetentionPolicy(db.Model):
    """Reglas de retención por categoría de dato (ISO/IEC 27701, cláusula de retención)."""

    __tablename__ = "retention_policies"

    id = db.Column(db.Integer, primary_key=True)
    data_category = db.Column(db.String(100), unique=True, nullable=False)
    retention_days = db.Column(db.Integer, nullable=False)
    legal_basis = db.Column(db.String(300), nullable=True)
    erasable = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "data_category": self.data_category,
            "retention_days": self.retention_days,
            "legal_basis": self.legal_basis,
            "erasable": self.erasable,
        }
