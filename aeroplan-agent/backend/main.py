"""
AeroPlan-Agent :: FastAPI backend entrypoint

Run: uvicorn backend.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.database import init_db
from backend.utils.logger import setup_logging
from backend.api import routes_emergency, routes_misc

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Autonomous Multi-Agent Framework for Real-Time Emergency Detection and Disaster Response",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_emergency.router)
app.include_router(routes_misc.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "agents": [
            "MonitoringAgent", "VisionAnalysisAgent", "VerificationAgent",
            "RiskAssessmentAgent", "GeospatialIntelligenceAgent",
            "EmergencyPlanningAgent", "ExplainableAIAgent",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
