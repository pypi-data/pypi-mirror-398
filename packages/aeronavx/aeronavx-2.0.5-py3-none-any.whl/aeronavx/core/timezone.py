from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..models.airport import Airport
from ..core.loader import get_airport_by_iata, get_airport_by_icao
from ..utils.logging import get_logger


logger = get_logger()


try:
    from timezonefinder import TimezoneFinder
    _tz_finder = TimezoneFinder()
    HAS_TIMEZONEFINDER = True
except ImportError:
    _tz_finder = None
    HAS_TIMEZONEFINDER = False
    logger.warning("timezonefinder not installed, timezone functionality will be limited")


def get_timezone_for_airport(airport: Airport) -> str | None:
    if not HAS_TIMEZONEFINDER:
        return None

    try:
        tz_name = _tz_finder.timezone_at(
            lat=airport.latitude_deg,
            lng=airport.longitude_deg
        )
        return tz_name
    except Exception as e:
        logger.debug(f"Could not determine timezone for {airport.name}: {e}")
        return None


def get_timezone_for_code(code: str, code_type: str = "iata") -> str | None:
    if code_type == "iata":
        airport = get_airport_by_iata(code)
    elif code_type == "icao":
        airport = get_airport_by_icao(code)
    else:
        airport = get_airport_by_iata(code) or get_airport_by_icao(code)

    if airport is None:
        return None

    return get_timezone_for_airport(airport)


def local_time_for_airport(
    airport: Airport,
    dt_utc: Optional[datetime] = None
) -> datetime | None:
    tz_name = get_timezone_for_airport(airport)

    if tz_name is None:
        return None

    if dt_utc is None:
        dt_utc = datetime.utcnow()

    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))

    try:
        tz = ZoneInfo(tz_name)
        local_dt = dt_utc.astimezone(tz)
        return local_dt
    except ZoneInfoNotFoundError:
        logger.debug(f"Timezone {tz_name} not found")
        return None
    except Exception as e:
        logger.debug(f"Error converting to local time: {e}")
        return None


def local_time_for_code(
    code: str,
    code_type: str = "iata",
    dt_utc: Optional[datetime] = None
) -> datetime | None:
    if code_type == "iata":
        airport = get_airport_by_iata(code)
    elif code_type == "icao":
        airport = get_airport_by_icao(code)
    else:
        airport = get_airport_by_iata(code) or get_airport_by_icao(code)

    if airport is None:
        return None

    return local_time_for_airport(airport, dt_utc)


def get_timezone_offset(latitude: float, longitude: float) -> float:
    """
    Get UTC timezone offset in hours for given coordinates.

    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees

    Returns:
        UTC offset in hours (e.g., -5.0 for EST, 9.0 for JST)
        Returns approximate offset based on longitude if timezonefinder unavailable
    """
    if not HAS_TIMEZONEFINDER:
        # Fallback: Approximate based on longitude
        # Each 15 degrees longitude ≈ 1 hour offset
        offset = round(longitude / 15.0)
        # Clamp to valid range
        if offset > 12:
            offset -= 24
        elif offset < -12:
            offset += 24
        return float(offset)

    try:
        # Get timezone name
        tz_name = _tz_finder.timezone_at(lat=latitude, lng=longitude)

        if tz_name is None:
            # Fallback to longitude approximation
            offset = round(longitude / 15.0)
            if offset > 12:
                offset -= 24
            elif offset < -12:
                offset += 24
            return float(offset)

        # Get actual UTC offset for this timezone
        tz = ZoneInfo(tz_name)
        # Use current time to get offset (accounts for DST)
        now_utc = datetime.now(ZoneInfo("UTC"))
        now_local = now_utc.astimezone(tz)

        # Calculate offset in hours
        offset_seconds = now_local.utcoffset().total_seconds()
        offset_hours = offset_seconds / 3600.0

        return offset_hours

    except Exception as e:
        logger.debug(f"Could not determine timezone offset for ({latitude}, {longitude}): {e}")
        # Fallback to longitude approximation
        offset = round(longitude / 15.0)
        if offset > 12:
            offset -= 24
        elif offset < -12:
            offset += 24
        return float(offset)
