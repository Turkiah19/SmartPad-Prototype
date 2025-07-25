from pydantic import BaseModel
from typing import List

class GPS(BaseModel):
    latitude: float
    longitude: float

class Weather(BaseModel):
    wind_speed: float  # knots
    wind_direction: str

class Aircraft(BaseModel):
    model: str
    weight: float  # kg

class LandingRequest(BaseModel):
    gps: GPS
    weather: Weather
    aircraft: Aircraft

class LandingResponse(BaseModel):
    path_type: str
    direction: str
    risk_score: int
    warnings: List[str]
