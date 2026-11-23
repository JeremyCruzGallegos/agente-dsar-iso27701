from io import BytesIO
from uuid import uuid4

from pypdf import PdfReader
from sqlalchemy import inspect

from dsar_api.extensions import db
from dsar_api.models import DsarRequest
from tests.conftest import DPO


def test_oposicion_preserves_subject_and_prior_tickets(app, client, seeded):
    def submit(kind):
        response = client.post('/api/intake', headers={'Idempotency-Key': uuid4().hex}, json={'user_id': seeded, 'email': 'ensayo@example.invalid',
                               'request_type': kind, 'details': 'Ensayo de matrícula'})
        assert response.status_code == 201
        return response.json['ticket_id']

    earlier = submit('Acceso')
    with app.app_context():
        # El esquema previo persiste los nombres de enum en VARCHAR sin CHECK de tipo.
        assert not inspect(db.engine).get_check_constraints('dsar_requests')
        assert DsarRequest.query.filter_by(ticket_id=earlier).one().request_type.name == 'ACCESO'
        db.create_all()
    ticket = submit('Oposicion')
    route = '/api/requests/' + ticket
    data = client.get(route, headers=DPO).json['data']
    assert data['status'] == 'Recibido' and data['request_type_label'] == 'Oposición'
    assert client.get('/api/requests?request_type=Oposicion', headers=DPO).json['total'] == 1
    assert client.get('/api/requests/' + earlier, headers=DPO).json['data']['request_type'] == 'Acceso'
    for status in ['En verificacion', 'En proceso']:
        assert client.patch(route+'/status', headers=DPO, json={'status': status}).status_code == 200
    assert client.patch(route+'/status', headers=DPO, json={'status': 'Completado'}).status_code == 422
    note = 'D20 §7. Ensayo: se admite la oposición en el tratamiento identificado.'
    response = client.patch(route+'/status', headers=DPO, json={'status':'Completado','resolution_note':note})
    assert response.json['data']['resolution_note'] == note
    log = client.get('/api/audit-log', query_string={'ticket_id':ticket}, headers=DPO).json['data']
    assert sorted(e['action'] for e in log) == ['REQUEST_CREATED'] + ['REQUEST_STATUS_CHANGE'] * 3
    report = client.get(route+'/report.pdf', headers=DPO)
    pdf = PdfReader(BytesIO(report.data)).pages[0].extract_text()
    assert 'Oposición' in pdf and 'Completado' in pdf and ticket in pdf
    assert client.get('/api/user-data', query_string={'user_id':seeded}, headers=DPO).json['data']['activo']
