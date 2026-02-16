"""UTC-first time helpers used across the pipeline."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def to_iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).isoformat()


def parse_ts(value: str | int | float | datetime) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=UTC)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def dt_partition(value: date | datetime | str) -> str:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    ts = parse_ts(value) if not isinstance(value, datetime) else value
    return ts.astimezone(UTC).date().isoformat()


def subtract_seconds(ts: datetime, seconds: int) -> datetime:
    return ts - timedelta(seconds=seconds)
