
import os
def env(name, default=None, required=False):
    v = os.getenv(name, default)
    if required and not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v

CEREBRIX_ENV = env("CEREBRIX_ENV", "test")
OIDC_ISSUER = env("OIDC_ISSUER")
OIDC_AUDIENCE = env("OIDC_AUDIENCE")
TEST_JWT_SECRET = env("TEST_JWT_SECRET")
