"""
AeroPlan-Agent :: Vision Detector

Wraps Ultralytics YOLOv11 / RT-DETR for disaster-object detection.

Fine-tuning instructions (see docs/DATASETS.md):
    yolo detect train data=disaster.yaml model=yolo11n.pt epochs=100 imgsz=640
    # or for RT-DETR:
    yolo detect train data=disaster.yaml model=rtdetr-l.pt epochs=100 imgsz=640

If no fine-tuned checkpoint is present at settings.VISION_MODEL_PATH, the
detector degrades gracefully to a lightweight OpenCV heuristic analyzer
(color/motion/texture based) so the whole pipeline remains runnable for
demos and grading without requiring GPU training beforehand.
"""
import os
import logging
from typing import List, Dict
import numpy as np
import cv2

from backend.core.config import get_settings
from backend.ml.labels import DISASTER_CLASSES

logger = logging.getLogger("aeroplan.vision")
settings = get_settings()

_model = None
_model_kind = None  # "yolo" | "heuristic"


def _try_load_ultralytics_model():
    global _model, _model_kind
    try:
        from ultralytics import YOLO
        path = settings.VISION_MODEL_PATH
        if os.path.exists(path):
            _model = YOLO(path)
            _model_kind = "yolo"
            logger.info(f"Loaded fine-tuned disaster model from {path}")
        else:
            # fall back to a generic pretrained checkpoint (COCO classes) purely
            # to keep the pipeline end-to-end functional pre-fine-tuning
            _model = YOLO(settings.VISION_MODEL_FALLBACK)
            _model_kind = "yolo_generic"
            logger.warning(
                "No fine-tuned disaster checkpoint found — using generic "
                "pretrained weights. Detections will be limited to COCO "
                "classes (person, car, truck, etc). Fine-tune per docs/DATASETS.md."
            )
    except Exception as e:
        logger.warning(f"Ultralytics unavailable ({e}); using heuristic fallback detector.")
        _model = None
        _model_kind = "heuristic"


def _heuristic_fire_smoke_flood(image: np.ndarray) -> List[Dict]:
    """
    Lightweight, dependency-free emergency cue detector used only when no
    trained model is available. NOT a replacement for the fine-tuned model —
    provides plausible signal for demo/testing purposes based on classic
    color-space heuristics used in early fire/flood-detection literature.
    """
    detections = []
    h, w = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # --- Fire: high-saturation orange/red/yellow regions ---
    fire_mask = cv2.inRange(hsv, (0, 100, 150), (35, 255, 255))
    fire_ratio = cv2.countNonZero(fire_mask) / (h * w)
    if fire_ratio > 0.02:
        ys, xs = np.where(fire_mask > 0)
        if len(xs) > 0:
            bbox = [float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())]
            detections.append({
                "label": "fire",
                "confidence": round(min(0.55 + fire_ratio * 2, 0.95), 2),
                "bbox": bbox,
            })

    # --- Smoke: low-saturation gray haze covering large area ---
    gray_mask = cv2.inRange(hsv, (0, 0, 120), (180, 40, 220))
    smoke_ratio = cv2.countNonZero(gray_mask) / (h * w)
    if smoke_ratio > 0.25:
        detections.append({
            "label": "smoke",
            "confidence": round(min(0.5 + smoke_ratio * 0.5, 0.9), 2),
            "bbox": [0.0, 0.0, float(w), float(h) * 0.5],
        })

    # --- Flood: dominant blue/brown-murky water tone in lower frame ---
    lower_half = hsv[int(h * 0.5):, :]
    water_mask = cv2.inRange(lower_half, (90, 30, 40), (140, 255, 200))
    water_ratio = cv2.countNonZero(water_mask) / (lower_half.shape[0] * w)
    if water_ratio > 0.35:
        detections.append({
            "label": "flood",
            "confidence": round(min(0.5 + water_ratio * 0.5, 0.9), 2),
            "bbox": [0.0, float(h) * 0.5, float(w), float(h)],
        })

    return detections


def detect(image: np.ndarray) -> List[Dict]:
    """
    Runs disaster-object detection on a single BGR image (numpy array).
    Returns list of {label, confidence, bbox}.
    """
    global _model, _model_kind
    if _model_kind is None:
        _try_load_ultralytics_model()

    if _model_kind in ("yolo", "yolo_generic") and _model is not None:
        results = _model.predict(image, conf=settings.VISION_CONFIDENCE_THRESHOLD, verbose=False)
        out = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = _model.names.get(cls_id, str(cls_id)) if hasattr(_model, "names") else str(cls_id)
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                out.append({"label": label, "confidence": round(conf, 2), "bbox": xyxy})
        # Supplement generic COCO model with heuristic disaster cues since it
        # cannot detect fire/smoke/flood classes on its own.
        if _model_kind == "yolo_generic":
            out.extend(_heuristic_fire_smoke_flood(image))
        return out

    return _heuristic_fire_smoke_flood(image)


def estimate_affected_area(bbox: List[float], image_shape, gsd_m_per_px: float = 0.05) -> float:
    """
    Rough affected-area estimate in square meters from a bounding box,
    given an assumed ground-sample-distance (meters/pixel). For webcam feeds
    this is a coarse proxy; for satellite imagery gsd_m_per_px should be set
    from the actual product resolution (e.g., Sentinel-2 = 10 m/px).
    """
    x1, y1, x2, y2 = bbox
    width_px = max(x2 - x1, 0)
    height_px = max(y2 - y1, 0)
    return round(width_px * height_px * (gsd_m_per_px ** 2), 2)


CLASS_LIST = DISASTER_CLASSES
