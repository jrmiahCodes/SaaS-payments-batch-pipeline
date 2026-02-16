# ADR 0004 - Deterministic Stripe-Like Mock API

**Status:** Accepted

## Context

We need realistic ingestion behavior without external credentials, billing risk, or unstable test data.

## Decision

Provide a mock Stripe-style API with deterministic data generation and endpoints:

- `/v1/payment_intents`
- `/v1/charges`
- `/v1/invoices`
- `/v1/customers`
- `/health`

Contract features:

- Filtering by `created_gte` / `created_lte`
- Stable ordering (`created`, then `id`)
- Cursor pagination via `starting_after`
- Response shape `{object, data, has_more, url}`

## Consequences

Positive:

- Repeatable CI and integration tests.
- No dependency on real Stripe account/auth.

Trade-offs:

- Not all Stripe semantics/fields are represented.

## Interface Boundary

`StripeLikeClient` protocol isolates the extractor from provider specifics so real Stripe can replace mock client with minimal code changes.

## Real Stripe Delta

Real Stripe integration would add API auth, expansions, stricter rate-limit behavior, and broader schemas.
