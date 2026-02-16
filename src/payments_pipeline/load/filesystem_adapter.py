"""Filesystem-backed object storage adapter for LOCAL mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FilesystemAdapter:
    def __init__(self, root: Path):
        self.root = root

    def _resolve(self, relative_path: str) -> Path:
        normalized = Path(relative_path)
        if normalized.is_absolute():
            raise ValueError("Path must be relative")
        resolved = (self.root / normalized).resolve()
        root = self.root.resolve()
        if root not in resolved.parents and resolved != root:
            raise ValueError(f"Unsafe path outside root: {relative_path}")
        return resolved

    def put_bytes(self, path: str, data: bytes) -> str:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return str(target)

    def put_json(self, path: str, obj: Any) -> str:
        return self.put_bytes(path, json.dumps(obj, default=str).encode("utf-8"))

    def list(self, prefix: str) -> list[str]:
        base = self._resolve(prefix)
        if not base.exists():
            return []
        if base.is_file():
            return [str(base)]
        return sorted(str(item) for item in base.rglob("*") if item.is_file())

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
