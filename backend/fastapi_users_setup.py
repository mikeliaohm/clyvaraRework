"""FastAPI Users integration for incremental migration from custom auth."""

import os
from typing import Optional, AsyncGenerator

from fastapi import Depends, Request
from fastapi_users import FastAPIUsers
from fastapi_users import schemas as fu_schemas
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.manager import BaseUserManager, IntegerIDMixin
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, Role, UserRole, get_async_db

JWT_SECRET = os.getenv("JWT_SECRET", "your_random_jwt_secret_here")


class UserRead(fu_schemas.BaseUser[int]):
    username: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(fu_schemas.BaseUserCreate):
    username: str
    full_name: str
    specialty: Optional[str] = None
    graduation_year: Optional[int] = None
    institution: Optional[str] = None


class UserUpdate(fu_schemas.BaseUserUpdate):
    username: Optional[str] = None
    full_name: Optional[str] = None
    specialty: Optional[str] = None
    graduation_year: Optional[int] = None
    institution: Optional[str] = None


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = JWT_SECRET
    verification_token_secret = JWT_SECRET

    async def _ensure_role(self, role_name: str, description: Optional[str] = None) -> Role:
        query = await self.user_db.session.execute(select(Role).where(Role.name == role_name))
        role = query.scalar_one_or_none()
        if role:
            return role

        role = Role(name=role_name, description=description)
        self.user_db.session.add(role)
        await self.user_db.session.commit()
        await self.user_db.session.refresh(role)
        return role

    async def _assign_role_if_missing(self, user_id: int, role_name: str) -> None:
        role = await self._ensure_role(role_name)
        query = await self.user_db.session.execute(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id)
        )
        existing = query.scalar_one_or_none()
        if existing:
            return

        self.user_db.session.add(UserRole(user_id=user_id, role_id=role.id))
        await self.user_db.session.commit()

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        # Ensure every account created via fastapi-users gets baseline RBAC.
        await self._assign_role_if_missing(user.id, "user")

    async def assign_roles(self, user_id: int, role_names: list[str]) -> None:
        for role_name in role_names:
            await self._assign_role_if_missing(user_id, role_name)


async def get_user_db(session: AsyncSession = Depends(get_async_db)) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="/api/fau/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=JWT_SECRET, lifetime_seconds=60 * 60 * 24 * 7)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


current_active_fau_user = fastapi_users.current_user(active=True)
current_superuser_fau_user = fastapi_users.current_user(active=True, superuser=True)
