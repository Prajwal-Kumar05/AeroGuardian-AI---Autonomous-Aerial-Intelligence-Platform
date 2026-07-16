"""
AeroPlan-Agent :: Vision Analysis Agent

Runs the fine-tuned RT-DETR / YOLOv11 disaster-detection model (with
heuristic fallback) on the frame acquired by the Monitoring Agent.
"""
import time
import logging
from backend.agents.state import AeroPlanState
from backend.ml import detector
from backend.ml.labels import LABEL_TO_EMERGENCY_TYPE

logger = logging.getLogger("aeroplan.agent.vision")


def vision_agent(state: AeroPlanState) -> AeroPlanState:
    t0 = time.time()
    frame = state.get("_frame")

    if frame is None:
        state["detections"] = []
        _log(state, "VisionAnalysisAgent", "detect_objects", "no_frame", "0 detections", t0)
        return state

    dets = detector.detect(frame)
    for d in dets:
        d["affected_area_m2"] = detector.estimate_affected_area(d["bbox"], frame.shape)
        d["emergency_type"] = LABEL_TO_EMERGENCY_TYPE.get(d["label"], d["label"])

    state["detections"] = dets
    _log(state, "VisionAnalysisAgent", "detect_objects",
         f"frame_shape={frame.shape}", f"{len(dets)} detections: {[d['label'] for d in dets]}", t0)
    return state


def _log(state, agent, action, inp, out, t0):
    logs = state.setdefault("agent_logs", [])
    logs.append({
        "agent_name": agent, "action": action,
        "input_summary": inp, "output_summary": out,
        "duration_ms": round((time.time() - t0) * 1000, 1),
    })
