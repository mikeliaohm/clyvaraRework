"""Dual-mode authentication: Supabase JWT in production, local JWT in development.

Set AUTH_MODE=local (default) for development without Supabase.
Set AUTH_MODE=supabase for production with Supabase Auth.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db, User

AUTH_MODE = os.getenv("AUTH_MODE", "local")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

security = HTTPBearer(auto_error=False)


def _decode_supabase_jwt(token: str) -> Dict:
    """Decode and verify a Supabase-issued JWT."""
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_JWT_SECRET not configured",
        )
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return {
            "sub": payload["sub"],  # Supabase user UUID
            "email": payload.get("email", ""),
            "role": payload.get("role", "authenticated"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def _decode_local_jwt(token: str) -> Dict:
    """Decode a locally-issued JWT (dev mode)."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            "sub": str(payload["user_id"]),
            "email": payload.get("email", ""),
            "role": "authenticated",
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def create_local_token(user_id: int, email: str) -> str:
    """Issue a local JWT for dev login. Only available when AUTH_MODE=local."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Dict:
    """Authenticate the request and return a user dict.

    Returns: {"user_id": str, "email": str, "role": str}
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials

    if AUTH_MODE == "supabase":
        claims = _decode_supabase_jwt(token)
    else:
        claims = _decode_local_jwt(token)

    # Look up local user row
    user = _resolve_user(db, claims)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return {"user_id": str(user.id), "email": user.email, "role": claims["role"]}


def _resolve_user(db: Session, claims: Dict) -> Optional[User]:
    """Find local User row from JWT claims."""
    sub = claims["sub"]

    # In local mode, sub is the integer user ID
    if AUTH_MODE != "supabase":
        try:
            return db.query(User).filter(User.id == int(sub)).first()
        except (TypeError, ValueError):
            pass

    # In supabase mode, sub is the Supabase UUID stored in external_auth_id
    user = db.query(User).filter(User.external_auth_id == sub).first()
    if user:
        return user

    # Fallback: match by email
    email = claims.get("email")
    if email:
        return db.query(User).filter(User.email == email).first()

    return None
