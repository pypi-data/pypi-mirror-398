from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Tuple

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

def sign_download_token(signing_key: str, path: str, ttl_seconds: int) -> str:
    """Create a short-lived token for file URLs.

    Token format: <exp>.<sig>
      exp: unix epoch seconds
      sig: b64url(HMAC-SHA256(key, f"{exp}:{path}"))
    """
    exp = int(time.time()) + int(ttl_seconds)
    msg = f"{exp}:{path}".encode("utf-8")
    sig = hmac.new(signing_key.encode("utf-8"), msg, hashlib.sha256).digest()
    return f"{exp}.{_b64url(sig)}"

def verify_download_token(signing_key: str, token: str, path: str) -> Tuple[bool, str]:
    """Verify a download token for a path."""
    try:
        exp_str, sig_b64 = token.split(".", 1)
        exp = int(exp_str)
    except Exception:
        return False, "Malformed token"

    if int(time.time()) > exp:
        return False, "Token expired"

    msg = f"{exp}:{path}".encode("utf-8")
    expected = hmac.new(signing_key.encode("utf-8"), msg, hashlib.sha256).digest()
    got = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected, got):
        return False, "Signature mismatch"
    return True, "OK"
