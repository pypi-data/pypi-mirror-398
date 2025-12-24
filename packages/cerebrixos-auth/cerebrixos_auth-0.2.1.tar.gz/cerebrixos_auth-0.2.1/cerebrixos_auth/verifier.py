
from jose import jwt
from .config import CEREBRIX_ENV, OIDC_ISSUER, OIDC_AUDIENCE, TEST_JWT_SECRET
from .jwks import get_jwks

def verify_bearer_jwt(auth):
    if not auth or not auth.startswith("Bearer "):
        raise RuntimeError("Missing Bearer token")
    token = auth.split(" ",1)[1]
    if CEREBRIX_ENV == "test":
        return jwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], audience=OIDC_AUDIENCE, options={"verify_iss": False})
    return jwt.decode(token, get_jwks(OIDC_ISSUER), algorithms=["RS256"], audience=OIDC_AUDIENCE, issuer=OIDC_ISSUER)
