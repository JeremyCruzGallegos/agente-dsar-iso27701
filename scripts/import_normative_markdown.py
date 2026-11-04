"""Importa el material temporal a PostgreSQL; los Markdown nunca son consultados por el agente."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TEMPORAL = ROOT / "docs" / "temporal"
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]


SOURCES = {
    "iso_iec_27701_2025_standard.md": {
        "code": "ISO-IEC-27701-2025", "title": "ISO/IEC 27701:2025",
        "source_type": "iso", "issuing_body": "ISO/IEC", "jurisdiction": "Internacional",
        "publication_date": date(2025, 10, 14), "official_url": "https://www.iso.org/standard/27701",
        "verified": True, "profile": "iso",
        "notes": "Copia local autorizada por el equipo para uso académico; no redistribuir.",
    },
    "pol_tica_de_protecci_n_de_datos_personales_unsa.md": {
        "code": "UNSA-POL-PRIVACIDAD", "title": "Política de protección de datos personales UNSA",
        "source_type": "institutional", "issuing_body": "Universidad Nacional de San Agustín",
        "official_url": "https://www.unsa.edu.pe/servicios/politica-proteccion-datos.html",
        "verified": True, "profile": "policy",
        "notes": "Contenido institucional contrastado con la referencia oficial publicada por la UNSA.",
    },
    "decreto_supremo_016_2024_jus.md": {
        "code": "DS-016-2024-JUS", "title": "Reglamento de la Ley N.° 29733",
        "source_type": "regulation", "issuing_body": "Ministerio de Justicia y Derechos Humanos",
        "publication_date": date(2024, 11, 30),
        "official_url": "https://busquedas.elperuano.pe/dispositivo/SE/2349653-1",
        "verified": False, "profile": "articles",
        "notes": "Resumen incompleto: declara 98 artículos y solo contiene 27; la norma oficial contiene 135.",
    },
    "estatuto_universitario.md": {
        "code": "UNSA-ESTATUTO", "title": "Estatuto de la UNSA",
        "source_type": "institutional", "issuing_body": "Universidad Nacional de San Agustín",
        "publication_date": date(2015, 11, 6),
        "official_url": "https://transparencia.unsa.edu.pe/handle/123456789/784?show=full",
        "verified": False, "profile": "articles",
        "notes": "Texto parcial y sujeto a resoluciones modificatorias posteriores.",
    },
    "resoluci_n_de_consejo_universitario_n_0306_2022.md": {
        "code": "UNSA-RCU-0306-2022", "title": "RCU 0306-2022 — ROF y organigrama",
        "source_type": "institutional", "issuing_body": "Consejo Universitario UNSA",
        "verified": False, "profile": "generic", "notes": "Pendiente de cotejo con el original oficial.",
    },
    "resoluci_n_consejo_universitario_262_2020_tupa_unsa.md": {
        "code": "UNSA-RCU-0262-2020", "title": "RCU 0262-2020 — TUPA UNSA",
        "source_type": "institutional", "issuing_body": "Consejo Universitario UNSA",
        "verified": False, "profile": "generic", "notes": "Pendiente de cotejo con el original oficial.",
    },
    "oficio_370_2024_um_oppm_unsa.md": {
        "code": "UNSA-OFICIO-370-2024", "title": "Oficio 370-2024-UM-OPPM/UNSA",
        "source_type": "institutional", "issuing_body": "Universidad Nacional de San Agustín",
        "verified": False, "profile": "generic", "notes": "Compilación de documentos; pendiente de cotejo.",
    },
    "documentos_e_instrumentos_de_gesti_n_institucional.md": {
        "code": "UNSA-INSTRUMENTOS-GESTION", "title": "Documentos e instrumentos de gestión institucional",
        "source_type": "guidance", "issuing_body": "Universidad Nacional de San Agustín",
        "verified": False, "profile": "generic", "notes": "Resumen auxiliar; no constituye norma autónoma.",
    },
    "formulario_denuncia_ley_datos_personales.md": {
        "code": "ANPD-FORM-DENUNCIA", "title": "Formulario de denuncia sobre datos personales",
        "source_type": "guidance", "issuing_body": "Autoridad Nacional de Protección de Datos Personales",
        "verified": False, "profile": "generic", "notes": "Formulario de referencia, no crea obligaciones.",
    },
    "plan_estrat_gico_institucional_2025_2030_unsa.md": {
        "code": "UNSA-PEI-2025-2030", "title": "Plan Estratégico Institucional UNSA 2025-2030",
        "source_type": "institutional", "issuing_body": "Universidad Nacional de San Agustín",
        "verified": False, "profile": "generic", "notes": "Contexto institucional; baja autoridad para derechos.",
    },
    "RR-0116-2025-POI-2025.md": {
        "code": "UNSA-POI-2025", "title": "Plan Operativo Institucional UNSA 2025",
        "source_type": "institutional", "issuing_body": "Universidad Nacional de San Agustín",
        "publication_date": date(2025, 1, 1), "verified": False, "profile": "generic",
        "notes": "Contexto operativo; baja autoridad para resolver derechos.",
    },
}

HEADING = re.compile(r"^(#{2,5})\s+(.+?)\s*$")
ARTICLE = re.compile(r"^(art[ií]culo\s+\d+[^:.-]*)(?:\s*[:.-]\s*(.*))?$", re.I)
ISO_CODE = re.compile(r"^(?:[4-9]|10)(?:\.\d+)*\b|^B\.[1-3](?:\.\d+)*\b", re.I)


def plain(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower())
                   if not unicodedata.combining(c))


def clean_markdown(value: str) -> str:
    value = re.sub(r"<!--.*?-->", "", value, flags=re.S)
    value = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("__", "")
    return re.sub(r"\n{3,}", "\n\n", value).strip(" \n-")


def blocks(path: Path):
    current = None
    content: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING.match(line)
        if match:
            if current:
                yield current, clean_markdown("\n".join(content))
            current, content = match.group(2).strip(), []
        elif current:
            content.append(line)
    if current:
        yield current, clean_markdown("\n".join(content))


def relevant(profile: str, heading: str, content: str) -> bool:
    normalized = plain(heading)
    if len(content) < 35 or normalized in {"contenido", "contents", "tabla de contenidos"}:
        return False
    if profile == "iso":
        return bool(ISO_CODE.match(heading))
    if profile == "articles":
        return bool(ARTICLE.match(heading))
    if profile == "policy":
        return not normalized.startswith(("pagina ", "tabla de contenido"))
    return not any(word in normalized for word in ("tabla de contenido", "equipo tecnico", "comision de planeamiento"))


def classify(heading: str, content: str):
    text = plain(heading + " " + content)
    rules = (
        (("acceso", "access rights"), "derecho de acceso", "access"),
        (("rectificacion", "actualizacion"), "derecho de rectificación", "rectification"),
        (("cancelacion", "supresion", "deletion"), "derecho de supresión", "erasure"),
        (("oposicion",), "derecho de oposición", "objection"),
        (("portabilidad", "portability"), "derecho de portabilidad", "portability"),
        (("consentimiento", "consent"), "consentimiento", "consent"),
        (("incidente", "breach"), "incidentes de seguridad", None),
        (("seguridad", "security"), "seguridad de la información", None),
        (("retencion", "retention"), "retención", None),
        (("transferencia", "transfer"), "transferencias", None),
    )
    for terms, topic, right in rules:
        if any(term in text for term in terms):
            return topic, right
    return "privacidad y gestión institucional", None


def extract(path: Path, config: dict):
    result, seen = [], set()
    for position, (heading, content) in enumerate(blocks(path), 1):
        if not relevant(config["profile"], heading, content):
            continue
        article = ARTICLE.match(heading)
        code = article.group(1).strip() if article else heading.split(" ", 1)[0]
        title = (article.group(2) if article else heading).strip() or None
        # Los documentos genéricos pueden repetir títulos; el prefijo mantiene idempotencia.
        if config["profile"] in ("generic", "policy"):
            code = f"S{position:03d}"
        if code in seen:
            code = f"{code} [{position}]"
        seen.add(code)
        topic, right = classify(heading, content)
        result.append({"provision_code": code[:100], "heading": title[:500] if title else None,
                       "content": content, "topic": topic, "right_type": right,
                       "keywords": heading, "sort_order": position,
                       "verified": config["verified"]})
    return result


def import_all(*, apply=False):
    prepared = []
    for filename, config in SOURCES.items():
        path = TEMPORAL / filename
        if not path.exists():
            prepared.append((filename, config, [], "AUSENTE"))
            continue
        provisions = extract(path, config)
        prepared.append((filename, config, provisions, "OK"))
    if not apply:
        return prepared

    from dsar_api import create_app
    from dsar_api.extensions import db
    from dsar_api.models import LegalProvision, LegalSource
    app = create_app()
    with app.app_context():
        try:
            for _, config, provisions, state in prepared:
                if state != "OK":
                    continue
                source = LegalSource.query.filter_by(code=config["code"]).first()
                if not source:
                    source = LegalSource(code=config["code"])
                    db.session.add(source)
                for name in ("title", "source_type", "issuing_body", "jurisdiction",
                             "publication_date", "official_url", "notes"):
                    if name in config:
                        setattr(source, name, config[name])
                source.status = "active"
                db.session.flush()
                LegalProvision.query.filter_by(source_id=source.id).delete()
                for item in provisions:
                    db.session.add(LegalProvision(source_id=source.id, **item))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    return prepared


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Escribe en la base; sin esto solo simula")
    args = parser.parse_args()
    rows = import_all(apply=args.apply)
    for filename, config, provisions, state in rows:
        verified = sum(item["verified"] for item in provisions)
        print(f"{state:7} {filename}: {len(provisions)} disposiciones, {verified} verificadas")
    print("Importación aplicada." if args.apply else "Simulación: no se modificó la base.")
    return 1 if any(state != "OK" for *_, state in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
