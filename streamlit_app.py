import streamlit as st
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import datetime

from app.logic import generate_recommendation
from app.models import LandingRequest, GPS, Weather, Aircraft

# ─── Initialize Session State ───────────────────────────
if "resp" not in st.session_state:
    st.session_state.resp = None
    st.session_state.inputs = {}
    st.session_state.params = {}

# ─── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="SmartPad VTOL Landing Assistant",
    layout="wide",
)
st.title("🚁 SmartPad VTOL Landing Assistant")

# ─── Scenario Presets with Weather Conditions ────────────
SCENARIOS = {
    "Clear Skies (Riyadh Center)": {
        "gps": GPS(latitude=24.7136, longitude=46.6753),
        "weather": Weather(wind_speed=10, wind_direction="NE"),
        "condition": "Clear",
        "aircraft": Aircraft(model="AW139", weight=5500),
        "obstacles": [
            {"lat": 24.7140, "lon": 46.6760, "height": 50},
            {"lat": 24.7130, "lon": 46.6740, "height": 80},
        ],
    },
    "Rainstorm (Jeddah Coast)": {
        "gps": GPS(latitude=21.4858, longitude=39.1925),
        "weather": Weather(wind_speed=15, wind_direction="SE"),
        "condition": "Rain",
        "aircraft": Aircraft(model="AW139", weight=5400),
        "obstacles": [
            {"lat": 21.4870, "lon": 39.1935, "height": 30},
            {"lat": 21.4840, "lon": 39.1910, "height": 60},
        ],
    },
    "Foggy Morning (Taif)": {
        "gps": GPS(latitude=21.2854, longitude=40.4058),
        "weather": Weather(wind_speed=5, wind_direction="N"),
        "condition": "Fog",
        "aircraft": Aircraft(model="AW139", weight=5300),
        "obstacles": [
            {"lat": 21.2860, "lon": 40.4065, "height": 40},
            {"lat": 21.2840, "lon": 40.4040, "height": 70},
        ],
    },
    "Dust Storm (Dammam)": {
        "gps": GPS(latitude=26.3927, longitude=49.9777),
        "weather": Weather(wind_speed=20, wind_direction="NW"),
        "condition": "Dust Storm",
        "aircraft": Aircraft(model="AW139", weight=5600),
        "obstacles": [
            {"lat": 26.3935, "lon": 49.9785, "height": 20},
            {"lat": 26.3910, "lon": 49.9760, "height": 90},
        ],
    },
}

# ─── Sidebar: Scenario & Inputs ─────────────────────────
st.sidebar.header("Demo Scenario")
scenario_name = st.sidebar.selectbox("Choose a scenario:", list(SCENARIOS.keys()))
params = SCENARIOS[scenario_name]

st.sidebar.header("Flight Inputs (override)")
lat = st.sidebar.number_input("Latitude", value=params["gps"].latitude, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=params["gps"].longitude, format="%.4f")
wind_speed = st.sidebar.slider(
    "Wind speed (knots)", 0, 80, int(params["weather"].wind_speed)
)
wind_dir = st.sidebar.selectbox(
    "Wind direction",
    ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
    index=["N","NE","E","SE","S","SW","W","NW"].index(params["weather"].wind_direction)
)
condition = params["condition"]
model = st.sidebar.text_input("Aircraft model", value=params["aircraft"].model)
weight = st.sidebar.number_input(
    "Aircraft weight (kg)", 1000, 15000, int(params["aircraft"].weight)
)

# ─── Trigger Recommendation ─────────────────────────────
if st.sidebar.button("Get Recommendation"):
    req = LandingRequest(
        gps=GPS(latitude=lat, longitude=lon),
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model=model, weight=weight),
    )
    st.session_state.resp = generate_recommendation(req)
    st.session_state.inputs = {
        "lat": lat,
        "lon": lon,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "condition": condition,
        "model": model,
        "weight": weight,
    }
    st.session_state.params = params

# ─── Persistent Display ─────────────────────────────────
if st.session_state.resp:
    resp = st.session_state.resp
    inputs = st.session_state.inputs
    params = st.session_state.params

    lat = inputs["lat"]
    lon = inputs["lon"]
    wind_speed = inputs["wind_speed"]
    wind_dir = inputs["wind_dir"]
    condition = inputs["condition"]
    model = inputs["model"]
    weight = inputs["weight"]

    # ─── Map Visualization ────────────────────────────────
    st.subheader("🗺️ Landing Zone Map")
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
    for obs in params["obstacles"]:
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=obs["height"] * 0.2,
            color="red",
            fill=True,
            fill_opacity=0.6,
        ).add_to(m)
    folium.Marker(
        [lat, lon],
        icon=folium.Icon(color="green", icon="helicopter", prefix="fa")
    ).add_to(m)
    st_folium(m, width="100%", height=500)

    # ─── Recommendation Details ───────────────────────────
    st.subheader("🛬 Landing Recommendation")
    st.markdown(f"- **Condition:** {condition}")
    performance_desc = (
        "Within PC1 limits. Approach directions S185"
        if resp.path_type == "PC1"
        else "Within PC2 limits. Approach directions S185"
    )
    st.markdown(f"- **Performance Class:** {performance_desc}")
    st.markdown("- **Landing Profile:** Confined area AW139 profile. LDPL 170ft")

    # ─── PDF Report Generation & Download ─────────────────
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"Scenario: {scenario_name}", ln=True)
    pdf.cell(0, 8, f"Location: {lat:.4f}, {lon:.4f}", ln=True)
    pdf.cell(0, 8, f"Condition: {condition}", ln=True)
    pdf.cell(0, 8, f"Wind: {wind_speed} kt {wind_dir}", ln=True)
    pdf.cell(0, 8, f"Aircraft: {model}, {weight} kg", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Performance Class: {performance_desc}", ln=True)
    pdf.cell(0, 8, "Landing Profile: Confined area AW139 profile. LDPL 170ft", ln=True)
    pdf.ln(5)
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
