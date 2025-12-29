from abc import ABC, abstractmethod
from datetime import datetime, timezone
from elasticsearch import AsyncElasticsearch, Elasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from redis.asyncio import Redis as AsyncRedis
from redis import Redis as SyncRedis
from sqlalchemy import text
from typing import Generic, Type, TypeVar
from uuid import uuid4
from nexo.logging.enums import LogLevel
from nexo.logging.logger import Database
from nexo.schemas.application import ApplicationContext, OptApplicationContext
from nexo.schemas.connection import OptConnectionContext
from nexo.schemas.google import ListOfPublisherHandlers
from nexo.schemas.operation.context import generate
from nexo.schemas.operation.enums import (
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from nexo.schemas.operation.mixins import Timestamp
from nexo.schemas.operation.system import (
    SystemOperationAction,
    SuccessfulSystemOperation,
)
from nexo.schemas.security.authentication import OptAnyAuthentication
from nexo.schemas.security.authorization import OptAnyAuthorization
from nexo.schemas.security.impersonation import OptImpersonation
from nexo.types.uuid import OptUUID
from nexo.utils.exception import extract_details
from ..config import (
    MySQLConfig,
    PostgreSQLConfig,
    SQLiteConfig,
    SQLServerConfig,
    SQLConfigT,
    ElasticsearchConfig,
    MongoConfig,
    RedisConfig,
    NoSQLConfigT,
    DatabaseConfigT,
)
from ..enums import Connection
from ..types import DeclarativeBaseT
from .client import (
    ElasticsearchClientManager,
    MongoClientManager,
    RedisClientManager,
    ClientManagerT,
)
from .engine import EngineManager
from .session import SessionManager


class Manager(ABC, Generic[DatabaseConfigT]):
    def __init__(
        self,
        config: DatabaseConfigT,
        logger: Database,
        publishers: ListOfPublisherHandlers = [],
        application_context: OptApplicationContext = None,
    ) -> None:
        super().__init__()
        self._config = config
        self._logger = logger
        self._publishers = publishers
        self._application_context = (
            application_context
            if application_context is not None
            else ApplicationContext.new()
        )
        self._operation_context = generate(
            origin=Origin.SERVICE,
            layer=Layer.UTILITY,
            target=Target.DATABASE,
        )

    @abstractmethod
    async def async_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        pass

    @abstractmethod
    def sync_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        pass

    @abstractmethod
    async def dispose(self):
        pass


class NoSQLManager(
    Manager[NoSQLConfigT],
    Generic[
        NoSQLConfigT,
        ClientManagerT,
    ],
):
    client_manager_cls: Type[ClientManagerT]

    def __init__(
        self,
        config: NoSQLConfigT,
        logger: Database,
        publishers: ListOfPublisherHandlers = [],
        application_context: OptApplicationContext = None,
    ) -> None:
        super().__init__(config, logger, publishers, application_context)
        self._client_manager = self.client_manager_cls(config)  # type: ignore

    @property
    def client(self) -> ClientManagerT:
        return self._client_manager

    async def async_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        """Check client connectivity by executing a simple query."""
        client = self._client_manager.get(Connection.ASYNC)
        try:
            if isinstance(client, AsyncElasticsearch):
                return await client.ping()
            elif isinstance(client, AsyncIOMotorClient):
                db = client.get_database(str(self._config.connection.database))
                await db.command("ping")
                return True
            elif isinstance(client, AsyncRedis):
                await client.ping()
                return True
            else:
                raise TypeError(f"Invalid client type: '{type(client)}'")
        except Exception as e:
            self._logger.error(
                "Unexpected error occured while checking client connection",
                exc_info=True,
                extra={"json_fields": {"exc_details": extract_details(e)}},
            )
            return False

    def sync_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        """Check client connectivity by executing a simple query."""
        client = self._client_manager.get(Connection.SYNC)
        try:
            if isinstance(client, Elasticsearch):
                return client.ping()
            elif isinstance(client, MongoClient):
                db = client.get_database(str(self._config.connection.database))
                db.command("ping")
                return True
            elif isinstance(client, SyncRedis):
                client.ping()
                return True
            else:
                raise TypeError(f"Invalid client type: '{type(client)}'")
        except Exception as e:
            self._logger.error(
                "Unexpected error occured while checking client connection",
                exc_info=True,
                extra={"json_fields": {"exc_details": extract_details(e)}},
            )
            return False

    async def dispose(self):
        await self._client_manager.dispose()


class ElasticsearchManager(
    NoSQLManager[ElasticsearchConfig, ElasticsearchClientManager]
):
    client_manager_cls = ElasticsearchClientManager


class MongoManager(NoSQLManager[MongoConfig, MongoClientManager]):
    client_manager_cls = MongoClientManager


class RedisManager(NoSQLManager[RedisConfig, RedisClientManager]):
    client_manager_cls = RedisClientManager


AnyNoSQLManager = ElasticsearchManager | MongoManager | RedisManager


NoSQLManagerT = TypeVar("NoSQLManagerT", bound=AnyNoSQLManager)


class SQLManager(Manager[SQLConfigT], Generic[SQLConfigT, DeclarativeBaseT]):
    def __init__(
        self,
        Base: Type[DeclarativeBaseT],
        config: SQLConfigT,
        logger: Database,
        publishers: ListOfPublisherHandlers = [],
        application_context: OptApplicationContext = None,
    ) -> None:
        super().__init__(config, logger, publishers, application_context)
        self._engine_manager = EngineManager[SQLConfigT](config)
        self._session_manager = SessionManager(
            config=config,
            engines=self._engine_manager.get_all(),
            logger=self._logger,
            publishers=self._publishers,
            application_context=self._application_context,
        )
        self.Base = Base
        self.Base.metadata.create_all(bind=self._engine_manager.get(Connection.SYNC))

    @property
    def engine(self) -> EngineManager[SQLConfigT]:
        return self._engine_manager

    @property
    def session(self) -> SessionManager:
        return self._session_manager

    async def async_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        """Check database connectivity by executing a simple query."""
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = SystemOperationAction(
            type=SystemOperationType.DATABASE_CONNECTION, details=None
        )
        executed_at = datetime.now(tz=timezone.utc)
        try:
            async with self._session_manager.get(
                Connection.ASYNC,
                operation_id=operation_id,
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            ) as session:
                await session.execute(text("SELECT 1"))
                operation = SuccessfulSystemOperation[None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=self._operation_context,
                    action=operation_action,
                    timestamp=Timestamp.completed_now(executed_at),
                    summary="Database connectivity check successful",
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=None,
                )
                operation.log(self._logger, LogLevel.INFO)
                operation.publish(self._logger, self._publishers)
            return True
        except Exception:
            return False

    def sync_check_connection(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
    ) -> bool:
        """Check database connectivity by executing a simple query."""
        operation_id = operation_id if operation_id is not None else uuid4()
        operation_action = SystemOperationAction(
            type=SystemOperationType.DATABASE_CONNECTION, details=None
        )
        executed_at = datetime.now(tz=timezone.utc)
        try:
            with self._session_manager.get(
                Connection.SYNC,
                operation_id=operation_id,
                connection_context=connection_context,
                authentication=authentication,
                authorization=authorization,
                impersonation=impersonation,
            ) as session:
                session.execute(text("SELECT 1"))
                operation = SuccessfulSystemOperation[None](
                    application_context=self._application_context,
                    id=operation_id,
                    context=self._operation_context,
                    action=operation_action,
                    timestamp=Timestamp.completed_now(executed_at),
                    summary="Database connectivity check successful",
                    connection_context=connection_context,
                    authentication=authentication,
                    authorization=authorization,
                    impersonation=impersonation,
                    response=None,
                )
                operation.log(self._logger, LogLevel.INFO)
                operation.publish(self._logger, self._publishers)
            return True
        except Exception:
            return False

    async def dispose(self):
        self._session_manager.dispose()
        await self._engine_manager.dispose()


class MySQLManager(
    SQLManager[MySQLConfig, DeclarativeBaseT], Generic[DeclarativeBaseT]
):
    pass


class PostgreSQLManager(
    SQLManager[PostgreSQLConfig, DeclarativeBaseT], Generic[DeclarativeBaseT]
):
    pass


class SQLiteManager(
    SQLManager[SQLiteConfig, DeclarativeBaseT], Generic[DeclarativeBaseT]
):
    pass


class SQLServerManager(
    SQLManager[SQLServerConfig, DeclarativeBaseT], Generic[DeclarativeBaseT]
):
    pass


AnySQLManager = MySQLManager | PostgreSQLManager | SQLiteManager | SQLServerManager


SQLManagerT = TypeVar("SQLManagerT", bound=AnySQLManager)


AnyDatabaseManager = AnySQLManager | AnyNoSQLManager


DatabaseManagerT = TypeVar("DatabaseManagerT", bound=AnyDatabaseManager)
