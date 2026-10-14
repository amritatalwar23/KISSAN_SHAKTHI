"""Tests for Multilingual Assistance Module."""
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.services.multilingual_service import multilingual_service

client = TestClient(app)

def test_language_detection():
    assert multilingual_service.detect_language("How are my tomato crops doing?") == "en"
    assert multilingual_service.detect_language("ಟೊಮೆಟೊ ಬೆಳೆಗೆ ಯಾವ ಗೊಬ್ಬರ ಹಾಕಬೇಕು?") == "kn"
    assert multilingual_service.detect_language("आलू की फसल में कौन सी खाद डालें?") == "hi"

def test_translation_endpoint_kannada():
    response = client.post("/translate", json={"text": "Tomato Early Blight", "target_lang": "kn"})
    assert response.status_code == 200
    data = response.json()
    assert data["target_lang"] == "kn"
    assert "ಟೊಮೆಟೊ" in data["translated_text"]

def test_translation_endpoint_hindi():
    response = client.post("/translate", json={"text": "Potato Late Blight", "target_lang": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert data["target_lang"] == "hi"
    assert "आलू" in data["translated_text"]

def test_unsupported_language_fallback():
    response = client.post("/translate", json={"text": "Hello farmer", "target_lang": "fr"})
    assert response.status_code == 200
    data = response.json()
    assert data["target_lang"] == "en"
