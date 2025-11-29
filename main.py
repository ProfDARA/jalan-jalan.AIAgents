"""Main planner agent runner

Usage examples:
  python main.py --destination "Bali, Indonesia" --date 2025-12-20 --origin "Jakarta, Indonesia"
"""
import argparse
import json
from agents.weather_agent import WeatherAgent
from agents.location_agent import LocationAgent
from agents.cost_agent import CostAgent


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

    print("Running WeatherAgent...")
    weather = WeatherAgent.run(destination, date)

    print("Running LocationAgent...")
    places = LocationAgent.run(weather, destination)

    # determine origin coords
    if args.origin:
        origin_coords = geocode(args.origin)
    else:
        # if no origin given, assume same coordinates as destination (local trip)
        origin_coords = (weather.get("lat"), weather.get("lon"))

    dest_coords = (weather.get("lat"), weather.get("lon"))

    print("Running CostAgent...")
    cost = CostAgent.run(places, origin_coords=origin_coords, dest_coords=dest_coords, nights=args.nights, hotel_tier=args.hotel_tier)

    final = {
        "destination": destination,
        "date": date,
        "weather": weather,
        "recommended_places": places,
        "costs": cost,
    }

    print(json.dumps(final, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
