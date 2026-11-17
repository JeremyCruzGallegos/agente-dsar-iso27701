"""Recuperación de casos guía UNSA que orientan, pero no fundamentan, la respuesta."""
from __future__ import annotations

import math

from ..models import InstitutionalCaseGuide
from .legal_search import _query_tokens, _tokens


def _score(query_tokens, guide):
    fields = (
        (guide.title, 3.0), (guide.area, 2.5), (guide.keywords, 3.0),
        (guide.scenario, 1.5), (guide.reasoning_focus, 1.0),
    )
    score = sum(weight * len(query_tokens & _tokens(value)) for value, weight in fields)
    return score / math.sqrt(max(1, len(query_tokens)))


def buscar_casos_guia(query_text, k=2):
    """Devuelve ejemplos institucionales similares sin tratarlos como autoridad normativa."""
    if k <= 0:
        return []
    tokens = _query_tokens(query_text)
    ranked = [(row, _score(tokens, row))
              for row in InstitutionalCaseGuide.query.filter_by(active=True).all()]
    ranked = [(row, score) for row, score in ranked if score > 0]
    ranked.sort(key=lambda item: (-item[1], item[0].code))
    return [{**row.to_dict(), "score": round(float(score), 6)} for row, score in ranked[:k]]
