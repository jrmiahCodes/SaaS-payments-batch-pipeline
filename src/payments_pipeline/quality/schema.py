"""Schema checks for silver/gold models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from payments_pipeline.config.logging import get_logger

try:
    import duckdb
except Exception:  # pragma: no cover
    duckdb = None


MODEL_RULES: dict[str, dict[str, Any]] = {
    "dim_customers": {"required_columns": ["id"], "not_null": ["id"]},
    "fct_payments": {"required_columns": ["id"], "not_null": ["id"]},
    "fct_invoices": {"required_columns": ["id"], "not_null": ["id"]},
}


@dataclass(slots=True)
class CheckResult:
    model: str
    passed: bool
    messages: list[str]


def _columns(conn: Any, parquet_path: Path) -> list[str]:
    rows = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path.as_posix()}')").fetchall()
    return [row[0] for row in rows]


def run_schema_checks(base_dir: Path) -> list[CheckResult]:
    if duckdb is None:
        raise RuntimeError("duckdb is required for schema checks")

    logger = get_logger(__name__)
    conn = duckdb.connect()
    results: list[CheckResult] = []

    for model, rules in MODEL_RULES.items():
        candidates = sorted(base_dir.glob(f"gold/model={model}/dt=*/data.parquet"))
        if not candidates:
            results.append(CheckResult(model=model, passed=False, messages=["missing parquet output"]))
            continue
        parquet_path = candidates[-1]
        cols = set(_columns(conn, parquet_path))
        messages: list[str] = []
        passed = True

        required = set(rules.get("required_columns", []))
        missing = required - cols
        if missing:
            passed = False
            messages.append(f"missing columns: {sorted(missing)}")

        for col in rules.get("not_null", []):
            null_count = conn.execute(
                f"SELECT COUNT(*) FROM read_parquet('{parquet_path.as_posix()}') WHERE {col} IS NULL"
            ).fetchone()[0]
            if null_count > 0:
                passed = False
                messages.append(f"column {col} has {null_count} nulls")

        if passed:
            messages.append("ok")
        results.append(CheckResult(model=model, passed=passed, messages=messages))

    logger.info("schema_checks_complete", extra={"results": [asdict(r) for r in results]})
    return results
