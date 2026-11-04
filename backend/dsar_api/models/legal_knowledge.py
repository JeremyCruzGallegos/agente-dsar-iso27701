"""Corpus normativo estructurado del agente de derechos."""
from __future__ import annotations

from ..extensions import db
from .data_subject import utcnow


class LegalSource(db.Model):
    __tablename__ = "legal_sources"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(300), nullable=False)
    source_type = db.Column(db.String(30), nullable=False, index=True)
    issuing_body = db.Column(db.String(200), nullable=False)
    jurisdiction = db.Column(db.String(100), nullable=False, default="Perú")
    publication_date = db.Column(db.Date, nullable=True)
    effective_from = db.Column(db.Date, nullable=True)
    effective_to = db.Column(db.Date, nullable=True)
    official_url = db.Column(db.String(1000), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    provisions = db.relationship(
        "LegalProvision", back_populates="source", cascade="all, delete-orphan", lazy="selectin"
    )

    def to_dict(self, include_provisions=False):
        data = {
            "id": self.id, "code": self.code, "title": self.title,
            "source_type": self.source_type, "issuing_body": self.issuing_body,
            "jurisdiction": self.jurisdiction,
            "publication_date": self.publication_date.isoformat() if self.publication_date else None,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_to": self.effective_to.isoformat() if self.effective_to else None,
            "official_url": self.official_url, "status": self.status, "notes": self.notes,
        }
        if include_provisions:
            data["provisions"] = [item.to_dict() for item in self.provisions]
        return data


class LegalProvision(db.Model):
    __tablename__ = "legal_provisions"
    __table_args__ = (
        db.UniqueConstraint("source_id", "provision_code", name="uq_source_provision_code"),
        db.Index("ix_legal_provisions_source_order", "source_id", "sort_order"),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("legal_sources.id", ondelete="CASCADE"), nullable=False)
    provision_code = db.Column(db.String(100), nullable=False)
    heading = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True, index=True)
    right_type = db.Column(db.String(40), nullable=True, index=True)
    applies_to = db.Column(db.String(300), nullable=True)
    keywords = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("legal_provisions.id", ondelete="SET NULL"), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    verified = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    source = db.relationship("LegalSource", back_populates="provisions")
    parent = db.relationship("LegalProvision", remote_side=[id])

    def to_dict(self):
        return {
            "id": self.id, "source_id": self.source_id,
            "provision_code": self.provision_code, "heading": self.heading,
            "content": self.content, "topic": self.topic, "right_type": self.right_type,
            "applies_to": self.applies_to, "keywords": self.keywords,
            "parent_id": self.parent_id, "sort_order": self.sort_order, "verified": self.verified,
        }


class LegalRelation(db.Model):
    __tablename__ = "legal_relations"
    __table_args__ = (db.UniqueConstraint(
        "from_provision_id", "to_provision_id", "relation_type", name="uq_legal_relation"
    ),)

    id = db.Column(db.Integer, primary_key=True)
    from_provision_id = db.Column(
        db.Integer, db.ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False
    )
    to_provision_id = db.Column(
        db.Integer, db.ForeignKey("legal_provisions.id", ondelete="CASCADE"), nullable=False
    )
    relation_type = db.Column(db.String(30), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
