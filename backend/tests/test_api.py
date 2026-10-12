from datetime import date, timedelta

import pytest

from dsar_api.extensions import db
from dsar_api.models import AuditLog, DataSubject
from tests.conftest import DPO, SERVICE


# ---------- Seguridad ----------
def test_health_is_public(client):
    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "mala"}])
def test_endpoints_require_valid_key(client, headers):
    assert client.get("/api/user-data?user_id=72839102", headers=headers).status_code == 401
    assert client.get("/api/audit-log", headers=headers).status_code == 401


def test_audit_log_is_dpo_only(client):
    assert client.get("/api/audit-log", headers=SERVICE).status_code == 403
    assert client.get("/api/audit-log", headers=DPO).status_code == 200


def test_missing_server_keys_deny_everything(app, client):
    app.config["SERVICE_API_KEY"] = ""
    app.config["DPO_API_KEY"] = ""
    assert client.get("/api/user-data?user_id=72839102", headers={"X-API-Key": ""}).status_code == 401


# ---------- Acceso / Portabilidad ----------
def test_user_data_access(client, seeded):
    r = client.get(f"/api/user-data?user_id={seeded}", headers=SERVICE)
    body = r.get_json()
    assert r.status_code == 200 and body["status"] == "success"
    assert body["data"]["nombre"] == "Juan Pérez" and body["data"]["activo"] is True


def test_user_data_portable_format(client, seeded):
    r = client.get(f"/api/user-data?user_id={seeded}&format=portable", headers=SERVICE)
    assert r.get_json()["data"]["format"] == "portable-json"


def test_user_data_not_found_and_invalid(client):
    assert client.get("/api/user-data?user_id=99999999", headers=SERVICE).status_code == 404
    assert client.get("/api/user-data?user_id=%27%3B--", headers=SERVICE).status_code == 422


# ---------- Rectificación ----------
def test_rectify_updates_allowed_fields_only(client, seeded):
    r = client.patch("/api/rectify-user", json={"user_id": seeded, "changes": {"nombre": "Juan P. Soto"}},
                     headers=SERVICE)
    assert r.status_code == 200 and r.get_json()["data"]["nombre"] == "Juan P. Soto"
    bad = client.patch("/api/rectify-user", json={"user_id": seeded, "changes": {"active": False}}, headers=SERVICE)
    assert bad.status_code == 422


# ---------- Supresión y criterios de retención ----------
def test_erase_anonymizes_subject_and_requests(client, app, seeded):
    ticket = client.post("/api/requests", json={
        "user_id": seeded, "email": "juan@email.com", "request_type": "Supresion", "details": "borrar todo"},
        headers=SERVICE).get_json()["data"]["ticket_id"]
    r = client.post("/api/delete-user", json={"user_id": seeded, "ticket_id": ticket}, headers=SERVICE)
    assert r.status_code == 200
    with app.app_context():
        s = DataSubject.query.one()
        assert s.full_name is None and s.email is None and s.active is False and s.is_anonymized
        assert s.requests.one().email == "anonimizado@invalid" and s.requests.one().details is None
    # el titular original ya no es localizable
    assert client.get(f"/api/user-data?user_id={seeded}", headers=SERVICE).status_code == 404


def test_erase_blocked_by_retention(client, app, seeded):
    with app.app_context():
        s = DataSubject.query.one()
        s.retention_until = date.today() + timedelta(days=30)
        db.session.commit()
    r = client.post("/api/delete-user", json={"user_id": seeded}, headers=SERVICE)
    assert r.status_code == 409 and r.get_json()["error"]["code"] == "retention_blocked"
    with app.app_context():
        assert DataSubject.query.one().full_name == "Juan Pérez"


def test_erase_blocked_by_legal_hold(client, app, seeded):
    with app.app_context():
        s = DataSubject.query.one()
        s.legal_hold, s.legal_hold_reason = True, "Litigio en curso"
        db.session.commit()
    r = client.post("/api/delete-user", json={"user_id": seeded}, headers=SERVICE)
    assert r.status_code == 409 and "Litigio" in r.get_json()["error"]["message"]


# ---------- Solicitudes y SLA ----------
def test_create_request_returns_ticket_and_sla(client, seeded):
    r = client.post("/api/requests", json={
        "user_id": seeded, "email": "Juan@Email.com", "request_type": "Acceso"}, headers=SERVICE)
    data = r.get_json()["data"]
    assert r.status_code == 201 and data["ticket_id"].startswith("DSAR-")
    assert data["status"] == "Recibido" and data["sla_days_remaining"] in (29, 30)


def test_create_request_validation(client):
    base = {"user_id": "72839102", "email": "a@b.com", "request_type": "Acceso"}
    for patch in ({"request_type": "Hackeo"}, {"email": "no-es-correo"}, {"user_id": ""}):
        r = client.post("/api/requests", json={**base, **patch}, headers=SERVICE)
        assert r.status_code == 422, patch
    assert client.post("/api/requests", data="no json", headers=SERVICE).status_code == 422


def test_status_transitions(client, seeded):
    t = client.post("/api/requests", json={"user_id": seeded, "email": "a@b.com", "request_type": "Acceso"},
                    headers=SERVICE).get_json()["data"]["ticket_id"]
    url = f"/api/requests/{t}/status"
    assert client.patch(url, json={"status": "Completado"}, headers=SERVICE).status_code == 409  # salto inválido
    assert client.patch(url, json={"status": "En proceso"}, headers=SERVICE).status_code == 200
    done = client.patch(url, json={"status": "Completado", "resolution_note": "Enviado"}, headers=SERVICE)
    assert done.get_json()["data"]["sla_days_remaining"] is None
    assert client.patch(url, json={"status": "En proceso"}, headers=SERVICE).status_code == 409  # ya cerrada


def test_list_requests_filters_and_pagination(client, seeded):
    for rt in ("Acceso", "Supresion", "Acceso"):
        client.post("/api/requests", json={"user_id": seeded, "email": "a@b.com", "request_type": rt},
                    headers=SERVICE)
    r = client.get("/api/requests?request_type=Acceso&limit=1", headers=DPO).get_json()
    assert r["total"] == 2 and len(r["data"]) == 1
    assert client.get("/api/requests?limit=0", headers=DPO).status_code == 422


# ---------- Auditoría ----------
def test_audit_trail_records_events_without_plain_pii(client, app, seeded):
    client.get(f"/api/user-data?user_id={seeded}", headers=SERVICE)
    client.get("/api/user-data?user_id=00000000", headers=SERVICE)  # denegado/no encontrado
    rows = client.get(f"/api/audit-log?user_id={seeded}", headers=DPO).get_json()["data"]
    assert {"SUBJECT_CREATED", "USER_DATA_ACCESS"} <= {r["action"] for r in rows}
    assert all(seeded not in str(r) for r in rows)  # el documento no aparece en claro
    denied = client.get("/api/audit-log?outcome=denied", headers=DPO).get_json()["data"]
    assert denied and denied[0]["action"] == "SUBJECT_LOOKUP"


def test_audit_log_is_immutable(app, client, seeded):
    with app.app_context():
        entry = AuditLog.query.first()
        entry.action = "MANIPULADO"
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()
        with pytest.raises(Exception):
            db.session.delete(AuditLog.query.first())
            db.session.commit()
        db.session.rollback()


def test_unknown_route_returns_json_404(client):
    r = client.get("/api/nada")
    assert r.status_code == 404 and r.get_json()["status"] == "error"
