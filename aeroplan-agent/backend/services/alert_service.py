"""
AeroPlan-Agent :: Alert Dispatch Service (SIMULATION ONLY)

This module NEVER contacts real emergency services. It simulates
SMS / Email / Dashboard-popup / Voice-alert dispatch to Police, Fire
Department, Ambulance, and NDRF, and logs each simulated alert to the
database for the dashboard's "Emergency Alerts" and "Decision Logs" views.
"""
import logging
import datetime as dt
from backend.core.config import get_settings

logger = logging.getLogger("aeroplan.alerts")
settings = get_settings()

DISPATCH_MATRIX = {
    "fire": ["fire_department", "police"],
    "flood": ["ndrf", "police"],
    "road_accident": ["ambulance", "police"],
    "structural_collapse": ["ndrf", "fire_department", "ambulance"],
    "obstruction": ["police"],
    "crowd_hazard": ["police"],
}

CHANNELS = ["sms", "email", "dashboard_popup", "voice_alert"]


def build_alert_messages(emergency: dict) -> list:
    """
    emergency: dict with emergency_type, severity, latitude, longitude, confidence
    Returns list of {channel, recipient_type, message}
    """
    recipients = DISPATCH_MATRIX.get(emergency["emergency_type"], ["police"])
    messages = []
    for recipient in recipients:
        text = (
            f"[SIMULATED ALERT] {emergency['emergency_type'].upper()} detected "
            f"(severity: {emergency['severity'].upper()}, confidence: {emergency['confidence']*100:.0f}%) "
            f"at lat={emergency['latitude']:.5f}, lon={emergency['longitude']:.5f}. "
            f"Dispatch requested: {recipient.replace('_',' ').title()}. "
            f"Time: {dt.datetime.utcnow().isoformat()}Z"
        )
        for channel in CHANNELS:
            messages.append({"channel": channel, "recipient_type": recipient, "message": text})
    return messages


def dispatch(emergency: dict) -> list:
    """
    SIMULATES dispatch — logs only, no real network calls to emergency
    services are ever made (settings.SIMULATE_ALERTS_ONLY is enforced).
    """
    assert settings.SIMULATE_ALERTS_ONLY, "Real dispatch is disabled by design in this project."
    alerts = build_alert_messages(emergency)
    for a in alerts:
        logger.info(f"[SIMULATED::{a['channel']}::{a['recipient_type']}] {a['message']}")
    return alerts
