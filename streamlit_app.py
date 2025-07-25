import streamlit as st
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import datetime

from app.logic import generate_recommendation
from app.models import LandingRequest, GPS, Weather, Aircraft

# ─── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="SmartPad VTOL Landing Assistant",
    layout="wide",
)
st.title("🚁 SmartPad VTOL Landing Assistant")

# ─── Scenario Presets ───────────────────────────────────
SCENARIOS = {
    "Urban Canyon (Riyadh Center)": {
        "gps": GPS(latitude=24.7136, longitude=46.6753),
        "weather": Weather(wind_speed=35, wind_direction="NE"),
        "aircraft": Aircraft(model="AW139", weight=5500),
        "obstacles": [
            {"lat": 24.7138, "lon": 46.6760, "height": 50},
            {"lat": 24.7140, "lon": 46.6750, "height": 15},
            {"lat": 24.7135, "lon": 46.6740, "height": 80},
        ],
    },
    "Mountain Ridge (Asir Region)": {
        "gps": GPS(latitude=18.2408, longitude=42.5068),
        "weather": Weather(wind_speed=20, wind_direction="W"),
        "aircraft": Aircraft(model="AW139", weight=5200),
        "obstacles": [
            {"lat": 18.2415, "lon": 42.5075, "height": 120},
            {"lat": 18.2420, "lon": 42.5060, "height": 45},
        ],
    },
}

# ─── Sidebar: Scenario + Inputs ─────────────────────────
st.sidebar.header("Demo Scenario")
scenario_name = st.sidebar.selectbox("Choose a scenario:", list(SCENARIOS.keys()))
params = SCENARIOS[scenario_name]

st.sidebar.header("Flight Inputs (override)")
lat = st.sidebar.number_input(
    "Latitude", value=params["gps"].latitude, format="%.4f"
)
lon = st.sidebar.number_input(
    "Longitude", value=params["gps"].longitude, format="%.4f"
)
wind_speed = st.sidebar.slider(
    "Wind speed (knots)", 0, 80, int(params["weather"].wind_speed)
)
wind_dir = st.sidebar.selectbox(
    "Wind direction",
    ["N","NE","E","SE","S","SW","W","NW"],
    index=["N","NE","E","SE","S","SW","W","NW"].index(params["weather"].wind_direction)
)
model = st.sidebar.text_input("Aircraft model", value=params["aircraft"].model)
weight = st.sidebar.number_input(
    "Aircraft weight (kg)", 1000, 15000, int(params["aircraft"].weight)
)

# ─── Trigger Recommendation ─────────────────────────────
if st.sidebar.button("Get Recommendation"):
    # Build request
    req = LandingRequest(
        gps=GPS(latitude=lat, longitude=lon),
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model=model, weight=weight),
    )
    resp = generate_recommendation(req)

    # ─── Map Visualization ────────────────────────────────
    st.subheader("🗺️ Landing Zone Map")
   m = folium.Map(
    location=[lat, lon],
    zoom_start=15,
    tiles="OpenStreetMap",  # built‑in, no attribution needed
)
    # Obstacles
    for obs in params["obstacles"]:
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=obs["height"] * 0.2,
            color="red",
            fill=True,
            fill_opacity=0.6,
        ).add_to(m)
    # Aircraft marker
    folium.Marker(
        [lat, lon],
        icon=folium.Icon(color="green", icon="helicopter", prefix="fa")
    ).add_to(m)
    st_folium(m, width="100%", height=500)

    # ─── Recommendation Details ───────────────────────────
    st.subheader("🛬 Landing Recommendation")
    st.markdown(f"**Path Type:** `{resp.path_type}`")
    st.markdown(f"**Direction:** `{resp.direction}`")
    st.markdown(f"**Risk Score:** {resp.risk_score}")
    if resp.warnings:
        st.warning("\n".join(resp.warnings))

    # ─── PDF Report Generation & Download ─────────────────
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"Location: {lat:.4f}, {lon:.4f}", ln=True)
    pdf.cell(0, 8, f"Wind: {wind_speed} kt {wind_dir}", ln=True)
    pdf.cell(0, 8, f"Aircraft: {model}, {weight} kg", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Path Type: {resp.path_type}", ln=True)
    pdf.cell(0, 8, f"Direction: {resp.direction}", ln=True)
    pdf.cell(0, 8, f"Risk Score: {resp.risk_score}", ln=True)
    if resp.warnings:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Warnings:", ln=True)
        pdf.set_font("Arial", size=12)
        for w in resp.warnings:
            pdf.multi_cell(0, 8, f"- {w}")
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name="SmartPad_Landing_Report.pdf",
        mime="application/pdf",
    )
