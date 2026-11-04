from pathlib import Path

from scripts.import_normative_markdown import extract


def test_extracts_articles_and_discards_table_of_contents(tmp_path):
    path = tmp_path / "law.md"
    path.write_text("""# Norma
## Tabla de contenidos
Artículo 1 ..... 2
### Artículo 1.- Objeto
Este artículo regula el ejercicio verificable de un derecho del titular.
### Artículo 2.- Acceso
El titular puede solicitar acceso a la información registrada.
""", encoding="utf-8")
    rows = extract(path, {"profile": "articles", "verified": False})
    assert [row["provision_code"] for row in rows] == ["Artículo 1", "Artículo 2"]
    assert rows[1]["right_type"] == "access"
    assert all(row["verified"] is False for row in rows)


def test_iso_profile_only_keeps_operational_clauses(tmp_path):
    path = tmp_path / "iso.md"
    path.write_text("""# ISO
## COPYRIGHT PROTECTED DOCUMENT
Texto de copyright suficientemente largo que no debe convertirse en evidencia.
## 1 Scope
Alcance introductorio suficientemente largo que tampoco se importa.
### 4.1 Context
The organization shall determine privacy context and relevant interested parties.
#### B.1.3 Obligations to PII principals
The controller should establish obligations related to PII principals and access rights.
""", encoding="utf-8")
    rows = extract(path, {"profile": "iso", "verified": True})
    assert [row["provision_code"] for row in rows] == ["4.1", "B.1.3"]
    assert all(row["verified"] is True for row in rows)


def test_duplicate_article_numbers_receive_unique_codes(tmp_path):
    path = tmp_path / "regulation.md"
    path.write_text("""# Decreto
### Artículo 1.- Aprobación
El decreto aprueba un reglamento adjunto con disposiciones suficientes.
## Reglamento adjunto
### Artículo 1.- Objeto
El reglamento desarrolla el objeto y alcance del tratamiento regulado.
""", encoding="utf-8")
    rows = extract(path, {"profile": "articles", "verified": False})
    assert rows[0]["provision_code"] == "Artículo 1"
    assert rows[1]["provision_code"].startswith("Artículo 1 [")
    assert len({row["provision_code"] for row in rows}) == 2
