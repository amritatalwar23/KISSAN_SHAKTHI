"""Tests for Government Schemes and Subsidies Module."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_schemes_all():
    response = client.post("/recommend/scheme", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 5
    assert "disclaimer" in data
    # Check that PM-KISAN exists
    scheme_names = [s["name"] for s in data["schemes"]]
    assert any("PM-KISAN" in name or "Kisan Samman" in name for name in scheme_names)

def test_schemes_state_filter():
    response = client.post("/recommend/scheme", json={"state": "Karnataka"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    # Check for Karnataka scheme (e.g. Raitha Siri) or central schemes
    names = [s["name"] for s in data["schemes"]]
    assert any("Raitha Siri" in name for name in names)

def test_schemes_keyword_search():
    response = client.post("/recommend/scheme", json={"keyword": "insurance"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_found"] >= 1
    assert any("Fasal Bima" in s["name"] or "PMFBY" in s["name"] for s in data["schemes"])
