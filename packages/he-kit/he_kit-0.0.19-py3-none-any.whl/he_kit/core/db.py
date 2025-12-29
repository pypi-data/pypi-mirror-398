from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

engine: AsyncEngine | None = None
session_maker: async_sessionmaker[AsyncSession] | None = None


@asynccontextmanager
async def db_lifespan(app):
    """Set up and tear down the database engine/sessionmaker."""
    global engine, session_maker

    engine = create_async_engine(
        app.settings.DB_URL,
        echo=app.settings.DB_ECHO_SQL,
        pool_pre_ping=True,
    )
    assert engine is not None
    session_maker = async_sessionmaker(
        engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
    )

    yield

    if engine is not None:
        await engine.dispose()

    engine = None
    session_maker = None


async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide a databse session for use in dependency injection."""
    assert session_maker is not None, "Database not initialized"
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
