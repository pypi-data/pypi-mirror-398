import re
from typing import Optional

from ..exceptions import WeatherDataError
from ..utils.logging import get_logger
from ..utils.validators import is_valid_icao


try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


logger = get_logger()


METAR_URL_TEMPLATE = "https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao}.TXT"
TAF_URL_TEMPLATE = "https://tgftp.nws.noaa.gov/data/forecasts/taf/stations/{icao}.TXT"


def _sanitize_icao(icao: str) -> str:
    icao_clean = re.sub(r'[^A-Z0-9]', '', icao.upper())

    if not is_valid_icao(icao_clean):
        raise WeatherDataError(f"Invalid ICAO code: {icao}")

    return icao_clean


def get_metar(icao: str, timeout: float = 5.0) -> str | None:
    if not HAS_REQUESTS:
        logger.warning("requests library not installed, cannot fetch METAR data")
        return None

    try:
        icao_clean = _sanitize_icao(icao)
        url = METAR_URL_TEMPLATE.format(icao=icao_clean)

        response = requests.get(url, timeout=timeout)

        if response.status_code == 404:
            logger.debug(f"METAR not found for {icao_clean}")
            return None

        response.raise_for_status()

        lines = response.text.strip().split('\n')

        if len(lines) >= 2:
            return lines[1].strip()

        return response.text.strip()

    except WeatherDataError:
        raise
    except Exception as e:
        if HAS_REQUESTS and hasattr(e, '__module__') and 'requests' in e.__module__:
            logger.debug(f"Failed to fetch METAR for {icao}: {e}")
        else:
            logger.debug(f"Unexpected error fetching METAR: {e}")
        return None


def get_taf(icao: str, timeout: float = 5.0) -> str | None:
    if not HAS_REQUESTS:
        logger.warning("requests library not installed, cannot fetch TAF data")
        return None

    try:
        icao_clean = _sanitize_icao(icao)
        url = TAF_URL_TEMPLATE.format(icao=icao_clean)

        response = requests.get(url, timeout=timeout)

        if response.status_code == 404:
            logger.debug(f"TAF not found for {icao_clean}")
            return None

        response.raise_for_status()

        lines = response.text.strip().split('\n')

        if len(lines) >= 2:
            return '\n'.join(lines[1:]).strip()

        return response.text.strip()

    except WeatherDataError:
        raise
    except Exception as e:
        if HAS_REQUESTS and hasattr(e, '__module__') and 'requests' in e.__module__:
            logger.debug(f"Failed to fetch TAF for {icao}: {e}")
        else:
            logger.debug(f"Unexpected error fetching TAF: {e}")
        return None
