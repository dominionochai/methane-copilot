"""Offline tests for the copilot decision-layer modules.

These tests intentionally pass local records and temporary case directories so
that running ``pytest copilot/tests`` never needs credentials or network access.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from copilot import dollar_engine
from copilot import heal_tracker
from copilot import source_attribution


UTC = timezone.utc


def test_dollar_engine_math_and_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    result = dollar_engine.calculate_impact(
        2.0,
        price_usd_per_mmbtu=None,
        carbon_price_usd_per_ton_co2e=50.0,
    )

    assert result["lost_gas_commodity_usd"] == pytest.approx(2.0 * 52.0 * 3.0)
    assert result["mmbtu"] == pytest.approx(104.0)
    assert result["henry_hub_usd_per_mmbtu"] == 3.0
    assert result["henry_hub_source"] == "fallback_constant"
    assert result["henry_hub_period"] is None
    assert result["henry_hub_fallback_reason"] == "missing_api_key"
    assert result["co2e_tons"] == pytest.approx(56.0)
    assert result["climate_damage_usd"] == pytest.approx(3200.0)
    assert result["carbon_price_usd"] == pytest.approx(2800.0)


def test_dollar_engine_explicit_price_and_math() -> None:
    result = dollar_engine.calculate_impact(
        1.5,
        price_usd_per_mmbtu=4.0,
        carbon_price_usd_per_ton_co2e=25.0,
        mmbtu_per_metric_ton=52.0,
        social_cost_usd_per_metric_ton=1600.0,
        gwp100=28.0,
    )

    assert result["lost_gas_commodity_usd"] == pytest.approx(312.0)
    assert result["co2e_tons"] == pytest.approx(42.0)
    assert result["climate_damage_usd"] == pytest.approx(2400.0)
    assert result["carbon_price_usd"] == pytest.approx(1050.0)
    assert result["henry_hub_source"] == "caller"


@pytest.mark.parametrize(
    "call",
    [
        lambda: dollar_engine.lost_gas_commodity_value(-1.0, price_usd_per_mmbtu=3.0),
        lambda: dollar_engine.co2e_tons(1.0, gwp100=float("nan")),
        lambda: dollar_engine.calculate_impact(1.0, carbon_price_usd_per_ton_co2e=-1.0),
        lambda: dollar_engine.fetch_eia_henry_hub(fallback=-1.0),
        lambda: dollar_engine.fetch_eia_henry_hub(timeout_seconds=0.0),
    ],
)
def test_dollar_engine_rejects_bad_input(call) -> None:
    with pytest.raises(ValueError):
        call()


def _record(
    *,
    timestamp: datetime,
    latitude: float = 0.0,
    longitude: float = 0.0,
    u_m_s: float = 1.0,
    v_m_s: float = 2.0,
) -> source_attribution.WindRecord:
    return source_attribution.WindRecord(
        timestamp=timestamp,
        latitude=latitude,
        longitude=longitude,
        u_m_s=u_m_s,
        v_m_s=v_m_s,
    )


def test_source_interpolation_and_longitude_wrap() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    result = source_attribution.interpolate_wind(
        [_record(timestamp=timestamp, latitude=0.0, longitude=179.0)],
        latitude=0.0,
        longitude=-179.0,
        timestamp=timestamp,
    )

    assert result["u_m_s"] == pytest.approx(1.0)
    assert result["v_m_s"] == pytest.approx(2.0)
    assert result["speed_m_s"] == pytest.approx(2.2360679775)
    assert result["record_count"] == 1.0


@pytest.mark.parametrize(
    "latitude, longitude",
    [(91.0, 0.0), (-91.0, 0.0), (0.0, 181.0), (0.0, -181.0)],
)
def test_source_coordinate_validation(latitude: float, longitude: float) -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError):
        source_attribution.interpolate_wind(
            [_record(timestamp=timestamp)], latitude, longitude, timestamp
        )


def test_propagate_backward_has_stable_schema() -> None:
    result = source_attribution.propagate_backward(
        {"latitude": 10.0, "longitude": 179.9},
        {"u_m_s": 3.0, "v_m_s": 4.0},
        1000.0,
    )

    assert set(result) == {
        "latitude",
        "longitude",
        "travel_distance_m",
        "travel_time_s",
    }
    assert result["travel_distance_m"] == 1000.0
    assert result["travel_time_s"] == pytest.approx(200.0)
    assert -180.0 <= result["longitude"] <= 180.0


def test_propagate_backward_validates_coordinates_and_distance() -> None:
    with pytest.raises(ValueError):
        source_attribution.propagate_backward(
            {"latitude": 91.0, "longitude": 0.0}, {"u_m_s": 1.0, "v_m_s": 0.0}, 1.0
        )
    with pytest.raises(ValueError):
        source_attribution.propagate_backward(
            {"latitude": 0.0, "longitude": 0.0}, {"u_m_s": 1.0, "v_m_s": 0.0}, -1.0
        )


def _advance_to_repair_scheduled(case_id: str, case_dir) -> dict:
    case = heal_tracker.create_case(
        10.0,
        20.0,
        2.0,
        detected_at="2026-01-01T00:00:00Z",
        case_id=case_id,
        case_dir=case_dir,
    )
    for status in ("source_named", "billed", "repair_scheduled"):
        case = heal_tracker.update_case(
            case_id, {"status": status}, case_dir=case_dir
        )
    return case


def test_heal_tracker_legal_lifecycle_and_illegal_jump(tmp_path) -> None:
    case_id = "case-0123456789ab"
    case = heal_tracker.create_case(
        10.0,
        20.0,
        2.0,
        detected_at="2026-01-01T00:00:00Z",
        case_id=case_id,
        case_dir=tmp_path,
    )
    assert case["status"] == "detected"

    with pytest.raises(ValueError, match="illegal status transition"):
        heal_tracker.update_case(case_id, {"status": "billed"}, case_dir=tmp_path)
    assert json.loads((tmp_path / f"{case_id}.json").read_text())["status"] == "detected"

    for status in ("source_named", "billed", "repair_scheduled", "resolved"):
        case = heal_tracker.update_case(case_id, {"status": status}, case_dir=tmp_path)
    assert case["status"] == "resolved"
    assert [entry["event"] for entry in case["history"]] == [
        "detected",
        "updated",
        "updated",
        "updated",
        "updated",
    ]


def test_heal_tracker_case_id_and_path_safety(tmp_path) -> None:
    for invalid in ("../case-0123456789ab", "case-0123456789ab/child", "case-nope"):
        with pytest.raises(ValueError, match="invalid case id"):
            heal_tracker.create_case(0.0, 0.0, 1.0, case_id=invalid, case_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_heal_tracker_atomic_write_preserves_previous_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_id = "case-0123456789ab"
    heal_tracker.create_case(0.0, 0.0, 1.0, case_id=case_id, case_dir=tmp_path)
    path = tmp_path / f"{case_id}.json"
    before = path.read_text()

    def fail_dump(*args, **kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(heal_tracker.json, "dump", fail_dump)
    with pytest.raises(OSError, match="simulated write failure"):
        heal_tracker.update_case(case_id, {"notes": "not persisted"}, case_dir=tmp_path)

    assert path.read_text() == before
    assert list(tmp_path.glob("*.tmp")) == []


def test_heal_tracker_rescan_ignores_non_later_detection_and_records_time(tmp_path) -> None:
    case_id = "case-0123456789ab"
    _advance_to_repair_scheduled(case_id, tmp_path)

    result = heal_tracker.rescan_check(
        case_id,
        [{"detected_at": "2026-01-01T00:00:00Z", "latitude": 10.0, "longitude": 20.0}],
        rescan_at="2026-01-02T00:00:00Z",
        case_dir=tmp_path,
    )

    assert result["status"] == "resolved"
    assert result["rescan_match"] is False
    assert result["last_rescan_at"] == "2026-01-02T00:00:00Z"
    assert result["resolved_at"] == "2026-01-02T00:00:00Z"


def test_heal_tracker_rescan_keeps_scheduled_case_on_later_match(tmp_path) -> None:
    case_id = "case-abcdef012345"
    _advance_to_repair_scheduled(case_id, tmp_path)

    result = heal_tracker.rescan_check(
        case_id,
        [{"detected_at": "2026-01-01T00:01:00Z", "latitude": 10.0, "longitude": 20.0}],
        rescan_at="2026-01-02T00:00:00Z",
        case_dir=tmp_path,
    )

    assert result["status"] == "repair_scheduled"
    assert result["rescan_match"] is True
    assert result["last_rescan_at"] == "2026-01-02T00:00:00Z"
