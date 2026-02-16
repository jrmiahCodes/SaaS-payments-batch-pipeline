# ADR 0001 - Medallion Architecture On S3-Compatible Paths

**Status:** Accepted

## Context

The pipeline needs replayability, clear layer contracts, and low operating cost while running in local mode and CI today, with S3 portability later.

## Decision

Use a Bronze/Silver/Gold architecture with explicit key conventions:

- `bronze/source=stripe/entity=<entity>/dt=YYYY-MM-DD/run_id=<run_id>/part-*.jsonl`
- `silver/source=stripe/entity=<entity>/dt=YYYY-MM-DD/data.parquet`
- `gold/model=<model>/dt=YYYY-MM-DD/data.parquet`

Bronze is immutable and append-only per `run_id`.

## Consequences

Positive:

- Clear contracts between ingest and transform.
- Safe backfills and auditability through immutable Bronze.
- Straightforward partition pruning using `dt`.

Trade-offs:

- More objects to manage than a single-table approach.
- Need lifecycle policies to control Bronze storage growth.

Lifecycle implications:

- Bronze can have shorter retention.
- Silver/Gold retain longer for analytics and lineage.

## Alternatives Considered

- Single raw zone only (weaker contracts and consumption ergonomics).
- Direct warehouse ingestion (higher initial cost and coupling).
