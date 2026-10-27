from unittest.mock import patch

from tests.conftest import DPO


SEARCH = 'dsar_api.services.case_service.buscar_pii_vectorial'


def test_case_analysis_requires_authentication(client):
    assert client.post('/api/case-analysis', json={'case': 'caso válido'}).status_code == 401


def test_case_analysis_returns_traceable_evidence(client):
    matches = [{'texto': 'La persona puede solicitar acceso.', 'fuente': 'estatuto.md',
                'seccion': 'Derecho de acceso', 'score': .82}]
    with patch(SEARCH, return_value=matches):
        response = client.post('/api/case-analysis', json={'case': ' acceso del estudiante '}, headers=DPO)
    assert response.status_code == 200
    data = response.json['data']
    assert data['coverage'] == 'evidence_found'
    assert data['evidence'][0]['section'] == 'Derecho de acceso'
    assert '[1]' in data['answer']


def test_case_analysis_does_not_invent_when_empty(client):
    with patch(SEARCH, return_value=[]):
        response = client.post('/api/case-analysis', json={'case': 'caso sin norma'}, headers=DPO)
    assert response.json['data']['coverage'] == 'insufficient_evidence'
    assert response.json['data']['evidence'] == []


def test_agent_page_is_available(client):
    assert client.get('/agente').status_code == 200
