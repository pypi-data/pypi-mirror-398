from typing import Dict

import pytest
from keycloak import KeycloakOpenID


@pytest.fixture(scope="session")
def keycloak_token() -> Dict[str, str]:
    kc = KeycloakOpenID(
        server_url="http://localhost:8080",
        realm_name="teron",
        client_id="teron-core-api",
        client_secret_key="tjWtEoiKhGl7mH8nkg3s2DUGnugJjwQA",
    )

    token = kc.token(
        username="demo",
        password="demo",
    )

    return token
