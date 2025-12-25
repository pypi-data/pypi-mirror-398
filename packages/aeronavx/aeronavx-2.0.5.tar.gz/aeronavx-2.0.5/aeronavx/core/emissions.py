from typing import Sequence

from ..models.airport import Airport
from ..core.loader import get_airport_by_iata, get_airport_by_icao
from ..core.distance import distance
from ..exceptions import RoutingError
from ..utils.constants import DEFAULT_CO2_KG_PER_PAX_KM


def estimate_co2_kg_for_segment(
    from_airport: Airport,
    to_airport: Airport,
    model: str = "haversine",
    factor_kg_per_pax_km: float = DEFAULT_CO2_KG_PER_PAX_KM
) -> float:
    dist_km = distance(
        from_airport.latitude_deg,
        from_airport.longitude_deg,
        to_airport.latitude_deg,
        to_airport.longitude_deg,
        model=model,
        unit="km"
    )

    return dist_km * factor_kg_per_pax_km


def estimate_co2_kg_for_route(
    airports: Sequence[Airport],
    model: str = "haversine",
    factor_kg_per_pax_km: float = DEFAULT_CO2_KG_PER_PAX_KM
) -> float:
    if len(airports) < 2:
        return 0.0

    total_co2 = 0.0

    for i in range(len(airports) - 1):
        co2 = estimate_co2_kg_for_segment(
            airports[i],
            airports[i + 1],
            model=model,
            factor_kg_per_pax_km=factor_kg_per_pax_km
        )
        total_co2 += co2

    return total_co2


def estimate_co2_kg_by_codes(
    from_code: str,
    to_code: str,
    code_type: str = "iata",
    model: str = "haversine",
    factor_kg_per_pax_km: float = DEFAULT_CO2_KG_PER_PAX_KM
) -> float:
    if code_type == "iata":
        from_airport = get_airport_by_iata(from_code)
        to_airport = get_airport_by_iata(to_code)
    elif code_type == "icao":
        from_airport = get_airport_by_icao(from_code)
        to_airport = get_airport_by_icao(to_code)
    else:
        from_airport = get_airport_by_iata(from_code) or get_airport_by_icao(from_code)
        to_airport = get_airport_by_iata(to_code) or get_airport_by_icao(to_code)

    if from_airport is None:
        raise RoutingError(f"Origin airport not found: {from_code}")
    if to_airport is None:
        raise RoutingError(f"Destination airport not found: {to_code}")

    return estimate_co2_kg_for_segment(from_airport, to_airport, model, factor_kg_per_pax_km)


def estimate_co2_kg_route_by_codes(
    codes: Sequence[str],
    code_type: str = "iata",
    model: str = "haversine",
    factor_kg_per_pax_km: float = DEFAULT_CO2_KG_PER_PAX_KM
) -> float:
    airports = []

    for code in codes:
        if code_type == "iata":
            airport = get_airport_by_iata(code)
        elif code_type == "icao":
            airport = get_airport_by_icao(code)
        else:
            airport = get_airport_by_iata(code) or get_airport_by_icao(code)

        if airport is None:
            raise RoutingError(f"Airport not found: {code}")

        airports.append(airport)

    return estimate_co2_kg_for_route(airports, model, factor_kg_per_pax_km)
