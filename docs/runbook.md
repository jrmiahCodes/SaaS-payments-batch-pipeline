# Runbook

## Daily Operations

1. Start mock API (or source API endpoint).
2. Run extraction:
   - `payments-pipeline run-all --days 1`
3. Run transforms:
   - `payments-pipeline run-transforms`
4. Run quality checks:
   - `payments-pipeline run-quality`
5. Inspect `_state/manifests/run_<run_id>.json` and logs.

## Backfill Procedure

Use a larger lookback window:

- `payments-pipeline run-all --days 7`
- Re-run transforms and quality.

Because Bronze is append-only by `run_id`, backfills are replay-safe.

## Reprocess A Date Safely

1. Keep existing Bronze files unchanged (immutable history).
2. Re-run extraction window that includes target date.
3. Re-run transforms to regenerate partition outputs.
4. Validate quality checks and `_latest` pointers.

## Manifests Rotation

- Keep `_state/manifests/run_<run_id>.json` as immutable run log.
- `_state/manifests/_latest/*.json` is mutable and should point to latest valid artifact.
- Optional housekeeping: archive run manifests older than 90 days.

## Failure Playbooks

### API outage / rate limits

Symptoms:

- HTTP 429/5xx spikes, retry warnings.

Actions:

1. Verify source `/health` and logs.
2. Retry run; retries are automatic for transient failures.
3. Reduce `MAX_PAGE_SIZE` temporarily if source unstable.

### Partial batch writes

Symptoms:

- Missing partitions or fewer records than expected.

Actions:

1. Check run manifest and per-entity extraction metrics.
2. Re-run same command; idempotent output strategy prevents duplicates in downstream layers.

### Schema drift

Symptoms:

- `run-quality` fails schema checks.

Actions:

1. Inspect failing model and missing columns.
2. Update silver SQL mapping and relevant tests.
3. Re-run transforms + quality.

### Webhook signature failures

Symptoms:

- 400 responses from webhook endpoint.

Actions:

1. Validate `WEBHOOK_SECRET` and signing header.
2. Confirm tolerance window and clock skew.
3. For local testing, disable verification explicitly.

### Duplicate webhook deliveries

Symptoms:

- Event already processed.

Actions:

1. Expected behavior: marker-based idempotency should skip duplicate writes.
2. Confirm marker exists in `bronze/.../webhook_events/markers/`.

## Debugging Map

1. Logs (JSON): first stop for command failure and entity-level counters.
2. `_state/watermarks/*.json`: incremental cursor continuity.
3. `_state/manifests/run_<run_id>.json`: run outputs and checks.
4. `_state/manifests/_latest/*.json`: freshness source-of-truth.

Common errors and fixes:

- `S3_BUCKET is required when PIPELINE_ENV=AWS`: set `S3_BUCKET` or switch to LOCAL.
- `duckdb is required for transforms`: install runtime deps from `pyproject.toml`.
- `Mock API not healthy`: ensure mock server is started and port is correct.
