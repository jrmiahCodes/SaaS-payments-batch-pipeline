"""Base extractor primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from payments_pipeline.clients.stripe_like_interface import StripeLikeClient
from payments_pipeline.config.logging import get_logger, set_run_context
from payments_pipeline.load.writer import BronzeWriter
from payments_pipeline.utils.ids import new_correlation_id
from payments_pipeline.utils.time import to_iso, utc_now


@dataclass(slots=True)
class ExtractResult:
    entity: str
    records: int
    pages: int
    api_calls: int
    retries: int
    failures: int
    watermark: int | None
    bronze_paths: list[str]


class BaseExtractor:
    entity: str = ""

    def __init__(self, client: StripeLikeClient, writer: BronzeWriter):
        self.client = client
        self.writer = writer
        self.logger = get_logger(self.__class__.__name__)

    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        return record

    def envelope(self, raw: dict[str, Any], run_context: dict[str, Any], correlation_id: str) -> dict[str, Any]:
        return {
            "data": raw,
            "meta": {
                "entity": self.entity,
                "run_id": run_context["run_id"],
                "correlation_id": correlation_id,
                "ingested_at": to_iso(utc_now()),
                "source": "stripe_mock",
                "lifted": self.normalize(raw),
            },
        }

    def extract_window(self, start_ts: int, end_ts: int, run_context: dict[str, Any]) -> ExtractResult:
        correlation_id = new_correlation_id()
        set_run_context(correlation_id=correlation_id)

        records, metrics = self.client.iter_entity(
            self.entity,
            created_gte=start_ts,
            created_lte=end_ts,
            limit=run_context["settings"].max_page_size,
        )
        wrapped = [self.envelope(row, run_context, correlation_id=correlation_id) for row in records]
        write_result = self.writer.write_bronze_jsonl(self.entity, wrapped, run_context)
        max_created = max((int(item.get("created", 0)) for item in records), default=None)
        self.logger.info(
            "extract_window_complete",
            extra={
                "entity": self.entity,
                "records": len(records),
                "pages": metrics.get("pages", 0),
                "api_calls": metrics.get("api_calls", 0),
            },
        )
        return ExtractResult(
            entity=self.entity,
            records=len(records),
            pages=metrics.get("pages", 0),
            api_calls=metrics.get("api_calls", 0),
            retries=metrics.get("retries", 0),
            failures=metrics.get("failures", 0),
            watermark=max_created,
            bronze_paths=write_result.paths,
        )
