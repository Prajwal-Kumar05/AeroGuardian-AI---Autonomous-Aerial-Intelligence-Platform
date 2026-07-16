"""
AeroPlan-Agent :: Centralized configuration
All secrets/keys are read from environment variables (.env).
Never hardcode credentials here.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AeroPlan-Agent"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    # --- Database ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/aeroplan"
    )

    # --- External APIs ---
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    NASA_FIRMS_API_KEY: str = os.getenv("NASA_FIRMS_API_KEY", "")
    SENTINEL_HUB_CLIENT_ID: str = os.getenv("SENTINEL_HUB_CLIENT_ID", "")
    SENTINEL_HUB_CLIENT_SECRET: str = os.getenv("SENTINEL_HUB_CLIENT_SECRET", "")
    GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT: str = os.getenv("GEE_SERVICE_ACCOUNT", "")

    # --- LLM / Agent reasoning (for ExplainableAI + LangGraph reasoning nodes) ---
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")

    # --- Vision model ---
    VISION_MODEL_PATH: str = os.getenv("VISION_MODEL_PATH", "backend/ml/weights/yolo11_disaster.pt")
    VISION_MODEL_FALLBACK: str = os.getenv("VISION_MODEL_FALLBACK", "yolo11n.pt")
    VISION_CONFIDENCE_THRESHOLD: float = float(os.getenv("VISION_CONF_THRESHOLD", "0.35"))

    # --- Geospatial defaults (demo city center; override per deployment) ---
    DEFAULT_LAT: float = float(os.getenv("DEFAULT_LAT", "12.9716"))
    DEFAULT_LON: float = float(os.getenv("DEFAULT_LON", "77.5946"))
    OSM_NETWORK_RADIUS_M: int = int(os.getenv("OSM_NETWORK_RADIUS_M", "3000"))

    # --- Alerts (simulated, no real dispatch) ---
    SIMULATE_ALERTS_ONLY: bool = True
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # --- Security ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
