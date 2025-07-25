import random
from app.models import LandingRequest, LandingResponse

def generate_recommendation(request: LandingRequest) -> LandingResponse:
    warnings = []

    # Rule 1: Dangerous wind
    if request.weather.wind_speed > 30:
        warnings.append("High wind speed: risky landing conditions.")

    # Rule 2: Heavy aircraft
    if request.aircraft.weight > 6000:
        warnings.append("Heavy aircraft: requires longer clearance zone.")

    # Rule 3: Risk score calculation
    risk_score = 0
    risk_score += request.weather.wind_speed  # wind adds direct risk
    risk_score += 10 if "AW139" in request.aircraft.model else 5
    risk_score = min(risk_score, 100)

    # Rule 4: Choose landing profile
    path_type = "PC2" if risk_score < 50 else "PC1"
    direction = random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

    return LandingResponse(
        path_type=path_type,
        direction=direction,
        risk_score=risk_score,
        warnings=warnings
    )
