"""
FastAPI Application Entry Point
Rule Evaluator API - Đánh giá hồ sơ bảo hiểm
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.routers import evaluate


# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API đánh giá hồ sơ bảo hiểm theo các rules sử dụng GPT-4o-mini",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(evaluate.router)


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "model": settings.openai_model
    }


@app.get("/info", tags=["Info"])
async def app_info():
    """Application information"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "model": settings.openai_model,
        "endpoints": {
            "health": "GET /",
            "info": "GET /info",
            "evaluate": "POST /evaluate",
            "docs": "GET /docs"
        }
    }
