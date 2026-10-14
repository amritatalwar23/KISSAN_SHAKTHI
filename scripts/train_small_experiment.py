"""Phase 5: Small Model Experiment & Pipeline Verification.

Verifies end-to-end training loop, checkpoint saving, metric calculation,
and backend inference model loading without downloading multi-gigabyte datasets.
"""

import sys
import json
import time
from pathlib import Path

# Safe encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from torchvision import models
from sklearn.metrics import f1_score, classification_report

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.logging import logger
from backend.app.core.config import settings

def run_small_experiment():
    print("=" * 60)
    print("KISAN SHAKTI: Running Stage A Small Model Training Experiment")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Hardware compute device: {device}")

    # Load target classes from class mapping
    class_map_file = Path(settings.DISEASE_CLASS_MAP)
    with open(class_map_file, "r", encoding="utf-8") as f:
        class_data = json.load(f)
    classes = class_data["classes"]
    num_classes = len(classes)
    print(f"Loaded {num_classes} agricultural disease classes for Tomato, Potato, and Corn.")

    # 1. Generate small representative sample batch (4 samples per class = 68 samples)
    print("Generating representative sample tensors (224x224 RGB)...")
    torch.manual_seed(42)
    sample_images = torch.randn(num_classes * 4, 3, 224, 224)
    sample_labels = torch.cat([torch.full((4,), c_id, dtype=torch.long) for c_id in range(num_classes)])

    dataset = TensorDataset(sample_images, sample_labels)
    train_size = int(0.75 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = torch.utils.data.random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=8, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=8, shuffle=False)
    print(f"Dataset split: {len(train_set)} training samples, {len(val_set)} validation samples.")

    # 2. Initialize MobileNetV3 Small transfer learning architecture
    print("Initializing MobileNetV3 Small architecture...")
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001)

    # 3. Training Loop (1 Verification Epoch)
    start_time = time.time()
    print("Executing training epoch...")
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    train_loss = running_loss / total
    train_acc = correct / total
    elapsed = time.time() - start_time
    print(f"Training Epoch Complete in {elapsed:.2f}s | Loss: {train_loss:.4f} | Accuracy: {train_acc:.2%}")

    # 4. Validation Loop
    model.eval()
    val_preds, val_targets = [], []
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            val_preds.extend(preds.cpu().numpy())
            val_targets.extend(labels.cpu().numpy())

    macro_f1 = f1_score(val_targets, val_preds, average="macro", zero_division=0)
    print(f"Validation Complete | Macro F1-Score: {macro_f1:.4f}")

    # 5. Save model checkpoint
    model_save_path = Path(settings.DISEASE_MODEL_PATH)
    model_save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), model_save_path)
    file_size_mb = model_save_path.stat().st_size / (1024**2)
    print(f"SUCCESS: Model weights exported to {model_save_path} ({file_size_mb:.2f} MB)")

    # 6. Verify Backend Loader
    print("Verifying backend DiseaseService loader...")
    from backend.app.services.disease_service import DiseaseService
    test_service = DiseaseService()
    assert test_service.is_model_trained is True, "Service should confirm trained model state!"
    assert test_service.model is not None, "Model must be instantiated!"
    print("Backend DiseaseService verification: PASSED! Model is loaded and active.")
    print("=" * 60)

if __name__ == "__main__":
    run_small_experiment()
