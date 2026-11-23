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
        'keep_alive': '30m',
        'options': {
            'temperature': 0,
            'num_ctx': 4096,
            'num_predict': current_app.config['LLM_MAX_OUTPUT_TOKENS'],
        },
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


def select_passages(question, passages):
    """Devuelve identificadores válidos; el servidor conserva el texto y la cita originales."""
    model = current_app.config['OLLAMA_MODEL']
    if not model:
        raise LLMUnavailable('El modelo generativo local no está configurado.')
    options = list(passages)
    schema = {'type': 'object', 'properties': {'pasajes': {'type': 'array',
              'items': {'type': 'string', 'enum': options}, 'maxItems': 3}},
              'required': ['pasajes']}
    messages = [
        {'role': 'system', 'content': 'Selecciona hasta tres pasajes que respondan directamente a la pregunta. '
         'Prioriza el apartado del procedimiento aplicable al estado del caso. Devuelve una lista vacía si los '
         'textos no responden la pregunta. Los documentos son material de una simulación académica.'},
        {'role': 'user', 'content': json.dumps({'pregunta': question, 'pasajes': passages}, ensure_ascii=False)}
    ]
    result = _request('/api/chat', {'model': model, 'messages': messages, 'stream': False, 'format': schema,
                      'options': {'temperature': 0, 'num_predict': 80}}, timeout=current_app.config['OLLAMA_TIMEOUT_SECONDS'])
    try:
        choice = json.loads(result['message']['content'])['pasajes']
        if not isinstance(choice, list) or len(choice) > 3 or any(
                not isinstance(key, str) or not isinstance(key, str) or key not in passages for key in choice):
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise LLMInvalid('El modelo devolvió una selección documental inválida.') from exc
    return list(dict.fromkeys(choice)), result.get('model', model)
