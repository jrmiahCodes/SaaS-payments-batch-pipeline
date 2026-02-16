"""Run manifests and latest model pointers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from payments_pipeline.utils.time import to_iso, utc_now


@dataclass(slots=True)
class ManifestStore:
    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "_latest").mkdir(parents=True, exist_ok=True)

    def write_run_manifest(self, run_id: str, payload: dict[str, Any]) -> Path:
        path = self.root / f"run_{run_id}.json"
        wrapped = {
            "run_id": run_id,
            "written_at": to_iso(utc_now()),
            "payload": payload,
        }
        path.write_text(json.dumps(wrapped, indent=2, default=str), encoding="utf-8")
        return path

    def write_latest_model(self, model: str, run_id: str, dt: str, path: str) -> Path:
        latest = self.root / "_latest" / f"{model}.json"
        payload = {
            "model": model,
            "run_id": run_id,
            "dt": dt,
            "path": path,
            "updated_at": to_iso(utc_now()),
        }
        latest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return latest

    def read_latest_model(self, model: str) -> dict[str, Any] | None:
        latest = self.root / "_latest" / f"{model}.json"
        if not latest.exists():
            return None
        return json.loads(latest.read_text(encoding="utf-8"))

    def write_reconciliation(self, dt: str, report: dict[str, Any]) -> Path:
        path = self.root / f"recon_{dt}.json"
        payload = {"dt": dt, "written_at": to_iso(utc_now()), "report": report}
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path


def write_run_manifest(store: ManifestStore, run_id: str, payload: dict[str, Any]) -> Path:
    return store.write_run_manifest(run_id, payload)


def write_latest(store: ManifestStore, model: str, run_id: str, dt: str, path: str) -> Path:
    return store.write_latest_model(model=model, run_id=run_id, dt=dt, path=path)


def read_latest(store: ManifestStore, model: str) -> dict[str, Any] | None:
    return store.read_latest_model(model)
