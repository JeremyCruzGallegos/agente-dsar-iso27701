"""Recuperación del conocimiento normativo almacenado en la base de datos."""
from __future__ import annotations

import math
import re
import unicodedata

from sqlalchemy import func

from ..extensions import db
from ..models import LegalProvision, LegalSource


class SearchUnavailable(RuntimeError):
    pass


def validar_consulta(value, k=5):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("query debe ser texto no vacío.")
    if len(value) > 4000:
        raise ValueError("query admite hasta 4000 caracteres.")
    if type(k) is not int or not 1 <= k <= 50:
        raise ValueError("k debe ser un entero entre 1 y 50.")
    return value.strip()


def _plain(value):
    return "".join(c for c in unicodedata.normalize("NFKD", (value or "").lower())
                   if not unicodedata.combining(c))


def _tokens(value):
    return {token for token in re.findall(r"[a-z0-9]{3,}", _plain(value))
            if token not in {"para", "como", "esta", "este", "debe", "datos", "sobre"}}


def _score(query_tokens, provision):
    fields = (
        (provision.source.code, 4.0), (provision.source.title, 3.0),
        (provision.provision_code, 4.0), (provision.heading, 3.0),
        (provision.topic, 2.5), (provision.right_type, 2.5),
        (provision.keywords, 2.0), (provision.content, 1.0),
    )
    score = 0.0
    for value, weight in fields:
        words = _tokens(value)
        score += weight * len(query_tokens & words)
    return score / math.sqrt(max(1, len(query_tokens)))


def buscar_normativa(query_text, k=5, *, user_id=None):
    """Devuelve disposiciones verificadas y vigentes ordenadas por coincidencia."""
    del user_id  # El corpus normativo no contiene datos personales de titulares.
    query = validar_consulta(query_text, k)
    tokens = _tokens(query)
    try:
        rows = (LegalProvision.query.join(LegalSource)
                .filter(LegalProvision.verified.is_(True), LegalSource.status == "active")
                .all())
    except Exception as exc:
        raise SearchUnavailable("No se pudo consultar el corpus normativo en la base de datos.") from exc
    ranked = [(row, _score(tokens, row)) for row in rows]
    ranked = [(row, score) for row, score in ranked if score > 0]
    ranked.sort(key=lambda item: (-item[1], item[0].source.code, item[0].sort_order))
    return [{
        "texto": row.content,
        "fuente": f"{row.source.code} — {row.source.title}",
        "seccion": " — ".join(filter(None, (row.provision_code, row.heading))),
        "score": round(float(score), 6),
        "source_type": ("institutional" if row.source.source_type == "institutional" else "normative"),
        "database_source_type": row.source.source_type,
        "source_id": row.source_id,
        "provision_id": row.id,
        "official_url": row.source.official_url,
    } for row, score in ranked[:k]]


def buscar_exacta(term):
    term = validar_consulta(term)
    pattern = f"%{term}%"
    rows = (LegalProvision.query.join(LegalSource)
            .filter(LegalProvision.verified.is_(True), LegalSource.status == "active",
                    LegalProvision.content.ilike(pattern)).limit(50).all())
    return [{"texto": row.content, "fuente": f"{row.source.code} — {row.source.title}",
             "seccion": row.provision_code, "score": 1.0,
             "source_type": row.source.source_type, "provision_id": row.id}
            for row in rows]


def estado_corpus():
    try:
        sources = LegalSource.query.filter_by(status="active").count()
        provisions = (db.session.query(func.count(LegalProvision.id)).join(LegalSource)
                      .filter(LegalSource.status == "active", LegalProvision.verified.is_(True)).scalar())
        ready = bool(provisions)
        return {"ready": ready, "documents": sources, "chunks": provisions,
                "sources": sources, "provisions": provisions,
                "message": ("Corpus normativo de base de datos listo."
                            if ready else "La base no contiene disposiciones verificadas.")}
    except Exception as exc:
        raise SearchUnavailable("No se pudo comprobar el corpus normativo.") from exc
