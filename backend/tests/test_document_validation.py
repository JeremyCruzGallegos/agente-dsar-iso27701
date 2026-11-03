from pathlib import Path

from scripts.validate_documents import validate_all, validate_document


VALID = """---
titulo: Norma de prueba
tipo: norma
entidad: Entidad oficial
fecha_publicacion: 2026-01-01
estado: vigente
fuente_oficial: https://example.edu/norma
documento_completo: true
verificado_por: Equipo
fecha_verificacion: 2026-11-03
---
# Norma de prueba
## Artículo 1. Objeto
""" + ('Contenido oficial de prueba. ' * 8)


def test_valid_authoritative_document(tmp_path):
    docs = tmp_path / 'documentos'; folder = docs / 'legislacion'; folder.mkdir(parents=True)
    path = folder / 'norma.md'; path.write_text(VALID, encoding='utf-8')
    assert validate_document(path, docs) == []


def test_rejects_missing_metadata_and_wrong_category(tmp_path):
    docs = tmp_path / 'documentos'; folder = docs / 'unsa'; folder.mkdir(parents=True)
    path = folder / 'norma.md'; path.write_text(VALID.replace('tipo: norma', 'tipo: referencia'), encoding='utf-8')
    errors = validate_document(path, docs)
    assert any('tipo debe ser institucional' in error for error in errors)
    path.write_text('# Sin metadatos\n## Sección\n' + 'texto ' * 60, encoding='utf-8')
    assert validate_document(path, docs) == ['falta el bloque de metadatos entre ---']


def test_rejects_legacy_txt_or_pdf_files(tmp_path):
    docs = tmp_path / 'documentos'; folder = docs / 'referencias'; folder.mkdir(parents=True)
    (folder / 'valido.md').write_text(VALID.replace('tipo: norma', 'tipo: referencia'), encoding='utf-8')
    legacy = folder / 'documento.txt'; legacy.write_text('texto', encoding='utf-8')
    _, invalid = validate_all(docs)
    assert legacy in invalid
