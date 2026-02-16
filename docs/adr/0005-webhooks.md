# ADR 0005 - Optional Webhooks For Capture And Reconciliation

**Status:** Accepted

## Context

SaaS systems often use both polling and webhooks. Polling gives completeness/backfill; webhooks provide low-latency signals.

## Decision

Implement webhooks as optional capture/reconciliation, not the authoritative marts builder.

- Endpoint: `POST /webhooks/stripe`
- Optional signature verification controlled by config flags.
- Event idempotency via `event_id` marker (or deterministic payload hash fallback).

## Consequences

Positive:

- Demonstrates real-world dual-ingestion architecture.
- Supports duplicate-delivery handling and forensic replay.

Trade-offs:

- Additional operational path to monitor.

## Batch vs Webhook Positioning

- Batch remains source of truth for Silver/Gold.
- Webhooks improve observability and timeliness but do not directly mutate marts.
