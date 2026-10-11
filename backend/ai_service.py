import os
import json
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
You are an expert travel planner specializing in destinations across India.

Create a practical, personalized travel itinerary using these preferences:

Starting city: {trip_data['starting_city']}
Destination: {trip_data['destination']}
Start date: {trip_data['start_date']}
End date: {trip_data['end_date']}
Budget in INR: {trip_data['budget']}
Number of travelers: {trip_data['travelers']}
Interests: {', '.join(trip_data['interests'])}
Travel style: {trip_data['travel_style']}

Return exactly one valid JSON object with this structure:

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
- Include morning, afternoon, and evening activities for every day.
- Personalize activities using the interests and travel style.
- Consider the budget and number of travelers.
- Include relevant attractions, food, transportation, and experiences.
- All costs must be numeric values in INR, not strings.
- Every activity must contain time, activity, and estimated_cost.
- Every day must contain day, title, and activities.
- The final object must contain destination, summary, days,
  estimated_total_cost, and travel_tips.
- Keep the response concise but complete.
- Do not invent precise opening hours or claim prices are verified.
- Return valid JSON only, without Markdown or additional explanations.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional travel planner specializing in India. "
                    "Return one complete, valid JSON object matching the user's "
                    "requested structure. Use double quotes for JSON keys and strings. "
                    "Do not use Markdown or code fences. Keep the output concise "
                    "and ensure the JSON is complete."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        max_tokens=4096,
    )

    choice = response.choices[0]
    content = choice.message.content

    print("Groq finish reason:", choice.finish_reason)
    print("Groq response length:", len(content or ""))
    print("Groq response ending:", repr((content or "")[-500:]))

    if choice.finish_reason == "length":
        raise ValueError(
            "The AI response reached its output token limit. "
            "Try a shorter trip."
        )

    if not content:
        raise ValueError("The AI returned an empty response.")

    content = content.strip()

    # Remove Markdown code fences if present.
    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    # Parse the AI response as JSON.
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        print("Invalid JSON returned by Groq:")
        print(f"Error: {exc}")
        print("Full AI response:")
        print(content)

        raise ValueError(
            "The AI returned invalid JSON. Please try again."
        ) from exc

    # Validate the required response fields.
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
        if not isinstance(day, dict):
            raise ValueError("Each day must be a JSON object.")

        if not {"day", "title", "activities"}.issubset(day):
            raise ValueError(
                "A day in the AI response is missing required fields."
            )

        if not isinstance(day["activities"], list):
            raise ValueError("The activities field must be a list.")

        for activity in day["activities"]:
            if not isinstance(activity, dict):
                raise ValueError("Each activity must be a JSON object.")

            required_activity_fields = {
                "time",
                "activity",
                "estimated_cost",
            }

            if not required_activity_fields.issubset(activity):
                raise ValueError(
                    "An activity is missing required fields."
                )

    return result