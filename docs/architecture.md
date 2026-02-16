# Architecture

## System Overview

```text
                    +----------------------+
                    |  mock_api (FastAPI)  |
                    | /v1/* + /health      |
                    +----------+-----------+
                               |
                               | list(entity, created window, pagination)
                               v
+---------------------+   +---------------------------+   +-----------------------+
| payments-pipeline   |-->| Bronze (raw JSONL)       |-->| DuckDB SQL transforms |
| CLI (run-all etc.)  |   | bronze/source=stripe/... |   | silver then gold      |
+----------+----------+   +-------------+-------------+   +-----------+-----------+
           |                            |                             |
           |                            v                             v
           |                    _state/watermarks            silver/* + gold/* parquet
           |                    _state/manifests
           |
           v
+---------------------+
| Quality checks      |
| schema/freshness/   |
| reconciliation      |
+---------------------+
```

## Batch Flow

1. CLI creates `run_id`, loads settings, and initializes JSON logging.
2. Each extractor computes an incremental window from watermark plus safety window.
3. Extracted API records are wrapped as `{data, meta}` and written append-only to Bronze under `run_id`.
4. DuckDB SQL builds Silver typed tables from Bronze, then Gold facts/dimensions from Silver.
5. Quality checks validate schema, freshness, and rowcount/referential consistency.
6. Manifest files record outputs and `_latest` pointers for Gold models.

## Webhook Flow (Optional)

1. `POST /webhooks/stripe` receives raw payload and headers.
2. Signature verification can be enabled with `VERIFY_WEBHOOK_SIGNATURES=true` and `WEBHOOK_SECRET`.
3. Event idempotency is enforced via marker object keyed by `event_id` (or deterministic payload hash fallback).
4. Events are stored in Bronze `webhook_events` for audit and reconciliation.

## Storage Layout and S3 Mapping

Local and S3 use the same logical keys:

- `bronze/source=stripe/entity=<entity>/dt=YYYY-MM-DD/run_id=<run_id>/part-00000.jsonl`
- `silver/source=stripe/entity=<entity>/dt=YYYY-MM-DD/data.parquet`
- `gold/model=<model>/dt=YYYY-MM-DD/data.parquet`
- `_state/watermarks/<entity>.json`
- `_state/manifests/run_<run_id>.json`
- `_state/manifests/_latest/<gold_model>.json`

In `PIPELINE_ENV=LOCAL`, keys are rooted at `LOCAL_DATA_DIR`.
In `PIPELINE_ENV=AWS`, keys map to `s3://<S3_BUCKET>/...`.

## Design For Portability

Current deployment mode:

- Compute: local shell or GitHub Actions runner
- Storage: local filesystem in CI (`_local_data/`) or optional S3

Future deployment path without core rewrites:

- Keep CLI and module boundaries unchanged
- Move scheduler/compute to ECS task or Lambda orchestration
- Keep pathing and contracts stable so quality/ops procedures remain valid

## Interface Boundaries

- `clients/stripe_like_interface.py`: source system contract
- `extract/*`: extraction and Bronze envelope contract
- `transform/sql/*`: declarative model logic
- `quality/*`: post-transform validations
- `state/*`: run continuity and discoverability

## Data Contracts

### Silver Guarantees

- One table per source entity
- Stable primary key column `id`
- Typed scalar columns from raw payload
- `created_ts` normalized to UTC timestamp
- `dt` partition field for pruning

### Gold Guarantees

- Business-friendly grain with documented join assumptions
- Deterministic model outputs per `dt` partition
- Manifest `_latest` pointer for consumption/freshness checks
