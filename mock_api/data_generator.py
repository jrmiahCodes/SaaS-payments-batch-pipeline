"""Deterministic mock Stripe-style data generator."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    seed: int = 42
    days: int = 30
    customers_per_day: int = 5


def _stable_id(prefix: str, key: str) -> str:
    digest = hashlib.sha256(f"{prefix}:{key}".encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _created_ts(day_start: datetime, offset_seconds: int) -> int:
    return int((day_start + timedelta(seconds=offset_seconds)).timestamp())


def generate_dataset(config: GenerationConfig | None = None) -> dict[str, list[dict[str, Any]]]:
    cfg = config or GenerationConfig()
    rng = random.Random(cfg.seed)

    now = datetime.now(tz=UTC)
    start_day = datetime(now.year, now.month, now.day, tzinfo=UTC) - timedelta(days=cfg.days)

    customers: list[dict[str, Any]] = []
    invoices: list[dict[str, Any]] = []
    payment_intents: list[dict[str, Any]] = []
    charges: list[dict[str, Any]] = []

    for d in range(cfg.days + 1):
        day = start_day + timedelta(days=d)
        for idx in range(cfg.customers_per_day):
            customer_key = f"{day.date()}:{idx}"
            customer_id = _stable_id("cus", customer_key)
            created = _created_ts(day, idx * 600)
            customer = {
                "id": customer_id,
                "object": "customer",
                "created": created,
                "email": f"user{idx}@example.com",
                "name": f"Customer {idx}",
                "metadata": {"segment": "demo"},
            }
            customers.append(customer)

            invoice_id = _stable_id("in", customer_key)
            period_start = created
            period_end = created + 2592000
            total = rng.randint(1000, 20000)
            invoice = {
                "id": invoice_id,
                "object": "invoice",
                "created": created + 120,
                "due_date": created + 7 * 86400,
                "status": "paid",
                "customer": customer_id,
                "total": total,
                "amount_due": total,
                "period_start": period_start,
                "period_end": period_end,
            }
            invoices.append(invoice)

            pi_id = _stable_id("pi", customer_key)
            charge_id = _stable_id("ch", customer_key)
            pi = {
                "id": pi_id,
                "object": "payment_intent",
                "created": created + 300,
                "amount": total,
                "currency": "usd",
                "status": "succeeded",
                "customer": customer_id,
                "latest_charge": charge_id,
                "invoice": invoice_id,
            }
            payment_intents.append(pi)

            charge = {
                "id": charge_id,
                "object": "charge",
                "created": created + 360,
                "amount": total,
                "currency": "usd",
                "status": "succeeded",
                "customer": customer_id,
                "payment_intent": pi_id,
                "invoice": invoice_id,
            }
            charges.append(charge)

    def _sort(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(rows, key=lambda r: (int(r["created"]), str(r["id"])))

    return {
        "customers": _sort(customers),
        "invoices": _sort(invoices),
        "payment_intents": _sort(payment_intents),
        "charges": _sort(charges),
    }


def filter_and_paginate(
    records: list[dict[str, Any]],
    *,
    created_gte: int | None,
    created_lte: int | None,
    starting_after: str | None,
    limit: int,
) -> tuple[list[dict[str, Any]], bool]:
    data = records
    if created_gte is not None:
        data = [r for r in data if int(r["created"]) >= int(created_gte)]
    if created_lte is not None:
        data = [r for r in data if int(r["created"]) <= int(created_lte)]

    if starting_after:
        start_idx = next((idx for idx, row in enumerate(data) if row["id"] == starting_after), None)
        if start_idx is not None:
            data = data[start_idx + 1 :]

    page = data[:limit]
    has_more = len(data) > limit
    return page, has_more
