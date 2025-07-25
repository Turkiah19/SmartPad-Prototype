import streamlit as st
from app.logic import generate_recommendation
from app.models import LandingRequest, GPS, Weather, Aircraft

st.title("🚁 SmartPad VTOL Landing Assistant")

st.sidebar.header("Flight Inputs")
lat = st.sidebar.number_input("Latitude", value=24.7136, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=46.6753, format="%.4f")
wind_speed = st.sidebar.slider("Wind speed (knots)", 0, 60, 35)
wind_dir = st.sidebar.selectbox("Wind direction", ["N","NE","E","SE","S","SW","W","NW"])
model = st.sidebar.text_input("Aircraft model", value="AW139")
weight = st.sidebar.number_input("Aircraft weight (kg)", 1000, 10000, 5500)

if st.sidebar.button("Get Recommendation"):
    req = LandingRequest(
        gps=GPS(latitude=lat, longitude=lon),
        weather=Weather(wind_speed=wind_speed, wind_direction=wind_dir),
        aircraft=Aircraft(model=model, weight=weight)
    )
    resp = generate_recommendation(req)
    st.subheader("🛬 Landing Recommendation")
    st.write(f"**Path Type:** {resp.path_type}")
    st.write(f"**Direction:** {resp.direction}")
    st.write(f"**Risk Score:** {resp.risk_score}")
    if resp.warnings:
        st.warning("  \n".join(resp.warnings))
