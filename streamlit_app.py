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

# ─── Helipad Information ─────────────────────────────────
HELIPAD_NAME = "KFMC (King Fahad Medical City)"
HELIPAD_LAT = 24 + 41.27 / 60  # N24°41.27
HELIPAD_LON = 46 + 42.31 / 60  # E46°42.31

# ─── Scenario Presets with Weather Conditions ────────────
SCENARIOS = {
    "Clear Skies (Riyadh Center)": {
        "weather": Weather(wind_speed=10, wind_direction="NE"),
        "condition": "Clear",
        "aircraft": Aircraft(model="AW139", weight=5500),
        "obstacles": [
            {"lat": 24.7140, "lon": 46.6760, "height": 50},
            {"lat": 24.7130, "lon": 46.6740, "height": 80},
        ],
    },
    "Rainstorm (Jeddah Coast)": {
        "weather": Weather(wind_speed=15, wind_direction="SE"),
        "condition": "Rain",
        "aircraft": Aircraft(model="AW139", weight=5400),
        "obstacles": [
            {"lat": 21.4870, "lon": 39.1935, "height": 30},
            {"lat": 21.4840, "lon": 39.1910, "height": 60},
        ],
    },
    "Foggy Morning (Taif)": {
        "weather": Weather(wind_speed=5, wind_direction="N"),
        "condition": "Fog",
        "aircraft": Aircraft(model="AW139", weight=5300),
        "obstacles": [
            {"lat": 21.2860, "lon": 40.4065, "height": 40},
            {"lat": 21.2840, "lon": 40.4040, "height": 70},
        ],
    },
    "Dust Storm (Dammam)": {
        "weather": Weather(wind_speed=20, wind_direction="NW"),
        "condition": "Dust Storm",
        "aircraft": Aircraft(model="AW139", weight=5600),
        "obstacles": [
            {"lat": 26.3935, "lon": 49.9785, "height": 20},
            {"lat": 26.3910, "lon": 49.9760, "height": 90},
        ],
    },
}

# ─── Sidebar: Helipad & Scenario ─────────────────────────
st.sidebar.header("Helipad Location and Name")
st.sidebar.markdown(f"**{HELIPAD_NAME}**")
st.sidebar.markdown(f"Coordinates: N24°41.27 E46°42.31")

st.sidebar.header("Demo Scenario")
scenario_name = st.sidebar.selectbox("Choose a scenario:", list(SCENARIOS.keys()))
params = SCENARIOS[scenario_name]

# ─── Trigger Recommendation ─────────────────────────────
if st.sidebar.button("Get Recommendation"):
    # Build request with static helipad GPS
    req = LandingRequest(
        gps=GPS(latitude=HELIPAD_LAT, longitude=HELIPAD_LON),
        weather=params["weather"],
        aircraft=params["aircraft"],
    )
    # Override PC based on weight
    if req.aircraft.weight > 6000:
        req_pc = "PC2"
    else:
        req_pc = "PC1"
    resp = generate_recommendation(req)
    resp.path_type = req_pc
    st.session_state.resp = resp
    st.session_state.params = params

# ─── Persistent Display ─────────────────────────────────
if st.session_state.resp:
    resp = st.session_state.resp
    params = st.session_state.params

    # ─── Map Visualization ────────────────────────────────
    st.subheader("🗺️ Landing Zone Map")
    m = folium.Map(location=[HELIPAD_LAT, HELIPAD_LON], zoom_start=15, tiles="OpenStreetMap")
    for obs in params["obstacles"]:
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=obs["height"] * 0.2,
            color="red",
            fill=True,
            fill_opacity=0.6,
        ).add_to(m)
    folium.Marker(
        [HELIPAD_LAT, HELIPAD_LON],
        icon=folium.Icon(color="green", icon="helicopter", prefix="fa")
    ).add_to(m)
    st_folium(m, width="100%", height=500)

    # ─── Recommendation Details ───────────────────────────
    st.subheader("🛬 Landing Recommendation")
    # Performance Class
    performance_label = (
        "Within PC1 limits" if resp.path_type == "PC1" else "Within PC2 limits"
    )
    st.markdown(f"**Performance Class:** {performance_label}")
    # Approach Direction
    st.markdown("**Approach Direction:** S185")
    # Landing Profile
    st.markdown("**Landing Profile:** Confined area AW139 profile")
    st.markdown("**LDP:** 170ft")
    # Risk Score
    risk_label = "Low" if resp.risk_score <= 50 else "High"
    st.markdown(f"**Risk Score:** {resp.risk_score} {risk_label}")

    # ─── PDF Report Generation & Download ─────────────────
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"Helipad: {HELIPAD_NAME} ({HELIPAD_LAT:.6f}, {HELIPAD_LON:.6f})", ln=True)
    pdf.cell(0, 8, f"Scenario: {scenario_name}", ln=True)
    pdf.cell(0, 8, f"Condition: {params['condition']}", ln=True)
    pdf.cell(0, 8, f"Wind: {resp.risk_score} kt {params['weather'].wind_direction}", ln=True)
    pdf.cell(0, 8, f"Aircraft: {params['aircraft'].model}, {params['aircraft'].weight} kg", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Performance Class: {performance_label}", ln=True)
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
