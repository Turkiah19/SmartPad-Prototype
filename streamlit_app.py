import streamlit as st
import pandas as pd
import pydeck as pdk
import json
from io import BytesIO

from app.logic import generate_recommendation
from app.models import LandingRequest, GPS, Weather, Aircraft

# ─── Page Config & Styling ───────────────────────────
st.set_page_config(
    page_title="SmartPad VTOL Landing Assistant",
    layout="wide",
)
st.title("🚁 SmartPad VTOL Landing Assistant")

# ─── Scenario Presets ─────────────────────────────────
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

st.sidebar.header("Demo Scenario")
scenario_name = st.sidebar.selectbox("Choose a scenario:", list(SCENARIOS.keys()))
params = SCENARIOS[scenario_name]

# ─── Inputs from Scenario (you can still override) ─────
st.sidebar.header("Flight Inputs (override)")
lat = st.sidebar.number_input("Latitude", value=params["gps"].latitude, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=params["gps"].longitude, format="%.4f")
wind_speed = st.sidebar.slider("Wind speed (knots)", 0, 80, params["weather"].wind_speed)
wind_dir = st.sidebar.selectbox("Wind direction", ["N","NE","E","SE","S","SW","W","NW"], index=["N","NE","E","SE","S","SW","W","NW"].index(params["weather"].wind_direction))
model = st.sidebar.text_input("Aircraft model", value=params["aircraft"].model)
weight = st.sidebar.number_input("Aircraft weight (kg)", 1000, 15000, params["aircraft"].weight)

# ─── Run Recommendation ────────────────────────────────
if st.sidebar.button("Get Recommendation"):
    req = LandingRequest(
        gps=GPS(latitude=lat, longitude=lon),
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model=model, weight=weight),
    )
    resp = generate_recommendation(req)

    # ─── Map Visualization ─────────────────────────────
    st.subheader("🗺️ Landing Zone Visualization")
    df_obs = pd.DataFrame(params["obstacles"])
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=lat, longitude=lon, zoom=14, pitch=45
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df_obs,
                get_position=["lon","lat"],
                get_radius="height * 0.5",
                get_fill_color=[200, 30, 0, 160],
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=pd.DataFrame([{"lat":lat, "lon":lon, "marker":1}]),
                get_position=["lon","lat"],
                get_radius=50,
                get_fill_color=[0, 150, 30, 200],
            ),
        ],
    )
    st.pydeck_chart(deck, use_container_width=True)

    # ─── Show Recommendation ────────────────────────────
    st.subheader("🛬 Landing Recommendation")
    st.markdown(f"**Path Type:** `{resp.path_type}`")
    st.markdown(f"**Direction:** `{resp.direction}`")
    st.markdown(f"**Risk Score:** {resp.risk_score}")
    if resp.warnings:
        st.warning("\n".join(resp.warnings))

    # ─── Download Result ────────────────────────────────
    result_json = json.dumps(resp.dict(), indent=2)
    st.download_button(
        "📥 Download Recommendation (JSON)",
        result_json,
        file_name="landing_recommendation.json",
        mime="application/json",
    )
