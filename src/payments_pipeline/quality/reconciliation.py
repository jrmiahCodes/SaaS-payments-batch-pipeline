"""Rowcount and referential reconciliation checks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from payments_pipeline.config.logging import get_logger
from payments_pipeline.state.manifests import ManifestStore

try:
    import duckdb
except Exception:  # pragma: no cover
    duckdb = None


@dataclass(slots=True)
class ReconResult:
    passed: bool
    checks: list[dict[str, Any]]


def _count_jsonl_records(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            total += sum(1 for _ in f)
    return total


def run_reconciliation(
    base_dir: Path, manifest_store: ManifestStore, tolerance_ratio: float = 0.01
) -> ReconResult:
    logger = get_logger(__name__)
    checks: list[dict[str, Any]] = []

    entities = ["payment_intents", "charges", "invoices", "customers"]
    dt_dirs = sorted((base_dir / "bronze").glob("source=stripe/entity=*/dt=*"))
    dt = dt_dirs[-1].name.split("dt=")[-1] if dt_dirs else "unknown"

    if duckdb is None:
        raise RuntimeError("duckdb is required for reconciliation")
    conn = duckdb.connect()

    for entity in entities:
        bronze_files = sorted(
            (base_dir / "bronze" / f"source=stripe/entity={entity}").glob(
                "dt=*/run_id=*/part-*.jsonl"
            )
        )
        bronze_count = _count_jsonl_records(bronze_files)

        silver_files = sorted(
            (base_dir / "silver" / f"source=stripe/entity={entity}").glob("dt=*/data.parquet")
        )
        silver_count = 0
        if silver_files:
            silver_count = conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{silver_files[-1].as_posix()}')"
            ).fetchone()[0]

        diff = abs(bronze_count - silver_count)
        tolerance = max(1, int(bronze_count * tolerance_ratio))
        passed = diff <= tolerance
        checks.append(
            {
                "type": "rowcount",
                "entity": entity,
                "bronze_count": bronze_count,
                "silver_count": silver_count,
                "diff": diff,
                "tolerance": tolerance,
                "passed": passed,
            }
        )

    customers_latest = sorted(
        (base_dir / "silver/source=stripe/entity=customers").glob("dt=*/data.parquet")
    )
    charges_latest = sorted(
        (base_dir / "silver/source=stripe/entity=charges").glob("dt=*/data.parquet")
    )
    if customers_latest and charges_latest:
        missing_refs = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{charges_latest[-1].as_posix()}') c
            LEFT JOIN read_parquet('{customers_latest[-1].as_posix()}') d
            ON trim(c.customer_id) = trim(d.id)
            WHERE nullif(trim(c.customer_id), '') IS NOT NULL
              AND d.id IS NULL
            """
        ).fetchone()[0]
        checks.append(
            {
                "type": "referential",
                "relation": "charges.customer_id -> customers.id",
                "missing_refs": missing_refs,
                "passed": missing_refs == 0,
            }
        )

    passed = all(check.get("passed", False) for check in checks)
    report = {"passed": passed, "checks": checks}
    manifest_store.write_reconciliation(dt=dt, report=report)

    logger.info("reconciliation_complete", extra=report)
    return ReconResult(passed=passed, checks=checks)
