# API Reference

Base URL: `http://localhost:8000`
Interactive Swagger UI: `/docs` · ReDoc: `/redoc`

## `POST /api/emergency/run`
Runs the full multi-agent pipeline against coordinates + a webcam/satellite source.

**Body**
```json
{ "latitude": 12.9716, "longitude": 77.5946, "source": "webcam", "image_path": null }
```

**Response** (`AgentGraphResult`)
```json
{
  "emergency": {
    "id": "uuid", "emergency_type": "fire", "status": "verified",
    "confidence": 0.82, "severity": "high", "risk_score": 71.4,
    "latitude": 12.9716, "longitude": 77.5946,
    "affected_area_m2": 812.0, "affected_population_estimate": 4,
    "reasoning": "...", "detections": [...], "routes": [...]
  },
  "reasoning_chain": [{"step": "Monitoring", "detail": "..."}, ...],
  "alerts_dispatched": [{"channel": "sms", "recipient_type": "fire_department", "message": "..."}]
}
```

## `POST /api/emergency/run-upload`
Multipart form: `latitude`, `longitude`, `file` (image). Runs the pipeline
against an uploaded frame instead of a live webcam.

## `GET /api/emergency/history?limit=50`
Returns recent emergency records (incident timeline data source).

## `GET /api/weather?lat=...&lon=...`
Returns current weather (OpenWeatherMap passthrough with synthetic fallback).

## `GET /api/alerts?limit=50`
Returns simulated alert dispatch history.

## `GET /api/logs?limit=100`
Returns per-agent execution logs (decision-log / audit trail view).

## `GET /health`
Liveness probe — `{"status": "ok"}`.
