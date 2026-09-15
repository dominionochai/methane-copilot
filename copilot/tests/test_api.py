from __future__ import annotations

from pathlib import Path

from copilot import api


def test_live_adapters_use_documented_urls(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=10.0):
        calls.append((url, params))
        if url == api.EIA_HENRY_HUB_URL:
            return {"response": {"data": [{"period": "2026-01-02", "value": "3.25"}]}}
        return {"current": {"time": "2026-01-02T00:00", "wind_speed_10m": 4.0, "wind_direction_10m": 90.0}}

    monkeypatch.setattr(api, "_json_get", fake_get)
    assert api.fetch_eia_henry_hub("runtime-only-key")["price"] == 3.25
    records, meta = api.fetch_open_meteo_wind(31.0, -102.0)
    assert records and meta["url"] == api.OPEN_METEO_URL
    assert calls[0][0] == "https://api.eia.gov/v2/seriesid/NG.RNGWHHD.D/"
    assert "runtime-only-key" not in repr(calls)


def test_end_to_end_flow_with_supplied_wind(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(api, "fetch_eia_henry_hub", lambda: {"price": 3.0, "source": "test", "period": "2026-01-02", "series": "NG.RNGWHHD.D"})
    result = api.run_flow({
        "case_dir": tmp_path / "cases",
        "credit_dir": tmp_path / "credits",
        "plume": {"plume_id": "plume-test", "scene_timestamp": "2026-01-02T00:00:00Z", "centroid": {"latitude": 31.0, "longitude": -102.0}, "estimated_flux": {"metric_tons_ch4_per_day": 2.4}, "plume_length_m": 500},
        "facilities": [{"facility_id": "f1", "name": "Facility One", "latitude": 31.0, "longitude": -102.0, "component": "valve"}],
        "wind_records": [{"timestamp": "2026-01-02T00:00:00Z", "latitude": 31.0, "longitude": -102.0, "u_m_s": 1.0, "v_m_s": 0.0}],
    })
    assert result["ok"] is True
    assert result["data"]["source"]["attribution"]["matched_facility"]["facility_id"] == "f1"
    assert result["data"]["case"]["status"] == "resolved"
    assert result["data"]["credit"]["status"] == "minted"
    assert result["data"]["credit"]["credit_count"] == 67
