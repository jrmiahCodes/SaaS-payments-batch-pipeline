"""Stable interface for Stripe-like API clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class ListPage:
    entity: str
    data: list[dict[str, Any]]
    has_more: bool
    next_cursor: str | None
    request_meta: dict[str, Any]


class StripeLikeClient(Protocol):
    def list_entity(
        self,
        entity: str,
        *,
        created_gte: int | None,
        created_lte: int | None,
        starting_after: str | None,
        limit: int,
    ) -> ListPage:
        ...

    def iter_entity(
        self,
        entity: str,
        *,
        created_gte: int | None,
        created_lte: int | None,
        limit: int,
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        ...
