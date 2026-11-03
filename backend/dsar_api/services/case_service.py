"""RAG de casos: recupera evidencia y genera una conclusión local con citas."""
from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from flask import current_app

from ai_engine.search_engine import SearchUnavailable, buscar_pii_vectorial, validar_consulta

from ..errors import ApiError, ValidationError
from . import audit_service, llm_service
from .validators import require_json

ROOT = Path(__file__).resolve().parents[3]
SKILL_PATH = ROOT / 'skills' / 'analizar-caso-normativo' / 'SKILL.md'
MAX_HISTORY = 8


def _plain(text):
    return ''.join(char for char in unicodedata.normalize('NFKD', text.lower())
                   if not unicodedata.combining(char))


def _is_followup(case):
    plain = _plain(case)
    markers = ('acciones concretas', 'que hacer', 'primero', 'ese caso', 'lo anterior',
               'y si', 'que plazo', 'puedes explicar', 'por que')
    return len(plain.split()) <= 7 or any(marker in plain for marker in markers)


def _retrieval_query(case, history):
    base = case
    followup = _is_followup(case)
    if followup:
        previous = next((item['content'] for item in reversed(history)
                         if item['role'] == 'user'), '')
        if previous:
            base = previous + '\nPregunta de seguimiento: ' + case
    plain = _plain(base)
    expansions = []
    if any(term in plain for term in ('acceso', 'consultar mis datos', 'conocer mis datos')):
        expansions.append('derecho de acceso e información datos personales titular ejercicio solicitud respuesta')
    if any(term in plain for term in ('filtr', 'fuga', 'incidente', 'expuest', 'vulneracion')):
        expansions.append('incidente de seguridad filtración datos personales notificación autoridad titulares afectados medidas de seguridad')
    if any(term in plain for term in ('rectific', 'corregir', 'actualizar datos')):
        expansions.append('derecho de rectificación actualización datos personales')
    if any(term in plain for term in ('suprim', 'eliminar', 'borrar', 'cancelacion')):
        expansions.append('derecho de cancelación supresión datos personales conservación')
    if 'consent' in plain:
        expansions.append('consentimiento tratamiento datos personales revocación finalidad')
    return (base + '\n' + ' '.join(expansions))[:4000], followup


def _history(value):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > MAX_HISTORY:
        raise ValidationError(f'history debe contener como máximo {MAX_HISTORY} mensajes.')
    clean = []
    for item in value:
        if not isinstance(item, dict) or item.get('role') not in ('user', 'assistant'):
            raise ValidationError('Cada mensaje de history requiere role user o assistant.')
        content = item.get('content')
        if not isinstance(content, str) or not content.strip() or len(content) > 4000:
            raise ValidationError('Cada mensaje de history debe contener entre 1 y 4000 caracteres.')
        clean.append({'role': item['role'], 'content': content.strip()})
    return clean


def _source_type(source):
    normalized = source.replace('\\', '/').lower()
    name = normalized.rsplit('/', 1)[-1]
    if normalized.startswith('casos_ficticios/'):
        return 'fictitious_case'
    if name.startswith(('formulario_', 'documentos_e_instrumentos_')):
        return 'reference'
    if normalized.startswith('unsa/'):
        return 'institutional'
    if normalized.startswith(('legislacion/', 'iso/')):
        return 'normative'
    return 'reference'


def _evidence(results):
    return [{
        'id': index,
        'source': result['fuente'],
        'section': result.get('seccion'),
        'excerpt': result['texto'],
        'score': result['score'],
        'source_type': _source_type(result['fuente']),
    } for index, result in enumerate(results, 1)]


def _skill_rules():
    try:
        text = SKILL_PATH.read_text(encoding='utf-8')
        return re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL).strip()
    except OSError:
        return ('Cita toda conclusión con [n]. No inventes obligaciones. '
                'Indica cuando la evidencia sea insuficiente.')


def _messages(case, history, evidence, *, followup=False):
    max_chars = current_app.config['LLM_CONTEXT_MAX_CHARS']
    blocks, used = [], 0
    normative = [item for item in evidence if item['source_type'] in ('normative', 'institutional')]
    # Una conclusión normativa no debe contaminarse con la resolución inventada
    # de un caso de estudio cuando ya existen normas recuperadas.
    prompt_evidence = normative or evidence
    for item in prompt_evidence:
        label = 'CASO FICTICIO, NO ES NORMA' if item['source_type'] == 'fictitious_case' else item['source_type'].upper()
        block = (f"[{item['id']}] Tipo: {label}\nFuente: {item['source']}\n"
                 f"Sección: {item['section'] or 'Sin sección'}\nFragmento:\n{item['excerpt']}")
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    shape = (
        'Responde únicamente la PREGUNTA DE SEGUIMIENTO. No repitas el análisis ni la conclusión anterior. '
        'Si pide acciones, entrega una lista numerada de pasos concretos y ordenados.'
        if followup else
        'Responde el CASO ACTUAL con tres apartados: Análisis, Conclusión y Acciones recomendadas.'
    )
    response_rules = (
        'Responde únicamente con el resultado final en texto plano. ' + shape + ' '
        'Cada afirmación documental debe incluir citas [n] usando solo los IDs proporcionados. '
        'No inventes causales de rechazo, requisitos, plazos ni obligaciones. Si falta información, '
        'indícalo al final bajo el apartado Límites. No devuelvas JSON.'
    )
    system = (
        'Eres un agente académico de análisis normativo de la UNSA. Usa EXCLUSIVAMENTE la evidencia '
        'proporcionada. Los casos ficticios sirven como ejemplo, nunca como autoridad normativa. '
        'Los formularios y documentos-resumen son referencias auxiliares, no crean obligaciones. '
        'No afirmes vigencia, jerarquía ni texto completo si el fragmento no lo demuestra. '
        'No combines frases de fuentes diferentes como si pertenecieran a una sola.\n\n'
        + _skill_rules() + '\n\n' + response_rules
    )
    messages = [{'role': 'system', 'content': system}]
    messages.extend(history[-MAX_HISTORY:])
    context = '\n\n'.join(blocks)
    messages.append({'role': 'user', 'content': f'CASO ACTUAL:\n{case}\n\nEVIDENCIA RECUPERADA:\n{context}'})
    return messages


def _fallback(evidence, reason):
    if not evidence:
        answer = ('No se encontró sustento suficiente en la documentación indexada. No corresponde '
                  'inventar una conclusión; incorpora una fuente aplicable o reformula el caso.')
        coverage = 'insufficient_evidence'
    else:
        refs = ', '.join(f'[{row["id"]}]' for row in evidence[:3])
        answer = (f'Se recuperó evidencia relacionada {refs}, pero el modelo generativo local no pudo '
                  'producir una conclusión validada. Revisa los fragmentos mostrados.')
        coverage = 'evidence_found'
    return {'answer': answer, 'coverage': coverage, 'mode': 'retrieval_only',
            'model': None, 'confidence': 'baja', 'citations': [], 'limitations': [reason]}


def _remove_unsupported_rejections(answer):
    """Retira causales de denegación sensibles si el modelo no las cita en esa frase."""
    forbidden = ('puede rechazar', 'no cumple con los requisitos', 'no tiene el derecho',
                 'justificacion valida', 'debe justificar', 'falta de justificacion')
    parts = re.split(r'(?<=[.!?])\s+', answer)
    kept, removed = [], False
    for part in parts:
        plain = _plain(part)
        if any(term in plain for term in forbidden) and not re.search(r'\[\d+\]', part):
            removed = True
        else:
            kept.append(part)
    return ' '.join(kept).strip(), removed


def analyze(payload):
    payload = require_json(payload)
    try:
        case = validar_consulta(payload.get('case'), 12)
    except ValueError as exc:
        raise ValidationError(str(exc).replace('query', 'case')) from exc
    history = _history(payload.get('history'))
    try:
        retrieval_query, followup = _retrieval_query(case, history)
        evidence = _evidence(buscar_pii_vectorial(retrieval_query, 12))
    except SearchUnavailable as exc:
        raise ApiError(str(exc), code='case_analysis_unavailable', status_code=503) from exc
    except Exception as exc:
        raise ApiError('No se pudo analizar el caso.', code='case_analysis_failed', status_code=500) from exc

    if not evidence:
        generated = _fallback([], 'No existe evidencia recuperada para fundamentar una conclusión.')
    else:
        try:
            generated = llm_service.generate(_messages(
                case, history if followup else [], evidence, followup=followup))
            generated['answer'], removed = _remove_unsupported_rejections(generated['answer'])
            if removed:
                generated['limitations'].append(
                    'Se omitió una posible causal de rechazo porque el modelo no aportó una cita directa.')
            allowed = {row['id'] for row in evidence}
            cited = generated['citations']
            mentioned = {int(value) for value in re.findall(r'\[(\d+)\]', generated['answer'])}
            if not set(cited).issubset(allowed):
                raise llm_service.LLMInvalid('La respuesta no contiene citas válidas.')
            if not cited:
                cited = [row['id'] for row in evidence
                         if row['source_type'] in ('normative', 'institutional')][:3]
                generated['citations'] = cited
            missing = [item for item in cited if item not in mentioned]
            if missing:
                generated['answer'] += '\n\nFuentes utilizadas: ' + ', '.join(f'[{item}]' for item in missing) + '.'
            generated['limitations'] = list(dict.fromkeys(generated['limitations'])) or [
                'La conclusión depende de fragmentos recuperados; verifica los documentos completos y su vigencia.'
            ]
            generated.update({'coverage': 'evidence_found', 'mode': 'generative_rag'})
        except (llm_service.LLMUnavailable, llm_service.LLMInvalid) as exc:
            generated = _fallback(evidence, str(exc))

    audit_service.record('CASE_ANALYSIS', entity_type='document', detail={
        'count': len(evidence), 'mode': generated['mode'], 'model': generated.get('model')})
    return {**generated, 'evidence': evidence,
            'notice': ('Análisis académico preliminar basado únicamente en documentos locales. '
                       'Verifica la fuente completa, su fidelidad y vigencia antes de decidir.')}
