"""Supported coordinate systems. / 지원하는 좌표계."""

from __future__ import annotations

from enum import Enum
from typing import Union


class CoordSystem(str, Enum):
    """A coordinate system understood by :func:`koreacoord.transform`.

    좌표 변환에 사용할 수 있는 좌표계.

    Members compare equal to their own names, so plain strings work anywhere a
    ``CoordSystem`` is accepted. / 멤버가 문자열과 같게 비교되므로
    ``"WGS84"`` 처럼 문자열을 그대로 넘겨도 됩니다.
    """

    TM = "TM"
    """Transverse Mercator, central belt, Bessel 1841. / 중부원점 TM (베셀)."""

    WTM = "WTM"
    """Transverse Mercator, central belt, WGS84. / 중부원점 TM (WGS84)."""

    CONGNAMUL = "CONGNAMUL"
    """Kakao(Daum) map internal grid, Bessel 1841. / 카카오 콩나물 좌표 (베셀)."""

    WCONGNAMUL = "WCONGNAMUL"
    """Kakao(Daum) map internal grid, WGS84. / 카카오 콩나물 좌표 (WGS84)."""

    KTM = "KTM"
    """Transverse Mercator, 128°E origin, Bessel 1841. / KTM (베셀)."""

    WKTM = "WKTM"
    """Transverse Mercator, 128°E origin, WGS84. / KTM (WGS84)."""

    UTM = "UTM"
    """UTM **Zone 52N** only, WGS84. / UTM 52N 존 전용 (WGS84)."""

    WGS84 = "WGS84"
    """Geographic longitude/latitude on WGS84. / WGS84 경위도."""

    BESSEL = "BESSEL"
    """Geographic longitude/latitude on Bessel 1841 (Tokyo datum).
    / 베셀 경위도 (도쿄측지계)."""

    def __str__(self) -> str:
        return self.value


SystemLike = Union[CoordSystem, str]


def coerce(value: SystemLike, argname: str) -> CoordSystem:
    """Normalize a string or enum member into a :class:`CoordSystem`.

    문자열이나 열거형 값을 :class:`CoordSystem` 으로 정규화합니다.

    Raises:
        ValueError: if the name is not a supported system. / 지원하지 않는 좌표계일 때.
    """
    if isinstance(value, CoordSystem):
        return value
    if isinstance(value, str):
        try:
            return CoordSystem(value.strip().upper())
        except ValueError:
            pass
    supported = ", ".join(s.value for s in CoordSystem)
    raise ValueError(f"{argname}={value!r} is not a supported coordinate system. Use one of: {supported}")
