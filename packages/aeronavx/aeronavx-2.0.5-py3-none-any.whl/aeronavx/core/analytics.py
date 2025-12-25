from collections import defaultdict
from typing import Optional

from ..models.airport import Airport
from ..core.loader import get_all_airports
from ..core.search import nearest_airports


_precomputed_neighbors: Optional[dict[str, list[Airport]]] = None


def airports_per_country() -> dict[str, int]:
    airports = get_all_airports()
    counts = defaultdict(int)

    for airport in airports:
        if airport.iso_country:
            counts[airport.iso_country] += 1

    return dict(counts)


def airports_per_continent() -> dict[str, int]:
    airports = get_all_airports()
    counts = defaultdict(int)

    for airport in airports:
        if airport.continent:
            counts[airport.continent] += 1

    return dict(counts)


def airports_per_type() -> dict[str, int]:
    airports = get_all_airports()
    counts = defaultdict(int)

    for airport in airports:
        if airport.type:
            counts[airport.type] += 1

    return dict(counts)


def highest_elevation_airports(n: int = 10) -> list[Airport]:
    airports = get_all_airports()

    airports_with_elevation = [
        a for a in airports if a.elevation_ft is not None
    ]

    airports_with_elevation.sort(key=lambda a: a.elevation_ft, reverse=True)

    return airports_with_elevation[:n]


def lowest_elevation_airports(n: int = 10) -> list[Airport]:
    airports = get_all_airports()

    airports_with_elevation = [
        a for a in airports if a.elevation_ft is not None
    ]

    airports_with_elevation.sort(key=lambda a: a.elevation_ft)

    return airports_with_elevation[:n]


def country_centroids() -> dict[str, tuple[float, float]]:
    airports = get_all_airports()

    country_coords = defaultdict(list)

    for airport in airports:
        if airport.iso_country:
            country_coords[airport.iso_country].append(
                (airport.latitude_deg, airport.longitude_deg)
            )

    centroids = {}

    for country, coords in country_coords.items():
        avg_lat = sum(lat for lat, _ in coords) / len(coords)
        avg_lon = sum(lon for _, lon in coords) / len(coords)
        centroids[country] = (avg_lat, avg_lon)

    return centroids


def precompute_nearest_neighbors(k: int = 5) -> dict[str, list[Airport]]:
    global _precomputed_neighbors

    airports = get_all_airports()
    _precomputed_neighbors = {}

    for airport in airports:
        neighbors = nearest_airports(
            airport.latitude_deg,
            airport.longitude_deg,
            n=k + 1
        )

        neighbors_filtered = [
            a for a in neighbors if a.name != airport.name
        ][:k]

        key = airport.iata_code or airport.gps_code or str(airport.id)
        _precomputed_neighbors[key] = neighbors_filtered

    return _precomputed_neighbors


def get_precomputed_neighbors(code: str, code_type: str = "iata") -> list[Airport] | None:
    if _precomputed_neighbors is None:
        return None

    return _precomputed_neighbors.get(code.upper())


def total_airports() -> int:
    return len(get_all_airports())


def airports_with_scheduled_service() -> int:
    airports = get_all_airports()
    return sum(1 for a in airports if a.scheduled_service is True)


def airports_by_type_and_country() -> dict[str, dict[str, int]]:
    airports = get_all_airports()
    result = defaultdict(lambda: defaultdict(int))

    for airport in airports:
        if airport.type and airport.iso_country:
            result[airport.type][airport.iso_country] += 1

    return {k: dict(v) for k, v in result.items()}
