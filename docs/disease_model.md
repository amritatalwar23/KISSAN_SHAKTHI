# Kisan Shakti — Crop Disease Model Specification

## 1. Model Architecture
- **Base Architecture**: MobileNetV3 Small (`mobilenet_v3_small`)
- **Pretraining**: Transfer learning from ImageNet-1K pretrained weights
- **Classification Head**: Adaptive average pooling followed by a Dropout (0.2) and a Linear projection layer mapping 1024 latent features to 17 disease classes.
- **Parameters**: ~1.5 million parameters (~5.98 MB state dict).
- **Inference Speed**: ~20-40 ms per image on standard CPU; <5 ms on GPU.

---

## 2. Input Specifications
- **Input Dimensions**: `3 x 224 x 224` (RGB channels)
- **Normalization**:
  - Means: `[0.485, 0.456, 0.406]`
  - Standard Deviations: `[0.229, 0.224, 0.225]`
- **Supported File Formats**: JPEG, PNG, WEBP (Max size: 10 MB).

---

## 3. Output Classes (17 Classes)
1. `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot`
2. `Corn_(maize)___Common_rust_`
3. `Corn_(maize)___Northern_Leaf_Blight`
4. `Corn_(maize)___healthy`
5. `Potato___Early_blight`
6. `Potato___Late_blight`
7. `Potato___healthy`
8. `Tomato___Bacterial_spot`
9. `Tomato___Early_blight`
10. `Tomato___Late_blight`
11. `Tomato___Leaf_Mold`
12. `Tomato___Septoria_leaf_spot`
13. `Tomato___Spider_mites Two-spotted_spider_mite`
14. `Tomato___Target_Spot`
15. `Tomato___Tomato_Yellow_Leaf_Curl_Virus`
16. `Tomato___Tomato_mosaic_virus`
17. `Tomato___healthy`

---

## 4. Safeguards & Uncertainty Policies
- **Out-of-Distribution (OOD) Guard**: Monochromatic, blank, or non-plant images with standard deviation < 8.0 are rejected prior to classification.
- **Confidence Threshold**: 60% (`CONFIDENCE_THRESHOLD = 0.60`).
- **Uncertainty Flagging**: If the top prediction has a softmax probability below 0.60, the prediction status is marked `uncertain`, a cautionary warning is attached, and the farmer is advised to seek physical confirmation from an agricultural extension officer.
