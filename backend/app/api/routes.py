"""FastAPI REST API Endpoints for Kisan Shakti."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from typing import Optional, Dict, Any

from backend.app.schemas.schemas import (
    SpeakRequest,
    HealthResponse,
    DiseasePredictionResponse,
    QueryRequest,
    QueryResponse,
    SchemeSearchRequest,
    SchemeSearchResponse,
    CropPlanningRequest,
    CropPlanningResponse,
    ExpertLookupRequest,
    ExpertLookupResponse,
    WellbeingRequest,
    WellbeingResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    TranslationRequest,
    TranslationResponse,
)
from backend.app.services.disease_service import disease_service
from backend.app.services.scheme_service import scheme_service
from backend.app.services.crop_service import crop_service
from backend.app.services.expert_service import expert_service
from backend.app.services.wellbeing_service import wellbeing_service
from backend.app.services.rag_service import rag_service
from backend.app.services.multilingual_service import multilingual_service
from backend.app.services.orchestrator_service import orchestrator_service
from backend.app.services.voice_service import voice_service
from backend.app.database.db import get_analytics_summary
from backend.app.core.logging import logger

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """System health check and module status."""
    return {
        "status": "healthy",
        "app_name": "Kisan Shakti",
        "version": "1.0.0",
        "modules_loaded": {
            "disease_detection": disease_service.model is not None,
            "crop_planning": len(crop_service.crop_rules) > 0,
            "government_schemes": len(scheme_service.schemes) > 0,
            "expert_directory": len(expert_service.directory) > 0,
            "wellbeing_crisis_support": True,
            "rag_knowledge_base": len(rag_service.chunks) > 0,
            "multilingual_service": True,
            "orchestrator": True
        }
    }


@router.post("/predict/disease", response_model=DiseasePredictionResponse, tags=["Crop Health"])
async def predict_disease(
    file: UploadFile = File(...),
    crop_hint: Optional[str] = Form(None)
):
    """Diagnoses crop disease from uploaded leaf image using MobileNetV3 deep learning."""
    # Validate content type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type and file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Please upload a JPG, PNG, or WEBP image."
        )

    try:
        image_bytes = await file.read()
        result = disease_service.predict(image_bytes, filename=file.filename or "upload.jpg", crop_hint=crop_hint)
        return result
    except Exception as e:
        logger.error(f"Error in /predict/disease endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing leaf image: {str(e)}"
        )


@router.post("/query", response_model=QueryResponse, tags=["Assistant & Orchestrator"])
def orchestrate_query(req: QueryRequest):
    """Processes farmer queries via central AI orchestrator with safety and module routing."""
    try:
        res = orchestrator_service.route_and_execute(
            query=req.query,
            user_language=req.language,
            location=req.location,
            conversation_history=req.history
        )
        return res
    except Exception as e:
        logger.error(f"Error in /query endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/recommend/scheme", response_model=SchemeSearchResponse, tags=["Government Schemes"])
def recommend_schemes(req: SchemeSearchRequest):
    """Searches verified Indian agricultural schemes, subsidies, and credit programs."""
    try:
        return scheme_service.search_schemes(
            state=req.state,
            category=req.category,
            crop=req.crop,
            keyword=req.keyword
        )
    except Exception as e:
        logger.error(f"Error in /recommend/scheme endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search schemes: {str(e)}"
        )


@router.post("/recommend/crop", response_model=CropPlanningResponse, tags=["Crop Planning"])
def recommend_crop_planning(req: CropPlanningRequest):
    """Recommends crops factoring soil type, seasonal calendar, water availability, and land size."""
    try:
        return crop_service.recommend_crops(
            state=req.state,
            district=req.district,
            season=req.season,
            soil_type=req.soil_type,
            water_availability=req.water_availability,
            land_size_acres=req.land_size_acres,
            preferred_category=req.preferred_category
        )
    except Exception as e:
        logger.error(f"Error in /recommend/crop endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate crop plan: {str(e)}"
        )


@router.post("/expert", response_model=ExpertLookupResponse, tags=["Expert & KVK Directory"])
def lookup_experts(req: ExpertLookupRequest):
    """Locates verified Krishi Vigyan Kendras (KVK) and agricultural support centers."""
    try:
        return expert_service.lookup_experts(
            state=req.state,
            district=req.district,
            category=req.category
        )
    except Exception as e:
        logger.error(f"Error in /expert endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lookup expert directory: {str(e)}"
        )


@router.post("/wellbeing", response_model=WellbeingResponse, tags=["Safety & Wellbeing"])
def check_wellbeing(req: WellbeingRequest):
    """Evaluates distress signals and provides free, verified 24x7 crisis helplines (Tele-MANAS, KCC)."""
    try:
        return wellbeing_service.assess_wellbeing(text=req.message, language=req.language or "en")
    except Exception as e:
        logger.error(f"Error in /wellbeing endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess wellbeing: {str(e)}"
        )


@router.post("/rag/query", response_model=RAGQueryResponse, tags=["Knowledge Base"])
def query_knowledge_base(req: RAGQueryRequest):
    """Direct query to the ICAR/KVK grounded agricultural knowledge retrieval engine."""
    try:
        return rag_service.query(question=req.question, top_k=req.top_k)
    except Exception as e:
        logger.error(f"Error in /rag/query endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge retrieval error: {str(e)}"
        )


@router.post("/translate", response_model=TranslationResponse, tags=["Multilingual"])
def translate_agricultural_text(req: TranslationRequest):
    """Translates agricultural text across English, Kannada, and Hindi."""
    try:
        return multilingual_service.translate_text(
            text=req.text,
            target_lang=req.target_lang,
            source_lang=req.source_lang or "auto"
        )
    except Exception as e:
        logger.error(f"Error in /translate endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(e)}"
        )


@router.get("/analytics", tags=["Analytics"])
def get_analytics():
    """Returns aggregated usage statistics and diagnostic metrics for the dashboard."""
    try:
        return get_analytics_summary()
    except Exception as e:
        logger.error(f"Error in /analytics endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics retrieval error: {str(e)}"
        )


async def _read_audio(file: UploadFile) -> bytes:
    audio = await file.read()
    if len(audio) < 1000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Audio clip is empty or too short")
    if len(audio) > 25 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio clip exceeds 25 MB")
    return audio


@router.post("/voice/transcribe", tags=["Voice"])
async def transcribe_voice(file: UploadFile = File(...), language: Optional[str] = Form(None)):
    """Speech-to-text for a recorded or uploaded clip (Whisper, runs locally)."""
    audio = await _read_audio(file)
    try:
        return await run_in_threadpool(voice_service.transcribe, audio, language)
    except Exception as e:
        logger.error(f"Error in /voice/transcribe endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Could not decode audio: {e}")


@router.post("/voice/speak", tags=["Voice"])
def speak_text(req: SpeakRequest):
    """Text-to-speech; returns an MP3 of the text in the requested language."""
    try:
        return Response(content=voice_service.synthesize(req.text, req.language or "en"), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Error in /voice/speak endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Speech synthesis unavailable: {e}")


@router.post("/voice/query", tags=["Voice"])
async def voice_query(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    state: Optional[str] = Form("Karnataka"),
):
    """Full voice loop: transcribe the clip, then answer it in the spoken language."""
    audio = await _read_audio(file)
    try:
        heard = await run_in_threadpool(voice_service.transcribe, audio, language)
    except Exception as e:
        logger.error(f"Error in /voice/query transcription: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Could not decode audio: {e}")
    if len(heard["text"]) < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No speech detected in the clip")

    result = await run_in_threadpool(
        orchestrator_service.route_and_execute,
        query=heard["text"],
        user_language=heard["language"],
        location={"state": state or "Karnataka"},
    )
    result["transcription"] = heard
    return result
