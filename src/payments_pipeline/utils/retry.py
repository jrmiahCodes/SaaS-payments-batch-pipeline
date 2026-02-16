"""Lightweight retry utilities with backoff and jitter."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RetryConfig:
    max_attempts: int = 4
    base_delay_seconds: float = 0.3
    max_delay_seconds: float = 5.0
    jitter_ratio: float = 0.2


def retry_call(
    func: Callable[[], T],
    *,
    retryable_exceptions: tuple[type[Exception], ...],
    config: RetryConfig | None = None,
    logger: logging.Logger | None = None,
    metrics: dict[str, int] | None = None,
) -> T:
    cfg = config or RetryConfig()
    attempt = 0
    while True:
        attempt += 1
        try:
            return func()
        except retryable_exceptions as exc:
            if metrics is not None:
                metrics["retries"] = metrics.get("retries", 0) + 1
            if attempt >= cfg.max_attempts:
                if metrics is not None:
                    metrics["failures"] = metrics.get("failures", 0) + 1
                if logger:
                    logger.error(
                        "retry_exhausted",
                        extra={"attempt": attempt, "error": str(exc)},
                    )
                raise
            exp_delay = min(cfg.max_delay_seconds, cfg.base_delay_seconds * (2 ** (attempt - 1)))
            jitter = exp_delay * cfg.jitter_ratio * random.random()
            sleep_for = exp_delay + jitter
            if logger:
                logger.warning(
                    "retrying",
                    extra={
                        "attempt": attempt,
                        "sleep_seconds": round(sleep_for, 3),
                        "error": str(exc),
                    },
                )
            time.sleep(sleep_for)


def retry(
    *,
    retryable_exceptions: tuple[type[Exception], ...],
    config: RetryConfig | None = None,
    logger: logging.Logger | None = None,
    metrics: dict[str, int] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return retry_call(
                lambda: func(*args, **kwargs),
                retryable_exceptions=retryable_exceptions,
                config=config,
                logger=logger,
                metrics=metrics,
            )

        return wrapper

    return decorator
