# ADR 0007 - Partitioning And File Sizing

**Status:** Accepted

## Context

Query efficiency and storage cost depend on partition strategy and file size. Over-partitioning or tiny files can degrade performance.

## Decision

Use `dt` as the primary partition key across Bronze/Silver/Gold.

- Bronze: per-run JSONL chunks.
- Silver/Gold: Parquet outputs partitioned by `dt`.

File sizing guidance:

- Chunk Bronze writes to avoid excessive tiny files.
- Prefer fewer larger Parquet files per partition for read efficiency.

## Consequences

Positive:

- Strong partition pruning for date-bound queries.
- Simpler retention/lifecycle operations by `dt`.

Trade-offs:

- Too many `dt` partitions can increase metadata overhead.
- Too few partitions can increase scan volume.

## Evolution Path

If data volume grows substantially:

1. Add secondary partitioning/bucketing where justified.
2. Introduce compaction jobs.
3. Re-evaluate model-level partition keys based on query patterns.
