import math

from ..utils.validators import validate_coordinates


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    y = math.sin(delta_lon) * math.cos(lat2_rad)
    x = (
        math.cos(lat1_rad) * math.sin(lat2_rad) -
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    )

    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)

    return (bearing_deg + 360) % 360


def final_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return (initial_bearing(lat2, lon2, lat1, lon1) + 180) % 360


def midpoint(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float]:
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon1_rad = math.radians(lon1)
    delta_lon = math.radians(lon2 - lon1)

    bx = math.cos(lat2_rad) * math.cos(delta_lon)
    by = math.cos(lat2_rad) * math.sin(delta_lon)

    lat_mid = math.atan2(
        math.sin(lat1_rad) + math.sin(lat2_rad),
        math.sqrt((math.cos(lat1_rad) + bx) ** 2 + by ** 2)
    )

    lon_mid = lon1_rad + math.atan2(by, math.cos(lat1_rad) + bx)

    return (math.degrees(lat_mid), math.degrees(lon_mid))


def intermediate_point(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    fraction: float
) -> tuple[float, float]:
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"Fraction must be in [0, 1], got {fraction}")

    if fraction == 0.0:
        return (lat1, lon1)
    if fraction == 1.0:
        return (lat2, lon2)

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon1_rad = math.radians(lon1)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    delta = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    a_frac = math.sin((1 - fraction) * delta) / math.sin(delta)
    b_frac = math.sin(fraction * delta) / math.sin(delta)

    x = a_frac * math.cos(lat1_rad) * math.cos(lon1_rad) + b_frac * math.cos(lat2_rad) * math.cos(lon2_rad)
    y = a_frac * math.cos(lat1_rad) * math.sin(lon1_rad) + b_frac * math.cos(lat2_rad) * math.sin(lon2_rad)
    z = a_frac * math.sin(lat1_rad) + b_frac * math.sin(lat2_rad)

    lat_inter = math.atan2(z, math.sqrt(x ** 2 + y ** 2))
    lon_inter = math.atan2(y, x)

    return (math.degrees(lat_inter), math.degrees(lon_inter))


def great_circle_path(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    num_points: int = 100
) -> list[tuple[float, float]]:
    if num_points < 2:
        raise ValueError(f"num_points must be at least 2, got {num_points}")

    path = []
    for i in range(num_points):
        fraction = i / (num_points - 1)
        point = intermediate_point(lat1, lon1, lat2, lon2, fraction)
        path.append(point)

    return path
