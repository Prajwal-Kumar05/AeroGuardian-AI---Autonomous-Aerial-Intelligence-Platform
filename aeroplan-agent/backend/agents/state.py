"""
AeroPlan-Agent :: Shared multi-agent state (LangGraph)

Every agent node reads from and writes to this single TypedDict, which is
threaded through the graph. This is the "shared memory / blackboard" the
agents reason over collaboratively.
"""
from typing import TypedDict, List, Dict, Any, Optional


class AeroPlanState(TypedDict, total=False):
    # --- inputs ---
    latitude: float
    longitude: float
    source: str                       # webcam | upload | satellite
    image_path: Optional[str]

    # --- Monitoring Agent outputs ---
    frame_available: bool
    weather: Dict[str, Any]
    satellite_context: Dict[str, Any]

    # --- Vision Analysis Agent outputs ---
    detections: List[Dict[str, Any]]

    # --- Verification Agent outputs ---
    is_true_emergency: bool
    emergency_confidence: float
    emergency_type: str
    verification_notes: List[str]

    # --- Risk Assessment Agent outputs ---
    severity: str                      # low | medium | high | critical
    risk_score: float
    affected_population_estimate: int
    affected_area_m2: float

    # --- Geospatial Intelligence Agent outputs ---
    nearby_hospitals: List[Dict[str, Any]]
    nearby_fire_stations: List[Dict[str, Any]]
    nearby_police_stations: List[Dict[str, Any]]
    safe_zones: List[Dict[str, Any]]
    blocked_roads: List[Any]

    # --- Emergency Planning Agent outputs ---
    primary_route: Dict[str, Any]
    alternative_route: Dict[str, Any]
    selected_shelter: Dict[str, Any]
    recommendations: List[str]
    dispatch_units: List[str]

    # --- Explainable AI Agent outputs ---
    reasoning_chain: List[Dict[str, Any]]
    explanation: str

    # --- Alerts ---
    alerts_dispatched: List[Dict[str, Any]]

    # --- bookkeeping ---
    agent_logs: List[Dict[str, Any]]
    emergency_id: Optional[str]
