"""Carga las copias de trabajo del ejercicio, manteniendo estables los ID de sus apartados."""
import json
import re
from pathlib import Path

from sqlalchemy import text

from ..extensions import db
from ..models import LegalProvision, LegalSource

DIRECTORY = Path(__file__).resolve().parents[3] / 'docs' / 'pims'
PREFIX = 'PIMS-SIM-'
SCOPES = {'pims': 'procedimiento', 'registros': 'registro'}


def sections(path):
    """Conserva los apartados numerados, o una fila por riesgo en las matrices."""
    if path.suffix == '.xlsx':
        from openpyxl import load_workbook
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            rows = iter(workbook.active.values)
            next(rows)  # Título
            headers = next(rows)
            for row in rows:
                if row[0]:
                    if any(value is None for value in row[:len(headers)]):
                        raise ValueError(f'{path.name}: fila incompleta o fórmula sin recalcular')
                    yield str(row[0]), str(row[3]), '\n'.join(f'{h}: {v}' for h, v in zip(headers, row))
        finally:
            workbook.close()
        return
    if path.suffix == '.docx':
        from docx import Document
        lines = [(p.style.name.startswith('Heading'), p.text) for p in Document(path).paragraphs]
    else:
        lines = [(line.startswith('## '), line.removeprefix('## ')) for line in path.read_text(encoding='utf8').splitlines()]
    current, content = None, []
    for heading, line in lines:
        if heading:
            if current:
                yield current[1], current[2], '\n'.join(content).strip()
            current = re.fullmatch(r'(\d+)\. (.+)', line)
            content = []
        elif current:
            content.append(line)
    if current:
        yield current[1], current[2], '\n'.join(content).strip()


def import_pims():
    catalog = json.loads((DIRECTORY / 'catalogo.json').read_text(encoding='utf8'))
    expected = {PREFIX + item['code'] for item in catalog}
    if not expected or len(expected) != len(catalog):
        raise ValueError('El catálogo está vacío o contiene documentos duplicados.')
    count = 0
    try:
        if db.engine.dialect.name == 'postgresql':
            db.session.execute(text('SELECT pg_advisory_xact_lock(277012025)'))
        for item in catalog:
            code = PREFIX + item['code']
            source = LegalSource.query.filter_by(code=code).one_or_none()
            if source is None:
                source = LegalSource(code=code)
                db.session.add(source)
            source.title = f"{item['title']} · v{item['version']} · simulación académica"
            source.issuing_body = 'Equipo académico del PIMS simulado'
            source.notes = item['kind']
            source.source_type = 'guidance'
            source.status = 'active'
            source.jurisdiction = 'Ejercicio de matrícula UNSA'
            db.session.flush()
            previous = {row.provision_code: row for row in source.provisions}
            seen = set()
            for order, (key, heading, body) in enumerate(sections(DIRECTORY / item['file']), 1):
                if not body or key in seen:
                    raise ValueError(f'Apartado vacío o repetido en {code}: {key}')
                seen.add(key)
                row = previous.pop(key, None)
                if row is None:
                    row = LegalProvision(source=source, provision_code=key)
                    db.session.add(row)
                row.heading = heading
                row.content = body
                row.sort_order = order
                row.verified = True  # Texto copiado del archivo identificado en el catálogo académico.
            if not seen:
                raise ValueError(f'{code} no contiene apartados consultables.')
            for old in previous.values():
                db.session.delete(old)
            count += len(seen)
        retired = LegalSource.query.filter(LegalSource.code.startswith(PREFIX),
                    LegalSource.issuing_body == 'Equipo académico del PIMS simulado',
                    ~LegalSource.code.in_(expected)).all()
        for source in retired:
            source.status = 'superseded'
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return len(catalog), count
