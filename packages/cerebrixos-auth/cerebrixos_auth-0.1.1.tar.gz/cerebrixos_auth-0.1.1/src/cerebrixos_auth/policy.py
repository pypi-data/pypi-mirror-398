from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

def require_audience(payload: Dict[str, Any], expected_aud: str) -> None:
    """Enforce JWT audience claim supports a specific audience."""
    aud = payload.get("aud")
    if isinstance(aud, list):
        ok = expected_aud in aud
    else:
        ok = (aud == expected_aud)
    if not ok:
        raise PermissionError(f"JWT audience mismatch (expected {expected_aud})")

def require_purpose(payload: Dict[str, Any], expected_purpose: str) -> None:
    """Enforce a 'typ' or 'purpose' claim for token specialization."""
    purpose = payload.get("typ") or payload.get("purpose")
    if purpose != expected_purpose:
        raise PermissionError(f"JWT purpose mismatch (expected {expected_purpose})")

def require_claim(payload: Dict[str, Any], claim: str) -> Any:
    if claim not in payload or payload.get(claim) in (None, ""):
        raise PermissionError(f"Missing required JWT claim: {claim}")
    return payload[claim]

def _parse_scopes(payload: Dict[str, Any]) -> List[str]:
    scope = payload.get("scope") or payload.get("scp") or ""
    if isinstance(scope, list):
        return [str(s) for s in scope]
    return [s for s in str(scope).split() if s]

def require_scopes(payload: Dict[str, Any], required_scopes: Iterable[str]) -> None:
    have = set(_parse_scopes(payload))
    need = set(required_scopes)
    missing = sorted(list(need - have))
    if missing:
        raise PermissionError(f"Missing required scopes: {', '.join(missing)}")

def tenant_user_from_payload(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Extract tenant and user scope from JWT claims.

    Conventions:
      - tenant_id claim is required
      - user id defaults to 'sub' claim
    """
    tenant_id = payload.get("tenant_id") or payload.get("tid")
    user_id = payload.get("user_id") or payload.get("sub")
    if not tenant_id:
        raise PermissionError("Missing tenant_id in token")
    if not user_id:
        raise PermissionError("Missing user_id/sub in token")
    return str(tenant_id), str(user_id)
