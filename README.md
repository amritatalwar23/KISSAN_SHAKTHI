# Kisan Shakti (किसान शक्ति / ಕಿಸಾನ್ ಶಕ್ತಿ)
## AI-Based Multilingual Agricultural Assistance System

Kisan Shakti is an AI-powered agricultural advisory platform designed to empower Indian farmers with timely, reliable, and accessible agricultural guidance. It provides crop disease diagnosis, agronomic crop planning, government scheme eligibility discovery, verified Krishi Vigyan Kendra (KVK) expert assistance, multilingual interactions (English, Kannada, Hindi), and crisis wellbeing support.

---

## 🌟 Key Features

1. **Crop Disease Identification**:
   - Deep learning image diagnosis for major Indian crops (Tomato, Potato, Corn/Maize).
   - Top-k predictions, confidence scoring, grounded advisory, and out-of-distribution uncertainty safeguards.
   - Built with lightweight transfer learning (MobileNetV3).

2. **Agricultural Knowledge Base (RAG)**:
   - Grounded retrieval over credible institutional sources (ICAR, KVKs, State Agricultural Universities).
   - Transparent source attribution and citations.

3. **Government Schemes & Subsidies**:
   - Discover schemes like PM-KISAN, PMFBY, PM Krishi Sinchayee Yojana, and KCC.
   - Filter by State, Farmer Category, and Land Holding with verified official portal links.

4. **Smart Crop Planning**:
   - Rule-grounded agronomic recommendation engine factoring soil type, agro-climatic season, water availability, and land size.

5. **Expert & KVK Directory**:
   - Location-indexed directory of verified Krishi Vigyan Kendras, Agricultural Research Stations, and university extension centers.

6. **Farmer Wellbeing & Crisis Support**:
   - Conservative, empathetic detection of severe distress and farming crisis signals.
   - Verified national helplines: **Tele-MANAS (14416 / 1800-891-4416)** and **Kisan Call Centre (1800-180-1551)**.

7. **Multilingual & Voice Assistance**:
   - Support for **English**, **Kannada (ಕನ್ನಡ)**, and **Hindi (हिन्दी)**.
   - Web Speech API integration for voice-in and voice-out workflows.

8. **Interactive Visual Dashboard**:
   - Plotly-powered visual monitoring of queries, diagnostic trends, and crop advisory metrics.

---

## 🏗️ Architecture

```
                       +---------------------------------------+
                       |   Kisan Shakti Web Interface (GUI)    |
                       |  (Streamlit / Responsive Dashboard)   |
                       +-------------------+-------------------+
                                           | HTTP REST API
                                           v
+-----------------------------------------------------------------------------------+
|                           FastAPI Central Backend                                 |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | /predict/disease   |   | /query (Orchestrator) |   | /recommend/scheme      |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | /recommend/crop    |   | /expert               |   | /wellbeing             |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
+-----------------------------------------------------------------------------------+
       |                    |                    |                   |
       v                    v                    v                   v
[Disease Engine]     [RAG Retriever]     [Agronomic Rules]    [Verified Directories]
(MobileNetV3 CV)    (Vector / TF-IDF)     (ICAR / Agri Dept)      (KVK / Extension)
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Git

### 2. Setup Environment
```bash
git clone <repo-url>
cd KISAAN_SHAKTHI

# Create and activate virtual environment (optional)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env
```

### 3. Launch the Backend
```bash
python scripts/run_backend.py
# Or directly:
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: `http://127.0.0.1:8000/docs`

### 4. Launch the Web Interface
```bash
python scripts/run_frontend.py
# Or directly:
streamlit run frontend/app.py
```
Web app will be available at: `http://localhost:8501`

---

## 🧪 Running Tests
```bash
pytest backend/tests -v
```

---

## 🔒 Safety & Disclaimer
Kisan Shakti provides preliminary decision-support information based on machine learning models and public agricultural datasets. AI diagnostic suggestions must not replace certified agricultural extension officers, agronomists, or laboratory pathogen testing.
