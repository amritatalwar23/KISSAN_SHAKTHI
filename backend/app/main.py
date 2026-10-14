"""Kisan Shakti — Main FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.db import init_db
from backend.app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle events."""
    logger.info("Initializing Kisan Shakti database and services...")
    init_db()
    logger.info("Kisan Shakti backend started successfully.")
    yield
    logger.info("Kisan Shakti backend shutting down.")


app = FastAPI(
    title="Kisan Shakti API",
    description=(
        "AI-Based Multilingual Agricultural Assistance System providing "
        "crop disease identification, agricultural RAG knowledge retrieval, "
        "government scheme discovery, smart crop planning, verified KVK expert assistance, "
        "and farmer crisis wellbeing support."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, "CORS_ORIGINS") else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(router)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again or contact support.",
            "error_type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
