"""Runway data model for AeroNavX."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Runway:
    """
    Represents an airport runway with detailed information.

    Attributes:
        id: Unique runway identifier
        airport_ref: Reference to parent airport
        airport_ident: Airport identifier code
        length_ft: Runway length in feet
        width_ft: Runway width in feet
        surface: Surface material (e.g., 'ASPH', 'CONC', 'GRASS')
        lighted: Whether runway is lighted
        closed: Whether runway is closed
        le_ident: Low end runway identifier (e.g., '09L')
        le_latitude_deg: Low end latitude
        le_longitude_deg: Low end longitude
        le_elevation_ft: Low end elevation in feet
        le_heading_degT: Low end true heading in degrees
        le_displaced_threshold_ft: Low end displaced threshold in feet
        he_ident: High end runway identifier (e.g., '27R')
        he_latitude_deg: High end latitude
        he_longitude_deg: High end longitude
        he_elevation_ft: High end elevation in feet
        he_heading_degT: High end true heading in degrees
        he_displaced_threshold_ft: High end displaced threshold in feet

    Example:
        >>> runway = Runway(
        ...     id=12345,
        ...     airport_ident='KJFK',
        ...     length_ft=14511,
        ...     width_ft=200,
        ...     surface='ASPH',
        ...     lighted=True,
        ...     le_ident='04L',
        ...     he_ident='22R'
        ... )
        >>> print(f"{runway.le_ident}/{runway.he_ident}: {runway.length_ft}ft")
        04L/22R: 14511ft
    """

    id: int
    airport_ref: int
    airport_ident: str
    length_ft: Optional[float] = None
    width_ft: Optional[float] = None
    surface: Optional[str] = None
    lighted: Optional[bool] = None
    closed: Optional[bool] = None

    # Low end (LE)
    le_ident: Optional[str] = None
    le_latitude_deg: Optional[float] = None
    le_longitude_deg: Optional[float] = None
    le_elevation_ft: Optional[float] = None
    le_heading_degT: Optional[float] = None
    le_displaced_threshold_ft: Optional[float] = None

    # High end (HE)
    he_ident: Optional[str] = None
    he_latitude_deg: Optional[float] = None
    he_longitude_deg: Optional[float] = None
    he_elevation_ft: Optional[float] = None
    he_heading_degT: Optional[float] = None
    he_displaced_threshold_ft: Optional[float] = None

    @property
    def designation(self) -> str:
        """Get runway designation (e.g., '09L/27R')."""
        parts = []
        if self.le_ident:
            parts.append(self.le_ident)
        if self.he_ident:
            parts.append(self.he_ident)
        return "/".join(parts) if parts else "Unknown"

    @property
    def length_m(self) -> Optional[float]:
        """Get runway length in meters."""
        return self.length_ft * 0.3048 if self.length_ft else None

    @property
    def width_m(self) -> Optional[float]:
        """Get runway width in meters."""
        return self.width_ft * 0.3048 if self.width_ft else None

    @property
    def is_operational(self) -> bool:
        """Check if runway is operational (not closed)."""
        return not self.closed

    @property
    def is_paved(self) -> bool:
        """Check if runway surface is paved."""
        if not self.surface:
            return False
        paved_surfaces = ['ASPH', 'CONC', 'ASPH-CONC', 'CONC-ASPH', 'PEM', 'BIT']
        return any(s in self.surface.upper() for s in paved_surfaces)

    def as_dict(self) -> dict:
        """Convert runway to dictionary."""
        return {
            'id': self.id,
            'airport_ref': self.airport_ref,
            'airport_ident': self.airport_ident,
            'designation': self.designation,
            'length_ft': self.length_ft,
            'width_ft': self.width_ft,
            'length_m': self.length_m,
            'width_m': self.width_m,
            'surface': self.surface,
            'lighted': self.lighted,
            'closed': self.closed,
            'is_operational': self.is_operational,
            'is_paved': self.is_paved,
            'le_ident': self.le_ident,
            'le_latitude_deg': self.le_latitude_deg,
            'le_longitude_deg': self.le_longitude_deg,
            'le_elevation_ft': self.le_elevation_ft,
            'le_heading_degT': self.le_heading_degT,
            'he_ident': self.he_ident,
            'he_latitude_deg': self.he_latitude_deg,
            'he_longitude_deg': self.he_longitude_deg,
            'he_elevation_ft': self.he_elevation_ft,
            'he_heading_degT': self.he_heading_degT,
        }

    def __repr__(self) -> str:
        """String representation of runway."""
        length_str = f"{self.length_ft:.0f}ft" if self.length_ft else "unknown"
        return f"<Runway {self.airport_ident} {self.designation}: {length_str}, {self.surface or 'unknown surface'}>"
