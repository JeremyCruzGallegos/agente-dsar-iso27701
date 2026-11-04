"""Comprueba la conexión y resume el corpus normativo SQL."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from dsar_api import create_app
from dsar_api.services.legal_search import estado_corpus

app = create_app()
with app.app_context():
    status = estado_corpus()
print(status["message"])
print(f"Fuentes: {status['sources']}; disposiciones verificadas: {status['provisions']}.")
