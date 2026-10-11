from pydantic import BaseModel, Field
from typing import List


class TripRequest(BaseModel):
    starting_city: str
    destination: str
    start_date: str
    end_date: str
    budget: float = Field(gt=0)
    travelers: int = Field(ge=1, le=50)
    interests: List[str]
    travel_style: str


class Activity(BaseModel):
    time: str
    activity: str
    estimated_cost: float


class DayPlan(BaseModel):
    day: int
    title: str
    activities: List[Activity]


class ItineraryResponse(BaseModel):
    destination: str
    summary: str
    days: List[DayPlan]
    estimated_total_cost: float
    travel_tips: List[str]