"""Convert between Korean coordinate systems. / 한국 좌표계 간 변환.

>>> from koreacoord import transform
>>> transform(126.9876757, 37.5611523, "WGS84", "WCONGNAMUL")
"""

from __future__ import annotations

from ._params import BESSEL_1841, WGS84_ELLIPSOID, Ellipsoid, TMParams
from .core import get_trans_coord, map_type, supported_systems, transform
from .systems import CoordSystem

__version__ = "0.1.0"

__all__ = [
    "CoordSystem",
    "transform",
    "supported_systems",
    "get_trans_coord",
    "map_type",
    "Ellipsoid",
    "TMParams",
    "BESSEL_1841",
    "WGS84_ELLIPSOID",
    "__version__",
]
