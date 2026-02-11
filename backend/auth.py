"""
Hybrid JWT Authentication module
- Development: Local JWT-based auth
- Production: Supabase Auth integration (backend proxies to Supabase)
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

# Environment mode: 'local' or 'supabase'
AUTH_MODE = os.getenv("AUTH_MODE", "local")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your_random_jwt_secret_here")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")  # For production
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
    Decode and verify a JWT token (supports both local and Supabase modes)

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        if AUTH_MODE == "supabase" and SUPABASE_JWT_SECRET:
            # Production: Verify Supabase JWT
            payload = jwt.decode(
                token, 
                SUPABASE_JWT_SECRET, 
                algorithms=[JWT_ALGORITHM],
                audience="authenticated"
            )
        else:
            # Development: Verify local JWT
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

# ============================================================
# Supabase Integration (for production mode)
# ============================================================

async def supabase_signup(email: str, password: str, metadata: Dict = None) -> Dict:
    """
    Proxy signup request to Supabase Auth (production mode only)
    
    Returns:
        {
            "access_token": str,
            "user": {
                "id": str,
                "email": str,
                ...
            }
        }
    """
    import httpx
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase credentials not configured"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{supabase_url}/auth/v1/signup",
            json={
                "email": email,
                "password": password,
                "data": metadata or {}
            },
            headers={
                "apikey": supabase_key,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            error = response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=error.get("error_description") or error.get("msg", "Signup failed")
            )
        
        return response.json()

async def supabase_login(email: str, password: str) -> Dict:
    """
    Proxy login request to Supabase Auth (production mode only)
    
    Returns:
        {
            "access_token": str,
            "user": {
                "id": str,
                "email": str,
                ...
            }
        }
    """
    import httpx
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500, 
            detail="Supabase credentials not configured"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{supabase_url}/auth/v1/token?grant_type=password",
            json={
                "email": email,
                "password": password
            },
            headers={
                "apikey": supabase_key,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            error = response.json()
            raise HTTPException(
                status_code=401,
                detail=error.get("error_description") or error.get("msg", "Invalid credentials")
            )
        
        return response.json()
