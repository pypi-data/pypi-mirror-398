import math
from typing import Literal

from ..utils.constants import (
    EARTH_RADIUS_KM,
    EARTH_SEMI_MAJOR_AXIS_M,
    EARTH_SEMI_MINOR_AXIS_M,
    EARTH_FLATTENING,
)
from ..utils.units import convert_distance, DistanceUnit
from ..utils.validators import validate_coordinates


DistanceModel = Literal["haversine", "slc", "vincenty"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def slc_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lon = math.radians(lon2 - lon1)

    cos_angle = (
        math.sin(lat1_rad) * math.sin(lat2_rad) +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)
    )

    cos_angle = max(-1.0, min(1.0, cos_angle))

    angle = math.acos(cos_angle)

    return EARTH_RADIUS_KM * angle


def vincenty_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    a = EARTH_SEMI_MAJOR_AXIS_M
    b = EARTH_SEMI_MINOR_AXIS_M
    f = EARTH_FLATTENING

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon1_rad = math.radians(lon1)
    lon2_rad = math.radians(lon2)

    L = lon2_rad - lon1_rad

    U1 = math.atan((1 - f) * math.tan(lat1_rad))
    U2 = math.atan((1 - f) * math.tan(lat2_rad))

    sin_U1 = math.sin(U1)
    cos_U1 = math.cos(U1)
    sin_U2 = math.sin(U2)
    cos_U2 = math.cos(U2)

    lambda_val = L
    lambda_prev = 0.0
    iteration_limit = 100
    iteration = 0

    while iteration < iteration_limit:
        sin_lambda = math.sin(lambda_val)
        cos_lambda = math.cos(lambda_val)

        sin_sigma = math.sqrt(
            (cos_U2 * sin_lambda) ** 2 +
            (cos_U1 * sin_U2 - sin_U1 * cos_U2 * cos_lambda) ** 2
        )

        if sin_sigma == 0:
            return 0.0

        cos_sigma = sin_U1 * sin_U2 + cos_U1 * cos_U2 * cos_lambda

        sigma = math.atan2(sin_sigma, cos_sigma)

        sin_alpha = cos_U1 * cos_U2 * sin_lambda / sin_sigma
        cos_sq_alpha = 1 - sin_alpha ** 2

        if cos_sq_alpha == 0:
            cos_2sigma_m = 0
        else:
            cos_2sigma_m = cos_sigma - 2 * sin_U1 * sin_U2 / cos_sq_alpha

        C = f / 16 * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))

        lambda_prev = lambda_val
        lambda_val = L + (1 - C) * f * sin_alpha * (
            sigma + C * sin_sigma * (
                cos_2sigma_m + C * cos_sigma * (-1 + 2 * cos_2sigma_m ** 2)
            )
        )

        if abs(lambda_val - lambda_prev) < 1e-12:
            break

        iteration += 1

    if iteration >= iteration_limit:
        return haversine_km(lat1, lon1, lat2, lon2)

    u_sq = cos_sq_alpha * (a ** 2 - b ** 2) / (b ** 2)

    A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    delta_sigma = B * sin_sigma * (
        cos_2sigma_m + B / 4 * (
            cos_sigma * (-1 + 2 * cos_2sigma_m ** 2) -
            B / 6 * cos_2sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos_2sigma_m ** 2)
        )
    )

    distance_m = b * A * (sigma - delta_sigma)

    return distance_m / 1000.0


def distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    model: DistanceModel = "haversine",
    unit: DistanceUnit = "km"
) -> float:
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)

    if model == "haversine":
        dist_km = haversine_km(lat1, lon1, lat2, lon2)
    elif model == "slc":
        dist_km = slc_km(lat1, lon1, lat2, lon2)
    elif model == "vincenty":
        dist_km = vincenty_km(lat1, lon1, lat2, lon2)
    else:
        raise ValueError(f"Unknown distance model: {model}")

    return convert_distance(dist_km, "km", unit)


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return distance(lat1, lon1, lat2, lon2, model="haversine", unit="km")


def distance_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return distance(lat1, lon1, lat2, lon2, model="haversine", unit="mi")


def distance_nmi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return distance(lat1, lon1, lat2, lon2, model="haversine", unit="nmi")
