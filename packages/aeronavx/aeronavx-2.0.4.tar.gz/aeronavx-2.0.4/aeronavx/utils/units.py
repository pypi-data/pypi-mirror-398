from typing import Literal

from .constants import (
    KM_TO_MI,
    KM_TO_NM,
    MI_TO_KM,
    NM_TO_KM,
    M_TO_FT,
    FT_TO_M,
)

DistanceUnit = Literal["km", "mi", "nmi", "m"]
ElevationUnit = Literal["ft", "m"]


def km_to_mi(km: float) -> float:
    return km * KM_TO_MI


def km_to_nmi(km: float) -> float:
    return km * KM_TO_NM


def km_to_m(km: float) -> float:
    return km * 1000.0


def mi_to_km(mi: float) -> float:
    return mi * MI_TO_KM


def nmi_to_km(nmi: float) -> float:
    return nmi * NM_TO_KM


def m_to_km(m: float) -> float:
    return m / 1000.0


def ft_to_m(ft: float) -> float:
    return ft * FT_TO_M


def m_to_ft(m: float) -> float:
    return m * M_TO_FT


def convert_distance(value: float, from_unit: DistanceUnit, to_unit: DistanceUnit) -> float:
    if from_unit == to_unit:
        return value

    if from_unit == "km":
        km_value = value
    elif from_unit == "mi":
        km_value = mi_to_km(value)
    elif from_unit == "nmi":
        km_value = nmi_to_km(value)
    elif from_unit == "m":
        km_value = m_to_km(value)
    else:
        raise ValueError(f"Unknown distance unit: {from_unit}")

    if to_unit == "km":
        return km_value
    elif to_unit == "mi":
        return km_to_mi(km_value)
    elif to_unit == "nmi":
        return km_to_nmi(km_value)
    elif to_unit == "m":
        return km_to_m(km_value)
    else:
        raise ValueError(f"Unknown distance unit: {to_unit}")


def convert_elevation(value: float, from_unit: ElevationUnit, to_unit: ElevationUnit) -> float:
    if from_unit == to_unit:
        return value

    if from_unit == "ft":
        if to_unit == "m":
            return ft_to_m(value)
    elif from_unit == "m":
        if to_unit == "ft":
            return m_to_ft(value)

    raise ValueError(f"Cannot convert {from_unit} to {to_unit}")
