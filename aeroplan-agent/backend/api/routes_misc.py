from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.config import get_settings
from backend.models import db_models
from backend.services.weather_service import get_current_weather

router = APIRouter(prefix="/api", tags=["misc"])
settings = get_settings()


@router.get("/weather")
def weather(lat: float = None, lon: float = None):
    lat = lat if lat is not None else settings.DEFAULT_LAT
    lon = lon if lon is not None else settings.DEFAULT_LON
    return get_current_weather(lat, lon)


@router.get("/alerts")
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(db_models.Alert).order_by(db_models.Alert.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "emergency_id": r.emergency_id, "channel": r.channel,
            "recipient_type": r.recipient_type, "message": r.message,
            "simulated": r.simulated, "status": r.status, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/logs")
def list_logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(db_models.AgentLog).order_by(db_models.AgentLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "emergency_id": r.emergency_id, "agent_name": r.agent_name,
            "action": r.action, "input_summary": r.input_summary, "output_summary": r.output_summary,
            "duration_ms": r.duration_ms, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
