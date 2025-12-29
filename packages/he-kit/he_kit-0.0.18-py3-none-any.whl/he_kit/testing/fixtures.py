import importlib

import pytest
from alembic import command
from fastapi.testclient import TestClient

from ..utils.alembic import get_alembic_config


@pytest.fixture()
def db_file(tmp_path_factory):
    """Create temporary db file."""
    return tmp_path_factory.mktemp("data") / "test.db"


@pytest.fixture(autouse=True)
def set_up_db(monkeypatch, db_file):
    """Run Alembic migrations before any test."""
    db_url = f"sqlite+aiosqlite:///{db_file}"
    monkeypatch.setenv("DB_URL", db_url)
    # Is this even necessary since we're setting the DB_URL in the env before
    # we load the application?
    alembic_cfg = get_alembic_config()
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
    yield


def _import_app(module_name: str):
    """Dynamically import app from app module."""
    mod = importlib.import_module(f"{module_name}.app")
    return mod.create_app()


@pytest.fixture
def client(request):
    """Inject a FastAPI test client."""
    app_module_name = getattr(request.config, "module_name")
    app = _import_app(app_module_name)
    with TestClient(app) as c:
        yield c
