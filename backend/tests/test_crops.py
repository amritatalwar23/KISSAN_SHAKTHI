"""Tests for Smart Crop Planning Module."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_crop_planning_recommendation():
    payload = {
        "state": "Karnataka",
        "district": "Dharwad",
        "season": "Kharif",
        "soil_type": "Red sandy loam",
        "water_availability": "Moderate",
        "land_size_acres": 2.5
    }
    response = client.post("/recommend/crop", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    top_rec = data["recommendations"][0]
    assert "crop_name" in top_rec
    assert "suitability_score" in top_rec
    assert top_rec["suitability_score"] >= 0.60
    assert "rationale" in top_rec
    assert "key_risks_and_cautions" in top_rec
    assert "assumptions" in data
    assert "cautions" in data
    assert "disclaimer" in data

def test_crop_planning_missing_inputs_handling():
    payload = {
        "state": "Karnataka",
        "season": "Rabi",
        "soil_type": "Black cotton soil",
        "water_availability": "Low"
    }
    response = client.post("/recommend/crop", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["assumptions"]) >= 1
