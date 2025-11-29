"""CostAgent

Provides rough cost estimates for transport, hotel, and attraction tickets.
"""
from math import radians, sin, cos, sqrt, atan2
from typing import List


def haversine(lat1, lon1, lat2, lon2):
    # returns distance in kilometers
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class CostAgent:
    @staticmethod
    def estimate_transport(origin_coords, dest_coords):
        # very rough per-km cost estimates in USD
        km = haversine(origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1])
        # If distance small, assume local transport; long -> intercity
        if km < 5:
            taxi = max(1.5 * km, 2.0)
            bus = max(0.5 * km, 1.0)
        else:
            taxi = 0.6 * km
            bus = 0.25 * km

        transport = {
            "distance_km": round(km, 2),
            "taxi_usd": round(taxi, 2),
            "bus_usd": round(bus, 2),
            "suggested_mode": "bus" if bus < taxi else "taxi",
        }
        return transport

    @staticmethod
    def estimate_hotel(nights=1, quality="mid"):
        # simple tiers
        tiers = {"budget": 40, "mid": 80, "premium": 180}
        base = tiers.get(quality, 80)
        return {"nights": nights, "price_per_night_usd": base, "total_usd": base * nights}

    @staticmethod
    def estimate_tickets(spots: List[dict]):
        # simple heuristics by type
        type_map = {
            "museum": 10,
            "beach": 0,
            "park": 0,
            "market": 0,
            "tour": 15,
            "garden": 5,
            "cafe": 0,
            "brewery": 8,
            "mall": 0,
        }
        items = []
        total = 0
        for s in spots:
            t = s.get("type", "tour")
            price = type_map.get(t, 10)
            items.append({"name": s.get("name"), "type": t, "ticket_usd": price})
            total += price
        return {"items": items, "total_usd": total}

    @staticmethod
    def run(recommended_places: List[dict], origin_coords=(0, 0), dest_coords=(0, 0), nights=1, hotel_tier="mid"):
        transport = CostAgent.estimate_transport(origin_coords, dest_coords)
        hotel = CostAgent.estimate_hotel(nights=nights, quality=hotel_tier)
        tickets = CostAgent.estimate_tickets(recommended_places)

        breakdown = {
            "transport": transport,
            "hotel": hotel,
            "tickets": tickets,
            "grand_total_usd": round(transport.get("taxi_usd", 0) + hotel["total_usd"] + tickets["total_usd"], 2),
        }
        return breakdown
