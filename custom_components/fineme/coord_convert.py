"""Coordinate system conversion for Fineme GPS Tracker.

The Fineme API returns coordinates in BD09 (Baidu) system.
HA's default map (OpenStreetMap/Leaflet) uses WGS84.

Conversion chain: BD09 → GCJ02 → WGS84

Coordinate systems:
- WGS84: GPS standard, used by OpenStreetMap, international maps
- GCJ02: China national security offset (Mars coordinates), used by AMap/Tencent
- BD09:  Baidu further offset on top of GCJ02, used by Baidu Maps
"""

import math

# Constants
PI = math.pi
X_PI = PI * 3000.0 / 180.0
SEMI_MAJOR = 6378245.0          # Krasovsky ellipsoid semi-major axis
EE = 0.00669342162296594323     # Krasovsky ellipsoid eccentricity squared


def _transform_lat(lng: float, lat: float) -> float:
    """Internal latitude transform for GCJ02 offset."""
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) +
            20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) +
            40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) +
            320.0 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng: float, lat: float) -> float:
    """Internal longitude transform for GCJ02 offset."""
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) +
            20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) +
            40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) +
            300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def _out_of_china(lng: float, lat: float) -> bool:
    """Rough check if coordinates are outside China mainland."""
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def bd09_to_gcj02(bd_lng: float, bd_lat: float) -> tuple[float, float]:
    """Convert BD09 coordinates to GCJ02.

    Args:
        bd_lng: Baidu longitude
        bd_lat: Baidu latitude

    Returns:
        (gcj_lng, gcj_lat) tuple
    """
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * X_PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * X_PI)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return gcj_lng, gcj_lat


def gcj02_to_wgs84(gcj_lng: float, gcj_lat: float) -> tuple[float, float]:
    """Convert GCJ02 coordinates to WGS84.

    Args:
        gcj_lng: GCJ02 longitude (Mars coordinates)
        gcj_lat: GCJ02 latitude (Mars coordinates)

    Returns:
        (wgs_lng, wgs_lat) tuple
    """
    if _out_of_china(gcj_lng, gcj_lat):
        return gcj_lng, gcj_lat

    dlat = _transform_lat(gcj_lng - 105.0, gcj_lat - 35.0)
    dlng = _transform_lng(gcj_lng - 105.0, gcj_lat - 35.0)
    radlat = gcj_lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((SEMI_MAJOR * (1 - EE)) /
                              (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (SEMI_MAJOR / sqrtmagic *
                              math.cos(radlat) * PI)
    wgs_lat = gcj_lat - dlat
    wgs_lng = gcj_lng - dlng
    return wgs_lng, wgs_lat


def bd09_to_wgs84(bd_lng: float, bd_lat: float) -> tuple[float, float]:
    """Convert BD09 coordinates directly to WGS84.

    This is the main entry point for the Fineme integration,
    as the API returns BD09 and HA uses WGS84.

    Args:
        bd_lng: Baidu longitude (BD09)
        bd_lat: Baidu latitude (BD09)

    Returns:
        (wgs_lng, wgs_lat) tuple in WGS84
    """
    gcj_lng, gcj_lat = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj_lng, gcj_lat)


def wgs84_to_gcj02(wgs_lng: float, wgs_lat: float) -> tuple[float, float]:
    """Convert WGS84 coordinates to GCJ02 (for reference)."""
    if _out_of_china(wgs_lng, wgs_lat):
        return wgs_lng, wgs_lat

    dlat = _transform_lat(wgs_lng - 105.0, wgs_lat - 35.0)
    dlng = _transform_lng(wgs_lng - 105.0, wgs_lat - 35.0)
    radlat = wgs_lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((SEMI_MAJOR * (1 - EE)) /
                              (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (SEMI_MAJOR / sqrtmagic *
                              math.cos(radlat) * PI)
    gcj_lat = wgs_lat + dlat
    gcj_lng = wgs_lng + dlng
    return gcj_lng, gcj_lat


def gcj02_to_bd09(gcj_lng: float, gcj_lat: float) -> tuple[float, float]:
    """Convert GCJ02 coordinates to BD09 (for reference)."""
    z = math.sqrt(gcj_lng * gcj_lng + gcj_lat * gcj_lat) + \
        0.00002 * math.sin(gcj_lat * X_PI)
    theta = math.atan2(gcj_lat, gcj_lng) + 0.000003 * math.cos(gcj_lng * X_PI)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat
