"""Webhook handling logic."""

from __future__ import annotations

from dataclasses import dataclass

from payments_pipeline.clients.webhook_signing import (
    SignatureVerificationError,
    extract_event_id,
    verify_signature,
)
from payments_pipeline.config.logging import get_logger
from payments_pipeline.config.settings import Settings
from payments_pipeline.webhooks.repository import WebhookRepository


@dataclass(slots=True)
class HandlerResult:
    accepted: bool
    duplicate: bool
    event_id: str
    stored_path: str | None


def handle_stripe_webhook(
    payload_bytes: bytes, headers: dict[str, str], settings: Settings
) -> HandlerResult:
    logger = get_logger(__name__)

    signature_header = headers.get("stripe-signature") or headers.get("Stripe-Signature")
    if settings.verify_webhook_signatures:
        verify_signature(
            payload_bytes,
            header_value=signature_header,
            secret=settings.webhook_secret,
            tolerance_seconds=settings.safety_window_seconds,
        )

    event_id = extract_event_id(payload_bytes)
    repo = WebhookRepository(settings)

    if repo.exists(event_id):
        logger.info("webhook_duplicate", extra={"event_id": event_id})
        return HandlerResult(accepted=True, duplicate=True, event_id=event_id, stored_path=None)

    stored = repo.write(event_id=event_id, payload=payload_bytes, headers=headers)
    logger.info("webhook_stored", extra={"event_id": event_id, "path": stored})
    return HandlerResult(accepted=True, duplicate=False, event_id=event_id, stored_path=stored)


__all__ = ["HandlerResult", "SignatureVerificationError", "handle_stripe_webhook"]
