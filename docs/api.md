# Kisan Shakti — REST API Documentation

The Kisan Shakti FastAPI backend exposes modular, documented REST endpoints. When the backend is running, interactive Swagger UI documentation is available at `http://127.0.0.1:8000/docs`.

---

## Base URL
`http://127.0.0.1:8000`

---

## Endpoints

### 1. `GET /health`
System liveness check and status of loaded modules.
- **Response**:
```json
{
  "status": "healthy",
  "app_name": "Kisan Shakti",
  "version": "1.0.0",
  "modules_loaded": {
    "disease_detection": true,
    "crop_planning": true,
    "government_schemes": true,
    "expert_directory": true,
    "wellbeing_crisis_support": true,
    "rag_knowledge_base": true,
    "multilingual_service": true,
    "orchestrator": true
  }
}
```

---

### 2. `POST /predict/disease`
Diagnoses crop disease from an uploaded leaf image file.
- **Content-Type**: `multipart/form-data`
- **Body**: `file` (Binary image: JPG, PNG, WEBP)
- **Response**:
```json
{
  "crop_name": "Tomato",
  "disease_name": "Early Blight (Alternaria linariae)",
  "is_healthy": false,
  "confidence": 0.8942,
  "status": "confident",
  "advisory": "Prune infected bottom leaves touching the soil. Spray azoxystrobin (1 ml/L) or mancozeb (2.5 g/L).",
  "top_alternatives": [
    {
      "label": "Tomato___Septoria_leaf_spot",
      "crop": "Tomato",
      "disease": "Septoria Leaf Spot",
      "confidence": 0.0621
    }
  ],
  "source_references": ["ICAR-IIHR Tomato Disease Advisory"],
  "warning": null
}
```

---

### 3. `POST /query`
Processes multi-intent farmer queries through the central AI orchestrator.
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "query": "Tell me about PM-KISAN subsidy and crop insurance",
  "language": "en",
  "location": { "state": "Karnataka" }
}
```

---

### 4. `POST /recommend/scheme`
Filters verified central and state welfare schemes.
- **Body**:
```json
{
  "state": "Karnataka",
  "crop": "Potato",
  "keyword": "insurance"
}
```

---

### 5. `POST /recommend/crop`
Generates agronomic crop suitability recommendations.
- **Body**:
```json
{
  "state": "Karnataka",
  "district": "Dharwad",
  "season": "Kharif",
  "soil_type": "Red sandy loam",
  "water_availability": "Moderate",
  "land_size_acres": 2.5
}
```

---

### 6. `POST /expert`
Looks up verified Krishi Vigyan Kendras (KVK) and extension centers.
- **Body**:
```json
{
  "state": "Karnataka",
  "district": "Bangalore Rural"
}
```

---

### 7. `POST /wellbeing`
Detects acute farmer distress and provides verified 24x7 helplines.
- **Body**:
```json
{
  "message": "I lost my crop and need emergency help",
  "language": "en"
}
```

---

### 8. `POST /rag/query`
Direct query to the ICAR/KVK grounded knowledge base.
- **Body**:
```json
{
  "question": "How to control fall armyworm in maize?",
  "top_k": 3
}
```

---

### 9. `POST /translate`
Translates agricultural text across English, Kannada, and Hindi.
- **Body**:
```json
{
  "text": "Tomato Late Blight",
  "target_lang": "kn"
}
```

---

### 10. `GET /analytics`
Retrieves aggregated observability metrics from SQLite for dashboard rendering.
