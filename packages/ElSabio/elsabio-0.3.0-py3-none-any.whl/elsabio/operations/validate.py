# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Validation of data models."""

# Standard library
from collections.abc import Sequence
from typing import Literal

# Third party
import duckdb
import pandas as pd

# Local
from elsabio.core import OperationResult

type SortOrder = Literal['ASC', 'DESC']


def validate_missing_values(
    model: duckdb.DuckDBPyRelation,
    cols: Sequence[str],
    order_by: Sequence[tuple[str, SortOrder]] | None = None,
    index_cols: str | Sequence[str] | None = None,
    date_as_object: bool = True,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Validate a data model for missing values.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model to check for missing values.

    cols : Sequence[str]
        The columns of `model` to check for missing values.

    order_by : Sequence[tuple[str, Literal['ASC', 'DESC']]] or None, default None
        The columns to use for ordering the DataFrame containing rows with missing values.
        Specify as a tuple of column name, order by expression ('ASC' or 'DESC').

    index_cols : str or Sequence[str] or None, default None
        The columns to assign as the index columns of the validation DataFrame.

    date_as_object : bool, default True
        True if date columns should be kept as date objects and False to convert
        to a datetime column.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df_missing : pandas.DataFrame
        A DataFrame containing the rows with missing values in required `cols`.
        An empty DataFrame is returned if the data is valid.
    """

    cols_select_str = ''
    filter_clause = ''

    for col in cols:
        cols_select_str = f'{cols_select_str}, {col}'
        filter_clause = f'{filter_clause} OR {col} IS NULL'

    cols_select_str = cols_select_str[2:]  # Remove leading ", "
    filter_clause = filter_clause[4:]  # Remove leading " OR "

    rel = model.select(cols_select_str).filter(filter_clause)

    if order_by:
        order = ', '.join(f'{c} {asc_desc}' for c, asc_desc in order_by)
        rel = rel.order(order)

    df_invalid = rel.to_df(date_as_object=date_as_object).set_index(index_cols)

    if (nr_invalid := df_invalid.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=(
                f'Found rows ({nr_invalid}) with missing values in required columns {tuple(cols)}!'
            ),
        )
        return result, df_invalid

    return OperationResult(ok=True), pd.DataFrame()


def validate_duplicate_rows(
    model: duckdb.DuckDBPyRelation,
    cols: Sequence[str] | None = None,
    count_colname: str = 'nr_duplicates',
    exclude_rows_with_nulls: Sequence[str] | None = None,
    order_by: Sequence[tuple[str, SortOrder]] | None = None,
    index_cols: str | Sequence[str] | None = None,
    date_as_object: bool = True,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Validate a data model for duplicate rows.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model to check for duplicate rows.

    cols : Sequence[str] or None, default None
        The columns of `model` that together define a unique row.

    exclude_rows_with_nulls : Sequence[str] or None, default None
        The columns in which to exclude NULL values when counting duplicates.
        If None NULL exclusion is omitted.

    count_colname : str, default 'nr_duplicates'
        The name of the column with the count of duplicates.

    order_by : Sequence[tuple[str, Literal['ASC', 'DESC']]] or None, default None
        The columns to use for ordering the DataFrame containing the duplicate rows.
        Specify as a tuple of column name, order by expression ('ASC' or 'DESC').

    index_cols : str or Sequence[str] or None, default None
        The columns to assign as the index columns of the validation DataFrame.

    date_as_object : bool, default True
        True if date columns should be kept as date objects and False to convert
        to a datetime column.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df : pandas.DataFrame
        The DataFrame containing the duplicate rows.
        An empty DataFrame is returned if the data is valid.
    """

    cols = cols if cols else model.columns
    select_str = ', '.join(c for c in cols)
    select_str = f'{select_str}\n, COUNT(*) AS {count_colname}'

    rel_name = 'rel'

    query = f"""\
SELECT
    {select_str}

FROM {rel_name}

GROUP BY ALL

HAVING COUNT(*) > 1
"""  # noqa: S608

    rel = model.query(virtual_table_name=rel_name, sql_query=query)

    if exclude_rows_with_nulls:
        rel = rel.filter('OR '.join(f'{c} IS NOT NULL' for c in exclude_rows_with_nulls))

    if order_by:
        order = ', '.join(f'{c} {asc_desc}' for c, asc_desc in order_by)
        rel = rel.order(order)

    df = rel.to_df(date_as_object=date_as_object).set_index(index_cols)

    if (nr_invalid := df.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=(f'Found duplicate rows ({nr_invalid}) over columns: {tuple(cols)}!'),
        )
        return result, df

    return OperationResult(ok=True), pd.DataFrame()


def validate_at_start_of_month(
    model: duckdb.DuckDBPyRelation,
    date_col: str,
    display_cols: Sequence[str] | None = None,
    order_by: Sequence[tuple[str, SortOrder]] | None = None,
    index_cols: str | Sequence[str] | None = None,
    date_as_object: bool = True,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Check that the date column `date_col` is at the start of a month.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model to validate that all date values are at the start of a month.

    date_col : str
        The name of the date column to validate.

    display_cols : Sequence[str] or None, default None
        The columns of `model` to include in the validation DataFrame `df_invalid`.
        If None all columns of `model` are included.

    order_by : Sequence[tuple[str, Literal['ASC', 'DESC']]] or None, default None
        The columns to use for ordering the validation DataFrame.
        Specify as a tuple of column name, order by expression ('ASC' or 'DESC').

    index_cols : str or Sequence[str] or None, default None
        The columns to assign as the index columns of the validation DataFrame.

    date_as_object : bool, default True
        True if the date column `date_col` entries should be kept as date objects
        and False to convert to a datetime column.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df_invalid : pandas.DataFrame
        A DataFrame containing the rows with dates not a the start of a month.
        An empty DataFrame is returned if the data is valid.
    """

    rel = model.select(', '.join(c for c in display_cols)) if display_cols else model
    rel = rel.filter(f'day({date_col}) != 1')

    if order_by:
        order = ', '.join(f'{c} {asc_desc}' for c, asc_desc in order_by)
        rel = rel.order(order)

    df_invalid = rel.to_df(date_as_object=date_as_object).set_index(index_cols)

    if (nr_invalid := df_invalid.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=f'Found rows ({nr_invalid}) not at start of month!',
        )
        return result, df_invalid

    return OperationResult(ok=True), pd.DataFrame()
