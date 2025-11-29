"""Main planner agent runner

Usage examples:
  python main.py --destination "Bali, Indonesia" --date 2025-12-20 --origin "Jakarta, Indonesia"
"""
import argparse
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from agents.weather_agent import WeatherAgent
from agents.location_agent import LocationAgent
from agents.cost_agent import CostAgent
from agents.session import InMemorySessionService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def geocode(place):
    # reuse weather agent geocoder
    return WeatherAgent.geocode_place(place)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--destination", required=True)
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--origin", required=False, default=None)
    p.add_argument("--nights", type=int, default=1)
    p.add_argument("--hotel_tier", choices=["budget", "mid", "premium"], default="mid")
    args = p.parse_args()

    destination = args.destination
    date = args.date

    logger.info("Starting planner for %s on %s", destination, date)

    # Create a session for this planning run
    session_id = InMemorySessionService.create_session({"destination": destination, "date": date})

    # Parallelize weather fetch and origin geocoding (if origin provided)
    with ThreadPoolExecutor(max_workers=2) as ex:
        weather_fut = ex.submit(WeatherAgent.run, destination, date)
        if args.origin:
            origin_fut = ex.submit(geocode, args.origin)
        else:
            origin_fut = None

        logger.info("Waiting for weather and origin geocode results")
        weather = weather_fut.result()
        if origin_fut:
            origin_coords = origin_fut.result()
        else:
            origin_coords = (weather.get("lat"), weather.get("lon"))

    logger.info("Weather fetched: lat=%s lon=%s", weather.get("lat"), weather.get("lon"))

    # Run LocationAgent (sequentially after weather available)
    logger.info("Running LocationAgent...")
    places = LocationAgent.run(weather, destination)

    dest_coords = (weather.get("lat"), weather.get("lon"))

    logger.info("Running CostAgent...")
    cost = CostAgent.run(places, origin_coords=origin_coords, dest_coords=dest_coords, nights=args.nights, hotel_tier=args.hotel_tier)

    # Simple evaluator: score places based on weather and type preferences
    def evaluate_places(places_list, weather_info):
        scores = []
        umbrella = weather_info.get("umbrella_recommendation", "unknown")
        for p in places_list:
            score = 50
            t = p.get("type", "tour")
            if umbrella == "high" and t in ("museum", "mall", "market", "brewery"):
                score += 30
            if umbrella == "low" and t in ("beach", "park", "garden"):
                score += 20
            # temperature preference
            temp = weather_info.get("temp_max") or 25
            if temp >= 28 and t == "beach":
                score += 10
            scores.append({"name": p.get("name"), "score": score})
        return scores

    eval_scores = evaluate_places(places, weather)
    logger.info("Evaluation scores: %s", eval_scores)

    final = {
        "destination": destination,
        "date": date,
        "weather": weather,
        "recommended_places": places,
        "costs": cost,
        "session_id": session_id,
        "evaluation": eval_scores,
    }

    print(json.dumps(final, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
