"""Freshness checks based on manifest latest pointers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta

from payments_pipeline.config.logging import get_logger
from payments_pipeline.state.manifests import ManifestStore
from payments_pipeline.utils.time import parse_ts, utc_now


@dataclass(slots=True)
class FreshnessResult:
    model: str
    passed: bool
    message: str


def run_freshness_checks(store: ManifestStore, *, max_age_hours: int = 24) -> list[FreshnessResult]:
    logger = get_logger(__name__)
    results: list[FreshnessResult] = []
    latest_dir = store.root / "_latest"
    pointers = sorted(latest_dir.glob("*.json"))

    if not pointers:
        return [
            FreshnessResult(
                model="all",
                passed=False,
                message="No _latest manifests found. Run transforms and ensure gold latest pointers are written.",
            )
        ]

    for pointer in pointers:
        payload = __import__("json").loads(pointer.read_text(encoding="utf-8"))
        model = payload.get("model", pointer.stem)
        updated_at = parse_ts(payload["updated_at"])
        age = utc_now() - updated_at
        if age > timedelta(hours=max_age_hours):
            results.append(
                FreshnessResult(
                    model=model,
                    passed=False,
                    message=f"stale by {age}. latest dt={payload.get('dt')} run_id={payload.get('run_id')}",
                )
            )
        else:
            results.append(FreshnessResult(model=model, passed=True, message="ok"))

    logger.info("freshness_checks_complete", extra={"results": [asdict(r) for r in results]})
    return results
