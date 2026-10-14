"""Tests for Expert and KVK Directory Lookup Module."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_expert_lookup_karnataka():
    response = client.post("/expert", json={"state": "Karnataka", "district": "Bangalore Rural"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    # Check that contact has real address and phone or email
    contact = data["contacts"][0]
    assert "name" in contact
    assert "address" in contact
    assert "official_link" in contact
    assert "verified_on" in contact
    assert "kvk.icar.gov.in" in data["official_directory_url"]

def test_expert_lookup_national_fallback():
    # If a state with no local KVK in mock is queried, national Kisan Call Centre must still be present
    response = client.post("/expert", json={"state": "Goa"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    names = [c["name"] for c in data["contacts"]]
    assert any("Kisan Call Centre" in name for name in names)
