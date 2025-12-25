from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ..models.airport import Airport

try:
    from scipy.spatial import KDTree as ScipyKDTree
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

from ..utils.constants import EARTH_RADIUS_KM
import math


class SpatialIndex:
    def __init__(self, airports: Sequence["Airport"]):
        self.airports = list(airports)
        self._use_scipy = HAS_SCIPY and len(self.airports) > 100

        if self._use_scipy:
            coords_rad = [
                (math.radians(a.latitude_deg), math.radians(a.longitude_deg))
                for a in self.airports
            ]
            self._tree = ScipyKDTree(coords_rad)
        else:
            self._tree = None

    def nearest(
        self,
        lat: float,
        lon: float,
        n: int = 1,
        max_distance_km: float | None = None
    ) -> list["Airport"]:
        if self._use_scipy:
            return self._nearest_scipy(lat, lon, n, max_distance_km)
        else:
            return self._nearest_linear(lat, lon, n, max_distance_km)

    def _nearest_scipy(
        self,
        lat: float,
        lon: float,
        n: int,
        max_distance_km: float | None
    ) -> list["Airport"]:
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        if max_distance_km is not None:
            max_distance_rad = max_distance_km / EARTH_RADIUS_KM
            distances, indices = self._tree.query(
                [lat_rad, lon_rad],
                k=min(n, len(self.airports)),
                distance_upper_bound=max_distance_rad
            )
        else:
            distances, indices = self._tree.query(
                [lat_rad, lon_rad],
                k=min(n, len(self.airports))
            )

        if n == 1:
            distances = [distances]
            indices = [indices]

        result = []
        for dist, idx in zip(distances, indices):
            if idx < len(self.airports) and not math.isinf(dist):
                result.append(self.airports[idx])

        return result

    def _nearest_linear(
        self,
        lat: float,
        lon: float,
        n: int,
        max_distance_km: float | None
    ) -> list["Airport"]:
        from ..core.distance import haversine_km

        distances = [
            (haversine_km(lat, lon, a.latitude_deg, a.longitude_deg), a)
            for a in self.airports
        ]

        distances.sort(key=lambda x: x[0])

        if max_distance_km is not None:
            distances = [(d, a) for d, a in distances if d <= max_distance_km]

        return [a for _, a in distances[:n]]

    def within_radius(self, lat: float, lon: float, radius_km: float) -> list["Airport"]:
        if self._use_scipy:
            lat_rad = math.radians(lat)
            lon_rad = math.radians(lon)
            radius_rad = radius_km / EARTH_RADIUS_KM

            indices = self._tree.query_ball_point([lat_rad, lon_rad], radius_rad)
            return [self.airports[i] for i in indices]
        else:
            from ..core.distance import haversine_km

            return [
                a for a in self.airports
                if haversine_km(lat, lon, a.latitude_deg, a.longitude_deg) <= radius_km
            ]


def build_spatial_index(airports: Sequence["Airport"]) -> SpatialIndex:
    return SpatialIndex(airports)
