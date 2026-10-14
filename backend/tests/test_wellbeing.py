"""Tests for Farmer Wellbeing and Crisis Support Module."""
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_wellbeing_normal_query():
    response = client.post("/wellbeing", json={"message": "What is the best fertilizer for tomato plants?"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis_detected"] is False
    assert data["urgency_level"] == "normal"

def test_wellbeing_acute_crisis_english():
    response = client.post("/wellbeing", json={"message": "I lost everything to the flood and I want to kill myself."})
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis_detected"] is True
    assert data["urgency_level"] == "immediate_crisis"
    assert len(data["helplines"]) >= 2
    # Verify Tele-MANAS (14416) is provided
    numbers = [h["number"] for h in data["helplines"]]
    assert any("14416" in num for num in numbers)

def test_wellbeing_acute_crisis_kannada():
    response = client.post("/wellbeing", json={"message": "ಬೆಳೆ ನಾಶವಾಯಿತು, ನನಗೆ ಆತ್ಮಹತ್ಯೆ ಮಾಡಿಕೊಳ್ಳುವ ಯೋಚನೆ ಬರುತ್ತಿದೆ"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis_detected"] is True
    assert data["urgency_level"] == "immediate_crisis"

def test_wellbeing_elevated_debt_distress():
    response = client.post("/wellbeing", json={"message": "I am under severe loan burden and heavy debt after crop failure."})
    assert response.status_code == 200
    data = response.json()
    assert data["is_crisis_detected"] is True
    assert data["urgency_level"] in ["elevated", "immediate_crisis"]
