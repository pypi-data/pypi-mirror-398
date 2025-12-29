# Helicon kit

A project generator that bootstraps a FastAPI setup following Helicon's
standards and best practices.

## Included tools

These are the major tools that are configured and included in the project:

- structlog
- sqlmodel
- alembic
- fastapi
- pydantic-settings
- pytest

## Start a new project

Run the following commands to initialize a new project:

```
mkdir helicon-app
cd helicon-app
uvx he-kit init
```

After answering the prompts you should have a fully runnable FastAPI setup:

```
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── Dockerfile
├── main.py
├── pyproject.toml
├── README.md
├── migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions
├── src
│   └── helicon_app
│       ├── app.py
│       ├── conf.py
│       ├── __init__.py
│       ├── models
│       │   └── __init__.py
│       ├── routers
│       │   └── __init__.py
│       └── schemas
│           └── __init__.py
└── tests
    └── conftest.py
```

You can verify that it works by running the test suite and starting the
development server:

```
uv run pytest
uv run he-kit dev
```

It is recommended that you  synchronize the new environment and install the
supplied pre-commit hooks (mypy and ruff):

```
uv sync
uv run pre-commit install
```

### Create a model and migrations

Helicon-kit uses SQLModel and Alembic. To start working with models, first
create a new module in the `models/` directory. We'll call it
`models/users.py`:

```python
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
```

We have to make sure the models are importable via `your_module_name.models`
in order for Alembic to discover them. We do this by importing the new module
in `models/__init__.py`:

```python
from .users import *
```

Create the migrations and apply them:

```
uv run he-kit makemigrations "add user model"
uv run he-kit migrate
```

### Create and register a new router

Firstly we need to define some API schemas. We'll add them in the module
`schemas/users.py`:

```python
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    name: str
    email: str


class UserRead(SQLModel):
    id: int
    name: str
    email: str
```

Note: as both schemas and models are derrived from `SQLModel` you can of
course create base classes and extend them to avoid repeating attributes.

We'll continue and a new module in the `routers/` directory. We'll stay on the
theme and call it `routers/users.py`:

```python
from he_kit.core.db import db_session
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.users import User
from ..schemas.users import UserCreate, UserRead

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(session: AsyncSession = Depends(db_session)):
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate, session: AsyncSession = Depends(db_session)):
    user = User.model_validate(user)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

And finally we register the router in `app.py`:

```python
from he_kit.core.app import App

from .conf import settings
from .routers.users import router as user_router


def create_app():
    app = App(settings=settings)

    app.include_router(user_router, prefix="/users")

    return app


app = create_app()
```

### Writing tests

To verify that everything works we'll create a testmodule in
`tests/test_user_endpoints.py`:

```python
def test_create_user(client):
    payload = {"name": "Alice", "email": "alice@example.com"}
    r = client.post("/users/", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_list_users(client):
    payload = {"name": "Bob", "email": "bob@example.com"}
    r = client.post("/users/", json=payload)
    assert r.status_code == 200

    r = client.get("/users/")
    assert r.status_code == 200
    users = r.json()
    assert any(u["name"] == "Bob" for u in users)
```

Save the file and run the tests suite:

```
uv run pytest
```

## Local development setup

To install `he-kit` from local disk to try it out during development, you can
install it with `pip`:

```
mkdir test-dir
cd test-dir
uv venv
pip install -e ../path/to/he-kit
uv run he-kit ...
```

## Keycloak authentication

`he-kit` support Keycloak as an optional authentication backend.

### Installation

Keycloak support is provided via an optional dependency.

```
uv add he-kit[keycloak]
```

### Configuration

Enable the Keycloak backend by setting `AUTH_BACKEND` to the fully qualified
provider path and supplying `AUTH_BACKEND_SETTINGS` as a `KeycloakSettings`
instance.

```python
from he_kit.core.conf import DefaultSettings
from he_kit.authn.keycloak import KeycloakSettings

settings = DefaultSettings(
    AUTH_BACKEND="he_kit.authn.keycloak.KeycloakAuthProvider",
    AUTH_BACKEND_SETTINGS=KeycloakSettings(
        SERVER_URL="http://localhost:8080",
        REALM="my-realm",
        CLIENT_ID="api-client",
        CLIENT_SECRET="secret",
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="admin",
    ),
)
```

## Releasing a new version

Update the version in the `pyproject.toml` file, commit it, create a matching
tag in git, and push:

    git tag v0.1.x
    git push --tags
