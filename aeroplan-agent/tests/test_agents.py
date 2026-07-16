"""
AeroPlan-Agent :: Unit & integration tests
Run: pytest tests/ -v
"""
import numpy as np
from backend.agents.state import AeroPlanState
from backend.agents.verification_agent import verification_agent
from backend.agents.risk_agent import risk_agent
from backend.ml import detector


def test_verification_rejects_low_confidence():
    state: AeroPlanState = {
        "detections": [{"label": "fire", "confidence": 0.2, "emergency_type": "fire", "bbox": [0, 0, 10, 10]}],
        "weather": {"humidity_pct": 50, "wind_speed_ms": 2, "rainfall_mm": 0},
        "satellite_context": {"firms": {"available": False}},
        "agent_logs": [],
    }
    out = verification_agent(state)
    assert out["is_true_emergency"] is False


def test_verification_accepts_corroborated_fire():
    state: AeroPlanState = {
        "detections": [{"label": "fire", "confidence": 0.6, "emergency_type": "fire", "bbox": [0, 0, 50, 50]}],
        "weather": {"humidity_pct": 20, "wind_speed_ms": 8, "rainfall_mm": 0},
        "satellite_context": {"firms": {"available": True, "hotspot_count": 3}},
        "agent_logs": [],
    }
    out = verification_agent(state)
    assert out["is_true_emergency"] is True
    assert out["emergency_confidence"] > 0.6


def test_risk_agent_scales_with_wind_for_fire():
    base_state: AeroPlanState = {
        "is_true_emergency": True,
        "emergency_type": "fire",
        "emergency_confidence": 0.8,
        "detections": [{"label": "fire", "affected_area_m2": 500}],
        "weather": {"wind_speed_ms": 2},
        "agent_logs": [],
    }
    low_wind = risk_agent(dict(base_state))

    high_wind_state = dict(base_state)
    high_wind_state["weather"] = {"wind_speed_ms": 14}
    high_wind = risk_agent(high_wind_state)

    assert high_wind["risk_score"] > low_wind["risk_score"]


def test_heuristic_detector_runs_on_blank_image():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    dets = detector._heuristic_fire_smoke_flood(img)
    assert isinstance(dets, list)


def test_false_alarm_skips_severity():
    state: AeroPlanState = {
        "is_true_emergency": False,
        "detections": [],
        "agent_logs": [],
    }
    out = risk_agent(state)
    assert out["severity"] == "none"
    assert out["risk_score"] == 0.0
