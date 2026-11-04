"""Inicializa y comprueba el corpus normativo en la base de datos."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]


def main():
    from dsar_api import create_app
    from dsar_api.extensions import db
    from dsar_api.services.legal_search import estado_corpus
    app = create_app()
    with app.app_context():
        db.create_all()
        status = estado_corpus()
    print("Base de datos preparada.")
    print(f"Fuentes activas: {status['sources']}; disposiciones verificadas: {status['provisions']}.")
    if not status["ready"]:
        print("Carga fuentes y disposiciones mediante /api/knowledge antes de consultar al agente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
