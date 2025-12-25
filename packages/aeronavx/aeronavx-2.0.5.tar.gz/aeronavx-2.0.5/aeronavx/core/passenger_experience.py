"""
AeroNavX Passenger Experience Layer v2.0

Passenger-focused analytics:
- Jet lag severity and recovery estimation
- Timezone crossing analysis
- Flight fatigue calculation
- Optimal departure time recommendations
- Recovery strategies
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import math

from ..models.airport import Airport
from ..core.distance import distance
from ..core.routing import estimate_flight_time_hours
from ..core.timezone import get_timezone_offset
from ..utils.logging import get_logger

logger = get_logger()


class FlightDirection(Enum):
    """Flight direction for jet lag calculation."""
    EASTBOUND = "eastbound"  # Harder to adjust
    WESTBOUND = "westbound"  # Easier to adjust
    NORTHBOUND = "northbound"  # Minimal jet lag
    SOUTHBOUND = "southbound"  # Minimal jet lag


class JetLagSeverity(Enum):
    """Jet lag severity levels."""
    NONE = "none"  # < 2 hours difference
    MILD = "mild"  # 2-4 hours
    MODERATE = "moderate"  # 4-6 hours
    SEVERE = "severe"  # 6-8 hours
    EXTREME = "extreme"  # > 8 hours


@dataclass
class JetLagReport:
    """Comprehensive jet lag analysis."""
    origin: Airport
    destination: Airport
    timezone_difference_hours: float
    direction: FlightDirection
    severity: JetLagSeverity
    estimated_recovery_days: float
    symptoms_peak_day: int
    recommendations: List[str]
    optimal_departure_times: List[int]  # Hours (0-23) for departure

    def __repr__(self):
        return (
            f"JetLagReport({self.severity.value}: "
            f"{abs(self.timezone_difference_hours):.1f}h shift, "
            f"{self.estimated_recovery_days:.1f} days recovery)"
        )


@dataclass
class FatigueReport:
    """Flight fatigue analysis."""
    flight_duration_hours: float
    departure_time_hour: int  # 0-23
    arrival_time_hour: int  # 0-23
    fatigue_score: float  # 0-100 (higher = more fatigue)
    red_eye_flight: bool
    crossing_midnight: bool
    recommendations: List[str]

    def __repr__(self):
        return f"FatigueReport(score: {self.fatigue_score:.0f}/100, red-eye: {self.red_eye_flight})"


class PassengerExperience:
    """
    Analyze passenger experience factors.

    Features:
    - Jet lag severity calculation
    - Recovery time estimation
    - Optimal departure time suggestions
    - Flight fatigue analysis
    - Personalized recommendations
    """

    def __init__(self):
        """Initialize passenger experience analyzer."""
        pass

    def calculate_jet_lag(
        self,
        origin: Airport,
        destination: Airport,
        passenger_age: int = 35,
        frequent_traveler: bool = False
    ) -> JetLagReport:
        """
        Calculate comprehensive jet lag report.

        Based on research:
        - Eastbound travel is harder (need to wake earlier)
        - Rule of thumb: 1 day recovery per 1-2 hour time difference
        - Age affects recovery speed
        - Direction matters more than distance

        Args:
            origin: Origin airport
            destination: Destination airport
            passenger_age: Passenger age (affects recovery)
            frequent_traveler: If true, adapts faster

        Returns:
            JetLagReport with detailed analysis
        """
        # Get timezone offsets
        origin_tz = get_timezone_offset(origin.latitude_deg, origin.longitude_deg)
        dest_tz = get_timezone_offset(destination.latitude_deg, destination.longitude_deg)

        # Calculate timezone difference
        tz_diff = dest_tz - origin_tz

        # Normalize to -12 to +12 hours
        if tz_diff > 12:
            tz_diff -= 24
        elif tz_diff < -12:
            tz_diff += 24

        # Determine direction
        if abs(tz_diff) < 1:
            direction = FlightDirection.NORTHBOUND  # Effectively no E-W movement
        elif tz_diff > 0:
            direction = FlightDirection.EASTBOUND
        else:
            direction = FlightDirection.WESTBOUND

        # Calculate severity
        abs_diff = abs(tz_diff)

        if abs_diff < 2:
            severity = JetLagSeverity.NONE
        elif abs_diff < 4:
            severity = JetLagSeverity.MILD
        elif abs_diff < 6:
            severity = JetLagSeverity.MODERATE
        elif abs_diff < 8:
            severity = JetLagSeverity.SEVERE
        else:
            severity = JetLagSeverity.EXTREME

        # Calculate recovery time
        # Base: 1 day per 2 hours time difference
        base_recovery_days = abs_diff / 2.0

        # Eastbound penalty (25% harder)
        if direction == FlightDirection.EASTBOUND:
            base_recovery_days *= 1.25

        # Age factor (older = slower recovery)
        if passenger_age > 50:
            base_recovery_days *= 1.3
        elif passenger_age < 25:
            base_recovery_days *= 0.8

        # Frequent traveler bonus
        if frequent_traveler:
            base_recovery_days *= 0.7

        # Symptoms typically peak on day 2-3
        symptoms_peak = min(3, int(base_recovery_days / 2) + 1)

        # Generate recommendations
        recommendations = self._generate_jet_lag_recommendations(
            tz_diff, direction, severity, base_recovery_days
        )

        # Optimal departure times
        optimal_times = self._calculate_optimal_departure_times(tz_diff, direction)

        return JetLagReport(
            origin=origin,
            destination=destination,
            timezone_difference_hours=tz_diff,
            direction=direction,
            severity=severity,
            estimated_recovery_days=base_recovery_days,
            symptoms_peak_day=symptoms_peak,
            recommendations=recommendations,
            optimal_departure_times=optimal_times
        )

    def _generate_jet_lag_recommendations(
        self,
        tz_diff: float,
        direction: FlightDirection,
        severity: JetLagSeverity,
        recovery_days: float
    ) -> List[str]:
        """Generate personalized jet lag recommendations."""
        recommendations = []

        if severity == JetLagSeverity.NONE:
            recommendations.append("No significant jet lag expected")
            return recommendations

        # Pre-flight
        if abs(tz_diff) >= 3:
            if direction == FlightDirection.EASTBOUND:
                recommendations.append(
                    "Pre-adjust: Go to bed 30-60 min earlier for 2-3 days before departure"
                )
            else:
                recommendations.append(
                    "Pre-adjust: Go to bed 30-60 min later for 2-3 days before departure"
                )

        # During flight
        recommendations.append("Stay hydrated: Drink water every hour during flight")
        recommendations.append("Avoid alcohol and caffeine during flight")

        if abs(tz_diff) >= 4:
            recommendations.append(
                "Sleep strategy: Try to sleep according to destination timezone"
            )

        # Post-arrival
        recommendations.append(
            f"Expect symptoms to peak around day {int(recovery_days / 2) + 1}"
        )

        recommendations.append("Get sunlight exposure in the morning at destination")

        if direction == FlightDirection.EASTBOUND:
            recommendations.append(
                "Eastbound travel: Use bright light in the morning, avoid evening light"
            )
        else:
            recommendations.append(
                "Westbound travel: Use bright light in the evening to delay sleep"
            )

        # Melatonin suggestion for severe jet lag
        if severity in [JetLagSeverity.SEVERE, JetLagSeverity.EXTREME]:
            recommendations.append(
                "Consider melatonin supplement (0.5-3mg) 30 min before target bedtime"
            )

        # Recovery timeline
        if recovery_days > 3:
            recommendations.append(
                f"Full recovery expected in {recovery_days:.0f} days - avoid important "
                "meetings on arrival day if possible"
            )

        return recommendations

    def _calculate_optimal_departure_times(
        self,
        tz_diff: float,
        direction: FlightDirection
    ) -> List[int]:
        """Calculate optimal departure times to minimize jet lag."""
        optimal = []

        if abs(tz_diff) < 2:
            # No significant jet lag - any time is fine
            return [9, 14, 19]  # Morning, afternoon, evening

        if direction == FlightDirection.EASTBOUND:
            # Eastbound: Prefer evening departures
            # Arrive in morning at destination = easier to adjust
            optimal = [18, 20, 22]

        elif direction == FlightDirection.WESTBOUND:
            # Westbound: Prefer morning/early afternoon departures
            # Arrive in evening at destination
            optimal = [8, 10, 13]

        else:
            # North-south: Minimal jet lag
            optimal = [9, 14, 19]

        return optimal

    def calculate_flight_fatigue(
        self,
        origin: Airport,
        destination: Airport,
        departure_time_hour: int,
        include_ground_time: bool = True
    ) -> FatigueReport:
        """
        Calculate flight fatigue score.

        Factors:
        - Flight duration
        - Departure time (red-eye flights worse)
        - Crossing midnight
        - Airport transit time

        Args:
            origin: Origin airport
            destination: Destination airport
            departure_time_hour: Departure hour (0-23)
            include_ground_time: Add airport/transit time

        Returns:
            FatigueReport
        """
        # Calculate flight time
        flight_hours = estimate_flight_time_hours(origin, destination)

        # Add ground time if requested
        total_hours = flight_hours
        if include_ground_time:
            # Assume 2 hours before + 1 hour after
            total_hours += 3

        # Calculate arrival time
        arrival_time_hour = (departure_time_hour + int(total_hours)) % 24

        # Base fatigue from duration
        # Long-haul flights (>8h) significantly more fatiguing
        if total_hours < 3:
            duration_fatigue = 20
        elif total_hours < 6:
            duration_fatigue = 35
        elif total_hours < 10:
            duration_fatigue = 55
        else:
            # Very long flights
            duration_fatigue = 70 + min(20, (total_hours - 10) * 2)

        # Departure time penalty
        # Red-eye flights (22:00 - 05:00 departure) are worst
        time_penalty = 0
        red_eye = False

        if 22 <= departure_time_hour or departure_time_hour <= 5:
            time_penalty = 25
            red_eye = True
        elif 6 <= departure_time_hour <= 8:
            time_penalty = 10  # Early morning - some disruption
        elif 18 <= departure_time_hour <= 21:
            time_penalty = 5  # Evening - minor disruption

        # Check if crossing midnight
        crossing_midnight = False
        if departure_time_hour > arrival_time_hour or flight_hours >= 24:
            crossing_midnight = True
            time_penalty += 10

        # Calculate total fatigue score
        fatigue_score = min(100, duration_fatigue + time_penalty)

        # Generate recommendations
        recommendations = []

        if fatigue_score > 70:
            recommendations.append("High fatigue expected - plan recovery time")
            recommendations.append("Avoid scheduling important activities on arrival day")

        if red_eye:
            recommendations.append("Red-eye flight - try to sleep on the plane")
            recommendations.append("Consider overnight layover if possible")

        if flight_hours > 10:
            recommendations.append("Long-haul flight - walk every 2-3 hours")
            recommendations.append("Do in-seat exercises to prevent DVT")

        if crossing_midnight:
            recommendations.append("Flight crosses midnight - bring sleep aids (eye mask, earplugs)")

        if fatigue_score < 40:
            recommendations.append("Moderate fatigue expected - manageable with rest")

        return FatigueReport(
            flight_duration_hours=flight_hours,
            departure_time_hour=departure_time_hour,
            arrival_time_hour=arrival_time_hour,
            fatigue_score=fatigue_score,
            red_eye_flight=red_eye,
            crossing_midnight=crossing_midnight,
            recommendations=recommendations
        )

    def recommend_best_departure_time(
        self,
        origin: Airport,
        destination: Airport,
        passenger_age: int = 35
    ) -> Tuple[int, str]:
        """
        Recommend best departure time considering both jet lag and fatigue.

        Args:
            origin: Origin airport
            destination: Destination airport
            passenger_age: Passenger age

        Returns:
            (best_hour, reason)
        """
        # Get jet lag analysis
        jet_lag = self.calculate_jet_lag(origin, destination, passenger_age=passenger_age)

        # Score each potential departure time
        best_score = -1
        best_hour = 9
        best_reason = ""

        for hour in range(24):
            # Calculate fatigue
            fatigue = self.calculate_flight_fatigue(origin, destination, hour)

            # Combined score (lower is better)
            # Weight: 60% jet lag recovery, 40% fatigue
            score = (
                (1 - jet_lag.estimated_recovery_days / 10.0) * 60 +
                (1 - fatigue.fatigue_score / 100.0) * 40
            )

            # Bonus for optimal jet lag times
            if hour in jet_lag.optimal_departure_times:
                score += 10

            if score > best_score:
                best_score = score
                best_hour = hour

        # Generate reason
        if best_hour in jet_lag.optimal_departure_times:
            best_reason = (
                f"Optimal for {jet_lag.direction.value} travel, "
                f"minimizes jet lag ({jet_lag.timezone_difference_hours:+.0f}h shift)"
            )
        else:
            best_reason = (
                f"Balances jet lag and flight fatigue for "
                f"{jet_lag.timezone_difference_hours:+.0f}h timezone shift"
            )

        return best_hour, best_reason


# Convenience functions
def calculate_jet_lag(
    origin: Airport,
    destination: Airport,
    age: int = 35
) -> JetLagReport:
    """
    Calculate jet lag for a flight.

    Args:
        origin: Origin airport
        destination: Destination airport
        age: Passenger age

    Returns:
        JetLagReport
    """
    analyzer = PassengerExperience()
    return analyzer.calculate_jet_lag(origin, destination, passenger_age=age)


def get_best_departure_time(
    origin: Airport,
    destination: Airport,
    age: int = 35
) -> Tuple[int, str]:
    """
    Get recommended departure time.

    Args:
        origin: Origin airport
        destination: Destination airport
        age: Passenger age

    Returns:
        (hour, reason)
    """
    analyzer = PassengerExperience()
    return analyzer.recommend_best_departure_time(origin, destination, age)


def assess_flight_fatigue(
    origin: Airport,
    destination: Airport,
    departure_hour: int
) -> FatigueReport:
    """
    Assess flight fatigue.

    Args:
        origin: Origin airport
        destination: Destination airport
        departure_hour: Departure time (0-23)

    Returns:
        FatigueReport
    """
    analyzer = PassengerExperience()
    return analyzer.calculate_flight_fatigue(origin, destination, departure_hour)
