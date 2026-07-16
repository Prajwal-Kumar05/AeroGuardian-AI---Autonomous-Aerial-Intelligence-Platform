"""
AeroPlan-Agent :: /emergency routes
Triggers the LangGraph multi-agent pipeline and persists results.
"""
import datetime as dt
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models import db_models
from backend.models.schemas import EmergencyRunRequest, AgentGraphResult
from backend.agents.graph import run_pipeline

router = APIRouter(prefix="/api/emergency", tags=["emergency"])


@router.post("/run", response_model=AgentGraphResult)
def run_emergency_pipeline(payload: EmergencyRunRequest, db: Session = Depends(get_db)):
    result = run_pipeline(
        latitude=payload.latitude,
        longitude=payload.longitude,
        source=payload.source,
        image_path=payload.image_path,
    )
    emergency_out = _persist(result, db)
    return AgentGraphResult(
        emergency=emergency_out,
        reasoning_chain=result.get("reasoning_chain", []),
        alerts_dispatched=result.get("alerts_dispatched", []),
    )


@router.post("/run-upload", response_model=AgentGraphResult)
async def run_with_upload(
    latitude: float = Form(...),
    longitude: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    import os
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{dt.datetime.utcnow().timestamp()}_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())

    result = run_pipeline(latitude=latitude, longitude=longitude, source="upload", image_path=path)
    emergency_out = _persist(result, db)
    return AgentGraphResult(
        emergency=emergency_out,
        reasoning_chain=result.get("reasoning_chain", []),
        alerts_dispatched=result.get("alerts_dispatched", []),
    )


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(db_models.Emergency)
        .order_by(db_models.Emergency.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id, "emergency_type": r.emergency_type, "status": r.status,
            "severity": r.severity, "risk_score": r.risk_score,
            "latitude": r.latitude, "longitude": r.longitude,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


def _persist(result: dict, db: Session):
    from backend.models.schemas import EmergencyOut, DetectionOut, RouteOut

    status = "verified" if result.get("is_true_emergency") else "false_alarm"
    em = db_models.Emergency(
        emergency_type=result.get("emergency_type", "none"),
        status=status,
        confidence=result.get("emergency_confidence", 0.0),
        severity=result.get("severity", "none"),
        risk_score=result.get("risk_score", 0.0),
        latitude=result.get("latitude"),
        longitude=result.get("longitude"),
        affected_area_m2=result.get("affected_area_m2"),
        affected_population_estimate=result.get("affected_population_estimate"),
        source=result.get("source", "webcam"),
        reasoning=result.get("explanation", ""),
    )
    db.add(em)
    db.flush()

    for d in result.get("detections", []):
        db.add(db_models.Detection(
            emergency_id=em.id, label=d["label"], confidence=d["confidence"],
            bbox=d["bbox"], frame_source=result.get("source", "webcam"),
        ))

    weather = result.get("weather", {})
    if weather:
        db.add(db_models.WeatherSnapshot(
            latitude=result.get("latitude"), longitude=result.get("longitude"),
            temperature_c=weather.get("temperature_c"), humidity_pct=weather.get("humidity_pct"),
            wind_speed_ms=weather.get("wind_speed_ms"), rainfall_mm=weather.get("rainfall_mm"),
            visibility_m=weather.get("visibility_m"), condition=weather.get("condition"),
            raw_payload=weather.get("raw_payload"),
        ))

    routes_out = []
    for rtype, route in (("primary", result.get("primary_route")), ("alternative", result.get("alternative_route"))):
        if route and route.get("distance_m") is not None:
            db.add(db_models.Route(
                emergency_id=em.id, route_type=rtype, algorithm=route.get("algorithm"),
                origin_lat=result.get("latitude"), origin_lon=result.get("longitude"),
                destination_name=result.get("selected_shelter", {}).get("name", "N/A"),
                destination_lat=result.get("selected_shelter", {}).get("latitude"),
                destination_lon=result.get("selected_shelter", {}).get("longitude"),
                distance_m=route.get("distance_m"), path_coordinates=route.get("path_coordinates"),
                blocked_roads_avoided=result.get("blocked_roads", []),
            ))
            routes_out.append(RouteOut(
                route_type=rtype, algorithm=route.get("algorithm"),
                destination_name=result.get("selected_shelter", {}).get("name", "N/A"),
                distance_m=route.get("distance_m"), path_coordinates=route.get("path_coordinates"),
            ))

    for a in result.get("alerts_dispatched", []):
        db.add(db_models.Alert(
            emergency_id=em.id, channel=a["channel"], recipient_type=a["recipient_type"],
            message=a["message"], simulated=True, status="sent",
        ))

    for log in result.get("agent_logs", []):
        db.add(db_models.AgentLog(
            emergency_id=em.id, agent_name=log["agent_name"], action=log["action"],
            input_summary=log.get("input_summary"), output_summary=log.get("output_summary"),
            duration_ms=log.get("duration_ms"),
        ))

    db.commit()
    db.refresh(em)

    return EmergencyOut(
        id=em.id, emergency_type=em.emergency_type, status=em.status,
        confidence=em.confidence, severity=em.severity, risk_score=em.risk_score,
        latitude=em.latitude, longitude=em.longitude,
        affected_area_m2=em.affected_area_m2,
        affected_population_estimate=em.affected_population_estimate,
        reasoning=em.reasoning,
        detections=[DetectionOut(label=d["label"], confidence=d["confidence"], bbox=d["bbox"])
                    for d in result.get("detections", [])],
        routes=routes_out,
    )
