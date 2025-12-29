from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated, Generic, TypeVar
from .config import (
    ElasticsearchConfig,
    MongoConfig,
    RedisConfig,
    MySQLConfig,
    PostgreSQLConfig,
    SQLiteConfig,
    SQLServerConfig,
    DatabaseConfigT,
)
from .managers import (
    ElasticsearchManager,
    MongoManager,
    RedisManager,
    MySQLManager,
    PostgreSQLManager,
    SQLiteManager,
    SQLServerManager,
    DatabaseManagerT,
)
from .types import DeclarativeBaseT


class Handler(
    BaseModel,
    Generic[
        DatabaseConfigT,
        DatabaseManagerT,
    ],
):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Annotated[DatabaseConfigT, Field(..., description="Config")]
    manager: Annotated[DatabaseManagerT, Field(..., description="Manager")]


HandlerT = TypeVar("HandlerT", bound=Handler)


class ElasticsearchHandler(Handler[ElasticsearchConfig, ElasticsearchManager]):
    pass


class MongoHandler(Handler[MongoConfig, MongoManager]):
    pass


class RedisHandler(Handler[RedisConfig, RedisManager]):
    pass


class MySQLHandler(
    Handler[MySQLConfig, MySQLManager[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


class PostgreSQLHandler(
    Handler[PostgreSQLConfig, PostgreSQLManager[DeclarativeBaseT]],
    Generic[DeclarativeBaseT],
):
    pass


class SQLiteHandler(
    Handler[SQLiteConfig, SQLiteManager[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


class SQLServerHandler(
    Handler[SQLServerConfig, SQLServerManager[DeclarativeBaseT]],
    Generic[DeclarativeBaseT],
):
    pass


class BaseHandlers(BaseModel, Generic[HandlerT]):
    primary: Annotated[HandlerT, Field(..., description="Primary handler")]


OptBaseHandlers = BaseHandlers | None
BaseHandlersT = TypeVar("BaseHandlersT", bound=OptBaseHandlers)


class ElasticsearchHandlers(BaseHandlers[ElasticsearchHandler]):
    pass


OptElasticsearchHandlers = ElasticsearchHandlers | None
ElasticsearchHandlersT = TypeVar(
    "ElasticsearchHandlersT", bound=OptElasticsearchHandlers
)


class MongoHandlers(BaseHandlers[MongoHandler]):
    pass


OptMongoHandlers = MongoHandlers | None
MongoHandlersT = TypeVar("MongoHandlersT", bound=OptMongoHandlers)


class RedisHandlers(BaseHandlers[RedisHandler]):
    pass


OptRedisHandlers = RedisHandlers | None
RedisHandlersT = TypeVar("RedisHandlersT", bound=OptRedisHandlers)


class NoSQLHandlers(
    BaseModel, Generic[ElasticsearchHandlersT, MongoHandlersT, RedisHandlersT]
):
    elasticsearch: Annotated[
        ElasticsearchHandlersT, Field(..., description="Elasticsearch handlers")
    ]
    mongo: Annotated[MongoHandlersT, Field(..., description="Mongo handlers")]
    redis: Annotated[RedisHandlersT, Field(..., description="Redis handlers")]


OptNoSQLHandlers = NoSQLHandlers | None
NoSQLHandlersT = TypeVar("NoSQLHandlersT", bound=OptNoSQLHandlers)


class MySQLHandlers(
    BaseHandlers[MySQLHandler[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


OptMySQLHandlers = MySQLHandlers | None
MySQLHandlersT = TypeVar("MySQLHandlersT", bound=OptMySQLHandlers)


class PostgreSQLHandlers(
    BaseHandlers[PostgreSQLHandler[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


OptPostgreSQLHandlers = PostgreSQLHandlers | None
PostgreSQLHandlersT = TypeVar("PostgreSQLHandlersT", bound=OptPostgreSQLHandlers)


class SQLiteHandlers(
    BaseHandlers[SQLiteHandler[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


OptSQLiteHandlers = SQLiteHandlers | None
SQLiteHandlersT = TypeVar("SQLiteHandlersT", bound=OptSQLiteHandlers)


class SQLServerHandlers(
    BaseHandlers[SQLServerHandler[DeclarativeBaseT]], Generic[DeclarativeBaseT]
):
    pass


OptSQLServerHandlers = SQLServerHandlers | None
SQLServerHandlersT = TypeVar("SQLServerHandlersT", bound=OptSQLServerHandlers)


class SQLHandlers(
    BaseModel,
    Generic[
        MySQLHandlersT,
        PostgreSQLHandlersT,
        SQLiteHandlersT,
        SQLServerHandlersT,
    ],
):
    mysql: Annotated[MySQLHandlersT, Field(..., description="MySQL handlers")]
    postgresql: Annotated[
        PostgreSQLHandlersT, Field(..., description="PostgreSQL handlers")
    ]
    sqlite: Annotated[SQLiteHandlersT, Field(..., description="SQLite handlers")]
    sqlserver: Annotated[
        SQLServerHandlersT, Field(..., description="SQLServer handlers")
    ]


OptSQLHandlers = SQLHandlers | None
SQLHandlersT = TypeVar("SQLHandlersT", bound=OptSQLHandlers)


class DatabaseHandlers(
    BaseModel,
    Generic[
        NoSQLHandlersT,
        SQLHandlersT,
    ],
):
    nosql: Annotated[NoSQLHandlersT, Field(..., description="NoSQL handlers")]
    sql: Annotated[SQLHandlersT, Field(..., description="SQL handlers")]


OptDatabaseHandlers = DatabaseHandlers | None
DatabaseHandlersT = TypeVar("DatabaseHandlersT", bound=OptDatabaseHandlers)
