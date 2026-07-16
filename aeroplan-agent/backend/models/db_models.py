"""
AeroPlan-Agent :: ORM Models
Tables: emergencies, detections, weather_snapshots, routes, alerts, agent_logs
"""
import uuid
import datetime as dt
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Emergency(Base):
    __tablename__ = "emergencies"

    id = Column(String, primary_key=True, default=gen_uuid)
    emergency_type = Column(String, nullable=False)          # fire, flood, accident, ...
    status = Column(String, default="verified")               # verified, false_alarm, resolved
    confidence = Column(Float, default=0.0)
    severity = Column(String, default="low")                  # low/medium/high/critical
    risk_score = Column(Float, default=0.0)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    affected_area_m2 = Column(Float, nullable=True)
    affected_population_estimate = Column(Integer, nullable=True)
    source = Column(String, default="webcam")                 # webcam, upload, satellite
    reasoning = Column(Text, nullable=True)                    # explainable-AI narrative
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    detections = relationship("Detection", back_populates="emergency", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="emergency", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="emergency", cascade="all, delete-orphan")
    logs = relationship("AgentLog", back_populates="emergency", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(String, primary_key=True, default=gen_uuid)
    emergency_id = Column(String, ForeignKey("emergencies.id"))
    label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox = Column(JSON, nullable=True)                         # [x1,y1,x2,y2]
    frame_source = Column(String, default="webcam")
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    emergency = relationship("Emergency", back_populates="detections")


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id = Column(String, primary_key=True, default=gen_uuid)
    latitude = Column(Float)
    longitude = Column(Float)
    temperature_c = Column(Float)
    humidity_pct = Column(Float)
    wind_speed_ms = Column(Float)
    rainfall_mm = Column(Float, nullable=True)
    visibility_m = Column(Float, nullable=True)
    condition = Column(String, nullable=True)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)


class Route(Base):
    __tablename__ = "routes"

    id = Column(String, primary_key=True, default=gen_uuid)
    emergency_id = Column(String, ForeignKey("emergencies.id"))
    route_type = Column(String, default="primary")             # primary, alternative
    algorithm = Column(String, default="dijkstra")              # dijkstra, astar
    origin_lat = Column(Float)
    origin_lon = Column(Float)
    destination_name = Column(String)
    destination_lat = Column(Float)
    destination_lon = Column(Float)
    distance_m = Column(Float, nullable=True)
    path_coordinates = Column(JSON, nullable=True)              # list of [lat, lon]
    blocked_roads_avoided = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    emergency = relationship("Emergency", back_populates="routes")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=gen_uuid)
    emergency_id = Column(String, ForeignKey("emergencies.id"))
    channel = Column(String, nullable=False)                    # sms/email/dashboard/voice
    recipient_type = Column(String, nullable=False)             # police/fire/ambulance/ndrf/public
    message = Column(Text, nullable=False)
    simulated = Column(Boolean, default=True)
    status = Column(String, default="sent")
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    emergency = relationship("Emergency", back_populates="alerts")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    emergency_id = Column(String, ForeignKey("emergencies.id"), nullable=True)
    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    emergency = relationship("Emergency", back_populates="logs")
