from app.models import LandingRequest, LandingResponse

# ─── Constants ─────────────────────────────────────────
# Max obstacle height (ft) in each landing direction
OBSTACLE_MAX_HEIGHT = {
    "N":  80,
    "NE": 75,
    "E":  90,
    "SE": 100,
    "S":  85,
    "SW": 70,
    "W":  95,
    "NW": 60,
}
MIN_CLEARANCE_FT = 120

# Mapping each wind direction to the opposite landing direction
OPPOSITE = {
    "N":  "S",
    "NE": "SW",
    "E":  "W",
    "SE": "NW",
    "S":  "N",
    "SW": "NE",
    "W":  "E",
    "NW": "SE",
}

def generate_recommendation(req: LandingRequest) -> LandingResponse:
    # 1) Determine landing direction = opposite of wind
    wind_dir = req.weather.wind_direction
    landing_dir = OPPOSITE.get(wind_dir, "N")

    # 2) Compute Decision Height (DH)
    obstacle_ht = OBSTACLE_MAX_HEIGHT.get(landing_dir, 0)
    decision_height = obstacle_ht + MIN_CLEARANCE_FT

    # 3) Simple risk scoring (adjust as needed)
    risk_score = int(req.weather.wind_speed + req.aircraft.weight / 100)
    risk_score = min(risk_score, 100)  # cap at 100

    warnings = []
    if req.weather.wind_speed > 30:
        warnings.append("High wind speed: risky landing conditions.")
    if req.aircraft.weight > 6000:
        warnings.append("Heavy aircraft: requires longer clearance zone.")

    # 4) Always a confined-area landing type
    return LandingResponse(
        path_type="Confined Area",
        direction=landing_dir,
        decision_height=decision_height,
        risk_score=risk_score,
        warnings=warnings,
    )
