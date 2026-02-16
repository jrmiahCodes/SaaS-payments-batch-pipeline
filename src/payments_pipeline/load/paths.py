"""Naming conventions for bronze/silver/gold/state objects."""

from __future__ import annotations

from pathlib import Path

from payments_pipeline.config.settings import Settings


def bronze_relative_path(entity: str, dt: str, run_id: str, part: int = 0) -> str:
    return f"bronze/source=stripe/entity={entity}/dt={dt}/run_id={run_id}/part-{part:05d}.jsonl"


def silver_relative_path(entity: str, dt: str) -> str:
    return f"silver/source=stripe/entity={entity}/dt={dt}/data.parquet"


def gold_relative_path(model: str, dt: str) -> str:
    return f"gold/model={model}/dt={dt}/data.parquet"


def watermark_relative_path(entity: str) -> str:
    return f"_state/watermarks/{entity}.json"


def manifest_relative_path(run_id: str) -> str:
    return f"_state/manifests/run_{run_id}.json"


def latest_model_relative_path(model: str) -> str:
    return f"_state/manifests/_latest/{model}.json"


def recon_relative_path(dt: str) -> str:
    return f"_state/manifests/recon_{dt}.json"


def to_local_path(settings: Settings, relative_path: str) -> Path:
    return settings.local_data_dir / relative_path


def state_local_dir(settings: Settings) -> Path:
    return settings.state_root
