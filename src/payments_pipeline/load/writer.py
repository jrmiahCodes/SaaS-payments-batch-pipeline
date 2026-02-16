"""Writers for bronze JSONL and metadata sidecars."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from payments_pipeline.config.logging import get_logger
from payments_pipeline.config.settings import Settings
from payments_pipeline.load.filesystem_adapter import FilesystemAdapter
from payments_pipeline.load.paths import bronze_relative_path
from payments_pipeline.utils.time import dt_partition, utc_now

try:
    import boto3
except Exception:  # pragma: no cover
    boto3 = None


@dataclass(slots=True)
class WriteResult:
    entity: str
    record_count: int
    chunk_count: int
    paths: list[str]
    schema_hash: str


class BronzeWriter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = get_logger(__name__)
        self.fs = FilesystemAdapter(settings.local_data_dir)
        self._s3 = (
            boto3.client("s3", region_name=settings.aws_region)
            if boto3 and settings.pipeline_env == "AWS"
            else None
        )

    def _put_bytes(self, relative_path: str, data: bytes) -> str:
        if self.settings.pipeline_env == "AWS":
            if not self._s3 or not self.settings.s3_bucket:
                raise RuntimeError("boto3 or S3 bucket not configured for AWS mode")
            self._s3.put_object(Bucket=self.settings.s3_bucket, Key=relative_path, Body=data)
            return f"s3://{self.settings.s3_bucket}/{relative_path}"
        return self.fs.put_bytes(relative_path, data)

    def write_bronze_jsonl(
        self,
        entity: str,
        records: list[dict[str, Any]],
        run_context: dict[str, Any],
        *,
        chunk_size: int = 1000,
        deterministic_order: bool = True,
        write_sidecar: bool = True,
    ) -> WriteResult:
        if deterministic_order:
            records = sorted(
                records, key=lambda r: str(r.get("data", {}).get("id", r.get("id", "")))
            )

        dt = dt_partition(run_context.get("now") or utc_now())
        run_id = str(run_context["run_id"])
        paths: list[str] = []

        schema_keys = sorted({k for rec in records for k in rec.keys()})
        schema_hash = hashlib.sha256("|".join(schema_keys).encode("utf-8")).hexdigest()

        for idx in range(0, len(records), chunk_size):
            chunk = records[idx : idx + chunk_size]
            part = idx // chunk_size
            rel_path = bronze_relative_path(entity=entity, dt=dt, run_id=run_id, part=part)
            body = "\n".join(json.dumps(row, default=str, sort_keys=True) for row in chunk) + (
                "\n" if chunk else ""
            )
            paths.append(self._put_bytes(rel_path, body.encode("utf-8")))

        if write_sidecar and paths:
            sidecar = {
                "entity": entity,
                "run_id": run_id,
                "dt": dt,
                "record_count": len(records),
                "chunk_count": len(paths),
                "schema_hash": schema_hash,
            }
            sidecar_rel = bronze_relative_path(entity=entity, dt=dt, run_id=run_id, part=0).replace(
                "part-00000.jsonl", "_metadata.json"
            )
            self._put_bytes(sidecar_rel, json.dumps(sidecar, indent=2).encode("utf-8"))

        self.logger.info(
            "bronze_write_complete",
            extra={"entity": entity, "record_count": len(records), "chunk_count": len(paths)},
        )

        return WriteResult(
            entity=entity,
            record_count=len(records),
            chunk_count=len(paths),
            paths=paths,
            schema_hash=schema_hash,
        )
