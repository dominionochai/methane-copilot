"""Validated, first-order wind-aware methane source screening."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

LOGGER = logging.getLogger(__name__)
EARTH_RADIUS_M = 6_371_000.0
UNCERTAINTY_DISCLAIMER = "Heuristic screening only; confirm any facility attribution with local data, a suitable dispersion model, and field investigation."


def _coord(value: Any, name: str, low: float, high: float) -> float:
    result = float(value)
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f"{name} must be finite and between {low} and {high}")
    return result


def _wind(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _time(value: Any) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class WindRecord:
    timestamp: datetime
    latitude: float
    longitude: float
    u_m_s: float
    v_m_s: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _time(self.timestamp))
        object.__setattr__(self, "latitude", _coord(self.latitude, "latitude", -90, 90))
        object.__setattr__(self, "longitude", _coord(self.longitude, "longitude", -180, 180))
        object.__setattr__(self, "u_m_s", _wind(self.u_m_s, "u_m_s"))
        object.__setattr__(self, "v_m_s", _wind(self.v_m_s, "v_m_s"))


def _record(row: Mapping[str, Any]) -> WindRecord:
    def get(*names: str) -> Any:
        for name in names:
            if name in row:
                return row[name]
        return None
    values = (get("timestamp", "time", "datetime"), get("latitude", "lat"), get("longitude", "lon", "lng"), get("u_m_s", "u10", "u"), get("v_m_s", "v10", "v"))
    if any(value is None for value in values):
        raise ValueError("wind records need timestamp, latitude, longitude, u, and v")
    return WindRecord(*values)


def load_wind_csv(path: str | os.PathLike[str]) -> list[WindRecord]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [_record(row) for row in csv.DictReader(handle)]


def load_wind_config(path: str | os.PathLike[str]) -> list[WindRecord]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    records = data.get("records", []) if isinstance(data, Mapping) else data
    if not isinstance(records, list):
        raise ValueError("wind config must be a JSON list or {records: [...]}")
    return [_record(row) for row in records]


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1, lat2 = _coord(lat1, "lat1", -90, 90), _coord(lat2, "lat2", -90, 90)
    lon1, lon2 = _coord(lon1, "lon1", -180, 180), _coord(lon2, "lon2", -180, 180)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    delta_lon = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    a = math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, a)))


def interpolate_wind(records: Iterable[WindRecord | Mapping[str, Any]], latitude: float, longitude: float, timestamp: str | datetime) -> dict[str, float]:
    """Inverse-distance/time interpolation with validated finite inputs."""
    lat, lon, target = _coord(latitude, "latitude", -90, 90), _coord(longitude, "longitude", -180, 180), _time(timestamp)
    values = [item if isinstance(item, WindRecord) else _record(item) for item in records]
    if not values:
        raise ValueError("at least one wind record is required")
    total = total_u = total_v = 0.0
    for item in values:
        distance_km = _distance_m(lat, lon, item.latitude, item.longitude) / 1000.0
        hours = abs((item.timestamp - target).total_seconds()) / 3600.0
        weight = 1.0 / ((1.0 + distance_km) * (1.0 + hours))
        total += weight
        total_u += weight * item.u_m_s
        total_v += weight * item.v_m_s
    u, v = total_u / total, total_v / total
    return {"u_m_s": u, "v_m_s": v, "speed_m_s": math.hypot(u, v), "record_count": float(len(values))}


def fetch_era5_wind(plume: Mapping[str, Any]) -> tuple[list[WindRecord] | None, dict[str, str]]:
    """Attempt CDS retrieval; return logged, structured CDS/NetCDF errors."""
    if not (os.getenv("CDSAPI_KEY") or os.getenv("CDSAPI_URL") or Path("~/.cdsapirc").expanduser().exists()):
        reason = {"code": "not_configured", "message": "ERA5 skipped: CDS API is not configured"}
        LOGGER.info(reason["message"])
        return None, reason
    try:
        import cdsapi
    except ImportError:
        reason = {"code": "dependency_unavailable", "message": "ERA5 unavailable: optional cdsapi is not installed"}
        LOGGER.warning(reason["message"])
        return None, reason
    centroid = plume.get("centroid") or plume.get("georeferenced_centroid")
    try:
        lat = _coord(centroid["latitude"], "latitude", -90, 90)
        lon = _coord(centroid["longitude"], "longitude", -180, 180)
        observed = _time(plume["scene_timestamp"])
    except (KeyError, TypeError, ValueError) as exc:
        reason = {"code": "invalid_plume", "message": f"ERA5 unavailable: {type(exc).__name__}"}
        LOGGER.warning(reason["message"])
        return None, reason
    fd, filename = tempfile.mkstemp(suffix=".nc")
    os.close(fd)
    target = Path(filename)
    try:
        options: dict[str, Any] = {"quiet": True}
        if os.getenv("CDSAPI_URL"):
            options["url"] = os.environ["CDSAPI_URL"]
        if os.getenv("CDSAPI_KEY"):
            options["key"] = os.environ["CDSAPI_KEY"]
        cdsapi.Client(**options).retrieve("reanalysis-era5-single-levels", {"product_type": "reanalysis", "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"], "year": f"{observed.year:04d}", "month": f"{observed.month:02d}", "day": f"{observed.day:02d}", "time": [f"{observed.hour:02d}:00"], "area": [lat + .25, lon - .25, lat - .25, lon + .25], "format": "netcdf"}, str(target))
        import xarray as xr
        with xr.open_dataset(target) as dataset:
            u_name, v_name = ("u10", "v10") if "u10" in dataset else ("10u", "10v")
            u = float(dataset[u_name].sel(latitude=lat, longitude=lon, method="nearest").sel(time=observed, method="nearest").item())
            v = float(dataset[v_name].sel(latitude=lat, longitude=lon, method="nearest").sel(time=observed, method="nearest").item())
        return [WindRecord(observed, lat, lon, u, v)], {"code": "cds_live", "message": "ERA5 wind retrieved"}
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        reason = {"code": "cds_or_netcdf_error", "message": f"ERA5 unavailable: {type(exc).__name__}"}
        LOGGER.warning(reason["message"])
        return None, reason
    finally:
        target.unlink(missing_ok=True)


def propagate_backward(centroid: Mapping[str, Any], wind: Mapping[str, Any], plume_length_m: float = 1000.0) -> dict[str, float]:
    """Return an upwind point, wrapped longitude, and explicit travel_time_s."""
    lat, lon = _coord(centroid["latitude"], "latitude", -90, 90), _coord(centroid["longitude"], "longitude", -180, 180)
    if abs(lat) >= 89.999:
        raise ValueError("polar coordinates are unstable for longitude propagation")
    distance = float(plume_length_m)
    if not math.isfinite(distance) or distance < 0:
        raise ValueError("plume_length_m must be finite and non-negative")
    u, v = _wind(wind["u_m_s"], "u_m_s"), _wind(wind["v_m_s"], "v_m_s")
    speed = math.hypot(u, v)
    if speed == 0 or distance == 0:
        return {"latitude": lat, "longitude": lon, "travel_distance_m": 0.0, "travel_time_s": 0.0}
    east, north = -u / speed * distance, -v / speed * distance
    result_lat = lat + math.degrees(north / EARTH_RADIUS_M)
    result_lon = (lon + math.degrees(east / (EARTH_RADIUS_M * math.cos(math.radians(lat))))) % 360.0
    if result_lon > 180:
        result_lon -= 360.0
    return {"latitude": result_lat, "longitude": result_lon, "travel_distance_m": distance, "travel_time_s": distance / speed}


def _nearest(location: Mapping[str, float], facilities: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any] | None, float | None]:
    best: Mapping[str, Any] | None = None
    best_distance: float | None = None
    for facility in facilities:
        try:
            lat = facility.get("latitude", facility.get("lat"))
            lon = facility.get("longitude", facility.get("lon"))
            if lat is None or lon is None:
                continue
            distance = _distance_m(location["latitude"], location["longitude"], float(lat), float(lon))
        except (TypeError, ValueError):
            continue
        if best_distance is None or distance < best_distance:
            best, best_distance = facility, distance
    return best, best_distance


def attribute_source(plume: Mapping[str, Any], facilities: Sequence[Mapping[str, Any]] | None = None, *, wind_records: Iterable[WindRecord | Mapping[str, Any]] | None = None, wind_csv: str | os.PathLike[str] | None = None, wind_config: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Return candidate coordinates and a heuristic score, never an unverified facility.

    A catalogue-match score is clamp(.85*exp(-distance_m/5000), .05, .95).
    Without a match the score is .20 with wind and .05 with zero-wind fallback.
    """
    centroid = plume.get("centroid", plume.get("georeferenced_centroid"))
    if not isinstance(centroid, Mapping) or "scene_timestamp" not in plume:
        raise ValueError("plume needs scene_timestamp and a georeferenced centroid")
    lat, lon = _coord(centroid["latitude"], "latitude", -90, 90), _coord(centroid["longitude"], "longitude", -180, 180)
    if wind_records is not None:
        records, note = [x if isinstance(x, WindRecord) else _record(x) for x in wind_records], {"code": "caller_records", "message": "caller-supplied wind records"}
    elif wind_csv is not None:
        records, note = load_wind_csv(wind_csv), {"code": "csv", "message": str(wind_csv)}
    elif wind_config is not None:
        records, note = load_wind_config(wind_config), {"code": "json", "message": str(wind_config)}
    else:
        records, note = fetch_era5_wind(plume)
        records = records or []
    if records:
        wind = interpolate_wind(records, lat, lon, plume["scene_timestamp"])
        candidate = propagate_backward(centroid, wind, float(plume.get("plume_length_m", plume.get("mask_length_m", 1000.0))))
    else:
        wind = {"u_m_s": 0.0, "v_m_s": 0.0, "speed_m_s": 0.0, "record_count": 0.0}
        candidate = {"latitude": lat, "longitude": lon, "travel_distance_m": 0.0, "travel_time_s": 0.0}
    facility, distance = _nearest(candidate, facilities or [])
    score = max(.05, min(.95, .85 * math.exp(-distance / 5000))) if distance is not None else (.20 if records else .05)
    result: dict[str, Any] = {"candidate_source_coordinates": {"latitude": candidate["latitude"], "longitude": candidate["longitude"]}, "travel_distance_m": candidate["travel_distance_m"], "travel_time_s": candidate["travel_time_s"], "facility_distance_m": distance, "confidence_score": round(score, 3), "confidence_type": "heuristic_score", "wind": wind, "wind_source": note, "estimated_flux": plume.get("estimated_flux"), "uncertainty_disclaimer": UNCERTAINTY_DISCLAIMER}
    if facility is not None:
        result["matched_facility"] = dict(facility)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plume-json", type=Path)
    parser.add_argument("--wind-csv", type=Path)
    parser.add_argument("--wind-config", type=Path)
    args = parser.parse_args(argv)
    try:
        sample = {"centroid": {"latitude": 29.7604, "longitude": -95.3698}, "scene_timestamp": "2026-01-15T15:00:00Z", "estimated_flux": {"metric_tons_ch4_per_day": 2.4}, "plume_length_m": 1800}
        plume = json.loads(args.plume_json.read_text(encoding="utf-8")) if args.plume_json else sample
        print(json.dumps(attribute_source(plume, wind_csv=args.wind_csv, wind_config=args.wind_config), indent=2))
        return 0
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        print(f"source attribution error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
