from typing import List, Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic_settings import BaseSettings

from .base import AuthContext, AuthProvider, UserProfile


class KeycloakSettings(BaseSettings):
    SERVER_URL: str
    REALM: str
    CLIENT_ID: str
    CLIENT_SECRET: str

    ADMIN_USERNAME: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None


class KeycloakAuthBackend(AuthProvider[KeycloakSettings]):
    """Keycloak authentication provider."""

    auth_backend_settings_class = KeycloakSettings
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def __init__(self, settings) -> None:
        super().__init__(settings)

        try:
            from keycloak import KeycloakAdmin  # type: ignore[import-not-found]
            from keycloak import KeycloakOpenID  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "KeycloakAuthProvider requires the 'keycloak' extra:\n"
                "Install he-kit[keycloak]"
            ) from exc

        self._openid = KeycloakOpenID(
            server_url=self.provider_settings.SERVER_URL,
            realm_name=self.provider_settings.REALM,
            client_id=self.provider_settings.CLIENT_ID,
            client_secret_key=self.provider_settings.CLIENT_SECRET,
        )

        self._issuer = (
            f"{self.provider_settings.SERVER_URL}/realms/{self.provider_settings.REALM}"
        )
        self._client_id = self.provider_settings.CLIENT_ID

        self._public_key = (
            "-----BEGIN PUBLIC KEY-----\n"
            + self._openid.public_key()
            + "\n-----END PUBLIC KEY-----"
        )

        self._admin = None
        if (
            self.provider_settings.ADMIN_USERNAME
            and self.provider_settings.ADMIN_PASSWORD
        ):
            self._admin = KeycloakAdmin(
                server_url=self.provider_settings.SERVER_URL,
                realm_name=self.provider_settings.REALM,
                username=self.provider_settings.ADMIN_USERNAME,
                password=self.provider_settings.ADMIN_PASSWORD,
                verify=True,
            )

    async def get_token(self, request: Request) -> str:
        token = await self.oauth2_scheme(request)
        assert token is not None
        return token

    async def verify_token(self, token: str) -> AuthContext:
        try:
            claims = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                audience="account",
                issuer=self._issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            ) from exc

        user_id = claims.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )

        tenants = [self.provider_settings.REALM]

        return AuthContext(
            user_id=user_id,
            tenants=tenants,
            auth_provider="keycloak",
            claims=claims,
        )

    async def get_user(self, user_id: str) -> UserProfile:
        if not self._admin:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="User lookup not enabled",
            )

        try:
            user = self._admin.get_user(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        name = (
            f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
            or user.get("username")
            or "N/A"
        )

        return UserProfile(
            user_id=user["id"],
            name=name,
            email=user.get("email", "N/A"),
            photo_url=None,
        )

    async def get_users(self, user_ids: List[str]) -> List[UserProfile]:
        if not self._admin:
            return []

        users: List[UserProfile] = []
        for uid in user_ids:
            try:
                users.append(await self.get_user(uid))
            except HTTPException:
                continue

        return users
