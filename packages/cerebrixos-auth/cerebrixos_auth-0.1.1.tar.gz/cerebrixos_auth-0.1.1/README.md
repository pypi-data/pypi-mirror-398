# cerebrixos_auth

Auth helpers for CerebrixOS-style multi-tenant systems.

## Install

```bash
pip install cerebrixos_auth
```

## Environment variables

Required:
- CEREBRIX_ENV=test|prod
- OIDC_ISSUER
- OIDC_AUDIENCE
- WEBHOOK_HMAC_SECRET
- DOWNLOAD_SIGNING_KEY

Test-only:
- TEST_JWT_SECRET (required when CEREBRIX_ENV=test)

Optional:
- FILE_URL_TTL_SECONDS (default 900)
- JWKS_CACHE_TTL_SECONDS (default 3600)
- JWKS_TIMEOUT_SECONDS (default 5)

## Quick usage (FastAPI)

```python
from fastapi import FastAPI, Request
from cerebrixos_auth import load_config_from_env, verify_bearer_jwt, tenant_user_from_payload

app = FastAPI()
cfg = load_config_from_env()

@app.get("/secure")
def secure(req: Request):
    payload = verify_bearer_jwt(req.headers.get("authorization"), cfg)
    tenant_id, user_id = tenant_user_from_payload(payload)
    return {"tenant_id": tenant_id, "user_id": user_id}
```
