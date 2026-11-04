"""Diagnóstico de configuración/servicios; no muestra claves ni datos del titular."""
import argparse
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, ProxyHandler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:5000')
    args = parser.parse_args()
    urlopen = build_opener(ProxyHandler({})).open
    from dsar_api import create_app
    app = create_app()
    failed = False
    for name in ('SERVICE_API_KEY', 'DPO_API_KEY', 'AUDIT_HASH_KEY'):
        present = bool(app.config[name]); failed |= not present
        print(f'{name}: {"configurada" if present else "FALTA (ejecuta scripts/setup.py)"}')
    print('Modo de entrada:', app.config['DSAR_INTAKE_MODE'])
    if app.config['DSAR_INTAKE_MODE'] == 'n8n':
        present = bool(app.config['N8N_WEBHOOK_TOKEN']); failed |= not present
        print('Credencial del webhook:', 'configurada' if present else 'FALTA')
        from urllib.parse import urlsplit
        parts = urlsplit(app.config['N8N_WEBHOOK_URL'])
        try:
            with urlopen(f'{parts.scheme}://{parts.netloc}/healthz', timeout=5) as response:
                print('n8n:', response.status)
        except (URLError, OSError):
            print('n8n no responde: verifica servicio, puerto y hostname (Docker usa backend/n8n, no localhost).'); failed = True
        print('Comprueba que el flujo esté publicado y ambas credenciales Header Auth coincidan. No se envió ninguna solicitud.')
    try:
        with urlopen(args.url.rstrip('/') + '/api/health', timeout=5) as response:
            print('Flask:', json.load(response)['data'])
    except HTTPError as error:
        try: print('Flask:', json.load(error)['error']['message'])
        except (ValueError, KeyError): print('Flask: respuesta HTTP', error.code)
        failed = True
    except (URLError, OSError):
        print('Flask no responde: inicia python app.py, verifica puerto y URL.'); failed = True
    with app.app_context():
        from dsar_api.services.legal_search import estado_corpus
        status = estado_corpus()
        print(f"Corpus SQL: {status['sources']} fuentes, {status['provisions']} disposiciones verificadas")
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
