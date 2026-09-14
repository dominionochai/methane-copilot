# Methane Copilot decision layer

`copilot/` is a small, original decision layer that can sit above UNEP MARS-S2L. MARS-S2L supplies methane-plume detection (including a georeferenced mask/centroid, scene time, and estimated flux); these modules turn that detection into screening attribution, value/damage estimates, and a human-review repair workflow.

## Modules

- **`source_attribution.py`** loads a plume JSON detection, optionally retrieves ERA5 wind through `cdsapi` when configured, or reads wind from CSV/JSON, interpolates U/V at the detection time and location, propagates backward along the wind vector, and optionally ranks a supplied facility catalogue. It always returns a clear uncertainty disclaimer: this is a screening aid, not verified attribution.
- **`dollar_engine.py`** contains pure, unit-testable calculations for lost-gas commodity value, CO2e, EPA-style social cost of methane, and a caller-supplied carbon price. `fetch_eia_henry_hub()` lazily imports `requests` only when an EIA API request is actually attempted; without `EIA_API_KEY` it returns the documented fallback and provenance.
- **`heal_tracker.py`** stores one JSON case per detection in `copilot/cases/`, enforces the lifecycle below, provides explicit repair playbooks, compares estimated daily gas burn with a planning fix cost, and can resolve a scheduled case when a later rescan finds no matching detection. Writes are atomic and case IDs are path-safe.

## Dependencies and offline use

The copilot modules use the Python standard library on their offline paths. They target Python 3.12 or newer. `requests` is optional and is imported lazily only by the live EIA Henry Hub lookup. `cdsapi` and the ERA5/NetCDF reader used by `fetch_era5_wind()` are optional integrations; callers can instead provide local CSV/JSON wind data. `numpy` and `python-dotenv` are not dependencies of this decision layer and are not used by it. No network service or credential is needed for the offline tests.

## Case lifecycle

Cases move through this exact, ordered lifecycle:

```text
detected -> source_named -> billed -> repair_scheduled -> resolved
```

`update_case()` permits only one forward transition at a time. `rescan_check()` records the rescan timestamp and resolves a `repair_scheduled` case only when a later rescan has no matching detection within the configured distance tolerance.

## Economic assumptions and provenance

**ALL economic constants are dated assumptions, not universal facts.** Carry their source and vintage with any report, and replace them with project-specific values when available:

- EPA 2023 SC-CH4: the default social cost is **USD 1,600 per metric tonne CH4 (2020 USD, 2% average discount rate)**, from the [EPA 2023 SC-CH4 report](https://www.epa.gov/system/files/documents/2023-12/epa_scghg_2023_report_final.pdf).
- Henry Hub: the live value is the EIA Henry Hub daily series when an `EIA_API_KEY` is supplied; the offline fallback is **USD 3.00/MMBtu** and is explicitly labelled `fallback_constant` with reason `missing_api_key` (or the relevant live-request failure). Treat that fallback as a dated assumption and record the date/source used for production work.
- Energy conversion: **52 MMBtu per metric tonne CH4 HHV** is an engineering screening assumption; confirm it against the project’s gas composition and heating-value basis.
- Methane climate conversion: **GWP100 = 28** is a configured screening assumption; record the assessment/vintage with the result.
- Carbon price: `calculate_impact()` accepts the **carbon price in USD per tonne CO2e** from the caller. It is not a market quote; supply and record a dated policy, market, or project source.

The engine returns Henry Hub source, period, and fallback reason alongside calculated values so downstream reports can preserve this provenance.

## Licensing and attribution

The code in this directory is the user’s original decision layer and is covered by the repository’s LGPL terms. The MARS-S2L code is a separate upstream component distributed under LGPL. **MARS-S2L models and data carry separate CC BY-NC-SA terms beyond the LGPL code**; review and comply with those model/data terms before redistribution or commercial use. Attribution is a screening aid and must be validated with appropriate meteorology, local facility data, safety controls, and field confirmation before operational action.

## Quick examples

```bash
python copilot/source_attribution.py
python copilot/dollar_engine.py
python copilot/heal_tracker.py
pytest copilot/tests
```

All code assumes explicit units: metric tonnes CH4, MMBtu, metres/second, and US dollars; see function docstrings for conventions and defaults.
