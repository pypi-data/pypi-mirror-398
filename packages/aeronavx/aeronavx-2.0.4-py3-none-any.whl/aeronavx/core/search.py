from typing import Sequence

from ..models.airport import Airport
from ..core.loader import get_all_airports, get_airport_by_iata, get_airport_by_icao
from ..utils.spatial_index import build_spatial_index
from ..utils.logging import get_logger


logger = get_logger()

_spatial_index = None


try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


def _get_spatial_index():
    global _spatial_index

    if _spatial_index is None:
        airports = get_all_airports()
        _spatial_index = build_spatial_index(airports)

    return _spatial_index


def search_airports_by_name(query: str, limit: int = 20) -> list[Airport]:
    airports = get_all_airports()

    if not query:
        return airports[:limit]

    query_lower = query.lower()

    if HAS_RAPIDFUZZ:
        choices = {a.name: a for a in airports}
        results = process.extract(
            query,
            choices.keys(),
            scorer=fuzz.WRatio,
            limit=limit
        )
        return [choices[name] for name, score, _ in results]
    else:
        exact_matches = [a for a in airports if query_lower in a.name.lower()]
        startswith_matches = [a for a in airports if a.name.lower().startswith(query_lower)]

        results = []
        seen = set()

        for a in startswith_matches:
            if a.name not in seen:
                results.append(a)
                seen.add(a.name)

        for a in exact_matches:
            if a.name not in seen:
                results.append(a)
                seen.add(a.name)

        return results[:limit]


def filter_airports(
    country: str | None = None,
    region: str | None = None,
    municipality: str | None = None,
    types: Sequence[str] | None = None,
    scheduled_only: bool | None = None,
) -> list[Airport]:
    airports = get_all_airports()
    results = airports

    if country:
        country_upper = country.upper()
        results = [a for a in results if a.iso_country == country_upper]

    if region:
        region_upper = region.upper()
        results = [a for a in results if a.iso_region == region_upper]

    if municipality:
        municipality_lower = municipality.lower()
        results = [
            a for a in results
            if a.municipality and municipality_lower in a.municipality.lower()
        ]

    if types:
        types_set = set(types)
        results = [a for a in results if a.type in types_set]

    if scheduled_only is True:
        results = [a for a in results if a.scheduled_service is True]

    return results


def airports_in_country(country_code: str) -> list[Airport]:
    return filter_airports(country=country_code)


def airports_in_region(region_code: str) -> list[Airport]:
    return filter_airports(region=region_code)


def nearest_airports(
    lat: float,
    lon: float,
    n: int = 1,
    max_distance_km: float | None = None
) -> list[Airport]:
    index = _get_spatial_index()
    return index.nearest(lat, lon, n, max_distance_km)


def airports_within_radius(lat: float, lon: float, radius_km: float) -> list[Airport]:
    index = _get_spatial_index()
    return index.within_radius(lat, lon, radius_km)


def nearest_airport(lat: float, lon: float, max_distance_km: float | None = None) -> Airport | None:
    """
    Find the single nearest airport to a location.

    Args:
        lat: Latitude
        lon: Longitude
        max_distance_km: Maximum search distance in km

    Returns:
        Nearest Airport object or None if no airports found

    Examples:
        >>> from aeronavx import nearest_airport
        >>> airport = nearest_airport(40.7128, -74.0060)  # NYC
        >>> print(f"{airport.iata_code}: {airport.name}")
        JFK: John F Kennedy International Airport
    """
    results = nearest_airports(lat, lon, n=1, max_distance_km=max_distance_km)
    return results[0] if results else None


def nearest_airport_to_point(lat: float, lon: float, n: int = 1) -> list[Airport]:
    return nearest_airports(lat, lon, n)


def nearest_airport_to_airport(code: str, n: int = 1, code_type: str = "iata") -> list[Airport]:
    if code_type == "iata":
        airport = get_airport_by_iata(code)
    elif code_type == "icao":
        airport = get_airport_by_icao(code)
    else:
        airport = get_airport_by_iata(code)
        if airport is None:
            airport = get_airport_by_icao(code)

    if airport is None:
        return []

    all_nearest = nearest_airports(airport.latitude_deg, airport.longitude_deg, n + 1)

    return [a for a in all_nearest if a.name != airport.name][:n]


def clear_spatial_index() -> None:
    global _spatial_index
    _spatial_index = None
    logger.info("Cleared spatial index cache")
