from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple
import requests

# Very small in-memory cache. If you run multi-process (gunicorn), each worker caches independently.
_JWKS_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

def _get_cached(cache_key: str) -> Optional[Dict[str, Any]]:
    item = _JWKS_CACHE.get(cache_key)
    if not item:
        return None
    expires_at, value = item
    if time.time() > expires_at:
        _JWKS_CACHE.pop(cache_key, None)
        return None
    return value

def _set_cached(cache_key: str, value: Dict[str, Any], ttl_seconds: int) -> None:
    _JWKS_CACHE[cache_key] = (time.time() + ttl_seconds, value)

def fetch_oidc_jwks(issuer: str, cache_ttl_seconds: int = 3600, timeout_seconds: int = 5) -> Dict[str, Any]:
    """Fetch OIDC metadata then JWKS. Caches results in-process.

    issuer: e.g. https://auth.example.com
    Returns: JWKS dict (must contain 'keys')
    """
    issuer = issuer.rstrip("/")
    cache_key = f"jwks::{issuer}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    # OIDC discovery
    discovery_url = f"{issuer}/.well-known/openid-configuration"
    r = requests.get(discovery_url, timeout=timeout_seconds)
    r.raise_for_status()
    meta = r.json()
    jwks_uri = meta.get("jwks_uri")
    if not jwks_uri:
        raise RuntimeError("OIDC discovery did not provide jwks_uri")

    r2 = requests.get(jwks_uri, timeout=timeout_seconds)
    r2.raise_for_status()
    jwks = r2.json()
    if "keys" not in jwks:
        raise RuntimeError("JWKS response missing 'keys'")

    _set_cached(cache_key, jwks, cache_ttl_seconds)
    return jwks
