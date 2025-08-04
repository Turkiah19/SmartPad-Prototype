import streamlit as st
import folium
from streamlit_folium import st_folium
from fpdf import FPDF
import datetime

from app.logic import generate_recommendation
from app.models import LandingRequest, GPS, Weather, Aircraft

# ─── Page Config ────────────────────────────────────────
st.set_page_config(page_title="SmartPad VTOL Landing Assistant", layout="wide")
st.title("SmartPad VTOL Landing Assistant")

# ─── Pilot & Aircraft Info ──────────────────────────────
st.header("Pilot & Aircraft Information")
pilot_col, aircraft_col = st.columns(2)
with pilot_col:
    st.subheader("Pilot Info")
    st.markdown("""
    - **Name:** Capt. Khalid Al-Huwaidi  
    - **License:** CPL IR RW  
    - **Total Hours:** 1500 h  
    """)
with aircraft_col:
    st.subheader("Aircraft Info")
    st.markdown("""
    - **Model:** AW139  
    - **Max Takeoff Weight:** 7000 kg  
    - **Registration:** HZ-ABC  
    - **MTOW Category:** Medium  
    """)

# ─── Flight Inputs ───────────────────────────────────────
st.header("Flight Inputs")
col1, col2 = st.columns(2)
with col1:
    city         = st.selectbox("City (Helipad)", ["Riyadh (KFMC)", "Jeddah", "Taif", "Dammam"])
    weather_cond = st.selectbox("Weather Condition", ["Clear", "Rain", "Fog", "Dust Storm"])
with col2:
    wind_speed = st.slider("Wind speed (knots)", 0, 80, 10)
    wind_dir   = st.selectbox("Wind direction", ["N","NE","E","SE","S","SW","W","NW"])
    weight     = st.number_input("Aircraft weight (kg)", 1000, 15000, 5500)

# ─── City & Scenario Data ───────────────────────────────
SCENARIOS = {
    "Riyadh (KFMC)": {
        "gps": GPS(24.688000, 46.705200),
        "obstacles": [
            {"lat": 24.6890, "lon": 46.7060, "height": 50},
            {"lat": 24.6875, "lon": 46.7040, "height": 80},
        ],
    },
    "Jeddah": {
        "gps": GPS(21.485800, 39.192500),
        "obstacles": [
            {"lat": 21.4870, "lon": 39.1935, "height": 30},
            {"lat": 21.4840, "lon": 39.1910, "height": 60},
        ],
    },
    "Taif": {
        "gps": GPS(21.285400, 40.405800),
        "obstacles": [
            {"lat": 21.2860, "lon": 40.4065, "height": 40},
            {"lat": 21.2840, "lon": 40.4040, "height": 70},
        ],
    },
    "Dammam": {
        "gps": GPS(26.392700, 49.977700),
        "obstacles": [
            {"lat": 26.3935, "lon": 49.9785, "height": 20},
            {"lat": 26.3910, "lon": 49.9760, "height": 90},
        ],
    },
}

# ─── Build & call recommendation ───────────────────────
if st.button("Get Recommendation"):
    req = LandingRequest(
        gps=SCENARIOS[city]["gps"],
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model="AW139", weight=weight),
    )
    resp = generate_recommendation(req)
    st.session_state.resp   = resp
    st.session_state.inputs = {_
