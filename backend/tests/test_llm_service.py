from unittest.mock import patch

import pytest

from dsar_api.services import llm_service


def test_plain_ollama_response_extracts_citations(app):
    app.config['OLLAMA_MODEL'] = 'modelo-prueba'
    raw = {'model': 'modelo-prueba', 'message': {'content': 'Conclusión fundada [1] y [3].'}}
    with app.app_context(), patch.object(llm_service, '_request', return_value=raw) as request:
        result = llm_service.generate([{'role': 'user', 'content': 'caso'}])
    assert result['answer'] == 'Conclusión fundada [1] y [3].'
    assert result['citations'] == [1, 3]
    payload = request.call_args.args[1]
    assert 'format' not in payload
    assert payload['stream'] is False
    assert payload['options']['temperature'] == 0
    assert payload['options']['num_predict'] == 650
    assert payload['keep_alive'] == '2m'


def test_empty_response_is_rejected(app):
    app.config['OLLAMA_MODEL'] = 'modelo-prueba'
    raw = {'message': {'content': '   '}}
    with app.app_context(), patch.object(llm_service, '_request', return_value=raw):
        with pytest.raises(llm_service.LLMInvalid):
            llm_service.generate([])
