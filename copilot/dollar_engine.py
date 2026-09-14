"""Pure methane-loss, climate-damage, and carbon-price calculations.

All public functions use metric tonnes CH4, MMBtu, tonnes CO2e, and USD.
Constants are explicit assumptions, not financial advice or project accounting.
"""
from __future__ import annotations
import math
import os

DEFAULT_EIA_HENRY_HUB_PRICE_USD_PER_MMBTU = 3.00
"""Documented offline/default Henry Hub price in USD per MMBtu."""
DEFAULT_MMBTU_PER_METRIC_TON_CH4 = 52.0
"""Approximate higher-heating-value energy content per metric tonne CH4."""
EPA_SOCIAL_COST_METHANE_USD_PER_METRIC_TON = 1500.0
"""Illustrative EPA 2023 SC-CH4 central assumption, 2020 USD/metric tonne."""
DEFAULT_METHANE_GWP100 = 28.0

def _valid(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0: raise ValueError(f"{name} must be finite and non-negative")
    return result

def fetch_eia_henry_hub(api_key: str | None = None, *, fallback: float = DEFAULT_EIA_HENRY_HUB_PRICE_USD_PER_MMBTU, timeout_seconds: float = 10.0) -> float:
    """Fetch EIA API v2 series RNGWHHD, falling back if key/dependency/network/value is absent."""
    key = api_key or os.getenv("EIA_API_KEY"); fallback = _valid(fallback, "fallback")
    if not key: return fallback
    try:
        import requests  # type: ignore[import-not-found]
        response = requests.get("https://api.eia.gov/v2/natural-gas/pri/fut/data/", params={"api_key": key, "frequency": "daily", "data[0]": "value", "facets[seriesId][]": "RNGWHHD", "sort[0][column]": "period", "sort[0][direction]": "desc", "length": 1}, timeout=timeout_seconds)
        response.raise_for_status(); rows = response.json().get("response", {}).get("data", [])
        if rows and rows[0].get("value") not in (None, ""): return _valid(float(rows[0]["value"]), "EIA price")
    except Exception: pass
    return fallback

def lost_gas_commodity_value(metric_tons_ch4: float, *, price_usd_per_mmbtu: float, mmbtu_per_metric_ton: float = DEFAULT_MMBTU_PER_METRIC_TON_CH4) -> float:
    """Gross lost-gas value = tonnes CH4 * MMBtu/tonne * EIA Henry Hub USD/MMBtu."""
    return _valid(metric_tons_ch4, "metric_tons_ch4") * _valid(mmbtu_per_metric_ton, "mmbtu_per_metric_ton") * _valid(price_usd_per_mmbtu, "price_usd_per_mmbtu")

def climate_damage_value(metric_tons_ch4: float, *, social_cost_usd_per_metric_ton: float = EPA_SOCIAL_COST_METHANE_USD_PER_METRIC_TON) -> float:
    """Climate damage using the documented EPA-style SC-CH4 USD/metric-ton assumption."""
    return _valid(metric_tons_ch4, "metric_tons_ch4") * _valid(social_cost_usd_per_metric_ton, "social_cost_usd_per_metric_ton")

def co2e_tons(metric_tons_ch4: float, *, gwp100: float = DEFAULT_METHANE_GWP100) -> float:
    """CO2e convention requested here: metric tonnes CH4 * 28 GWP100."""
    return _valid(metric_tons_ch4, "metric_tons_ch4") * _valid(gwp100, "gwp100")

def carbon_price_value(metric_tons_ch4: float, *, carbon_price_usd_per_ton_co2e: float, gwp100: float = DEFAULT_METHANE_GWP100) -> float:
    """Carbon-price value = CO2e tonnes * supplied USD per tonne CO2e."""
    return co2e_tons(metric_tons_ch4, gwp100=gwp100) * _valid(carbon_price_usd_per_ton_co2e, "carbon_price_usd_per_ton_co2e")

def calculate_impact(metric_tons_ch4: float, *, price_usd_per_mmbtu: float | None = None, carbon_price_usd_per_ton_co2e: float = 0.0, mmbtu_per_metric_ton: float = DEFAULT_MMBTU_PER_METRIC_TON_CH4, social_cost_usd_per_metric_ton: float = EPA_SOCIAL_COST_METHANE_USD_PER_METRIC_TON, gwp100: float = DEFAULT_METHANE_GWP100) -> dict[str, float]:
    """Compose commodity value, CO2e, climate damage, and carbon-price value."""
    tons = _valid(metric_tons_ch4, "metric_tons_ch4"); price = fetch_eia_henry_hub() if price_usd_per_mmbtu is None else _valid(price_usd_per_mmbtu, "price_usd_per_mmbtu")
    return {"metric_tons_ch4": tons, "mmbtu": tons * mmbtu_per_metric_ton, "henry_hub_usd_per_mmbtu": price, "lost_gas_commodity_usd": lost_gas_commodity_value(tons, price_usd_per_mmbtu=price, mmbtu_per_metric_ton=mmbtu_per_metric_ton), "co2e_tons": co2e_tons(tons, gwp100=gwp100), "climate_damage_usd": climate_damage_value(tons, social_cost_usd_per_metric_ton=social_cost_usd_per_metric_ton), "carbon_price_usd": carbon_price_value(tons, carbon_price_usd_per_ton_co2e=carbon_price_usd_per_ton_co2e, gwp100=gwp100)}

if __name__ == "__main__":
    import json; print(json.dumps(calculate_impact(2.4, carbon_price_usd_per_ton_co2e=50), indent=2))
