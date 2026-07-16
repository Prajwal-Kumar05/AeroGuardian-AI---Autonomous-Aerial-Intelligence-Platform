# Deployment Guide

## 1. Containerized deployment (single VM / on-prem server)

```bash
docker compose up -d --build
```
This launches `db` (PostgreSQL), `backend` (FastAPI on :8000), and
`dashboard` (Streamlit on :8501) as three services on a shared network.
Put a reverse proxy (Nginx/Caddy) in front for TLS termination in
production.

Example Nginx snippet:
```nginx
server {
    listen 443 ssl;
    server_name aeroplan.example.edu;

    location /api/ { proxy_pass http://localhost:8000; }
    location /      { proxy_pass http://localhost:8501; }
}
```

## 2. Cloud deployment options

| Component | Suggested service |
|---|---|
| Backend (FastAPI) | AWS ECS / Fargate, Render, Railway, or a GPU-enabled VM (for real-time vision inference) |
| Dashboard (Streamlit) | Streamlit Community Cloud, or same container host as backend |
| Database | AWS RDS / Supabase / Neon (managed PostgreSQL) |
| Vision inference | GPU instance (e.g. AWS g4dn, or a local edge device with a CUDA-capable GPU) if running RT-DETR/YOLOv11 at video frame-rate |

## 3. Environment separation
- Use distinct `.env` files per environment (`.env.dev`, `.env.staging`, `.env.prod`)
- Never commit `.env` — only `.env.example` is tracked in version control
- Rotate `SECRET_KEY` and all API keys before any public deployment

## 4. Scaling notes
- The LangGraph pipeline is stateless per-request — horizontal scaling of
  the FastAPI backend behind a load balancer is straightforward.
- OSMnx road-network downloads are cached in-process per `(lat, lon,
  radius)` key; for multi-instance deployments, consider a shared Redis
  cache or pre-downloading network graphs for known monitored zones.
- For genuinely continuous (24/7) webcam monitoring, replace the
  request-triggered `run_pipeline()` call with a background scheduler
  (e.g. APScheduler / Celery beat) invoking the graph on a fixed interval
  per camera feed.

## 5. Safety & scope reminder
`backend/services/alert_service.py` enforces `SIMULATE_ALERTS_ONLY = True`
and only logs simulated alerts — no code path in this repository contacts
real emergency dispatch systems. Any production deployment intending to
notify real responders would require formal integration agreements with
local emergency services, which is explicitly out of scope for this
academic project.
