"""
AeroNavX Network Intelligence Layer v2.0

Advanced network analysis for aviation:
- Hub detection and scoring
- Network centrality analysis
- Geographic coverage optimization
- Connection pattern analysis
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math

from ..models.airport import Airport
from ..core.loader import get_all_airports
from ..core.distance import distance
from ..core.search import airports_within_radius, nearest_airports
from ..utils.logging import get_logger

logger = get_logger()


@dataclass
class HubScore:
    """Hub potential score for an airport."""
    airport: Airport
    hub_score: float  # 0-100
    connectivity_score: float  # Potential connections within range
    geographic_score: float  # Strategic location
    infrastructure_score: float  # Airport size/capacity
    factors: Dict[str, float]  # Breakdown of scoring factors

    def __repr__(self):
        return (
            f"HubScore({self.airport.iata_code or self.airport.ident}: "
            f"{self.hub_score:.1f}/100)"
        )


@dataclass
class NetworkMetrics:
    """Network-wide metrics."""
    total_airports: int
    potential_connections: int
    average_connectivity: float
    network_density: float
    top_hubs: List[HubScore]
    coverage_gaps: List[Tuple[float, float]]  # (lat, lon) of underserved regions


class NetworkIntelligence:
    """
    Intelligent network analysis for aviation.

    Features:
    - Hub detection based on geographic position and connectivity
    - Network centrality calculations
    - Coverage gap analysis
    - Strategic positioning insights
    """

    def __init__(
        self,
        max_connection_range_km: float = 5000.0,
        min_airport_size: str = "medium_airport"
    ):
        """
        Initialize network intelligence engine.

        Args:
            max_connection_range_km: Maximum range for viable connections
            min_airport_size: Minimum airport type to consider
        """
        self.max_connection_range_km = max_connection_range_km
        self.min_airport_size = min_airport_size
        self._airports_cache: Optional[List[Airport]] = None

    def get_eligible_airports(self) -> List[Airport]:
        """Get airports eligible for network analysis."""
        if self._airports_cache is not None:
            return self._airports_cache

        all_airports = get_all_airports()

        # Filter by size if needed
        size_priority = {
            "large_airport": 3,
            "medium_airport": 2,
            "small_airport": 1
        }

        min_priority = size_priority.get(self.min_airport_size, 0)

        eligible = [
            airport for airport in all_airports
            if size_priority.get(airport.type, 0) >= min_priority
        ]

        self._airports_cache = eligible
        logger.info(f"Loaded {len(eligible)} eligible airports for network analysis")
        return eligible

    def calculate_hub_score(
        self,
        airport: Airport,
        all_airports: Optional[List[Airport]] = None
    ) -> HubScore:
        """
        Calculate comprehensive hub potential score.

        Scoring factors:
        - Connectivity: Number of reachable airports within range
        - Geographic centrality: Distance from population/traffic centers
        - Infrastructure: Airport size and facilities
        - Regional coverage: Fills gaps in network

        Args:
            airport: Airport to score
            all_airports: Optional list of all airports (for efficiency)

        Returns:
            HubScore with detailed breakdown
        """
        if all_airports is None:
            all_airports = self.get_eligible_airports()

        factors = {}

        # 1. Connectivity Score (40 points)
        nearby = airports_within_radius(
            airport.latitude_deg,
            airport.longitude_deg,
            self.max_connection_range_km,
            unit="km"
        )

        # Filter to eligible airports only
        eligible_set = {a.ident for a in all_airports}
        nearby_eligible = [a for a in nearby if a.ident in eligible_set and a.ident != airport.ident]

        connectivity_raw = len(nearby_eligible)
        # Normalize: assume 100+ connections = max score
        connectivity_score = min(40.0, (connectivity_raw / 100.0) * 40.0)
        factors['connectivity'] = connectivity_score
        factors['reachable_airports'] = connectivity_raw

        # 2. Geographic Centrality Score (30 points)
        # Calculate average distance to all other airports
        # Lower average distance = more central = higher score
        if len(all_airports) > 1:
            total_distance = 0.0
            count = 0

            # Sample for performance (use up to 200 airports)
            sample_size = min(200, len(all_airports))
            sample_step = max(1, len(all_airports) // sample_size)

            for i in range(0, len(all_airports), sample_step):
                other = all_airports[i]
                if other.ident == airport.ident:
                    continue

                dist = distance(
                    airport.latitude_deg, airport.longitude_deg,
                    other.latitude_deg, other.longitude_deg,
                    unit="km"
                )
                total_distance += dist
                count += 1

            avg_distance = total_distance / count if count > 0 else 0

            # Lower avg distance = higher score
            # Assume 5000km avg = lowest score, 1000km = highest
            geographic_score = max(0, min(30.0, 30.0 * (1 - (avg_distance - 1000) / 4000)))
            factors['avg_distance_km'] = avg_distance
        else:
            geographic_score = 15.0
            factors['avg_distance_km'] = 0

        factors['geographic_centrality'] = geographic_score

        # 3. Infrastructure Score (20 points)
        size_scores = {
            "large_airport": 20.0,
            "medium_airport": 12.0,
            "small_airport": 5.0
        }
        infrastructure_score = size_scores.get(airport.type, 0.0)
        factors['infrastructure'] = infrastructure_score

        # 4. Regional Coverage Score (10 points)
        # Check if this airport serves an underserved region
        # Find nearest neighbors
        nearest = nearest_airports(
            airport.latitude_deg,
            airport.longitude_deg,
            limit=5
        )

        # Filter out self and get eligible only
        nearest_eligible = [
            a for a in nearest
            if a.ident != airport.ident and a.ident in eligible_set
        ]

        if nearest_eligible:
            # Calculate distance to nearest eligible airport
            nearest_dist = distance(
                airport.latitude_deg, airport.longitude_deg,
                nearest_eligible[0].latitude_deg, nearest_eligible[0].longitude_deg,
                unit="km"
            )

            # If nearest airport is far, this fills a coverage gap
            # 500km+ = max score
            coverage_score = min(10.0, (nearest_dist / 500.0) * 10.0)
        else:
            coverage_score = 10.0  # Only airport = max coverage score

        factors['coverage'] = coverage_score

        # Calculate total
        total_score = (
            connectivity_score +
            geographic_score +
            infrastructure_score +
            coverage_score
        )

        return HubScore(
            airport=airport,
            hub_score=total_score,
            connectivity_score=connectivity_score,
            geographic_score=geographic_score,
            infrastructure_score=infrastructure_score,
            factors=factors
        )

    def identify_hubs(
        self,
        top_n: int = 20,
        min_score: float = 50.0,
        region: Optional[str] = None
    ) -> List[HubScore]:
        """
        Identify top hub airports.

        Args:
            top_n: Number of top hubs to return
            min_score: Minimum hub score threshold
            region: Optional region filter (continent or country code)

        Returns:
            List of HubScore objects, sorted by score (descending)
        """
        airports = self.get_eligible_airports()

        # Apply region filter if specified
        if region:
            region_upper = region.upper()
            airports = [
                a for a in airports
                if (a.continent == region_upper or
                    a.iso_country == region_upper or
                    a.iso_region == region_upper)
            ]

        logger.info(f"Scoring {len(airports)} airports for hub potential...")

        scores = []
        for i, airport in enumerate(airports):
            if i % 100 == 0 and i > 0:
                logger.debug(f"Scored {i}/{len(airports)} airports")

            score = self.calculate_hub_score(airport, airports)

            if score.hub_score >= min_score:
                scores.append(score)

        # Sort by hub score (descending)
        scores.sort(key=lambda x: x.hub_score, reverse=True)

        logger.info(f"Identified {len(scores)} airports above threshold {min_score}")

        return scores[:top_n]

    def calculate_network_metrics(
        self,
        region: Optional[str] = None
    ) -> NetworkMetrics:
        """
        Calculate comprehensive network metrics.

        Args:
            region: Optional region filter

        Returns:
            NetworkMetrics object
        """
        airports = self.get_eligible_airports()

        if region:
            region_upper = region.upper()
            airports = [
                a for a in airports
                if (a.continent == region_upper or
                    a.iso_country == region_upper)
            ]

        logger.info(f"Calculating network metrics for {len(airports)} airports...")

        # Calculate potential connections
        total_connections = 0
        connection_counts = []

        for airport in airports:
            nearby = airports_within_radius(
                airport.latitude_deg,
                airport.longitude_deg,
                self.max_connection_range_km,
                unit="km"
            )

            # Count eligible airports only (excluding self)
            eligible_set = {a.ident for a in airports}
            nearby_count = sum(
                1 for a in nearby
                if a.ident in eligible_set and a.ident != airport.ident
            )

            total_connections += nearby_count
            connection_counts.append(nearby_count)

        # Network density: actual connections / possible connections
        max_possible = len(airports) * (len(airports) - 1) / 2
        density = total_connections / max_possible if max_possible > 0 else 0

        # Average connectivity
        avg_connectivity = sum(connection_counts) / len(connection_counts) if connection_counts else 0

        # Identify top hubs
        top_hubs = self.identify_hubs(top_n=10, min_score=0)

        # Find coverage gaps (simplified: grid-based approach)
        coverage_gaps = self._find_coverage_gaps(airports)

        return NetworkMetrics(
            total_airports=len(airports),
            potential_connections=total_connections,
            average_connectivity=avg_connectivity,
            network_density=density,
            top_hubs=top_hubs,
            coverage_gaps=coverage_gaps
        )

    def _find_coverage_gaps(
        self,
        airports: List[Airport],
        grid_resolution: int = 10
    ) -> List[Tuple[float, float]]:
        """
        Find underserved regions using grid-based analysis.

        Args:
            airports: List of airports
            grid_resolution: Grid resolution (NxN)

        Returns:
            List of (lat, lon) coordinates for coverage gaps
        """
        # Create a simple grid covering the world
        gaps = []

        # Focus on inhabited regions: -60 to 80 latitude
        lat_step = 140 / grid_resolution
        lon_step = 360 / grid_resolution

        for i in range(grid_resolution):
            lat = -60 + i * lat_step

            for j in range(grid_resolution):
                lon = -180 + j * lon_step

                # Find nearest airport to this grid point
                min_distance = float('inf')

                for airport in airports:
                    dist = distance(
                        lat, lon,
                        airport.latitude_deg, airport.longitude_deg,
                        unit="km"
                    )

                    if dist < min_distance:
                        min_distance = dist

                # If nearest airport is > 500km away, this is a gap
                if min_distance > 500:
                    gaps.append((lat, lon))

        return gaps

    def suggest_new_hub(
        self,
        region: Optional[str] = None,
        avoid_existing_hubs_km: float = 300.0
    ) -> Optional[Tuple[float, float, str]]:
        """
        Suggest location for a new hub airport.

        Args:
            region: Target region
            avoid_existing_hubs_km: Minimum distance from existing hubs

        Returns:
            (latitude, longitude, reason) or None
        """
        airports = self.get_eligible_airports()

        if region:
            region_upper = region.upper()
            airports = [
                a for a in airports
                if (a.continent == region_upper or a.iso_country == region_upper)
            ]

        # Find coverage gaps
        gaps = self._find_coverage_gaps(airports, grid_resolution=20)

        if not gaps:
            return None

        # Score each gap location
        best_gap = None
        best_score = -1

        for lat, lon in gaps:
            # Count airports within range
            nearby = airports_within_radius(lat, lon, self.max_connection_range_km, unit="km")

            # Check distance from existing hubs
            too_close_to_hub = False
            for airport in nearby:
                if airport.type == "large_airport":
                    dist = distance(lat, lon, airport.latitude_deg, airport.longitude_deg, unit="km")
                    if dist < avoid_existing_hubs_km:
                        too_close_to_hub = True
                        break

            if too_close_to_hub:
                continue

            # Score: high connectivity potential + far from existing hubs
            score = len(nearby)

            if score > best_score:
                best_score = score
                best_gap = (lat, lon)

        if best_gap:
            reason = f"Serves {best_score} airports, fills coverage gap"
            return (best_gap[0], best_gap[1], reason)

        return None


# Convenience functions
def identify_global_hubs(top_n: int = 20, min_score: float = 50.0) -> List[HubScore]:
    """
    Identify top global hub airports.

    Args:
        top_n: Number of hubs to return
        min_score: Minimum hub score

    Returns:
        List of HubScore objects
    """
    engine = NetworkIntelligence()
    return engine.identify_hubs(top_n=top_n, min_score=min_score)


def identify_regional_hubs(
    region: str,
    top_n: int = 10,
    min_score: float = 40.0
) -> List[HubScore]:
    """
    Identify top regional hub airports.

    Args:
        region: Region code (continent or country)
        top_n: Number of hubs to return
        min_score: Minimum hub score

    Returns:
        List of HubScore objects
    """
    engine = NetworkIntelligence()
    return engine.identify_hubs(top_n=top_n, min_score=min_score, region=region)


def calculate_global_network_metrics() -> NetworkMetrics:
    """
    Calculate global aviation network metrics.

    Returns:
        NetworkMetrics object
    """
    engine = NetworkIntelligence()
    return engine.calculate_network_metrics()


def calculate_regional_network_metrics(region: str) -> NetworkMetrics:
    """
    Calculate regional aviation network metrics.

    Args:
        region: Region code (continent or country)

    Returns:
        NetworkMetrics object
    """
    engine = NetworkIntelligence()
    return engine.calculate_network_metrics(region=region)
