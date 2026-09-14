"""Pure methane-loss, climate-damage, and carbon-price calculations."""
from __future__ import annotations

import logging
import math
import os
from typing import Any

LOGGER = logging.getLogger(__name__)
DEFAULT_EIA_HENRY_HUB_PRICE_USD_PER_MMBTU = 3.0
MMBTU_PER_METRIC_TON_CH4_HHV = 52.0
"""Screening assumption: 52 MMBtu/metric-ton CH4 HHV; replace with project data when available."""
EPA2023_SC_CH4_2020USD = 1600.0
"""EPA 2023 SC-CH4: 1,600 USD/metric ton in 2020 USD at a 2% average discount rate.

Source: https://www.epa.gov/system/files/documents/2023-12/epa_scghg_2023_report_final.pdf
"""
DEFAULT_METHANE_GWP100 = 28.0


def _value(value: float, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return result


def fetch_eia_henry_hub(api_key: str | None = None, *, fallback: float = DEFAULT_EIA_HENRY_HUB_PRICE_USD_PER_MMBTU, timeout_seconds: float = 10.0) -> dict[str, Any]:
    """Return live EIA data or a logged structured fallback result."""
    timeout = float(timeout_seconds)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout_seconds must be finite and greater than zero")
    fallback_value = _value(fallback, "fallback")
    key = api_key or os.getenv("EIA_API_KEY")
    if not key:
        reason = "missing_api_key"
        LOGGER.warning("Using Henry Hub fallback: %s", reason)
        return {"price": fallback_value, "source": "fallback_constant", "period": None, "fallback_reason": reason}
    try:
        import requests
    except ImportError:
        reason = "requests_unavailable"
        LOGGER.warning("Using Henry Hub fallback: %s", reason)
        return {"price": fallback_value, "source": "fallback_constant", "period": None, "fallback_reason": reason}
    try:
        response = requests.get("https://api.eia.gov/v2/natural-gas/pri/fut/data/", params={"api_key": key, "frequency": "daily", "data[0]": "value", "facets[seriesId][]": "RNGWHHD", "sort[0][column]": "period", "sort[0][direction]": "desc", "length": 1}, timeout=timeout)
        response.raise_for_status()
        row = response.json()["response"]["data"][0]
        price = _value(row["value"], "EIA price")
        return {"price": price, "source": "eia_live", "period": row.get("period"), "fallback_reason": None}
    except requests.exceptions.RequestException as exc:
        reason = f"network_error:{type(exc).__name__}"
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        reason = f"invalid_response:{type(exc).__name__}"
    LOGGER.warning("Using Henry Hub fallback: %s", reason)
    return {"price": fallback_value, "source": "fallback_constant", "period": None, "fallback_reason": reason}


def lost_gas_commodity_value(metric_tons_ch4: float, *, price_usd_per_mmbtu: float, mmbtu_per_metric_ton: float = MMBTU_PER_METRIC_TON_CH4_HHV) -> float:
    """Return tonnes CH4 × assumed HHV MMBtu/tonne × USD/MMBtu."""
    return _value(metric_tons_ch4, "metric_tons_ch4") * _value(mmbtu_per_metric_ton, "mmbtu_per_metric_ton") * _value(price_usd_per_mmbtu, "price_usd_per_mmbtu")


def climate_damage_value(metric_tons_ch4: float, *, social_cost_usd_per_metric_ton: float = EPA2023_SC_CH4_2020USD) -> float:
    """Return a dated EPA SC-CH4 screening estimate in USD."""
    return _value(metric_tons_ch4, "metric_tons_ch4") * _value(social_cost_usd_per_metric_ton, "social_cost_usd_per_metric_ton")


def co2e_tons(metric_tons_ch4: float, *, gwp100: float = DEFAULT_METHANE_GWP100) -> float:
    """Convert tonnes CH4 to tonnes CO2e using the supplied GWP100 assumption."""
    return _value(metric_tons_ch4, "metric_tons_ch4") * _value(gwp100, "gwp100")


def carbon_price_value(metric_tons_ch4: float, *, carbon_price_usd_per_ton_co2e: float, gwp100: float = DEFAULT_METHANE_GWP100) -> float:
    """Return CO2e tonnes × supplied USD per tonne CO2e."""
    return co2e_tons(metric_tons_ch4, gwp100=gwp100) * _value(carbon_price_usd_per_ton_co2e, "carbon_price_usd_per_ton_co2e")


def calculate_impact(metric_tons_ch4: float, *, price_usd_per_mmbtu: float | None = None, carbon_price_usd_per_ton_co2e: float = 0.0, mmbtu_per_metric_ton: float = MMBTU_PER_METRIC_TON_CH4_HHV, social_cost_usd_per_metric_ton: float = EPA2023_SC_CH4_2020USD, gwp100: float = DEFAULT_METHANE_GWP100) -> dict[str, Any]:
    """Compose commodity, CO2e, climate-damage, and carbon-price values."""
    tons = _value(metric_tons_ch4, "metric_tons_ch4")
    fetched = fetch_eia_henry_hub() if price_usd_per_mmbtu is None else {"price": _value(price_usd_per_mmbtu, "price_usd_per_mmbtu"), "source": "caller", "period": None, "fallback_reason": None}
    price = float(fetched["price"])
    return {"metric_tons_ch4": tons, "mmbtu": tons * _value(mmbtu_per_metric_ton, "mmbtu_per_metric_ton"), "henry_hub_usd_per_mmbtu": price, "henry_hub_source": fetched["source"], "henry_hub_period": fetched["period"], "henry_hub_fallback_reason": fetched["fallback_reason"], "lost_gas_commodity_usd": lost_gas_commodity_value(tons, price_usd_per_mmbtu=price, mmbtu_per_metric_ton=mmbtu_per_metric_ton), "co2e_tons": co2e_tons(tons, gwp100=gwp100), "climate_damage_usd": climate_damage_value(tons, social_cost_usd_per_metric_ton=social_cost_usd_per_metric_ton), "carbon_price_usd": carbon_price_value(tons, carbon_price_usd_per_ton_co2e=carbon_price_usd_per_ton_co2e, gwp100=gwp100)}


if __name__ == "__main__":
    import json
    print(json.dumps(calculate_impact(2.4, carbon_price_usd_per_ton_co2e=50), indent=2))
