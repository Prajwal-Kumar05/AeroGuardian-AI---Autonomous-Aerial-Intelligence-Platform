"""
AeroPlan-Agent :: Explainable AI Agent

Synthesizes the full reasoning chain (Monitoring -> Vision -> Verification
-> Risk -> Geospatial -> Planning) into a human-readable explanation, so
every decision the system makes is auditable by first responders.

If ANTHROPIC_API_KEY is configured, uses Claude to produce a fluent natural
-language narrative from the structured reasoning chain. Otherwise falls
back to a deterministic template — the system is fully explainable either
way, the LLM only improves readability.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.core.config import get_settings

logger = logging.getLogger("aeroplan.agent.xai")
settings = get_settings()


def _build_reasoning_chain(state: AeroPlanState) -> list:
    chain = []
    chain.append({
        "step": "Monitoring",
        "detail": f"Weather sampled: {state.get('weather', {})}",
    })
    chain.append({
        "step": "Vision Analysis",
        "detail": f"Detections: {[(d['label'], d['confidence']) for d in state.get('detections', [])]}",
    })
    chain.append({
        "step": "Verification",
        "detail": "; ".join(state.get("verification_notes", [])) or "No verification notes.",
    })
    if state.get("is_true_emergency"):
        chain.append({
            "step": "Risk Assessment",
            "detail": f"Severity={state.get('severity')}, risk_score={state.get('risk_score')}, "
                      f"affected_area={state.get('affected_area_m2')} m^2, "
                      f"est_population={state.get('affected_population_estimate')}",
        })
        chain.append({
            "step": "Geospatial Intelligence",
            "detail": f"{len(state.get('nearby_hospitals', []))} hospitals, "
                      f"{len(state.get('nearby_fire_stations', []))} fire stations, "
                      f"{len(state.get('safe_zones', []))} candidate safe zones identified.",
        })
        chain.append({
            "step": "Emergency Planning",
            "detail": "; ".join(state.get("recommendations", [])),
        })
    return chain


def _template_explanation(state: AeroPlanState) -> str:
    if not state.get("is_true_emergency"):
        return (
            "No emergency was confirmed. Vision cues (if any) fell below the "
            "confidence threshold or were contradicted by weather/satellite "
            "context, so this was classified as a false alarm."
        )
    return (
        f"A {state['emergency_type'].replace('_',' ')} was detected with "
        f"{state['emergency_confidence']*100:.0f}% confidence, corroborated by "
        f"contextual weather and satellite signals (see verification notes). "
        f"Given the estimated affected area of {state.get('affected_area_m2', 0):.0f} m^2 "
        f"and current weather conditions, the system assessed a risk score of "
        f"{state.get('risk_score')}/100, classified as {state.get('severity','').upper()} severity. "
        f"Based on nearby infrastructure, the system recommends dispatching "
        f"{', '.join(u.replace('_',' ') for u in state.get('dispatch_units', []))} "
        f"and evacuating toward "
        f"{state.get('selected_shelter', {}).get('name', 'the nearest identified safe zone')}."
    )


def _llm_explanation(state: AeroPlanState, chain: list) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = (
            "You are the Explainable-AI module of an emergency-response system. "
            "Given this structured multi-agent reasoning chain, write a concise "
            "(4-6 sentence) human-readable explanation for a first responder, "
            "covering: what was detected, why it was verified as real (or ruled out), "
            "why the severity was assigned, and why the recommended action follows. "
            f"Reasoning chain: {chain}"
        )
        resp = client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if hasattr(b, "text"))
    except Exception as e:
        logger.warning(f"LLM explanation unavailable ({e}); using template explanation.")
        return _template_explanation(state)


def explainable_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()
    chain = _build_reasoning_chain(state)
    state["reasoning_chain"] = chain

    if settings.ANTHROPIC_API_KEY:
        state["explanation"] = _llm_explanation(state, chain)
    else:
        state["explanation"] = _template_explanation(state)

    _log(state, "ExplainableAIAgent", "explain",
         f"{len(chain)} reasoning steps", "explanation generated", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
