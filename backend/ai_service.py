import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key) if api_key else None


def generate_itinerary(trip_data: dict) -> dict:
    if client is None:
        raise RuntimeError("GROQ_API_KEY is missing from the backend .env file.")

    prompt = f"""
You are an expert travel planner.

Create a practical, personalized itinerary using these preferences:

Starting city: {trip_data['starting_city']}
Destination: {trip_data['destination']}
Start date: {trip_data['start_date']}
End date: {trip_data['end_date']}
Budget in INR: {trip_data['budget']}
Travelers: {trip_data['travelers']}
Interests: {', '.join(trip_data['interests'])}
Travel style: {trip_data['travel_style']}

Return ONLY valid JSON with this structure:
{{
  "destination": "string",
  "summary": "string",
  "days": [
    {{
      "day": 1,
      "title": "string",
      "activities": [
        {{
          "time": "Morning",
          "activity": "string",
          "estimated_cost": 500
        }}
      ]
    }}
  ],
  "estimated_total_cost": 5000,
  "travel_tips": ["string"]
}}

Requirements:
- Generate one day for each date in the requested date range.
- Respect the stated budget as much as possible.
- Include morning, afternoon, and evening activities.
- Consider the travel style and interests.
- Use INR for estimated costs.
- Do not invent precise opening hours or claim that prices are verified.
- Return valid JSON without Markdown fences.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": "You generate useful travel plans and valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)