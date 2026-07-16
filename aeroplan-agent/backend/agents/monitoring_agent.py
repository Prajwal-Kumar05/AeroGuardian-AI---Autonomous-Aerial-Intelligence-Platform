"""
AeroPlan-Agent :: Monitoring Agent

Continuously (or on-demand, per pipeline run) gathers raw signal from all
information sources: webcam / uploaded media frame, weather, and satellite
context. This agent performs NO reasoning — it is purely a data-acquisition
node feeding the rest of the graph.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.services import weather_service, satellite_service
from backend.utils.image_utils import load_image, capture_webcam_frame

logger = logging.getLogger("aeroplan.agent.monitoring")


def monitoring_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()
    lat, lon = state["latitude"], state["longitude"]

    # 1. Acquire frame (webcam / uploaded / satellite placeholder)
    frame_available = False
    try:
        if state.get("source") == "webcam":
            frame = capture_webcam_frame()
            state["_frame"] = frame  # not persisted to DB; internal only
            frame_available = True
        elif state.get("image_path"):
            frame = load_image(state["image_path"])
            state["_frame"] = frame
            frame_available = True
    except Exception as e:
        logger.warning(f"Monitoring Agent: frame capture failed ({e}); vision agent will skip.")

    # 2. Live weather
    state["weather"] = weather_service.get_current_weather(lat, lon)

    # 3. Satellite context (used later for verification only)
    state["satellite_context"] = {
        "firms": satellite_service.get_active_fire_hotspots(lat, lon),
    }

    state["frame_available"] = frame_available
    _log(state, "MonitoringAgent", "gather_signals",
         f"source={state.get('source')}", f"frame={frame_available}, weather_ok=True", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
