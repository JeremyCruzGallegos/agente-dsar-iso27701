"""Comandos: `flask --app app init-db`, `flask --app app seed-demo` (ejecutar desde backend/)."""
from datetime import date, timedelta

import click

from .extensions import db
from .models import DataSubject, RetentionPolicy


def register_cli(app) -> None:
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas y las políticas de retención por defecto."""
        db.create_all()
        defaults = [
            ("datos_contacto", 365, "Consentimiento del titular", True),
            ("datos_facturacion", 3650, "Obligación tributaria", False),
            ("logs_auditoria", 1825, "ISO/IEC 27701 - evidencia de cumplimiento", False),
        ]
        for category, days, basis, erasable in defaults:
            if not RetentionPolicy.query.filter_by(data_category=category).first():
                db.session.add(
                    RetentionPolicy(data_category=category, retention_days=days, legal_basis=basis, erasable=erasable)
                )
        db.session.commit()
        click.echo("Base de datos lista.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Datos de ejemplo para probar el frontend (incluye un titular con retención)."""
        db.create_all()
        samples = [
            DataSubject(document_id="72839102", full_name="Juan Pérez", email="juan@email.com"),
            DataSubject(
                document_id="45120987", full_name="María Quispe", email="maria@email.com",
                retention_until=date.today() + timedelta(days=365),
            ),
        ]
        for s in samples:
            if not DataSubject.query.filter_by(document_id=s.document_id).first():
                db.session.add(s)
        db.session.commit()
        click.echo("Datos de demostración cargados.")
