"""Configuración por entorno. Todo valor sensible viene de variables de entorno."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class BaseConfig:
    ENV_NAME = "base"
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'dsar.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Autenticación por API key (header X-API-Key). Sin clave => acceso denegado.
    SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "")  # n8n / servicios internos
    DPO_API_KEY = os.getenv("DPO_API_KEY", "")          # panel del DPO
    # Clave para referenciar al titular en la bitácora sin guardar su documento en claro.
    AUDIT_HASH_KEY = os.getenv("AUDIT_HASH_KEY", "")

    CORS_ORIGINS = _csv(os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"))

    # Plazo legal para responder una solicitud (días).
    DSAR_SLA_DAYS = int(os.getenv("DSAR_SLA_DAYS", "30"))
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200


class DevelopmentConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG = True


class TestingConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SERVICE_API_KEY = "test-service-key"
    DPO_API_KEY = "test-dpo-key"
    AUDIT_HASH_KEY = "test-audit-key"


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"
    DEBUG = False

    @classmethod
    def validate(cls) -> None:
        missing = [
            name
            for name in ("SERVICE_API_KEY", "DPO_API_KEY", "AUDIT_HASH_KEY", "DATABASE_URL")
            if not os.getenv(name)
        ]
        if missing:
            raise RuntimeError(
                "Faltan variables de entorno obligatorias en producción: " + ", ".join(missing)
            )


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    name = name or os.getenv("APP_ENV", "development")
    try:
        return CONFIGS[name]
    except KeyError:
        raise RuntimeError(f"APP_ENV desconocido: {name!r}. Usa: {', '.join(CONFIGS)}")
