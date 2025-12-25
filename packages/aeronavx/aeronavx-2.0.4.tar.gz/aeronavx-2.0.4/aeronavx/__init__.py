from .models import Airport, Runway
from .core.airports import get as get_airport, get_by_iata, get_by_icao, search_by_name as search_airports_by_name
from .core.distance import distance, distance_km, distance_mi, distance_nmi
from .core.geodesy import initial_bearing, midpoint, great_circle_path
from .core.search import nearest_airport, nearest_airports, airports_within_radius
from .core.routing import estimate_flight_time_hours as estimate_flight_time, route_distance
from .core.emissions import estimate_co2_kg_by_codes as estimate_co2_kg_for_segment
from .core.weather import get_metar, get_taf
# from .core.runways import (
#     get_runways_by_airport,
#     get_longest_runway,
#     get_paved_runways,
# )
# from .core.statistics import (
#     get_country_stats,
#     get_continent_stats,
#     get_global_stats,
#     get_top_countries_by_airports,
#     get_top_countries_by_large_airports,
# )

# NEW v2.0.0: Network Intelligence Layer
from .core.network_intelligence import (
    NetworkIntelligence,
    HubScore,
    NetworkMetrics,
    identify_global_hubs,
    identify_regional_hubs,
    calculate_global_network_metrics,
    calculate_regional_network_metrics,
)

# NEW v2.0.0: Synthetic Route Engine
from .core.synthetic_routes import (
    SyntheticRouteEngine,
    SyntheticRoute,
    Waypoint,
    FlightProfile,
    FlightPhase,
    AircraftCategory,
    generate_route,
    generate_random_route_from,
)

# NEW v2.0.0: Advanced Emissions Calculator
from .core.emissions_v2 import (
    EmissionsCalculatorV2,
    EmissionReport,
    AircraftType,
    FuelType,
    calculate_flight_emissions,
    compare_saf_savings,
)

# NEW v2.0.0: Geo-Spatial Advanced
from .core.geospatial_advanced import (
    GeoSpatialAdvanced,
    RouteComparison,
    OptimalAltitude,
    FlightCorridor,
    AirspaceClass,
    RouteType,
    compare_routes,
    get_optimal_altitude,
    check_polar_route,
)

# NEW v2.0.0: Passenger Experience (Jet Lag)
from .core.passenger_experience import (
    PassengerExperience,
    JetLagReport,
    FatigueReport,
    JetLagSeverity,
    FlightDirection,
    calculate_jet_lag,
    get_best_departure_time,
    assess_flight_fatigue,
)

from .exceptions import (
    AeroNavXError,
    AirportNotFoundError,
    InvalidAirportCodeError,
    DataLoadError,
    RoutingError,
    WeatherDataError,
)


__version__ = "2.0.4"

__all__ = [
    # Models
    "Airport",
    "Runway",
    # Core Functions
    "get_airport",
    "get_by_iata",
    "get_by_icao",
    "distance",
    "distance_km",
    "distance_mi",
    "distance_nmi",
    "initial_bearing",
    "midpoint",
    "great_circle_path",
    "nearest_airport",
    "nearest_airports",
    "airports_within_radius",
    "estimate_flight_time",
    "route_distance",
    "estimate_co2_kg_for_segment",
    "search_airports_by_name",
    "get_metar",
    "get_taf",
    # "get_runways_by_airport",
    # "get_longest_runway",
    # "get_paved_runways",
    # "get_country_stats",
    # "get_continent_stats",
    # "get_global_stats",
    # "get_top_countries_by_airports",
    # "get_top_countries_by_large_airports",
    # v2.0.0: Network Intelligence
    "NetworkIntelligence",
    "HubScore",
    "NetworkMetrics",
    "identify_global_hubs",
    "identify_regional_hubs",
    "calculate_global_network_metrics",
    "calculate_regional_network_metrics",
    # v2.0.0: Synthetic Routes
    "SyntheticRouteEngine",
    "SyntheticRoute",
    "Waypoint",
    "FlightProfile",
    "FlightPhase",
    "AircraftCategory",
    "generate_route",
    "generate_random_route_from",
    # v2.0.0: Advanced Emissions
    "EmissionsCalculatorV2",
    "EmissionReport",
    "AircraftType",
    "FuelType",
    "calculate_flight_emissions",
    "compare_saf_savings",
    # v2.0.0: Geo-Spatial Advanced
    "GeoSpatialAdvanced",
    "RouteComparison",
    "OptimalAltitude",
    "FlightCorridor",
    "AirspaceClass",
    "RouteType",
    "compare_routes",
    "get_optimal_altitude",
    "check_polar_route",
    # v2.0.0: Passenger Experience
    "PassengerExperience",
    "JetLagReport",
    "FatigueReport",
    "JetLagSeverity",
    "FlightDirection",
    "calculate_jet_lag",
    "get_best_departure_time",
    "assess_flight_fatigue",
    # Exceptions
    "AeroNavXError",
    "AirportNotFoundError",
    "InvalidAirportCodeError",
    "DataLoadError",
    "RoutingError",
    "WeatherDataError",
]
