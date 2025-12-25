import heapq
from typing import Sequence

from ..models.airport import Airport
from ..core.loader import get_airport_by_iata, get_airport_by_icao, get_all_airports
from ..core.distance import distance
from ..core.search import filter_airports
from ..exceptions import RoutingError
from ..utils.constants import DEFAULT_CRUISE_SPEED_KTS, DEFAULT_MAX_LEG_KM
from ..utils.units import DistanceUnit, convert_distance
from ..utils.logging import get_logger


logger = get_logger()


def estimate_flight_time_hours(
    from_airport: Airport,
    to_airport: Airport,
    speed_kts: float = DEFAULT_CRUISE_SPEED_KTS,
    model: str = "haversine",
) -> float:
    dist_nmi = distance(
        from_airport.latitude_deg,
        from_airport.longitude_deg,
        to_airport.latitude_deg,
        to_airport.longitude_deg,
        model=model,
        unit="nmi"
    )

    return dist_nmi / speed_kts


def estimate_flight_time_h_m(
    from_airport: Airport,
    to_airport: Airport,
    speed_kts: float = DEFAULT_CRUISE_SPEED_KTS,
    model: str = "haversine",
) -> tuple[int, int]:
    hours_total = estimate_flight_time_hours(from_airport, to_airport, speed_kts, model)
    hours = int(hours_total)
    minutes = int((hours_total - hours) * 60)

    return (hours, minutes)


def route_distance(
    airports: Sequence[Airport],
    model: str = "haversine",
    unit: DistanceUnit = "km",
) -> float:
    if len(airports) < 2:
        return 0.0

    total_dist_km = 0.0

    for i in range(len(airports) - 1):
        a1 = airports[i]
        a2 = airports[i + 1]

        dist_km = distance(
            a1.latitude_deg,
            a1.longitude_deg,
            a2.latitude_deg,
            a2.longitude_deg,
            model=model,
            unit="km"
        )

        total_dist_km += dist_km

    return convert_distance(total_dist_km, "km", unit)


def route_distance_by_codes(
    codes: Sequence[str],
    code_type: str = "iata",
    model: str = "haversine",
    unit: DistanceUnit = "km",
) -> float:
    airports = []

    for code in codes:
        if code_type == "iata":
            airport = get_airport_by_iata(code)
        elif code_type == "icao":
            airport = get_airport_by_icao(code)
        else:
            airport = get_airport_by_iata(code)
            if airport is None:
                airport = get_airport_by_icao(code)

        if airport is None:
            raise RoutingError(f"Airport not found: {code}")

        airports.append(airport)

    return route_distance(airports, model, unit)


def shortest_path(
    origin_code: str,
    destination_code: str,
    code_type: str = "iata",
    max_leg_km: float = DEFAULT_MAX_LEG_KM,
    allowed_types: Sequence[str] | None = None,
    avoid_countries: Sequence[str] | None = None,
) -> list[Airport]:
    if code_type == "iata":
        origin = get_airport_by_iata(origin_code)
        destination = get_airport_by_iata(destination_code)
    elif code_type == "icao":
        origin = get_airport_by_icao(origin_code)
        destination = get_airport_by_icao(destination_code)
    else:
        origin = get_airport_by_iata(origin_code) or get_airport_by_icao(origin_code)
        destination = get_airport_by_iata(destination_code) or get_airport_by_icao(destination_code)

    if origin is None:
        raise RoutingError(f"Origin airport not found: {origin_code}")
    if destination is None:
        raise RoutingError(f"Destination airport not found: {destination_code}")

    all_airports = get_all_airports()

    if allowed_types:
        all_airports = [a for a in all_airports if a.type in allowed_types]

    if avoid_countries:
        avoid_set = {c.upper() for c in avoid_countries}
        all_airports = [a for a in all_airports if a.iso_country not in avoid_set]

    airport_map = {a.name: a for a in all_airports}

    if origin.name not in airport_map or destination.name not in airport_map:
        raise RoutingError("Origin or destination excluded by filters")

    def heuristic(a: Airport, b: Airport) -> float:
        return distance(
            a.latitude_deg, a.longitude_deg,
            b.latitude_deg, b.longitude_deg,
            model="haversine", unit="km"
        )

    pq = [(0.0, 0.0, origin.name, [origin])]
    visited = set()

    while pq:
        f_score, g_score, current_name, path = heapq.heappop(pq)

        if current_name in visited:
            continue

        visited.add(current_name)
        current = airport_map[current_name]

        if current.name == destination.name:
            return path

        if len(visited) > 1000:
            logger.warning("Shortest path search exceeded 1000 visited nodes, stopping")
            break

        for neighbor in all_airports:
            if neighbor.name in visited:
                continue

            leg_dist = heuristic(current, neighbor)

            if leg_dist > max_leg_km:
                continue

            new_g_score = g_score + leg_dist
            new_f_score = new_g_score + heuristic(neighbor, destination)

            heapq.heappush(pq, (new_f_score, new_g_score, neighbor.name, path + [neighbor]))

    raise RoutingError(f"No path found from {origin_code} to {destination_code} with given constraints")
