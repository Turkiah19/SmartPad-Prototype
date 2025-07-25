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

# ─── Sidebar: Scenario & Inputs ─────────────────────────
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
wind_dir = st.s_
