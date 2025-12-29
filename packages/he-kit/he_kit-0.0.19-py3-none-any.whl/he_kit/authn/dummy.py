from typing import Dict, List, Optional

from fastapi import HTTPException, Request, status
from pydantic import BaseModel

from .base import AuthContext, AuthProvider, UserProfile


class DummySettings(BaseModel):
    pass


class DummyAuthProvider(AuthProvider[DummySettings]):
    """Dummy provider for local dev and testing.

    Authorization header format: "Bearer <tenant_key>:<user_id>"

    """

    auth_backend_settings_class = DummySettings

    def __init__(self, users: Optional[Dict[str, Dict]] = None):
        self._users = users or {}

    async def get_token(self, request: Request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
            )

        token = auth_header[len("Bearer ") :].strip()
        return token

    async def verify_token(self, token: str) -> AuthContext:
        if not token or ":" not in token:
            raise ValueError(
                "Invalid dummy token. Expected '<tenant_key>:<user_id>' format."
            )

        tenant_key, user_id = token.split(":", 1)

        return AuthContext(
            user_id=user_id, tenants=[tenant_key], auth_provider="dummy", claims={}
        )

    async def get_user(self, user_id: str) -> UserProfile:
        if user_id in self._users:
            record = self._users[user_id]

            return UserProfile(
                user_id=user_id,
                name=record.get("name", user_id.capitalize()),
                email=record.get("email", f"{user_id}@example.com"),
                photo_url=record.get("photo_url", None),
            )

        return UserProfile(
            user_id=user_id,
            name=user_id.capitalize(),
            email=f"{user_id}@example.com",
            photo_url="https://picsum.photos/id/64/500/500",
        )

    async def get_users(self, user_ids: List[str]) -> List[UserProfile]:
        return [await self.get_user(uid) for uid in user_ids]
