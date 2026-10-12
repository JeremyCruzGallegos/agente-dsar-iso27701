from unittest.mock import patch

import pytest

from ai_engine.search_engine import SearchUnavailable
from dsar_api.models import AuditLog
from tests.conftest import SERVICE

SERVICE_SEARCH = 'dsar_api.services.search_engine.buscar_pii_vectorial'


def test_search_is_authenticated(client):
    assert client.post('/api/vector-search', json={'query': 'datos'}).status_code == 401


@pytest.mark.parametrize('body', [[], {}, {'query': ' '}, {'query': 'x' * 4001},
                                 {'query': 'datos', 'k': True}, {'query': 'datos', 'k': 0},
                                 {'query': 'datos', 'k': 51}, {'query': 'datos', 'k': '5'}])
def test_invalid_search_does_not_load_model(client, body):
    with patch(SERVICE_SEARCH) as search:
        response = client.post('/api/vector-search', json=body, headers=SERVICE)
        assert response.status_code == 422
        search.assert_not_called()


def test_search_requires_valid_json(client):
    assert client.post('/api/vector-search', data='texto', headers=SERVICE).status_code == 415
    response = client.post('/api/vector-search', data='{', content_type='application/json', headers=SERVICE)
    assert response.status_code == 400
    assert response.json['status'] == 'error'


def test_search_returns_results_and_audits_without_query(client, app):
    results = [{'texto': 'Texto sintético', 'fuente': 'demo.txt', 'score': 0.75}]
    with patch(SERVICE_SEARCH, return_value=results) as search:
        response = client.post('/api/vector-search', json={'query': ' consulta privada ', 'k': 3}, headers=SERVICE)
        search.assert_called_once_with('consulta privada', 3)
    assert response.status_code == 200
    assert response.json['data'] == {'results': results, 'count': 1, 'metric': 'cosine_similarity'}
    with app.app_context():
        entry = AuditLog.query.filter_by(action='VECTOR_SEARCH').one()
        assert 'consulta privada' not in entry.detail
        assert 'Texto sintético' not in entry.detail


def test_search_unavailable_and_internal_errors(client):
    for exception, status in [(SearchUnavailable('Prepara el índice'), 503),
                              (RuntimeError('PII que no debe aparecer'), 500)]:
        with patch(SERVICE_SEARCH, side_effect=exception):
            response = client.post('/api/vector-search', json={'query': 'datos'}, headers=SERVICE)
        assert response.status_code == status
        assert response.json['status'] == 'error'
        assert 'PII que no debe aparecer' not in response.get_data(as_text=True)


def test_portal_assets_and_vector_cors(client):
    assert client.get('/').status_code == 200
    assert client.get('/static/main.js').status_code == 200
    assert client.get('/static/styles.css').status_code == 200
    assert client.get('/dpo').status_code == 200
    response = client.options('/api/vector-search', headers={
        'Origin': 'http://localhost:5000', 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type,X-API-Key',
    })
    assert response.headers['Access-Control-Allow-Origin'] == 'http://localhost:5000'
