from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from typing import Generic, Literal, Tuple, TypeVar, overload
from ..config import (
    MySQLConfig,
    PostgreSQLConfig,
    SQLiteConfig,
    SQLServerConfig,
    SQLConfigT,
)
from ..enums import Connection


class EngineManager(Generic[SQLConfigT]):
    def __init__(self, config: SQLConfigT) -> None:
        super().__init__()
        self._config = config

        self._async_engine: AsyncEngine = self._config.create_engine(Connection.ASYNC)
        self._sync_engine: Engine = self._config.create_engine(Connection.SYNC)

    @overload
    def get(self, connection: Literal[Connection.ASYNC]) -> AsyncEngine: ...
    @overload
    def get(self, connection: Literal[Connection.SYNC]) -> Engine: ...
    def get(self, connection: Connection = Connection.ASYNC) -> AsyncEngine | Engine:
        if connection is Connection.ASYNC:
            return self._async_engine
        elif connection is Connection.SYNC:
            return self._sync_engine

    def get_all(self) -> Tuple[AsyncEngine, Engine]:
        return (self._async_engine, self._sync_engine)

    async def dispose(self):
        await self._async_engine.dispose()
        self._sync_engine.dispose()


class MySQLEngineManager(EngineManager[MySQLConfig]):
    pass


class PostgreSQLEngineManager(EngineManager[PostgreSQLConfig]):
    pass


class SQLiteEngineManager(EngineManager[SQLiteConfig]):
    pass


class SQLServerEngineManager(EngineManager[SQLServerConfig]):
    pass


EngineManagerT = TypeVar(
    "EngineManagerT",
    MySQLEngineManager,
    PostgreSQLEngineManager,
    SQLiteEngineManager,
    SQLServerEngineManager,
)
