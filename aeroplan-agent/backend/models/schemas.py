"""
AeroPlan-Agent :: Pydantic request/response schemas
"""
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class WeatherOut(BaseModel):
    temperature_c: float
    humidity_pct: float
    wind_speed_ms: float
    rainfall_mm: Optional[float] = 0.0
    visibility_m: Optional[float] = 10000.0
    condition: Optional[str] = "clear"


class DetectionOut(BaseModel):
    label: str
    confidence: float
    bbox: List[float]


class RouteOut(BaseModel):
    route_type: str
    algorithm: str
    destination_name: str
    distance_m: Optional[float]
    path_coordinates: Optional[List[List[float]]]


class EmergencyRunRequest(BaseModel):
    latitude: float
    longitude: float
    image_path: Optional[str] = None          # path to uploaded / captured frame
    source: str = "webcam"                     # webcam | upload | satellite


class EmergencyOut(BaseModel):
    id: str
    emergency_type: str
    status: str
    confidence: float
    severity: str
    risk_score: float
    latitude: Optional[float]
    longitude: Optional[float]
    affected_area_m2: Optional[float]
    affected_population_estimate: Optional[int]
    reasoning: Optional[str]
    detections: List[DetectionOut] = []
    routes: List[RouteOut] = []

    class Config:
        from_attributes = True


class AgentGraphResult(BaseModel):
    emergency: Optional[EmergencyOut]
    reasoning_chain: List[Dict[str, Any]]
    alerts_dispatched: List[Dict[str, Any]]
