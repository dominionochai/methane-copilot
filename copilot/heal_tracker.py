"""JSON repair cases with a strict, auditable status lifecycle."""
from __future__ import annotations

import argparse
import json
import logging
import math
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .dollar_engine import fetch_eia_henry_hub, lost_gas_commodity_value
except ImportError:
    from dollar_engine import fetch_eia_henry_hub, lost_gas_commodity_value

LOGGER = logging.getLogger(__name__)
DEFAULT_CASE_DIR = Path(__file__).with_name("cases")
CASE_ID_PATTERN = re.compile(r"^case-[0-9a-f]{12}$")
STATUSES = ("detected", "source_named", "billed", "repair_scheduled", "resolved")
LEGAL_TRANSITIONS = dict(zip(STATUSES, STATUSES[1:]))
MUTABLE_FIELDS = frozenset({"status", "detected_at", "latitude", "longitude", "estimated_flux_tpd", "facility_name", "component", "detection_id", "notes", "metadata", "repair_scheduled_at", "resolved_at", "resolution", "last_rescan_at", "rescan_match"})
DEFAULT_REPAIR_COSTS = {"flange": 500.0, "valve": 750.0, "generic": 1000.0}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _coordinate(value: float, name: str, low: float, high: float) -> float:
    result = float(value)
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f"{name} must be finite and between {low} and {high}")
    return result


def _flux(value: float) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("estimated_flux_tpd must be finite and non-negative")
    return result


def _serializable(value: Any, name: str) -> Any:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-serializable") from exc
    return value


def _case_path(case_id: str, case_dir: str | Path) -> Path:
    identifier = case_id[:-5] if case_id.endswith(".json") else case_id
    if not CASE_ID_PATTERN.fullmatch(identifier):
        raise ValueError("invalid case id; expected case-[12 hexadecimal characters]")
    root = Path(case_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = (root / f"{identifier}.json").resolve()
    if path.parent != root:
        raise ValueError("case path escapes case directory")
    return path


def _load(case_id: str, case_dir: str | Path) -> dict[str, Any]:
    path = _case_path(case_id, case_dir)
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("case JSON must be an object")
    return data


def _write(case: Mapping[str, Any], case_dir: str | Path) -> dict[str, Any]:
    path = _case_path(str(case["case_id"]), case_dir)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(case), handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return dict(case)


def create_case(latitude: float, longitude: float, estimated_flux_tpd: float, *, detected_at: str | None = None, facility_name: str | None = None, component: str | None = None, detection_id: str | None = None, notes: str = "", metadata: Mapping[str, Any] | None = None, case_dir: str | Path = DEFAULT_CASE_DIR, case_id: str | None = None) -> dict[str, Any]:
    """Create a case at the first exact lifecycle status, ``detected``."""
    identifier = case_id or f"case-{uuid.uuid4().hex[:12]}"
    _case_path(identifier, case_dir)
    detected = _timestamp(detected_at or _now(), "detected_at")
    metadata_value = dict(metadata or {})
    _serializable(metadata_value, "metadata")
    created = _now()
    case = {"case_id": identifier, "status": "detected", "created_at": created, "detected_at": detected, "latitude": _coordinate(latitude, "latitude", -90, 90), "longitude": _coordinate(longitude, "longitude", -180, 180), "estimated_flux_tpd": _flux(estimated_flux_tpd), "facility_name": facility_name, "component": component, "detection_id": detection_id, "notes": notes, "metadata": metadata_value, "history": [{"at": created, "event": "detected"}]}
    return _write(case, case_dir)


def _validate_field(name: str, value: Any) -> Any:
    if name == "latitude":
        return _coordinate(value, name, -90, 90)
    if name == "longitude":
        return _coordinate(value, name, -180, 180)
    if name == "estimated_flux_tpd":
        return _flux(value)
    if name.endswith("_at"):
        return _timestamp(value, name)
    if name == "metadata":
        return _serializable(value, name)
    return value


def update_case(case_id: str, updates: Mapping[str, Any] | None = None, *, case_dir: str | Path = DEFAULT_CASE_DIR, **fields: Any) -> dict[str, Any]:
    """Apply only whitelisted fields and one legal lifecycle transition."""
    changes = dict(updates or {})
    changes.update(fields)
    protected = {"case_id", "history", "created_at"} & set(changes)
    if protected:
        raise ValueError(f"immutable case fields: {', '.join(sorted(protected))}")
    unknown = set(changes) - MUTABLE_FIELDS
    if unknown:
        raise ValueError(f"unsupported case fields: {', '.join(sorted(unknown))}")
    case = _load(case_id, case_dir)
    current = case.get("status")
    if current not in STATUSES:
        raise ValueError("case has invalid status")
    for name in changes:
        changes[name] = _validate_field(name, changes[name])
    requested = changes.get("status", current)
    if requested not in STATUSES or (requested != current and LEGAL_TRANSITIONS.get(current) != requested):
        raise ValueError(f"illegal status transition: {current} -> {requested}")
    case.update(changes)
    case.setdefault("history", []).append({"at": _now(), "event": "updated", "fields": sorted(changes)})
    return _write(case, case_dir)


def resolve_case(case_id: str, *, resolution: str = "resolved after review", resolved_at: str | None = None, case_dir: str | Path = DEFAULT_CASE_DIR) -> dict[str, Any]:
    return update_case(case_id, {"status": "resolved", "resolution": resolution, "resolved_at": resolved_at or _now()}, case_dir=case_dir)


def list_open_cases(case_dir: str | Path = DEFAULT_CASE_DIR) -> list[dict[str, Any]]:
    """Skip malformed files individually and log their filenames."""
    folder = Path(case_dir)
    if not folder.exists():
        return []
    results = []
    for path in sorted(folder.glob("*.json")):
        try:
            case = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(case, dict) and case.get("status") != "resolved":
                results.append(case)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            LOGGER.warning("Skipping bad case file %s: %s", path.name, exc)
    return sorted(results, key=lambda item: item.get("detected_at", ""))


def suggest_repair_playbook(case: Mapping[str, Any], *, price_usd_per_mmbtu: float | None = None, repair_costs: Mapping[str, float] | None = None) -> dict[str, Any]:
    """Prefer explicit ``component`` over free text and expose assumptions."""
    costs = dict(DEFAULT_REPAIR_COSTS)
    costs.update(repair_costs or {})
    for name, value in costs.items():
        costs[name] = _flux(value)
    component = str(case.get("component") or "").strip().lower()
    text = component or " ".join(str(case.get(key, "")) for key in ("notes", "facility_name")).lower()
    if "flange" in text:
        action, cost_key = "isolate, torque bolts, then reseal if needed", "flange"
    elif "valve" in text:
        action, cost_key = "inspect stem and replace packing", "valve"
    else:
        action, cost_key = "inspect, soap-test, and confirm component", "generic"
    price = fetch_eia_henry_hub() if price_usd_per_mmbtu is None else {"price": _flux(price_usd_per_mmbtu), "source": "caller"}
    daily_burn = lost_gas_commodity_value(_flux(case.get("estimated_flux_tpd", 0)), price_usd_per_mmbtu=float(price["price"]))
    repair_cost = costs[cost_key]
    return {"playbook": action, "estimated_repair_cost_usd": repair_cost, "estimated_daily_burn_usd": daily_burn, "payback_days": repair_cost / daily_burn if daily_burn else None, "cost_table": costs, "assumptions": ["repair costs are configurable planning estimates, not quotes", "52 MMBtu/metric-ton CH4 HHV is an engineering screening assumption", "Henry Hub price is live or a dated fallback assumption"], "price_source": price.get("source"), "disclaimer": "Verify isolation, safety, scope, and actual costs before work."}


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians((lon2 - lon1 + 180.0) % 360.0 - 180.0)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6_371_000.0 * math.asin(math.sqrt(min(1.0, a)))


def rescan_check(case_id: str, later_detections: Iterable[Mapping[str, Any]] | None, *, rescan_at: str | None = None, coordinate_tolerance_m: float = 100.0, case_dir: str | Path = DEFAULT_CASE_DIR) -> dict[str, Any]:
    """Record a required rescan and resolve only an unrepeated scheduled case."""
    if rescan_at is None:
        raise ValueError("rescan_at is required")
    scan_time = _timestamp(rescan_at, "rescan_at")
    case = _load(case_id, case_dir)
    if case.get("status") == "resolved":
        return case
    original = _timestamp(case["detected_at"], "detected_at")
    matched = False
    for detection in later_detections or []:
        stamp = detection.get("detected_at", detection.get("scene_timestamp", detection.get("timestamp")))
        if stamp is None or _timestamp(stamp, "detection timestamp") <= original:
            continue
        lat = detection.get("latitude", detection.get("lat"))
        lon = detection.get("longitude", detection.get("lon"))
        if lat is None or lon is None:
            continue
        if _distance_m(float(case["latitude"]), float(case["longitude"]), float(lat), float(lon)) <= _flux(coordinate_tolerance_m):
            matched = True
            break
    changes: dict[str, Any] = {"last_rescan_at": scan_time, "rescan_match": matched}
    if not matched and case.get("status") == "repair_scheduled":
        changes.update({"status": "resolved", "resolved_at": scan_time, "resolution": "later rescan found no matching detection"})
    return update_case(case_id, changes, case_dir=case_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path)
    args = parser.parse_args()
    folder = args.case_dir or Path(tempfile.mkdtemp())
    case = create_case(29.7604, -95.3698, 2.4, component="valve", case_dir=folder)
    print(json.dumps({"created": case, "advice": suggest_repair_playbook(case, price_usd_per_mmbtu=3.0)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
