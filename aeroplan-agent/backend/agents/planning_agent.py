"""
AeroPlan-Agent :: Emergency Planning Agent

Generates the evacuation route(s), selects the nearest viable shelter, and
produces concrete recommendations + dispatch-unit suggestions, using the
road network + amenities gathered by the Geospatial Agent.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.services import osm_service, routing_service
from backend.services.alert_service import DISPATCH_MATRIX

logger = logging.getLogger("aeroplan.agent.planning")


def planning_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()

    if not state.get("is_true_emergency"):
        _log(state, "EmergencyPlanningAgent", "skip", "false_alarm", "skipped", t0)
        return state

    lat, lon = state["latitude"], state["longitude"]
    shelters = state.get("safe_zones", [])
    dispatch_units = DISPATCH_MATRIX.get(state["emergency_type"], ["police"])
    recommendations = [f"Dispatch: {u.replace('_', ' ').title()}" for u in dispatch_units]

    if state["severity"] in ("high", "critical"):
        recommendations.append("Cordon off a 200m radius safety perimeter around the incident zone.")
    if state["emergency_type"] == "fire":
        recommendations.append("Advise downwind residents to evacuate; high wind may accelerate spread.")
    if state["emergency_type"] == "flood":
        recommendations.append("Restrict vehicle access to low-lying roads near the incident.")

    plan = None
    if shelters:
        try:
            G = osm_service.get_road_network(lat, lon)
            plan = routing_service.plan_evacuation(
                G, origin=(lat, lon), shelters=shelters,
                blocked_coords=state.get("blocked_roads", []),
            )
        except Exception as e:
            logger.error(f"Planning Agent: routing failed ({e}).")

    if plan:
        state["selected_shelter"] = plan["shelter"]
        state["primary_route"] = plan["primary"]
        state["alternative_route"] = plan["alternative"]
        recommendations.append(f"Primary evacuation route -> {plan['shelter']['name']} "
                                f"({plan['primary']['distance_m']} m via Dijkstra).")
    else:
        state["selected_shelter"] = {}
        state["primary_route"] = {}
        state["alternative_route"] = {}
        recommendations.append("No safe shelter/route could be computed automatically — "
                                "manual coordination advised.")

    state["dispatch_units"] = dispatch_units
    state["recommendations"] = recommendations

    _log(state, "EmergencyPlanningAgent", "plan",
         f"{len(shelters)} candidate shelters", f"{len(recommendations)} recommendations", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
