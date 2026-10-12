"""Application factory del backend DSAR (ISO/IEC 27701)."""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from .config import ProductionConfig, get_config
from .errors import register_error_handlers
from .extensions import cors, db


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    app = Flask(__name__, instance_relative_config=False)
    config = get_config(config_name)
    if config is ProductionConfig:
        ProductionConfig.validate()
    app.config.from_object(config)

    # Carpeta para la BD SQLite local (ignorada por git).
    (Path(__file__).resolve().parent.parent / "instance").mkdir(exist_ok=True)

    db.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        allow_headers=["Content-Type", "X-API-Key"],
    )

    from . import models  # noqa: F401  (registra tablas en el metadata)
    from .api import register_blueprints
    from .cli import register_cli

    register_blueprints(app)
    register_error_handlers(app)
    register_cli(app)

    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()

    return app
