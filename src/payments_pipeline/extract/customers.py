"""Customers extractor."""

from __future__ import annotations

from payments_pipeline.extract.base import BaseExtractor, ExtractResult
from payments_pipeline.state.watermarks import WatermarkStore, commit, get_window
from payments_pipeline.utils.time import utc_now


class CustomersExtractor(BaseExtractor):
    entity = "customers"

    def normalize(self, record: dict) -> dict:
        return {
            "id": record.get("id"),
            "created": record.get("created"),
            "email": record.get("email"),
            "name": record.get("name"),
        }

    def run(self, run_context: dict, days: int) -> ExtractResult:
        settings = run_context["settings"]
        store = WatermarkStore(settings.watermarks_root)
        window = get_window(
            self.entity,
            now_ts=int(utc_now().timestamp()),
            days=days,
            safety_window=settings.safety_window_seconds,
            store=store,
        )
        result = self.extract_window(window.start_ts, window.end_ts, run_context)
        if result.watermark is not None:
            commit(self.entity, result.watermark, run_context["run_id"], store)
        return result
