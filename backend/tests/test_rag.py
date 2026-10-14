"""Tests for Agricultural Knowledge Base (RAG) Module."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_rag_query_with_evidence():
    response = client.post("/rag/query", json={"question": "How to control tomato early blight and late blight?"})
    assert response.status_code == 200
    data = response.json()
    assert data["sufficient_evidence"] is True
    assert "retrieved_chunks" in data
    assert len(data["retrieved_chunks"]) >= 1
    assert "sources" in data
    assert any("IIHR" in src or "ICAR" in src for src in data["sources"])

def test_rag_query_no_evidence_fallback():
    response = client.post("/rag/query", json={"question": "What is the quantum mechanics equation for supercomputers?"})
    assert response.status_code == 200
    data = response.json()
    assert data["sufficient_evidence"] is False
    assert "could not verify" in data["grounded_answer"].lower()
