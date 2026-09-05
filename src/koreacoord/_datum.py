"""Datum shift between Bessel 1841 (Tokyo) and WGS84. / 베셀(도쿄측지계)↔WGS84 측지계 변환."""

from __future__ import annotations

import math
from typing import Tuple

from ._params import (
    DEG,
    MOLODENSKY_DS,
    MOLODENSKY_DX,
    MOLODENSKY_DY,
    MOLODENSKY_DZ,
    MOLODENSKY_KAPPA,
    MOLODENSKY_OMEGA,
    MOLODENSKY_PHI,
    BESSEL_1841,
    Ellipsoid,
    WGS84_ELLIPSOID,
)

_CARTESIAN_ITERATIONS = 31
_CARTESIAN_TOLERANCE = 1.0e-18


def geodetic_to_cartesian(lon: float, lat: float, ell: Ellipsoid) -> Tuple[float, float, float]:
    """Geographic to geocentric cartesian at zero height. / 경위도를 지심 직교좌표로 (높이 0)."""
    lat_r = lat * DEG
    lon_r = lon * DEG
    nu = ell.a / math.sqrt(1 - ell.e2 * math.sin(lat_r) ** 2)
    return (
        nu * math.cos(lat_r) * math.cos(lon_r),
        nu * math.cos(lat_r) * math.sin(lon_r),
        nu * (ell.b**2 / ell.a**2) * math.sin(lat_r),
    )


def cartesian_to_geodetic(x: float, y: float, z: float, ell: Ellipsoid) -> Tuple[float, float]:
    """Geocentric cartesian to geographic. / 지심 직교좌표를 경위도로.

    Latitude is solved iteratively. / 위도는 반복 계산으로 수렴시킵니다.
    """
    lon = math.degrees(math.atan2(y, x))
    if lon < 0:
        lon += 360.0

    p = math.hypot(x, y)
    one_minus_e2 = ell.b**2 / ell.a**2

    nu = ell.a
    height = 0.0
    lat_r = 0.0
    previous = 0.0
    for _ in range(_CARTESIAN_ITERATIONS):
        lat_r = math.atan(z / math.sqrt((one_minus_e2 * nu + height) ** 2 - z**2))
        if abs(lat_r - previous) < _CARTESIAN_TOLERANCE:
            break
        nu = ell.a / math.sqrt(1 - ell.e2 * math.sin(lat_r) ** 2)
        height = p / math.cos(lat_r) - nu
        previous = lat_r

    return lon, lat_r / DEG


def _wgs84_frame_to_bessel(x: float, y: float, z: float) -> Tuple[float, float, float]:
    scale = 1 + MOLODENSKY_DS
    return (
        x + scale * (MOLODENSKY_KAPPA * y - MOLODENSKY_PHI * z) + MOLODENSKY_DX,
        y + scale * (-MOLODENSKY_KAPPA * x + MOLODENSKY_OMEGA * z) + MOLODENSKY_DY,
        z + scale * (MOLODENSKY_PHI * x - MOLODENSKY_OMEGA * y) + MOLODENSKY_DZ,
    )


def _bessel_frame_to_wgs84(x: float, y: float, z: float) -> Tuple[float, float, float]:
    scale = 1 + MOLODENSKY_DS
    sx = (x - MOLODENSKY_DX) * scale
    sy = (y - MOLODENSKY_DY) * scale
    sz = (z - MOLODENSKY_DZ) * scale
    return (
        (sx - MOLODENSKY_KAPPA * sy + MOLODENSKY_PHI * sz) / scale,
        (MOLODENSKY_KAPPA * sx + sy - MOLODENSKY_OMEGA * sz) / scale,
        (-MOLODENSKY_PHI * sx + MOLODENSKY_OMEGA * sy + sz) / scale,
    )


def bessel_to_wgs84(lon: float, lat: float) -> Tuple[float, float]:
    """Bessel/Tokyo geographic to WGS84 geographic. / 베셀 경위도를 WGS84 경위도로."""
    x, y, z = geodetic_to_cartesian(lon, lat, BESSEL_1841)
    return cartesian_to_geodetic(*_bessel_frame_to_wgs84(x, y, z), WGS84_ELLIPSOID)


def wgs84_to_bessel(lon: float, lat: float) -> Tuple[float, float]:
    """WGS84 geographic to Bessel/Tokyo geographic. / WGS84 경위도를 베셀 경위도로."""
    x, y, z = geodetic_to_cartesian(lon, lat, WGS84_ELLIPSOID)
    return cartesian_to_geodetic(*_wgs84_frame_to_bessel(x, y, z), BESSEL_1841)
