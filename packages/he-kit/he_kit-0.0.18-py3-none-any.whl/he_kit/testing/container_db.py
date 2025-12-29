import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def pg_container():
    """Start a Postgres container for the duration of the test session."""
    container = PostgresContainer("postgres:16")
    container.start()
    yield container
    container.stop()


@pytest_asyncio.fixture
async def db_url(pg_container, monkeypatch):
    """Extract the details from the postgres container, create a connection
    string and patch the environment so the URL becomes available in future
    fixtures.

    """
    user = pg_container.username
    password = pg_container.password
    host = pg_container.get_container_host_ip()
    port = pg_container.get_exposed_port(pg_container.port)
    db = pg_container.dbname

    # TODO: We need to know if the user expects a sync or async connection
    # string here.
    async_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

    monkeypatch.setenv("DB_URL", async_url)

    yield async_url
