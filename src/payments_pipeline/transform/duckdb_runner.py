"""DuckDB transform runner."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from payments_pipeline.config.logging import get_logger
from payments_pipeline.state.manifests import ManifestStore
from payments_pipeline.transform.models import MODEL_EXECUTION_ORDER
from payments_pipeline.utils.time import dt_partition, utc_now

try:
    import duckdb
except Exception:  # pragma: no cover
    duckdb = None


@dataclass(slots=True)
class TransformMetric:
    model: str
    layer: str
    runtime_seconds: float
    status: str


def run_transforms(run_context: dict[str, Any]) -> list[TransformMetric]:
    if duckdb is None:
        raise RuntimeError("duckdb is required for transforms")

    logger = get_logger(__name__)
    settings = run_context["settings"]
    run_id = run_context["run_id"]
    dt = dt_partition(run_context.get("now") or utc_now())

    settings.state_root.mkdir(parents=True, exist_ok=True)
    db_path = settings.state_root / "pipeline.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute("PRAGMA threads=4")

    metrics: list[TransformMetric] = []
    manifest = ManifestStore(settings.manifests_root)

    for spec in MODEL_EXECUTION_ORDER:
        start = time.time()
        status = "ok"
        try:
            if not spec.sql_path.exists() or not spec.sql_path.read_text(encoding="utf-8").strip():
                logger.warning("transform_sql_missing_or_empty", extra={"model": spec.name, "path": str(spec.sql_path)})
                status = "skipped"
            else:
                sql = spec.sql_path.read_text(encoding="utf-8")
                sql = sql.replace("{{LOCAL_DATA_DIR}}", settings.local_data_dir.resolve().as_posix())
                conn.execute(sql)

                if spec.layer == "silver":
                    out_dir = settings.silver_root / "source=stripe" / f"entity={spec.name}" / f"dt={dt}"
                else:
                    out_dir = settings.gold_root / f"model={spec.name}" / f"dt={dt}"

                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / "data.parquet"
                conn.execute(f"COPY (SELECT * FROM {spec.name}) TO '{out_path.as_posix()}' (FORMAT PARQUET)")

                if spec.layer == "gold":
                    manifest.write_latest_model(spec.name, run_id=run_id, dt=dt, path=str(out_path))
        except Exception:
            logger.exception("transform_failed", extra={"model": spec.name, "layer": spec.layer})
            status = "failed"
            raise
        finally:
            metrics.append(
                TransformMetric(
                    model=spec.name,
                    layer=spec.layer,
                    runtime_seconds=round(time.time() - start, 3),
                    status=status,
                )
            )

    logger.info("transforms_completed", extra={"metrics": [asdict(m) for m in metrics]})
    return metrics
