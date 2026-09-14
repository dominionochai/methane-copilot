"""Wind-aware, first-order attribution of a methane plume to an upwind source.

This is a screening decision layer above MARS-S2L, not a dispersion model or
regulatory attribution.  ERA5/CDS is optional; local CSV or JSON wind records
are supported with a documented zero-wind fallback.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

EARTH_RADIUS_M = 6_371_000.0
UNCERTAINTY_DISCLAIMER = ("Screening attribution only: wind interpolation, plume travel time, "
    "terrain, atmospheric stability, source multiplicity, and geolocation error are simplified. "
    "Confirm any facility attribution with local data and a suitable dispersion/field investigation.")

@dataclass(frozen=True)
class WindRecord:
    """A georeferenced wind observation; U is eastward and V is northward."""
    timestamp: datetime
    latitude: float
    longitude: float
    u_m_s: float
    v_m_s: float

def _time(value: Any) -> datetime:
    """Parse an ISO timestamp and normalize it to UTC."""
    result = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return (result if result.tzinfo else result.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)

def _record(value: Mapping[str, Any]) -> WindRecord:
    """Normalize common CSV/JSON field aliases into a WindRecord."""
    def get(*names: str) -> Any:
        for name in names:
            if name in value:
                return value[name]
        return None
    fields = (get("timestamp", "time", "datetime"), get("latitude", "lat"),
              get("longitude", "lon", "lng"), get("u_m_s", "u10", "u"),
              get("v_m_s", "v10", "v"))
    if any(item is None for item in fields):
        raise ValueError("wind records need timestamp, latitude, longitude, u and v")
    return WindRecord(_time(fields[0]), float(fields[1]), float(fields[2]), float(fields[3]), float(fields[4]))

def load_wind_csv(path: str | os.PathLike[str]) -> list[WindRecord]:
    """Load a CSV containing timestamp, latitude, longitude, u, and v columns."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [_record(row) for row in csv.DictReader(handle)]

def load_wind_config(path: str | os.PathLike[str]) -> list[WindRecord]:
    """Load a JSON list or an object containing a ``records`` list."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    data = data.get("records", []) if isinstance(data, Mapping) else data
    if not isinstance(data, list):
        raise ValueError("wind config must be a JSON list or {records: [...]}")
    return [_record(item) for item in data]

def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return haversine distance in metres."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))

def interpolate_wind(records: Iterable[WindRecord | Mapping[str, Any]], latitude: float,
                     longitude: float, timestamp: str | datetime) -> dict[str, float]:
    """Interpolate U/V with inverse distance in space and time.

    Weights are ``1 / ((1 + distance_km) * (1 + time_delta_hours))``.  This is
    intentionally transparent and stable for sparse local files; ERA5 records
    use the same interpolation contract.
    """
    target = _time(timestamp)
    values = [item if isinstance(item, WindRecord) else _record(item) for item in records]
    if not values:
        raise ValueError("at least one wind record is required")
    total = u = v = 0.0
    for item in values:
        distance_km = _distance_m(latitude, longitude, item.latitude, item.longitude) / 1000
        hours = abs((item.timestamp - target).total_seconds()) / 3600
        weight = 1 / ((1 + distance_km) * (1 + hours))
        total += weight; u += weight * item.u_m_s; v += weight * item.v_m_s
    u /= total; v /= total
    return {"u_m_s": u, "v_m_s": v, "speed_m_s": math.hypot(u, v), "record_count": float(len(values))}

def fetch_era5_wind(plume: Mapping[str, Any]) -> tuple[list[WindRecord] | None, str]:
    """Attempt CDS ERA5 when configured; otherwise return a clear fallback note.

    A configured ``cdsapi`` client downloads one NetCDF point/time request.
    ``xarray`` is optional for reading that response.  Any credential, network,
    dependency, or response problem returns ``None`` so CSV/JSON fallback can run.
    """
    configured = bool(os.getenv("CDSAPI_KEY") or os.getenv("CDSAPI_URL") or Path("~/.cdsapirc").expanduser().exists())
    if not configured:
        return None, "ERA5 skipped: no CDS API credentials/configuration found"
    try:
        import cdsapi  # type: ignore[import-not-found]
    except ImportError:
        return None, "ERA5 unavailable: install optional cdsapi; using local fallback"
    centroid = plume.get("centroid", plume.get("georeferenced_centroid"))
    if not isinstance(centroid, Mapping):
        return None, "ERA5 unavailable: plume centroid is not georeferenced"
    lat, lon = float(centroid["latitude"]), float(centroid["longitude"])
    observed = _time(plume["scene_timestamp"])
    target = Path(tempfile.mkstemp(suffix=".nc")[1])
    try:
        options: dict[str, Any] = {"quiet": True}
        if os.getenv("CDSAPI_URL"): options["url"] = os.environ["CDSAPI_URL"]
        if os.getenv("CDSAPI_KEY"): options["key"] = os.environ["CDSAPI_KEY"]
        cdsapi.Client(**options).retrieve("reanalysis-era5-single-levels", {
            "product_type": "reanalysis", "variable": ["10m_u_component_of_wind", "10m_v_component_of_wind"],
            "year": f"{observed.year:04d}", "month": f"{observed.month:02d}", "day": f"{observed.day:02d}",
            "time": [f"{observed.hour:02d}:00"], "area": [lat + .25, lon - .25, lat - .25, lon + .25], "format": "netcdf"
        }, str(target))
        try:
            import xarray as xr  # type: ignore[import-not-found]
        except ImportError:
            return None, "ERA5 downloaded but xarray is unavailable; using local fallback"
        with xr.open_dataset(target) as dataset:
            u_name, v_name = ("u10", "v10") if "u10" in dataset else ("10u", "10v")
            u = dataset[u_name].sel(latitude=lat, longitude=lon, method="nearest")
            v = dataset[v_name].sel(latitude=lat, longitude=lon, method="nearest")
            time_dim = "time" if "time" in u.dims else "valid_time"
            u_value = float(u.sel({time_dim: observed}, method="nearest").item())
            v_value = float(v.sel({time_dim: observed}, method="nearest").item())
        return [WindRecord(observed, lat, lon, u_value, v_value)], "ERA5 CDS"
    except Exception as exc:
        return None, f"ERA5 request failed ({type(exc).__name__}); using local fallback"
    finally:
        target.unlink(missing_ok=True)

def propagate_backward(centroid: Mapping[str, Any], wind: Mapping[str, float], plume_length_m: float = 1000.0) -> dict[str, float]:
    """Move the centroid backward along the wind vector by plume length.

    The default 1 km distance is only a screening assumption when MARS-S2L
    does not provide a georeferenced plume length.
    """
    lat, lon = float(centroid["latitude"]), float(centroid["longitude"])
    u, v = float(wind["u_m_s"]), float(wind["v_m_s"]); speed = math.hypot(u, v)
    distance = max(0.0, float(plume_length_m))
    if speed == 0: return {"latitude": lat, "longitude": lon, "travel_distance_m": 0.0}
    east, north = -u / speed * distance, -v / speed * distance
    return {"latitude": lat + math.degrees(north / EARTH_RADIUS_M),
            "longitude": lon + math.degrees(east / (EARTH_RADIUS_M * math.cos(math.radians(lat)))),
            "travel_distance_m": distance, "travel_time_s": distance / speed}

def _nearest(location: Mapping[str, float], facilities: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any] | None, float | None]:
    """Return nearest facility and distance in metres, ignoring incomplete rows."""
    best, best_distance = None, None
    for facility in facilities:
        lat = facility.get("latitude", facility.get("lat")); lon = facility.get("longitude", facility.get("lon"))
        if lat is None or lon is None: continue
        distance = _distance_m(location["latitude"], location["longitude"], float(lat), float(lon))
        if best_distance is None or distance < best_distance: best, best_distance = facility, distance
    return best, best_distance

def attribute_source(plume: Mapping[str, Any], facilities: Sequence[Mapping[str, Any]] | None = None,
                     wind_records: Iterable[WindRecord | Mapping[str, Any]] | None = None,
                     wind_csv: str | os.PathLike[str] | None = None,
                     wind_config: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Return likely upwind source coordinates, facility, confidence, and caveat.

    Required plume fields are ``scene_timestamp`` and a georeferenced
    ``centroid`` (latitude/longitude); ``estimated_flux`` is passed through.
    If no facility catalogue is supplied, no facility name is invented.
    """
    centroid = plume.get("centroid", plume.get("georeferenced_centroid"))
    if not isinstance(centroid, Mapping) or "scene_timestamp" not in plume:
        raise ValueError("plume needs scene_timestamp and a georeferenced centroid")
    note = ""
    if wind_records is not None:
        records = [x if isinstance(x, WindRecord) else _record(x) for x in wind_records]; note = "caller-supplied wind records"
    else:
        records, note = fetch_era5_wind(plume); records = records or []
        if not records and wind_csv: records, note = load_wind_csv(wind_csv), f"CSV fallback: {wind_csv}"
        if not records and wind_config: records, note = load_wind_config(wind_config), f"JSON fallback: {wind_config}"
    if records:
        wind = interpolate_wind(records, float(centroid["latitude"]), float(centroid["longitude"]), plume["scene_timestamp"])
        source = propagate_backward(centroid, wind, float(plume.get("plume_length_m", plume.get("mask_length_m", 1000))))
    else:
        wind = {"u_m_s": 0.0, "v_m_s": 0.0, "speed_m_s": 0.0, "record_count": 0.0}
        source = {"latitude": float(centroid["latitude"]), "longitude": float(centroid["longitude"]), "travel_distance_m": 0.0}
        note = note or "no ERA5 or local wind source; zero-wind fallback"
    facility, distance = _nearest(source, facilities or [])
    name = None if facility is None else str(facility.get("name", facility.get("id", "unnamed facility")))
    confidence = (max(.05, min(.95, .85 * math.exp(-distance / 5000))) if distance is not None else (.20 if records else .05))
    return {"likely_upwind_source_facility": name, "likely_source_coordinates": {"latitude": source["latitude"], "longitude": source["longitude"]},
            "facility_distance_m": distance, "confidence": round(confidence, 3), "wind": wind, "wind_source": note,
            "estimated_flux": plume.get("estimated_flux"), "uncertainty_disclaimer": UNCERTAINTY_DISCLAIMER}

def main() -> None:
    """Run the documented sample plume JSON demo."""
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--plume-json"); parser.add_argument("--wind-csv"); args = parser.parse_args()
    sample = {"centroid": {"latitude": 29.7604, "longitude": -95.3698}, "scene_timestamp": "2026-01-15T15:00:00Z", "estimated_flux": {"metric_tons_ch4_per_day": 2.4}, "plume_length_m": 1800}
    plume = json.loads(Path(args.plume_json).read_text(encoding="utf-8")) if args.plume_json else sample
    print(json.dumps(attribute_source(plume, wind_csv=args.wind_csv), indent=2))

if __name__ == "__main__": main()
