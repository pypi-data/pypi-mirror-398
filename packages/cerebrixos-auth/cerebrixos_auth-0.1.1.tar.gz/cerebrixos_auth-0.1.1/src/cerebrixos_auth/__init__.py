"""cerebrixos_auth

Small, dependency-light helpers for:
- Verifying Bearer JWTs (test HS256 or prod OIDC/JWKS RS256)
- Extracting tenant/user scope from claims
- Enforcing audience/purpose/scopes
- Signing short-lived download tokens (HMAC)
- Signing/verifying webhook requests (HMAC + timestamp + nonce)

Designed to be reused across Modal and non-Modal Python services.
"""

from .config import AuthConfig, load_config_from_env
from .jwt_verify import verify_bearer_jwt, verify_jwt_payload
from .policy import (
    require_audience,
    require_purpose,
    require_scopes,
    require_claim,
    tenant_user_from_payload,
)
from .tokens import (
    sign_download_token,
    verify_download_token,
)
from .webhook import (
    sign_webhook_headers,
    verify_webhook_request,
)

__all__ = [
    "AuthConfig",
    "load_config_from_env",
    "verify_bearer_jwt",
    "verify_jwt_payload",
    "require_audience",
    "require_purpose",
    "require_scopes",
    "require_claim",
    "tenant_user_from_payload",
    "sign_download_token",
    "verify_download_token",
    "sign_webhook_headers",
    "verify_webhook_request",
]
