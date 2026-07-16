"""
AeroPlan-Agent :: Verification Agent

Cross-verifies raw vision detections against weather, satellite context,
and simple historical/contextual plausibility rules BEFORE anything is
declared a true emergency. This is what separates AeroPlan-Agent from a
naive "detect and alert" system — it actively tries to rule out false
alarms (e.g., a sunset misread as fire, a shadow misread as flood).
"""
import time
import logging
from collections import Counter
from backend.agents.state import AeroPlanState

logger = logging.getLogger("aeroplan.agent.verification")

MIN_VISION_CONFIDENCE = 0.45


def verification_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()
    detections = state.get("detections", [])
    notes = []

    if not detections:
        state["is_true_emergency"] = False
        state["emergency_confidence"] = 0.0
        state["emergency_type"] = "none"
        state["verification_notes"] = ["No emergency-relevant objects detected in frame."]
        _log(state, "VerificationAgent", "verify", "0 detections", "false_alarm", t0)
        return state

    # Pick the dominant emergency-relevant detection (highest confidence, non-benign class)
    relevant = [d for d in detections if d["label"] not in ("person", "vehicle", "crowd")]
    candidate_pool = relevant if relevant else detections
    top = max(candidate_pool, key=lambda d: d["confidence"])

    base_conf = top["confidence"]
    notes.append(f"Top vision cue: {top['label']} @ {base_conf:.2f} confidence.")

    # --- Cross-check 1: minimum vision confidence gate ---
    if base_conf < MIN_VISION_CONFIDENCE:
        state["is_true_emergency"] = False
        state["emergency_confidence"] = base_conf
        state["emergency_type"] = top["emergency_type"]
        state["verification_notes"] = notes + ["Below minimum confidence threshold -> flagged as false alarm."]
        _log(state, "VerificationAgent", "verify", top["label"], "false_alarm (low_conf)", t0)
        return state

    boost = 0.0

    # --- Cross-check 2: weather plausibility ---
    weather = state.get("weather", {})
    if top["label"] in ("fire", "smoke"):
        if weather.get("humidity_pct", 50) < 35 and weather.get("wind_speed_ms", 0) > 4:
            boost += 0.08
            notes.append("Low humidity + moderate/high wind supports fire plausibility (+0.08).")
        if weather.get("rainfall_mm", 0) > 5:
            boost -= 0.15
            notes.append("Active rainfall reduces fire plausibility (-0.15).")
    if top["label"] == "flood":
        if weather.get("rainfall_mm", 0) > 10:
            boost += 0.1
            notes.append("Recent heavy rainfall supports flood plausibility (+0.10).")

    # --- Cross-check 3: satellite corroboration (fire only) ---
    if top["label"] in ("fire", "smoke"):
        firms = state.get("satellite_context", {}).get("firms", {})
        if firms.get("available") and firms.get("hotspot_count", 0) > 0:
            boost += 0.15
            notes.append(f"NASA FIRMS confirms {firms['hotspot_count']} active thermal hotspot(s) nearby (+0.15).")
        elif firms.get("available"):
            boost -= 0.05
            notes.append("NASA FIRMS shows no active hotspots nearby (-0.05).")

    # --- Cross-check 4: multi-frame / multi-class agreement ---
    labels = Counter(d["label"] for d in detections)
    if labels[top["label"]] > 1:
        boost += 0.05
        notes.append(f"Multiple ({labels[top['label']]}) consistent detections in-frame (+0.05).")

    final_conf = max(0.0, min(base_conf + boost, 0.99))
    is_true = final_conf >= MIN_VISION_CONFIDENCE

    state["is_true_emergency"] = is_true
    state["emergency_confidence"] = round(final_conf, 2)
    state["emergency_type"] = top["emergency_type"]
    state["verification_notes"] = notes

    _log(state, "VerificationAgent", "verify",
         f"{top['label']}@{base_conf:.2f}", f"true_emergency={is_true}, conf={final_conf:.2f}", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
