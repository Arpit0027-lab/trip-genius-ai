import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import TripRequest, ItineraryResponse
from ai_service import generate_itinerary
from supabase_client import supabase



app = FastAPI(
    title="TripGenius AI",
    description="AI-powered Personalized Travel Itinerary Planner",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://trip-genius-ai-nine.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Welcome to TripGenius AI!", "status": "Backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/itinerary", response_model=ItineraryResponse)
def create_itinerary(trip: TripRequest):
    try:
        itinerary = generate_itinerary(trip.model_dump())
        trip_record = {
            "starting_city": trip.starting_city,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "budget": trip.budget,
            "travelers": trip.travelers,
            "interests": trip.interests,
            "travel_style": trip.travel_style,
        }
        saved_trip = supabase.table("trips").insert(trip_record).execute()
        if not saved_trip.data:
            raise RuntimeError("Supabase did not return the saved trip.")

        trip_id = saved_trip.data[0]["id"]
        itinerary_record = {
            "trip_id": trip_id,
            "summary": itinerary["summary"],
            "itinerary_data": itinerary,
            "estimated_total_cost": itinerary["estimated_total_cost"],
        }
        supabase.table("itineraries").insert(itinerary_record).execute()
        return itinerary
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to generate or save itinerary: {type(exc).__name__}: {exc}",
        )


@app.get("/api/trips")
def get_saved_trips():
    try:
        trips = (
            supabase.table("trips")
            .select("*, itineraries(*)")
            .order("created_at", desc=True)
            .execute()
        )
        return {"trips": trips.data}
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve saved trips: {type(exc).__name__}: {exc}",
        )


@app.get("/api/trips/{trip_id}")
def get_saved_trip(trip_id: str):
    try:
        result = (
            supabase.table("trips")
            .select("*, itineraries(*)")
            .eq("id", trip_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Trip not found.")
        return result.data[0]
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve trip: {type(exc).__name__}: {exc}",
        )


@app.delete("/api/trips/{trip_id}")
def delete_saved_trip(trip_id: str):
    try:
        supabase.table("itineraries").delete().eq("trip_id", trip_id).execute()
        deleted_trip = (
            supabase.table("trips").delete().eq("id", trip_id).execute()
        )
        if not deleted_trip.data:
            raise HTTPException(
                status_code=404,
                detail="Trip not found or could not be deleted.",
            )
        return {"message": "Trip deleted successfully.", "trip_id": trip_id}
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete trip: {type(exc).__name__}: {exc}",
        )


def build_maps_search(destination: str, category: str, food_type: str = "all"):
    """Build a Google Maps search link without requiring an API key."""
    search_terms = {
        "hotel": "hotels",
        "restaurant": "restaurants",
    }

    term = search_terms[category]
    if category == "restaurant":
        if food_type == "vegetarian":
            term = "vegetarian restaurants"
        elif food_type == "non-vegetarian":
            term = "non vegetarian restaurants"
        elif food_type == "jain":
            term = "Jain food restaurants"

    from urllib.parse import quote_plus

    query = quote_plus(f"{term} in {destination}")
    return {
        "destination": destination,
        "category": category,
        "food_type": food_type if category == "restaurant" else None,
        "source": "Google Maps search",
        "count": 0,
        "places": [],
        "search_url": f"https://www.google.com/maps/search/{query}",
        "notice": (
            "This opens live map search results. This endpoint does not retrieve "
            "or verify individual listings, ratings, availability, or dietary claims. "
            "Confirm Jain/vegetarian preparation directly with the restaurant."
        ),
    }


@app.get("/api/places/hotels")
def search_hotels(destination: str):
    return build_maps_search(destination, "hotel")


@app.get("/api/places/restaurants")
def search_restaurants(destination: str, food_type: str = "all"):
    allowed_food_types = {"all", "vegetarian", "non-vegetarian", "jain"}
    if food_type not in allowed_food_types:
        raise HTTPException(
            status_code=400,
            detail="food_type must be all, vegetarian, non-vegetarian, or jain.",
        )
    return build_maps_search(destination, "restaurant", food_type)
