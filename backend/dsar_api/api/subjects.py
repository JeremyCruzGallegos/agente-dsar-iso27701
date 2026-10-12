from flask import Blueprint, request

from ..errors import ok
from ..security import require_role
from ..services import subject_service

bp = Blueprint("subjects", __name__)

ROLES = ("service", "dpo")


@bp.get("/user-data")
@require_role(*ROLES)
def user_data():
    """Acceso / Portabilidad. `?format=portable` entrega un JSON de portabilidad."""
    portable = request.args.get("format") == "portable"
    data = subject_service.access_data(
        request.args.get("user_id", ""), portable=portable, ticket_id=request.args.get("ticket_id")
    )
    return ok(data)


@bp.post("/users")
@require_role(*ROLES)
def create_user():
    subject = subject_service.create_subject(request.get_json(silent=True))
    return ok(subject.to_dict(), 201)


@bp.patch("/rectify-user")
@require_role(*ROLES)
def rectify_user():
    subject = subject_service.rectify(request.get_json(silent=True))
    return ok(subject.to_dict())


@bp.post("/delete-user")
@require_role(*ROLES)
def delete_user():
    """Supresión por anonimización; 409 `retention_blocked` si hay retención legal."""
    return ok(subject_service.erase(request.get_json(silent=True)))
