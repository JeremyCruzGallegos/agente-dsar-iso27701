from flask import Blueprint, request

from ..errors import ok
from ..security import require_role
from ..services import knowledge_service
from ..services.legal_search import estado_corpus

bp = Blueprint("knowledge", __name__)


@bp.get("/knowledge/status")
@require_role("service", "dpo")
def status():
    return ok(estado_corpus())


@bp.get("/knowledge/sources")
@require_role("service", "dpo")
def sources():
    return ok(knowledge_service.list_sources())


@bp.post("/knowledge/sources")
@require_role("dpo")
def create_source():
    return ok(knowledge_service.create_source(request.get_json()), 201)


@bp.get("/knowledge/sources/<int:source_id>")
@require_role("service", "dpo")
def source(source_id):
    return ok(knowledge_service.get_source(source_id))


@bp.post("/knowledge/sources/<int:source_id>/provisions")
@require_role("dpo")
def add_provision(source_id):
    return ok(knowledge_service.add_provision(source_id, request.get_json()), 201)


@bp.patch("/knowledge/provisions/<int:provision_id>")
@require_role("dpo")
def update_provision(provision_id):
    return ok(knowledge_service.update_provision(provision_id, request.get_json()))
