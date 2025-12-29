from urllib.parse import urlparse, urlunparse

from alembic.config import Config
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

from .project import find_project_root, get_settings

ASYNC_TO_SYNC_SCHEMES = {
    "postgresql+asyncpg": "postgresql",
    "sqlite+aiosqlite": "sqlite",
}

SYNC_TO_ASYNC_SCHEMES = {
    "postgresql": "postgresql+asyncpg",
    "sqlite": "sqlite+aiosqlite",
}


def async_to_sync_db_url(url: str) -> str:
    """Convert async db url to sync."""
    parsed = urlparse(url)
    scheme_lower = parsed.scheme.lower()

    if scheme_lower not in ASYNC_TO_SYNC_SCHEMES:
        return url

    new_scheme = ASYNC_TO_SYNC_SCHEMES[scheme_lower]
    new_parsed = parsed._replace(scheme=new_scheme)
    return urlunparse(new_parsed)


def sync_to_async_db_url(url: str) -> str:
    """Convert sync db url to async."""
    parsed = urlparse(url)
    scheme_lower = parsed.scheme.lower()

    if scheme_lower not in SYNC_TO_ASYNC_SCHEMES:
        return url

    new_scheme = SYNC_TO_ASYNC_SCHEMES[scheme_lower]
    new_parsed = parsed._replace(scheme=new_scheme)
    return urlunparse(new_parsed)


def get_alembic_config() -> Config:
    """Load Alembic config from project root and inject DB_URL, script
    location, and log level.

    """
    root = find_project_root()

    ini_path = root / "alembic.ini"
    migrations_dir = root / "migrations"

    if not ini_path.exists():
        raise FileNotFoundError(f"No alembic.ini found in {root}")

    settings = get_settings(force_reload=True)

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.DB_URL)
    cfg.set_main_option("script_location", str(migrations_dir))
    cfg.set_main_option("logger_alembic.level", settings.LOG_LEVEL)
    cfg.config_file_name = str(ini_path)

    return cfg


def run_migrations_offline(context, target_metadata):
    """Run migrations in offline mode. No async version available as
    offline migrations no I/O with the database layer occurs.

    """
    # TODO: If we use get_config() here instead we can run the default alembic
    # cli without wrapping it?
    config = context.config

    url = async_to_sync_db_url(config.get_main_option("sqlalchemy.url"))
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


async def async_run_migrations_online(context, target_metadata):
    """Run migrations in online mode. Async edition."""
    config = context.config

    connectable = create_async_engine(
        sync_to_async_db_url(config.get_main_option("sqlalchemy.url")),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
            )
        )

        def do_run_migrations(sync_connection):
            with sync_connection.begin():
                context.run_migrations()

        await connection.run_sync(do_run_migrations)


def run_migrations_online_sync(context, target_metadata):
    """Run migrations in online mode. Sync edition."""
    config = context.config
    config.set_main_option(
        "sqlalchemy.url", async_to_sync_db_url(config.get_main_option("sqlalchemy.url"))
    )

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
