# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Operations for working with files."""

# Standard library
import os
from pathlib import Path

# Third party
import duckdb

# Local
from elsabio.core import OperationResult
from elsabio.datetime import get_current_timestamp


def read_parquet(
    path: Path, conn: duckdb.DuckDBPyConnection | None = None
) -> tuple[duckdb.DuckDBPyRelation, OperationResult]:
    r"""Load the contents of parquet file(s).

    Parameters
    ----------
    path : pathlib.Path
        The path to the parquet file or directory of parquet files.

    conn : duckdb.DuckDBPyConnection or None, default None
        The DuckDB connection to use for querying the parquet file(s).
        If None the global DuckDB in-memory database is used.

    Returns
    -------
    rel : duckdb.DuckDBPyRelation
        The DuckDB relation object of the dataset from the parquet file.

    result : elsabio.core.OperationResult
        The result of loading the parquet files.
    """

    if not path.exists():
        result = OperationResult(
            ok=False, short_msg=f'The parquet file path "{path}" does not exist!'
        )
        rel = duckdb.sql('SELECT NULL')
        return rel, result

    pattern = str(path / '*.parquet') if path.is_dir() else str(path)
    _conn = duckdb if conn is None else conn

    try:
        rel = _conn.read_parquet(pattern)
    except (duckdb.IOException, duckdb.InvalidInputException) as e:
        result = OperationResult(
            ok=False,
            short_msg=str(e),
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
        rel = duckdb.sql('SELECT NULL')
    else:
        result = OperationResult(ok=True)

    return rel, result


def write_parquet(
    rel: duckdb.DuckDBPyRelation,
    path: Path | str,
    partition_by: list[str] | None = None,
    overwrite: bool = False,
    row_group_size: int | None = None,
) -> OperationResult:
    r"""Write the contents of a DuckDB relation object to a parquet file.

    Parameters
    ----------
    rel : duckdb.DuckDBPyRelation
        The relation object of the data model to write to the parquet file.

    path : pathlib.Path
        The path to the parquet file or directory root of a parquet hive partition.

    partition_by : list[str] or None, default None
        The columns to partition the data by.

    overwrite : bool, default False
        True if files that already exist in the parquet hive should be allowed to
        be overwritten and False otherwise. Used in conjunction with `partition_by`.

    row_group_size : int or None, default None
        The number of rows to write into each row group.
        If None, the default of 122880 rows per group is used.
    """

    try:
        rel.to_parquet(
            file_name=str(path),
            partition_by=partition_by,
            overwrite=overwrite,
            row_group_size=row_group_size,
        )
    except duckdb.IOException as e:
        result = OperationResult(
            ok=False,
            short_msg=str(e),
            code=f'{e.__module__}.{e.__class__.__name__}',
        )
        rel = duckdb.sql('SELECT NULL')
    else:
        result = OperationResult(ok=True)

    return result


def move_files(
    source_dir: Path, target_dir: Path, prepend_move_datetime: bool = False
) -> tuple[list[Path], OperationResult]:
    r"""Move the files in `source_dir` to `target_dir`.

    Parameters
    ----------
    source_dir : pathlib.Path
        The source directory where the files to move are located.

    target_dir : pathlib.Path
        The target directory where to move the files.

    prepend_move_datetime : bool, default False
        True if a the current timestamp should be prepended to the filename when
        moved to `target_dir` and False to preserve the original filename as is.

    Returns
    -------
    files : list[pathlib.Path]
        The files in `source_dir` that were moved to `target_dir`.

    result : elsabio.core.OperationResult
        The result of moving the files in `source_dir` to `target_dir`.
    """

    files = []
    errors = []

    for item in source_dir.iterdir():
        if item.is_dir():
            continue

        if prepend_move_datetime:
            move_datetime = get_current_timestamp().strftime(r'%Y-%m-%dT%H.%M.%S%z')
            target_filename = f'{move_datetime}_{item.name}'
        else:
            target_filename = item.name

        target_file = target_dir / target_filename
        files.append(item)

        try:
            os.renames(item, target_file)
        except (PermissionError, OSError) as e:
            errors.append(f'Unable to move "{item}" to "{target_dir}"!\n{e!s}')
            result = OperationResult(ok=False, short_msg=str(e), code=e.__class__.__name__)

    if errors:
        result = OperationResult(ok=False, short_msg='\n'.join(e for e in errors))
    else:
        result = OperationResult(ok=True)

    return files, result
