"""
AeroPlan-Agent :: LangGraph Orchestration

Wires the 7 agents into a directed graph:

    Monitoring -> Vision -> Verification --(true)--> Risk -> Geospatial
                                          |--(false)-> End (log false alarm)
    Risk -> Geospatial -> Planning -> Explainable -> Alerts -> End

Conditional routing at Verification means false alarms short-circuit the
graph immediately after explanation, saving compute (no route-planning or
dispatch for non-events) while still logging full reasoning for audit.
"""
import logging
from langgraph.graph import StateGraph, END

from backend.agents.state import AeroPlanState
from backend.agents.monitoring_agent import monitoring_agent
from backend.agents.vision_agent import vision_agent
from backend.agents.verification_agent import verification_agent
from backend.agents.risk_agent import risk_agent
from backend.agents.geospatial_agent import geospatial_agent
from backend.agents.planning_agent import planning_agent
from backend.agents.explainable_agent import explainable_agent
from backend.services.alert_service import dispatch

logger = logging.getLogger("aeroplan.graph")


def alert_node(state: AeroPlanState) -> AeroPlanState:
    if not state.get("is_true_emergency"):
        state["alerts_dispatched"] = []
        return state
    emergency = {
        "emergency_type": state["emergency_type"],
        "severity": state["severity"],
        "confidence": state["emergency_confidence"],
        "latitude": state["latitude"],
        "longitude": state["longitude"],
    }
    state["alerts_dispatched"] = dispatch(emergency)
    return state


def _route_after_verification(state: AeroPlanState) -> str:
    return "risk" if state.get("is_true_emergency") else "explain"


def build_graph():
    graph = StateGraph(AeroPlanState)

    graph.add_node("monitor", monitoring_agent)
    graph.add_node("vision", vision_agent)
    graph.add_node("verify", verification_agent)
    graph.add_node("risk", risk_agent)
    graph.add_node("geospatial", geospatial_agent)
    graph.add_node("plan", planning_agent)
    graph.add_node("explain", explainable_agent)
    graph.add_node("alert", alert_node)

    graph.set_entry_point("monitor")
    graph.add_edge("monitor", "vision")
    graph.add_edge("vision", "verify")
    graph.add_conditional_edges(
        "verify", _route_after_verification, {"risk": "risk", "explain": "explain"}
    )
    graph.add_edge("risk", "geospatial")
    graph.add_edge("geospatial", "plan")
    graph.add_edge("plan", "explain")
    graph.add_edge("explain", "alert")
    graph.add_edge("alert", END)

    return graph.compile()


aeroplan_graph = build_graph()


def run_pipeline(latitude: float, longitude: float, source: str = "webcam", image_path: str = None) -> AeroPlanState:
    initial_state: AeroPlanState = {
        "latitude": latitude,
        "longitude": longitude,
        "source": source,
        "image_path": image_path,
        "agent_logs": [],
    }
    final_state = aeroplan_graph.invoke(initial_state)
    return final_state
