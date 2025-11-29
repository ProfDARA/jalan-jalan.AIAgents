# Projekt Full ADK Multi-Agent System with Gemini-2.0-Flash

from adk import Agent, Tool, Router
import requests
from openai import OpenAI


# ------------------------------------------------------------
# LLM Client (Gemini 2.0 Flash + free alternatives)
# ------------------------------------------------------------
llm_client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/",
    api_key="YOUR_GEMINI_API_KEY"
)

DEFAULT_MODEL = "gemini-2.0-flash"


# ------------------------------------------------------------
# Weather Agent (Free Weather API: Open-Meteo.com)
# ------------------------------------------------------------
class WeatherTool(Tool):
    name = "get_weather"
    description = "Get weather forecast using Open-Meteo API (free)."

    def run(self, destination: str, date: str) -> dict:
        # Why: Open-Meteo is free and good for real use
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo = requests.get(geocode_url, params={"name": destination}).json()

        if "results" not in geo:
            return {"error": "Destination not found"}

        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather = requests.get(weather_url, params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation",
            "timezone": "auto"
        }).json()

        return weather


weather_agent = Agent(
    name="weather_agent",
    model=DEFAULT_MODEL,
    instructions="Ambil cuaca dari Open-Meteo API.",
    tools=[WeatherTool()]
)


# ------------------------------------------------------------
# Location Suggestion Agent
# ------------------------------------------------------------
class LocationTool(Tool):
    name = "suggest_locations"
    description = "Generate location recommendations using Gemini."

    def run(self, destination: str, weather: dict) -> dict:
        # Why: Use LLM to reason based on weather patterns
        prompt = f"""
        Kamu adalah expert wisata.
        Berdasarkan cuaca berikut:

        {weather}

        Rekomendasikan 5 tempat wisata yang cocok di {destination}
        Format JSON: {{"places": [...]}}
        """
        res = llm_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.parsed


location_agent = Agent(
    name="location_agent",
    model=DEFAULT_MODEL,
    instructions="Gunakan Gemini untuk rekomendasi tempat wisata.",
    tools=[LocationTool()]
)


# ------------------------------------------------------------
# Cost Estimation Agent
# ------------------------------------------------------------
class CostTool(Tool):
    name = "calculate_cost"
    description = "Estimate travel cost using LLM + average public data."

    def run(self, destination: str, places: list) -> dict:
        prompt = f"""
        Buat estimasi biaya perjalanan ke {destination}
        untuk mengunjungi tempat:
        {places}

        Detailkan:
        - Transport
        - Hotel per malam
        - Tiket masuk
        - Total

        Format JSON.
        """
        res = llm_client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.parsed


cost_agent = Agent(
    name="cost_agent",
    model=DEFAULT_MODEL,
    instructions="Hitung estimasi biaya wisata.",
    tools=[CostTool()]
)


# ------------------------------------------------------------
# Router (Multi-Agent Coordinator)
# ------------------------------------------------------------
planner_router = Router(
    name="tourist_router",
    instructions="Koordinasikan semua sub-agent.",
    agents=[weather_agent, location_agent, cost_agent]
)


# ------------------------------------------------------------
# Main Planner Agent
# ------------------------------------------------------------
planner_agent = Agent(
    name="planner_agent",
    model=DEFAULT_MODEL,
    instructions="""
    Kamu adalah agen utama perencanaan wisata.
    Urutan:
    1) weather_agent → cuaca
    2) location_agent → rekomendasi
    3) cost_agent → estimasi biaya
    """,
    router=planner_router
)


# ------------------------------------------------------------
# Entry Function
# ------------------------------------------------------------
def create_itinerary(destination: str, date: str):
    weather = weather_agent.run({"destination": destination, "date": date})
    places = location_agent.run({"destination": destination, "weather": weather})
    costs = cost_agent.run({"destination": destination, "places": places["places"]})

    return {
        "destination": destination,
        "date": date,
        "weather": weather,
        "places": places,
        "costs": costs
    }


if __name__ == "__main__":
    result = create_itinerary("Bali", "2025-07-10")
    print(result)
