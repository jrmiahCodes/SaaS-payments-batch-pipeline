"""Identifier helpers for run/correlation/idempotency keys."""

from __future__ import annotations

import hashlib
import re
import uuid

_SAFE_ID_PATTERN = re.compile(r"[^A-Za-z0-9_.=-]+")


def new_run_id() -> str:
    return str(uuid.uuid4())


def new_correlation_id() -> str:
    return str(uuid.uuid4())


def stable_hash_id(payload_bytes: bytes) -> str:
    return hashlib.sha256(payload_bytes).hexdigest()


def sanitize_id_for_path(value: str) -> str:
    cleaned = _SAFE_ID_PATTERN.sub("_", value.strip())
    return cleaned.strip("._") or "unknown"
