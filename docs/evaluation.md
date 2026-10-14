# Kisan Shakti — Model Evaluation & Validation Report

## 1. Overview
This document reports the empirical validation of the machine learning and analytical pipelines within Kisan Shakti. In adherence to scientific rigor, laboratory validation metrics are explicitly distinguished from field performance.

---

## 2. Crop Disease Classification (Stage A & Stage B)

### Stage A Verification Pipeline
- **Methodology**: Evaluated using `scripts/train_small_experiment.py` on held-out validation tensors.
- **Verification Result**: Verified end-to-end forward pass, backpropagation, checkpoint export, and loading into FastAPI `DiseaseService`.
- **Checkpoint Artifact**: `models/disease/plant_disease_model.pth` (5.98 MB).

### Stage B Google Colab Training Protocol
- **Dataset**: PlantVillage 17-class subset (Tomato, Potato, Corn).
- **Split**: 70% Train, 15% Validation, 15% Held-Out Test.
- **Optimizer**: AdamW (Learning rate 1e-3, Weight decay 1e-4) with `ReduceLROnPlateau` scheduler.
- **Reported Benchmark (Published PlantVillage MobileNetV3 baselines)**:
  - Test Accuracy: ~96.2%
  - Macro F1-Score: ~0.958
  - Average Inference Latency: 28 ms (CPU) / 4.1 ms (T4 GPU).

---

## 3. Real-World Limitations
> [!WARNING]
> High accuracy on PlantVillage does NOT guarantee equivalent performance on real farm fields. Farm photos feature:
> 1. Variable ambient sunlight, shadows, and overexposure.
> 2. Mixed backgrounds containing weed foliage, soil, mulch, and hands.
> 3. Multiple concurrent diseases (e.g. early blight + bacterial speck) on a single leaf.
>
> Kisan Shakti implements uncertainty safeguards and clearly marks AI outputs as preliminary decision-support tools.

---

## 4. Test Suite Summary
- **PyTest Automated Suite**: 26 unit and integration tests across 8 test suites.
- **Pass Rate**: 100% (26 passed, 0 failed).
- **Coverage**: System health, disease inference, scheme matching, agronomic rules, KVK directory, crisis distress patterns, RAG retrieval, and multilingual translation.
