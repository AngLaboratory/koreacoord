# koreacoord

[![CI](https://github.com/AngLaboratory/koreacoord/actions/workflows/ci.yml/badge.svg)](https://github.com/AngLaboratory/koreacoord/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/koreacoord)](https://pypi.org/project/koreacoord/)
[![Python](https://img.shields.io/pypi/pyversions/koreacoord)](https://pypi.org/project/koreacoord/)

Convert between the coordinate systems used on Korean maps — TM, KTM, UTM 52N,
Kakao's Congnamul grid, WGS84 and Bessel/Tokyo — with no dependencies.

한국 지도에서 쓰이는 좌표계(TM, KTM, UTM 52N, 카카오 콩나물 좌표, WGS84, 베셀)를
서로 변환합니다. 외부 의존성이 없습니다.

## Install

```bash
pip install koreacoord
```

## Quick start

```python
from koreacoord import transform

# Seoul City Hall, WGS84 -> Kakao's Congnamul grid
x, y = transform(126.9876757, 37.5611523, "WGS84", "WCONGNAMUL")

# Enum members work too, and are what your IDE will autocomplete
from koreacoord import CoordSystem as CS

x, y = transform(126.9876757, 37.5611523, CS.WGS84, CS.UTM)
```

The axis order is always **x then y** — longitude before latitude for geographic
systems, easting before northing for projected ones.

## Supported systems

| Name | Description | Datum |
| --- | --- | --- |
| `WGS84` | Geographic longitude/latitude | WGS84 |
| `BESSEL` | Geographic longitude/latitude | Bessel 1841 (Tokyo) |
| `TM` | Transverse Mercator, central belt origin | Bessel 1841 |
| `WTM` | Transverse Mercator, central belt origin | WGS84 |
| `KTM` | Transverse Mercator, 128°E origin | Bessel 1841 |
| `WKTM` | Transverse Mercator, 128°E origin | WGS84 |
| `UTM` | UTM **zone 52N only** | WGS84 |
| `CONGNAMUL` | Kakao(Daum) map grid | Bessel 1841 |
| `WCONGNAMUL` | Kakao(Daum) map grid | WGS84 |

```python
from koreacoord import supported_systems

supported_systems()
# ['TM', 'WTM', 'CONGNAMUL', 'WCONGNAMUL', 'KTM', 'WKTM', 'UTM', 'WGS84', 'BESSEL']
```

## Scope

**This library is for Korea.** Every projection origin and datum parameter is
fixed to Korean values:

- `UTM` is hard-wired to **zone 52N** (central meridian 129°E). Coordinates from
  another zone will be silently wrong.
- `BESSEL` uses the Tokyo-datum shift published for the Korean peninsula, so it
  is not a general Bessel 1841 conversion.
- `CONGNAMUL` relocates several island regions (Jeju, Ulleung, Dokdo) the way
  Kakao's maps draw them. `WCONGNAMUL` does not — it only applies the 2.5×
  scale, matching the reference implementation.

Congnamul results are returned as integers; every other system returns floats.

## API

```python
transform(x, y, from_system, to_system) -> tuple[float, float]
supported_systems() -> list[str]
```

`transform` raises `ValueError` for an unknown system name and `TypeError` if
the coordinates are not numbers.

The original keyword-only form is kept as an alias:

```python
from koreacoord import get_trans_coord

x, y = get_trans_coord(x=126.9876757, y=37.5611523,
                       input="WGS84", output="WCONGNAMUL")
```

## Accuracy

Measured by the test suite, across seven points from Mokpo to Dokdo:

| | Agreement |
| --- | --- |
| TM projection vs. [pyproj](https://pyproj4.github.io/pyproj/) | within 0.04 mm |
| Round trip within one datum | within 0.03 mm |
| Round trip across datums | a few mm |
| Congnamul grid | ±0.2 m (the grid is integer) |

These are numbers about *self-consistency*, not about surveying truth. The
datum shift is a 7-parameter Molodensky-Badekas approximation, so against
official Korean survey data the realistic expectation is **metre-level**
agreement, not centimetres.

---

# 한국어

## 설치

```bash
pip install koreacoord
```

## 사용법

```python
from koreacoord import transform

# 서울시청, WGS84 -> 카카오 콩나물 좌표
x, y = transform(126.9876757, 37.5611523, "WGS84", "WCONGNAMUL")

# 문자열 대신 열거형을 써도 됩니다 (IDE 자동완성이 됩니다)
from koreacoord import CoordSystem as CS

x, y = transform(126.9876757, 37.5611523, CS.WGS84, CS.UTM)
```

축 순서는 항상 **x 먼저, y 나중**입니다. 경위도계는 경도→위도, 평면좌표계는
동거(easting)→북거(northing) 순서입니다.

## 지원 좌표계

| 이름 | 설명 | 측지계 |
| --- | --- | --- |
| `WGS84` | 경위도 | WGS84 |
| `BESSEL` | 경위도 | 베셀 1841 (도쿄측지계) |
| `TM` | 중부원점 TM | 베셀 1841 |
| `WTM` | 중부원점 TM | WGS84 |
| `KTM` | 경도 128° 원점 TM | 베셀 1841 |
| `WKTM` | 경도 128° 원점 TM | WGS84 |
| `UTM` | UTM **52N 존 전용** | WGS84 |
| `CONGNAMUL` | 카카오(다음) 지도 좌표 | 베셀 1841 |
| `WCONGNAMUL` | 카카오(다음) 지도 좌표 | WGS84 |

## 사용 범위

**이 라이브러리는 한국 전용입니다.** 투영 원점과 측지계 파라미터가 전부 한국
값으로 고정되어 있습니다.

- `UTM`은 **52N 존(중앙자오선 129°E)** 으로 고정입니다. 다른 존의 좌표를 넣으면
  오류 없이 틀린 값이 나옵니다.
- `BESSEL`은 한반도용 도쿄측지계 변환값을 쓰므로 일반적인 베셀 1841 변환이
  아닙니다.
- `CONGNAMUL`은 카카오 지도가 제주·울릉·독도를 옮겨 그리는 보정을 반영합니다.
  `WCONGNAMUL`은 이 보정 없이 2.5배 배율만 적용합니다 (원 구현과 동일).

콩나물 좌표는 정수로, 나머지는 실수로 반환됩니다.

## 정확도

목포부터 독도까지 7개 지점으로 측정한 값입니다.

| | 일치 수준 |
| --- | --- |
| TM 투영 vs [pyproj](https://pyproj4.github.io/pyproj/) | 0.04mm 이내 |
| 같은 측지계 내 왕복 변환 | 0.03mm 이내 |
| 측지계를 넘는 왕복 변환 | 수 mm |
| 콩나물 좌표 | ±0.2m (격자가 정수) |

이건 **자체 정합성** 수치이지 측량 성과와의 일치도가 아닙니다. 측지계 변환이
7-파라미터 Molodensky-Badekas 근사라서, 국토지리정보원 성과와 비교하면
센티미터가 아니라 **미터 단위**로 맞는다고 보는 게 현실적입니다.

## 라이선스

MIT
