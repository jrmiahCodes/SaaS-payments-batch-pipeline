"""HTTP-backed Stripe-like client for local mock API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from payments_pipeline.clients.stripe_like_interface import ListPage
from payments_pipeline.config.logging import get_logger
from payments_pipeline.utils.retry import RetryConfig, retry_call


@dataclass(slots=True)
class ApiMetrics:
    api_calls: int = 0
    retries: int = 0
    failures: int = 0


class MockStripeClient:
    def __init__(self, base_url: str, timeout_seconds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger(__name__)

    def list_entity(
        self,
        entity: str,
        *,
        created_gte: int | None,
        created_lte: int | None,
        starting_after: str | None,
        limit: int,
    ) -> ListPage:
        params: dict[str, Any] = {
            "created_gte": created_gte,
            "created_lte": created_lte,
            "starting_after": starting_after,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        url = f"{self.base_url}/v1/{entity}"

        def _call() -> requests.Response:
            response = requests.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            return response

        metrics: dict[str, int] = {}
        response = retry_call(
            _call,
            retryable_exceptions=(requests.RequestException,),
            config=RetryConfig(),
            logger=self.logger,
            metrics=metrics,
        )
        payload = response.json()
        data = payload.get("data", [])
        has_more = bool(payload.get("has_more", False))
        next_cursor = data[-1]["id"] if has_more and data else None
        request_meta = {
            "url": str(response.url),
            "status_code": response.status_code,
            "retries": metrics.get("retries", 0),
            "failures": metrics.get("failures", 0),
        }
        return ListPage(entity=entity, data=data, has_more=has_more, next_cursor=next_cursor, request_meta=request_meta)

    def iter_entity(
        self,
        entity: str,
        *,
        created_gte: int | None,
        created_lte: int | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        starting_after: str | None = None
        all_records: list[dict[str, Any]] = []
        metrics = {"api_calls": 0, "retries": 0, "failures": 0, "pages": 0}

        while True:
            page = self.list_entity(
                entity,
                created_gte=created_gte,
                created_lte=created_lte,
                starting_after=starting_after,
                limit=limit,
            )
            metrics["api_calls"] += 1
            metrics["pages"] += 1
            metrics["retries"] += int(page.request_meta.get("retries", 0))
            metrics["failures"] += int(page.request_meta.get("failures", 0))
            all_records.extend(page.data)
            if not page.has_more or not page.next_cursor:
                break
            starting_after = page.next_cursor

        return all_records, metrics
