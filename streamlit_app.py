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
    city = st.selectbox("City (Helipad)", ["Riyadh (KFMC)", "Jeddah", "Taif", "Dammam"])
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
    st.session_state.resp = resp
    st.session_state.inputs = {
        "city": city,
        "weather": weather_cond,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "weight": weight
    }

# ─── Display map & results ──────────────────────────────
if "resp" in st.session_state:
    resp   = st.session_state.resp
    inputs = st.session_state.inputs
    data   = SCENARIOS[inputs["city"]]
    lat, lon = data["gps"].latitude, data["gps"].longitude

    # Map with cleared landing area, obstacles & arrow
    st.subheader("Landing Zone Map")
    m = folium.Map(location=[lat, lon], zoom_start=15, tiles="OpenStreetMap")

    # Cleared landing area (200 m radius)
    folium.Circle(
        location=[lat, lon],
        radius=200,
        color="green",
        fill=True,
        fill_opacity=0.2,
        tooltip="Cleared Landing Area (200 m radius)"
    ).add_to(m)

    # Obstacle markers
    for obs in data["obstacles"]:
        folium.CircleMarker(
            location=[obs["lat"], obs["lon"]],
            radius=obs["height"] * 0.2,
            color="red",
            fill=True,
            fill_opacity=0.6,
            tooltip=f"Obstacle: {obs['height']} ft"
        ).add_to(m)

    # Helipad marker
    folium.Marker(
        [lat, lon],
        icon=folium.Icon(color="blue", icon="home", prefix="fa"),
        tooltip="Helipad"
    ).add_to(m)

    # Landing direction arrow
    OFF = {
        "N":  (0.01,   0),
        "NE": (0.007, 0.007),
        "E":  (0,     0.01),
        "SE": (-0.007,0.007),
        "S":  (-0.01,  0),
        "SW": (-0.007,-0.007),
        "W":  (0,    -0.01),
        "NW": (0.007,-0.007),
    }
    dlat, dlon = OFF[resp.direction]
    folium.PolyLine(
        [[lat, lon], [lat + dlat, lon + dlon]],
        color="blue", weight=3,
        tooltip=f"Landing Dir: {resp.direction}"
    ).add_to(m)

    st_folium(m, width="100%", height=400)

    # Recommendation details
    st.subheader("Landing Recommendation")
    st.markdown(f"- **City:** {inputs['city']}")
    st.markdown(f"- **Weather:** {inputs['weather']}")
    st.markdown(f"- **Landing Type:** {resp.path_type}")
    st.markdown(f"- **Approach Direction:** {resp.direction}")
    st.markdown(f"- **Landing Profile:** Confined area AW139 profile")
    st.markdown(f"- **LDP:** 170 ft")
    st.markdown(f"- **Decision Height (DH):** {resp.decision_height} ft")
    risk_label = "Low" if resp.risk_score <= 50 else "High"
    st.markdown(f"- **Risk Score:** {resp.risk_score} ({risk_label})")

    # PDF download
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"City: {inputs['city']}", ln=True)
    pdf.cell(0, 8, f"Weather: {inputs['weather']}", ln=True)
    pdf.cell(0, 8, f"Wind: {inputs['wind_speed']} kt {inputs['wind_dir']}", ln=True)
    pdf.cell(0, 8, f"Aircraft Weight: {inputs['weight']} kg", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Landing Type: {resp.path_type}", ln=True)
    pdf.cell(0, 8, f"Approach Direction: {resp.direction}", ln=True)
    pdf.cell(0, 8, f"Landing Profile: Confined area AW139 profile", ln=True)
    pdf.cell(0, 8, f"LDP: 170 ft", ln=True)
    pdf.cell(0, 8, f"Decision Height (DH): {resp.decision_height} ft", ln=True)
    pdf.ln(5)
    pdf.cell(0, 8, f"Risk Score: {resp.risk_score} ({risk_label})", ln=True)
    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="SmartPad_Landing_Report.pdf",
        mime="application/pdf",
    )
