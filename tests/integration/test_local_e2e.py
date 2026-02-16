import os
import subprocess
import time
from pathlib import Path

import requests

from payments_pipeline.cli import main
from payments_pipeline.config.settings import get_settings


def _wait_for_health(url: str, timeout: float = 15.0) -> None:
    started = time.time()
    while time.time() - started < timeout:
        try:
            resp = requests.get(url, timeout=1)
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise AssertionError(f"Service did not become healthy: {url}")


def test_local_mode_end_to_end(tmp_path: Path, monkeypatch) -> None:
    api_port = 8011
    api_proc = subprocess.Popen(
        [
            os.environ.get("PYTHON", "python3"),
            "-m",
            "uvicorn",
            "mock_api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_for_health(f"http://127.0.0.1:{api_port}/health")

        monkeypatch.setenv("PIPELINE_ENV", "LOCAL")
        monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path / "_local_data"))
        monkeypatch.setenv("MOCK_API_BASE_URL", f"http://127.0.0.1:{api_port}")
        monkeypatch.setenv("MAX_PAGE_SIZE", "50")
        get_settings.cache_clear()

        assert main(["run-all", "--days", "1"]) == 0
        assert main(["run-transforms"]) == 0
        assert main(["run-quality"]) == 0

        assert (tmp_path / "_local_data" / "bronze").exists()
        assert (tmp_path / "_local_data" / "silver").exists()
        assert (tmp_path / "_local_data" / "gold").exists()
        assert any((tmp_path / "_local_data" / "gold").rglob("data.parquet"))
    finally:
        api_proc.terminate()
        api_proc.wait(timeout=10)
        get_settings.cache_clear()
