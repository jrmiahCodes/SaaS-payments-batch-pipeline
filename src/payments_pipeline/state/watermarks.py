"""Watermark state management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from payments_pipeline.utils.time import parse_ts, to_iso, utc_now


@dataclass(slots=True)
class Window:
    start_ts: int
    end_ts: int


@dataclass(slots=True)
class WatermarkState:
    last_success_created_ts: int | None
    last_run_id: str | None
    updated_at: str | None


class WatermarkStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, entity: str) -> Path:
        return self.root / f"{entity}.json"

    def load(self, entity: str) -> WatermarkState:
        path = self._path(entity)
        if not path.exists():
            return WatermarkState(last_success_created_ts=None, last_run_id=None, updated_at=None)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = path.with_suffix(".corrupt.json")
            path.rename(backup)
            return WatermarkState(last_success_created_ts=None, last_run_id=None, updated_at=None)
        return WatermarkState(
            last_success_created_ts=payload.get("last_success_created_ts"),
            last_run_id=payload.get("last_run_id"),
            updated_at=payload.get("updated_at"),
        )

    def commit(self, entity: str, new_watermark: int, run_id: str) -> Path:
        path = self._path(entity)
        tmp = path.with_suffix(".tmp")
        payload = {
            "last_success_created_ts": int(new_watermark),
            "last_run_id": run_id,
            "updated_at": to_iso(utc_now()),
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)
        return path


def get_window(
    entity: str, now_ts: int, days: int, safety_window: int, store: WatermarkStore
) -> Window:
    state = store.load(entity)
    if state.last_success_created_ts is None:
        start_dt = parse_ts(now_ts) - timedelta(days=days)
        start_ts = int(start_dt.timestamp())
    else:
        start_ts = max(0, int(state.last_success_created_ts) - int(safety_window))
    end_ts = int(now_ts)
    if start_ts > end_ts:
        start_ts = end_ts
    return Window(start_ts=start_ts, end_ts=end_ts)


def commit(entity: str, new_watermark: int, run_id: str, store: WatermarkStore) -> Path:
    return store.commit(entity=entity, new_watermark=new_watermark, run_id=run_id)
