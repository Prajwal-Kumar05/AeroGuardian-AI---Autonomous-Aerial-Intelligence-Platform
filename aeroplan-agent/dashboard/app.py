"""
AeroPlan-Agent :: Streamlit Dashboard

Run: streamlit run dashboard/app.py

Unified control room UI: live monitoring, detection, satellite view,
weather, risk heatmap, evacuation route map, AI reasoning, timeline,
alerts, and decision logs.
"""
import os
import sys
import time
import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

API_BASE = os.getenv("AEROPLAN_API_BASE", "http://localhost:8000")

st.set_page_config(page_title="AeroPlan-Agent | Emergency Control Room", layout="wide", page_icon="🚨")

# ---------- Sidebar ----------
st.sidebar.title("🚨 AeroPlan-Agent")
st.sidebar.caption("AI-Powered Autonomous Multi-Agent Framework for Real-Time Emergency Detection and Disaster Response")

lat = st.sidebar.number_input("Latitude", value=12.9716, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=77.5946, format="%.6f")
source = st.sidebar.selectbox("Input Source", ["webcam", "upload", "satellite"])

uploaded_file = None
if source == "upload":
    uploaded_file = st.sidebar.file_uploader("Upload image / video frame", type=["jpg", "jpeg", "png"])

run_btn = st.sidebar.button("▶ Run Multi-Agent Pipeline", type="primary", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("**Agents in this pipeline**")
st.sidebar.markdown(
    "1. Monitoring Agent\n"
    "2. Vision Analysis Agent\n"
    "3. Verification Agent\n"
    "4. Risk Assessment Agent\n"
    "5. Geospatial Intelligence Agent\n"
    "6. Emergency Planning Agent\n"
    "7. Explainable AI Agent"
)

st.title("Unified Emergency Dashboard")

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None

# ---------- Run pipeline ----------
if run_btn:
    with st.spinner("Running multi-agent reasoning pipeline..."):
        try:
            if source == "upload" and uploaded_file is not None:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"latitude": lat, "longitude": lon}
                resp = requests.post(f"{API_BASE}/api/emergency/run-upload", data=data, files=files, timeout=120)
            else:
                resp = requests.post(
                    f"{API_BASE}/api/emergency/run",
                    json={"latitude": lat, "longitude": lon, "source": source},
                    timeout=120,
                )
            resp.raise_for_status()
            st.session_state["last_result"] = resp.json()
            st.success("Pipeline run complete.")
        except Exception as e:
            st.error(f"Pipeline run failed: {e}")

result = st.session_state["last_result"]

tabs = st.tabs([
    "📡 Monitoring", "🎯 Detection", "🛰️ Satellite", "⛅ Weather",
    "⚠️ Risk", "🗺️ Evacuation Route", "🧠 AI Reasoning",
    "📜 Timeline & Logs", "📢 Alerts",
])

# ---- Monitoring tab ----
with tabs[0]:
    st.subheader("Live Monitoring")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Source: **{source}**  |  Location: `({lat}, {lon})`")
        if source == "upload" and uploaded_file:
            st.image(uploaded_file, caption="Uploaded frame", use_container_width=True)
        elif source == "webcam":
            st.warning("Webcam capture happens server-side when the pipeline runs "
                       "(requires a camera attached to the backend host).")
    with col2:
        try:
            w = requests.get(f"{API_BASE}/api/weather", params={"lat": lat, "lon": lon}, timeout=10).json()
            st.metric("Temperature", f"{w.get('temperature_c','-')} °C")
            st.metric("Wind Speed", f"{w.get('wind_speed_ms','-')} m/s")
        except Exception:
            st.warning("Backend not reachable — start the FastAPI server (`uvicorn backend.main:app`).")

# ---- Detection tab ----
with tabs[1]:
    st.subheader("Emergency Detection (Vision Analysis Agent)")
    if result and result.get("emergency"):
        em = result["emergency"]
        if em["detections"]:
            df = pd.DataFrame(em["detections"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No emergency-relevant objects detected.")
        st.write(f"**Emergency Type:** {em['emergency_type']}  |  **Status:** {em['status']}  |  "
                 f"**Confidence:** {em['confidence']*100:.0f}%")
    else:
        st.info("Run the pipeline to see detections here.")

# ---- Satellite tab ----
with tabs[2]:
    st.subheader("Satellite Verification (NASA FIRMS / Sentinel-2)")
    st.caption("Used by the Verification Agent to corroborate fire/flood detections — not as primary detector.")
    st.info("Configure NASA_FIRMS_API_KEY / SENTINEL_HUB credentials in .env to enable live imagery. "
            "See backend/services/satellite_service.py")

# ---- Weather tab ----
with tabs[3]:
    st.subheader("Weather Intelligence (OpenWeatherMap)")
    try:
        w = requests.get(f"{API_BASE}/api/weather", params={"lat": lat, "lon": lon}, timeout=10).json()
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Temp (°C)", w.get("temperature_c"))
        c2.metric("Humidity (%)", w.get("humidity_pct"))
        c3.metric("Wind (m/s)", w.get("wind_speed_ms"))
        c4.metric("Rainfall (mm)", w.get("rainfall_mm"))
        c5.metric("Visibility (m)", w.get("visibility_m"))
        st.caption(f"Condition: {w.get('condition')}")
    except Exception:
        st.warning("Backend not reachable.")

# ---- Risk tab ----
with tabs[4]:
    st.subheader("Risk Assessment")
    if result and result.get("emergency"):
        em = result["emergency"]
        severity_color = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴", "none": "⚪"}
        st.metric("Risk Score", f"{em['risk_score']}/100")
        st.markdown(f"### Severity: {severity_color.get(em['severity'],'')} **{em['severity'].upper()}**")
        c1, c2 = st.columns(2)
        c1.metric("Affected Area (m²)", em.get("affected_area_m2"))
        c2.metric("Est. Affected Population", em.get("affected_population_estimate"))
        st.progress(min(em["risk_score"] / 100, 1.0))
    else:
        st.info("Run the pipeline to compute risk.")

# ---- Route tab ----
with tabs[5]:
    st.subheader("Evacuation Route Planning (OSMnx + Dijkstra/A*)")
    m = folium.Map(location=[lat, lon], zoom_start=14)
    folium.Marker([lat, lon], tooltip="Incident", icon=folium.Icon(color="red", icon="fire")).add_to(m)

    if result and result.get("emergency") and result["emergency"].get("routes"):
        colors = {"primary": "blue", "alternative": "green"}
        for r in result["emergency"]["routes"]:
            coords = r.get("path_coordinates") or []
            if coords:
                folium.PolyLine(coords, color=colors.get(r["route_type"], "gray"), weight=5,
                                 tooltip=f"{r['route_type']} ({r['distance_m']} m) via {r['algorithm']}").add_to(m)
                folium.Marker(coords[-1], tooltip=r["destination_name"],
                              icon=folium.Icon(color="green", icon="home")).add_to(m)
    st_folium(m, width=1100, height=520)

# ---- Reasoning tab ----
with tabs[6]:
    st.subheader("Explainable AI — Reasoning Chain")
    if result:
        st.markdown(f"> {result.get('emergency', {}).get('reasoning', 'No reasoning generated.')}")
        for step in result.get("reasoning_chain", []):
            with st.expander(f"🔎 {step['step']}"):
                st.write(step["detail"])
    else:
        st.info("Run the pipeline to view the reasoning chain.")

# ---- Timeline & Logs tab ----
with tabs[7]:
    st.subheader("Incident Timeline & Agent Decision Logs")
    try:
        history = requests.get(f"{API_BASE}/api/emergency/history", timeout=10).json()
        if history:
            st.dataframe(pd.DataFrame(history), use_container_width=True)
        logs = requests.get(f"{API_BASE}/api/logs", timeout=10).json()
        if logs:
            st.markdown("#### Agent Execution Logs")
            st.dataframe(pd.DataFrame(logs), use_container_width=True)
    except Exception:
        st.warning("Backend not reachable.")

# ---- Alerts tab ----
with tabs[8]:
    st.subheader("Emergency Alerts (Simulated — no real dispatch)")
    if result and result.get("alerts_dispatched"):
        st.dataframe(pd.DataFrame(result["alerts_dispatched"]), use_container_width=True)
    try:
        alerts = requests.get(f"{API_BASE}/api/alerts", timeout=10).json()
        if alerts:
            st.markdown("#### Alert History")
            st.dataframe(pd.DataFrame(alerts), use_container_width=True)
    except Exception:
        pass
    st.caption("⚠️ All SMS / Email / Voice / Dashboard alerts are SIMULATED for this academic prototype. "
               "No real emergency services are contacted.")
