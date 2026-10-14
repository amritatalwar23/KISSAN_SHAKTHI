"""Tests for Crop Disease Detection Module."""
import io
import pytest
from PIL import Image, ImageDraw
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.services.disease_service import disease_service

client = TestClient(app)

def create_dummy_leaf_image(color=(34, 139, 34), add_spots=True, size=(224, 224)) -> bytes:
    """Generates synthetic RGB image with variance mimicking a leaf with spots."""
    img = Image.new("RGB", size, color=color)
    draw = ImageDraw.Draw(img)
    if add_spots:
        # Draw contrasting spot to ensure non-zero variance
        draw.ellipse([50, 50, 100, 100], fill=(139, 69, 19))
        draw.ellipse([120, 120, 180, 180], fill=(255, 215, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_disease_prediction_valid_image():
    img_bytes = create_dummy_leaf_image()
    response = client.post(
        "/predict/disease",
        files={"file": ("leaf_test.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "crop_name" in data
    assert "disease_name" in data
    assert "confidence" in data
    assert "status" in data
    assert data["status"] in ["confident", "uncertain"]
    assert "advisory" in data
    assert len(data["advisory"]) > 10
    assert "top_alternatives" in data
    assert "source_references" in data
    assert len(data["source_references"]) >= 1

def test_disease_prediction_monochromatic_rejection():
    """Checks out-of-distribution safeguard: flat solid color images should be rejected."""
    flat_img = Image.new("RGB", (224, 224), color=(0, 0, 0))
    buf = io.BytesIO()
    flat_img.save(buf, format="JPEG")
    
    response = client.post(
        "/predict/disease",
        files={"file": ("blank.jpg", buf.getvalue(), "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert "blank" in data["warning"].lower() or "monochromatic" in data["warning"].lower()

def test_disease_prediction_invalid_format():
    """Unsupported content types must return HTTP 415."""
    response = client.post(
        "/predict/disease",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 415

def test_disease_prediction_empty_file():
    """Empty files must be safely rejected."""
    result = disease_service.predict(b"", filename="empty.jpg")
    assert result["status"] == "rejected"
    assert "empty" in result["warning"].lower()
