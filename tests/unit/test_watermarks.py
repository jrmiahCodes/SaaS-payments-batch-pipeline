from pathlib import Path

from payments_pipeline.state.watermarks import WatermarkStore, commit, get_window


def test_watermark_window_and_commit(tmp_path: Path) -> None:
    store = WatermarkStore(tmp_path)
    window = get_window("charges", now_ts=1700000000, days=1, safety_window=300, store=store)
    assert window.start_ts <= window.end_ts

    commit("charges", new_watermark=1700000000, run_id="run-123", store=store)
    state = store.load("charges")
    assert state.last_success_created_ts == 1700000000
    assert state.last_run_id == "run-123"

    window2 = get_window("charges", now_ts=1700000200, days=1, safety_window=300, store=store)
    assert window2.start_ts == 1699999700
