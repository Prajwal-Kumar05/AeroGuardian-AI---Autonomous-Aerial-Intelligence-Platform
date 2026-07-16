"""
AeroPlan-Agent :: Risk Assessment Agent

Combines verified emergency type/confidence, affected area, weather
multipliers, and a crude population-density proxy into a single 0-100 risk
score, mapped to Low/Medium/High/Critical severity tiers used across the
Planning, Alerting, and Dashboard layers.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.services.weather_service import wind_fire_risk_multiplier

logger = logging.getLogger("aeroplan.agent.risk")

# crude population-density proxy (people per km^2) — replace with real
# census/gridded-population data (e.g. WorldPop) for production use.
DEFAULT_POPULATION_DENSITY = 4500


def risk_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()

    if not state.get("is_true_emergency"):
        state["severity"] = "none"
        state["risk_score"] = 0.0
        state["affected_population_estimate"] = 0
        state["affected_area_m2"] = 0.0
        _log(state, "RiskAssessmentAgent", "assess", "false_alarm", "risk=0", t0)
        return state

    emergency_type = state["emergency_type"]
    confidence = state["emergency_confidence"]
    detections = state.get("detections", [])
    area_m2 = max((d.get("affected_area_m2", 0) for d in detections), default=0.0)

    base_score = {
        "fire": 55, "flood": 50, "road_accident": 45,
        "structural_collapse": 65, "obstruction": 25, "crowd_hazard": 30,
    }.get(emergency_type, 35)

    score = base_score * confidence

    # Weather amplification
    weather = state.get("weather", {})
    if emergency_type == "fire":
        score *= wind_fire_risk_multiplier(weather.get("wind_speed_ms", 0))
    if emergency_type == "flood" and weather.get("rainfall_mm", 0) > 15:
        score *= 1.25

    # Area amplification (log-scaled so it doesn't dominate)
    import math
    if area_m2 > 0:
        score *= 1 + min(math.log10(area_m2 + 1) / 20, 0.3)

    score = round(min(score, 100), 1)

    if score >= 80:
        severity = "critical"
    elif score >= 55:
        severity = "high"
    elif score >= 30:
        severity = "medium"
    else:
        severity = "low"

    affected_population = round((area_m2 / 1_000_000) * DEFAULT_POPULATION_DENSITY)

    state["risk_score"] = score
    state["severity"] = severity
    state["affected_area_m2"] = area_m2
    state["affected_population_estimate"] = max(affected_population, 1)

    _log(state, "RiskAssessmentAgent", "assess",
         f"{emergency_type}@{confidence}", f"score={score}, severity={severity}", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
