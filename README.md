# AI Planner Agents (Gemini-friendly)

This small project demonstrates a 3-agent planner using free services and an optional Gemini (Google) model.

Structure (matches your pseudocode):

- `WeatherAgent`: queries `open-meteo.com` and uses Nominatim (OpenStreetMap) for geocoding.
- `LocationAgent`: attempts to use `gemini-2.0-flash` (via `google.generativeai`) when `GOOGLE_API_KEY` is set. Falls back to simple heuristics.
- `CostAgent`: provides rough transport, hotel, and ticket cost estimates.

Quick start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate; pip install -r "requirements.txt"
```

2. (Optional) If you have access to Google Generative API, set env var `GOOGLE_API_KEY`.

3. Run an example:

```powershell
python main.py --destination "Yogyakarta, Indonesia" --date 2025-12-15 --origin "Jakarta, Indonesia" --nights 2 --hotel_tier mid
```

Notes

- This project does not include API keys or direct Gemini credentials. If you want `LocationAgent` to use Gemini, install the appropriate SDK and set `GOOGLE_API_KEY`.
- The code uses free public endpoints (Nominatim and Open-Meteo). Respect their usage policies and rate limits.

Next steps you might want me to do:

- Wire a proper Gemini call with exact SDK usage for your environment.
- Add unit tests and CI.
- Package as a small CLI or web service.
