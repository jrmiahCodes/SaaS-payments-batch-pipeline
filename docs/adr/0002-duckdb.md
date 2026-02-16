# ADR 0002 - DuckDB For Local And CI Transforms

**Status:** Accepted

## Context

We need SQL-first transformations with zero dedicated infrastructure and deterministic behavior in local development and GitHub Actions.

## Decision

Use DuckDB as the transform engine.

- Execute Silver models first, then Gold models.
- Keep SQL models in `src/payments_pipeline/transform/sql/silver/` and `src/payments_pipeline/transform/sql/gold/`.
- Materialize outputs as partitioned Parquet files.

## Consequences

Positive:

- Minimal cost and simple developer setup.
- Portable SQL-centric workflow.

Trade-offs:

- Not designed for high-concurrency serving.
- Large-scale distributed processing is out of scope.

Non-goals:

- Serving low-latency BI with concurrent users.
- Handling very large distributed workloads.

## Alternatives Considered

- Spark/Databricks.
- Warehouse-native transforms (Snowflake/Redshift/BigQuery).

## Migration Path

Keep model contracts and CLI stable; replace transform execution backend with Spark or warehouse jobs if scale requires it.
