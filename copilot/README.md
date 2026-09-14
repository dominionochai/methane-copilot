# Methane Copilot decision layer

`copilot/` is an offline-first decision layer above UNEP MARS-S2L. It turns methane-plume detections into screening attribution, value/damage estimates, repair workflows, and a deliberately local carbon-credit registry demo.

## Carbon-credit screening

`credit_mint.py` is dependency-free and separates pure math from persistence:

```bash
python copilot/credit_mint.py demo
pytest copilot/tests/test_credit_mint.py
python -m py_compile copilot/credit_mint.py
```

The canonical demo is **12.4 metric tonnes CH4 × GWP100 28 = 347.2 tCO2e**, displayed as **347 whole credits**. At the illustrative **$15/tCO2e** price, gross revenue is **$5,208.00** and the documented **15% commission assumption** leaves **$4,426.80 net**. The UI and CLI show an illustrative **$7–$25/tCO2e screening range**, informed by the [World Bank Carbon Pricing Dashboard](https://carbonpricingdashboard.worldbank.org/) and requiring project-specific market evidence before use.

GWP100 is intentionally held at 28 throughout this feature for consistency with the existing screening UI; see the [IPCC AR5 WGI technical summary](https://www.ipcc.ch/report/ar5/wg1/technical-summary/) for the source convention and record the assessment/vintage in production reporting. This is not a claim that one GWP value applies to every standard or vintage.

A batch may be created only from a heal case with `status: "resolved"`, a timezone-aware `resolved_at`, and a non-empty `resolution`. JSON writes use a same-directory temporary file, `fsync`, and `os.replace`. The local registry enforces only these legal one-step transitions:

```text
minted -> verified -> listed -> sold
```

`CreditRegistry` stores JSON under `copilot/credits/` by default and strictly validates IDs, finite numbers, timezone-aware ISO-8601 timestamps, payload fields, derived GWP math, and lifecycle statuses. Its statuses are internal workflow markers. **They do not mean a third-party registry has verified, listed, or sold a credit, and they do not establish additionality, permanence, ownership, eligibility, or compliance.**

## Existing modules

- **`source_attribution.py`** loads plume detections, optionally retrieves ERA5 wind through `cdsapi`, or reads local CSV/JSON wind data, propagates backward along the wind vector, and optionally ranks a supplied facility catalogue. It returns a screening disclaimer, not verified attribution.
- **`dollar_engine.py`** contains pure calculations for lost-gas commodity value, CO2e, EPA-style social cost of methane, and a caller-supplied carbon price. Live EIA lookup is lazy and the offline fallback is explicitly labeled.
- **`heal_tracker.py`** stores one JSON case per detection in `copilot/cases/`, enforces `detected -> source_named -> billed -> repair_scheduled -> resolved`, provides repair playbooks, and can resolve a scheduled case when a later rescan finds no matching detection. Writes are atomic and case IDs are path-safe.

## Dependencies and offline use

The copilot modules use the Python standard library on offline paths and target Python 3.12 or newer. `requests`, `cdsapi`, and the ERA5/NetCDF reader are optional integrations. No network service or credential is needed for offline tests. Model/data licensing remains separate from the repository's LGPL code; review the upstream CC BY-NC-SA terms before redistribution or commercial use.
