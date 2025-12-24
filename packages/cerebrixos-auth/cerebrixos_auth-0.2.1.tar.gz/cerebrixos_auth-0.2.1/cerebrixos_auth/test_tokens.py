
import time
from jose import jwt
from .config import TEST_JWT_SECRET, OIDC_AUDIENCE

def generate_test_jwt(tenant_id, user_id, scopes=None, ttl_seconds=3600):
    now = int(time.time())
    return jwt.encode({
        "sub": user_id,
        "tenant_id": tenant_id,
        "scopes": scopes or [],
        "iat": now,
        "exp": now + ttl_seconds,
        "aud": OIDC_AUDIENCE,
    }, TEST_JWT_SECRET, algorithm="HS256")
