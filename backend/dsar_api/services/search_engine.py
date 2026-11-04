"""Adaptador entre la API autenticada y el corpus normativo SQL."""
from .legal_search import SearchUnavailable, buscar_normativa as buscar_pii_vectorial, validar_consulta

from ..errors import ApiError, ValidationError
from . import audit_service
from .validators import require_json
from .validators import clean_document_id


def search(payload):
    payload = require_json(payload)
    query, k = payload.get('query'), payload.get('k', 5)
    try:
        query = validar_consulta(query, k)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    user_id = clean_document_id(payload['user_id']) if 'user_id' in payload else None
    try:
        results = (buscar_pii_vectorial(query, k, user_id=user_id) if user_id is not None
                   else buscar_pii_vectorial(query, k))
    except SearchUnavailable as exc:
        raise ApiError(str(exc), code='vector_search_unavailable', status_code=503) from exc
    except Exception as exc:
        raise ApiError('No se pudo completar la búsqueda normativa.',
                       code='vector_search_failed', status_code=500) from exc
    audit_service.record('LEGAL_SEARCH', entity_type='legal_provision',
                         detail={'k': k, 'count': len(results)})
    return {'results': results, 'count': len(results), 'metric': 'weighted_term_match'}
