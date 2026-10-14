"""Test system health and startup."""
import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Kisan Shakti"
    assert "modules_loaded" in data
    assert data["modules_loaded"]["disease_detection"] is True
    assert data["modules_loaded"]["government_schemes"] is True
    assert data["modules_loaded"]["crop_planning"] is True
    assert data["modules_loaded"]["expert_directory"] is True
    assert data["modules_loaded"]["wellbeing_crisis_support"] is True
