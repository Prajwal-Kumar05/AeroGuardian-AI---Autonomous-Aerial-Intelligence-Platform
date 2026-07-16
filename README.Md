# 🚨 AeroPlan-Agent

**AI-Powered Autonomous Multi-Agent Framework for Real-Time Emergency Detection and Disaster Response**

A final-year BE Computer Science project combining **Agentic AI**, **Computer
Vision**, **GeoAI**, and **Disaster Management** into one autonomous
platform that doesn't just *detect* emergencies — it *reasons* over
multi-source context, verifies, assesses risk, plans evacuation, and
explains every decision it makes.

---

## ✨ What makes this different from a plain object detector

A naive system runs YOLO on a webcam and fires an alert on any positive
detection. **AeroPlan-Agent orchestrates 7 cooperating AI agents** (via
**LangGraph**) that monitor, detect, cross-verify against weather and
satellite data, score risk, map the terrain, plan an evacuation route, and
produce a human-readable explanation — before any alert is ever raised.

```
Monitoring → Vision Analysis → Verification → Risk Assessment →
Geospatial Intelligence → Emergency Planning → Explainable AI → Alerts
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for full diagrams
(architecture, LangGraph workflow, sequence, ER, agent-communication).

## 🧠 The 7 Agents

| # | Agent | Role |
|---|---|---|
| 1 | **Monitoring Agent** | Pulls webcam/upload frames, live weather, satellite context |
| 2 | **Vision Analysis Agent** | RT-DETR / YOLOv11 detection: fire, smoke, flood, accidents, collapsed buildings, blocked roads, crowds |
| 3 | **Verification Agent** | Cross-checks vision output against weather + NASA FIRMS satellite hotspots to rule out false alarms |
| 4 | **Risk Assessment Agent** | Computes severity (Low/Medium/High/Critical), risk score, affected area & population |
| 5 | **Geospatial Intelligence Agent** | OSMnx-powered lookup of hospitals, fire/police stations, safe zones, blocked roads |
| 6 | **Emergency Planning Agent** | Dijkstra + A* evacuation routing, shelter selection, dispatch recommendations |
| 7 | **Explainable AI Agent** | Produces the full auditable reasoning chain + human-readable narrative |

## 🗂️ Project Structure

```
aeroplan-agent/
├── backend/
│   ├── agents/          # 7 LangGraph agent nodes + graph.py orchestration
│   ├── api/              # FastAPI routers
│   ├── core/              # config, database session
│   ├── ml/                 # YOLOv11/RT-DETR detector + heuristic fallback
│   ├── models/              # SQLAlchemy ORM + Pydantic schemas
│   ├── services/              # weather, satellite, OSM, routing, alerts
│   ├── utils/                   # image I/O, logging
│   └── main.py                   # FastAPI entrypoint
├── dashboard/
│   └── app.py                      # Streamlit unified control room
├── database/
│   └── schema.sql                   # reference PostgreSQL DDL
├── datasets/
│   └── README.md                     # dataset sources + fine-tuning guide
├── docs/
│   ├── ARCHITECTURE.md                # all diagrams (mermaid)
│   ├── INSTALLATION.md
│   ├── DEPLOYMENT.md
│   └── API.md
├── tests/
│   └── test_agents.py
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.dashboard
├── requirements.txt
└── .env.example
```

## 🚀 Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env               # fill in API keys (all optional — has fallbacks)

# Terminal 1
uvicorn backend.main:app --reload --port 8000

# Terminal 2
streamlit run dashboard/app.py
```

Or with Docker: `docker compose up --build`. Full details in
[`docs/INSTALLATION.md`](docs/INSTALLATION.md) and
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

**Note:** the project runs end-to-end out of the box even with zero API
keys configured — every external integration (weather, satellite, LLM
narrative, fine-tuned vision model) has a documented graceful fallback so
grading/demo is never blocked by missing credentials.

## 🖥️ Dashboard

Streamlit unified control room with tabs for Live Monitoring, Detection,
Satellite View, Weather, Risk Heatmap, Evacuation Route Map (Folium),
AI Reasoning, Incident Timeline & Decision Logs, and simulated Emergency
Alerts.

## 📡 Data Sources

Webcam · Uploaded media · Sentinel-2 / NASA FIRMS · OpenWeatherMap ·
OpenStreetMap (OSMnx). See [`datasets/README.md`](datasets/README.md) for
training-data sources (Roboflow, Kaggle) and the YOLOv11/RT-DETR
fine-tuning command.

## ⚠️ Important scope note

All emergency-service notifications (Police / Fire / Ambulance / NDRF via
SMS, Email, Dashboard popup, Voice alert) are **simulated only**
(`backend/services/alert_service.py`). This project never contacts real
emergency services.

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📄 Further documentation

- [Architecture & Diagrams](docs/ARCHITECTURE.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Reference](docs/API.md)
- [Datasets & Fine-tuning](datasets/README.md)

## 🔮 Future Scope

- Real-time video-stream inference (vs. single-frame polling) with temporal smoothing
- Multi-camera fusion & sensor triangulation for precise incident geolocation
- Federated learning across municipal camera networks for privacy-preserving model improvement
- Integration with official emergency-dispatch CAD systems (requires formal agreements — out of current scope)
- Reinforcement-learning-based dynamic re-routing as new road-blockage data streams in
- Mobile app for citizen-reported incident corroboration
