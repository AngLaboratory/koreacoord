"""Transverse Mercator forward/inverse projection. / 횡메르카토르 정·역투영."""

from __future__ import annotations

import math
from typing import Tuple

from ._params import DEG, Ellipsoid, TMParams

_FOOTPOINT_ITERATIONS = 5


def _meridian_coefficients(ell: Ellipsoid) -> Tuple[float, float, float, float, float]:
    """Series coefficients for the meridian arc. / 자오선 호길이 급수 계수."""
    a = ell.a
    n = (a - ell.b) / (a + ell.b)
    return (
        a * (1 - n + 5 * (n**2 - n**3) / 4 + 81 * (n**4 - n**5) / 64),
        3 * a * (n - n**2 + 7 * (n**3 - n**4) / 8 + 55 * n**5 / 64) / 2,
        15 * a * (n**2 - n**3 + 3 * (n**4 - n**5) / 4) / 16,
        35 * a * (n**3 - n**4 + 11 * n**5 / 16) / 48,
        315 * a * (n**4 - n**5) / 512,
    )


def _meridian_arc(lat_rad: float, coefficients: Tuple[float, ...]) -> float:
    """Meridian arc length from the equator. / 적도로부터의 자오선 호길이."""
    a0, a2, a4, a6, a8 = coefficients
    return (
        a0 * lat_rad
        - a2 * math.sin(2 * lat_rad)
        + a4 * math.sin(4 * lat_rad)
        - a6 * math.sin(6 * lat_rad)
        + a8 * math.sin(8 * lat_rad)
    )


def geodetic_to_tm(lon: float, lat: float, ell: Ellipsoid, proj: TMParams) -> Tuple[float, float]:
    """Project geographic coordinates onto a TM grid. / 경위도를 TM 평면좌표로 투영.

    Args:
        lon: longitude in degrees / 경도(°)
        lat: latitude in degrees / 위도(°)

    Returns:
        ``(easting, northing)`` in meters / 미터 단위의 ``(동거, 북거)``
    """
    coefficients = _meridian_coefficients(ell)
    e2, ep2 = ell.e2, ell.ep2
    k0 = proj.k0

    lat_r = lat * DEG
    dlon = lon * DEG - proj.lon0 * DEG

    arc0 = _meridian_arc(proj.lat0 * DEG, coefficients) * k0
    arc = _meridian_arc(lat_r, coefficients) * k0

    sin_lat = math.sin(lat_r)
    cos_lat = math.cos(lat_r)
    t = sin_lat / cos_lat
    t2, t4, t6 = t**2, t**4, t**6
    eta2 = ep2 * cos_lat**2
    nu = ell.a / math.sqrt(1 - e2 * sin_lat**2)

    common = nu * sin_lat * cos_lat * k0
    n1 = common / 2
    n2 = common * cos_lat**2 * (5 - t2 + 9 * eta2 + 4 * eta2**2) / 24
    n3 = (
        common
        * cos_lat**4
        * (
            61
            - 58 * t2
            + t4
            + 270 * eta2
            - 330 * t2 * eta2
            + 445 * eta2**2
            + 324 * eta2**3
            - 680 * t2 * eta2**2
            + 88 * eta2**4
            - 600 * t2 * eta2**3
            - 192 * t2 * eta2**4
        )
        / 720
    )
    n4 = common * cos_lat**6 * (1385 - 3111 * t2 + 543 * t4 - t6) / 40320

    northing = (
        arc
        + dlon**2 * n1
        + dlon**4 * n2
        + dlon**6 * n3
        + dlon**8 * n4
        - arc0
        + proj.false_northing
    )

    e1 = nu * cos_lat * k0
    e2_term = nu * cos_lat**3 * k0 * (1 - t2 + eta2) / 6
    e3 = (
        nu
        * cos_lat**5
        * k0
        * (
            5
            - 18 * t2
            + t4
            + 14 * eta2
            - 58 * t2 * eta2
            + 13 * eta2**2
            + 4 * eta2**3
            - 64 * t2 * eta2**2
            - 25 * t2 * eta2**3
        )
        / 120
    )
    e4 = nu * cos_lat**7 * k0 * (61 - 479 * t2 + 179 * t4 - t6) / 5040

    easting = proj.false_easting + dlon * e1 + dlon**3 * e2_term + dlon**5 * e3 + dlon**7 * e4

    return easting, northing


def tm_to_geodetic(
    easting: float, northing: float, ell: Ellipsoid, proj: TMParams
) -> Tuple[float, float]:
    """Unproject a TM grid coordinate back to geographic. / TM 평면좌표를 경위도로 역투영.

    Args:
        easting: easting in meters / 동거(m)
        northing: northing in meters / 북거(m)

    Returns:
        ``(lon, lat)`` in degrees / 도(°) 단위의 ``(경도, 위도)``
    """
    coefficients = _meridian_coefficients(ell)
    a, e2, ep2 = ell.a, ell.e2, ell.ep2
    k0 = proj.k0

    arc0 = _meridian_arc(proj.lat0 * DEG, coefficients) * k0
    target_arc = (northing + arc0 - proj.false_northing) / k0

    # 위도 0에서 출발해 자오선 호길이를 맞추는 footpoint 위도를 반복해서 찾음
    lat_f = target_arc / (a * (1 - e2))
    for _ in range(_FOOTPOINT_ITERATIONS):
        rho = a * (1 - e2) / math.pow(math.sqrt(1 - e2 * math.sin(lat_f) ** 2), 3)
        lat_f += (target_arc - _meridian_arc(lat_f, coefficients)) / rho

    sin_f = math.sin(lat_f)
    cos_f = math.cos(lat_f)
    rho = a * (1 - e2) / math.pow(math.sqrt(1 - e2 * sin_f**2), 3)
    nu = a / math.sqrt(1 - e2 * sin_f**2)
    t = sin_f / cos_f
    t2, t4, t6 = t**2, t**4, t**6
    eta2 = ep2 * cos_f**2
    dx = easting - proj.false_easting

    d1 = t / (2 * rho * nu * k0**2)
    d2 = t * (5 + 3 * t2 + eta2 - 4 * eta2**2 - 9 * t2 * eta2) / (24 * rho * nu**3 * k0**4)
    d3 = (
        t
        * (
            61
            + 90 * t2
            + 46 * eta2
            + 45 * t4
            - 252 * t2 * eta2
            - 3 * eta2**2
            + 100 * eta2**3
            - 66 * t2 * eta2**2
            - 90 * t4 * eta2
            + 88 * eta2**4
            + 225 * t4 * eta2**2
            + 84 * t2 * eta2**3
            - 192 * t2 * eta2**4
        )
        / (720 * rho * nu**5 * k0**6)
    )
    d4 = t * (1385 + 3633 * t2 + 4095 * t4 + 1575 * t6) / (40320 * rho * nu**7 * k0**8)

    lat_r = lat_f - dx**2 * d1 + dx**4 * d2 - dx**6 * d3 + dx**8 * d4

    c1 = 1 / (nu * cos_f * k0)
    c2 = (1 + 2 * t2 + eta2) / (6 * nu**3 * cos_f * k0**3)
    c3 = (
        5
        + 6 * eta2
        + 28 * t2
        - 3 * eta2**2
        + 8 * t2 * eta2
        + 24 * t4
        - 4 * eta2**3
        + 4 * t2 * eta2**2
        + 24 * t2 * eta2**3
    ) / (120 * nu**5 * cos_f * k0**5)
    c4 = (61 + 662 * t2 + 1320 * t4 + 720 * t6) / (5040 * nu**7 * cos_f * k0**7)

    lon_r = proj.lon0 * DEG + dx * c1 - dx**3 * c2 + dx**5 * c3 - dx**7 * c4

    return lon_r / DEG, lat_r / DEG
