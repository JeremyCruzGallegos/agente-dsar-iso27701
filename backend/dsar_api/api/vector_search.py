from flask import Blueprint, request

from ..errors import ok
from ..security import require_role
from ..services import search_engine

bp = Blueprint('vector_search', __name__)


@bp.post('/vector-search')
@require_role('service', 'dpo')
def vector_search():
    return ok(search_engine.search(request.get_json()))
