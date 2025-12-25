"""
AeroNavX Emissions Calculator v2.0

Advanced emissions calculations with:
- Aircraft-specific fuel consumption
- Load factor optimization
- Sustainable Aviation Fuel (SAF) support
- Radiative forcing for high-altitude emissions
- NOx, contrails, and other pollutants
- Carbon offsetting calculations
- Multi-modal transport comparison
"""

from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.airport import Airport
from ..core.distance import distance
from ..utils.logging import get_logger

logger = get_logger()


class AircraftType(Enum):
    """Common aircraft types with emission profiles."""
    # Narrow-body
    A320 = "A320"
    A321 = "A321"
    B737_800 = "B737-800"
    B737_MAX = "B737-MAX"

    # Wide-body
    A350_900 = "A350-900"
    B777_300ER = "B777-300ER"
    B787_9 = "B787-9"
    A380 = "A380"

    # Regional
    E175 = "E175"
    CRJ900 = "CRJ900"
    ATR72 = "ATR72"

    # Private
    G650 = "G650"
    FALCON_7X = "Falcon 7X"


class FuelType(Enum):
    """Fuel types with carbon intensities."""
    JET_A1 = "Jet A-1"  # Standard aviation fuel
    SAF_HEFA = "SAF-HEFA"  # Sustainable Aviation Fuel - HEFA
    SAF_FT = "SAF-FT"  # Fischer-Tropsch SAF
    BLENDED_30 = "30% SAF Blend"  # 30% SAF + 70% Jet A-1


@dataclass
class AircraftEmissionProfile:
    """Emission profile for specific aircraft type."""
    aircraft_type: AircraftType
    fuel_burn_kg_per_km: float  # Per aircraft-km
    typical_seats: int
    typical_load_factor: float  # 0-1
    nox_index_g_per_kg_fuel: float  # NOx emissions index
    max_range_km: float

    def get_fuel_per_pax_km(self, load_factor: Optional[float] = None) -> float:
        """Calculate fuel per passenger-km."""
        lf = load_factor or self.typical_load_factor
        passengers = self.typical_seats * lf
        if passengers == 0:
            return 0
        return self.fuel_burn_kg_per_km / passengers


@dataclass
class FuelEmissionFactor:
    """Emission factors for fuel types."""
    fuel_type: FuelType
    co2_kg_per_kg_fuel: float  # Direct CO2 from combustion
    lifecycle_co2_kg_per_kg_fuel: float  # Including production
    radiative_forcing_multiplier: float  # For high-altitude effects
    soot_reduction: float  # 0-1, compared to Jet A-1


# Aircraft emission profiles database
AIRCRAFT_PROFILES = {
    AircraftType.A320: AircraftEmissionProfile(
        aircraft_type=AircraftType.A320,
        fuel_burn_kg_per_km=2.5,
        typical_seats=180,
        typical_load_factor=0.82,
        nox_index_g_per_kg_fuel=12.0,
        max_range_km=6100
    ),
    AircraftType.A321: AircraftEmissionProfile(
        aircraft_type=AircraftType.A321,
        fuel_burn_kg_per_km=2.8,
        typical_seats=220,
        typical_load_factor=0.83,
        nox_index_g_per_kg_fuel=12.5,
        max_range_km=7400
    ),
    AircraftType.B737_800: AircraftEmissionProfile(
        aircraft_type=AircraftType.B737_800,
        fuel_burn_kg_per_km=2.6,
        typical_seats=189,
        typical_load_factor=0.81,
        nox_index_g_per_kg_fuel=11.8,
        max_range_km=5765
    ),
    AircraftType.B737_MAX: AircraftEmissionProfile(
        aircraft_type=AircraftType.B737_MAX,
        fuel_burn_kg_per_km=2.3,  # 14% more efficient
        typical_seats=189,
        typical_load_factor=0.81,
        nox_index_g_per_kg_fuel=11.0,
        max_range_km=6570
    ),
    AircraftType.A350_900: AircraftEmissionProfile(
        aircraft_type=AircraftType.A350_900,
        fuel_burn_kg_per_km=6.2,
        typical_seats=325,
        typical_load_factor=0.85,
        nox_index_g_per_kg_fuel=10.5,
        max_range_km=15000
    ),
    AircraftType.B777_300ER: AircraftEmissionProfile(
        aircraft_type=AircraftType.B777_300ER,
        fuel_burn_kg_per_km=7.8,
        typical_seats=396,
        typical_load_factor=0.84,
        nox_index_g_per_kg_fuel=13.0,
        max_range_km=13649
    ),
    AircraftType.B787_9: AircraftEmissionProfile(
        aircraft_type=AircraftType.B787_9,
        fuel_burn_kg_per_km=5.5,
        typical_seats=290,
        typical_load_factor=0.86,
        nox_index_g_per_kg_fuel=10.0,
        max_range_km=14140
    ),
    AircraftType.A380: AircraftEmissionProfile(
        aircraft_type=AircraftType.A380,
        fuel_burn_kg_per_km=12.0,
        typical_seats=555,
        typical_load_factor=0.80,
        nox_index_g_per_kg_fuel=14.0,
        max_range_km=15200
    ),
    AircraftType.E175: AircraftEmissionProfile(
        aircraft_type=AircraftType.E175,
        fuel_burn_kg_per_km=1.4,
        typical_seats=88,
        typical_load_factor=0.75,
        nox_index_g_per_kg_fuel=11.5,
        max_range_km=3704
    ),
    AircraftType.CRJ900: AircraftEmissionProfile(
        aircraft_type=AircraftType.CRJ900,
        fuel_burn_kg_per_km=1.5,
        typical_seats=90,
        typical_load_factor=0.73,
        nox_index_g_per_kg_fuel=12.0,
        max_range_km=2956
    ),
    AircraftType.G650: AircraftEmissionProfile(
        aircraft_type=AircraftType.G650,
        fuel_burn_kg_per_km=3.8,
        typical_seats=19,
        typical_load_factor=0.60,
        nox_index_g_per_kg_fuel=15.0,
        max_range_km=13000
    )
}

# Fuel emission factors
FUEL_FACTORS = {
    FuelType.JET_A1: FuelEmissionFactor(
        fuel_type=FuelType.JET_A1,
        co2_kg_per_kg_fuel=3.16,  # Standard kerosene
        lifecycle_co2_kg_per_kg_fuel=3.55,  # Including extraction/refining
        radiative_forcing_multiplier=1.9,  # IPCC estimate
        soot_reduction=0.0
    ),
    FuelType.SAF_HEFA: FuelEmissionFactor(
        fuel_type=FuelType.SAF_HEFA,
        co2_kg_per_kg_fuel=3.16,  # Same combustion
        lifecycle_co2_kg_per_kg_fuel=0.60,  # 83% reduction lifecycle
        radiative_forcing_multiplier=1.7,  # Reduced contrails
        soot_reduction=0.50
    ),
    FuelType.SAF_FT: FuelEmissionFactor(
        fuel_type=FuelType.SAF_FT,
        co2_kg_per_kg_fuel=3.16,
        lifecycle_co2_kg_per_kg_fuel=0.40,  # 89% reduction
        radiative_forcing_multiplier=1.6,
        soot_reduction=0.70
    ),
    FuelType.BLENDED_30: FuelEmissionFactor(
        fuel_type=FuelType.BLENDED_30,
        co2_kg_per_kg_fuel=3.16,
        lifecycle_co2_kg_per_kg_fuel=2.66,  # 25% reduction
        radiative_forcing_multiplier=1.85,
        soot_reduction=0.15
    )
}


@dataclass
class EmissionReport:
    """Comprehensive emission report."""
    distance_km: float
    aircraft_type: AircraftType
    fuel_type: FuelType
    passengers: int
    load_factor: float

    # Fuel consumption
    total_fuel_kg: float
    fuel_per_pax_kg: float

    # CO2 emissions
    direct_co2_kg: float  # From combustion
    lifecycle_co2_kg: float  # Including production
    co2_with_rf_kg: float  # Including radiative forcing
    co2_per_pax_kg: float

    # Other pollutants
    nox_kg: float
    soot_kg: float

    # Comparison
    alternative_train_co2_kg: Optional[float] = None
    co2_reduction_vs_conventional_pct: Optional[float] = None

    def get_carbon_offset_cost_usd(self, price_per_ton: float = 15.0) -> float:
        """Calculate carbon offset cost."""
        tons = self.co2_with_rf_kg / 1000.0
        return tons * price_per_ton

    def __repr__(self):
        return (
            f"EmissionReport({self.aircraft_type.value}: "
            f"{self.co2_per_pax_kg:.1f} kg CO2/pax for {self.distance_km:.0f}km)"
        )


class EmissionsCalculatorV2:
    """
    Advanced emissions calculator with aircraft-specific data.

    Features:
    - 10+ aircraft type profiles
    - Multiple fuel types including SAF
    - Load factor optimization
    - Radiative forcing
    - NOx and contrails
    - Multi-modal comparison
    """

    def __init__(self):
        """Initialize emissions calculator."""
        self.aircraft_profiles = AIRCRAFT_PROFILES
        self.fuel_factors = FUEL_FACTORS

    def calculate(
        self,
        origin: Airport,
        destination: Airport,
        aircraft_type: AircraftType = AircraftType.A320,
        fuel_type: FuelType = FuelType.JET_A1,
        load_factor: Optional[float] = None,
        include_radiative_forcing: bool = True
    ) -> EmissionReport:
        """
        Calculate comprehensive emissions for a flight.

        Args:
            origin: Origin airport
            destination: Destination airport
            aircraft_type: Aircraft type
            fuel_type: Fuel type
            load_factor: Override default load factor (0-1)
            include_radiative_forcing: Include high-altitude effects

        Returns:
            EmissionReport with detailed breakdown
        """
        # Get aircraft profile
        profile = self.aircraft_profiles[aircraft_type]
        fuel_factor = self.fuel_factors[fuel_type]

        # Calculate distance
        dist_km = distance(
            origin.latitude_deg, origin.longitude_deg,
            destination.latitude_deg, destination.longitude_deg,
            unit="km"
        )

        # Determine load factor
        lf = load_factor if load_factor is not None else profile.typical_load_factor
        passengers = int(profile.typical_seats * lf)

        # Calculate fuel consumption
        total_fuel_kg = profile.fuel_burn_kg_per_km * dist_km
        fuel_per_pax_kg = total_fuel_kg / passengers if passengers > 0 else 0

        # Direct CO2 emissions
        direct_co2_kg = total_fuel_kg * fuel_factor.co2_kg_per_kg_fuel

        # Lifecycle CO2 (including production)
        lifecycle_co2_kg = total_fuel_kg * fuel_factor.lifecycle_co2_kg_per_kg_fuel

        # Apply radiative forcing if requested
        if include_radiative_forcing:
            co2_with_rf_kg = lifecycle_co2_kg * fuel_factor.radiative_forcing_multiplier
        else:
            co2_with_rf_kg = lifecycle_co2_kg

        co2_per_pax_kg = co2_with_rf_kg / passengers if passengers > 0 else 0

        # NOx emissions
        nox_kg = total_fuel_kg * (profile.nox_index_g_per_kg_fuel / 1000.0)

        # Soot (simplified estimate)
        base_soot_kg = total_fuel_kg * 0.0001  # ~0.01% of fuel mass
        soot_kg = base_soot_kg * (1 - fuel_factor.soot_reduction)

        # Compare to train (if distance < 1500km)
        train_co2 = None
        if dist_km < 1500:
            # Average train: 14g CO2/pax-km (electric), 41g (diesel)
            # Use 25g as mixed average
            train_co2 = dist_km * 0.025  # kg per passenger

        # Calculate reduction vs conventional fuel
        co2_reduction_pct = None
        if fuel_type != FuelType.JET_A1:
            conventional_lifecycle = total_fuel_kg * FUEL_FACTORS[FuelType.JET_A1].lifecycle_co2_kg_per_kg_fuel
            if include_radiative_forcing:
                conventional_lifecycle *= FUEL_FACTORS[FuelType.JET_A1].radiative_forcing_multiplier
            co2_reduction_pct = ((conventional_lifecycle - co2_with_rf_kg) / conventional_lifecycle) * 100

        return EmissionReport(
            distance_km=dist_km,
            aircraft_type=aircraft_type,
            fuel_type=fuel_type,
            passengers=passengers,
            load_factor=lf,
            total_fuel_kg=total_fuel_kg,
            fuel_per_pax_kg=fuel_per_pax_kg,
            direct_co2_kg=direct_co2_kg,
            lifecycle_co2_kg=lifecycle_co2_kg,
            co2_with_rf_kg=co2_with_rf_kg,
            co2_per_pax_kg=co2_per_pax_kg,
            nox_kg=nox_kg,
            soot_kg=soot_kg,
            alternative_train_co2_kg=train_co2,
            co2_reduction_vs_conventional_pct=co2_reduction_pct
        )

    def compare_aircraft(
        self,
        origin: Airport,
        destination: Airport,
        aircraft_types: Optional[List[AircraftType]] = None
    ) -> List[EmissionReport]:
        """
        Compare emissions across different aircraft types.

        Args:
            origin: Origin airport
            destination: Destination airport
            aircraft_types: List of aircraft to compare (or common types)

        Returns:
            List of EmissionReports, sorted by CO2/pax (ascending)
        """
        if aircraft_types is None:
            # Compare common narrow-body and wide-body
            aircraft_types = [
                AircraftType.A320,
                AircraftType.B737_800,
                AircraftType.B737_MAX,
                AircraftType.A350_900,
                AircraftType.B787_9
            ]

        reports = []

        for aircraft in aircraft_types:
            try:
                report = self.calculate(origin, destination, aircraft_type=aircraft)
                reports.append(report)
            except Exception as e:
                logger.warning(f"Failed to calculate for {aircraft}: {e}")

        # Sort by CO2 per passenger
        reports.sort(key=lambda r: r.co2_per_pax_kg)

        return reports

    def compare_fuels(
        self,
        origin: Airport,
        destination: Airport,
        aircraft_type: AircraftType = AircraftType.A320
    ) -> List[EmissionReport]:
        """
        Compare different fuel types for the same route.

        Args:
            origin: Origin airport
            destination: Destination airport
            aircraft_type: Aircraft type to use

        Returns:
            List of EmissionReports for different fuels
        """
        fuel_types = [
            FuelType.JET_A1,
            FuelType.BLENDED_30,
            FuelType.SAF_HEFA,
            FuelType.SAF_FT
        ]

        reports = []

        for fuel in fuel_types:
            report = self.calculate(origin, destination, aircraft_type=aircraft_type, fuel_type=fuel)
            reports.append(report)

        return reports

    def optimize_load_factor(
        self,
        origin: Airport,
        destination: Airport,
        aircraft_type: AircraftType = AircraftType.A320,
        target_emissions_per_pax_kg: float = 100.0
    ) -> Tuple[float, EmissionReport]:
        """
        Find optimal load factor to meet emission targets.

        Args:
            origin: Origin airport
            destination: Destination airport
            aircraft_type: Aircraft type
            target_emissions_per_pax_kg: Target CO2/pax

        Returns:
            (optimal_load_factor, EmissionReport)
        """
        # Binary search for optimal load factor
        low, high = 0.5, 1.0
        best_lf = low
        best_report = None

        for _ in range(10):  # 10 iterations for convergence
            mid = (low + high) / 2
            report = self.calculate(origin, destination, aircraft_type=aircraft_type, load_factor=mid)

            if report.co2_per_pax_kg > target_emissions_per_pax_kg:
                # Need higher load factor
                low = mid
            else:
                high = mid

            best_lf = mid
            best_report = report

            # Check convergence
            if abs(high - low) < 0.01:
                break

        return best_lf, best_report


# Convenience functions
def calculate_flight_emissions(
    origin: Airport,
    destination: Airport,
    aircraft: str = "A320",
    fuel: str = "Jet A-1"
) -> EmissionReport:
    """
    Calculate flight emissions (convenience function).

    Args:
        origin: Origin airport
        destination: Destination airport
        aircraft: Aircraft type name
        fuel: Fuel type name

    Returns:
        EmissionReport
    """
    # Map string to enum
    aircraft_map = {a.value: a for a in AircraftType}
    fuel_map = {f.value: f for f in FuelType}

    aircraft_type = aircraft_map.get(aircraft, AircraftType.A320)
    fuel_type = fuel_map.get(fuel, FuelType.JET_A1)

    calc = EmissionsCalculatorV2()
    return calc.calculate(origin, destination, aircraft_type=aircraft_type, fuel_type=fuel_type)


def compare_saf_savings(
    origin: Airport,
    destination: Airport,
    aircraft: str = "A320"
) -> Dict[str, float]:
    """
    Compare SAF savings vs conventional fuel.

    Returns:
        Dict with CO2 reduction percentages for each SAF type
    """
    aircraft_map = {a.value: a for a in AircraftType}
    aircraft_type = aircraft_map.get(aircraft, AircraftType.A320)

    calc = EmissionsCalculatorV2()
    reports = calc.compare_fuels(origin, destination, aircraft_type=aircraft_type)

    savings = {}
    for report in reports:
        if report.co2_reduction_vs_conventional_pct is not None:
            savings[report.fuel_type.value] = report.co2_reduction_vs_conventional_pct

    return savings
