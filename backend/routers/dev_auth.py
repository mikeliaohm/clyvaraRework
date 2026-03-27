"""Dev-only auth routes for local development without Supabase.

Only mounted when AUTH_MODE=local. Provides simple login/register
endpoints that issue local JWTs.
"""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from auth import create_local_token, get_current_user
from database import get_db, User

router = APIRouter(prefix="/api/auth", tags=["auth-dev"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    graduation_year: int | None = None
    institution: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    graduation_year: int | None = None
    institution: str | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(body.password.encode(), user.password.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_local_token(user.id, user.email)
    return AuthResponse(access_token=token, user_id=user.id, email=user.email)


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()

    email_prefix = body.email.split("@")[0]
    user = User(
        email=body.email,
        password=hashed,
        username=body.username or email_prefix,
        full_name=body.full_name or email_prefix,
        specialty=body.specialty,
        graduation_year=body.graduation_year,
        institution=body.institution,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_local_token(user.id, user.email)
    return AuthResponse(access_token=token, user_id=user.id, email=user.email)


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(current_user["user_id"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        specialty=user.specialty,
        graduation_year=user.graduation_year,
        institution=user.institution,
    )
