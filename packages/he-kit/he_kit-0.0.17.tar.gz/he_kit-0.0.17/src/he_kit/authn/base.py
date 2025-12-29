from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar

from fastapi import Request
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

AuthProviderSettings = TypeVar("AuthProviderSettings", bound=BaseSettings)


class AuthContext(BaseModel):
    user_id: str
    tenants: List[str] = Field(default_factory=list)
    claims: dict[str, Any]
    auth_provider: str


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    photo_url: Optional[str] = None


class AuthProvider(ABC, Generic[AuthProviderSettings]):
    auth_backend_settings_class: Type[AuthProviderSettings]

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        if not hasattr(cls, "auth_backend_settings_class"):
            raise TypeError(
                "Subclasses of AuthProvider must define the auth_backend_settings_class attribute."
            )

    def __init__(self, settings: Any):
        self.settings = settings
        self.provider_settings = self.auth_backend_settings_class.model_validate(
            settings.AUTH_BACKEND_SETTINGS
        )

    @abstractmethod
    async def verify_token(self, token: str) -> AuthContext: ...

    @abstractmethod
    async def get_token(self, request: Request) -> str: ...

    @abstractmethod
    async def get_user(self, user_id: str) -> UserProfile: ...

    @abstractmethod
    async def get_users(self, user_ids: List[str]) -> List[UserProfile]: ...
