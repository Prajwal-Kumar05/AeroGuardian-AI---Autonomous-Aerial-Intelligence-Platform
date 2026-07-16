"""
AeroPlan-Agent :: Satellite Intelligence Service

Integrates:
  - NASA FIRMS (active fire/hotspot detection, near-real-time, free API key)
  - Sentinel Hub (Sentinel-2 L2A true-color / NDVI / NDWI imagery)

Used strictly for VERIFICATION and impact-context by the Verification and
Risk agents — not as the primary detector.
"""
import logging
import requests
from backend.core.config import get_settings

logger = logging.getLogger("aeroplan.satellite")
settings = get_settings()

FIRMS_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/VIIRS_SNPP_NRT/{bbox}/1"


def get_active_fire_hotspots(lat: float, lon: float, delta: float = 0.15) -> dict:
    """
    Queries NASA FIRMS for active fire/thermal-anomaly hotspots within a
    bounding box around (lat, lon). Returns a summary usable by the
    Verification Agent to corroborate a vision-based fire detection.
    """
    if not settings.NASA_FIRMS_API_KEY:
        logger.warning("NASA_FIRMS_API_KEY not set — satellite fire verification skipped.")
        return {"available": False, "hotspot_count": 0, "hotspots": []}

    bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
    url = FIRMS_URL.format(key=settings.NASA_FIRMS_API_KEY, bbox=bbox)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        lines = [l for l in resp.text.splitlines() if l.strip()]
        hotspots = lines[1:]  # skip CSV header
        return {"available": True, "hotspot_count": len(hotspots), "hotspots": hotspots[:20]}
    except Exception as e:
        logger.error(f"NASA FIRMS query failed: {e}")
        return {"available": False, "hotspot_count": 0, "hotspots": [], "error": str(e)}


def get_sentinel2_true_color(lat: float, lon: float, size_px: int = 512) -> dict:
    """
    Fetches a Sentinel-2 L2A true-color thumbnail via Sentinel Hub Process API
    for the area around (lat, lon). Requires SENTINEL_HUB_CLIENT_ID/SECRET.
    Returns metadata + (optionally) raw image bytes reference; wired for the
    Geospatial/Verification agents to pull broader-context imagery.
    """
    if not settings.SENTINEL_HUB_CLIENT_ID or not settings.SENTINEL_HUB_CLIENT_SECRET:
        logger.warning("Sentinel Hub credentials not set — using placeholder satellite context.")
        return {"available": False, "note": "Configure SENTINEL_HUB_CLIENT_ID/SECRET in .env"}

    try:
        token_resp = requests.post(
            "https://services.sentinel-hub.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.SENTINEL_HUB_CLIENT_ID,
                "client_secret": settings.SENTINEL_HUB_CLIENT_SECRET,
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        token = token_resp.json()["access_token"]

        delta = 0.02
        bbox = [lon - delta, lat - delta, lon + delta, lat + delta]
        evalscript = """
        //VERSION=3
        function setup() { return { input: ["B02","B03","B04"], output: { bands: 3 } }; }
        function evaluatePixel(s) { return [s.B04*2.5, s.B03*2.5, s.B02*2.5]; }
        """
        req_body = {
            "input": {
                "bounds": {"bbox": bbox},
                "data": [{"type": "sentinel-2-l2a"}],
            },
            "output": {"width": size_px, "height": size_px},
            "evalscript": evalscript,
        }
        img_resp = requests.post(
            "https://services.sentinel-hub.com/api/v1/process",
            headers={"Authorization": f"Bearer {token}"},
            json=req_body,
            timeout=20,
        )
        img_resp.raise_for_status()
        return {"available": True, "bbox": bbox, "image_bytes": img_resp.content}
    except Exception as e:
        logger.error(f"Sentinel Hub fetch failed: {e}")
        return {"available": False, "error": str(e)}
