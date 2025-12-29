from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Annotated, Self, Set, TypeVar
from nexo.types.dict import OptStrToStrDict, StrToAnyDict
from nexo.types.integer import ListOfInts
from nexo.types.string import OptStr
from nexo.utils.formatter import CaseFormatter
from ..enums import PoolingStrategy


class BasePoolingConfig(BaseModel):
    """Base configuration class for database connection pooling."""


class ElasticsearchPoolingConfig(BasePoolingConfig):
    """Elasticsearch-specific pooling configuration."""

    block: Annotated[bool, Field(False, description="Block when pool is full")] = False
    ca_certs: Annotated[OptStr, Field(None, description="Path to CA certificates")] = (
        None
    )
    connections_per_node: Annotated[
        int, Field(10, description="Connections per Elasticsearch node", ge=1, le=50)
    ]
    dead_timeout: Annotated[
        float, Field(60.0, description="Dead node timeout in seconds", ge=5.0, le=600.0)
    ] = 60.0
    headers: Annotated[
        OptStrToStrDict,
        Field(None, description="Default headers for requests"),
    ] = None
    http_compress: Annotated[
        bool, Field(True, description="Enable HTTP compression")
    ] = True
    max_retries: Annotated[
        int, Field(3, description="Maximum number of retries", ge=0, le=10)
    ]
    maxsize: Annotated[
        int,
        Field(25, description="Maximum number of connections in pool", ge=1, le=100),
    ]
    retry_on_status: Annotated[
        ListOfInts,
        Field(
            [502, 503, 504],
            description="HTTP status codes to retry on",
        ),
    ] = [502, 503, 504]
    retry_on_timeout: Annotated[bool, Field(False, description="Retry on timeout")] = (
        False
    )
    timeout: Annotated[
        float, Field(10.0, description="Request timeout in seconds", ge=1.0, le=300.0)
    ]
    verify_certs: Annotated[
        bool, Field(True, description="Verify SSL certificates")
    ] = True

    @model_validator(mode="after")
    def validate_overflow(self) -> Self:
        if self.connections_per_node > self.maxsize:
            raise ValueError("connections_per_node must not exceed maxsize")
        return self

    @property
    def client_kwargs_exclusions(self) -> Set[str]:
        return {
            "connections_per_node",
            "block",
            "headers",
            "dead_timeout",
        }

    @property
    def client_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.client_kwargs_exclusions, exclude_none=True)


class MongoPoolingConfig(BasePoolingConfig):
    """Mongo-specific pooling configuration."""

    model_config = ConfigDict(alias_generator=CaseFormatter.to_camel)

    connect_timeout_ms: Annotated[
        int,
        Field(
            20_000,
            alias="connectTimeoutMS",
            description="Connection timeout in milliseconds",
            ge=1_000,
            le=300_000,
        ),
    ] = 20_000
    max_connecting: Annotated[
        int,
        Field(
            2,
            alias="maxConnecting",
            description="Maximum number of concurrent connection attempts",
            ge=1,
            le=10,
        ),
    ] = 2
    max_idle_time_ms: Annotated[
        int,
        Field(
            600_000,
            alias="maxIdleTimeMS",
            description="Max idle time in milliseconds",
            ge=1_000,
            le=3_600_000,
        ),
    ] = 600_000
    max_pool_size: Annotated[
        int,
        Field(
            100,
            alias="maxPoolSiza",
            description="Maximum number of connections in pool",
            ge=1,
            le=500,
        ),
    ] = 100
    min_pool_size: Annotated[
        int,
        Field(
            0,
            alias="minPoolSize",
            description="Minimum number of connections in pool",
            ge=0,
            le=100,
        ),
    ] = 0
    server_selection_timeout_ms: Annotated[
        int,
        Field(
            30_000,
            alias="serverSelectionTimeoutMS",
            description="Server selection timeout",
            ge=1_000,
            le=300_000,
        ),
    ] = 30_000

    @property
    def client_kwargs(self) -> StrToAnyDict:
        return self.model_dump(by_alias=True, exclude_none=True)


class RedisPoolingConfig(BasePoolingConfig):
    """Redis-specific pooling configuration."""

    connection_timeout: Annotated[
        float, Field(5.0, description="Connection timeout in seconds", ge=1.0, le=60.0)
    ] = 5.0
    decode_responses: Annotated[
        bool, Field(True, description="Decode responses to strings")
    ] = True
    health_check_interval: Annotated[
        int, Field(30, description="Health check interval in seconds", ge=5, le=300)
    ] = 30
    max_connections: Annotated[
        int,
        Field(50, description="Maximum number of connections in pool", ge=1, le=1_000),
    ] = 50
    retry_on_timeout: Annotated[
        bool, Field(True, description="Retry on connection timeout")
    ] = True
    socket_timeout: Annotated[
        float, Field(5.0, description="Socket timeout in seconds", ge=1.0, le=60.0)
    ] = 5.0
    socket_keepalive: Annotated[
        bool, Field(True, description="Enable TCP keepalive")
    ] = True

    @property
    def client_kwargs_exclusions(self) -> Set[str]:
        return {"health_check_interval", "connection_timeout"}

    @property
    def client_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.client_kwargs_exclusions, exclude_none=True)


class MySQLPoolingConfig(BasePoolingConfig):
    """MySQL-specific pooling configuration."""

    autocommit: Annotated[bool, Field(False, description="Enable autocommit mode")] = (
        False
    )
    connect_timeout: Annotated[
        float, Field(10.0, description="Connection timeout in seconds", ge=1.0, le=60.0)
    ] = 10.0
    max_overflow: Annotated[
        int,
        Field(15, description="Maximum number of overflow connections", ge=0, le=200),
    ] = 15
    pool_pre_ping: Annotated[
        bool, Field(True, description="Validate connections before use")
    ] = True
    pool_recycle: Annotated[
        int,
        Field(7200, description="Connection recycle time in seconds", ge=60, le=86_400),
    ] = 7200
    pool_size: Annotated[
        int, Field(8, description="Number of connections in the pool", ge=1, le=500)
    ] = 8
    pool_timeout: Annotated[
        float,
        Field(
            20.0,
            description="Timeout in seconds for getting connection",
            ge=1.0,
            le=300.0,
        ),
    ] = 20.0
    strategy: Annotated[
        PoolingStrategy, Field(PoolingStrategy.FIXED, description="Pooling strategy")
    ] = PoolingStrategy.FIXED

    @property
    def engine_kwargs_exclusions(self) -> Set[str]:
        return {"strategy"}

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.engine_kwargs_exclusions, exclude_none=True)


class PostgreSQLPoolingConfig(BasePoolingConfig):
    """PostgreSQL-specific pooling configuration."""

    max_overflow: Annotated[
        int,
        Field(20, description="Maximum number of overflow connections", ge=0, le=500),
    ] = 20
    pool_pre_ping: Annotated[
        bool, Field(True, description="Validate connections before use")
    ] = True
    pool_recycle: Annotated[
        int,
        Field(
            3_600, description="Connection recycle time in seconds", ge=60, le=86_400
        ),
    ] = 3_600
    pool_reset_on_return: Annotated[
        bool, Field(True, description="Reset connection state on return to pool")
    ] = True
    pool_size: Annotated[
        int, Field(10, description="Number of connections in the pool", ge=1, le=1_000)
    ] = 10
    pool_timeout: Annotated[
        float,
        Field(
            30.0,
            description="Timeout in seconds for getting connection",
            ge=1.0,
            le=300.0,
        ),
    ] = 30.0
    prepared_statement_cache_size: Annotated[
        int, Field(100, description="Prepared statement cache size", ge=0, le=10_000)
    ] = 100
    strategy: Annotated[
        PoolingStrategy, Field(PoolingStrategy.DYNAMIC, description="Pooling strategy")
    ] = PoolingStrategy.DYNAMIC

    @model_validator(mode="after")
    def validate_overflow(self) -> Self:
        if self.max_overflow > self.pool_size * 5:
            raise ValueError("max_overflow should not exceed 5x pool_size")
        return self

    @property
    def engine_kwargs_exclusions(self) -> Set[str]:
        return {
            "strategy",
            "prepared_statement_cache_size",
            "pool_reset_on_return",
        }

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.engine_kwargs_exclusions, exclude_none=True)


class SQLitePoolingConfig(BasePoolingConfig):
    """SQLite-specific pooling configuration."""

    busy_timeout: Annotated[
        int,
        Field(30_000, description="Busy timeout in milliseconds", ge=1_000, le=300_000),
    ]
    max_overflow: Annotated[
        int, Field(5, description="Maximum overflow connections", ge=0, le=20)
    ] = 5
    pool_size: Annotated[
        int,
        Field(1, description="Number of connections (limited for SQLite)", ge=1, le=10),
    ] = 1
    pool_timeout: Annotated[
        float, Field(30.0, description="Timeout in seconds", ge=1.0, le=300.0)
    ] = 30.0
    wal_mode: Annotated[
        bool, Field(True, description="Enable WAL mode for better concurrency")
    ] = True

    @property
    def engine_kwargs_exclusions(self) -> Set[str]:
        return {
            "wal_mode",
            "busy_timeout",
        }

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.engine_kwargs_exclusions, exclude_none=True)


class SQLServerPoolingConfig(BasePoolingConfig):
    """SQL Server-specific pooling configuration."""

    command_timeout: Annotated[
        int, Field(30, description="Command timeout in seconds", ge=1, le=3_600)
    ]
    connection_timeout: Annotated[
        int, Field(30, description="Connection timeout in seconds", ge=1, le=300)
    ] = 30
    encrypt: Annotated[bool, Field(True, description="Encrypt connection")] = True
    max_overflow: Annotated[
        int,
        Field(20, description="Maximum number of overflow connections", ge=0, le=200),
    ] = 20
    packet_size: Annotated[
        int,
        Field(
            4_096, description="Network packet size", ge=512, le=32_768, multiple_of=256
        ),
    ] = 4_096
    pool_pre_ping: Annotated[
        bool, Field(True, description="Validate connections before use")
    ] = True
    pool_recycle: Annotated[
        int,
        Field(
            3_600, ge=60, le=86_400, description="Connection recycle time in seconds"
        ),
    ] = 3_600
    pool_size: Annotated[
        int, Field(10, description="Number of connections in the pool", ge=1, le=500)
    ]
    pool_timeout: Annotated[
        float,
        Field(
            30.0,
            description="Timeout in seconds for getting connection",
            ge=1.0,
            le=300.0,
        ),
    ] = 30.0
    strategy: Annotated[
        PoolingStrategy, Field(PoolingStrategy.DYNAMIC, description="Pooling strategy")
    ] = PoolingStrategy.DYNAMIC
    trust_server_certificate: Annotated[
        bool, Field(False, description="Trust server certificate")
    ] = False

    @model_validator(mode="after")
    def validate_overflow(self) -> Self:
        if self.max_overflow > self.pool_size * 3:
            raise ValueError("max_overflow should not exceed 3x pool_size")
        return self

    @property
    def engine_kwargs_exclusions(self) -> Set[str]:
        return {
            "connection_timeout",
            "command_timeout",
            "packet_size",
            "trust_server_certificate",
        }

    @property
    def engine_kwargs(self) -> StrToAnyDict:
        return self.model_dump(exclude=self.engine_kwargs_exclusions, exclude_none=True)


PoolingConfigT = TypeVar(
    "PoolingConfigT",
    ElasticsearchPoolingConfig,
    MongoPoolingConfig,
    RedisPoolingConfig,
    MySQLPoolingConfig,
    PostgreSQLPoolingConfig,
    SQLitePoolingConfig,
    SQLServerPoolingConfig,
)
