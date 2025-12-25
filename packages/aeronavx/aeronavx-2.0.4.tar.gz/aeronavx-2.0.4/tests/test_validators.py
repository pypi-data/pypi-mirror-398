import pytest
from aeronavx.utils.validators import is_valid_iata, is_valid_icao, validate_coordinates, normalize_airport_code


def test_valid_iata():
    assert is_valid_iata("JFK") is True
    assert is_valid_iata("LHR") is True
    assert is_valid_iata("IST") is True


def test_invalid_iata():
    assert is_valid_iata("KJFK") is False
    assert is_valid_iata("JF") is False
    assert is_valid_iata("123") is False
    assert is_valid_iata("") is False


def test_valid_icao():
    assert is_valid_icao("KJFK") is True
    assert is_valid_icao("EGLL") is True
    assert is_valid_icao("LTFM") is True


def test_invalid_icao():
    assert is_valid_icao("JFK") is False
    assert is_valid_icao("KJFKX") is False
    assert is_valid_icao("") is False


def test_validate_coordinates_valid():
    validate_coordinates(0.0, 0.0)
    validate_coordinates(51.5074, -0.1278)
    validate_coordinates(-90.0, -180.0)
    validate_coordinates(90.0, 180.0)


def test_validate_coordinates_invalid():
    with pytest.raises(ValueError):
        validate_coordinates(91.0, 0.0)

    with pytest.raises(ValueError):
        validate_coordinates(-91.0, 0.0)

    with pytest.raises(ValueError):
        validate_coordinates(0.0, 181.0)

    with pytest.raises(ValueError):
        validate_coordinates(0.0, -181.0)


def test_normalize_airport_code():
    assert normalize_airport_code("jfk") == "JFK"
    assert normalize_airport_code(" lhr ") == "LHR"
    assert normalize_airport_code("IST") == "IST"
