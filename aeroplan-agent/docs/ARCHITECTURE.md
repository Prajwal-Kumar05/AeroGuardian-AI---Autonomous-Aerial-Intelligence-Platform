# AeroPlan-Agent — Architecture & Diagrams

## 1. System Architecture

```mermaid
flowchart TB
    subgraph Sources["Information Sources"]
        WC[Live Webcam / CCTV]
        UP[Uploaded Images & Videos]
        SAT[Satellite: Sentinel-2 / NASA FIRMS]
        WX[OpenWeatherMap API]
        OSM[OpenStreetMap / OSMnx]
    end

    subgraph Backend["FastAPI Backend"]
        API[REST API Layer]
        subgraph Agents["LangGraph Multi-Agent Orchestration"]
            A1[1. Monitoring Agent]
            A2[2. Vision Analysis Agent<br/>RT-DETR / YOLOv11]
            A3[3. Verification Agent]
            A4[4. Risk Assessment Agent]
            A5[5. Geospatial Intelligence Agent]
            A6[6. Emergency Planning Agent]
            A7[7. Explainable AI Agent]
            AL[Alert Dispatcher<br/>SIMULATED]
        end
        DB[(PostgreSQL / SQLite)]
    end

    subgraph Frontend["Streamlit Dashboard"]
        D1[Live Monitoring]
        D2[Detection View]
        D3[Risk & Severity]
        D4[Evacuation Map]
        D5[AI Reasoning]
        D6[Timeline & Logs]
        D7[Alerts]
    end

    WC --> A1
    UP --> A1
    SAT --> A1
    WX --> A1
    A1 --> A2 --> A3
    A3 -- true emergency --> A4 --> A5 --> A6 --> A7 --> AL
    A3 -- false alarm --> A7
    OSM --> A5
    OSM --> A6
    Agents --> DB
    API --> Agents
    DB --> Frontend
    API --> Frontend
```

## 2. Multi-Agent Workflow (LangGraph)

```mermaid
flowchart LR
    START([Start]) --> M[Monitoring Agent]
    M --> V[Vision Analysis Agent]
    V --> VER{Verification Agent}
    VER -- is_true_emergency = True --> R[Risk Assessment Agent]
    VER -- is_true_emergency = False --> X[Explainable AI Agent]
    R --> G[Geospatial Intelligence Agent]
    G --> P[Emergency Planning Agent]
    P --> X
    X --> AL[Alert Dispatch - Simulated]
    AL --> END([End])
```

## 3. Sequence Diagram — Single Pipeline Run

```mermaid
sequenceDiagram
    participant U as User / Dashboard
    participant API as FastAPI
    participant Mon as Monitoring Agent
    participant Vis as Vision Agent
    participant Ver as Verification Agent
    participant Risk as Risk Agent
    participant Geo as Geospatial Agent
    participant Plan as Planning Agent
    participant XAI as Explainable AI Agent
    participant Alert as Alert Service
    participant DB as Database

    U->>API: POST /api/emergency/run {lat, lon, source}
    API->>Mon: invoke(state)
    Mon->>Mon: capture frame + fetch weather + satellite context
    Mon->>Vis: state
    Vis->>Vis: run RT-DETR/YOLOv11 detection
    Vis->>Ver: state + detections
    Ver->>Ver: cross-verify vs weather/satellite/history
    alt True Emergency
        Ver->>Risk: state
        Risk->>Risk: compute severity + risk score
        Risk->>Geo: state
        Geo->>Geo: query OSM for hospitals/stations/safe zones
        Geo->>Plan: state
        Plan->>Plan: compute Dijkstra/A* evacuation routes
        Plan->>XAI: state
    else False Alarm
        Ver->>XAI: state
    end
    XAI->>XAI: build reasoning chain + explanation
    XAI->>Alert: state
    Alert->>Alert: simulate SMS/Email/Voice/Dashboard alerts
    Alert->>DB: persist emergency, detections, routes, alerts, logs
    Alert->>API: final state
    API->>U: EmergencyOut + reasoning_chain + alerts
```

## 4. Database ER Diagram

```mermaid
erDiagram
    EMERGENCIES ||--o{ DETECTIONS : has
    EMERGENCIES ||--o{ ROUTES : has
    EMERGENCIES ||--o{ ALERTS : has
    EMERGENCIES ||--o{ AGENT_LOGS : has

    EMERGENCIES {
        string id PK
        string emergency_type
        string status
        float confidence
        string severity
        float risk_score
        float latitude
        float longitude
        float affected_area_m2
        int affected_population_estimate
        string source
        text reasoning
        datetime created_at
        datetime resolved_at
    }
    DETECTIONS {
        string id PK
        string emergency_id FK
        string label
        float confidence
        json bbox
        string frame_source
        datetime created_at
    }
    WEATHER_SNAPSHOTS {
        string id PK
        float latitude
        float longitude
        float temperature_c
        float humidity_pct
        float wind_speed_ms
        float rainfall_mm
        float visibility_m
        string condition
        json raw_payload
        datetime created_at
    }
    ROUTES {
        string id PK
        string emergency_id FK
        string route_type
        string algorithm
        float origin_lat
        float origin_lon
        string destination_name
        float destination_lat
        float destination_lon
        float distance_m
        json path_coordinates
        json blocked_roads_avoided
        datetime created_at
    }
    ALERTS {
        string id PK
        string emergency_id FK
        string channel
        string recipient_type
        text message
        bool simulated
        string status
        datetime created_at
    }
    AGENT_LOGS {
        string id PK
        string emergency_id FK
        string agent_name
        string action
        text input_summary
        text output_summary
        float duration_ms
        datetime created_at
    }
```

## 5. Agent Communication Diagram (Shared-State Blackboard)

```mermaid
flowchart TB
    subgraph State["AeroPlanState (shared TypedDict / blackboard)"]
        S1[latitude, longitude, source]
        S2[weather, satellite_context]
        S3[detections]
        S4[is_true_emergency, emergency_confidence, emergency_type]
        S5[severity, risk_score, affected_area_m2]
        S6[nearby_hospitals, safe_zones, blocked_roads]
        S7[primary_route, alternative_route, recommendations]
        S8[reasoning_chain, explanation]
        S9[alerts_dispatched, agent_logs]
    end

    MonitoringAgent -- writes --> S1 & S2
    VisionAgent -- reads --> S2
    VisionAgent -- writes --> S3
    VerificationAgent -- reads --> S2 & S3
    VerificationAgent -- writes --> S4
    RiskAgent -- reads --> S4
    RiskAgent -- writes --> S5
    GeospatialAgent -- reads --> S1 & S3
    GeospatialAgent -- writes --> S6
    PlanningAgent -- reads --> S5 & S6
    PlanningAgent -- writes --> S7
    ExplainableAgent -- reads --> S1 & S2 & S3 & S4 & S5 & S6 & S7
    ExplainableAgent -- writes --> S8
    AlertService -- reads --> S4 & S5
    AlertService -- writes --> S9
```

## 6. Risk Scoring Algorithm

```
base_score(emergency_type) ∈ {fire:55, flood:50, road_accident:45,
                               structural_collapse:65, obstruction:25, crowd_hazard:30}

score = base_score × emergency_confidence
score ×= wind_fire_multiplier(wind_speed)      # fire only, 1.0–1.6x
score ×= 1.25                                   # flood + rainfall > 15mm
score ×= (1 + min(log10(affected_area_m2+1)/20, 0.3))

severity = critical if score>=80
           high     if score>=55
           medium    if score>=30
           low       otherwise
```

## 7. Technology Stack Summary

| Layer | Technology |
|---|---|
| Multi-agent orchestration | LangGraph (StateGraph) |
| Vision model | YOLOv11 / RT-DETR (Ultralytics) + OpenCV heuristic fallback |
| Backend API | FastAPI + Pydantic |
| Database | PostgreSQL (SQLAlchemy ORM), auto-fallback to SQLite |
| Geospatial | OSMnx, NetworkX, GeoPandas, Shapely, Rasterio |
| Weather | OpenWeatherMap REST API |
| Satellite | NASA FIRMS, Sentinel Hub (Sentinel-2) |
| Frontend | Streamlit + Folium (Leaflet) + Plotly |
| Explainability | Structured reasoning chain + optional Claude LLM narrative |
| Deployment | Docker Compose (backend, dashboard, PostgreSQL) |
