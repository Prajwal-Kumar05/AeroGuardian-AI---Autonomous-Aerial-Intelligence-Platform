"""AeroPlan-Agent :: Image I/O helpers"""
import numpy as np
import cv2


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not read image at {path}")
    return img


def capture_webcam_frame(device_index: int = 0) -> np.ndarray:
    """Grabs a single frame from a local webcam (acts as CCTV feed)."""
    cap = cv2.VideoCapture(device_index)
    if not cap.isOpened():
        raise RuntimeError("Webcam not accessible.")
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Failed to capture frame from webcam.")
    return frame


def draw_detections(image: np.ndarray, detections: list) -> np.ndarray:
    out = image.copy()
    for d in detections:
        x1, y1, x2, y2 = [int(v) for v in d["bbox"]]
        color = (0, 0, 255) if d["label"] in ("fire", "smoke") else (0, 165, 255)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, f"{d['label']} {d['confidence']:.2f}", (x1, max(y1 - 8, 0)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return out
