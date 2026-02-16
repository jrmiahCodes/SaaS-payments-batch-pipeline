# ADR 0006 - Idempotency And Retries

**Status:** Accepted

## Context

Pipeline runs may fail due to transient network/API/storage issues and must be safely rerunnable without creating duplicate analytical outputs.

## Decision

Define idempotency per stage:

- Bronze batch: append-only under `run_id` path.
- Webhooks: unique marker per `event_id` (or stable payload hash).
- Silver/Gold: deterministic model execution and partition writes.

Define retry policy:

- Retryable: network failures, HTTP 429/5xx, transient storage write/read errors.
- Non-retryable: schema/contract violations, invalid signatures, deterministic SQL logic errors.

## Consequences

Positive:

- Safe reruns and clearer failure semantics.
- Reduced operator intervention for transient incidents.

Trade-offs:

- Duplicate raw Bronze records can exist across retries/reruns; downstream models must remain deterministic.

## Safe Rerun Procedure

Re-run failed command with same parameters; validate manifests/quality outputs. No destructive rollback of immutable Bronze is required.
