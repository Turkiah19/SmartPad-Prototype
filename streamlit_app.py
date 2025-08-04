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

# ─── 1) Pilot & Aircraft Static Cards ───────────────────
st.header("Pilot & Aircraft Information")
pilot_col, aircraft_col = st.columns(2)
with pilot_col:
    st.subheader("Pilot Info")
    st.markdown("""
    - **Name:** Capt. Khalid Al-Huwaidi  
    - **License:** CPL IR RW  
    - **Total Hours:** 1500 h  
    - **Callsign:** Hawk-1
    """)
with aircraft_col:
    st.subheader("Aircraft Info")
    st.markdown("""
    - **Model:** AW139  
    - **Max Takeoff Weight:** 7000 kg  
    - **Registration:** HZ-ABC  
    - **MTOW Category:** Medium  
    """)

# ─── 2) Flight Inputs (inline) ───────────────────────────
st.header("Flight Inputs")

# 2a. Static lists for city & weather
CITIES = {
    "Riyadh (KFMC)": GPS(latitude=24.688000, longitude=46.705200),
    "Jeddah":      GPS(latitude=21.485800, longitude=39.192500),
    "Taif":        GPS(latitude=21.285400, longitude=40.405800),
    "Dammam":      GPS(latitude=26.392700, longitude=49.977700),
}
WEATHERS = {
    "Clear":      Weather(wind_speed=10, wind_direction="NE"),
    "Rain":       Weather(wind_speed=15, wind_direction="SE"),
    "Fog":        Weather(wind_speed=5,  wind_direction="N"),
    "Dust Storm": Weather(wind_speed=20, wind_direction="NW"),
}

# 2b. City & Weather selection
col1, col2 = st.columns(2)
with col1:
    city = st.selectbox("City (Helipad)", list(CITIES.keys()))
with col2:
    weather_cond = st.selectbox("Weather Condition", list(WEATHERS.keys()))

# 2c. Wind & Direction & Weight
col1, col2, col3 = st.columns(3)
with col1:
    wind_speed = st.slider(
        "Wind speed (knots)", 
        0, 80, 
        int(WEATHERS[weather_cond].wind_speed)
    )
with col2:
    wind_dir = st.selectbox(
        "Wind direction",
        ["N","NE","E","SE","S","SW","W","NW"],
        index=["N","NE","E","SE","S","SW","W","NW"]
              .index(WEATHERS[weather_cond].wind_direction)
    )
with col3:
    weight = st.number_input(
        "Aircraft weight (kg)", 
        1000, 15000, 
        value=5500
    )

# ─── 3) Get Recommendation ───────────────────────────────
if st.button("Get Recommendation"):
    # Build request
    req = LandingRequest(
        gps=CITIES[city],
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model="AW139", weight=weight),
    )
    # Call logic
    resp = generate_recommendation(req)

    # Store for display
    st.session_state.resp = resp
    st.session_state.inputs = {
        "city": city,
        "weather_cond": weather_cond,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "weight": weight,
    }

# ─── 4) Persistent Display ───────────────────────────────
if "resp" in st.session_state:
    resp   = st.session_state.resp
    inputs = st.session_state.inputs
    loc    = CITIES[inputs["city"]]

    # 4a. Map
    st.subheader("Landing Zone Map")
    m = folium.Map(
        location=[loc.latitude, loc.longitude],
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    # Mark helipad
    folium.Marker(
        [loc.latitude, loc.longitude],
        icon=folium.Icon(color="green", icon="helicopter", prefix="fa")
    ).add_to(m)
    # Obstacles are drawn inside generate_recommendation if desired
    st_folium(m, width="100%", height=400)

    # 4b. Recommendation Details
    st.subheader("Landing Recommendation")
    st.markdown(f"- **City:** {inputs['city']}")
    st.markdown(f"- **Weather:** {inputs['weather_cond']}")
    st.markdown(f"- **Landing Type:** {resp.path_type}")
    st.markdown(f"- **Approach Direction:** {resp.direction}")
    st.markdown(f"- **Landing Profile:** Confined area AW139 profile")
    st.markdown(f"- **LDP:** 170 ft")
    st.markdown(f"- **Decision Height (DH):** {resp.decision_height} ft")
    risk_label = "Low" if resp.risk_score <= 50 else "High"
    st.markdown(f"- **Risk Score:** {resp.risk_score} ({risk_label})")

    # 4c. PDF Download
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "SmartPad VTOL Landing Report", ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(5)
    pdf.cell(0, 8, f"Date/Time: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", ln=True)
    pdf.cell(0, 8, f"City: {inputs['city']}", ln=True)
    pdf.cell(0, 8, f"Weather: {inputs['weather_cond']}", ln=True)
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
