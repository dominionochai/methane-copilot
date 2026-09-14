"""JSON repair cases and lightweight methane-leak repair heuristics.

Runtime cases live in ``copilot/cases/`` by default.  The demo uses a temporary
folder, so generated case files are not committed to the repository.
"""
from __future__ import annotations
import argparse
import json
import math
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
try:
    from .dollar_engine import fetch_eia_henry_hub, lost_gas_commodity_value
except ImportError:  # direct script execution
    from dollar_engine import fetch_eia_henry_hub, lost_gas_commodity_value

DEFAULT_CASE_DIR = Path(__file__).with_name("cases")
EARTH_RADIUS_M = 6_371_000.0

def _now() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def _path(case_id: str, case_dir: str | Path) -> Path:
    if Path(case_id).name != case_id or not case_id.endswith(".json") and "/" in case_id: raise ValueError("invalid case id")
    return Path(case_dir) / (case_id if case_id.endswith(".json") else case_id + ".json")
def _load(case_id: str, case_dir: str | Path) -> dict[str, Any]:
    path = _path(case_id, case_dir)
    if not path.exists(): raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))
def _write(case: Mapping[str, Any], case_dir: str | Path) -> dict[str, Any]:
    folder = Path(case_dir); folder.mkdir(parents=True, exist_ok=True)
    _path(str(case["case_id"]), folder).write_text(json.dumps(case, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dict(case)

def create_case(latitude: float, longitude: float, estimated_flux_tpd: float, *, detected_at: str | None = None, facility_name: str | None = None, component: str | None = None, detection_id: str | None = None, notes: str = "", metadata: Mapping[str, Any] | None = None, case_dir: str | Path = DEFAULT_CASE_DIR, case_id: str | None = None) -> dict[str, Any]:
    """Create an open JSON case from a georeferenced detection."""
    identifier = case_id or "case-" + uuid.uuid4().hex[:12]
    now = _now(); case = {"case_id": identifier, "status": "open", "created_at": now, "detected_at": detected_at or now, "latitude": float(latitude), "longitude": float(longitude), "estimated_flux_tpd": float(estimated_flux_tpd), "facility_name": facility_name, "component": component, "detection_id": detection_id, "notes": notes, "metadata": dict(metadata or {}), "history": [{"at": now, "event": "created"}]}
    return _write(case, case_dir)

def update_case(case_id: str, updates: Mapping[str, Any] | None = None, *, case_dir: str | Path = DEFAULT_CASE_DIR, **fields: Any) -> dict[str, Any]:
    """Merge fields into a case and append an auditable history event."""
    case = _load(case_id, case_dir); changes = dict(updates or {}); changes.update(fields); changes.pop("case_id", None); case.update(changes); case.setdefault("history", []).append({"at": _now(), "event": "updated", "fields": sorted(changes)})
    return _write(case, case_dir)

def resolve_case(case_id: str, *, resolution: str = "resolved after review", resolved_at: str | None = None, case_dir: str | Path = DEFAULT_CASE_DIR) -> dict[str, Any]:
    """Mark a case resolved while preserving the reason and timestamp."""
    case = _load(case_id, case_dir); stamp = resolved_at or _now(); case.update({"status": "resolved", "resolved_at": stamp, "resolution": resolution}); case.setdefault("history", []).append({"at": stamp, "event": "resolved", "resolution": resolution}); return _write(case, case_dir)

def list_open_cases(case_dir: str | Path = DEFAULT_CASE_DIR) -> list[dict[str, Any]]:
    """List open JSON cases sorted by detection time."""
    folder = Path(case_dir)
    if not folder.exists(): return []
    cases = [json.loads(path.read_text(encoding="utf-8")) for path in folder.glob("*.json")]
    return sorted((case for case in cases if case.get("status") == "open"), key=lambda case: case.get("detected_at", ""))

def suggest_repair_playbook(case: Mapping[str, Any], *, price_usd_per_mmbtu: float | None = None) -> dict[str, Any]:
    """Suggest a human-review playbook and compare fix cost with daily burn.

    Heuristics are intentionally conservative: flange -> torque/reseal and
    valve -> replace packing. Costs are planning estimates, not quotations.
    """
    text = " ".join(str(case.get(key, "")) for key in ("component", "notes", "facility_name")).lower()
    if "flange" in text: action, fix_cost, rationale = "isolate, torque bolts, then reseal if needed", 500.0, "flange heuristic"
    elif "valve" in text: action, fix_cost, rationale = "inspect stem and replace packing", 750.0, "valve heuristic"
    else: action, fix_cost, rationale = "inspect, soap-test, and confirm component before repair", 1000.0, "generic inspection heuristic"
    price = fetch_eia_henry_hub() if price_usd_per_mmbtu is None else float(price_usd_per_mmbtu)
    daily_burn = lost_gas_commodity_value(float(case.get("estimated_flux_tpd", 0)), price_usd_per_mmbtu=price)
    return {"playbook": action, "rationale": rationale, "estimated_fix_cost_usd": fix_cost, "estimated_daily_burn_usd": daily_burn, "payback_days": fix_cost / daily_burn if daily_burn > 0 else None, "disclaimer": "Heuristic estimate; verify isolation, safety, scope, and actual costs before work."}

def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2); dp, dl = math.radians(lat2-lat1), math.radians(lon2-lon1); a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*EARTH_RADIUS_M*math.asin(math.sqrt(a))

def rescan_check(case_id: str, later_detections: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None, *, case_dir: str | Path = DEFAULT_CASE_DIR, coordinate_tolerance_m: float = 100.0) -> dict[str, Any]:
    """Resolve a case when no later detection is within the coordinate tolerance.

    A matching later detection leaves the case open and records the rescan.
    ``None`` or an empty iterable means the later scan found no matching plume.
    """
    case = _load(case_id, case_dir); detections = [] if later_detections is None else ([later_detections] if isinstance(later_detections, Mapping) else list(later_detections)); match = False
    for detection in detections:
        lat = detection.get("latitude", detection.get("lat")); lon = detection.get("longitude", detection.get("lon"))
        if lat is not None and lon is not None and _distance(float(case["latitude"]), float(case["longitude"]), float(lat), float(lon)) <= coordinate_tolerance_m: match = True; break
    case = update_case(case_id, {"last_rescan_at": _now(), "rescan_match": match}, case_dir=case_dir)
    if not match: case = resolve_case(case_id, resolution="later rescan found no detection at case coordinates", case_dir=case_dir)
    return case

def main() -> None:
    """Run an end-to-end create -> advise -> rescan demo in a temp folder."""
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--case-dir", type=Path); args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        folder = args.case_dir or Path(temporary); case = create_case(29.7604, -95.3698, 2.4, component="valve", notes="sample MARS-S2L detection", case_dir=folder); print(json.dumps({"created": case, "advice": suggest_repair_playbook(case, price_usd_per_mmbtu=3.0), "rescanned": rescan_check(case["case_id"], [], case_dir=folder)}, indent=2))

if __name__ == "__main__": main()
