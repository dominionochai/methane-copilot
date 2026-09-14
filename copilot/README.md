# Methane Copilot decision layer

`copilot/` is a small, original decision layer that can sit above UNEP
MARS-S2L. MARS-S2L supplies the methane-plume detection (including a
georeferenced mask/centroid, scene time, and estimated flux); these modules
turn that detection into screening attribution, value/damage estimates, and a
human-review repair workflow.

## Modules

- **`source_attribution.py`** loads a plume JSON detection, attempts an ERA5
  wind request through the CDS API when configured, otherwise reads wind from
  CSV/JSON, interpolates U/V at the detection time and location, propagates
  backward along the wind vector, and optionally ranks a supplied facility
  catalogue. It always returns a clear uncertainty disclaimer.
- **`dollar_engine.py`** contains pure, unit-testable calculations for gross
  lost-gas commodity value, CO2e, EPA-style social cost of methane, and a
  supplied carbon price. `fetch_eia_henry_hub()` uses `api.eia.gov/v2` when
  `EIA_API_KEY` exists and otherwise uses the documented default constant.
- **`heal_tracker.py`** stores one JSON case per detection in
  `copilot/cases/`, provides create/update/resolve/list operations, suggests
  simple flange/valve repair playbooks, compares estimated daily gas burn with
  a planning fix cost, and resolves a case when a later rescan has no matching
  detection. The demo uses a temporary directory; no generated case is
  committed. Git cannot represent an empty directory, so `cases/` is created
  at runtime and is intentionally absent from this commit.

## Requirements and composition

The baseline environment should provide **`requests`** and **`numpy`**. The
modules use the standard library where practical. **`cdsapi`** is optional for
ERA5 retrieval and **`python-dotenv`** is optional for loading local
configuration. Supply local wind data when CDS credentials or optional NetCDF
reading support are unavailable.

The detection stage comes from **UNEP MARS-S2L**, which is distributed under
LGPL. The code in this directory is the user's original decision layer and is
not a modification of MARS-S2L. Attribution is a screening aid and must be
validated with appropriate meteorology, local facility data, safety controls,
and field confirmation before operational action.

## Quick examples

```bash
python copilot/source_attribution.py
python copilot/dollar_engine.py
python copilot/heal_tracker.py
```

All code assumes explicit units: metric tonnes CH4, MMBtu, metres/second, and
US dollars; see function docstrings for conventions and defaults.
