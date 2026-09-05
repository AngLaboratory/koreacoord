"""Behaviour and accuracy tests for koreacoord."""

from __future__ import annotations

import pytest

import koreacoord
from koreacoord import CoordSystem, supported_systems, transform

# 위경도 오차를 미터로 환산할 때 쓰는 보수적인 상수(위도 1° 기준)
_DEGREE_METERS = 111320.0
_CONGNAMUL_METERS = 0.4  # 격자 1칸 = 1/2.5 m

_UNIT_METERS = {
    CoordSystem.WGS84: _DEGREE_METERS,
    CoordSystem.BESSEL: _DEGREE_METERS,
    CoordSystem.CONGNAMUL: _CONGNAMUL_METERS,
    CoordSystem.WCONGNAMUL: _CONGNAMUL_METERS,
}

_TOKYO_DATUM = {CoordSystem.TM, CoordSystem.KTM, CoordSystem.CONGNAMUL, CoordSystem.BESSEL}
_GRID = {CoordSystem.CONGNAMUL, CoordSystem.WCONGNAMUL}

POINTS = {
    "Seoul": (126.9784, 37.5666),
    "Busan": (129.0756, 35.1796),
    "Gangneung": (128.8961, 37.7519),
    "Mokpo": (126.3922, 34.8118),
    "Jeju": (126.5312, 33.4996),
    "Ulleung": (130.9057, 37.4845),
    "Dokdo": (131.8695, 37.2412),
}

# 서울시청. pyproj 및 원본 구현과 대조해 확정한 값.
SEOUL_EXPECTED = {
    CoordSystem.TM: (198022.06399006367, 451590.8513881066),
    CoordSystem.WTM: (198091.70807508586, 451896.12121964525),
    CoordSystem.CONGNAMUL: (495055, 1128977),
    CoordSystem.WCONGNAMUL: (495229, 1129740),
    CoordSystem.KTM: (309945.5901570672, 552083.9316309551),
    CoordSystem.WKTM: (309752.64632145653, 552391.2734630271),
    CoordSystem.UTM: (321459.8553393931, 4159650.97717958),
    CoordSystem.WGS84: (126.9784, 37.5666),
    CoordSystem.BESSEL: (126.98050013131386, 37.563802643900786),
}


def _unit_in_meters(system: CoordSystem) -> float:
    return _UNIT_METERS.get(system, 1.0)


# --------------------------------------------------------------------------
# accuracy
# --------------------------------------------------------------------------


@pytest.mark.parametrize("system,expected", SEOUL_EXPECTED.items(), ids=lambda v: getattr(v, "value", ""))
def test_seoul_matches_known_values(system, expected):
    """Pinned output so a future refactor cannot silently move results."""
    x, y = transform(*POINTS["Seoul"], "WGS84", system)
    assert x == pytest.approx(expected[0], abs=1e-6)
    assert y == pytest.approx(expected[1], abs=1e-6)


@pytest.mark.parametrize("name", POINTS)
@pytest.mark.parametrize("source", list(CoordSystem))
@pytest.mark.parametrize("target", list(CoordSystem))
def test_round_trip(name, source, target):
    """source -> target -> source must return to where it started."""
    seed = transform(*POINTS[name], "WGS84", source)
    there = transform(*seed, source, target)
    back = transform(*there, target, source)

    if target in _GRID:
        tolerance_m = 0.5  # 격자가 정수라 왕복 시 반 칸까지 손실
    elif (source in _TOKYO_DATUM) != (target in _TOKYO_DATUM):
        tolerance_m = 0.05  # Molodensky 근사의 왕복 오차
    else:
        tolerance_m = 1e-3  # 급수 전개 한계. 독도(중앙자오선 +4.9°)에서도 0.03mm 수준

    tolerance = tolerance_m / _unit_in_meters(source)
    assert back[0] == pytest.approx(seed[0], abs=tolerance)
    assert back[1] == pytest.approx(seed[1], abs=tolerance)


@pytest.mark.parametrize(
    "system,definition",
    [
        (
            CoordSystem.WTM,
            "+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=500000 "
            "+ellps=WGS84 +units=m +no_defs",
        ),
        (
            CoordSystem.WKTM,
            "+proj=tmerc +lat_0=38 +lon_0=128 +k=0.9999 +x_0=400000 +y_0=600000 "
            "+ellps=WGS84 +units=m +no_defs",
        ),
        (CoordSystem.UTM, "EPSG:32652"),
    ],
)
@pytest.mark.parametrize("name", POINTS)
def test_projection_matches_pyproj(system, definition, name):
    """The TM projection itself is checked against an independent implementation."""
    pyproj = pytest.importorskip("pyproj")

    crs = pyproj.CRS.from_user_input(definition)
    forward = pyproj.Transformer.from_crs(pyproj.CRS.from_epsg(4326), crs, always_xy=True)

    lon, lat = POINTS[name]
    expected_x, expected_y = forward.transform(lon, lat)
    x, y = transform(lon, lat, "WGS84", system)

    assert x == pytest.approx(expected_x, abs=1e-3)
    assert y == pytest.approx(expected_y, abs=1e-3)

    inverse = pyproj.Transformer.from_crs(crs, pyproj.CRS.from_epsg(4326), always_xy=True)
    expected_lon, expected_lat = inverse.transform(expected_x, expected_y)
    got_lon, got_lat = transform(expected_x, expected_y, system, "WGS84")

    assert got_lon == pytest.approx(expected_lon, abs=1e-9)
    assert got_lat == pytest.approx(expected_lat, abs=1e-9)


def test_datum_shift_has_expected_direction():
    """Tokyo datum sits north-east of WGS84 in Korea by roughly 300 m."""
    lon, lat = POINTS["Seoul"]
    bessel_lon, bessel_lat = transform(lon, lat, "WGS84", "BESSEL")

    assert bessel_lon - lon == pytest.approx(0.0021, abs=0.0005)
    assert bessel_lat - lat == pytest.approx(-0.0028, abs=0.0005)


# --------------------------------------------------------------------------
# congnamul specifics
# --------------------------------------------------------------------------


def test_congnamul_results_are_integers():
    for system in (CoordSystem.CONGNAMUL, CoordSystem.WCONGNAMUL):
        x, y = transform(*POINTS["Seoul"], "WGS84", system)
        assert isinstance(x, int)
        assert isinstance(y, int)


@pytest.mark.parametrize("name", ["Jeju", "Ulleung", "Dokdo"])
def test_island_regions_survive_a_congnamul_round_trip(name):
    """Undoing the island move must land back on the same spot.

    도서 지역 보정을 되돌릴 때 이동된 사각형으로 판정하지 않으면 50km 어긋난다.
    """
    lon, lat = POINTS[name]
    x, y = transform(lon, lat, "WGS84", "CONGNAMUL")
    back_lon, back_lat = transform(x, y, "CONGNAMUL", "WGS84")

    assert back_lon == pytest.approx(lon, abs=1e-5)
    assert back_lat == pytest.approx(lat, abs=1e-5)


def test_island_shift_applies_only_to_congnamul():
    """Jeju is relocated on the Bessel grid but not on the WGS84 one."""
    mainland = POINTS["Seoul"]
    island = POINTS["Jeju"]

    # 본토에서는 두 격자의 차이가 측지계 차이 정도(수백 칸)에 그침
    cong = transform(*mainland, "WGS84", "CONGNAMUL")
    wcong = transform(*mainland, "WGS84", "WCONGNAMUL")
    assert abs(cong[1] - wcong[1]) < 10_000

    # 제주에서는 CONGNAMUL 쪽만 크게 이동함
    cong = transform(*island, "WGS84", "CONGNAMUL")
    wcong = transform(*island, "WGS84", "WCONGNAMUL")
    assert cong[1] - wcong[1] > 100_000


# --------------------------------------------------------------------------
# api behaviour
# --------------------------------------------------------------------------


def test_same_system_returns_input():
    assert transform(126.9784, 37.5666, "WGS84", "WGS84") == (126.9784, 37.5666)


def test_strings_and_enum_members_agree():
    from_string = transform(*POINTS["Seoul"], "WGS84", "UTM")
    from_enum = transform(*POINTS["Seoul"], CoordSystem.WGS84, CoordSystem.UTM)
    assert from_string == from_enum


@pytest.mark.parametrize("name", ["wgs84", " WGS84 ", "WgS84"])
def test_system_names_are_case_and_space_insensitive(name):
    assert transform(198091.70807508586, 451896.12121964525, "WTM", name) == pytest.approx(
        POINTS["Seoul"], abs=1e-9
    )


def test_unknown_system_raises_value_error():
    with pytest.raises(ValueError, match="not a supported coordinate system"):
        transform(0.0, 0.0, "WGS84", "EPSG:5179")


def test_unknown_system_names_the_offending_argument():
    with pytest.raises(ValueError, match="from_system"):
        transform(0.0, 0.0, "NOPE", "WGS84")


def test_non_numeric_coordinates_raise_type_error():
    with pytest.raises(TypeError, match="must be numbers"):
        transform("서울", 37.5666, "WGS84", "UTM")


def test_supported_systems_lists_every_member():
    assert supported_systems() == [s.value for s in CoordSystem]
    assert "WCONGNAMUL" in supported_systems()


def test_coord_system_compares_equal_to_its_name():
    assert CoordSystem.WGS84 == "WGS84"
    assert str(CoordSystem.WCONGNAMUL) == "WCONGNAMUL"


# --------------------------------------------------------------------------
# backwards compatibility with the original script
# --------------------------------------------------------------------------


def test_get_trans_coord_alias():
    expected = transform(*POINTS["Seoul"], "WGS84", "WCONGNAMUL")
    got = koreacoord.get_trans_coord(
        x=POINTS["Seoul"][0], y=POINTS["Seoul"][1], input="WGS84", output="WCONGNAMUL"
    )
    assert got == expected


def test_get_trans_coord_is_keyword_only():
    with pytest.raises(TypeError):
        koreacoord.get_trans_coord(126.9784, 37.5666, "WGS84", "UTM")


def test_map_type_alias():
    assert koreacoord.map_type() == supported_systems()


def test_package_exposes_version():
    assert koreacoord.__version__
