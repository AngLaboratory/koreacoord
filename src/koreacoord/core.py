"""Coordinate transformation entry points. / 좌표 변환 진입점."""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from . import _congnamul
from ._datum import bessel_to_wgs84, wgs84_to_bessel
from ._params import (
    BESSEL_1841,
    KTM_ORIGIN,
    TM_ORIGIN,
    UTM52N_ORIGIN,
    WGS84_ELLIPSOID,
    WTM_ORIGIN,
    Ellipsoid,
    TMParams,
)
from ._projection import geodetic_to_tm, tm_to_geodetic
from .systems import CoordSystem, SystemLike, coerce

_TOKYO = "tokyo"
_WGS84 = "wgs84"

Converter = Callable[[float, float], Tuple[float, float]]


def _identity(x: float, y: float) -> Tuple[float, float]:
    return x, y


def _tm_converters(ell: Ellipsoid, proj: TMParams) -> Tuple[Converter, Converter]:
    def to_geographic(x: float, y: float) -> Tuple[float, float]:
        return tm_to_geodetic(x, y, ell, proj)

    def from_geographic(lon: float, lat: float) -> Tuple[float, float]:
        return geodetic_to_tm(lon, lat, ell, proj)

    return to_geographic, from_geographic


def _congnamul_converters(
    ell: Ellipsoid, proj: TMParams, *, shift_islands: bool
) -> Tuple[Converter, Converter]:
    to_tm = _congnamul.grid_to_tm_shifted if shift_islands else _congnamul.grid_to_tm
    to_grid = _congnamul.tm_to_grid_shifted if shift_islands else _congnamul.tm_to_grid

    def to_geographic(x: float, y: float) -> Tuple[float, float]:
        return tm_to_geodetic(*to_tm(x, y), ell, proj)

    def from_geographic(lon: float, lat: float) -> Tuple[float, float]:
        return to_grid(*geodetic_to_tm(lon, lat, ell, proj))

    return to_geographic, from_geographic


# system -> (datum, to geographic coords of that datum, back from them)
# 각 좌표계를 자기 측지계의 경위도로 오가는 표. 같은 측지계끼리는 측지계 변환을 건너뜀.
_REGISTRY: Dict[CoordSystem, Tuple[str, Converter, Converter]] = {
    CoordSystem.TM: (_TOKYO, *_tm_converters(BESSEL_1841, TM_ORIGIN)),
    CoordSystem.WTM: (_WGS84, *_tm_converters(WGS84_ELLIPSOID, WTM_ORIGIN)),
    CoordSystem.KTM: (_TOKYO, *_tm_converters(BESSEL_1841, KTM_ORIGIN)),
    CoordSystem.WKTM: (_WGS84, *_tm_converters(WGS84_ELLIPSOID, KTM_ORIGIN)),
    CoordSystem.UTM: (_WGS84, *_tm_converters(WGS84_ELLIPSOID, UTM52N_ORIGIN)),
    CoordSystem.CONGNAMUL: (
        _TOKYO,
        *_congnamul_converters(BESSEL_1841, TM_ORIGIN, shift_islands=True),
    ),
    CoordSystem.WCONGNAMUL: (
        _WGS84,
        *_congnamul_converters(WGS84_ELLIPSOID, WTM_ORIGIN, shift_islands=False),
    ),
    CoordSystem.BESSEL: (_TOKYO, _identity, _identity),
    CoordSystem.WGS84: (_WGS84, _identity, _identity),
}


def supported_systems() -> List[str]:
    """Names of every supported coordinate system. / 지원하는 좌표계 이름 목록."""
    return [system.value for system in CoordSystem]


def transform(
    x: float, y: float, from_system: SystemLike, to_system: SystemLike
) -> Tuple[float, float]:
    """Convert a single point between coordinate systems. / 좌표 한 점을 다른 좌표계로 변환.

    The axis order is always ``x`` then ``y`` — longitude before latitude for
    geographic systems, easting before northing for projected ones.
    축 순서는 항상 ``x``, ``y`` 입니다. 경위도계는 경도→위도, 평면좌표계는 동거→북거.

    Args:
        x: longitude, easting, or grid x / 경도·동거 또는 격자 x
        y: latitude, northing, or grid y / 위도·북거 또는 격자 y
        from_system: source system, e.g. ``"WGS84"`` / 입력 좌표계
        to_system: target system, e.g. ``CoordSystem.WCONGNAMUL`` / 출력 좌표계

    Returns:
        The converted ``(x, y)``. Congnamul results are integers.
        변환된 ``(x, y)``. 콩나물 좌표는 정수로 반환됩니다.

    Raises:
        ValueError: on an unknown coordinate system name / 지원하지 않는 좌표계일 때
        TypeError: if ``x`` or ``y`` is not a number / 좌표가 숫자가 아닐 때

    Example:
        >>> from koreacoord import transform
        >>> x, y = transform(126.9876757, 37.5611523, "WGS84", "WCONGNAMUL")

    Note:
        Parameters are tuned for Korea. ``UTM`` means zone 52N only, and
        ``BESSEL`` carries the Korean Tokyo-datum shift, so results outside the
        peninsula are not meaningful.
        모든 파라미터가 한국 기준입니다. ``UTM`` 은 52N 존 전용이고 ``BESSEL`` 은
        한반도용 도쿄측지계 변환값을 쓰므로, 한국 밖 좌표는 의미 있는 값이 아닙니다.
    """
    source = coerce(from_system, "from_system")
    target = coerce(to_system, "to_system")

    try:
        x = float(x)
        y = float(y)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"x and y must be numbers, got x={x!r}, y={y!r}") from exc

    if source is target:
        return x, y

    source_datum, to_geographic, _ = _REGISTRY[source]
    target_datum, _, from_geographic = _REGISTRY[target]

    lon, lat = to_geographic(x, y)
    if source_datum != target_datum:
        shift = bessel_to_wgs84 if source_datum == _TOKYO else wgs84_to_bessel
        lon, lat = shift(lon, lat)

    return from_geographic(lon, lat)


def get_trans_coord(
    *, x: float, y: float, input: SystemLike, output: SystemLike
) -> Tuple[float, float]:
    """Keyword-only alias of :func:`transform`. / :func:`transform` 의 키워드 전용 별칭.

    Kept for the original script's call signature. New code should call
    :func:`transform`. / 기존 스크립트 호환용입니다. 새 코드는 :func:`transform` 을 쓰세요.
    """
    return transform(x, y, input, output)


def map_type() -> List[str]:
    """Deprecated alias of :func:`supported_systems`. / :func:`supported_systems` 의 옛 이름."""
    return supported_systems()
