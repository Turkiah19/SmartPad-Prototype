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
    st.session_state.city = None
    st.session_state.weather = None

# ─── Page Config ────────────────────────────────────────
st.set_page_config(
    page_title="SmartPad VTOL Landing Assistant",
    layout="wide",
)
st.title("SmartPad VTOL Landing Assistant")

# ─── City Definitions ────────────────────────────────────
CITIES = {
    "Riyadh (KFMC)": {
        "gps": GPS(latitude=24.6880, longitude=46.7052),  # KFMC decimal
        "obstacles": [
            {"lat": 24.6890, "lon": 46.7060, "height": 50},
            {"lat": 24.6875, "lon": 46.7040, "height": 80},
        ],
    },
    "Jeddah": {
        "gps": GPS(latitude=21.4858, longitude=39.1925),
        "obstacles": [
            {"lat": 21.4870, "lon": 39.1935, "height": 30},
            {"lat": 21.4840, "lon": 39.1910, "height": 60},
        ],
    },
    "Taif": {
        "gps": GPS(latitude=21.2854, longitude=40.4058),
        "obstacles": [
            {"lat": 21.2860, "lon": 40.4065, "height": 40},
            {"lat": 21.2840, "lon": 40.4040, "height": 70},
        ],
    },
    "Dammam": {
        "gps": GPS(latitude=26.3927, longitude=49.9777),
        "obstacles": [
            {"lat": 26.3935, "lon": 49.9785, "height": 20},
            {"lat": 26.3910, "lon": 49.9760, "height": 90},
        ],
    },
}

# ─── Weather Options ────────────────────────────────────
WEATHERS = {
    "Clear": Weather(wind_speed=10, wind_direction="NE"),
    "Rain": Weather(wind_speed=15, wind_direction="SE"),
    "Fog": Weather(wind_speed=5, wind_direction="N"),
    "Dust Storm": Weather(wind_speed=20, wind_direction="NW"),
}

# ─── Sidebar: Select City and Weather ───────────────────
st.sidebar.header("Helipad City")
city = st.sidebar.selectbox("Select city:", list(CITIES.keys()))
params_city = CITIES[city]

st.sidebar.header("Weather Condition")
weather_cond = st.sidebar.selectbox("Select weather:", list(WEATHERS.keys()))
params_weather = WEATHERS[weather_cond]

# ─── Flight Inputs ──────────────────────────────────────
st.sidebar.header("Flight Inputs")
wind_speed = st.sidebar.slider(
    "Wind speed (knots)", 0, 80, int(params_weather.wind_speed)
)
wind_dir = st.sidebar.selectbox(
    "Wind direction",
    ["N","NE","E","SE","S","SW","W","NW"],
    index=["N","NE","E","SE","S","SW","W","NW"].index(params_weather.wind_direction)
)
weight = st.sidebar.number_input(
    "Aircraft weight (kg)", 1000, 15000, 5500
)

# ─── Trigger Recommendation ─────────────────────────────
if st.sidebar.button("Get Recommendation"):
    req = LandingRequest(
        gps=params_city["gps"],
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model="AW139", weight=weight),
    )
    # Determine Performance Class
    pc = "PC2" if weight > 6000 else "PC1"
    resp = generate_recommendation(req)
    resp.path_type = pc
    # Store for persistent display
    st.session_state.resp = resp
    st.session_state.inputs = {
        "weight": weight,
        "weather_cond": weather_cond,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
    }
    st.session_state.city = city

# ─── Persistent Display ─────────────────────────────────
if st.session_state.resp:
    resp = st.session_state.resp
    inputs = st.session_state.inputs
    city = st.session_state.city
    params_city = CITIES[city]

    lat = params_city["gps"].latitude
    lon = params_city["gps"].longitude

    # Map
    st.subheader("Landing Zone Map")
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")
    for obs in params_city["obstacles"]:
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=obs["height"] * 0.2,
            color="red",
            fill=True,
            fill_opacity=0.6,
        ).add_to(m)
    folium.Marker(
        [lat, lon], icon=folium.Icon(color="green", icon="helicopter", prefix="fa")
    ).add_to(m)
    st_folium(m, width="100%", height=500)

    # Recommendation Details
    st.subheader("Landing Recommendation")
    st.markdown(f"**City:** {city}")
    st.markdown(f"**Weather:** {inputs['weather_cond']}")
    performance_desc = "Within PC2 limits" if resp.path_type == "PC2" else "Within PC1 limits"
    st.markdown(f"**Performance Class:** {performance_desc}")
    st.markdown(f"**Approach Direction:** S185")
    st.markdown(f"**Landing Profile:** Confined area AW139 profile")
    st.markdown(f"**LDP:** 170ft")
    risk_label = "Low" if resp.risk_score <= 50 else "High"
    st.markdown(f"**Risk Score:** {resp.risk_score} {risk_label}")

    # PDF Report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"City: {city}", ln=True)
    pdf.cell(0, 8, f"Weather: {inputs['weather_cond']}", ln=True)
    pdf.cell(0, 8, f"Wind: {inputs['wind_speed']} kt {inputs['wind_dir']}", ln=True)
    pdf.cell(0, 8, f"Aircraft Weight: {inputs['weight']} kg", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Performance Class: {performance_desc}", ln=True)
    pdf.cell(0, 8, f"Approach Direction: S185", ln=True)
    pdf.cell(0, 8, f"Landing Profile: Confined area AW139 profile", ln=True)
    pdf.cell(0, 8, f"LDP: 170ft", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Risk Score: {resp.risk_score} {risk_label}", ln=True)
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_bytes,
        file_name="SmartPad_Landing_Report.pdf",
        mime="application/pdf",
    )
