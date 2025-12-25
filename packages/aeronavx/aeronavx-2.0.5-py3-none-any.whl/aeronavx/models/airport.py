from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True, slots=True)
class Airport:
    id: int | None
    ident: str | None
    type: str | None
    name: str
    latitude_deg: float
    longitude_deg: float
    elevation_ft: float | None
    continent: str | None
    iso_country: str | None
    iso_region: str | None
    municipality: str | None
    scheduled_service: bool | None
    gps_code: str | None
    iata_code: str | None
    local_code: str | None
    home_link: str | None
    wikipedia_link: str | None
    keywords: str | None

    # Alias properties for backward compatibility
    @property
    def latitude(self) -> float:
        """Alias for latitude_deg."""
        return self.latitude_deg

    @property
    def longitude(self) -> float:
        """Alias for longitude_deg."""
        return self.longitude_deg

    @property
    def country_code(self) -> str | None:
        """Alias for iso_country (ISO 3166-1 alpha-2 code)."""
        return self.iso_country

    @property
    def country(self) -> str | None:
        """Alias for iso_country (ISO 3166-1 alpha-2 code)."""
        return self.iso_country

    @property
    def icao_code(self) -> str | None:
        """Alias for gps_code (ICAO code)."""
        return self.gps_code

    def coords(self) -> tuple[float, float]:
        return (self.latitude_deg, self.longitude_deg)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def distance_to(self, other: "Airport", model: str = "haversine") -> float:
        """
        Calculate distance to another airport in kilometers.

        Args:
            other: Destination airport
            model: Distance calculation model ('haversine', 'vincenty', 'spherical')

        Returns:
            Distance in kilometers
        """
        from ..core.distance import distance as calc_distance
        return calc_distance(
            self.latitude_deg,
            self.longitude_deg,
            other.latitude_deg,
            other.longitude_deg,
            model=model,
            unit="km"
        )

    def distance_to_km(self, other: "Airport", model: str = "haversine") -> float:
        """
        Calculate distance to another airport in kilometers.

        Args:
            other: Destination airport
            model: Distance calculation model

        Returns:
            Distance in kilometers
        """
        return self.distance_to(other, model=model)

    def distance_to_nmi(self, other: "Airport", model: str = "haversine") -> float:
        """
        Calculate distance to another airport in nautical miles.

        Args:
            other: Destination airport
            model: Distance calculation model

        Returns:
            Distance in nautical miles
        """
        return self.distance_to(other, model=model) * 0.539957

    def distance_to_miles(self, other: "Airport", model: str = "haversine") -> float:
        """
        Calculate distance to another airport in statute miles.

        Args:
            other: Destination airport
            model: Distance calculation model

        Returns:
            Distance in statute miles
        """
        return self.distance_to(other, model=model) * 0.621371

    def bearing_to(self, other: "Airport") -> float:
        from ..core.geodesy import initial_bearing
        return initial_bearing(
            self.latitude_deg,
            self.longitude_deg,
            other.latitude_deg,
            other.longitude_deg
        )

    def __str__(self) -> str:
        codes = []
        if self.iata_code:
            codes.append(f"IATA:{self.iata_code}")
        if self.gps_code:
            codes.append(f"ICAO:{self.gps_code}")

        code_str = f" ({', '.join(codes)})" if codes else ""
        return f"{self.name}{code_str}"

    def __repr__(self) -> str:
        return f"Airport(name='{self.name}', iata='{self.iata_code}', icao='{self.gps_code}')"
