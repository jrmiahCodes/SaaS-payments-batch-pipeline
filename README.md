# SaaS Payments Batch Pipeline

![CI](https://img.shields.io/github/actions/workflow/status/jrmiahCodes/SaaS-payments-batch-pipeline/ci.yml?branch=main)
![License](https://img.shields.io/github/license/jrmiahCodes/SaaS-payments-batch-pipeline)
![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen)
![Architecture](https://img.shields.io/badge/architecture-medallion-orange)
![Engine](https://img.shields.io/badge/engine-DuckDB-yellow)

> Stripe-style Batch ELT to S3 with production Python, data quality checks, CI/CD, and cost-aware design.

This project demonstrates a **production-minded, cloud-ready SaaS ingestion pipeline** using a Stripe-like payments domain.

It is designed to:

- Showcase incremental batch ingestion with watermarks and safety windows
- Demonstrate idempotent processing and replayability
- Implement Medallion-style layering (Bronze / Silver / Gold)
- Use DuckDB for SQL-based transformations
- Include an optional webhook capture module for reconciliation
- Run locally or via GitHub Actions (zero-cost compute)
- Be containerizable and deployable to AWS (S3 + Lambda / ECS) later

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Model](#data-model)
- [Batch vs Webhooks](#batch-vs-webhooks)
- [S3 Layout and Naming](#s3-layout-and-naming)
- [Incremental Loads and Idempotency](#incremental-loads-and-idempotency)
- [Data Quality](#data-quality)
- [Observability](#observability)
- [Running Locally](#running-locally)
- [CI/CD](#cicd)
- [Cost Model](#cost-model)
- [Security Notes](#security-notes)
- [Failure and Recovery](#failure-and-recovery)
- [Architecture Decisions (ADRs)](#architecture-decisions-adrs)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

This is a **portfolio demonstration project** simulating a SaaS payments ingestion pipeline similar to Stripe.

It ingests mock API data for:

- `payment_intents`
- `charges`
- `invoices`
- `customers`

Data flows through a minimal Medallion architecture:

- **Bronze** – raw immutable JSON (append-only)
- **Silver** – typed and flattened Parquet
- **Gold** – curated fact and dimension tables

Key engineering practices:

- Incremental loads with watermarks and safety windows
- Retries with exponential backoff (API and storage)
- Idempotency and safe re-runs
- Structured JSON logging with correlation IDs
- Quality checks (schema, freshness, reconciliation)
- CI and scheduled demo runs via GitHub Actions

---

## Architecture

### Batch Flow

Mock Stripe API  
→ Bronze (raw JSON to S3 or local filesystem)  
→ DuckDB transformations  
→ Silver and Gold (partitioned Parquet)  
→ Query via DuckDB (optional Athena in AWS mode)

### Webhook Flow (Optional)

POST `/webhooks/stripe`  
→ (optional) signature verification  
→ Bronze `webhook_events` capture  
→ Reconciliation vs batch data  

The compute layer runs locally or in GitHub Actions, and can later be deployed to Lambda or ECS without changing core pipeline logic.

More detail: **[`docs/architecture.md`](docs/architecture.md)**

---

## Data Model

### Source Entities

- `payment_intents`
- `charges`
- `invoices`
- `customers`

### Gold Models

- `dim_customers`
- `fct_payments` (payment intents + charges)
- `fct_invoices`

### Webhook Events (Optional)

- `webhook_events` (raw capture)
- optional reconciliation output

---

## Batch vs Webhooks

Batch polling and webhooks are commonly used together in SaaS systems.

| Capability | Batch | Webhooks |
|------------|-------|----------|
| Completeness / backfills | Yes | No |
| Low-latency signals | No | Yes |
| Deterministic reprocessing | Yes | No (retries/out-of-order) |
| Operational complexity | Medium | Medium |

In this demo:

- Batch is authoritative.
- Webhooks are captured and reconciled.
- Webhooks do not directly update Gold models.

---

## S3 Layout and Naming

The layout is consistent across S3 and local demo mode:

- `bronze/source=stripe/entity=charges/dt=YYYY-MM-DD/run_id=<uuid>/`
- `silver/source=stripe/entity=charges/dt=YYYY-MM-DD/`
- `gold/model=fct_payments/dt=YYYY-MM-DD/`
- `_state/watermarks/`
- `_state/manifests/`

Design goals:

- Replayability and auditability
- Clear contracts between layers
- Partition pruning via `dt`
- Cost-aware lifecycle management

---

## Incremental Loads and Idempotency

- Watermark tracked per entity using `created` timestamp
- Safety window prevents missing late-arriving records
- Deduplication via stable entity IDs
- Bronze writes are append-only (run_id isolation)
- Silver and Gold use deterministic partition overwrites or dedupe logic

Backfills can be executed safely without duplicating results.

---

## Data Quality

Quality checks include:

- Schema validation (required columns)
- Freshness validation (expected `dt` partitions)
- Rowcount reconciliation (Bronze → Silver, Silver → Gold)

Quality failures stop pipeline execution.

---

## Observability

- Structured JSON logs
- `run_id` propagated across all steps
- Exceptions include stack traces in logs
- Metrics captured in logs:
  - records processed
  - API calls
  - retries
  - failures

---

## Running Locally

### Setup

    make setup

### Run Mock API

    make mock-api

### Recommended: Full Pipeline In One Command

    make run-pipeline DAYS=1

### You can force a stable run identity across commands using `RUN_ID`:

    RUN_ID=my-run-001 payments-pipeline run-all --days 1
    RUN_ID=my-run-001 payments-pipeline run-transforms
    RUN_ID=my-run-001 payments-pipeline run-quality

### Run Single Entity

    make run-batch ENTITY=charges DAYS=1
	
### Run Batch (all entities)

    make run-all DAYS=1

### Run Webhook Server

    make run-webhooks
	
### Quickstart Validation

Open two terminals.

Terminal 1:

    make mock-api

Expected checks:

- `http://127.0.0.1:8000/health` returns `{"status":"ok"}`
- `http://127.0.0.1:8000/docs` shows Swagger docs

Terminal 2:

    make run-pipeline DAYS=1

Alternative (split commands with stable run identity):

    RUN_ID=demo-run-001 payments-pipeline run-all --days 1
    RUN_ID=demo-run-001 payments-pipeline run-transforms
    RUN_ID=demo-run-001 payments-pipeline run-quality

Expected success signals:

- `run-pipeline` logs extraction (`bronze_write_complete`), transform completion, and quality pass in one flow
- if using split commands, all three commands share the same `run_id` when `RUN_ID` is set

Expected artifacts (default LOCAL mode):

- `_local_data/bronze/source=stripe/entity=*/dt=YYYY-MM-DD/run_id=*/part-*.jsonl`
- `_local_data/silver/source=stripe/entity=*/dt=YYYY-MM-DD/data.parquet`
- `_local_data/gold/model=*/dt=YYYY-MM-DD/data.parquet`
- `_local_data/_state/watermarks/*.json`
- `_local_data/_state/manifests/run_<run_id>.json`

---

## CI/CD

Workflows:

- `ci.yml` — lint and test on push and PR
- `batch_run.yml` — scheduled demo batch run (local mode) using `run-pipeline` for traceability
- `docs.yml` — publish docs via GitHub Pages

---

## Cost Model

Designed for minimal cost:

- Parquet storage
- Partitioned datasets
- Bronze short retention
- Gold longer retention
- Optional Athena pay-per-scan usage

Budget guardrails recommended if deployed to AWS.

See: **[`docs/cost_model.md`](docs/cost_model.md)**

---

## Security Notes

- No credentials committed
- Webhook signature verification supported (toggleable)
- Designed for least-privilege IAM if deployed

---

## Failure and Recovery

Handled scenarios:

- API rate limits
- Partial batch failures
- Duplicate webhook deliveries
- Schema evolution
- Safe re-runs and backfills

See: **[`docs/runbook.md`](docs/runbook.md)**

---

## Architecture Decisions (ADRs)

- [ADR 0001 — Medallion Architecture on S3](docs/adr/0001-medallion-on-s3.md)
- [ADR 0002 — DuckDB for Transformations](docs/adr/0002-duckdb.md)
- [ADR 0003 — GitHub Actions as Scheduler/Compute](docs/adr/0003-github-actions.md)
- [ADR 0004 — Stripe-like Mock API](docs/adr/0004-mock-stripe.md)
- [ADR 0005 — Optional Webhooks Module](docs/adr/0005-webhooks.md)
- [ADR 0006 — Idempotency and Retries](docs/adr/0006-idempotency-and-retries.md)
- [ADR 0007 — Partitioning and File Sizing](docs/adr/0007-partitioning-and-file-sizing.md)

---

## Roadmap

Future enhancements:

- Run in AWS mode against real S3 (same layout as local)
- Athena external tables (optional)
- Optional Postgres serving layer
- Docker containerization
- Swap mock API for real Stripe API
- Event-driven publish model

---

## License

This project is licensed under the terms of the **MIT License**. See [`LICENSE`](LICENSE).