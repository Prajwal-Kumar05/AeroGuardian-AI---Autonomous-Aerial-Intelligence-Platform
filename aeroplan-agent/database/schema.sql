-- AeroPlan-Agent :: PostgreSQL schema (reference DDL)
-- Auto-created at runtime by SQLAlchemy (backend/core/database.py::init_db),
-- provided here for documentation / manual provisioning / ER diagram source.

CREATE TABLE IF NOT EXISTS emergencies (
    id                              VARCHAR PRIMARY KEY,
    emergency_type                  VARCHAR NOT NULL,
    status                          VARCHAR DEFAULT 'verified',
    confidence                      FLOAT DEFAULT 0,
    severity                        VARCHAR DEFAULT 'low',
    risk_score                      FLOAT DEFAULT 0,
    latitude                        FLOAT,
    longitude                       FLOAT,
    affected_area_m2                FLOAT,
    affected_population_estimate    INTEGER,
    source                          VARCHAR DEFAULT 'webcam',
    reasoning                       TEXT,
    created_at                      TIMESTAMP DEFAULT NOW(),
    resolved_at                     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detections (
    id              VARCHAR PRIMARY KEY,
    emergency_id    VARCHAR REFERENCES emergencies(id) ON DELETE CASCADE,
    label           VARCHAR NOT NULL,
    confidence      FLOAT NOT NULL,
    bbox            JSONB,
    frame_source    VARCHAR DEFAULT 'webcam',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    id              VARCHAR PRIMARY KEY,
    latitude        FLOAT,
    longitude       FLOAT,
    temperature_c   FLOAT,
    humidity_pct    FLOAT,
    wind_speed_ms   FLOAT,
    rainfall_mm     FLOAT,
    visibility_m    FLOAT,
    condition       VARCHAR,
    raw_payload     JSONB,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS routes (
    id                      VARCHAR PRIMARY KEY,
    emergency_id            VARCHAR REFERENCES emergencies(id) ON DELETE CASCADE,
    route_type              VARCHAR DEFAULT 'primary',
    algorithm               VARCHAR DEFAULT 'dijkstra',
    origin_lat              FLOAT,
    origin_lon              FLOAT,
    destination_name        VARCHAR,
    destination_lat         FLOAT,
    destination_lon         FLOAT,
    distance_m              FLOAT,
    path_coordinates        JSONB,
    blocked_roads_avoided   JSONB,
    created_at              TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id              VARCHAR PRIMARY KEY,
    emergency_id    VARCHAR REFERENCES emergencies(id) ON DELETE CASCADE,
    channel         VARCHAR NOT NULL,
    recipient_type  VARCHAR NOT NULL,
    message         TEXT NOT NULL,
    simulated       BOOLEAN DEFAULT TRUE,
    status          VARCHAR DEFAULT 'sent',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id              VARCHAR PRIMARY KEY,
    emergency_id    VARCHAR REFERENCES emergencies(id) ON DELETE CASCADE,
    agent_name      VARCHAR NOT NULL,
    action          VARCHAR NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    duration_ms     FLOAT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emergencies_created_at ON emergencies(created_at);
CREATE INDEX IF NOT EXISTS idx_detections_emergency_id ON detections(emergency_id);
CREATE INDEX IF NOT EXISTS idx_routes_emergency_id ON routes(emergency_id);
CREATE INDEX IF NOT EXISTS idx_alerts_emergency_id ON alerts(emergency_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_emergency_id ON agent_logs(emergency_id);
