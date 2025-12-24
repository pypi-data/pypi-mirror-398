import asyncio
from sqlalchemy.ext.asyncio import (
    create_async_engine, async_sessionmaker, 
    AsyncEngine, AsyncSession
)

class EngineManager:
    _lock = asyncio.Lock()
    _engines = {}  # { conn_string: engine }

    @classmethod
    async def get_engine(cls, conn_string: str) -> AsyncEngine:
        # if already exists, return from cache
        if conn_string in cls._engines:
            return cls._engines[conn_string]

        # if it does not exist, protect creation with lock
        async with cls._lock:
            # double check
            if conn_string in cls._engines:
                return cls._engines[conn_string]

            engine = create_async_engine(
                conn_string,
                pool_size=20,
                max_overflow=40,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True
            )

            cls._engines[conn_string] = engine
            return engine


class SessionManager:
    _session_factories = {}

    @classmethod
    async def get_session_factory(cls, conn_string) -> async_sessionmaker[AsyncSession]:
        if conn_string in cls._session_factories:
            return cls._session_factories[conn_string]

        engine = await EngineManager.get_engine(conn_string)

        session_factory = async_sessionmaker(
            bind=engine,
            expire_on_commit=False
        )

        cls._session_factories[conn_string] = session_factory
        return session_factory
