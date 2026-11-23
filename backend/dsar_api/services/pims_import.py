"""Carga las copias de trabajo del ejercicio, manteniendo estables los ID de sus apartados."""
import json
import re
from pathlib import Path

from sqlalchemy import text

from docx import Document
from docx.table import Table
from openpyxl import load_workbook

from ..models.legal_knowledge import PimsOrigin
from ..extensions import db
from ..models import LegalProvision, LegalSource

DIRECTORY = Path(__file__).resolve().parents[3] / 'docs' / 'pims'
PREFIX = 'PIMS-SIM-'
SCOPES = {'pims': 'procedimiento', 'registros': 'registro'}


def matrix_sections(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        for sheet in workbook.worksheets:
            headers = None
            for number, values in enumerate(sheet.values, 1):
                if values[0] == 'Código':
                    headers = list(values)
                    continue
                if not headers or not any(value is not None for value in values):
                    continue
                fields = dict(zip(headers, values))
                if not all(headers) or len(fields) != len(headers) or None in fields.values():
                    raise ValueError(f'{path.name}, {sheet.title}, fila {number}: datos incompletos')
                key = str(fields['Código'])
                locator = f'{sheet.title}, fila {number} ({key})'
                yield key, str(fields.get('Amenaza', key)), '\n'.join(
                    f'{h}: {v}' for h, v in fields.items()), locator
    finally:
        workbook.close()


def word_blocks(path):
    table_number = 0
    for block in Document(path).iter_inner_content():
        if isinstance(block, Table):
            table_number += 1
            rows = iter(block.rows)
            header = next(rows, None)
            if header:
                names = [cell.text.strip() for cell in header.cells]
                yield False, f'Tabla {table_number}: ' + ' | '.join(names)
                for number, row in enumerate(rows, 2):
                    yield False, f'Tabla {table_number}, fila {number}: ' + ' | '.join(f'{name}: {cell.text.strip()}'
                                            for name, cell in zip(names, row.cells))
        else:
            yield block.style.name.startswith('Heading'), block.text


def sections(path):
    if path.suffix == '.xlsx':
        yield from matrix_sections(path)
        return
    word = path.suffix == '.docx'
    blocks = word_blocks(path) if word else (
        (line.startswith('## '), line.removeprefix('## '))
        for line in path.read_text(encoding='utf8').splitlines())
    key, title = 'ficha', 'Ficha documental y referencias de curso'
    body = []
    for heading, line in blocks:
        match = re.fullmatch(r'(\d+)\. (.+)', line) if heading else None
        if heading and (match or not word):
            if key and (body or key != 'ficha'):
                yield key, title, '\n'.join(body), ('Antes del primer apartado' if key == 'ficha'
                                                    else f'{key}. {title}')
            key, title = match.groups() if match else (None, None)
            body = []
        elif key and line.strip() and (word or key != 'ficha'):
            body.append(line.strip())
    if key and (body or key != 'ficha'):
        yield key, title, '\n'.join(body), f'{key}. {title}'


def import_pims():
    catalog = json.loads((DIRECTORY / 'catalogo.json').read_text(encoding='utf8'))
    expected = {PREFIX + item['code'] for item in catalog}
    if not expected or len(expected) != len(catalog):
        raise ValueError('El catálogo está vacío o contiene documentos duplicados.')
    count = 0
    try:
        if db.engine.dialect.name == 'postgresql':
            db.session.execute(text('SELECT pg_advisory_xact_lock(277012025)'))
        PimsOrigin.__table__.create(db.session.connection(), checkfirst=True)
        for item in catalog:
            code = PREFIX + item['code']
            source = LegalSource.query.filter_by(code=code).one_or_none()
            if source and source.issuing_body != 'Equipo académico del PIMS simulado':
                raise ValueError(f'El código {code} pertenece a otra fuente.')
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
            for order, (key, heading, body, locator) in enumerate(sections(DIRECTORY / item['file']), 1):
                if not body or key in seen:
                    raise ValueError(f'Apartado vacío o repetido en {code}: {key}')
                seen.add(key)
                row = previous.pop(key, None)
                if row is None:
                    row = LegalProvision(source=source, provision_code=key)
                    db.session.add(row)
                origin = row.origin or PimsOrigin(provision=row)
                db.session.add(origin)
                origin.file, origin.version = item['file'], item['version']
                origin.locator, origin.template = locator, item['template']
                row.heading = heading
                row.content = body
                row.sort_order = order
                row.verified = True  # Texto copiado del archivo identificado en el catálogo académico.
            if not seen:
                raise ValueError(f'{code} no contiene apartados consultables.')
            for old in previous.values():
                db.session.delete(old)
            count += len(seen)
        retired = LegalSource.query.filter(
            LegalSource.code.startswith(PREFIX), ~LegalSource.code.in_(expected),
            LegalSource.provisions.any(LegalProvision.origin.has()),
        )
        for source in retired:
            source.status = 'superseded'
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return len(catalog), count
