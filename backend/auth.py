"""
Custom JWT Authentication module
Replaces Supabase authentication with local JWT-based auth
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_random_jwt_secret_here")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(user_id: str, email: str, additional_claims: Optional[Dict] = None) -> str:
    """
    Create a JWT access token

    Args:
        user_id: User's unique identifier
        email: User's email address
        additional_claims: Optional additional claims to include in token

    Returns:
        Encoded JWT token string
    """
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expires_at,
        "iat": datetime.utcnow(),
        "role": "authenticated"
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> Dict:
    """
    Decode and verify a JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

def get_current_user(authorization: str = Header(None)) -> Dict:
    """
    Extract and verify user info from JWT token in Authorization header

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Dictionary containing user information

    Raises:
        HTTPException: If authorization header is missing or token is invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token)

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role", "authenticated")
    }

def get_optional_user(authorization: str = Header(None)) -> Optional[Dict]:
    """
    Extract user info from JWT token if present, otherwise return None
    Useful for endpoints that work for both authenticated and anonymous users

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Dictionary containing user information or None if not authenticated
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated")
        }
    except:
        return None
