import pytest

from dsar_api.models import LegalProvision
from dsar_api.services.pims_import import import_pims
from tests.conftest import DPO


def test_import_repeatedly_preserves_provision_ids(app):
    with app.app_context():
        counts = import_pims()
        ids = [r.id for r in LegalProvision.query.order_by(LegalProvision.id)]
        assert counts[0] == 11
        assert counts[1] == len(ids)
        assert import_pims() == counts
        assert [r.id for r in LegalProvision.query.order_by(LegalProvision.id)] == ids


@pytest.mark.parametrize('scope,query,code,section', [
    ('pims', 'Identidad ya verificada. Para rectificar la fecha de nacimiento en matrícula, ¿a quién se deriva?', 'D20', '3'),
    ('pims', 'Falta acreditación de identidad, ¿cómo procede recepción?', 'D20', '2'),
    ('registros', 'Actuaciones del expediente SIM-001 por rectificación de matrícula', 'SIM-001', '1'),
])
def test_queries_reference_correct_document_and_section(app, client, scope, query, code, section):
    with app.app_context():
        import_pims()
    data = client.post('/api/case-analysis', headers=DPO, json={'case': query, 'scope': scope}).json['data']
    first = data['evidence'][0]
    assert first['source'].startswith('PIMS-SIM-' + code + ' —')
    assert first['section'].startswith(section + ' —')
    assert data['mode'] == 'retrieval_only'
    assert data['citations'] == [first['id']]
    assert 'v0.1' in first['source']


def test_scopes_and_insufficient_evidence(app, client):
    with app.app_context():
        import_pims()
    for scope, query in [('pims', '¿Cuántos satélites orbitan Júpiter?'), ('normativa', 'rectificación de matrícula')]:
        data = client.post('/api/case-analysis', json={'scope': scope, 'case': query}, headers=DPO).json['data']
        assert data['coverage'] == 'insufficient_evidence'
        assert data['evidence'] == []
    wrong = client.post('/api/case-analysis', json={'scope': 'xxx', 'case': 'matrícula'}, headers=DPO)
    assert wrong.status_code == 422
