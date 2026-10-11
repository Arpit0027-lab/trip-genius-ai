import os
import json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


def generate_itinerary(trip_data: dict) -> dict:
    if client is None:
        raise RuntimeError(
            "GROQ_API_KEY is missing from the backend .env file."
        )

    prompt = f"""
You are an expert travel planner.

Create a practical, personalized travel itinerary using these preferences:

Starting city: {trip_data['starting_city']}
Destination: {trip_data['destination']}
Start date: {trip_data['start_date']}
End date: {trip_data['end_date']}
Budget in INR: {trip_data['budget']}
Number of travelers: {trip_data['travelers']}
Interests: {', '.join(trip_data['interests'])}
Travel style: {trip_data['travel_style']}

Return ONLY one valid JSON object using this exact structure:

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
- Generate one day for every date from the start date through the end date.
- Include morning, afternoon, and evening activities for each day.
- Personalize activities according to the interests and travel style.
- Consider the total budget and number of travelers.
- Use INR for all estimated costs.
- All costs must be numbers, not strings.
- Every activity must contain time, activity, and estimated_cost.
- Every day must contain day, title, and activities.
- The final object must contain destination, summary, days,
  estimated_total_cost, and travel_tips.
- Do not invent precise opening hours or claim prices are verified.
- Return valid JSON only. Do not use Markdown fences or explanations.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional travel planner. "
                    "Return a complete JSON object matching the requested "
                    "schema. Do not return Markdown or additional text."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The AI returned an empty response.")

    content = content.strip()

    # Remove Markdown fences if the model unexpectedly includes them.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"The AI returned invalid JSON: {exc}. "
            f"Response preview: {content[:300]}"
        ) from exc

    # Basic response validation before returning to FastAPI.
    required_fields = {
        "destination",
        "summary",
        "days",
        "estimated_total_cost",
        "travel_tips",
    }

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise ValueError(
            f"The AI response is missing fields: {sorted(missing_fields)}"
        )

    if not isinstance(result["days"], list) or not result["days"]:
        raise ValueError("The AI response contains no daily itinerary.")

    for day in result["days"]:
        if not {"day", "title", "activities"}.issubset(day):
            raise ValueError("A day in the AI response is missing required fields.")

        if not isinstance(day["activities"], list):
            raise ValueError("The activities field must be a list.")

        for activity in day["activities"]:
            if not {
                "time",
                "activity",
                "estimated_cost",
            }.issubset(activity):
                raise ValueError(
                    "An activity in the AI response is missing required fields."
                )

    return result