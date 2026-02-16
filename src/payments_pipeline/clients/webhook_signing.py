"""Stripe-compatible webhook signature verification utilities."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from payments_pipeline.config.logging import get_logger
from payments_pipeline.utils.ids import stable_hash_id


class SignatureVerificationError(Exception):
    pass


@dataclass(slots=True)
class ParsedSignature:
    timestamp: int
    signatures: list[str]


def _parse_signature_header(header_value: str) -> ParsedSignature:
    timestamp: int | None = None
    signatures: list[str] = []
    for piece in header_value.split(","):
        if "=" not in piece:
            continue
        key, val = piece.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key == "t":
            timestamp = int(val)
        elif key == "v1":
            signatures.append(val)
    if timestamp is None or not signatures:
        raise SignatureVerificationError("Invalid Stripe-Signature header")
    return ParsedSignature(timestamp=timestamp, signatures=signatures)


def verify_signature(
    payload_bytes: bytes,
    header_value: str | None,
    secret: str | None,
    tolerance_seconds: int = 300,
) -> bool:
    logger = get_logger(__name__)
    if not secret:
        logger.info("webhook_signature_skipped", extra={"reason": "missing_secret"})
        return True
    if not header_value:
        raise SignatureVerificationError("Missing Stripe-Signature header")

    parsed = _parse_signature_header(header_value)
    age = abs(int(time.time()) - parsed.timestamp)
    if tolerance_seconds >= 0 and age > tolerance_seconds:
        raise SignatureVerificationError("Signature timestamp outside tolerance")

    signed_payload = f"{parsed.timestamp}.".encode("utf-8") + payload_bytes
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, sig) for sig in parsed.signatures):
        raise SignatureVerificationError("Invalid signature")
    return True


def extract_event_id(payload_bytes: bytes) -> str:
    try:
        payload: dict[str, Any] = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return stable_hash_id(payload_bytes)

    event_id = payload.get("id")
    if isinstance(event_id, str) and event_id.strip():
        return event_id
    return stable_hash_id(payload_bytes)
