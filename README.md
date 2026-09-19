# methane-copilot

This repository contains the MARS-S2L research code and the small integration facade used by the Stitch frontend. The facade composes the existing `copilot/source_attribution.py`, `copilot/dollar_engine.py`, `copilot/real_tracker.py`, and `copilot/credit_mint.py` modules; it does not replace their validation or disclaimers.

## Integration status and requirements

* **Required for the local end-to-end flow:** Python 3.12+ is required. The repository itself and the existing test/runtime dependencies are required. `EIA_API_KEY` is optional for offline fallback but required for a live Henry Hub price.
* **Optional:** `EIA_API_KEY` (runtime-only; never commit, print, or log it), a local MARS plume JSON file, a facilities JSON file, and the optional ERA5/Copernicus source used by the lower-level attribution module.
* Eye on Methane/MARS publishes data dictionaries and downloads, but no clean standalone public plume API endpoint was found in the public materials. The integration therefore supports a documented local JSON import path rather than inventing an endpoint: `COPILOT_PLUME_JSON=/absolute/path/plume.json`.

## Environment variables

```bash
export EIA_API_KEY="<runtime-only EIA key>"        # optional; never commit or echo
export COPILOT_PLUME_JSON="/absolute/path/plume.json" # optional local MARS-shaped JSON
export COPILOT_FACILITIES_JSON="/absolute/path/facilities.json" # optional JSON array
export COPILOT_CASE_DIR="/absolute/path/runtime-cases"    # optional, defaults to copilot/cases
export COPILOT_CREDIT_DIR="/absolute/path/runtime-credits" # optional, defaults to copilot/credits
```

The plume import accepts an object with `scene_timestamp`, `centroid.latitude`, `centroid.longitude`, and `estimated_flux.metric_tonnes_ch4_per_day`. Facilities are an array of objects with latitude/longitude and optional name/component.

## Run tests and the sample flow

```bash
python -m pip install -e ".[test]"
python -m pytest copilot/tests/test_api.py copilot/tests/test_credit_mint.py
# Run the existing suite as well (may require the research dependencies):
python -m pytest
```

From the repository root, run the deterministic in-process sample:

```text
python - <<'PY'
from copilot.api import run_flow

result = run_flow({
    "case_dir": "/tmp/methane-cases",
    "credit_dir": "/tmp/methane-credits",
})
print(result["data"]["credit"]["credit_count"])
PY
```

The flow is: local plume import (or built-in demo object) -> Open-Meteo current wind attribution -> nearest facility heuristic -> EIA Henry Hub/constant fallback and gas, CO2e, climate-damage and lost-gas dollars -> `detected` -> `source_named` -> `billed` -> `repair_scheduled` -> `resolved` case lifecycle -> locally minted modeled credit batch.

## Web demo

See [`web/README.md`](web/README.md) for the web demo details. From the repository root, run:

```bash
cd web && npm install && npm run dev
```

Open `http://localhost:3000` in your browser. No API keys are needed.

## Response contract

`copilot.api.run_flow()` returns JSON-compatible data with `ok`, `data.source`, `data.exposure`, `data.case`, `data.repair`, `data.credit`, `values`, and `meta`. The frontend consumes the same shape at `GET /api/source`, `/api/bill`, `/api/heal`, and `/api/credit` through its adapter. `meta.sources` records the exact EIA, Open-Meteo, and Eye on Methane reference URLs.

## Verified external URLs and limitations

* EIA Henry Hub series: `https://api.eia.gov/v2/seriesid/NG.RNGWHHD.D/` (key supplied only as a query parameter at runtime).
* Open-Meteo no-key wind: `https://api.open-meteo.com/v1/forecast`.
* Eye on Methane public platform/data dictionary: `https://methanedata.unep.org/` and `https://methanedata.unep.org/dict-mars-plumes`.
* Attribution is a wind-aware heuristic screening result, not proof of source ownership. The local credit registry is an audit-friendly workflow mock, not third-party registry verification. Live EIA/Open-Meteo calls can fall back when unavailable.
