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

    def coords(self) -> tuple[float, float]:
        return (self.latitude_deg, self.longitude_deg)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def distance_to(self, other: "Airport", model: str = "haversine") -> float:
        from ..core.distance import distance as calc_distance
        return calc_distance(
            self.latitude_deg,
            self.longitude_deg,
            other.latitude_deg,
            other.longitude_deg,
            model=model,
            unit="km"
        )

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
