from typing import Dict, Any, List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, User, Role, UserRole
from fastapi_users_setup import current_active_fau_user
from config import openai_client


async def get_current_user(user: User = Depends(current_active_fau_user)) -> Dict:
    """Compatibility wrapper — returns the same dict shape the existing endpoints expect."""
    return {"user_id": str(user.id), "email": user.email, "role": "authenticated", "roles": []}


def _get_user_role_names(db: Session, user_id: int) -> List[str]:
    rows = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return [row[0] for row in rows]


def _resolve_user_from_auth_context(
    db: Session, current_user: Dict[str, Any]
) -> Optional[User]:
    token_user_id = current_user.get("user_id")
    token_email = current_user.get("email")

    if token_user_id is not None:
        try:
            user = db.query(User).filter(User.id == int(token_user_id)).first()
            if user:
                return user
        except (TypeError, ValueError):
            user = db.query(User).filter(
                User.external_auth_id == str(token_user_id)
            ).first()
            if user:
                return user

    if token_email:
        return db.query(User).filter(User.email == token_email).first()

    return None


def _enforce_admin_access(
    db: Session,
    current_user: Dict[str, Any],
    x_admin_key: Optional[str],
) -> None:
    import os

    user = _resolve_user_from_auth_context(db, current_user)
    user_is_admin = bool(user and "admin" in _get_user_role_names(db, user.id))

    admin_api_key = os.getenv("ADMIN_API_KEY")
    valid_admin_key = bool(admin_api_key and x_admin_key and x_admin_key == admin_api_key)

    if not user_is_admin and not valid_admin_key:
        raise HTTPException(status_code=403, detail="Admin access required")
