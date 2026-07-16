# Datasets & Model Fine-Tuning Guide

AeroPlan-Agent's Vision Analysis Agent is built on **YOLOv11 / RT-DETR**
(via Ultralytics). Out of the box the repo runs with either a generic
COCO-pretrained checkpoint plus an OpenCV heuristic fallback (for demo
purposes), or your own fine-tuned disaster-detection weights.

## 1. Recommended source datasets

| Dataset | Content | Link |
|---|---|---|
| Roboflow Universe — Disaster/Fire/Flood collections | Fire, smoke, flood, collapsed structures, road damage (pre-annotated, YOLO-format export) | https://universe.roboflow.com |
| Kaggle — Fire and Smoke Detection Dataset | Fire/smoke classification & detection images | https://www.kaggle.com/datasets |
| Kaggle — Flood Area Segmentation | Flood extent imagery | https://www.kaggle.com/datasets |
| NASA FIRMS Archive | Historical active-fire hotspot data (for verification-agent testing) | https://firms.modaps.eosdis.nasa.gov |
| Copernicus Sentinel-2 (via Sentinel Hub / Copernicus Browser) | Satellite true-color / NDVI / NDWI imagery | https://dataspace.copernicus.eu |
| OpenStreetMap (via OSMnx) | Road network + amenities (hospitals, fire/police stations) | https://www.openstreetmap.org |

## 2. Unified class schema (see `backend/ml/labels.py`)

```
fire, smoke, flood, road_accident, collapsed_building,
fallen_tree, blocked_road, crowd, vehicle, person
```

When merging multiple source datasets, remap their native class names to
this schema before training (a `remap_classes.py` helper script stub is a
good addition if you extend this project).

## 3. Fine-tuning command

```bash
# Prepare disaster.yaml (Ultralytics data config) pointing at your merged,
# YOLO-format-annotated dataset, then:

yolo detect train \
  data=disaster.yaml \
  model=yolo11n.pt \
  epochs=100 \
  imgsz=640 \
  batch=16 \
  project=runs/train \
  name=aeroplan_disaster_v1

# For RT-DETR instead:
yolo detect train data=disaster.yaml model=rtdetr-l.pt epochs=100 imgsz=640
```

Place the resulting `best.pt` at the path configured by
`VISION_MODEL_PATH` in `.env` (default: `backend/ml/weights/yolo11_disaster.pt`).

## 4. Evaluation

```bash
yolo detect val model=backend/ml/weights/yolo11_disaster.pt data=disaster.yaml
```

Track mAP50-95, per-class recall (fire/smoke recall is safety-critical —
prioritize recall over precision for these two classes, since the
Verification Agent already exists specifically to filter false positives
downstream).

## 5. Why the project runs without a trained checkpoint

`backend/ml/detector.py` degrades gracefully:
1. Fine-tuned checkpoint present → used directly.
2. Not present → generic COCO-pretrained YOLO is loaded (person/vehicle
   detection works out of the box) **and** supplemented with an OpenCV
   color-heuristic fire/smoke/flood cue detector, so the full multi-agent
   pipeline (including Verification, Risk, Planning) remains testable
   end-to-end before any custom training is done.
