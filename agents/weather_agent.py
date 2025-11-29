"""WeatherAgent

Queries Open-Meteo (free) for simplified weather information.
"""
import requests
from datetime import datetime

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherAgent:
    @staticmethod
    def geocode_place(place_name: str):
        params = {"q": place_name, "format": "json", "limit": 1}
        resp = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": "ai-agent/1.0"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Could not geocode place: {place_name}")
        return float(data[0]["lat"]), float(data[0]["lon"])

    @staticmethod
    def run(destination: str, date: str):
        """Return simplified weather info for `destination` on `date`.

        date: YYYY-MM-DD
        """
        lat, lon = WeatherAgent.geocode_place(destination)
        # Open-Meteo daily forecast: choose commonly-supported daily fields
        # `precipitation_probability_mean` may not be available on all endpoints, use `precipitation_sum` instead.
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
            "timezone": "UTC",
            "start_date": date,
            "end_date": date,
        }
        # allow one retry if the API says the requested date is out of allowed range
        attempts = 0
        while True:
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
            try:
                resp.raise_for_status()
                break
            except Exception as e:
                attempts += 1
                # try to parse JSON error to detect allowed range
                try:
                    err = resp.json()
                    reason = err.get("reason", "") if isinstance(err, dict) else ""
                except Exception:
                    reason = resp.text

                if attempts == 1 and isinstance(reason, str) and "out of allowed range" in reason:
                    # extract the allowed end date and retry with that end date
                    import re

                    m = re.search(r"from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", reason)
                    if m:
                        allowed_start, allowed_end = m.group(1), m.group(2)
                        # clamp requested start/end to allowed_end
                        params["start_date"] = allowed_end
                        params["end_date"] = allowed_end
                        continue

                body = resp.text
                raise RuntimeError(f"Open-Meteo request failed: {e}\nResponse body: {body}")
        j = resp.json()
        daily = j.get("daily", {})
        if not daily:
            raise ValueError("No weather data returned")

        simplified = {
            "destination": destination,
            "date": date,
            "lat": lat,
            "lon": lon,
            "temp_max": daily.get("temperature_2m_max", [None])[0],
            "temp_min": daily.get("temperature_2m_min", [None])[0],
            "precipitation_sum_mm": daily.get("precipitation_sum", [None])[0],
            "weathercode": daily.get("weathercode", [None])[0],
        }

        # Derive a simple summary
        try:
            ps = simplified.get("precipitation_sum_mm")
            if ps is None:
                umbrella = "unknown"
            elif ps > 5:
                umbrella = "high"
            elif ps > 0:
                umbrella = "possible"
            else:
                umbrella = "low"
        except Exception:
            umbrella = "unknown"

        simplified["umbrella_recommendation"] = umbrella
        return simplified
