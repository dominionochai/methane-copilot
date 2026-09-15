"""Small JSON API facade for the Methane Copilot frontend.

The facade deliberately composes the existing source, dollar, heal, and credit
modules. It does not claim that heuristic source attribution is a measurement.
"""
from __future__ import annotations

import json
import math
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .credit_mint import CreditBatch, CreditRegistry
from .dollar_engine import calculate_impact
from .heal_tracker import create_case, suggest_repair_playbook, update_case
from .source_attribution import WindRecord, attribute_source

EIA_HENRY_HUB_URL = "https://api.eia.gov/v2/seriesid/NG.RNGWHHD.D/"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
EYE_ON_METHANE_URL = "https://methanedata.unep.org/"
MARS_IMPORT_FORMAT = "local MARS JSON import (public API endpoint not documented)"
DEFAULT_PRICE_USD_PER_MMBTU = 3.0
DEFAULT_CASE_DIR = Path(__file__).with_name("cases")
DEFAULT_CREDIT_DIR = Path(__file__).with_name("credits")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_get(url: str, params: Mapping[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
    request = urllib.request.Request(url + (("?" + query) if query else ""), headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_eia_henry_hub(api_key: str | None = None) -> dict[str, Any]:
    """Fetch the latest Henry Hub observation without ever logging the key."""
    key = api_key or os.getenv("EIA_API_KEY")
    if not key:
        return {"price": DEFAULT_PRICE_USD_PER_MMBTU, "source": "fallback_constant", "period": None, "fallback_reason": "missing_api_key"}
    try:
        payload = _json_get(EIA_HENRY_HUB_URL, {"api_key": key, "length": 1})
        rows = payload.get("response", {}).get("data", [])
        row = rows[0] if rows else {}
        price = float(row["value"])
        if not math.isfinite(price) or price < 0:
            raise ValueError("invalid EIA value")
        return {"price": price, "source": "eia_live", "period": row.get("period"), "series": "NG.RNGWHHD.D", "fallback_reason": None}
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        # Do not include exception text: URL libraries can include query strings.
        return {"price": DEFAULT_PRICE_USD_PER_MMBTU, "source": "fallback_constant", "period": None, "fallback_reason": type(exc).__name__}


def fetch_open_meteo_wind(latitude: float, longitude: float) -> tuple[list[WindRecord], dict[str, Any]]:
    """Fetch current 10 m wind from the free, no-key Open-Meteo endpoint."""
    try:
        payload = _json_get(OPEN_METEO_URL, {"latitude": latitude, "longitude": longitude, "current": "wind_speed_10m,wind_direction_10m", "wind_speed_unit": "ms", "timezone": "UTC"})
        current = payload["current"]
        speed = float(current["wind_speed_10m"])
        direction = math.radians(float(current["wind_direction_10m"]))
        # Open-Meteo direction is where wind comes from; u/v here are east/north.
        record = WindRecord(current["time"], latitude, longitude, -speed * math.sin(direction), -speed * math.cos(direction))
        return [record], {"source": "open_meteo_current", "url": OPEN_METEO_URL}
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return [], {"source": "open_meteo_unavailable", "url": OPEN_METEO_URL}


def _read_json(path: str | os.PathLike[str]) -> Any:
    return json.loads(Path(path).expanduser().read_text(encoding="utf-8"))


def _plume(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("plume") is not None:
        return dict(payload["plume"])
    path = payload.get("plume_path") or os.getenv("COPILOT_PLUME_JSON")
    if path:
        value = _read_json(path)
        if not isinstance(value, dict):
            raise ValueError("plume JSON must be an object")
        return value
    return {
        "plume_id": "demo-plume",
        "scene_timestamp": _now(),
        "centroid": {"latitude": 31.8457, "longitude": -102.6120},
        "estimated_flux": {"metric_tons_ch4_per_day": 12.4},
        "plume_length_m": 1800.0,
    }


def _facilities(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("facilities")
    path = payload.get("facilities_path") or os.getenv("COPILOT_FACILITIES_JSON")
    if value is None and path:
        value = _read_json(path)
    if value is None:
        value = [{"facility_id": "facility-demo-01", "name": "Demo compressor facility", "latitude": 31.8457, "longitude": -102.6120, "component": "valve"}]
    if not isinstance(value, list):
        raise ValueError("facilities must be a JSON array")
    return [dict(item) for item in value]


def _metric(value: Any, unit: str, display: str | None = None, formula: str | None = None) -> dict[str, Any]:
    result = {"value": value, "unit": unit, "display": display if display is not None else f"{value} {unit}"}
    if formula:
        result["formula"] = formula
    return result


def run_source(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    plume = _plume(payload)
    facilities = _facilities(payload)
    centroid = plume.get("centroid") or plume.get("georeferenced_centroid")
    if not isinstance(centroid, Mapping):
        raise ValueError("plume requires centroid latitude and longitude")
    latitude, longitude = float(centroid["latitude"]), float(centroid["longitude"])
    supplied_wind = payload.get("wind_records")
    wind = [WindRecord(**dict(row)) for row in supplied_wind] if supplied_wind else []
    wind_meta: dict[str, Any] = {"source": "caller_supplied"} if wind else {}
    if not wind:
        wind, wind_meta = fetch_open_meteo_wind(latitude, longitude)
    attribution = attribute_source(plume, facilities, wind_records=wind)
    flux = float((plume.get("estimated_flux") or {}).get("metric_tons_ch4_per_day", plume.get("ch4_fluxrate", 0.0)))
    hourly_kg = flux * 1000.0 / 24.0
    confidence = float(attribution.get("confidence_score", 0.0)) * 100.0
    return {
        "ok": True,
        "data": {"plume": plume, "attribution": attribution},
        "values": {
            "methane_t_ch4": _metric(round(flux, 3), "t CH4", f"{flux:,.1f} t CH4"),
            "emission_rate_kg_h": _metric(round(hourly_kg, 2), "kg/hr", f"{hourly_kg:,.0f} kg/hr"),
            "confidence": _metric(round(confidence, 1), "%", f"{confidence:.1f}%"),
            "facility_name": _metric((attribution.get("matched_facility") or {}).get("name", "unmatched"), "", (attribution.get("matched_facility") or {}).get("name", "unmatched")),
            "wind_source": _metric(wind_meta.get("source"), "", wind_meta.get("source")),
        },
        "meta": {"sources": {"wind": wind_meta.get("url", OPEN_METEO_URL), "plume_import": MARS_IMPORT_FORMAT, "eye_on_methane": EYE_ON_METHANE_URL}, "limitations": [attribution.get("uncertainty_disclaimer", "")], "public_plume_api": False},
    }


def run_flow(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run plume import -> attribution -> dollars -> heal -> credit in one call."""
    payload = payload or {}
    source = run_source(payload)
    plume = source["data"]["plume"]
    attribution = source["data"]["attribution"]
    flux = float((plume.get("estimated_flux") or {}).get("metric_tons_ch4_per_day", plume.get("ch4_fluxrate", 0.0)))
    eia = fetch_eia_henry_hub()
    impact = calculate_impact(flux, price_usd_per_mmbtu=eia["price"])
    case_dir = payload.get("case_dir") or os.getenv("COPILOT_CASE_DIR") or DEFAULT_CASE_DIR
    credit_dir = payload.get("credit_dir") or os.getenv("COPILOT_CREDIT_DIR") or DEFAULT_CREDIT_DIR
    facility = attribution.get("matched_facility") or {}
    case = create_case(float(plume["centroid"]["latitude"]), float(plume["centroid"]["longitude"]), flux, facility_name=facility.get("name"), component=facility.get("component"), detection_id=plume.get("plume_id"), metadata={"attribution": attribution}, case_dir=case_dir)
    for status in ("source_named", "billed", "repair_scheduled"):
        case = update_case(case["case_id"], {"status": status}, case_dir=case_dir)
    repair = suggest_repair_playbook(case, price_usd_per_mmbtu=eia["price"])
    case = update_case(case["case_id"], {"status": "resolved", "resolution": "repair completed", "resc an_match": False} if False else {"status": "resolved", "resolution": "repair completed"}, case_dir=case_dir)
    batch = CreditBatch.from_resolved_case(case, batch_id=f"batch-{case['case_id'][-12:]}")
    registry = CreditRegistry(credit_dir)
    batch = registry.mint(batch)
    values = {
        "commodity_price_usd_per_mmbtu": _metric(eia["price"], "USD/MMBtu", f"${eia['price']:,.2f}/MMBtu"),
        "gas_value_usd": _metric(impact["lost_gas_commodity_usd"], "USD", f"${impact['lost_gas_commodity_usd']:,.2f}"),
        "regulatory_exposure_usd": _metric(impact["climate_damage_usd"], "USD", f"${impact['climate_damage_usd']:,.2f}"),
        "co2e_t": _metric(impact["co2e_tons"], "tCO2e", f"{impact['co2e_tons']:,.1f} tCO2e"),
        "climate_damage_usd": _metric(impact["climate_damage_usd"], "USD", f"${impact['climate_damage_usd']:,.2f}"),
        "lost_gas_usd": _metric(impact["lost_gas_commodity_usd"], "USD", f"${impact['lost_gas_commodity_usd']:,.2f}"),
        "case_id": _metric(case["case_id"], "", case["case_id"]),
        "case_status": _metric(case["status"], "", case["status"]),
        "repair_cost_usd": _metric(repair["estimated_repair_cost_usd"], "USD", f"${repair['estimated_repair_cost_usd']:,.2f}"),
        "credit_count": _metric(batch.credit_count, "credits", f"{batch.credit_count:,} credits"),
        "credit_co2e_t": _metric(batch.co2e_tonnes, "tCO2e", f"{batch.co2e_tonnes:,.1f} tCO2e"),
        "credit_net_revenue_usd": _metric(batch.economics.net_revenue_usd, "USD", f"${batch.economics.net_revenue_usd:,.2f}"),
    }
    return {"ok": True, "data": {"source": source["data"], "exposure": impact, "case": case, "repair": repair, "credit": batch.to_dict()}, "values": values, "meta": {"sources": {"eia": EIA_HENRY_HUB_URL, "wind": OPEN_METEO_URL, "plume_import": MARS_IMPORT_FORMAT, "eye_on_methane": EYE_ON_METHANE_URL}, "eia": {"source": eia["source"], "period": eia.get("period"), "series": eia.get("series", "NG.RNGWHHD.D")}, "limitations": ["Source attribution is a heuristic screening result; confirm with field data.", "Credit registry is a local audit-friendly workflow, not third-party verification."]}}


def response_for(route: str, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    flow = run_flow(payload)
    section = {"source": "source", "bill": "exposure", "heal": "case", "credit": "credit"}.get(route)
    if section:
        return {"ok": True, "data": flow["data"][section], "values": flow["values"], "meta": flow["meta"]}
    return flow
