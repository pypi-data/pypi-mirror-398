import csv
from pathlib import Path
from typing import Optional

from ..models.airport import Airport
from ..exceptions import DataLoadError
from ..utils.logging import get_logger
from ..utils.validators import normalize_airport_code


logger = get_logger()

_airports: list[Airport] = []
_iata_index: dict[str, Airport] = {}
_icao_index: dict[str, Airport] = {}
_id_index: dict[int, Airport] = {}
_loaded = False


def _find_data_file() -> Path:
    possible_paths = [
        Path(__file__).parent.parent / "data" / "airports.csv",  # aeronavx/data/airports.csv
        Path(__file__).parent.parent.parent / "data" / "airports.csv",  # legacy support
        Path.cwd() / "data" / "airports.csv",
        Path.cwd() / "airports.csv",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise DataLoadError(
        f"Could not find airports.csv. Searched in: {', '.join(str(p) for p in possible_paths)}"
    )


def _parse_bool(value: str) -> bool | None:
    if not value or value.lower() in ("", "no", "0", "false"):
        return False
    if value.lower() in ("yes", "1", "true"):
        return True
    return None


def _parse_int(value: str) -> int | None:
    try:
        return int(value) if value else None
    except ValueError:
        return None


def _parse_float(value: str) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def load_airports(
    data_path: Optional[Path | str] = None,
    force_reload: bool = False,
    include_types: Optional[list[str]] = None,
    exclude_types: Optional[list[str]] = None,
    countries: Optional[list[str]] = None,
    scheduled_service_only: bool = False,
    has_iata_only: bool = False,
) -> list[Airport]:
    """
    Load airports from CSV file with optional filtering.

    Args:
        data_path: Path to airports CSV file (default: auto-detect)
        force_reload: Force reload even if already loaded
        include_types: Only include these airport types (e.g., ['large_airport', 'medium_airport'])
        exclude_types: Exclude these airport types (e.g., ['heliport', 'closed'])
        countries: Only include these countries (ISO codes, e.g., ['US', 'GB', 'TR'])
        scheduled_service_only: Only include airports with scheduled service
        has_iata_only: Only include airports with IATA codes

    Returns:
        List of Airport objects

    Example:
        # Load only major airports
        airports = load_airports(
            include_types=['large_airport', 'medium_airport'],
            scheduled_service_only=True
        )

        # Load specific countries
        airports = load_airports(countries=['US', 'GB', 'TR'])
    """
    global _airports, _iata_index, _icao_index, _id_index, _loaded

    if _loaded and not force_reload:
        return _airports

    if data_path is None:
        data_path = _find_data_file()
    else:
        data_path = Path(data_path)
        if not data_path.exists():
            raise DataLoadError(f"Data file not found: {data_path}")

    logger.info(f"Loading airports from {data_path}")

    airports = []
    skipped = 0

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    lat = _parse_float(row.get("latitude_deg", ""))
                    lon = _parse_float(row.get("longitude_deg", ""))

                    if lat is None or lon is None:
                        skipped += 1
                        continue

                    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        skipped += 1
                        continue

                    name = row.get("name", "").strip()
                    if not name:
                        skipped += 1
                        continue

                    iata_code = row.get("iata_code", "").strip().upper() or None
                    gps_code = row.get("gps_code", "").strip().upper() or None
                    icao_code = row.get("icao_code", "").strip().upper() or None  # OurAirports format
                    local_code = row.get("local_code", "").strip().upper() or None

                    # Use icao_code if gps_code is empty (OurAirports compatibility)
                    if not gps_code and icao_code:
                        gps_code = icao_code

                    airport_type = row.get("type", "").strip() or None
                    iso_country = row.get("iso_country", "").strip().upper() or None
                    scheduled_service = _parse_bool(row.get("scheduled_service", ""))

                    # Apply filters
                    if include_types and airport_type not in include_types:
                        skipped += 1
                        continue

                    if exclude_types and airport_type in exclude_types:
                        skipped += 1
                        continue

                    if countries and iso_country not in countries:
                        skipped += 1
                        continue

                    if scheduled_service_only and not scheduled_service:
                        skipped += 1
                        continue

                    if has_iata_only and not iata_code:
                        skipped += 1
                        continue

                    airport = Airport(
                        id=_parse_int(row.get("id", "")),
                        ident=row.get("ident", "").strip() or None,
                        type=airport_type,
                        name=name,
                        latitude_deg=lat,
                        longitude_deg=lon,
                        elevation_ft=_parse_float(row.get("elevation_ft", "")),
                        continent=row.get("continent", "").strip() or None,
                        iso_country=iso_country,
                        iso_region=row.get("iso_region", "").strip().upper() or None,
                        municipality=row.get("municipality", "").strip() or None,
                        scheduled_service=scheduled_service,
                        gps_code=gps_code,
                        iata_code=iata_code,
                        local_code=local_code,
                        home_link=row.get("home_link", "").strip() or None,
                        wikipedia_link=row.get("wikipedia_link", "").strip() or None,
                        keywords=row.get("keywords", "").strip() or None,
                    )

                    airports.append(airport)

                except Exception as e:
                    logger.debug(f"Skipping row due to error: {e}")
                    skipped += 1
                    continue

    except Exception as e:
        raise DataLoadError(f"Failed to load airports: {e}")

    _airports = airports
    _build_indices()
    _loaded = True

    logger.info(f"Loaded {len(_airports)} airports (skipped {skipped})")

    return _airports


def _build_indices() -> None:
    global _iata_index, _icao_index, _id_index

    _iata_index.clear()
    _icao_index.clear()
    _id_index.clear()

    for airport in _airports:
        if airport.iata_code:
            code = normalize_airport_code(airport.iata_code)
            if code not in _iata_index:
                _iata_index[code] = airport

        if airport.gps_code:
            code = normalize_airport_code(airport.gps_code)
            if code not in _icao_index:
                _icao_index[code] = airport

        if airport.id is not None:
            _id_index[airport.id] = airport


def get_airport_by_iata(code: str) -> Airport | None:
    if not _loaded:
        load_airports()

    normalized = normalize_airport_code(code)
    return _iata_index.get(normalized)


def get_airport_by_icao(code: str) -> Airport | None:
    if not _loaded:
        load_airports()

    normalized = normalize_airport_code(code)
    return _icao_index.get(normalized)


def get_airport_by_id(airport_id: int) -> Airport | None:
    if not _loaded:
        load_airports()

    return _id_index.get(airport_id)


def get_all_airports() -> list[Airport]:
    if not _loaded:
        load_airports()

    return _airports.copy()


def get_airports_df():
    try:
        import pandas as pd

        if not _loaded:
            load_airports()

        return pd.DataFrame([a.as_dict() for a in _airports])

    except ImportError:
        logger.warning("pandas not installed, cannot return DataFrame")
        return None


def clear_cache() -> None:
    global _airports, _iata_index, _icao_index, _id_index, _loaded

    _airports.clear()
    _iata_index.clear()
    _icao_index.clear()
    _id_index.clear()
    _loaded = False

    logger.info("Cleared airport data cache")
