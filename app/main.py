from fastapi import FastAPI
from app.models import LandingRequest, LandingResponse
from app.logic import generate_recommendation

app = FastAPI()

@app.post("/recommend", response_model=LandingResponse)
def recommend_path(request: LandingRequest):
    return generate_recommendation(request)
