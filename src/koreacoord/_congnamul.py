"""Congnamul grid used by Kakao(Daum) maps. / 카카오(다음) 지도의 콩나물 좌표."""

from __future__ import annotations

import math
from typing import Tuple

SCALE = 2.5

# 지도상 별도 위치로 옮겨 그리는 도서 지역(제주·울릉·독도 등)의 TM 영역과 보정량.
# (x, y, width, height), 단위 m
_ISLAND_RECTS = (
    (112500.0, -50000.0, 33500.0, 53000.0),
    (146000.0, -50000.0, 54000.0, 58600.0),
    (130000.0, 44000.0, 15000.0, 14000.0),
    (532500.0, 437500.0, 25000.0, 25000.0),
    (625000.0, 412500.0, 25000.0, 25000.0),
    (-12500.0, 462500.0, 17500.0, 50000.0),
)

_SHIFT_TO_GRID = (
    (0.0, 50000.0),
    (0.0, 50000.0),
    (0.0, 10000.0),
    (-70378.0, -136.0),
    (-144738.0, -2161.0),
    (23510.0, -111.0),
)

_SHIFT_TO_TM = tuple((-dx, -dy) for dx, dy in _SHIFT_TO_GRID)

# 되돌릴 때는 이미 옮겨진 좌표가 들어오므로, 사각형도 같이 옮겨 놓고 판정한다.
_ISLAND_RECTS_MOVED = tuple(
    (rx + dx, ry + dy, rw, rh)
    for (rx, ry, rw, rh), (dx, dy) in zip(_ISLAND_RECTS, _SHIFT_TO_GRID)
)


def _round_half_up(value: float) -> int:
    return math.floor(value + 0.5)


def _island_offset(
    x: float,
    y: float,
    rects: Tuple[Tuple[float, float, float, float], ...],
    shifts: Tuple[Tuple[float, float], ...],
) -> Tuple[float, float]:
    for (rx, ry, rw, rh), shift in zip(rects, shifts):
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            return shift
    return 0.0, 0.0


def tm_to_grid(easting: float, northing: float) -> Tuple[int, int]:
    """Scale TM meters onto the grid. / TM 평면좌표에 배율만 적용."""
    return _round_half_up(easting * SCALE), _round_half_up(northing * SCALE)


def grid_to_tm(x: float, y: float) -> Tuple[float, float]:
    """Scale the grid back to TM meters. / 콩나물 좌표를 TM 평면좌표 배율로 되돌림."""
    return x / SCALE, y / SCALE


def tm_to_grid_shifted(easting: float, northing: float) -> Tuple[int, int]:
    """As :func:`tm_to_grid`, moving island regions. / 도서 지역 보정을 포함."""
    dx, dy = _island_offset(easting, northing, _ISLAND_RECTS, _SHIFT_TO_GRID)
    return (
        _round_half_up((easting + dx) * SCALE),
        _round_half_up((northing + dy) * SCALE),
    )


def grid_to_tm_shifted(x: float, y: float) -> Tuple[float, float]:
    """As :func:`grid_to_tm`, undoing the island move. / 도서 지역 보정을 되돌림."""
    easting, northing = grid_to_tm(x, y)
    dx, dy = _island_offset(easting, northing, _ISLAND_RECTS_MOVED, _SHIFT_TO_TM)
    return easting + dx, northing + dy
