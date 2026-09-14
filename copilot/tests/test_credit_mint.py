from __future__ import annotations

import json
import pytest

from copilot.credit_mint import CreditBatch, CreditRegistry, ValidationError, calculate_economics, validate_resolved_heal_case

RESOLVED = {"case_id": "case-0123456789ab", "status": "resolved", "resolved_at": "2026-09-14T16:42:00Z", "detected_at": "2026-09-09T08:12:00Z", "resolution": "Post-repair scan found no matching detection", "rescan_match": False}


def test_canonical_math_is_consistent() -> None:
    result = calculate_economics(12.4)
    assert result.gwp100 == 28
    assert result.co2e_tonnes == pytest.approx(347.2)
    assert result.credit_count == 347
    assert result.gross_revenue_usd == 5208.0
    assert result.net_revenue_usd == 4426.8


def test_mint_requires_resolved_case_and_persists_json(tmp_path) -> None:
    batch = CreditBatch.from_resolved_case(RESOLVED, batch_id="batch-0123456789ab", methane_tonnes=12.4)
    registry = CreditRegistry(tmp_path)
    registry.mint(batch)
    persisted = json.loads((tmp_path / "batch-0123456789ab.json").read_text())
    assert persisted["status"] == "minted"
    assert persisted["co2e_tonnes"] == pytest.approx(347.2)
    assert registry.get(batch.batch_id).credit_count == 347


def test_legal_transitions_are_one_step_only(tmp_path) -> None:
    registry = CreditRegistry(tmp_path)
    batch = CreditBatch.from_resolved_case(RESOLVED, batch_id="batch-legal", methane_tonnes=12.4)
    registry.mint(batch)
    for status in ("verified", "listed", "sold"):
        batch = registry.transition(batch.batch_id, status, at="2026-09-15T00:00:00Z")
        assert batch.status == status
    with pytest.raises(ValidationError, match="illegal"):
        registry.transition(batch.batch_id, "listed")


def test_strict_validation_rejects_bad_numbers_timestamps_and_statuses() -> None:
    with pytest.raises(ValidationError):
        calculate_economics(True)
    with pytest.raises(ValidationError):
        calculate_economics(float("nan"))
    with pytest.raises(ValidationError):
        validate_resolved_heal_case({**RESOLVED, "status": "repair_scheduled"})
    with pytest.raises(ValidationError):
        CreditBatch.from_dict({"batch_id": "x"})


def test_registry_rejects_unresolved_case() -> None:
    with pytest.raises(ValidationError, match="resolved"):
        CreditBatch.from_resolved_case({**RESOLVED, "status": "repair_scheduled"}, batch_id="batch-unresolved", methane_tonnes=1.0)
