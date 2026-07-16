"""
AeroPlan-Agent :: Geospatial Intelligence Agent

Uses OpenStreetMap (via OSMnx) to enumerate nearby critical infrastructure
and candidate safe zones around the emergency location. Skipped entirely
for false alarms to save time/bandwidth.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.services import osm_service

logger = logging.getLogger("aeroplan.agent.geospatial")


def geospatial_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()

    if not state.get("is_true_emergency"):
        _log(state, "GeospatialIntelligenceAgent", "skip", "false_alarm", "skipped", t0)
        return state

    lat, lon = state["latitude"], state["longitude"]

    try:
        state["nearby_hospitals"] = osm_service.find_nearby_amenities(lat, lon, "hospital")
        state["nearby_fire_stations"] = osm_service.find_nearby_amenities(lat, lon, "fire_station")
        state["nearby_police_stations"] = osm_service.find_nearby_amenities(lat, lon, "police")
        state["safe_zones"] = osm_service.identify_safe_zones(lat, lon)
    except Exception as e:
        logger.error(f"Geospatial Agent: OSM lookup failed ({e}); continuing with empty results.")
        state.setdefault("nearby_hospitals", [])
        state.setdefault("nearby_fire_stations", [])
        state.setdefault("nearby_police_stations", [])
        state.setdefault("safe_zones", [])

    # Blocked roads inferred from vision detections of type obstruction
    blocked = []
    for d in state.get("detections", []):
        if d["label"] in ("blocked_road", "fallen_tree", "collapsed_building", "road_accident"):
            blocked.append((lat, lon))  # coarse: treat incident point as blocked node
    state["blocked_roads"] = blocked

    _log(state, "GeospatialIntelligenceAgent", "map_context",
         f"({lat:.4f},{lon:.4f})",
         f"hospitals={len(state['nearby_hospitals'])}, safe_zones={len(state['safe_zones'])}", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
