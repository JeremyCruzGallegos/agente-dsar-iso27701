from dsar_api.models import LegalProvision, LegalSource
from dsar_api.services.legal_search import buscar_normativa, estado_corpus
from tests.conftest import DPO, SERVICE


SOURCE = {
    "code": "NORMA-TEST", "title": "Norma de prueba", "source_type": "law",
    "issuing_body": "Autoridad de prueba", "jurisdiction": "Perú",
    "official_url": "https://example.test/norma", "status": "active",
}


def test_knowledge_requires_dpo_for_writes(client):
    assert client.post("/api/knowledge/sources", json=SOURCE).status_code == 401
    assert client.post("/api/knowledge/sources", json=SOURCE, headers=SERVICE).status_code == 403


def test_create_source_provision_and_search_database(client, app):
    response = client.post("/api/knowledge/sources", json=SOURCE, headers=DPO)
    assert response.status_code == 201
    source_id = response.json["data"]["id"]
    provision = {
        "provision_code": "Artículo 1", "heading": "Derecho de acceso",
        "content": "El titular puede solicitar acceso a sus datos personales.",
        "topic": "derechos del titular", "right_type": "access",
        "keywords": "acceso información solicitud", "verified": True,
    }
    response = client.post(
        f"/api/knowledge/sources/{source_id}/provisions", json=provision, headers=DPO
    )
    assert response.status_code == 201
    with app.app_context():
        results = buscar_normativa("solicitud de derecho de acceso", 5)
        assert len(results) == 1
        assert results[0]["provision_id"] == response.json["data"]["id"]
        assert estado_corpus()["ready"] is True


def test_unverified_and_inactive_provisions_are_excluded(client, app):
    source_id = client.post("/api/knowledge/sources", json=SOURCE, headers=DPO).json["data"]["id"]
    created = client.post(f"/api/knowledge/sources/{source_id}/provisions", json={
        "provision_code": "1", "content": "Acceso a información", "verified": False,
    }, headers=DPO).json["data"]
    with app.app_context():
        assert buscar_normativa("acceso información", 5) == []
        assert estado_corpus()["ready"] is False
    response = client.patch(f"/api/knowledge/provisions/{created['id']}",
                            json={"verified": True}, headers=DPO)
    assert response.status_code == 200
    with app.app_context():
        assert len(buscar_normativa("acceso información", 5)) == 1


def test_source_code_and_provision_code_are_unique(client):
    first = client.post("/api/knowledge/sources", json=SOURCE, headers=DPO)
    assert client.post("/api/knowledge/sources", json=SOURCE, headers=DPO).status_code == 409
    source_id = first.json["data"]["id"]
    body = {"provision_code": "Art. 1", "content": "Texto suficiente", "verified": True}
    assert client.post(f"/api/knowledge/sources/{source_id}/provisions", json=body, headers=DPO).status_code == 201
    assert client.post(f"/api/knowledge/sources/{source_id}/provisions", json=body, headers=DPO).status_code == 409
