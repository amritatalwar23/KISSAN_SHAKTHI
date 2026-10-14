"""Crop Disease Detection Service.

Provides image validation, preprocessing, MobileNetV3 transfer learning inference,
uncertainty thresholding, out-of-distribution safeguards, and grounded ICAR advisory retrieval.
"""

import io
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, UnidentifiedImageError
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

from backend.app.core.config import settings, BASE_DIR
from backend.app.core.logging import logger
from backend.app.database.db import log_disease_prediction


class DiseaseService:
    def __init__(self):
        self.class_map_path = Path(settings.DISEASE_CLASS_MAP)
        self.metadata_path = Path(settings.DISEASE_METADATA)
        self.model_path = Path(settings.DISEASE_MODEL_PATH)
        self.confidence_threshold = getattr(settings, "CONFIDENCE_THRESHOLD", 0.60)
        self.classes: List[Dict[str, Any]] = []
        self.raw_to_info: Dict[str, Dict[str, Any]] = {}
        self.id_to_info: Dict[int, Dict[str, Any]] = {}
        self.model: Optional[nn.Module] = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_model_trained = False

        self._load_class_mapping()
        self._load_metadata()
        self._init_transforms()
        self._load_or_init_model()

    def _load_class_mapping(self):
        """Loads the 17-class PlantVillage mapping for Tomato, Potato, and Corn."""
        if self.class_map_path.exists():
            try:
                with open(self.class_map_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.classes = data.get("classes", [])
                    for item in self.classes:
                        self.raw_to_info[item["raw_class"]] = item
                        self.id_to_info[item["id"]] = item
                logger.info(f"Loaded {len(self.classes)} disease classes successfully.")
            except Exception as e:
                logger.error(f"Error loading disease class mapping: {e}")
        else:
            logger.warning(f"Class mapping file not found at {self.class_map_path}")

    def _load_metadata(self):
        """Loads model metadata."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                logger.error(f"Error loading model metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}

    def _init_transforms(self):
        """Defines standard PyTorch validation transforms matching MobileNetV3 requirements."""
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def _load_or_init_model(self):
        """Loads trained weights if available, or initializes MobileNetV3 architecture."""
        num_classes = len(self.classes) if self.classes else 17
        try:
            # Initialize MobileNetV3 Small architecture
            self.model = models.mobilenet_v3_small(weights=None)
            in_features = self.model.classifier[3].in_features
            self.model.classifier[3] = nn.Linear(in_features, num_classes)

            if self.model_path.exists():
                logger.info(f"Loading trained weights from {self.model_path}")
                checkpoint = torch.load(self.model_path, map_location=self.device)
                if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["state_dict"])
                elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self.model.load_state_dict(checkpoint)
                self.is_model_trained = True
                logger.info("Trained model checkpoint loaded successfully.")
            else:
                logger.warning(
                    f"No trained weights at {self.model_path}. "
                    "Operating with initialized architecture. (Train model in Phase 6)."
                )
                self.is_model_trained = False

            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            logger.error(f"Failed to initialize disease model: {e}")
            self.model = None

    def validate_image_bytes(self, image_bytes: bytes, filename: str = "upload.jpg") -> Tuple[bool, Optional[str], Optional[Image.Image]]:
        """Strict validation of image upload: file size, format, dimension, and integrity."""
        # 1. Size check
        if not image_bytes or len(image_bytes) == 0:
            return False, "Uploaded image file is empty (0 bytes).", None

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(image_bytes) > max_bytes:
            return False, f"File size ({len(image_bytes) / (1024*1024):.2f}MB) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.", None

        # 2. Format & Integrity check
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()  # Verifies file integrity
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError, Exception) as e:
            return False, f"Invalid or corrupted image format. Please upload a valid JPG, PNG, or WEBP image: {str(e)}", None

        # 3. Minimum dimension check
        width, height = img.size
        if width < 32 or height < 32:
            return False, f"Image resolution ({width}x{height}) is too small for accurate agricultural diagnosis (minimum 32x32 required).", None

        # 4. Out-of-distribution heuristic check (ensure image is not solid color/blank)
        img_np = np.array(img)
        std_dev = np.std(img_np)
        if std_dev < 8.0:
            return False, "The uploaded image appears nearly monochromatic or blank. Please upload a clear photo of crop leaves.", None

        return True, None, img

    def predict(self, image_bytes: bytes, filename: str = "leaf.jpg") -> Dict[str, Any]:
        """Runs validation, preprocessing, inference, and advisory retrieval."""
        is_valid, error_msg, img = self.validate_image_bytes(image_bytes, filename)
        if not is_valid or img is None:
            return {
                "crop_name": "Unknown",
                "disease_name": "Validation Failed",
                "is_healthy": False,
                "confidence": 0.0,
                "status": "rejected",
                "advisory": "Image could not be processed due to validation rejection.",
                "top_alternatives": [],
                "source_references": [],
                "warning": error_msg or "Image validation failed."
            }

        # Preprocessing
        try:
            tensor = self.transform(img).unsqueeze(0).to(self.device)
        except Exception as e:
            logger.error(f"Image transformation failed: {e}")
            return {
                "crop_name": "Unknown",
                "disease_name": "Processing Error",
                "is_healthy": False,
                "confidence": 0.0,
                "status": "rejected",
                "advisory": "Error occurred during image preprocessing.",
                "top_alternatives": [],
                "source_references": [],
                "warning": str(e)
            }

        # Model Inference
        top_alternatives = []
        try:
            with torch.no_grad():
                logits = self.model(tensor)
                probabilities = torch.softmax(logits, dim=1).squeeze(0)
                top_k_probs, top_k_indices = torch.topk(probabilities, k=min(3, len(self.classes)))

                top_class_id = int(top_k_indices[0].item())
                top_prob = float(top_k_probs[0].item())

                for p, idx in zip(top_k_probs[1:], top_k_indices[1:]):
                    alt_id = int(idx.item())
                    alt_info = self.id_to_info.get(alt_id, {"raw_class": f"Class_{alt_id}", "crop": "Unknown", "disease": "Unknown"})
                    top_alternatives.append({
                        "label": alt_info.get("raw_class", ""),
                        "crop": alt_info.get("crop", "Unknown"),
                        "disease": alt_info.get("disease", "Unknown"),
                        "confidence": round(float(p.item()), 4)
                    })
        except Exception as e:
            logger.error(f"Inference execution failed: {e}")
            return {
                "crop_name": "Unknown",
                "disease_name": "Inference Error",
                "is_healthy": False,
                "confidence": 0.0,
                "status": "rejected",
                "advisory": "Model inference failed.",
                "top_alternatives": [],
                "source_references": [],
                "warning": str(e)
            }

        matched_info = self.id_to_info.get(top_class_id, {
            "crop": "Corn (Maize)",
            "disease": "Suspected Foliar Spot",
            "is_healthy": False,
            "advisory": "Scout the field for lesion progression and consult local KVK.",
            "source": "ICAR Extension Advisory"
        })

        crop_name = matched_info.get("crop", "Unknown")
        disease_name = matched_info.get("disease", "Unknown")
        is_healthy = matched_info.get("is_healthy", False)
        advisory = matched_info.get("advisory", "Consult an agricultural extension specialist.")
        source = matched_info.get("source", "ICAR Extension Services")

        # Uncertainty Handling
        # If the model is not trained yet or confidence is below threshold:
        status = "confident"
        warning = None

        if not self.is_model_trained:
            status = "uncertain"
            warning = (
                "Notice: Running on initialized MobileNetV3 transfer-learning architecture. "
                "For high-accuracy production inference, run the Colab training pipeline "
                "(notebooks/disease_training_colab.ipynb) and place model weights in models/disease/."
            )
        elif top_prob < self.confidence_threshold:
            status = "uncertain"
            warning = (
                f"Confidence ({top_prob:.1%}) is below the threshold ({self.confidence_threshold:.0%}). "
                "This is a preliminary AI assessment, not a definitive diagnosis. "
                "Please verify the symptoms with an agricultural extension officer or Krishi Vigyan Kendra."
            )

        # Log prediction to DB for analytics
        log_disease_prediction(
            crop_name=crop_name,
            disease_name=disease_name,
            confidence=round(top_prob, 4),
            is_healthy=is_healthy,
            alternatives=top_alternatives,
            image_name=filename
        )

        return {
            "crop_name": crop_name,
            "disease_name": disease_name,
            "is_healthy": is_healthy,
            "confidence": round(top_prob, 4),
            "status": status,
            "advisory": advisory,
            "top_alternatives": top_alternatives,
            "source_references": [source],
            "warning": warning
        }


disease_service = DiseaseService()
