"""Webhook event repository with LOCAL and S3 backends."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from payments_pipeline.config.settings import Settings
from payments_pipeline.load.filesystem_adapter import FilesystemAdapter
from payments_pipeline.utils.ids import sanitize_id_for_path
from payments_pipeline.utils.time import to_iso, utc_now

try:
    import boto3
except Exception:  # pragma: no cover
    boto3 = None


@dataclass(slots=True)
class WebhookRepository:
    settings: Settings
    fs: FilesystemAdapter = field(init=False)
    s3: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.fs = FilesystemAdapter(self.settings.local_data_dir)
        self.s3 = (
            boto3.client("s3", region_name=self.settings.aws_region)
            if boto3 and self.settings.pipeline_env == "AWS"
            else None
        )

    def _marker_key(self, event_id: str) -> str:
        safe = sanitize_id_for_path(event_id)
        return f"bronze/source=stripe/entity=webhook_events/markers/{safe}.marker"

    def _payload_key(self, event_id: str, received_ts: str) -> str:
        safe = sanitize_id_for_path(event_id)
        dt = received_ts[:10]
        return f"bronze/source=stripe/entity=webhook_events/dt={dt}/event_id={safe}/payload.json"

    def exists(self, event_id: str) -> bool:
        key = self._marker_key(event_id)
        if self.settings.pipeline_env == "AWS":
            if not self.s3 or not self.settings.s3_bucket:
                raise RuntimeError("S3 repository unavailable")
            try:
                self.s3.head_object(Bucket=self.settings.s3_bucket, Key=key)
                return True
            except Exception:
                return False
        return self.fs.exists(key)

    def write(
        self, event_id: str, payload: bytes, headers: dict[str, str], received_ts: str | None = None
    ) -> str:
        ts = received_ts or to_iso(utc_now())
        payload_key = self._payload_key(event_id, ts)
        marker_key = self._marker_key(event_id)

        envelope = {
            "event_id": event_id,
            "received_ts": ts,
            "headers": headers,
            "payload": json.loads(payload.decode("utf-8")),
        }

        if self.settings.pipeline_env == "AWS":
            if not self.s3 or not self.settings.s3_bucket:
                raise RuntimeError("S3 repository unavailable")
            self.s3.put_object(
                Bucket=self.settings.s3_bucket,
                Key=payload_key,
                Body=json.dumps(envelope).encode("utf-8"),
            )
            self.s3.put_object(Bucket=self.settings.s3_bucket, Key=marker_key, Body=b"1")
            return f"s3://{self.settings.s3_bucket}/{payload_key}"

        location = self.fs.put_json(payload_key, envelope)
        self.fs.put_bytes(marker_key, b"1")
        return location
