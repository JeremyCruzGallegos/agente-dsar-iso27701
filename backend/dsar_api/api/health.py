from flask import Blueprint
from sqlalchemy import text

from ..errors import ok
from ..extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    db.session.execute(text("SELECT 1"))
    return ok({"service": "dsar-backend", "database": "up"})
