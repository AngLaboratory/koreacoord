"""Ellipsoid and projection constants. / 타원체·투영 원점 상수."""

from __future__ import annotations

import math
from typing import NamedTuple

DEG = math.pi / 180.0


class Ellipsoid(NamedTuple):
    """Reference ellipsoid. / 기준 타원체.

    a: semi-major axis in meters / 장반경(m)
    f: flattening / 편평률
    """

    a: float
    f: float

    @property
    def b(self) -> float:
        """Semi-minor axis. / 단반경."""
        return self.a * (1.0 - self.f)

    @property
    def e2(self) -> float:
        """First eccentricity squared. / 제1이심률의 제곱."""
        return (self.a**2 - self.b**2) / self.a**2

    @property
    def ep2(self) -> float:
        """Second eccentricity squared. / 제2이심률의 제곱."""
        return (self.a**2 - self.b**2) / self.b**2


class TMParams(NamedTuple):
    """Transverse Mercator origin. / 횡메르카토르 투영 원점.

    Angles in degrees, offsets in meters. / 각도는 도(°), 오프셋은 m.
    """

    false_northing: float
    false_easting: float
    k0: float
    lat0: float
    lon0: float


BESSEL_1841 = Ellipsoid(6377397.155, 0.0033427731799399794)
WGS84_ELLIPSOID = Ellipsoid(6378137.0, 0.0033528106647474805)

# 127°00'10.405" — 도쿄측지계 기준 한국 구 지형도의 중부원점 경도
TM_ORIGIN = TMParams(500000.0, 200000.0, 1.0, 38.0, 127.0028902777777777776)
WTM_ORIGIN = TMParams(500000.0, 200000.0, 1.0, 38.0, 127.0)
KTM_ORIGIN = TMParams(600000.0, 400000.0, 0.9999, 38.0, 128.0)

# UTM Zone 52N (중앙자오선 129°E). 한국 밖에서는 존이 달라 이 값이 맞지 않음.
UTM52N_ORIGIN = TMParams(0.0, 500000.0, 0.9996, 0.0, 129.0)

# Tokyo datum -> WGS84, 한반도 지역 7-parameter (Molodensky-Badekas)
MOLODENSKY_DX = 115.8
MOLODENSKY_DY = -474.99
MOLODENSKY_DZ = -674.11
MOLODENSKY_OMEGA = 1.16 / 3600.0 * DEG
MOLODENSKY_PHI = -2.31 / 3600.0 * DEG
MOLODENSKY_KAPPA = -1.63 / 3600.0 * DEG
MOLODENSKY_DS = -6.43e-6
