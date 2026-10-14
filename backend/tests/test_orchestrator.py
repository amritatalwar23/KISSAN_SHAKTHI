"""Tests for Central AI Orchestrator."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_orchestrator_routes_to_schemes():
    response = client.post("/query", json={"query": "Tell me about PM-KISAN subsidy and loan benefits"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_module"] == "schemes"
    assert "PM-KISAN" in data["answer"] or "scheme" in data["answer"].lower()

def test_orchestrator_routes_to_crops():
    response = client.post("/query", json={"query": "Which crop should I grow in Kharif season?"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_module"] == "crop_planning"
    assert "suitable crops" in data["answer"].lower() or "recommend" in data["answer"].lower()

def test_orchestrator_routes_to_experts():
    response = client.post("/query", json={"query": "Where is the nearest Krishi Vigyan Kendra KVK contact?"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_module"] == "experts"
    assert "KVK" in data["answer"] or "1800-180-1551" in data["answer"]

def test_orchestrator_routes_to_wellbeing_priority():
    response = client.post("/query", json={"query": "I am having suicidal thoughts after losing my farm"})
    assert response.status_code == 200
    data = response.json()
    assert data["routed_module"] == "wellbeing"
    assert "14416" in data["warning"] or any("14416" in h["number"] for h in data["structured_data"]["helplines"])
