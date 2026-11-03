"""Valida metadatos y estructura antes de indexar documentos Markdown."""
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'ai_engine' / 'documentos'
FOLDERS = {
    'legislacion': 'norma',
    'unsa': 'institucional',
    'iso': 'iso',
    'referencias': 'referencia',
    'casos_ficticios': 'caso_ficticio',
}
REQUIRED = {
    'titulo', 'tipo', 'entidad', 'fecha_publicacion', 'estado', 'fuente_oficial',
    'documento_completo', 'verificado_por', 'fecha_verificacion',
}
AUTHORITATIVE = {'norma', 'institucional', 'iso'}


def _frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not match:
        return None
    values = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            values[key.strip()] = value.strip().strip('"\'')
    return values


def validate_document(path, docs_dir=DOCS):
    errors = []
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return ['no se puede leer como UTF-8']
    metadata = _frontmatter(text)
    if metadata is None:
        return ['falta el bloque de metadatos entre ---']
    missing = sorted(REQUIRED - metadata.keys())
    if missing:
        errors.append('faltan metadatos: ' + ', '.join(missing))
    relative = path.relative_to(docs_dir)
    folder = relative.parts[0] if len(relative.parts) > 1 else ''
    expected = FOLDERS.get(folder)
    if not expected:
        errors.append('debe estar dentro de una categoría reconocida')
    elif metadata.get('tipo') != expected:
        errors.append(f'tipo debe ser {expected} para la carpeta {folder}')
    kind = metadata.get('tipo')
    if kind in AUTHORITATIVE:
        if not metadata.get('fuente_oficial', '').startswith(('https://', 'http://')):
            errors.append('una fuente autoritativa requiere URL oficial')
        if metadata.get('documento_completo', '').lower() != 'true':
            errors.append('una fuente autoritativa debe declararse completa')
    if not re.search(r'(?m)^#\s+\S', text):
        errors.append('falta un título Markdown de nivel 1')
    if not re.search(r'(?m)^##+\s+\S', text):
        errors.append('falta al menos una sección o artículo')
    if len(text) < 300:
        errors.append('el documento es demasiado corto para aportar contexto')
    return errors


def validate_all(docs_dir=DOCS):
    files = sorted(docs_dir.rglob('*.md'))
    invalid = {path: errors for path in files if (errors := validate_document(path, docs_dir))}
    for path in docs_dir.rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.txt', '.pdf'):
            invalid[path] = ['convierte este archivo a Markdown validado antes de indexarlo']
    return files, invalid


def main():
    files, invalid = validate_all()
    if not files:
        print('No hay documentos Markdown. Usa docs/PLANTILLA_FUENTE.md.', file=sys.stderr)
        return 1
    if invalid:
        for path, errors in invalid.items():
            print(path.relative_to(ROOT).as_posix() + ':', file=sys.stderr)
            for error in errors:
                print('  - ' + error, file=sys.stderr)
        return 1
    print(f'Documentos válidos: {len(files)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
