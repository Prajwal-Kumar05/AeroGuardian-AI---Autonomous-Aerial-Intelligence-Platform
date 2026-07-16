"""
AeroPlan-Agent :: Weather Service (OpenWeatherMap)
"""
import logging
import requests
from backend.core.config import get_settings

logger = logging.getLogger("aeroplan.weather")
settings = get_settings()

OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_current_weather(lat: float, lon: float) -> dict:
    """
    Fetches live weather from OpenWeatherMap. Falls back to a neutral
    synthetic reading (clearly flagged) if no API key is configured or the
    request fails, so the pipeline never hard-crashes during a demo.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY not set — returning synthetic weather reading.")
        return _synthetic_weather()

    try:
        resp = requests.get(
            OWM_URL,
            params={
                "lat": lat, "lon": lon,
                "appid": settings.OPENWEATHER_API_KEY,
                "units": "metric",
            },
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "temperature_c": data["main"]["temp"],
            "humidity_pct": data["main"]["humidity"],
            "wind_speed_ms": data["wind"]["speed"],
            "rainfall_mm": data.get("rain", {}).get("1h", 0.0),
            "visibility_m": data.get("visibility", 10000),
            "condition": data["weather"][0]["main"].lower(),
            "raw_payload": data,
        }
    except Exception as e:
        logger.error(f"Weather fetch failed: {e}")
        return _synthetic_weather()


def _synthetic_weather() -> dict:
    return {
        "temperature_c": 31.0,
        "humidity_pct": 40.0,
        "wind_speed_ms": 6.5,
        "rainfall_mm": 0.0,
        "visibility_m": 9000,
        "condition": "clear",
        "raw_payload": {"synthetic": True},
    }


def wind_fire_risk_multiplier(wind_speed_ms: float) -> float:
    """High wind accelerates fire spread — used by Risk Assessment Agent."""
    if wind_speed_ms >= 12:
        return 1.6
    if wind_speed_ms >= 8:
        return 1.35
    if wind_speed_ms >= 5:
        return 1.15
    return 1.0
