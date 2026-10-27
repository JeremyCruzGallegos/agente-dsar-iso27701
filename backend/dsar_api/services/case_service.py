"""Análisis extractivo de casos, limitado a las fuentes locales indexadas."""
from ai_engine.search_engine import SearchUnavailable, buscar_pii_vectorial, validar_consulta

from ..errors import ApiError, ValidationError
from . import audit_service
from .validators import require_json


def analyze(payload):
    payload = require_json(payload)
    try:
        caso = validar_consulta(payload.get('case'), 8)
    except ValueError as exc:
        raise ValidationError(str(exc).replace('query', 'case')) from exc
    try:
        resultados = buscar_pii_vectorial(caso, 8)
    except SearchUnavailable as exc:
        raise ApiError(str(exc), code='case_analysis_unavailable', status_code=503) from exc
    except Exception as exc:
        raise ApiError('No se pudo analizar el caso.', code='case_analysis_failed', status_code=500) from exc

    fuentes, evidencias = [], []
    for resultado in resultados:
        referencia = resultado['fuente']
        if resultado.get('seccion'):
            referencia += ' — ' + resultado['seccion']
        if referencia not in fuentes:
            fuentes.append(referencia)
        evidencias.append({
            'id': len(evidencias) + 1,
            'source': resultado['fuente'],
            'section': resultado.get('seccion'),
            'excerpt': resultado['texto'],
            'score': resultado['score'],
        })

    if evidencias:
        referencias = ', '.join(f'[{item["id"]}]' for item in evidencias[:3])
        respuesta = (
            f'Se encontraron disposiciones relacionadas con el caso en {len(fuentes)} fuente(s) '
            f'({referencias}). Revisa los fundamentos recuperados antes de emitir una conclusión. '
            'El sistema no encontró por sí solo una decisión obligatoria: la interpretación debe '
            'justificarse con el texto completo, su vigencia y la jerarquía de cada norma.'
        )
        cobertura = 'evidence_found'
    else:
        respuesta = (
            'No se encontró sustento suficiente en la documentación indexada. No corresponde '
            'inventar una respuesta; incorpora la norma aplicable o reformula el caso.'
        )
        cobertura = 'insufficient_evidence'

    audit_service.record('CASE_ANALYSIS', entity_type='document',
                         detail={'count': len(evidencias), 'sources': len(fuentes)})
    return {
        'answer': respuesta,
        'coverage': cobertura,
        'evidence': evidencias,
        'notice': ('Análisis académico preliminar basado únicamente en documentos locales. '
                   'No sustituye una decisión legal, administrativa ni de auditoría.'),
    }
