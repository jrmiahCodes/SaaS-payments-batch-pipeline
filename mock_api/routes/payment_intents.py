"""Payment intents route."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from mock_api.data_generator import filter_and_paginate

router = APIRouter()


@router.get("/v1/payment_intents")
def list_payment_intents(
    request: Request,
    created_gte: int | None = Query(default=None),
    created_lte: int | None = Query(default=None),
    starting_after: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    records = request.app.state.dataset["payment_intents"]
    page, has_more = filter_and_paginate(
        records,
        created_gte=created_gte,
        created_lte=created_lte,
        starting_after=starting_after,
        limit=limit,
    )
    return {"object": "list", "data": page, "has_more": has_more, "url": "/v1/payment_intents"}
