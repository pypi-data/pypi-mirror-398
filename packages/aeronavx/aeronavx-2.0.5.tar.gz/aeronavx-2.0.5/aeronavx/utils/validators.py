import re


def is_valid_iata(code: str) -> bool:
    if not isinstance(code, str):
        return False
    return bool(re.match(r'^[A-Z]{3}$', code.strip().upper()))


def is_valid_icao(code: str) -> bool:
    if not isinstance(code, str):
        return False
    return bool(re.match(r'^[A-Z]{4}$', code.strip().upper()))


def validate_coordinates(lat: float, lon: float) -> None:
    if not isinstance(lat, (int, float)):
        raise ValueError(f"Latitude must be numeric, got {type(lat).__name__}")
    if not isinstance(lon, (int, float)):
        raise ValueError(f"Longitude must be numeric, got {type(lon).__name__}")

    if not -90.0 <= lat <= 90.0:
        raise ValueError(f"Latitude must be in range [-90, 90], got {lat}")
    if not -180.0 <= lon <= 180.0:
        raise ValueError(f"Longitude must be in range [-180, 180], got {lon}")


def normalize_airport_code(code: str) -> str:
    if not isinstance(code, str):
        raise ValueError(f"Airport code must be a string, got {type(code).__name__}")
    return code.strip().upper()
