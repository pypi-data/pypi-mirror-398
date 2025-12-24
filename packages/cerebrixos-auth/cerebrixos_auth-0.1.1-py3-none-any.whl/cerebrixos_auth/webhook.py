from __future__ import annotations

import hashlib
import hmac
import time
from typing import Dict, Optional, Tuple

# Header names (case-insensitive in real HTTP servers; but keep a standard)
SIG_HEADER = "x-webhook-signature"
TS_HEADER = "x-webhook-timestamp"
NONCE_HEADER = "x-webhook-nonce"

def sign_webhook_headers(secret: str, body_bytes: bytes, timestamp: Optional[int] = None, nonce: Optional[str] = None) -> Dict[str, str]:
    """Generate headers for a webhook call.

    Signature is HMAC-SHA256 over:
      f"{timestamp}.{nonce}." + body_bytes

    Return headers that the receiver can verify.
    """
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        # simple deterministic nonce; override with uuid if you prefer
        nonce = str(int(time.time() * 1000))

    msg = f"{timestamp}.{nonce}.".encode("utf-8") + body_bytes
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    return {
        TS_HEADER: str(timestamp),
        NONCE_HEADER: nonce,
        SIG_HEADER: sig,
    }

def verify_webhook_request(
    secret: str,
    body_bytes: bytes,
    signature: Optional[str],
    timestamp: Optional[str],
    nonce: Optional[str],
    max_skew_seconds: int = 300,
) -> Tuple[bool, str]:
    """Verify webhook signature + freshness.

    max_skew_seconds: rejects requests that are too old/new to reduce replay window.
    You can also store nonce in a cache/DB for strict anti-replay.
    """
    if not signature or not timestamp or not nonce:
        return False, "Missing webhook signature headers"

    try:
        ts_int = int(timestamp)
    except ValueError:
        return False, "Invalid timestamp"

    now = int(time.time())
    if abs(now - ts_int) > int(max_skew_seconds):
        return False, "Timestamp outside allowed skew"

    msg = f"{ts_int}.{nonce}.".encode("utf-8") + body_bytes
    expected = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return False, "Signature mismatch"
    return True, "OK"
