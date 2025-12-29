from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from copy import deepcopy
from datetime import datetime, timezone
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    DatabaseError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from typing import (
    AsyncGenerator,
    Generator,
    Generic,
    Literal,
    Tuple,
    overload,
)
from uuid import uuid4
from nexo.logging.enums import LogLevel
from nexo.logging.logger import Database
from nexo.schemas.application import ApplicationContext, OptApplicationContext
from nexo.schemas.connection import OptConnectionContext
from nexo.schemas.error.enums import ErrorCode
from nexo.schemas.exception.exc import (
    MaleoException,
    Conflict,
    UnprocessableEntity,
    InternalServerError,
    ServiceUnavailable,
)
from nexo.schemas.exception.factory import MaleoExceptionFactory
from nexo.schemas.google import ListOfPublisherHandlers
from nexo.schemas.operation.action.system import SystemOperationAction
from nexo.schemas.operation.context import generate
from nexo.schemas.operation.enums import (
    OperationType,
    SystemOperationType,
    Origin,
    Layer,
    Target,
)
from nexo.schemas.operation.mixins import Timestamp
from nexo.schemas.operation.system import SuccessfulSystemOperation
from nexo.schemas.security.authentication import OptAnyAuthentication
from nexo.schemas.security.authorization import OptAnyAuthorization
from nexo.schemas.security.impersonation import OptImpersonation
from nexo.types.uuid import OptUUID
from nexo.utils.exception import extract_details
from ..enums import Connection
from ..config import SQLConfigT


class SessionManager(Generic[SQLConfigT]):
    def __init__(
        self,
        config: SQLConfigT,
        engines: Tuple[AsyncEngine, Engine],
        logger: Database,
        publishers: ListOfPublisherHandlers = [],
        application_context: OptApplicationContext = None,
    ):
        self._config = config
        self._async_engine, self._sync_engine = engines
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
            target_details=self._config.model_dump(include={"identifier"}),
        )
        self._operation_action = SystemOperationAction(
            type=SystemOperationType.DATABASE_CONNECTION, details=None
        )

        self.async_sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker[
            AsyncSession
        ](bind=self._async_engine, expire_on_commit=True)
        self.sync_sessionmaker: sessionmaker[Session] = sessionmaker[Session](
            bind=self._sync_engine, expire_on_commit=True
        )

    @overload
    def make(
        self,
        connection: Literal[Connection.ASYNC],
    ) -> AsyncSession: ...
    @overload
    def make(
        self,
        connection: Literal[Connection.SYNC],
    ) -> Session: ...
    def make(
        self,
        connection: Connection = Connection.ASYNC,
    ) -> AsyncSession | Session:
        """Make session."""
        if connection is Connection.ASYNC:
            return self.async_sessionmaker()
        else:
            return self.sync_sessionmaker()

    def make_async(self) -> AsyncSession:
        """Explicit async session."""
        return self.make(Connection.ASYNC)

    def make_sync(self) -> Session:
        """Explicit sync session."""
        return self.make(Connection.SYNC)

    async def _async_session_handler(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Reusable function for managing async database session."""
        operation_id = operation_id if operation_id is not None else uuid4()

        common_kwargs = {
            "application_context": self._application_context,
            "connection_context": connection_context,
            "authentication": authentication,
            "authorization": authorization,
            "impersonation": impersonation,
        }

        common_operation_kwargs = deepcopy(common_kwargs)
        common_operation_kwargs.update(
            {
                "id": operation_id,
                "context": self._operation_context,
                "action": self._operation_action,
            }
        )

        common_exc_kwargs = deepcopy(common_kwargs)
        common_exc_kwargs.update(
            {
                "operation_type": OperationType.SYSTEM,
                "operation_id": operation_id,
                "operation_context": self._operation_context,
                "operation_action": self._operation_action,
            }
        )

        session: AsyncSession = self.make_async()
        operation = SuccessfulSystemOperation[None](
            **common_operation_kwargs,
            timestamp=Timestamp.now(),
            summary="Successfully created new async database session",
            response=None,
        )
        operation.log(self._logger, LogLevel.DEBUG)
        operation.publish(self._logger, self._publishers)

        executed_at = datetime.now(tz=timezone.utc)

        try:
            # explicit transaction context — will commit on success, rollback on exception
            async with session.begin():
                yield session
            operation = SuccessfulSystemOperation[None](
                **common_operation_kwargs,
                timestamp=Timestamp.completed_now(executed_at),
                summary="Successfully committed async database transaction",
                response=None,
            )
            operation.log(self._logger, LogLevel.DEBUG)
            operation.publish(self._logger, self._publishers)
        except IntegrityError as ie:
            await session.rollback()
            exc = Conflict(
                *ie.args,
                details=extract_details(ie),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="IntegrityError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from ie
                else:
                    raise ie
        except OperationalError as oe:
            await session.rollback()
            exc = ServiceUnavailable(
                *oe.args,
                details=extract_details(oe),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="OperationalError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from oe
                else:
                    raise oe
        except ProgrammingError as pe:
            await session.rollback()
            exc = InternalServerError(
                *pe.args,
                details=extract_details(pe),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="ProgrammingError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from pe
                else:
                    raise pe
        except DatabaseError as de:
            await session.rollback()
            exc = InternalServerError(
                *de.args,
                details=extract_details(de),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="DatabaseError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from de
                else:
                    raise de
        except SQLAlchemyError as se:
            await session.rollback()
            exc = InternalServerError(
                *se.args,
                details=extract_details(se),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="SQLAlchemyError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from se
                else:
                    raise se
        except ValidationError as ve:
            await session.rollback()
            exc = UnprocessableEntity(
                details=extract_details(ve),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="ValidationError occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from ve
                else:
                    raise ve
        except HTTPException as he:
            await session.rollback()
            exc = MaleoExceptionFactory.from_code(
                he.status_code,
                details=extract_details(he),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="HTTPException occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from he
                else:
                    raise he
        except MaleoException as me:
            await session.rollback()
            me.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                raise me
        except Exception as e:
            await session.rollback()
            code: int | ErrorCode | None = None
            attr_names = ["code", "status_code"]
            for attr_name in attr_names:
                code = getattr(e, attr_name, None)
                if code is not None and isinstance(code, (int, ErrorCode)):
                    break
            if code is None:
                code = ErrorCode.INTERNAL_SERVER_ERROR
            exc = MaleoExceptionFactory.from_code(
                code,
                details=extract_details(e),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Unexpected error occured while handling async database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from e
                else:
                    raise e
        finally:
            await session.close()
            operation = SuccessfulSystemOperation[None](
                **common_operation_kwargs,
                timestamp=Timestamp.now(),
                summary="Successfully closed async database session",
                response=None,
            )
            operation.log(self._logger, LogLevel.DEBUG)
            operation.publish(self._logger, self._publishers)

    def _sync_session_handler(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> Generator[Session, None, None]:
        """Reusable function for managing sync database session."""
        operation_id = operation_id if operation_id is not None else uuid4()

        common_kwargs = {
            "application_context": self._application_context,
            "connection_context": connection_context,
            "authentication": authentication,
            "authorization": authorization,
            "impersonation": impersonation,
        }

        common_operation_kwargs = deepcopy(common_kwargs)
        common_operation_kwargs.update(
            {
                "id": operation_id,
                "context": self._operation_context,
                "action": self._operation_action,
            }
        )

        common_exc_kwargs = deepcopy(common_kwargs)
        common_exc_kwargs.update(
            {
                "operation_type": OperationType.SYSTEM,
                "operation_id": operation_id,
                "operation_context": self._operation_context,
                "operation_action": self._operation_action,
            }
        )

        session: Session = self.make_sync()
        operation = SuccessfulSystemOperation[None](
            **common_operation_kwargs,
            timestamp=Timestamp.now(),
            summary="Successfully created new sync database session",
            response=None,
        )
        operation.log(self._logger, LogLevel.DEBUG)
        operation.publish(self._logger, self._publishers)

        executed_at = datetime.now(tz=timezone.utc)

        try:
            # explicit transaction context — will commit on success, rollback on exception
            with session.begin():
                yield session
            operation = SuccessfulSystemOperation[None](
                **common_operation_kwargs,
                timestamp=Timestamp.completed_now(executed_at),
                summary="Successfully committed sync database transaction",
                response=None,
            )
            operation.log(self._logger, LogLevel.DEBUG)
            operation.publish(self._logger, self._publishers)
        except IntegrityError as ie:
            session.rollback()
            exc = Conflict(
                *ie.args,
                details=extract_details(ie),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="IntegrityError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from ie
                else:
                    raise ie
        except OperationalError as oe:
            session.rollback()
            exc = ServiceUnavailable(
                *oe.args,
                details=extract_details(oe),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="OperationalError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from oe
                else:
                    raise oe
        except ProgrammingError as pe:
            session.rollback()
            exc = InternalServerError(
                *pe.args,
                details=extract_details(pe),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="ProgrammingError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from pe
                else:
                    raise pe
        except DatabaseError as de:
            session.rollback()
            exc = InternalServerError(
                *de.args,
                details=extract_details(de),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="DatabaseError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from de
                else:
                    raise de
        except SQLAlchemyError as se:
            session.rollback()
            exc = InternalServerError(
                *se.args,
                details=extract_details(se),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="SQLAlchemyError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from se
                else:
                    raise se
        except ValidationError as ve:
            session.rollback()
            exc = UnprocessableEntity(
                details=extract_details(ve),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="ValidationError occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from ve
                else:
                    raise ve
        except HTTPException as he:
            session.rollback()
            exc = MaleoExceptionFactory.from_code(
                he.status_code,
                details=extract_details(he),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="HTTPException occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from he
                else:
                    raise he
        except MaleoException as me:
            session.rollback()
            me.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                raise me
        except Exception as e:
            session.rollback()
            code: int | ErrorCode | None = None
            attr_names = ["code", "status_code"]
            for attr_name in attr_names:
                code = getattr(e, attr_name, None)
                if code is not None and isinstance(code, (int, ErrorCode)):
                    break
            if code is None:
                code = ErrorCode.INTERNAL_SERVER_ERROR
            exc = MaleoExceptionFactory.from_code(
                code,
                details=extract_details(e),
                **common_exc_kwargs,
                operation_timestamp=Timestamp.completed_now(executed_at),
                operation_summary="Unexpected error occured while handling sync database session",
            )
            exc.log_and_publish_operation(self._logger, self._publishers)
            if raise_exc:
                if raise_as_maleo_exception:
                    raise exc from e
                else:
                    raise e
        finally:
            session.close()
            operation = SuccessfulSystemOperation[None](
                **common_operation_kwargs,
                timestamp=Timestamp.now(),
                summary="Successfully closed sync database session",
                response=None,
            )
            operation.log(self._logger, LogLevel.DEBUG)
            operation.publish(self._logger, self._publishers)

    @asynccontextmanager
    async def _async_context_manager(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager implementation."""
        async for session in self._async_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
            raise_exc,
            raise_as_maleo_exception,
        ):
            yield session

    @contextmanager
    def _sync_context_manager(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> Generator[Session, None, None]:
        """Sync context manager implementation."""
        yield from self._sync_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
            raise_exc,
            raise_as_maleo_exception,
        )

    # Overloaded context manager methods
    @overload
    def get(
        self,
        connection: Literal[Connection.ASYNC],
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AbstractAsyncContextManager[AsyncSession]: ...
    @overload
    def get(
        self,
        connection: Literal[Connection.SYNC],
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AbstractContextManager[Session]: ...
    def get(
        self,
        connection: Connection = Connection.ASYNC,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AbstractAsyncContextManager[AsyncSession] | AbstractContextManager[Session]:
        """Context manager for manual session handling."""
        if connection is Connection.ASYNC:
            return self._async_context_manager(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
                raise_exc,
                raise_as_maleo_exception,
            )
        else:
            return self._sync_context_manager(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
                raise_exc,
                raise_as_maleo_exception,
            )

    # Alternative: More explicit methods
    @asynccontextmanager
    async def get_async(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Explicit async context manager."""
        async for session in self._async_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
            raise_exc,
            raise_as_maleo_exception,
        ):
            yield session

    @contextmanager
    def get_sync(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ) -> Generator[Session, None, None]:
        """Explicit sync context manager."""
        yield from self._sync_session_handler(
            operation_id,
            connection_context,
            authentication,
            authorization,
            impersonation,
            raise_exc,
            raise_as_maleo_exception,
        )

    def as_async_dependency(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ):
        """Explicit async dependency injection."""

        def dependency() -> AsyncGenerator[AsyncSession, None]:
            return self._async_session_handler(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
                raise_exc,
                raise_as_maleo_exception,
            )

        return dependency

    def as_sync_dependency(
        self,
        operation_id: OptUUID = None,
        connection_context: OptConnectionContext = None,
        authentication: OptAnyAuthentication = None,
        authorization: OptAnyAuthorization = None,
        impersonation: OptImpersonation = None,
        raise_exc: bool = True,
        raise_as_maleo_exception: bool = True,
    ):
        """Explicit sync dependency injection."""

        def dependency() -> Generator[Session, None, None]:
            return self._sync_session_handler(
                operation_id,
                connection_context,
                authentication,
                authorization,
                impersonation,
                raise_exc,
                raise_as_maleo_exception,
            )

        return dependency

    def dispose(self):
        self.sync_sessionmaker.close_all()
