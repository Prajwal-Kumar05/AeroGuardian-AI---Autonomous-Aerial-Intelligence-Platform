# 🚨 AeroPlan-Agent

<div align="center">

<img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Agents-LangGraph-1B2430?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Vision-YOLOv11%20%7C%20RT--DETR-F2A93B?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge"/>

<br/><br/>

</div>

An autonomous, multi-agent emergency-response platform built with **LangGraph**, combining real-time computer vision, weather intelligence, satellite verification, and GeoAI-powered evacuation planning into a single reasoning pipeline — from raw camera frame to a fully explained, dispatch-ready decision.

---

## 🎯 Objective

Build an intelligent emergency-response system that continuously monitors multiple real-world information sources — webcam, uploaded media, satellite imagery, live weather, and OpenStreetMap data — and doesn't just detect emergencies, but **verifies, reasons, plans, and explains** using seven cooperating AI agents.

---

## ✨ Features

### 🧠 Multi-Agent Reasoning (LangGraph)
Seven specialized agents — Monitoring, Vision Analysis, Verification, Risk Assessment, Geospatial Intelligence, Emergency Planning, and Explainable AI — pass a shared state through a directed graph, collaboratively reasoning toward a verified, auditable decision instead of a single black-box prediction.

### 🎯 Vision-Based Emergency Detection
RT-DETR / YOLOv11 detection of fire, smoke, flood, road accidents, collapsed buildings, fallen trees, blocked roads, and crowds — with bounding boxes, confidence scores, and estimated affected area per detection.

### ✅ Cross-Verified, False-Alarm-Resistant
Before anything is declared a real emergency, the Verification Agent cross-checks vision output against live weather conditions and NASA FIRMS satellite hotspot data, actively down-weighting implausible detections (e.g. fire cues during heavy rainfall).

### ⚠️ Automated Risk Assessment
A weighted risk-scoring algorithm combines emergency type, verification confidence, affected area, and weather amplifiers (like wind-driven fire spread) into a 0–100 score mapped to Low / Medium / High / Critical severity.

### 🗺️ Dynamic Evacuation Planning
Live OpenStreetMap road-network queries via OSMnx, with Dijkstra (primary) and A* (alternative) routing to the nearest safe zone — automatically excluding roads flagged as blocked by the Vision Agent.

### 🧾 Explainable AI, Not a Black Box
Every run produces a full step-by-step reasoning chain plus a human-readable narrative explaining what was detected, why it was (or wasn't) verified, why that severity was assigned, and why that evacuation route was chosen.

### 📢 Simulated Emergency Alerts
SMS, Email, Dashboard popup, and Voice alert dispatch to Police, Fire Department, Ambulance, and NDRF — fully simulated and logged for demo/grading purposes; no real emergency services are ever contacted.

### 🖥️ Unified Live Dashboard
A Streamlit control room with tabs for live monitoring, detection results, satellite context, weather, risk scoring, an interactive evacuation map, the full AI reasoning chain, incident timeline, and alert history.

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| Agent Orchestration | LangGraph (StateGraph) |
| Backend API | FastAPI, Pydantic |
| Vision Model | YOLOv11 / RT-DETR (Ultralytics), OpenCV, PyTorch, Transformers |
| Geospatial | OSMnx, NetworkX, GeoPandas, Shapely, Rasterio |
| Weather & Satellite | OpenWeatherMap API, NASA FIRMS, Sentinel Hub (Sentinel-2) |
| Database | PostgreSQL (SQLAlchemy ORM), auto-fallback to SQLite |
| Frontend | Streamlit, Folium (Leaflet), Plotly |
| Explainability | Structured reasoning chain + optional Claude-based narrative |
| Deployment | Docker Compose |

---

## 🚀 Getting Started

1. **Clone the repository**
```bash
git clone https://github.com/your-username/aeroplan-agent
cd aeroplan-agent
```

2. **Install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```
All external integrations (weather, satellite, LLM narration, fine-tuned vision model) have graceful fallbacks — the project runs end-to-end with zero API keys configured.

3. **Run the backend**
```bash
uvicorn backend.main:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs
```

4. **Run the dashboard**
```bash
streamlit run dashboard/app.py
# http://localhost:8501
```

Or run everything with Docker:
```bash
docker compose up --build
```

---

## 📁 Project Structure

```
aeroplan-agent/
├── backend/
│   ├── agents/          # 7 LangGraph agent nodes + graph.py orchestration
│   │   ├── monitoring_agent.py
│   │   ├── vision_agent.py
│   │   ├── verification_agent.py
│   │   ├── risk_agent.py
│   │   ├── geospatial_agent.py
│   │   ├── planning_agent.py
│   │   └── explainable_agent.py
│   ├── api/               # FastAPI routers
│   ├── core/               # config, database session
│   ├── ml/                  # YOLOv11/RT-DETR detector + heuristic fallback
│   ├── models/                # SQLAlchemy ORM + Pydantic schemas
│   ├── services/                # weather, satellite, OSM, routing, alerts
│   └── main.py                    # FastAPI entrypoint
├── dashboard/
│   └── app.py                       # Streamlit unified control room
├── database/
│   └── schema.sql                    # PostgreSQL DDL
├── docs/                               # architecture diagrams, install/deploy/API guides
├── datasets/                            # dataset sources + fine-tuning guide
├── tests/
├── docker-compose.yml
└── requirements.txt
```

---

## 📸 Screenshots

<img width="600" alt="Detection and Risk Assessment tab" src="docs/screenshots/dashboard-detection-risk.png" />
<img width="600" alt="Evacuation Route Map tab" src="docs/screenshots/dashboard-evacuation-route.png" />
<img width="600" alt="AI Reasoning and Alerts tab" src="docs/screenshots/dashboard-ai-reasoning-alerts.png" />

---

## ⚠️ Scope Note

All emergency-service notifications (SMS, Email, Dashboard popup, Voice alert to Police/Fire/Ambulance/NDRF) are **simulated only**. This is an academic project and never integrates with real emergency-dispatch infrastructure.

---

## 📄 License

MIT License — free to use, modify, and distribute.
