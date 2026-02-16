# ADR 0003 - GitHub Actions For CI, Scheduling, And Demo Compute

**Status:** Accepted

## Context

The project prioritizes repeatability, visibility, and zero/low cost for portfolio-friendly operations.

## Decision

Use GitHub Actions for:

- CI (`lint`, `format check`, `mypy`, `pytest`).
- Scheduled batch demonstration runs.
- Publishing docs to GitHub Pages.

## Consequences

Positive:

- Transparent logs and reproducible runs.
- No separate scheduler/compute infra required initially.

Limitations:

- Runner runtime caps and resource limits.
- Dataset size must stay within manageable bounds.

Mitigation:

- Constrain `--days` history windows.
- Keep datasets deterministic and compact.

## Future Path

Reuse the same CLI commands in ECS tasks or Lambda orchestration if workload outgrows Actions.
