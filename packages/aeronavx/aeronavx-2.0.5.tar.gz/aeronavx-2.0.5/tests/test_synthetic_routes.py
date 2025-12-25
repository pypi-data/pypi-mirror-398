"""
Regression tests for synthetic route generation.

These tests ensure that critical route generation functionality
does not break in future releases.
"""

import pytest
from aeronavx import generate_route
from aeronavx.core.synthetic_routes import Waypoint, FlightPhase


def test_generate_route_ist_jfk():
    """
    Regression test: IST → JFK route generation must not raise TypeError.

    This test was added to prevent the recurrence of the bug:
    TypeError: great_circle_path() got an unexpected keyword argument 'fraction'
    """
    route = generate_route("IST", "JFK")

    assert route is not None
    assert route.origin.iata_code == "IST"
    assert route.destination.iata_code == "JFK"
    assert route.total_distance_km > 0
    assert route.total_time_hours > 0
    assert len(route.waypoints) > 0


def test_generate_route_has_waypoints():
    """Ensure generated routes have waypoints."""
    route = generate_route("IST", "JFK")

    assert hasattr(route, "waypoints")
    assert isinstance(route.waypoints, list)
    assert len(route.waypoints) > 5  # Should have takeoff, climb, cruise, descent, landing

    # Check waypoint structure
    for wp in route.waypoints:
        assert isinstance(wp, Waypoint)
        assert hasattr(wp, "latitude")
        assert hasattr(wp, "longitude")
        assert hasattr(wp, "altitude_ft")
        assert hasattr(wp, "phase")
        assert isinstance(wp.phase, FlightPhase)


def test_generate_route_waypoint_phases():
    """Ensure route has all expected flight phases."""
    route = generate_route("IST", "JFK")

    phases = {wp.phase for wp in route.waypoints}

    # Should have at least these phases
    expected_phases = {
        FlightPhase.TAXI_OUT,
        FlightPhase.TAKEOFF,
        FlightPhase.CRUISE,
        FlightPhase.LANDING,
    }

    assert expected_phases.issubset(phases), f"Missing phases: {expected_phases - phases}"


def test_generate_route_distance_consistency():
    """Ensure total distance is reasonable."""
    route = generate_route("IST", "JFK")

    # IST-JFK is approximately 8000 km
    assert 7500 < route.total_distance_km < 8500, \
        f"Distance {route.total_distance_km} km is outside expected range"


def test_generate_route_short_distance():
    """Test route generation for short distances."""
    route = generate_route("CDG", "LHR")  # Paris to London

    assert route is not None
    assert len(route.waypoints) > 0
    # Short route ~350 km
    assert 300 < route.total_distance_km < 450


def test_generate_route_different_aircraft():
    """Test route generation with different aircraft types."""
    aircraft_types = ["narrow_body", "wide_body", "regional", "private_jet"]

    for aircraft in aircraft_types:
        route = generate_route("IST", "JFK", aircraft=aircraft)
        assert route is not None
        assert len(route.waypoints) > 0
        assert route.flight_profile.aircraft_category.value == aircraft
