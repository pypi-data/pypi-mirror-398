from elasticsearch import AsyncElasticsearch, Elasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo import MongoClient
from redis.asyncio import Redis as AsyncRedis
from redis import Redis as SyncRedis
from sqlalchemy.engine import create_engine as create_sync_engine, Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from typing import Generic, Literal, TypeVar, overload
from nexo.enums.environment import OptEnvironment
from nexo.types.dict import StrToAnyDict
from nexo.types.string import OptStr
from ..enums import Connection, CacheOrigin, CacheLayer
from ..utils import build_cache_namespace
from .additional import AdditionalConfigT, RedisAdditionalConfig
from .connection import (
    PostgreSQLConnectionConfig,
    MySQLConnectionConfig,
    SQLiteConnectionConfig,
    SQLServerConnectionConfig,
    MongoConnectionConfig,
    RedisConnectionConfig,
    ElasticsearchConnectionConfig,
    ConnectionConfigT,
)
from .identifier import DatabaseIdentifierConfig
from .pooling import (
    PostgreSQLPoolingConfig,
    MySQLPoolingConfig,
    SQLitePoolingConfig,
    SQLServerPoolingConfig,
    MongoPoolingConfig,
    RedisPoolingConfig,
    ElasticsearchPoolingConfig,
    PoolingConfigT,
)


class BaseConfig(
    BaseModel, Generic[ConnectionConfigT, PoolingConfigT, AdditionalConfigT]
):
    """Base configuration for database."""

    identifier: DatabaseIdentifierConfig = Field(..., description="Identifier config")
    connection: ConnectionConfigT = Field(..., description="Connection config")
    pooling: PoolingConfigT = Field(..., description="Pooling config")
    additional: AdditionalConfigT = Field(..., description="Additional config")


class ElasticsearchConfig(
    BaseConfig[
        ElasticsearchConnectionConfig,
        ElasticsearchPoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def client_kwargs(self) -> StrToAnyDict:
        client_kwargs = {}

        if self.connection.username and self.connection.password:
            client_kwargs["http_auth"] = (
                self.connection.username,
                self.connection.password,
            )

        client_kwargs.update(self.pooling.client_kwargs)

        return client_kwargs

    @overload
    def create_client(
        self, connection: Literal[Connection.ASYNC]
    ) -> AsyncElasticsearch: ...
    @overload
    def create_client(self, connection: Literal[Connection.SYNC]) -> Elasticsearch: ...
    def create_client(
        self, connection: Connection
    ) -> AsyncElasticsearch | Elasticsearch:
        hosts = [{"host": self.connection.host, "port": self.connection.port}]
        if connection is Connection.ASYNC:
            return AsyncElasticsearch(hosts, **self.client_kwargs)
        else:
            return Elasticsearch(hosts, **self.client_kwargs)


class MongoConfig(
    BaseConfig[
        MongoConnectionConfig,
        MongoPoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def client_kwargs(self) -> StrToAnyDict:
        return self.pooling.client_kwargs

    @overload
    def create_client(
        self, connection: Literal[Connection.ASYNC]
    ) -> AsyncIOMotorClient: ...
    @overload
    def create_client(self, connection: Literal[Connection.SYNC]) -> MongoClient: ...
    def create_client(self, connection: Connection) -> AsyncIOMotorClient | MongoClient:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return AsyncIOMotorClient(url, **self.client_kwargs)
        else:
            return MongoClient(url, **self.client_kwargs)


class RedisConfig(
    BaseConfig[
        RedisConnectionConfig,
        RedisPoolingConfig,
        RedisAdditionalConfig,
    ]
):
    additional: RedisAdditionalConfig = Field(..., description="Additional config")

    @property
    def client_kwargs(self) -> StrToAnyDict:
        return self.pooling.client_kwargs

    @overload
    def create_client(self, connection: Literal[Connection.ASYNC]) -> AsyncRedis: ...
    @overload
    def create_client(self, connection: Literal[Connection.SYNC]) -> SyncRedis: ...
    def create_client(self, connection: Connection) -> AsyncRedis | SyncRedis:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return AsyncRedis.from_url(url, **self.client_kwargs)
        else:
            return SyncRedis.from_url(url, **self.client_kwargs)

    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[False],
        environment: OptEnvironment = None,
        use_self_base: Literal[False],
        base: OptStr = None,
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[False],
        environment: OptEnvironment = None,
        use_self_base: Literal[False],
        base: OptStr = None,
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[False],
        environment: OptEnvironment = None,
        use_self_base: Literal[True] = True,
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[False],
        environment: OptEnvironment = None,
        use_self_base: Literal[True] = True,
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[True] = True,
        use_self_base: Literal[False],
        base: OptStr = None,
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[True] = True,
        use_self_base: Literal[False],
        base: OptStr = None,
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[True] = True,
        use_self_base: Literal[True] = True,
        origin: Literal[CacheOrigin.SERVICE],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    @overload
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: Literal[True] = True,
        use_self_base: Literal[True] = True,
        client: str,
        origin: Literal[CacheOrigin.CLIENT],
        layer: CacheLayer,
        sep: str = ":",
    ) -> str: ...
    def build_namespace(
        self,
        *ext: str,
        use_self_environment: bool = True,
        environment: OptEnvironment = None,
        use_self_base: bool = True,
        base: OptStr = None,
        client: OptStr = None,
        origin: CacheOrigin,
        layer: CacheLayer,
        sep: str = ":",
    ) -> str:
        if use_self_environment:
            final_environment = self.identifier.environment
        else:
            final_environment = environment

        if use_self_base:
            final_base = self.additional.base_namespace
        else:
            final_base = base

        if origin is CacheOrigin.CLIENT:
            if client is None:
                raise ValueError(
                    "Argument 'client' can not be None if origin is client"
                )

            return build_cache_namespace(
                *ext,
                environment=final_environment,
                base=final_base,
                client=client,
                origin=origin,
                layer=layer,
                sep=sep,
            )

        return build_cache_namespace(
            *ext,
            environment=final_environment,
            base=final_base,
            origin=origin,
            layer=layer,
            sep=sep,
        )


NoSQLConfigT = TypeVar(
    "NoSQLConfigT",
    ElasticsearchConfig,
    MongoConfig,
    RedisConfig,
)


class MySQLConfig(
    BaseConfig[
        MySQLConnectionConfig,
        MySQLPoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return {
            **self.connection.engine_kwargs,
            **self.pooling.engine_kwargs,
        }

    @overload
    def create_engine(self, connection: Literal[Connection.ASYNC]) -> AsyncEngine: ...
    @overload
    def create_engine(self, connection: Literal[Connection.SYNC]) -> Engine: ...
    def create_engine(self, connection: Connection) -> AsyncEngine | Engine:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return create_async_engine(url, **self.engine_kwargs)
        elif connection is Connection.SYNC:
            return create_sync_engine(url, **self.engine_kwargs)


class PostgreSQLConfig(
    BaseConfig[
        PostgreSQLConnectionConfig,
        PostgreSQLPoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return {
            **self.connection.engine_kwargs,
            **self.pooling.engine_kwargs,
        }

    @overload
    def create_engine(self, connection: Literal[Connection.ASYNC]) -> AsyncEngine: ...
    @overload
    def create_engine(self, connection: Literal[Connection.SYNC]) -> Engine: ...
    def create_engine(self, connection: Connection) -> AsyncEngine | Engine:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return create_async_engine(url, **self.engine_kwargs)
        elif connection is Connection.SYNC:
            return create_sync_engine(url, **self.engine_kwargs)


class SQLiteConfig(
    BaseConfig[
        SQLiteConnectionConfig,
        SQLitePoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return {
            **self.connection.engine_kwargs,
            **self.pooling.engine_kwargs,
        }

    @overload
    def create_engine(self, connection: Literal[Connection.ASYNC]) -> AsyncEngine: ...
    @overload
    def create_engine(self, connection: Literal[Connection.SYNC]) -> Engine: ...
    def create_engine(self, connection: Connection) -> AsyncEngine | Engine:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return create_async_engine(url, **self.engine_kwargs)
        elif connection is Connection.SYNC:
            return create_sync_engine(url, **self.engine_kwargs)


class SQLServerConfig(
    BaseConfig[
        SQLServerConnectionConfig,
        SQLServerPoolingConfig,
        None,
    ]
):
    additional: None = None

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return {
            **self.connection.engine_kwargs,
            **self.pooling.engine_kwargs,
        }

    @overload
    def create_engine(self, connection: Literal[Connection.ASYNC]) -> AsyncEngine: ...
    @overload
    def create_engine(self, connection: Literal[Connection.SYNC]) -> Engine: ...
    def create_engine(self, connection: Connection) -> AsyncEngine | Engine:
        url = self.connection.make_url(connection)
        if connection is Connection.ASYNC:
            return create_async_engine(url, **self.engine_kwargs)
        elif connection is Connection.SYNC:
            return create_sync_engine(url, **self.engine_kwargs)


SQLConfigT = TypeVar(
    "SQLConfigT",
    MySQLConfig,
    PostgreSQLConfig,
    SQLiteConfig,
    SQLServerConfig,
)


DatabaseConfigT = TypeVar(
    "DatabaseConfigT",
    ElasticsearchConfig,
    MongoConfig,
    RedisConfig,
    MySQLConfig,
    PostgreSQLConfig,
    SQLiteConfig,
    SQLServerConfig,
)


class ElasticsearchConfigs(BaseModel):
    primary: ElasticsearchConfig = Field(
        ..., description="Primary Elasticsearch config"
    )


OptElasticsearchConfigs = ElasticsearchConfigs | None
ElasticsearchConfigsT = TypeVar("ElasticsearchConfigsT", bound=OptElasticsearchConfigs)


class MongoConfigs(BaseModel):
    primary: MongoConfig = Field(..., description="Primary Mongo config")


OptMongoConfigs = MongoConfigs | None
MongoConfigsT = TypeVar("MongoConfigsT", bound=OptMongoConfigs)


class RedisConfigs(BaseModel):
    primary: RedisConfig = Field(..., description="Primary Redis config")


OptRedisConfigs = RedisConfigs | None
RedisConfigsT = TypeVar("RedisConfigsT", bound=OptRedisConfigs)


class NoSQLConfigs(
    BaseModel, Generic[ElasticsearchConfigsT, MongoConfigsT, RedisConfigsT]
):
    elasticsearch: ElasticsearchConfigsT = Field(
        ..., description="Elasticsearch configs"
    )
    mongo: MongoConfigsT = Field(..., description="Mongo configs")
    redis: RedisConfigsT = Field(..., description="Redis configs")


OptNoSQLConfigs = NoSQLConfigs | None
NoSQLConfigsT = TypeVar("NoSQLConfigsT", bound=OptNoSQLConfigs)


class MySQLConfigs(BaseModel):
    primary: MySQLConfig = Field(..., description="Primary MySQL config")


OptMySQLConfigs = MySQLConfigs | None
MySQLConfigsT = TypeVar("MySQLConfigsT", bound=OptMySQLConfigs)


class PostgreSQLConfigs(BaseModel):
    primary: PostgreSQLConfig = Field(..., description="Primary PostgreSQL config")


OptPostgreSQLConfigs = PostgreSQLConfigs | None
PostgreSQLConfigsT = TypeVar("PostgreSQLConfigsT", bound=OptPostgreSQLConfigs)


class SQLiteConfigs(BaseModel):
    primary: SQLiteConfig = Field(..., description="Primary SQLite config")


OptSQLiteConfigs = SQLiteConfigs | None
SQLiteConfigsT = TypeVar("SQLiteConfigsT", bound=OptSQLiteConfigs)


class SQLServerConfigs(BaseModel):
    primary: SQLServerConfig = Field(..., description="Primary SQLServer config")


OptSQLServerConfigs = SQLServerConfigs | None
SQLServerConfigsT = TypeVar("SQLServerConfigsT", bound=OptSQLServerConfigs)


class SQLConfigs(
    BaseModel,
    Generic[
        MySQLConfigsT,
        PostgreSQLConfigsT,
        SQLiteConfigsT,
        SQLServerConfigsT,
    ],
):
    mysql: MySQLConfigsT = Field(..., description="MySQL configs")
    postgresql: PostgreSQLConfigsT = Field(..., description="PostgreSQL configs")
    sqlite: SQLiteConfigsT = Field(..., description="SQLite configs")
    sqlserver: SQLServerConfigsT = Field(..., description="SQLServer configs")


OptSQLConfigs = SQLConfigs | None
SQLConfigsT = TypeVar("SQLConfigsT", bound=OptSQLConfigs)


class DatabaseConfigs(
    BaseModel,
    Generic[
        NoSQLConfigsT,
        SQLConfigsT,
    ],
):
    nosql: NoSQLConfigsT = Field(..., description="NoSQL configs")
    sql: SQLConfigsT = Field(..., description="SQL configs")


OptDatabaseConfigs = DatabaseConfigs | None
DatabaseConfigsT = TypeVar("DatabaseConfigsT", bound=OptDatabaseConfigs)


class DatabaseConfigsMixin(BaseModel, Generic[DatabaseConfigsT]):
    database: DatabaseConfigsT = Field(..., description="Database configs")
