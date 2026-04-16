from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


class DatabaseManager:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            yield session

    async def ping(self) -> bool:
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False

        return True

    async def dispose(self) -> None:
        await self._engine.dispose()
