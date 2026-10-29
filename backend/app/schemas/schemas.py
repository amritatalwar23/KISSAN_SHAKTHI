"""Pydantic schemas for request validation and structured API responses (Pydantic v2 compliant)."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Health Check
class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    app_name: str = Field(..., json_schema_extra={"example": "Kisan Shakti"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    modules_loaded: Dict[str, bool]

# Disease Detection
class PredictionAlternative(BaseModel):
    label: str
    crop: str
    disease: str
    confidence: float

class DiseasePredictionResponse(BaseModel):
    crop_name: str
    disease_name: str
    is_healthy: bool
    confidence: float
    status: str = Field(..., description="'confident', 'uncertain', or 'rejected'")
    advisory: str
    top_alternatives: List[PredictionAlternative] = []
    source_references: List[str] = []
    warning: Optional[str] = None

# General Query & Orchestration
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, json_schema_extra={"example": "My tomato leaves have black spots with yellow halos, what should I do?"})
    language: Optional[str] = Field("en", json_schema_extra={"example": "en"})
    location: Optional[Dict[str, str]] = None
    history: List[Dict[str, str]] = Field(default_factory=list, max_length=8)

class QueryResponse(BaseModel):
    query: str
    language: str
    routed_module: str
    answer: str
    sources: List[str] = []
    structured_data: Optional[Dict[str, Any]] = None
    warning: Optional[str] = None

# Government Schemes
class SchemeSearchRequest(BaseModel):
    state: Optional[str] = Field(None, json_schema_extra={"example": "Karnataka"})
    category: Optional[str] = Field(None, json_schema_extra={"example": "Small and Marginal Farmer"})
    crop: Optional[str] = Field(None, json_schema_extra={"example": "Potato"})
    keyword: Optional[str] = None

class SchemeDetail(BaseModel):
    id: str
    name: str
    ministry: str
    level: str  # Central or State
    state: Optional[str] = None
    target_beneficiaries: str
    benefits: str
    eligibility_criteria: List[str]
    documents_required: List[str]
    official_link: str
    last_verified: str
    status: str

class SchemeSearchResponse(BaseModel):
    total_found: int
    schemes: List[SchemeDetail]
    disclaimer: str

# Crop Planning
class CropPlanningRequest(BaseModel):
    state: str = Field(..., json_schema_extra={"example": "Karnataka"})
    district: Optional[str] = Field(None, json_schema_extra={"example": "Dharwad"})
    season: str = Field(..., json_schema_extra={"example": "Kharif"})  # Kharif, Rabi, Zaid
    soil_type: str = Field(..., json_schema_extra={"example": "Red sandy loam"})
    water_availability: str = Field(..., json_schema_extra={"example": "Moderate"})  # High, Moderate, Low
    land_size_acres: Optional[float] = Field(None, json_schema_extra={"example": 2.5})
    preferred_category: Optional[str] = None

class CropRecommendation(BaseModel):
    crop_name: str
    variety: str
    season: str
    duration_days: str
    suitability_score: float
    rationale: str
    water_requirement: str
    soil_suitability: str
    key_risks_and_cautions: List[str]

class CropPlanningResponse(BaseModel):
    input_summary: Dict[str, Any]
    recommendations: List[CropRecommendation]
    assumptions: List[str]
    cautions: List[str]
    disclaimer: str

# Expert and KVK Lookup
class ExpertLookupRequest(BaseModel):
    state: str = Field(..., json_schema_extra={"example": "Karnataka"})
    district: Optional[str] = Field(None, json_schema_extra={"example": "Bangalore Rural"})
    category: Optional[str] = None

class ExpertContact(BaseModel):
    name: str
    organization: str
    type: str
    district: str
    state: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    official_link: str
    verified_on: str

class ExpertLookupResponse(BaseModel):
    total_found: int
    contacts: List[ExpertContact]
    official_directory_url: str
    disclaimer: str

# Farmer Wellbeing & Crisis
class WellbeingRequest(BaseModel):
    message: str = Field(..., min_length=2)
    language: Optional[str] = "en"

class CrisisHelpline(BaseModel):
    name: str
    number: str
    availability: str
    languages: str
    managed_by: str
    is_toll_free: bool

class WellbeingResponse(BaseModel):
    is_crisis_detected: bool
    urgency_level: str
    empathetic_message: str
    helplines: List[CrisisHelpline]
    safety_disclaimer: str

# RAG Knowledge Retrieval
class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 3

class RAGChunk(BaseModel):
    title: str
    content: str
    source: str
    publication: Optional[str] = None
    retrieval_score: float

class RAGQueryResponse(BaseModel):
    question: str
    retrieved_chunks: List[RAGChunk]
    grounded_answer: str
    sufficient_evidence: bool
    sources: List[str]

# Multilingual Translation
class TranslationRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = Field(..., json_schema_extra={"example": "kn"})

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    detected_lang: str
    target_lang: str
