from __future__ import annotations

from typing import Any, Dict, Optional
from .config import AuthConfig
from .jwks import fetch_oidc_jwks

from jose import jwt as jose_jwt
from jose.exceptions import JWTError, ExpiredSignatureError

def _strip_bearer(auth_header: Optional[str]) -> str:
    if not auth_header:
        raise ValueError("Missing Bearer token")
    if not auth_header.lower().startswith("bearer "):
        raise ValueError("Authorization header must be: Bearer <jwt>")
    return auth_header.split(" ", 1)[1].strip()

def verify_jwt_payload(token: str, cfg: AuthConfig) -> Dict[str, Any]:
    """Verify a JWT and return its claims payload.

    Test mode:
      - HS256 using cfg.test_jwt_secret

    Prod mode:
      - OIDC/JWKS from cfg.oidc_issuer
      - expected audience cfg.oidc_audience
      - expected issuer cfg.oidc_issuer
      - algorithm: RS256 (or whatever key supports; jose will enforce via headers)
    """
    try:
        if cfg.cerebrix_env == "test":
            # HS256 (shared secret) for local testing only.
            payload = jose_jwt.decode(
                token,
                cfg.test_jwt_secret,
                algorithms=["HS256"],
                audience=cfg.oidc_audience,
                issuer=cfg.oidc_issuer,
                options={"verify_at_hash": False},
            )
            return payload

        # prod: JWKS
        jwks = fetch_oidc_jwks(
            cfg.oidc_issuer,
            cache_ttl_seconds=cfg.jwks_cache_ttl_seconds,
            timeout_seconds=cfg.jwks_timeout_seconds,
        )
        payload = jose_jwt.decode(
            token,
            jwks,
            algorithms=["RS256", "ES256"],  # allow common OIDC algs; RS256 typical
            audience=cfg.oidc_audience,
            issuer=cfg.oidc_issuer,
            options={"verify_at_hash": False},
        )
        return payload

    except ExpiredSignatureError as e:
        raise PermissionError("Token expired (exp)") from e
    except JWTError as e:
        # Common causes: signature invalid, aud/iss mismatch, malformed token
        raise PermissionError(f"JWT invalid: {str(e)}") from e

def verify_bearer_jwt(authorization_header: Optional[str], cfg: AuthConfig) -> Dict[str, Any]:
    """Convenience: reads Authorization header, verifies JWT, returns claims."""
    token = _strip_bearer(authorization_header)
    return verify_jwt_payload(token, cfg)
