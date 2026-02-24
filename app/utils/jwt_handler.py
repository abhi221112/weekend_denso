"""
JWT Token Handler
=================
Generates and verifies access & refresh tokens using PyJWT.

Access token  → short-lived (30 min)
Refresh token → long-lived  (7 days)

Usage:
  from app.utils.jwt_handler import create_access_token, create_refresh_token, get_current_user

  # In login service:
  access  = create_access_token({"user_id": "testuser01", "supplier_code": "SUP001"})
  refresh = create_refresh_token({"user_id": "testuser01"})

  # In protected routes – add dependency:
  @router.get("/protected", dependencies=[Depends(get_current_user)])
  def my_endpoint(user: dict = Depends(get_current_user)):
      ...
"""

import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ── Configuration ────────────────────────────────────────────────
SECRET_KEY = "d-trace-supplier-end-user-api-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Bearer token scheme for Swagger UI
bearer_scheme = HTTPBearer(auto_error=False)


# ── Token Creation ───────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Create a short-lived access token (30 min)."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["type"] = "access"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a long-lived refresh token (7 days)."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload["type"] = "refresh"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Token Verification ──────────────────────────────────────────

def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Decode and verify a JWT token.
    Returns the payload dict or raises HTTPException.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type – expected {expected_type}",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ── FastAPI Dependency ───────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency – extracts and verifies the Bearer access token.
    Returns the decoded payload (user_id, supplier_code, etc.).

    Usage in routes:
        @router.get("/protected")
        def my_endpoint(user: dict = Depends(get_current_user)):
            user_id = user["user_id"]
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header – provide Bearer token",
        )
    return verify_token(credentials.credentials, expected_type="access")
