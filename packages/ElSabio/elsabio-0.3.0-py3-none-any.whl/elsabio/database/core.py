# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core database functionality."""

# Standard library
import logging
from collections.abc import Mapping, Sequence
from typing import Any, cast

# Third party
import pandas as pd
from sqlalchemy import URL as URL
from sqlalchemy import make_url as make_url
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.selectable import Select
from streamlit_passwordless.database import Session as Session
from streamlit_passwordless.database import SessionFactory as SessionFactory
from streamlit_passwordless.database import create_default_roles as create_default_roles
from streamlit_passwordless.database import create_session_factory as create_session_factory

# Local
from elsabio.core import OperationResult, has_required_columns
from elsabio.database.models.core.models import Base
from elsabio.models.core import DtypeMapping

type SQLQuery = str | Select | TextClause

logger = logging.getLogger(__name__)


def commit(session: Session, error_msg: str = 'Error committing transaction!') -> OperationResult:
    r"""Commit a database transaction.

    session : elsabio.db.Session
        An active database session.

    error_msg : str, default 'Error committing transaction!'
        An error message to add if an exception is raised when committing the transaction.

    Returns
    -------
    result : elsabio.OperationResult
        The result of committing the transaction.
    """

    try:
        session.commit()
    except SQLAlchemyError as e:
        long_msg = f'{error_msg}\n{e!s}'
        logger.exception(long_msg)
        result = OperationResult(
            ok=False,
            short_msg=error_msg,
            long_msg=long_msg,
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
        session.rollback()
    else:
        result = OperationResult(ok=True)

    return result


def load_sql_query_as_dataframe(
    query: SQLQuery,
    session: Session,
    dtypes: DtypeMapping,
    parse_dates: list[str] | None = None,
    error_msg: str = '',
) -> tuple[pd.DataFrame, OperationResult]:
    r"""Load the result of a SQL query into a :class:`pandas.DataFrame`.

    Parameters
    ----------
    query : elsabio.db.SQLQuery
        The SQL query to execute.

    session : elsabio.db.Session
        An active database session.

    dtypes : elsabio.models.DtypeMapping
        The datatypes of the columns of the `query`.

    parse_dates : list[str] or None, default None
        The columns to parse as datetime columns.

    error_msg : str, default ''
        An optional error message to include if an exception is raised when executing the query.

    Returns
    -------
    df : pandas.DataFrame
        The loaded dataset.

    result : elsabio.core.OperationResult
        The result of loading the dataset from the database.
    """

    try:
        df = pd.read_sql_query(
            sql=query,
            con=session.get_bind(),
            dtype=dtypes,
            parse_dates=parse_dates,
            dtype_backend='pyarrow',
        )
    except SQLAlchemyError as e:
        long_msg = f'{error_msg}\n{e!s}' if error_msg else str(e)
        logger.exception(long_msg)
        result = OperationResult(
            ok=False,
            short_msg=error_msg,
            long_msg=long_msg,
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
        df = pd.DataFrame()
    else:
        result = OperationResult(ok=True)

    return df, result


def bulk_insert_to_table(
    session: Session,
    table: str,
    df: pd.DataFrame,
    index: bool = False,
    required_cols: set[str] | None = None,
) -> OperationResult:
    r"""Bulk insert a DataFrame into a table.

    Parameters
    ----------
    session : elsabio.db.Session
        An open session to the database.

    table : str
        The name of the table to insert into.

    df : pandas.DataFrame
        The dataset to insert into `table`.

    index : bool, default False
        True if the index column(s) of the DataFrame should be included.

    required_cols : set[str] or None, default None
        The required columns that must exist in `df`. If None column validation is omitted.

    Returns
    -------
    result : elsabio.core.OperationResult
        The result of inserting the data into the database.
    """

    if required_cols:
        result = has_required_columns(cols=set(df.columns), required_cols=required_cols)
        if not result.ok:
            return result

    try:
        df.to_sql(name=table, con=session.get_bind(), if_exists='append', index=index)
    except SQLAlchemyError as e:
        short_msg = f'Unable to save DataFrame to table "{table}"'
        long_msg = f'{short_msg}!\n{e!s}'
        logger.exception(long_msg)
        result = OperationResult(
            ok=False,
            short_msg=short_msg,
            long_msg=long_msg,
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
    else:
        result = OperationResult(ok=True)

    return result


def bulk_update_table[T: Base](
    session: Session, model: type[T], df: pd.DataFrame, required_cols: set[str] | None = None
) -> OperationResult:
    r"""Bulk update a table by primary key from the contents of a DataFrame.

    Parameters
    ----------
    session : elsabio.db.Session
        An open session to the database.

    model : elsabio.database.models.Base
        The SQLALchemy ORM model representing the database table to update.
        Should be a subclass of :class:`elsabio.db.models.Base`.

    df : pandas.DataFrame
        The dataset to use for updating `model`. Note that the primary key of `model`
        must exist for every row in `df` since the update is done by primary key.

    required_cols : set[str] or None, default None
        The required columns that must exist in `df`. If None column validation is omitted.

    Returns
    -------
    elsabio.core.OperationResult
        The result of updating the existing records in the database.
    """

    if required_cols:
        result = has_required_columns(cols=set(df.columns), required_cols=required_cols)
        if not result.ok:
            return result

    records = cast(Sequence[Mapping[str, Any]], df.to_dict(orient='records'))

    try:
        session.execute(update(model), records)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        short_msg = f'Unable to update table {model.__tablename__}!'
        long_msg = f'{short_msg}!\n{e!s}'
        logger.exception(long_msg)
        result = OperationResult(
            ok=False,
            short_msg=short_msg,
            long_msg=long_msg,
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
    else:
        result = OperationResult(ok=True)

    return result
