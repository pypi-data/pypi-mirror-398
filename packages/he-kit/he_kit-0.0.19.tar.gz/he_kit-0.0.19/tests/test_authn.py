from typing import List

from fastapi import Depends, Request
from fastapi.testclient import TestClient

from he_kit.authn.dependencies import get_auth_context
from he_kit.authn.keycloak import KeycloakSettings as BaseKeycloakSettings
from he_kit.core.app import App
from he_kit.core.conf import DefaultSettings


class KeycloakSettings(BaseKeycloakSettings):
    SERVER_URL: str = "http://localhost:8080"
    REALM: str = "teron"
    AUDIENCE: List[str] = ["account"]
    CLIENT_ID: str = "teron-core-api"
    CLIENT_SECRET: str = "tjWtEoiKhGl7mH8nkg3s2DUGnugJjwQA"

    ADMIN_USERNAME: str | None = "admin"
    ADMIN_PASSWORD: str | None = "admin"


def test_dummy_auth_adapter_valid_user():
    settings = DefaultSettings(AUTH_BACKEND="he_kit.authn.dummy.DummyAuthProvider")

    app = App(settings=settings)

    @app.get("/me")
    async def me(request: Request, auth=Depends(get_auth_context)):
        return {
            "user_id": auth.user_id,
            "tenants": auth.tenants,
        }

    client = TestClient(app)
    token = "tenant123:alice"
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "alice"
    assert "tenant123" in data["tenants"]


def test_dummy_auth_adapter_invalid_header():
    settings = DefaultSettings(AUTH_BACKEND="he_kit.authn.dummy.DummyAuthProvider")

    app = App(settings=settings)

    @app.get("/me")
    async def me(request: Request, auth=Depends(get_auth_context)):
        return {
            "user_id": auth.user_id,
            "tenants": auth.tenants,
        }

    client = TestClient(app)
    token = "alice"
    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_keycloak_auth_adapter_valid_user(keycloak_token):
    settings = DefaultSettings(
        AUTH_BACKEND="he_kit.authn.keycloak.KeycloakAuthBackend",
        AUTH_BACKEND_SETTINGS=KeycloakSettings(),
    )

    app = App(settings=settings)

    @app.get("/me")
    async def me(request: Request, auth=Depends(get_auth_context)):
        return {
            "user_id": auth.user_id,
            "tenants": auth.tenants,
        }

    access_token = keycloak_token["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    client = TestClient(app, headers=headers)

    response = client.get("/me")

    assert response.status_code == 200
    data = response.json()

    assert data["user_id"] == "6d9e257a-7fb5-4273-9672-3ae7591a3029"
    assert "teron" in data["tenants"]
