from flask import Blueprint, request

from ..errors import ok
from ..security import require_role
from ..services import case_service, llm_service

bp = Blueprint('cases', __name__)


@bp.get('/agent/status')
@require_role('dpo')
def agent_status():
    return ok(llm_service.status())


@bp.post('/case-analysis')
@require_role('service', 'dpo')
def case_analysis():
    return ok(case_service.analyze(request.get_json()))
