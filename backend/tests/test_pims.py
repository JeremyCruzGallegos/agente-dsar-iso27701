import shutil

import pytest
from docx import Document
from dsar_api.extensions import db
from dsar_api.models import LegalSource
from dsar_api.services import pims_import, llm_service

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


def ask(client, query, scope='pims'):
    response = client.post('/api/case-analysis', headers=DPO, json={'case': query, 'scope': scope})
    assert response.status_code == 200
    return response.json['data']


@pytest.mark.parametrize('code,reference', [('D30', '7.2, 7.3 y A.3.17'), ('D11', '7.5.1–7.5.3'), ('D34', '10.2')])
def test_course_reference_and_origin(app, client, code, reference):
    with app.app_context():
        assert import_pims() == (11, 45)
    data = ask(client, f'¿Qué cláusulas o controles cita el documento {code}?')
    assert reference in data['answer'] and 'guía del curso' in data['answer']
    item = data['evidence'][0]
    assert item['origin']['file'] == f'plantillas/{code}.docx'
    assert item['origin']['locator'] == 'Antes del primer apartado'


def test_table_edit_and_atomic_reimport(app, client, monkeypatch, tmp_path):
    directory = tmp_path / 'pims'
    shutil.copytree(pims_import.DIRECTORY, directory)
    monkeypatch.setattr(pims_import, 'DIRECTORY', directory)
    path = directory / 'plantillas/D30.docx'
    doc = Document(path)
    doc.tables[0].cell(1, 1).text = 'Indicador centinela azul'
    doc.save(path)
    with app.app_context():
        db.session.add(LegalSource(code='EXTERNA', title='Historia', source_type='guidance',
                                  issuing_body='Otro grupo', status='active'))
        db.session.commit()
        import_pims()
        (directory / 'D20.md').unlink()
        doc.tables[0].cell(1, 1).text = 'Cambio que debe revertirse'
        doc.save(path)
        with pytest.raises(FileNotFoundError):
            import_pims()
        assert LegalSource.query.filter_by(code='EXTERNA').one().status == 'active'
    data = ask(client, 'D30 indicador centinela azul')
    assert 'Criterio de seguimiento: Indicador centinela azul' in data['answer']
    assert data['evidence'][0]['origin']['locator'].startswith('3.')


def test_matrix_comparison_reads_current_rows(app, client):
    with app.app_context():
        import_pims()
    for order in [('R01', 'R02', 'R03'), ('R03', 'R01', 'R02')]:
        data = ask(client, 'Contrasta los índices iniciales y residuales de ' + ', '.join(order), 'registros')
        lines = data['answer'].splitlines()[1:4]
        assert [line.split(' | ')[0] for line in lines] == list(order)
        import re
        expected = {'R01': ('6','4'), 'R02': ('5','3'), 'R03': ('4','3')}
        for risk, line in zip(order, lines):
            assert tuple(re.findall(r'\| (\d+) \[', line)) == expected[risk]
            refs = [int(n) for n in re.findall(r'\[(\d+)\]', line)]
            assert {data['evidence'][i-1]['origin']['file'] for i in refs} == {
                'plantillas/D13.xlsx', 'plantillas/D15-MAT.xlsx'}
            assert 'Pendiente del propietario' in line
    with app.app_context():
        row = LegalProvision.query.join(LegalSource).filter(
            LegalSource.code == 'PIMS-SIM-D13', LegalProvision.provision_code == 'R02').one()
        row.content = row.content.replace('Índice inicial: 5','Índice inicial: 9')
        db.session.commit()
    data = ask(client, 'Compara R02 con R77', 'registros')
    assert 'R02 | 9 [' in data['answer'] and 'R77 | Sin dato' in data['answer']
    assert data['coverage'] == 'partial'


@pytest.mark.parametrize('question', ['¿Cuál es el plazo legal exacto en días hábiles para rectificar matrícula?',
                                      '¿Cuántos días hábiles tengo para la rectificación en D20?'])
def test_missing_legal_duration(app, client, question):
    with app.app_context():
        import_pims()
    data = ask(client, question)
    assert data['coverage'] == 'partial' and 'no especifican el plazo legal' in data['answer']
    assert '30 días' not in data['answer']


def test_model_can_select_two_sections(app, client, monkeypatch):
    with app.app_context():
        import_pims()
    def choose(question, passages):
        ids = [next(k for k,v in passages.items() if f'§{section} —' in v) for section in ('2','3')]
        return ids, 'modelo-de-prueba'
    monkeypatch.setattr(llm_service, 'select_passages', choose)
    data = ask(client, 'D20: acreditación de identidad pendiente y derivación para rectificación de fecha de nacimiento')
    assert data['mode'] == 'document_selection' and len(set(data['citations'])) == 2
