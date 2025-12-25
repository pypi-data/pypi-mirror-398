import pytest
from aeronavx.core.distance import haversine_km, slc_km, vincenty_km, distance


def test_haversine_distance():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    dist = haversine_km(lat1, lon1, lat2, lon2)

    assert 5500 < dist < 5600


def test_slc_distance():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    dist = slc_km(lat1, lon1, lat2, lon2)

    assert 5500 < dist < 5600


def test_vincenty_distance():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    dist = vincenty_km(lat1, lon1, lat2, lon2)

    assert 5500 < dist < 5600


def test_distance_function_with_units():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    dist_km = distance(lat1, lon1, lat2, lon2, model="haversine", unit="km")
    dist_mi = distance(lat1, lon1, lat2, lon2, model="haversine", unit="mi")
    dist_nmi = distance(lat1, lon1, lat2, lon2, model="haversine", unit="nmi")

    assert 5500 < dist_km < 5600
    assert 3400 < dist_mi < 3500
    assert 2900 < dist_nmi < 3100


def test_zero_distance():
    lat, lon = 40.7128, -74.0060

    dist = haversine_km(lat, lon, lat, lon)

    assert dist == 0.0


def test_invalid_coordinates():
    with pytest.raises(ValueError):
        distance(91.0, 0.0, 0.0, 0.0)

    with pytest.raises(ValueError):
        distance(0.0, 181.0, 0.0, 0.0)
