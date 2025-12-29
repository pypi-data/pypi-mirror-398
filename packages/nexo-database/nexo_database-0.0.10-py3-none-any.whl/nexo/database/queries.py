from sqlalchemy import and_, asc, cast, desc, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select
from sqlalchemy.types import DATE, String, TEXT, TIMESTAMP
from typing import Any, Sequence, Type
from nexo.enums.order import Order
from nexo.enums.status import OptListOfDataStatuses
from nexo.schemas.mixins.filter import DateFilter
from nexo.schemas.mixins.sort import SortColumn
from nexo.types.any import ManyAny
from nexo.types.boolean import OptBool
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptListOfStrs, OptStr, ManyStrs
from .types import DeclarativeBaseT, RowT, StmtTypeT


def validate_column(
    table: Type[DeclarativeBaseT],
    column: str,
) -> InstrumentedAttribute | None:
    column_attr = getattr(table, column, None)
    if column_attr is not None and isinstance(column_attr, InstrumentedAttribute):
        return column_attr
    return None


def filter_column(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    column: str,
    value: Any,
    include_null: bool = False,
    strict: bool = True,
) -> StmtTypeT:
    column_attr = validate_column(table=table, column=column)
    if column_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{column}' for table '{table.__tablename__}'"
            )
        return stmt

    filters = []
    if value is not None:
        if isinstance(value, list):
            filters.extend([column_attr == val for val in value])
        else:
            filters.append(column_attr == value)

    if filters:
        if include_null:
            filters.append(column_attr.is_(None))
        stmt = stmt.filter(or_(*filters))

    return stmt


def filter_columns(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    columns: ManyStrs,
    values: ManyAny,
    strict: bool = True,
    is_union: bool = False,
) -> StmtTypeT:
    if len(columns) != len(values):
        raise ValueError("`columns` and `values` must have the same length")

    filters = []
    for column, value in zip(columns, values):
        column_attr = validate_column(table=table, column=column)
        if column_attr is None:
            if strict:
                raise AttributeError(
                    f"Invalid column '{column}' for table '{table.__tablename__}'"
                )
            continue
        if isinstance(value, list):
            filters.extend([column_attr == val for val in value])
        else:
            filters.append(column_attr == value)

    if filters:
        stmt = stmt.filter(or_(*filters) if is_union else and_(*filters))

    return stmt


def filter_ids(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    column: str,
    ids: OptListOfInts = None,
    include_null: bool = False,
    strict: bool = True,
) -> StmtTypeT:
    column_attr = validate_column(table=table, column=column)
    if column_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{column}' for table '{table.__tablename__}'"
            )
        return stmt

    id_filters = []
    if ids is not None:
        id_filters.extend([column_attr == id for id in ids])

    if id_filters:
        if include_null:
            id_filters.append(column_attr.is_(None))
        stmt = stmt.filter(or_(*id_filters))

    return stmt


def filter_timestamps(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    date_filters: Sequence[DateFilter],
) -> StmtTypeT:
    if date_filters:
        for date_filter in date_filters:
            try:
                sqla_table = table.__table__
                column = sqla_table.columns[date_filter.name]
                column_attr: InstrumentedAttribute = getattr(table, date_filter.name)
                if isinstance(column.type, (TIMESTAMP, DATE)):
                    if date_filter.from_date and date_filter.to_date:
                        stmt = stmt.filter(
                            column_attr.between(
                                date_filter.from_date, date_filter.to_date
                            )
                        )
                    elif date_filter.from_date:
                        stmt = stmt.filter(column_attr >= date_filter.from_date)
                    elif date_filter.to_date:
                        stmt = stmt.filter(column_attr <= date_filter.to_date)
            except KeyError:
                continue
    return stmt


def filter_statuses(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    column: str = "status",
    statuses: OptListOfDataStatuses = None,
    strict: bool = True,
) -> StmtTypeT:
    column_attr = validate_column(table=table, column=column)
    if column_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{column}' for table '{table.__tablename__}'"
            )
        return stmt
    if statuses is not None:
        status_filters = [column_attr == status for status in statuses]
        stmt = stmt.filter(or_(*status_filters))
    return stmt


def filter_is_root(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    parent_column: str = "parent_id",
    is_root: OptBool = None,
    strict: bool = True,
) -> StmtTypeT:
    parent_attr = validate_column(table=table, column=parent_column)
    if parent_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{parent_column}' for table '{table.__tablename__}'"
            )
        return stmt
    parent_attr = getattr(table, parent_column, None)
    if parent_attr is None or not isinstance(parent_attr, InstrumentedAttribute):
        return stmt
    if is_root is not None:
        stmt = stmt.filter(
            parent_attr.is_(None) if is_root else parent_attr.is_not(None)
        )
    return stmt


def filter_is_parent(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    id_column: str = "id",
    parent_column: str = "parent_id",
    is_parent: OptBool = None,
    strict: bool = True,
) -> StmtTypeT:
    id_attr = validate_column(table=table, column=id_column)
    if id_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{id_column}' for table '{table.__tablename__}'"
            )
        return stmt
    parent_attr = validate_column(table=table, column=parent_column)
    if parent_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{parent_column}' for table '{table.__tablename__}'"
            )
        return stmt
    if is_parent is not None:
        child_table = aliased(table)
        child_parent_attr = getattr(child_table, parent_column)
        subq = select(child_table).filter(child_parent_attr == id_attr).exists()
        stmt = stmt.filter(subq if is_parent else ~subq)
    return stmt


def filter_is_child(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    parent_column: str = "parent_id",
    is_child: OptBool = None,
    strict: bool = True,
) -> StmtTypeT:
    parent_attr = validate_column(table=table, column=parent_column)
    if parent_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{parent_column}' for table '{table.__tablename__}'"
            )
        return stmt
    if is_child is not None:
        stmt = stmt.filter(
            parent_attr.is_not(None) if is_child else parent_attr.is_(None)
        )
    return stmt


def filter_is_leaf(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    id_column: str = "id",
    parent_column: str = "parent_id",
    is_leaf: OptBool = None,
    strict: bool = True,
) -> StmtTypeT:
    id_attr = validate_column(table=table, column=id_column)
    if id_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{id_column}' for table '{table.__tablename__}'"
            )
        return stmt
    parent_attr = validate_column(table=table, column=parent_column)
    if parent_attr is None:
        if strict:
            raise AttributeError(
                f"Invalid column '{parent_column}' for table '{table.__tablename__}'"
            )
        return stmt
    if is_leaf is not None:
        child_table = aliased(table)
        child_parent_attr = getattr(child_table, parent_column)
        subq = select(child_table).filter(child_parent_attr == id_attr).exists()
        stmt = stmt.filter(~subq if is_leaf else subq)
    return stmt


def search(
    stmt: StmtTypeT,
    table: Type[DeclarativeBaseT],
    search: OptStr = None,
    columns: OptListOfStrs = None,
) -> StmtTypeT:
    if search is None:
        return stmt

    search_term = f"%{search}%"
    sqla_table = table.__table__
    search_filters = []

    for name, attr in vars(table).items():
        if not isinstance(attr, InstrumentedAttribute):
            continue

        try:
            column = sqla_table.columns[name]
        except KeyError:
            continue

        if columns is not None and name not in columns:
            continue

        if isinstance(column.type, (String, TEXT)):
            search_filters.append(cast(attr, TEXT).ilike(search_term))

    if search_filters:
        stmt = stmt.filter(or_(*search_filters))

    return stmt


def sort(
    stmt: Select[RowT],
    table: Type[DeclarativeBaseT],
    sort_columns: Sequence[SortColumn],
) -> Select[RowT]:
    for sort_column in sort_columns:
        try:
            sort_col = getattr(table, sort_column.name)
            sort_col = (
                asc(sort_col) if sort_column.order is Order.ASC else desc(sort_col)
            )
            stmt = stmt.order_by(sort_col)
        except AttributeError:
            continue
    return stmt


def paginate(stmt: Select[RowT], page: int, limit: int) -> Select[RowT]:
    offset: int = int((page - 1) * limit)
    stmt = stmt.limit(limit).offset(offset)
    return stmt
