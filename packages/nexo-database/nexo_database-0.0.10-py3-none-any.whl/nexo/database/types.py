from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Delete, Select, Update
from typing import Any, Tuple, TypeVar


DeclarativeBaseT = TypeVar("DeclarativeBaseT", bound=DeclarativeBase)
RowT = TypeVar("RowT", bound=Tuple[Any, ...])
AnyStmt = Delete | Select[RowT] | Update
StmtTypeT = TypeVar("StmtTypeT", bound=AnyStmt)
