"""
AeroNavX Geo-Spatial Advanced Layer v2.0

Advanced geospatial calculations for aviation:
- Flight corridors and restricted zones
- Optimal altitude selection by latitude
- Wind-optimized routing
- Rhumb line vs great circle comparison
- Airspace classification
- Polar route calculations
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import math

from ..models.airport import Airport
from ..core.distance import distance
from ..core.geodesy import initial_bearing, midpoint, great_circle_path
from ..utils.logging import get_logger

logger = get_logger()


class AirspaceClass(Enum):
    """ICAO airspace classifications."""
    CLASS_A = "A"  # IFR only, ATC clearance required
    CLASS_B = "B"  # IFR & VFR, ATC clearance required
    CLASS_C = "C"  # IFR & VFR, ATC clearance required (VFR: radio contact)
    CLASS_D = "D"  # IFR & VFR, ATC clearance required (IFR), radio contact (VFR)
    CLASS_E = "E"  # IFR & VFR, controlled
    CLASS_F = "F"  # Advisory service
    CLASS_G = "G"  # Uncontrolled


class RouteType(Enum):
    """Route calculation methods."""
    GREAT_CIRCLE = "great_circle"  # Shortest distance
    RHUMB_LINE = "rhumb_line"  # Constant bearing
    WIND_OPTIMIZED = "wind_optimized"  # Accounting for winds
    POLAR_OPTIMIZED = "polar_optimized"  # Special polar considerations


@dataclass
class FlightCorridor:
    """Flight corridor with width and altitude constraints."""
    centerline: List[Tuple[float, float]]  # (lat, lon) points
    width_km: float  # Corridor width
    min_altitude_ft: int
    max_altitude_ft: int
    name: str

    def contains_point(self, lat: float, lon: float, alt_ft: int) -> bool:
        """Check if point is within corridor."""
        # Check altitude
        if alt_ft < self.min_altitude_ft or alt_ft > self.max_altitude_ft:
            return False

        # Find closest point on centerline
        min_dist = float('inf')

        for i in range(len(self.centerline) - 1):
            # Distance to line segment
            # Simplified: just check distance to centerline points
            dist = distance(
                lat, lon,
                self.centerline[i][0], self.centerline[i][1],
                unit="km"
            )
            if dist < min_dist:
                min_dist = dist

        return min_dist <= (self.width_km / 2.0)


@dataclass
class RestrictedZone:
    """Restricted or prohibited airspace zone."""
    center_lat: float
    center_lon: float
    radius_km: float
    min_altitude_ft: int
    max_altitude_ft: int
    name: str
    zone_type: str  # "prohibited", "restricted", "danger", "military"

    def intersects_route(
        self,
        route_points: List[Tuple[float, float]],
        altitude_ft: int
    ) -> bool:
        """Check if route intersects this zone at given altitude."""
        # Check altitude range
        if altitude_ft < self.min_altitude_ft or altitude_ft > self.max_altitude_ft:
            return False

        # Check each route segment
        for point in route_points:
            dist = distance(
                point[0], point[1],
                self.center_lat, self.center_lon,
                unit="km"
            )
            if dist <= self.radius_km:
                return True

        return False


@dataclass
class OptimalAltitude:
    """Optimal altitude recommendation."""
    altitude_ft: int
    reason: str
    fuel_efficiency_score: float  # 0-100
    airspace_class: AirspaceClass
    jet_stream_benefit_kts: float  # Wind benefit/penalty


@dataclass
class RouteComparison:
    """Comparison of different route types."""
    great_circle_km: float
    rhumb_line_km: float
    distance_difference_km: float
    distance_difference_pct: float
    bearing_change_deg: float
    recommendation: RouteType


class GeoSpatialAdvanced:
    """
    Advanced geospatial analysis for aviation.

    Features:
    - Flight corridor analysis
    - Restricted zone avoidance
    - Optimal altitude selection
    - Route type comparison
    - Polar route handling
    """

    def __init__(self):
        """Initialize geospatial analyzer."""
        self.known_corridors: List[FlightCorridor] = []
        self.restricted_zones: List[RestrictedZone] = []

    def calculate_rhumb_line_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate rhumb line (constant bearing) distance.

        Rhumb lines are longer than great circles but easier to navigate
        (constant compass heading).

        Args:
            lat1, lon1: Start point
            lat2, lon2: End point

        Returns:
            Distance in kilometers
        """
        R = 6371.0  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = lat2_rad - lat1_rad
        delta_lon = math.radians(lon2 - lon1)

        # Handle the date line
        if abs(delta_lon) > math.pi:
            delta_lon = delta_lon - 2 * math.pi if delta_lon > 0 else delta_lon + 2 * math.pi

        # Calculate delta psi (isometric latitude difference)
        delta_psi = math.log(
            math.tan(lat2_rad / 2 + math.pi / 4) /
            math.tan(lat1_rad / 2 + math.pi / 4)
        )

        # Avoid division by zero
        if abs(delta_psi) < 1e-12:
            q = math.cos(lat1_rad)
        else:
            q = delta_lat / delta_psi

        # Distance
        dist = math.sqrt(delta_lat ** 2 + (q * delta_lon) ** 2) * R

        return dist

    def compare_route_types(
        self,
        origin: Airport,
        destination: Airport
    ) -> RouteComparison:
        """
        Compare great circle vs rhumb line routes.

        Args:
            origin: Origin airport
            destination: Destination airport

        Returns:
            RouteComparison with analysis
        """
        # Great circle distance
        gc_dist = distance(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            model="vincenty",
            unit="km"
        )

        # Rhumb line distance
        rl_dist = self.calculate_rhumb_line_distance(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg
        )

        # Calculate difference
        diff_km = rl_dist - gc_dist
        diff_pct = (diff_km / gc_dist) * 100 if gc_dist > 0 else 0

        # Calculate bearing change for great circle
        start_bearing = initial_bearing(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg
        )

        # End bearing (reverse)
        end_bearing = initial_bearing(
            destination.latitude_deg, destination.longitude_deg,
            origin.latitude_deg, origin.longitude_deg
        )
        end_bearing = (end_bearing + 180) % 360

        bearing_change = abs(end_bearing - start_bearing)
        if bearing_change > 180:
            bearing_change = 360 - bearing_change

        # Recommendation
        if diff_pct < 0.5:
            # Very small difference - rhumb line is fine
            recommendation = RouteType.RHUMB_LINE
        elif diff_pct > 2.0:
            # Significant difference - use great circle
            recommendation = RouteType.GREAT_CIRCLE
        else:
            # Moderate difference - consider other factors
            if bearing_change < 10:
                recommendation = RouteType.RHUMB_LINE
            else:
                recommendation = RouteType.GREAT_CIRCLE

        return RouteComparison(
            great_circle_km=gc_dist,
            rhumb_line_km=rl_dist,
            distance_difference_km=diff_km,
            distance_difference_pct=diff_pct,
            bearing_change_deg=bearing_change,
            recommendation=recommendation
        )

    def calculate_optimal_altitude(
        self,
        origin: Airport,
        destination: Airport,
        aircraft_weight_kg: float = 70000,
        wind_direction_deg: Optional[float] = None,
        wind_speed_kts: Optional[float] = None
    ) -> OptimalAltitude:
        """
        Calculate optimal cruise altitude considering various factors.

        Factors:
        - Latitude (jet stream consideration)
        - Distance (fuel efficiency)
        - Aircraft weight
        - Wind patterns

        Args:
            origin: Origin airport
            destination: Destination airport
            aircraft_weight_kg: Aircraft weight
            wind_direction_deg: Wind direction (optional)
            wind_speed_kts: Wind speed (optional)

        Returns:
            OptimalAltitude recommendation
        """
        # Calculate route midpoint
        mid_lat, mid_lon = midpoint(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg
        )

        # Distance
        dist_km = distance(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            unit="km"
        )

        # Base altitude on distance and weight
        if dist_km < 500:
            # Short flight - lower altitude
            base_altitude = 25000
        elif dist_km < 1500:
            # Medium flight
            base_altitude = 33000
        elif dist_km < 5000:
            # Long flight
            base_altitude = 37000
        else:
            # Ultra-long flight - maximize altitude
            base_altitude = 41000

        # Adjust for weight (heavier = lower initial cruise)
        if aircraft_weight_kg > 100000:
            base_altitude -= 2000
        elif aircraft_weight_kg < 50000:
            base_altitude += 2000

        # Consider jet stream (typically at 30-40k feet, 30-60° latitude)
        jet_stream_benefit = 0.0

        if 30 <= abs(mid_lat) <= 60:
            # In jet stream latitude band
            if wind_direction_deg is not None and wind_speed_kts is not None:
                # Calculate if wind is beneficial
                route_bearing = initial_bearing(
                    origin.latitude_deg, origin.longitude_deg,
                    destination.latitude_deg, destination.longitude_deg
                )

                # Wind coming from behind is beneficial
                bearing_diff = abs(wind_direction_deg - route_bearing)
                if bearing_diff > 180:
                    bearing_diff = 360 - bearing_diff

                # Tailwind component
                if bearing_diff < 90:
                    jet_stream_benefit = wind_speed_kts * math.cos(math.radians(bearing_diff))
                    # Climb higher to catch jet stream
                    if jet_stream_benefit > 30:  # Strong tailwind
                        base_altitude += 2000
                else:
                    jet_stream_benefit = -wind_speed_kts * math.cos(math.radians(bearing_diff - 180))
                    # Stay lower to avoid headwind
                    if jet_stream_benefit < -30:
                        base_altitude -= 2000

        # Determine airspace class at altitude
        if base_altitude >= 18000:
            airspace = AirspaceClass.CLASS_A  # Class A above FL180 in most countries
        elif base_altitude >= 10000:
            airspace = AirspaceClass.CLASS_E
        else:
            airspace = AirspaceClass.CLASS_E

        # Fuel efficiency score (higher altitude generally better for jets)
        # Optimal for most jets: 35,000 - 41,000 ft
        fuel_score = 100 - abs(base_altitude - 38000) / 400

        reason_parts = []

        if dist_km < 500:
            reason_parts.append("short distance")
        elif dist_km > 5000:
            reason_parts.append("long-haul flight")

        if jet_stream_benefit > 0:
            reason_parts.append(f"jet stream tailwind (+{jet_stream_benefit:.0f}kts)")
        elif jet_stream_benefit < 0:
            reason_parts.append(f"avoiding jet stream headwind")

        if aircraft_weight_kg > 100000:
            reason_parts.append("heavy aircraft")

        reason = "Optimized for: " + ", ".join(reason_parts) if reason_parts else "Standard cruise altitude"

        return OptimalAltitude(
            altitude_ft=base_altitude,
            reason=reason,
            fuel_efficiency_score=max(0, min(100, fuel_score)),
            airspace_class=airspace,
            jet_stream_benefit_kts=jet_stream_benefit
        )

    def is_polar_route(
        self,
        origin: Airport,
        destination: Airport,
        polar_threshold_deg: float = 70.0
    ) -> bool:
        """
        Check if route passes through polar regions.

        Args:
            origin: Origin airport
            destination: Destination airport
            polar_threshold_deg: Latitude threshold for polar region

        Returns:
            True if route passes near poles
        """
        # Check if either endpoint is in polar region
        if abs(origin.latitude_deg) >= polar_threshold_deg or \
           abs(destination.latitude_deg) >= polar_threshold_deg:
            return True

        # Check midpoint
        mid_lat, _ = midpoint(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg
        )

        return abs(mid_lat) >= polar_threshold_deg

    def calculate_polar_route_considerations(
        self,
        origin: Airport,
        destination: Airport
    ) -> Dict[str, any]:
        """
        Calculate special considerations for polar routes.

        Polar routes have special requirements:
        - ETOPS certification
        - Cold weather operations
        - Magnetic compass unreliability
        - Limited diversion airports

        Args:
            origin: Origin airport
            destination: Destination airport

        Returns:
            Dict with polar route considerations
        """
        is_polar = self.is_polar_route(origin, destination)

        if not is_polar:
            return {
                "is_polar_route": False,
                "considerations": []
            }

        considerations = []

        # Calculate maximum latitude
        max_lat = max(abs(origin.latitude_deg), abs(destination.latitude_deg))

        # Check midpoint
        mid_lat, mid_lon = midpoint(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg
        )
        max_lat = max(max_lat, abs(mid_lat))

        if max_lat > 80:
            considerations.append("Extreme polar route - special authorization required")
            considerations.append("Magnetic compass unreliable - GPS/INS navigation essential")

        if max_lat > 70:
            considerations.append("ETOPS 180 or higher certification recommended")
            considerations.append("Cold weather operations procedures required")
            considerations.append("Limited diversion airports - carry extra fuel")

        # Estimate fuel for polar operations
        # Typically 10-15% extra for contingencies
        considerations.append("Recommend 12% additional fuel for polar contingencies")

        # Communication challenges
        if max_lat > 75:
            considerations.append("HF radio communication required (satellite backup)")

        return {
            "is_polar_route": True,
            "maximum_latitude": max_lat,
            "route_midpoint": (mid_lat, mid_lon),
            "considerations": considerations
        }

    def generate_corridor(
        self,
        origin: Airport,
        destination: Airport,
        width_km: float = 10.0,
        altitude_ft: int = 35000,
        altitude_tolerance_ft: int = 4000,
        num_points: int = 50
    ) -> FlightCorridor:
        """
        Generate flight corridor along great circle route.

        Args:
            origin: Origin airport
            destination: Destination airport
            width_km: Corridor width
            altitude_ft: Center altitude
            altitude_tolerance_ft: Altitude tolerance (+/-)
            num_points: Number of centerline points

        Returns:
            FlightCorridor object
        """
        centerline = []

        for i in range(num_points):
            fraction = i / (num_points - 1)
            lat, lon = great_circle_path(
                origin.latitude_deg, origin.longitude_deg,
                destination.latitude_deg, destination.longitude_deg,
                fraction=fraction
            )
            centerline.append((lat, lon))

        origin_code = origin.iata_code or origin.ident
        dest_code = destination.iata_code or destination.ident

        return FlightCorridor(
            centerline=centerline,
            width_km=width_km,
            min_altitude_ft=altitude_ft - altitude_tolerance_ft,
            max_altitude_ft=altitude_ft + altitude_tolerance_ft,
            name=f"{origin_code}-{dest_code} Corridor"
        )


# Convenience functions
def compare_routes(origin: Airport, destination: Airport) -> RouteComparison:
    """Compare great circle vs rhumb line routes."""
    analyzer = GeoSpatialAdvanced()
    return analyzer.compare_route_types(origin, destination)


def get_optimal_altitude(
    origin: Airport,
    destination: Airport,
    aircraft_weight_kg: float = 70000
) -> OptimalAltitude:
    """Get optimal cruise altitude recommendation."""
    analyzer = GeoSpatialAdvanced()
    return analyzer.calculate_optimal_altitude(origin, destination, aircraft_weight_kg)


def check_polar_route(origin: Airport, destination: Airport) -> Dict[str, any]:
    """Check if route is polar and get special considerations."""
    analyzer = GeoSpatialAdvanced()
    return analyzer.calculate_polar_route_considerations(origin, destination)
