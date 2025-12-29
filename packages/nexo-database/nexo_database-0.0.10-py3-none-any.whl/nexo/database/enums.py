from enum import StrEnum
from nexo.types.string import ListOfStrs


class CacheOrigin(StrEnum):
    CLIENT = "client"
    SERVICE = "service"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class CacheLayer(StrEnum):
    REPOSITORY = "repository"
    SERVICE = "service"
    CONTROLLER = "controller"
    MIDDLEWARE = "middleware"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class Connection(StrEnum):
    ASYNC = "async"
    SYNC = "sync"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class Driver(StrEnum):
    # SQL Databases - Most Popular
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"

    # SQL Databases - Enterprise
    MSSQL = "mssql"

    # NoSQL Document Stores
    MONGODB = "mongodb"

    # NoSQL Key-Value
    REDIS = "redis"

    # Search Engines
    ELASTICSEARCH = "elasticsearch"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class PostgreSQLSSLMode(StrEnum):
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptPostgreSQLSSLMode = PostgreSQLSSLMode | None


class MySQLCharset(StrEnum):
    UTF8 = "utf8"
    UTF8MB4 = "utf8mb4"
    LATIN1 = "latin1"
    ASCII = "ascii"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class MongoReadPreference(StrEnum):
    PRIMARY = "primary"
    PRIMARY_PREFERRED = "primaryPreferred"
    SECONDARY = "secondary"
    SECONDARY_PREFERRED = "secondaryPreferred"
    NEAREST = "nearest"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


OptMongoReadPreference = MongoReadPreference | None


class ElasticsearchScheme(StrEnum):
    HTTP = "http"
    HTTPS = "https"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


class PoolingStrategy(StrEnum):
    FIXED = "fixed"
    DYNAMIC = "dynamic"
    OVERFLOW = "overflow"
    QUEUE = "queue"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]
