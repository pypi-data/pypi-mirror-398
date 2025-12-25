import pytest
from aeronavx.core.geodesy import initial_bearing, final_bearing, midpoint, intermediate_point, great_circle_path


def test_initial_bearing():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    bearing = initial_bearing(lat1, lon1, lat2, lon2)

    assert 280 < bearing < 300


def test_final_bearing():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    bearing = final_bearing(lat1, lon1, lat2, lon2)

    assert 230 < bearing < 250


def test_midpoint():
    lat1, lon1 = 51.5074, -0.1278
    lat2, lon2 = 40.7128, -74.0060

    mid_lat, mid_lon = midpoint(lat1, lon1, lat2, lon2)

    assert 50 < mid_lat < 54
    assert -42 < mid_lon < -38


def test_intermediate_point():
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 10.0, 10.0

    point = intermediate_point(lat1, lon1, lat2, lon2, 0.5)

    assert 4.5 < point[0] < 5.5
    assert 4.5 < point[1] < 5.5


def test_intermediate_point_boundaries():
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 10.0, 10.0

    start = intermediate_point(lat1, lon1, lat2, lon2, 0.0)
    end = intermediate_point(lat1, lon1, lat2, lon2, 1.0)

    assert start == (lat1, lon1)
    assert end == (lat2, lon2)


def test_great_circle_path():
    lat1, lon1 = 0.0, 0.0
    lat2, lon2 = 10.0, 10.0

    path = great_circle_path(lat1, lon1, lat2, lon2, num_points=11)

    assert len(path) == 11
    assert path[0] == (lat1, lon1)
    assert path[-1] == (lat2, lon2)


def test_invalid_fraction():
    with pytest.raises(ValueError):
        intermediate_point(0.0, 0.0, 10.0, 10.0, 1.5)
