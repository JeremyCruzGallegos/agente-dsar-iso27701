from flask import Blueprint, current_app, request

from ..errors import ok
from ..security import require_role
from ..services import audit_service
from ..services.validators import clean_document_id, clean_pagination

bp = Blueprint("audit", __name__)


@bp.get("/audit-log")
@require_role("dpo")  # sólo el DPO consulta la bitácora
def audit_log():
    limit, offset = clean_pagination(
        request.args,
        default=current_app.config["DEFAULT_PAGE_SIZE"],
        maximum=current_app.config["MAX_PAGE_SIZE"],
    )
    user_id = request.args.get("user_id")
    total, rows = audit_service.query_logs(
        document_id=clean_document_id(user_id) if user_id else None,
        ticket_id=request.args.get("ticket_id"),
        action=request.args.get("action"),
        outcome=request.args.get("outcome"),
        limit=limit,
        offset=offset,
    )
    return ok([r.to_dict() for r in rows], total=total, limit=limit, offset=offset)
