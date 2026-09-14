"""Offline carbon-credit screening and local registry workflow."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
import uuid
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

GWP100_METHANE = 28
ILLUSTRATIVE_CARBON_PRICE_USD = 15.0
CARBON_PRICE_RANGE_USD = (7.0, 25.0)
COMMISSION_RATE = 0.15
CREDIT_STATUS = Literal["minted", "verified", "listed", "sold"]
CREDIT_STATUSES = ("minted", "verified", "listed", "sold")
LEGAL_TRANSITIONS = dict(zip(CREDIT_STATUSES, CREDIT_STATUSES[1:]))
REGISTRY_VERIFICATION_DISCLAIMER = ("This local registry is an audit-friendly workflow mock: minted, verified, listed, and sold are internal statuses, not third-party registry verification or a compliance claim.")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ValidationError(ValueError):
    """Raised for invalid batch, heal-case, timestamp, number, or status input."""


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string")
    return value.strip()


def _identifier(value: Any, name: str) -> str:
    value = _text(value, name)
    if not _ID_RE.fullmatch(value):
        raise ValidationError(f"{name} contains unsupported characters or is too long")
    return value


def _number(value: Any, name: str, *, minimum: float = 0.0, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < minimum or (not allow_zero and result == 0):
        raise ValidationError(f"{name} must be finite and {'>= 0' if allow_zero else '> 0'}")
    return result


def _timestamp(value: Any, name: str) -> str:
    value = _text(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{name} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class CreditEconomics:
    methane_tonnes: float
    gwp100: int
    co2e_tonnes: float
    credit_count: int
    price_usd_per_tonne: float
    gross_revenue_usd: float
    commission_rate: float
    commission_usd: float
    net_revenue_usd: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_economics(methane_tonnes: float, *, price_usd_per_tonne: float = ILLUSTRATIVE_CARBON_PRICE_USD, commission_rate: float = COMMISSION_RATE) -> CreditEconomics:
    """Pure, deterministic screening math; no I/O, network, or global state."""
    methane = _number(methane_tonnes, "methane_tonnes")
    price = _number(price_usd_per_tonne, "price_usd_per_tonne")
    rate = _number(commission_rate, "commission_rate", minimum=0.0, allow_zero=True)
    if rate >= 1:
        raise ValidationError("commission_rate must be below 1")
    co2e = methane * GWP100_METHANE
    gross = round(co2e * price, 2)
    commission = round(gross * rate, 2)
    return CreditEconomics(methane, GWP100_METHANE, co2e, math.floor(co2e), price, gross, rate, commission, round(gross - commission, 2))


calculate_credit_economics = calculate_economics
calculate_credits = calculate_economics


@dataclass(frozen=True, slots=True)
class StatusEvent:
    status: CREDIT_STATUS
    at: str


@dataclass(frozen=True, slots=True)
class CreditBatch:
    batch_id: str
    case_id: str
    methane_tonnes: float
    detected_at: str
    resolved_at: str
    source: str = "methane-copilot"
    status: CREDIT_STATUS = "minted"
    created_at: str = field(default_factory=_now)
    history: tuple[StatusEvent, ...] = ()

    def __post_init__(self) -> None:
        _identifier(self.batch_id, "batch_id")
        _identifier(self.case_id, "case_id")
        _number(self.methane_tonnes, "methane_tonnes")
        _timestamp(self.detected_at, "detected_at")
        _timestamp(self.resolved_at, "resolved_at")
        _timestamp(self.created_at, "created_at")
        _text(self.source, "source")
        if self.status not in CREDIT_STATUSES:
            raise ValidationError(f"status must be one of {CREDIT_STATUSES}")
        for event in self.history:
            if event.status not in CREDIT_STATUSES:
                raise ValidationError("history contains an invalid status")
            _timestamp(event.at, "history.at")

    @property
    def economics(self) -> CreditEconomics:
        return calculate_economics(self.methane_tonnes)

    @property
    def co2e_tonnes(self) -> float:
        return self.economics.co2e_tonnes

    @property
    def credit_count(self) -> int:
        return self.economics.credit_count

    def to_dict(self) -> dict[str, Any]:
        return {"batch_id": self.batch_id, "case_id": self.case_id, "methane_tonnes": self.methane_tonnes, "detected_at": _timestamp(self.detected_at, "detected_at"), "resolved_at": _timestamp(self.resolved_at, "resolved_at"), "source": self.source, "status": self.status, "created_at": _timestamp(self.created_at, "created_at"), "co2e_tonnes": self.co2e_tonnes, "credit_count": self.credit_count, "history": [asdict(event) for event in self.history]}

    @classmethod
    def from_resolved_case(cls, case: Mapping[str, Any], *, batch_id: str, methane_tonnes: float, detected_at: str | None = None, source: str = "methane-copilot") -> "CreditBatch":
        resolved = validate_resolved_heal_case(case)
        detected = _timestamp(detected_at or resolved.get("detected_at"), "detected_at")
        created = _now()
        return cls(_identifier(batch_id, "batch_id"), _identifier(resolved["case_id"], "case_id"), _number(methane_tonnes, "methane_tonnes"), detected, _timestamp(resolved["resolved_at"], "resolved_at"), _text(source, "source"), created_at=created, history=(StatusEvent("minted", created),))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CreditBatch":
        if not isinstance(payload, Mapping):
            raise ValidationError("batch must be a JSON object")
        required = {"batch_id", "case_id", "methane_tonnes", "detected_at", "resolved_at", "source", "status", "created_at"}
        allowed = required | {"co2e_tonnes", "credit_count", "history"}
        missing, unknown = required - set(payload), set(payload) - allowed
        if missing:
            raise ValidationError(f"batch is missing fields: {sorted(missing)}")
        if unknown:
            raise ValidationError(f"batch has unsupported fields: {sorted(unknown)}")
        raw_history = payload.get("history", [])
        if not isinstance(raw_history, Sequence) or isinstance(raw_history, (str, bytes)):
            raise ValidationError("history must be an array")
        history = []
        for item in raw_history:
            if not isinstance(item, Mapping) or set(item) != {"status", "at"}:
                raise ValidationError("history entries must contain only status and at")
            history.append(StatusEvent(item["status"], _timestamp(item["at"], "history.at")))
        batch = cls(payload["batch_id"], payload["case_id"], payload["methane_tonnes"], payload["detected_at"], payload["resolved_at"], payload["source"], payload["status"], payload["created_at"], tuple(history))
        if "co2e_tonnes" in payload and payload["co2e_tonnes"] != batch.co2e_tonnes:
            raise ValidationError("co2e_tonnes does not match GWP100 methane math")
        if "credit_count" in payload and payload["credit_count"] != batch.credit_count:
            raise ValidationError("credit_count does not match GWP100 methane math")
        return batch


def validate_batch(payload: Mapping[str, Any]) -> CreditBatch:
    return CreditBatch.from_dict(payload)


def validate_resolved_heal_case(case: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(case, Mapping) or case.get("status") != "resolved":
        raise ValidationError("only a resolved heal case can mint credits")
    for name in ("case_id", "resolved_at", "resolution"):
        if name not in case:
            raise ValidationError(f"resolved heal case is missing {name}")
    result = dict(case)
    result["case_id"] = _identifier(case["case_id"], "case_id")
    result["resolved_at"] = _timestamp(case["resolved_at"], "resolved_at")
    result["resolution"] = _text(case["resolution"], "resolution")
    if "detected_at" in case:
        result["detected_at"] = _timestamp(case["detected_at"], "detected_at")
    if "rescan_match" in case and case["rescan_match"] is not False:
        raise ValidationError("a resolved heal case must have rescan_match=False when supplied")
    return result


validate_heal_case = validate_resolved_heal_case


def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


class CreditRegistry:
    def __init__(self, directory: str | Path | None = None) -> None:
        self.directory = Path(directory) if directory is not None else Path(__file__).with_name("credits")
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, batch_id: str) -> Path:
        identifier = _identifier(batch_id, "batch_id")
        root = self.directory.resolve()
        path = (root / f"{identifier}.json").resolve()
        if path.parent != root:
            raise ValidationError("batch path escapes registry directory")
        return path

    def save(self, batch: CreditBatch) -> CreditBatch:
        atomic_write_json(self._path(batch.batch_id), batch.to_dict())
        return batch

    def mint(self, batch: CreditBatch) -> CreditBatch:
        if batch.status != "minted":
            raise ValidationError("newly minted batches must have status minted")
        if self._path(batch.batch_id).exists():
            raise ValidationError(f"batch already exists: {batch.batch_id}")
        return self.save(batch)

    def get(self, batch_id: str) -> CreditBatch:
        path = self._path(batch_id)
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8") as handle:
            return CreditBatch.from_dict(json.load(handle))

    def list_batches(self) -> list[CreditBatch]:
        return [self.get(path.stem) for path in sorted(self.directory.glob("*.json"))]

    def transition(self, batch_id: str, status: CREDIT_STATUS, *, at: str | None = None) -> CreditBatch:
        current = self.get(batch_id)
        if status not in CREDIT_STATUSES:
            raise ValidationError(f"status must be one of {CREDIT_STATUSES}")
        if LEGAL_TRANSITIONS.get(current.status) != status:
            raise ValidationError(f"illegal credit status transition: {current.status} -> {status}")
        timestamp = _timestamp(at or _now(), "transition.at")
        return self.save(replace(current, status=status, history=current.history + (StatusEvent(status, timestamp),)))


def canonical_demo() -> dict[str, Any]:
    result = calculate_economics(12.4)
    return {"methane_tonnes": result.methane_tonnes, "gwp100_methane": result.gwp100, "co2e_tonnes": result.co2e_tonnes, "credits": result.credit_count, "price_usd_per_tonne_co2e": result.price_usd_per_tonne, "gross_revenue_usd": result.gross_revenue_usd, "commission_rate": result.commission_rate, "commission_usd": result.commission_usd, "net_revenue_usd": result.net_revenue_usd, "price_range_usd": list(CARBON_PRICE_RANGE_USD), "disclaimer": REGISTRY_VERIFICATION_DISCLAIMER}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=("demo",), default="demo")
    parser.add_argument("--methane", type=float, default=12.4)
    parser.add_argument("--price", type=float, default=ILLUSTRATIVE_CARBON_PRICE_USD)
    args = parser.parse_args(argv)
    result = calculate_economics(args.methane, price_usd_per_tonne=args.price)
    print(json.dumps({"methane_tonnes": result.methane_tonnes, "co2e_tonnes": result.co2e_tonnes, "credits": result.credit_count, "gross_revenue_usd": result.gross_revenue_usd, "net_revenue_usd": result.net_revenue_usd, "gwp100_methane": GWP100_METHANE, "commission_rate": COMMISSION_RATE, "disclaimer": REGISTRY_VERIFICATION_DISCLAIMER}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
