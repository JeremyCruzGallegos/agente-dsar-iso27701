"""Ensayo reproducible con PostgreSQL temporal, Edge, dos servidores Flask y Ollama."""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen
import zipfile

import psycopg

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'a9420a4'


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def serve(stack, env):
    number = port()
    process = subprocess.Popen([sys.executable, 'app.py'], cwd=ROOT, env=dict(env, FLASK_PORT=str(number)),
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def stop():
        process.terminate()
        process.wait(timeout=10)
    stack.callback(stop)
    base = f'http://127.0.0.1:{number}'
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError('Flask terminó durante el arranque.')
        try:
            with urlopen(base + '/api/health', timeout=1) as response:
                if response.status == 200:
                    return base
        except (OSError, URLError):
            time.sleep(.15)
    raise RuntimeError('Flask no respondió.')


def demonstrate(pg_bin, node, output):
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='entrega3-') as tmp, ExitStack() as stack:
        work = Path(tmp)
        cluster, password = work / 'cluster', secrets.token_urlsafe(32)
        pwfile = work / 'password'
        pwfile.write_text(password, encoding='ascii')
        pg = port()
        subprocess.run([pg_bin / 'initdb', '-D', cluster, '-U', 'demo', '--pwfile', pwfile,
                        '-A', 'scram-sha-256', '-E', 'UTF8', '--locale=C'], check=True)
        pwfile.unlink()
        ctl = [pg_bin / 'pg_ctl', '-D', cluster, '-w']
        subprocess.run([*ctl, '-l', work / 'postgres.log', '-o', f'-p {pg} -h 127.0.0.1', 'start'], check=True)
        stack.callback(subprocess.run, [*ctl, 'stop', '-m', 'fast'], check=True)
        url = f'postgresql://demo:{password}@127.0.0.1:{pg}/postgres'
        env = dict(os.environ, DATABASE_URL=url.replace('postgresql:', 'postgresql+psycopg:'),
                   APP_ENV='production', FLASK_HOST='127.0.0.1', FLASK_USE_RELOADER='0',
                   FLASK_DEBUG='0', DSAR_INTAKE_MODE='direct', DPO_API_KEY=secrets.token_urlsafe(),
                   SERVICE_API_KEY=secrets.token_urlsafe(), AUDIT_HASH_KEY=secrets.token_urlsafe(),
                   OLLAMA_MODEL='qwen2.5:1.5b', OLLAMA_BASE_URL='http://127.0.0.1:11434',
                   OLLAMA_TIMEOUT_SECONDS='240', PYTHONUTF8='1')
        # Crear una base poblada con el código publicado, sin cambiar la rama del usuario.
        archive = work / 'anterior.zip'
        subprocess.run(['git', 'archive', '--format=zip', '-o', archive, BASELINE,
                        'backend', 'app.py', 'docs/pims'], cwd=ROOT, check=True)
        prior = work / 'anterior'
        with zipfile.ZipFile(archive) as z:
            z.extractall(prior)
        def flask(command, directory):
            subprocess.run([sys.executable, '-m', 'flask', '--app', 'app', command],
                           cwd=directory, check=True, env=env)
        for command in ('init-db', 'seed-demo', 'import-pims'):
            flask(command, prior)
        legacy = subprocess.check_output([sys.executable, '-c',
            "from app import app; r=app.test_client().post('/api/intake',headers={'Idempotency-Key':'historico-entrega3'},"
            "json={'user_id':'72839102','email':'ensayo@example.invalid','request_type':'Acceso','details':'Ensayo previo'});"
            "assert r.status_code==201; print(r.json['ticket_id'])"], cwd=prior, env=env, text=True).strip()
        with psycopg.connect(url, autocommit=True) as conn:
            def identities():
                rows = conn.execute('SELECT s.code,p.provision_code,p.id FROM legal_sources s JOIN legal_provisions p '
                                    'ON p.source_id=s.id ORDER BY p.id').fetchall()
                return set(rows)
            old = identities()
            flask('import-pims', ROOT)
            new = identities()
            flask('import-pims', ROOT)
            assert len(old) == 38 and len(new) == 45 and old <= new and identities() == new
            sources = conn.execute('SELECT count(*) FROM legal_sources').fetchone()[0]
            assert sources == 11
            assert conn.execute('SELECT request_type FROM dsar_requests WHERE ticket_id=%s', (legacy,)).fetchone() == ('ACCESO',)
            summary = dict(postgresql=conn.info.server_version, baseline=BASELINE, anteriores=len(old),
                           actuales=len(new), documentos=sources, ids_previos_conservados=len(old),
                           segunda_importacion_estable=True, ticket_historico=legacy)
        online = serve(stack, env)
        offline = serve(stack, dict(env, OLLAMA_BASE_URL=f'http://127.0.0.1:{port()}'))
        subprocess.run([node, 'scripts/demo_entrega3.cjs', online, offline, str(output)],
                       cwd=ROOT, env=env, check=True)
        (output / 'importacion.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pg-bin', required=True, type=Path)
    parser.add_argument('--node', default=shutil.which('node') or 'node')
    parser.add_argument('--salida', required=True, type=Path)
    args = parser.parse_args()
    demonstrate(args.pg_bin, args.node, args.salida.resolve())
