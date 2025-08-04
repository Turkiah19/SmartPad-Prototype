from fastapi import FastAPI
from app.models import LandingRequest, LandingResponse
from app.logic import generate_recommendation

app = FastAPI(title="SmartPad VTOL Landing API")

@app.post("/recommend", response_model=LandingResponse)
def recommend(request: LandingRequest):
    """
    Generate a landing recommendation including:
    - Confined Area landing type
    - Approach direction opposite to wind
    - Decision Height = obstacle height + 120 ft
    - Risk score & warnings
    """
    return generate_recommendation(request)
