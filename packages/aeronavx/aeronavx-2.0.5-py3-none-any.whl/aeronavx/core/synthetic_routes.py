"""
AeroNavX Synthetic Route Engine v2.0

Generate realistic flight routes for testing, simulation, and training:
- Multi-leg route generation with waypoints
- Alternative route suggestions
- Emergency diversion planning
- Realistic flight profiles (altitude, speed, fuel)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math

from ..models.airport import Airport
from ..core.loader import get_airport_by_iata, get_airport_by_icao
from ..core.distance import distance
from ..core.geodesy import initial_bearing, midpoint, great_circle_path, intermediate_point
from ..core.search import nearest_airports, airports_within_radius
from ..core.routing import estimate_flight_time_hours
from ..utils.logging import get_logger

logger = get_logger()


class FlightPhase(Enum):
    """Flight phases for profile generation."""
    TAXI_OUT = "taxi_out"
    TAKEOFF = "takeoff"
    CLIMB = "climb"
    CRUISE = "cruise"
    DESCENT = "descent"
    APPROACH = "approach"
    LANDING = "landing"
    TAXI_IN = "taxi_in"


class AircraftCategory(Enum):
    """Aircraft categories for realistic performance."""
    NARROW_BODY = "narrow_body"  # A320, B737
    WIDE_BODY = "wide_body"  # A350, B777
    REGIONAL = "regional"  # CRJ, E175
    PRIVATE_JET = "private_jet"  # G650, Falcon


@dataclass
class FlightProfile:
    """Realistic flight profile with performance data."""
    aircraft_category: AircraftCategory
    cruise_altitude_ft: int
    cruise_speed_kts: int
    climb_rate_fpm: int  # Feet per minute
    descent_rate_fpm: int
    fuel_burn_kg_per_hour: float
    max_range_km: float

    @staticmethod
    def get_profile(category: AircraftCategory) -> 'FlightProfile':
        """Get realistic profile for aircraft category."""
        profiles = {
            AircraftCategory.NARROW_BODY: FlightProfile(
                aircraft_category=category,
                cruise_altitude_ft=39000,
                cruise_speed_kts=450,
                climb_rate_fpm=2000,
                descent_rate_fpm=1500,
                fuel_burn_kg_per_hour=2500,
                max_range_km=6000
            ),
            AircraftCategory.WIDE_BODY: FlightProfile(
                aircraft_category=category,
                cruise_altitude_ft=43000,
                cruise_speed_kts=490,
                climb_rate_fpm=1500,
                descent_rate_fpm=1200,
                fuel_burn_kg_per_hour=7000,
                max_range_km=15000
            ),
            AircraftCategory.REGIONAL: FlightProfile(
                aircraft_category=category,
                cruise_altitude_ft=31000,
                cruise_speed_kts=380,
                climb_rate_fpm=2500,
                descent_rate_fpm=1800,
                fuel_burn_kg_per_hour=1200,
                max_range_km=3000
            ),
            AircraftCategory.PRIVATE_JET: FlightProfile(
                aircraft_category=category,
                cruise_altitude_ft=45000,
                cruise_speed_kts=480,
                climb_rate_fpm=3000,
                descent_rate_fpm=2000,
                fuel_burn_kg_per_hour=900,
                max_range_km=12000
            )
        }
        return profiles[category]


@dataclass
class Waypoint:
    """Route waypoint with timing and altitude."""
    latitude: float
    longitude: float
    altitude_ft: int
    speed_kts: int
    phase: FlightPhase
    time_from_start_minutes: float
    fuel_remaining_kg: Optional[float] = None
    name: Optional[str] = None  # If it's a named fix or airport
    distance_from_origin_km: float = 0.0  # Distance from origin

    def __repr__(self):
        name_str = f" ({self.name})" if self.name else ""
        return (
            f"Waypoint{name_str}: {self.latitude:.2f},{self.longitude:.2f} "
            f"@ {self.altitude_ft}ft, {self.speed_kts}kts"
        )


@dataclass
class SyntheticRoute:
    """Complete synthetic flight route."""
    origin: Airport
    destination: Airport
    waypoints: List[Waypoint]
    total_distance_km: float
    total_time_hours: float
    total_fuel_kg: float
    flight_profile: FlightProfile
    intermediate_airports: List[Airport] = field(default_factory=list)
    diversion_airports: List[Airport] = field(default_factory=list)

    def get_cruise_waypoints(self) -> List[Waypoint]:
        """Get waypoints during cruise phase."""
        return [w for w in self.waypoints if w.phase == FlightPhase.CRUISE]

    def get_total_distance_nmi(self) -> float:
        """Get total distance in nautical miles."""
        return self.total_distance_km * 0.539957

    def __repr__(self):
        origin_code = self.origin.iata_code or self.origin.ident
        dest_code = self.destination.iata_code or self.destination.ident
        return (
            f"SyntheticRoute({origin_code} → {dest_code}: "
            f"{self.total_distance_km:.0f}km, {self.total_time_hours:.1f}hrs)"
        )


class SyntheticRouteEngine:
    """
    Generate realistic synthetic flight routes.

    Features:
    - Multi-leg routes with intermediate stops
    - Realistic waypoint generation
    - Flight profile simulation
    - Fuel planning
    - Emergency diversion airports
    """

    def __init__(
        self,
        default_aircraft: AircraftCategory = AircraftCategory.NARROW_BODY,
        waypoint_spacing_km: float = 100.0
    ):
        """
        Initialize synthetic route engine.

        Args:
            default_aircraft: Default aircraft category
            waypoint_spacing_km: Spacing between generated waypoints
        """
        self.default_aircraft = default_aircraft
        self.waypoint_spacing_km = waypoint_spacing_km

    def generate_direct_route(
        self,
        origin_code: str,
        destination_code: str,
        aircraft: Optional[AircraftCategory] = None,
        code_type: str = "iata"
    ) -> SyntheticRoute:
        """
        Generate direct route with realistic waypoints and profile.

        Args:
            origin_code: Origin airport code
            destination_code: Destination airport code
            aircraft: Aircraft category (optional)
            code_type: Code type ('iata' or 'icao')

        Returns:
            SyntheticRoute object
        """
        # Get airports
        if code_type == "iata":
            origin = get_airport_by_iata(origin_code)
            destination = get_airport_by_iata(destination_code)
        else:
            origin = get_airport_by_icao(origin_code)
            destination = get_airport_by_icao(destination_code)

        if not origin:
            raise ValueError(f"Origin airport not found: {origin_code}")
        if not destination:
            raise ValueError(f"Destination airport not found: {destination_code}")

        # Get flight profile
        aircraft_cat = aircraft or self.default_aircraft
        profile = FlightProfile.get_profile(aircraft_cat)

        # Calculate total distance
        total_distance_km = distance(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            unit="km"
        )

        # Check if route is within aircraft range
        if total_distance_km > profile.max_range_km:
            logger.warning(
                f"Route {total_distance_km:.0f}km exceeds max range "
                f"{profile.max_range_km:.0f}km - will need refueling stop"
            )

        # Generate waypoints along great circle path
        waypoints = self._generate_waypoints(
            origin, destination, profile, total_distance_km
        )

        # Calculate total time
        total_time_hours = estimate_flight_time_hours(
            origin, destination,
            speed_kts=profile.cruise_speed_kts
        )

        # Add time for climb/descent
        climb_time_hours = (profile.cruise_altitude_ft / profile.climb_rate_fpm) / 60
        descent_time_hours = (profile.cruise_altitude_ft / profile.descent_rate_fpm) / 60
        total_time_hours += climb_time_hours + descent_time_hours

        # Calculate fuel
        total_fuel_kg = total_time_hours * profile.fuel_burn_kg_per_hour
        # Add 10% reserve
        total_fuel_kg *= 1.10

        # Find diversion airports along route
        diversion_airports = self._find_diversion_airports(
            origin, destination, total_distance_km
        )

        return SyntheticRoute(
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            total_distance_km=total_distance_km,
            total_time_hours=total_time_hours,
            total_fuel_kg=total_fuel_kg,
            flight_profile=profile,
            diversion_airports=diversion_airports
        )

    def generate_multi_leg_route(
        self,
        airport_codes: List[str],
        aircraft: Optional[AircraftCategory] = None,
        code_type: str = "iata"
    ) -> List[SyntheticRoute]:
        """
        Generate multi-leg route with stops.

        Args:
            airport_codes: List of airport codes (minimum 2)
            aircraft: Aircraft category
            code_type: Code type ('iata' or 'icao')

        Returns:
            List of SyntheticRoute objects (one per leg)
        """
        if len(airport_codes) < 2:
            raise ValueError("Need at least 2 airports for a route")

        routes = []

        for i in range(len(airport_codes) - 1):
            route = self.generate_direct_route(
                airport_codes[i],
                airport_codes[i + 1],
                aircraft=aircraft,
                code_type=code_type
            )
            routes.append(route)

        return routes

    def generate_random_route(
        self,
        origin_code: str,
        max_distance_km: float = 5000.0,
        aircraft: Optional[AircraftCategory] = None,
        code_type: str = "iata"
    ) -> SyntheticRoute:
        """
        Generate random route from origin within distance limit.

        Args:
            origin_code: Origin airport code
            max_distance_km: Maximum route distance
            aircraft: Aircraft category
            code_type: Code type

        Returns:
            SyntheticRoute to random destination
        """
        # Get origin
        if code_type == "iata":
            origin = get_airport_by_iata(origin_code)
        else:
            origin = get_airport_by_icao(origin_code)

        if not origin:
            raise ValueError(f"Origin airport not found: {origin_code}")

        # Find airports within range
        candidates = airports_within_radius(
            origin.latitude_deg,
            origin.longitude_deg,
            max_distance_km
        )

        # Filter to medium/large airports
        candidates = [
            a for a in candidates
            if a.type in ["medium_airport", "large_airport"]
            and a.ident != origin.ident
        ]

        if not candidates:
            raise ValueError(f"No suitable destinations within {max_distance_km}km")

        # Pick random destination
        destination = random.choice(candidates)

        dest_code = destination.iata_code or destination.ident

        return self.generate_direct_route(
            origin_code, dest_code, aircraft=aircraft, code_type=code_type
        )

    def _generate_waypoints(
        self,
        origin: Airport,
        destination: Airport,
        profile: FlightProfile,
        total_distance_km: float
    ) -> List[Waypoint]:
        """Generate realistic waypoints along route."""
        waypoints = []

        # 1. Taxi out + Takeoff
        waypoints.append(Waypoint(
            latitude=origin.latitude_deg,
            longitude=origin.longitude_deg,
            altitude_ft=0,
            speed_kts=0,
            phase=FlightPhase.TAXI_OUT,
            time_from_start_minutes=0,
            name=origin.iata_code or origin.ident
        ))

        time_elapsed = 5  # 5 min taxi

        waypoints.append(Waypoint(
            latitude=origin.latitude_deg,
            longitude=origin.longitude_deg,
            altitude_ft=50,
            speed_kts=150,
            phase=FlightPhase.TAKEOFF,
            time_from_start_minutes=time_elapsed,
            name=f"{origin.iata_code or origin.ident} Departure"
        ))

        time_elapsed += 2  # 2 min takeoff

        # 2. Climb to cruise
        climb_time_min = (profile.cruise_altitude_ft / profile.climb_rate_fpm)
        climb_distance_km = (profile.cruise_speed_kts * 0.514444 * climb_time_min * 60) / 1000

        # Waypoint at top of climb
        climb_fraction = climb_distance_km / total_distance_km
        climb_pos = intermediate_point(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            climb_fraction
        )

        waypoints.append(Waypoint(
            latitude=climb_pos[0],
            longitude=climb_pos[1],
            altitude_ft=profile.cruise_altitude_ft,
            speed_kts=profile.cruise_speed_kts,
            phase=FlightPhase.CLIMB,
            time_from_start_minutes=time_elapsed + climb_time_min,
            name="Top of Climb"
        ))

        time_elapsed += climb_time_min

        # 3. Cruise waypoints
        cruise_distance_km = total_distance_km - climb_distance_km - climb_distance_km  # Symmetric

        num_cruise_waypoints = max(1, int(cruise_distance_km / self.waypoint_spacing_km))

        for i in range(1, num_cruise_waypoints + 1):
            fraction = climb_fraction + (i / (num_cruise_waypoints + 1)) * (1 - 2 * climb_fraction)
            pos = intermediate_point(
                origin.latitude_deg, origin.longitude_deg,
                destination.latitude_deg, destination.longitude_deg,
                fraction
            )

            segment_distance = (cruise_distance_km / (num_cruise_waypoints + 1))
            segment_time = (segment_distance / (profile.cruise_speed_kts * 1.852))  # hrs to min
            time_elapsed += segment_time * 60

            waypoints.append(Waypoint(
                latitude=pos[0],
                longitude=pos[1],
                altitude_ft=profile.cruise_altitude_ft,
                speed_kts=profile.cruise_speed_kts,
                phase=FlightPhase.CRUISE,
                time_from_start_minutes=time_elapsed,
                name=f"Cruise WP{i}"
            ))

        # 4. Top of descent
        descent_time_min = (profile.cruise_altitude_ft / profile.descent_rate_fpm)
        descent_fraction = 1 - climb_fraction

        tod_pos = intermediate_point(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            descent_fraction
        )

        waypoints.append(Waypoint(
            latitude=tod_pos[0],
            longitude=tod_pos[1],
            altitude_ft=profile.cruise_altitude_ft,
            speed_kts=profile.cruise_speed_kts,
            phase=FlightPhase.DESCENT,
            time_from_start_minutes=time_elapsed,
            name="Top of Descent"
        ))

        time_elapsed += descent_time_min

        # 5. Approach
        waypoints.append(Waypoint(
            latitude=destination.latitude_deg,
            longitude=destination.longitude_deg,
            altitude_ft=2000,
            speed_kts=180,
            phase=FlightPhase.APPROACH,
            time_from_start_minutes=time_elapsed,
            name=f"{destination.iata_code or destination.ident} Approach"
        ))

        time_elapsed += 5  # 5 min approach

        # 6. Landing + Taxi
        waypoints.append(Waypoint(
            latitude=destination.latitude_deg,
            longitude=destination.longitude_deg,
            altitude_ft=0,
            speed_kts=60,
            phase=FlightPhase.LANDING,
            time_from_start_minutes=time_elapsed,
            name=destination.iata_code or destination.ident
        ))

        time_elapsed += 2

        waypoints.append(Waypoint(
            latitude=destination.latitude_deg,
            longitude=destination.longitude_deg,
            altitude_ft=0,
            speed_kts=0,
            phase=FlightPhase.TAXI_IN,
            time_from_start_minutes=time_elapsed,
            name=f"{destination.iata_code or destination.ident} Gate"
        ))

        return waypoints

    def _find_diversion_airports(
        self,
        origin: Airport,
        destination: Airport,
        total_distance_km: float,
        max_diversion_distance_km: float = 300.0
    ) -> List[Airport]:
        """Find suitable diversion airports along route."""
        # Sample points along route
        diversion_candidates = []

        for fraction in [0.25, 0.5, 0.75]:
            pos = intermediate_point(
                origin.latitude_deg, origin.longitude_deg,
                destination.latitude_deg, destination.longitude_deg,
                fraction
            )

            # Find nearby airports
            nearby = airports_within_radius(
                pos[0], pos[1],
                max_diversion_distance_km
            )

            # Filter to medium/large airports
            suitable = [
                a for a in nearby
                if a.type in ["medium_airport", "large_airport"]
                and a.ident not in [origin.ident, destination.ident]
            ]

            # Add closest airport at this position
            if suitable:
                # Sort by distance
                suitable.sort(
                    key=lambda a: distance(
                        pos[0], pos[1],
                        a.latitude_deg, a.longitude_deg,
                        unit="km"
                    )
                )
                if suitable[0] not in diversion_candidates:
                    diversion_candidates.append(suitable[0])

        return diversion_candidates[:5]  # Return up to 5 diversion airports


# Convenience functions
def generate_route(
    origin: str,
    destination: str,
    aircraft: str = "narrow_body"
) -> SyntheticRoute:
    """
    Generate synthetic route (convenience function).

    Args:
        origin: Origin airport code
        destination: Destination airport code
        aircraft: Aircraft type ('narrow_body', 'wide_body', 'regional', 'private_jet')

    Returns:
        SyntheticRoute object
    """
    aircraft_map = {
        "narrow_body": AircraftCategory.NARROW_BODY,
        "wide_body": AircraftCategory.WIDE_BODY,
        "regional": AircraftCategory.REGIONAL,
        "private_jet": AircraftCategory.PRIVATE_JET
    }

    aircraft_cat = aircraft_map.get(aircraft, AircraftCategory.NARROW_BODY)

    engine = SyntheticRouteEngine()
    return engine.generate_direct_route(origin, destination, aircraft=aircraft_cat)


def generate_random_route_from(
    origin: str,
    max_distance_km: float = 5000.0,
    aircraft: str = "narrow_body"
) -> SyntheticRoute:
    """
    Generate random route from origin.

    Args:
        origin: Origin airport code
        max_distance_km: Maximum distance
        aircraft: Aircraft type

    Returns:
        SyntheticRoute to random destination
    """
    aircraft_map = {
        "narrow_body": AircraftCategory.NARROW_BODY,
        "wide_body": AircraftCategory.WIDE_BODY,
        "regional": AircraftCategory.REGIONAL,
        "private_jet": AircraftCategory.PRIVATE_JET
    }

    aircraft_cat = aircraft_map.get(aircraft, AircraftCategory.NARROW_BODY)

    engine = SyntheticRouteEngine()
    return engine.generate_random_route(origin, max_distance_km, aircraft=aircraft_cat)
