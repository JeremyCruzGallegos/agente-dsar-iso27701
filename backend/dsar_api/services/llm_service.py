"""Cliente mínimo para generar texto fundamentado con Ollama local."""
from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from flask import current_app


class LLMUnavailable(RuntimeError):
    """Ollama o el modelo configurado no están disponibles."""


class LLMInvalid(RuntimeError):
    """El modelo respondió con texto vacío o inutilizable."""


def _endpoint(path: str) -> str:
    base = current_app.config['OLLAMA_BASE_URL'].rstrip('/')
    parsed = urlparse(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise LLMUnavailable('OLLAMA_BASE_URL no es válida.')
    return base + path


def _request(path: str, payload: dict | None = None, *, timeout: int = 5):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = Request(_endpoint(path), data=data,
                      headers={'Content-Type': 'application/json'},
                      method='POST' if data is not None else 'GET')
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMUnavailable('Ollama no está disponible o el modelo no está preparado.') from exc


def status():
    model = current_app.config.get('OLLAMA_MODEL', '').strip()
    if not model:
        return {'ready': False, 'model': None,
                'message': 'Configura OLLAMA_MODEL para generar conclusiones.'}
    try:
        result = _request('/api/tags')
        names = {item.get('name') for item in result.get('models', [])}
        ready = model in names
        return {'ready': ready, 'model': model,
                'message': ('Modelo generativo local listo.' if ready else
                            f'Falta descargar el modelo local: ollama pull {model}')}
    except LLMUnavailable as exc:
        return {'ready': False, 'model': model, 'message': str(exc)}


def generate(messages: list[dict]):
    model = current_app.config.get('OLLAMA_MODEL', '').strip()
    if not model:
        raise LLMUnavailable('El modelo generativo local no está configurado.')
    payload = {
        'model': model,
        'messages': messages,
        'stream': False,
        'keep_alive': '2m',
        'options': {'temperature': 0, 'num_predict': 850},
    }
    result = _request('/api/chat', payload,
                      timeout=current_app.config['OLLAMA_TIMEOUT_SECONDS'])
    try:
        answer = result['message']['content'].strip()
        if not answer:
            raise ValueError
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise LLMInvalid('El modelo generativo devolvió una respuesta vacía.') from exc
    citations = list(dict.fromkeys(int(value) for value in re.findall(r'\[(\d+)\]', answer)))
    return {'answer': answer, 'citations': citations, 'limitations': [],
            'confidence': 'media', 'model': result.get('model', model)}
