from .cache import memoize, simple_cache
from .constants import (
    EARTH_RADIUS_KM,
    DEFAULT_CRUISE_SPEED_KTS,
    DEFAULT_CO2_KG_PER_PAX_KM,
    DEFAULT_MAX_LEG_KM,
)
from .logging import get_logger, set_log_level
from .spatial_index import SpatialIndex, build_spatial_index
from .units import (
    convert_distance,
    convert_elevation,
    km_to_mi,
    km_to_nmi,
    mi_to_km,
    nmi_to_km,
    ft_to_m,
    m_to_ft,
    DistanceUnit,
    ElevationUnit,
)
from .validators import (
    is_valid_iata,
    is_valid_icao,
    normalize_airport_code,
    validate_coordinates,
)

__all__ = [
    "memoize",
    "simple_cache",
    "EARTH_RADIUS_KM",
    "DEFAULT_CRUISE_SPEED_KTS",
    "DEFAULT_CO2_KG_PER_PAX_KM",
    "DEFAULT_MAX_LEG_KM",
    "get_logger",
    "set_log_level",
    "SpatialIndex",
    "build_spatial_index",
    "convert_distance",
    "convert_elevation",
    "km_to_mi",
    "km_to_nmi",
    "mi_to_km",
    "nmi_to_km",
    "ft_to_m",
    "m_to_ft",
    "DistanceUnit",
    "ElevationUnit",
    "is_valid_iata",
    "is_valid_icao",
    "normalize_airport_code",
    "validate_coordinates",
]
