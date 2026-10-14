# Kisan Shakti — System Architecture

## Overview
Kisan Shakti is an AI-based agricultural advisory system designed with a modular, decoupled architecture. It separates the presentation tier (Web GUI), application/API tier (FastAPI), and domain intelligence services (Computer Vision, RAG, Expert Matching, Schemes, Wellbeing).

---

## High-Level Component Diagram

```
+-----------------------------------------------------------------------------------+
|                            User Interface Layer                                   |
|   Streamlit Web Application (Desktop & Mobile Responsive)                         |
|   - Crop Disease Image Upload & Preview                                           |
|   - Multilingual AI Chat & Speech Synthesis                                      |
|   - Scheme Filtering & Eligibility Explorer                                      |
|   - Agronomic Crop Planning Form                                                  |
|   - Verified KVK Directory Explorer                                              |
|   - Observability & Analytics Dashboard (Plotly)                                 |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (JSON)
                                           v
+-----------------------------------------------------------------------------------+
|                            FastAPI Application Gateway                            |
|   - Request Validation (Pydantic V2)                                              |
|   - Global Exception Handling & Structured Logging                                |
|   - CORS Middleware & File Upload Guards (10MB max, RGB verification)             |
|   - SQLite Observability Logging                                                  |
+------------------------------------------+----------------------------------------+
                                           | Internal Dispatch
                                           v
+-----------------------------------------------------------------------------------+
|                              Modular AI & Domain Services                         |
|                                                                                   |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | DiseaseService     |   | OrchestratorService   |   | SchemeService          |  |
|  | MobileNetV3 (17 cl)|   | Intent Router         |   | Verified Govt Portals  |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | CropService        |   | ExpertService         |   | WellbeingService       |  |
|  | Agronomic Rules    |   | ICAR KVK Directory    |   | Tele-MANAS (14416)     |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
|  | RAGService         |   | MultilingualService   |   | Database Service       |  |
|  | Vector Retrieval   |   | en / kn / hi          |   | SQLite Analytics       |  |
|  +--------------------+   +-----------------------+   +------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## Architectural Principles
1. **Modularity over Monoliths**: No single AI model performs all tasks. Disease vision is separate from language retrieval, which is separate from rule-based agronomy.
2. **Deterministic Safety Guarding**: Severe crisis queries bypass general AI and immediately trigger validated life-safety helplines (Tele-MANAS, KCC).
3. **Evidence-Grounded RAG**: Knowledge answers require source attribution to ICAR/KVK institutional documents.
4. **Offline Resilience**: Essential functions run without requiring external cloud API keys.
5. **Decoupled API Contract**: FastAPI endpoints use standard Pydantic schemas, enabling future WhatsApp Business API integration without backend redesign.
