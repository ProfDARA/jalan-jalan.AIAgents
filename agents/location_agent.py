"""LocationAgent

Uses a generative model (Gemini) when available to suggest recommended spots
based on weather. Falls back to a heuristic generator if no model/key is configured.
"""
import os
from typing import List

try:
    # optional: google generative ai client
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False


class LocationAgent:
    @staticmethod
    def prompt_for_spots(destination: str, weather: dict) -> str:
        # Compose a prompt for Gemini-like models
        temp_max = weather.get("temp_max")
        umbrella = weather.get("umbrella_recommendation")
        date = weather.get("date")
        prompt = (
            f"You are a travel assistant. For {destination} on {date}, the forecast: "
            f"max temp {temp_max}, umbrella {umbrella}. "
            "Return 3 recommended places to visit, each with name, type, a one-line reason, and best time to visit. "
            "Output as JSON list of objects with keys: name, type, reason, best_time."
        )
        return prompt

    @staticmethod
    def call_gemini(prompt: str) -> List[dict]:
        # This function attempts to call Google Generative API (gemini-2.0-flash)
        api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GENAI_API_KEY")
        if not GENAI_AVAILABLE or not api_key:
            raise RuntimeError("Generative AI client not available or API key missing")
        # configure client; actual usage may vary by installed SDK version
        genai.configure(api_key=api_key)
        resp = genai.generate_text(model="gemini-2.0-flash", prompt=prompt)
        text = resp.text if hasattr(resp, "text") else str(resp)
        # Try to parse JSON from model output
        import json

        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            # If model returned plain text, we'll fallback to heuristic parse
            return []

    @staticmethod
    def heuristic(destination: str, weather: dict) -> List[dict]:
        # Simple rules based on umbrella recommendation and temperature
        umbrella = weather.get("umbrella_recommendation", "unknown")
        temp = weather.get("temp_max") or 25
        spots = []
        if umbrella == "high":
            spots = [
                {"name": "City Museum", "type": "museum", "reason": "Indoor exhibits to avoid rain", "best_time": "morning"},
                {"name": "Indoor Food Market", "type": "market", "reason": "Local food and shelter from rain", "best_time": "afternoon"},
                {"name": "Mall & Cultural Center", "type": "mall", "reason": "Shopping and local shows", "best_time": "evening"},
            ]
        elif umbrella == "low":
            if temp >= 28:
                spots = [
                    {"name": "Seaside Promenade", "type": "beach", "reason": "Great sunny day for walking", "best_time": "morning"},
                    {"name": "City Park", "type": "park", "reason": "Picnic and outdoor activities", "best_time": "afternoon"},
                    {"name": "Rooftop Cafe", "type": "cafe", "reason": "Views and refreshments", "best_time": "evening"},
                ]
            else:
                spots = [
                    {"name": "Historic Old Town", "type": "walking", "reason": "Pleasant temps for strolling", "best_time": "morning"},
                    {"name": "Botanical Garden", "type": "garden", "reason": "Relaxed outdoor visit", "best_time": "afternoon"},
                    {"name": "Local Brewery", "type": "brewery", "reason": "Indoor tasting with local food", "best_time": "evening"},
                ]
        else:
            spots = [
                {"name": "City Highlights Tour", "type": "tour", "reason": "Balanced mix of indoor/outdoor", "best_time": "morning"},
                {"name": "Local Market", "type": "market", "reason": "See local life", "best_time": "afternoon"},
                {"name": "Popular Cafe", "type": "cafe", "reason": "Rest and sample local cuisine", "best_time": "evening"},
            ]
        return spots

    @staticmethod
    def run(weather_data: dict, destination: str) -> List[dict]:
        # Try real model first if configured
        prompt = LocationAgent.prompt_for_spots(destination, weather_data)
        try:
            spots = LocationAgent.call_gemini(prompt)
            if spots:
                return spots
        except Exception:
            pass

        # Fallback heuristics
        return LocationAgent.heuristic(destination, weather_data)
