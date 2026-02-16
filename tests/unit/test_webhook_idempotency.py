import json
from pathlib import Path

from payments_pipeline.config.settings import Settings
from payments_pipeline.webhooks.handler import handle_stripe_webhook


def test_webhook_idempotency(tmp_path: Path) -> None:
    settings = Settings(
        pipeline_env="LOCAL",
        local_data_dir=tmp_path,
        verify_webhook_signatures=False,
    )

    payload = json.dumps({"id": "evt_test_1", "type": "invoice.paid"}).encode("utf-8")
    headers = {"content-type": "application/json"}

    first = handle_stripe_webhook(payload, headers, settings)
    second = handle_stripe_webhook(payload, headers, settings)

    assert first.accepted is True
    assert first.duplicate is False
    assert second.duplicate is True
