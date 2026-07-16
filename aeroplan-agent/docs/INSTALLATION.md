# Installation Guide

## Option A — Local (Python virtualenv)

### 1. Prerequisites
- Python 3.11+
- (Optional) PostgreSQL 14+ — the app auto-falls-back to local SQLite if unavailable
- GDAL system libraries (required by `rasterio`/`geopandas`):
  - Ubuntu/Debian: `sudo apt-get install gdal-bin libgdal-dev`
  - macOS: `brew install gdal`

### 2. Clone & set up environment
```bash
cd aeroplan-agent
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Fill in `.env` (all optional — the app runs with graceful fallbacks)
- `OPENWEATHER_API_KEY` — https://openweathermap.org/api (free tier)
- `NASA_FIRMS_API_KEY` — https://firms.modaps.eosdis.nasa.gov/api/
- `SENTINEL_HUB_CLIENT_ID` / `SECRET` — https://www.sentinel-hub.com/
- `ANTHROPIC_API_KEY` — optional, improves Explainable AI narrative fluency

### 4. Run the backend
```bash
uvicorn backend.main:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs
```

### 5. Run the dashboard (separate terminal)
```bash
streamlit run dashboard/app.py
# Opens at http://localhost:8501
```

### 6. Run tests
```bash
pytest tests/ -v
```

## Option B — Docker Compose (recommended for full-stack demo)

```bash
cp .env.example .env      # fill in optional keys
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Dashboard: http://localhost:8501
- PostgreSQL: localhost:5432 (user/pass: postgres/postgres)

## Fine-tuning the Vision model (optional but recommended)

See `datasets/README.md` for dataset sources and the exact `yolo detect
train` command. Without a fine-tuned checkpoint, the Vision Analysis Agent
automatically falls back to a generic pretrained model + OpenCV heuristic
detector so the full pipeline still runs end-to-end for grading/demo
purposes.

## Common issues

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'osgeo'` | Install GDAL system package before `pip install rasterio geopandas` |
| Webcam not accessible | Run backend on a machine with an attached camera, or use `source=upload` in the dashboard |
| OSM queries slow/failing | First call per location downloads the road network; subsequent calls are cached in-process |
| Streamlit can't reach backend | Ensure `uvicorn` is running on port 8000, or set `AEROPLAN_API_BASE` env var for the dashboard |
