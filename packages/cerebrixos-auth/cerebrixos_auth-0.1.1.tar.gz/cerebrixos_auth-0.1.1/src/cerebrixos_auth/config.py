from __future__ import annotations

from dataclasses import dataclass
import os

def _env(name: str, default: str | None = None, required: bool = False) -> str:
    v = os.getenv(name, default if default is not None else "")
    if required and not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v or ""

@dataclass(frozen=True)
class AuthConfig:
    """Configuration for cerebrixos_auth.

    Convention:
      - CEREBRIX_ENV=test  -> accept HS256 tokens signed by TEST_JWT_SECRET
      - CEREBRIX_ENV=prod  -> verify via OIDC issuer JWKS (RS256 typically)
    """
    cerebrix_env: str
    oidc_issuer: str
    oidc_audience: str

    # Used only when cerebrix_env == "test"
    test_jwt_secret: str

    # HMAC secrets for webhook and download signing
    webhook_hmac_secret: str
    download_signing_key: str

    # Defaults
    file_url_ttl_seconds: int = 900
    jwks_cache_ttl_seconds: int = 3600
    jwks_timeout_seconds: int = 5

def load_config_from_env(prefix: str = "") -> AuthConfig:
    """Load configuration from environment variables.

    If you want multiple configurations in one process, you can set a prefix
    and name variables like {PREFIX}_OIDC_ISSUER, etc.

    Required env vars:
      CEREBRIX_ENV
      OIDC_ISSUER
      OIDC_AUDIENCE
      WEBHOOK_HMAC_SECRET
      DOWNLOAD_SIGNING_KEY

    Test-only env var:
      TEST_JWT_SECRET (required when CEREBRIX_ENV=test)
    """
    p = (prefix + "_") if prefix else ""

    cerebrix_env = _env(p + "CEREBRIX_ENV", required=True).lower().strip()
    oidc_issuer = _env(p + "OIDC_ISSUER", required=True).rstrip("/")
    oidc_audience = _env(p + "OIDC_AUDIENCE", required=True)

    webhook_hmac_secret = _env(p + "WEBHOOK_HMAC_SECRET", required=True)
    download_signing_key = _env(p + "DOWNLOAD_SIGNING_KEY", required=True)

    file_url_ttl_seconds_str = _env(p + "FILE_URL_TTL_SECONDS", default="900")
    jwks_cache_ttl_str = _env(p + "JWKS_CACHE_TTL_SECONDS", default="3600")
    jwks_timeout_str = _env(p + "JWKS_TIMEOUT_SECONDS", default="5")

    try:
        file_url_ttl_seconds = int(file_url_ttl_seconds_str)
        jwks_cache_ttl_seconds = int(jwks_cache_ttl_str)
        jwks_timeout_seconds = int(jwks_timeout_str)
    except ValueError as e:
        raise RuntimeError(f"Invalid integer env var: {e}") from e

    test_jwt_secret = _env(p + "TEST_JWT_SECRET", default="")
    if cerebrix_env == "test" and not test_jwt_secret:
        raise RuntimeError("TEST_JWT_SECRET must be set when CEREBRIX_ENV=test")

    return AuthConfig(
        cerebrix_env=cerebrix_env,
        oidc_issuer=oidc_issuer,
        oidc_audience=oidc_audience,
        test_jwt_secret=test_jwt_secret,
        webhook_hmac_secret=webhook_hmac_secret,
        download_signing_key=download_signing_key,
        file_url_ttl_seconds=file_url_ttl_seconds,
        jwks_cache_ttl_seconds=jwks_cache_ttl_seconds,
        jwks_timeout_seconds=jwks_timeout_seconds,
    )
