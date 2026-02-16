"""Structured JSON logging helpers."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any

_RUN_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar("run_id", default=None)
_CORR_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", None) or _RUN_ID.get(),
            "correlation_id": getattr(record, "correlation_id", None) or _CORR_ID.get(),
            "entity": getattr(record, "entity", None),
            "step": getattr(record, "step", None),
        }
        for key, value in record.__dict__.items():
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            if key not in payload:
                payload[key] = value
        return json.dumps(payload, default=str)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = _RUN_ID.get()
        if not hasattr(record, "correlation_id"):
            record.correlation_id = _CORR_ID.get()
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(ContextFilter())
    root.addHandler(handler)


def set_run_context(run_id: str | None = None, correlation_id: str | None = None) -> None:
    if run_id is not None:
        _RUN_ID.set(run_id)
    if correlation_id is not None:
        _CORR_ID.set(correlation_id)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
