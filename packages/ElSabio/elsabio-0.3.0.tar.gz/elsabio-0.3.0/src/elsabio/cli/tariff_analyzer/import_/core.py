# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core functionality for the sub-command `import` of the Tariff Analyzer module."""

# Standard library
import logging
from collections.abc import Callable, Sequence
from pathlib import Path

# Third party
import duckdb
import pandas as pd

# Local
from elsabio.cli.core import Color, echo_with_log
from elsabio.cli.display import display_dataframe
from elsabio.config import ImportMethod
from elsabio.core import OperationResult
from elsabio.operations.file import move_files, read_parquet

type ValidationFunction = Callable[[duckdb.DuckDBPyRelation], tuple[OperationResult, pd.DataFrame]]


def format_list_of_files(files: Sequence[Path]) -> str:
    r"""Format a list of files as an enumerated string of filenames.

    Parameters
    ----------
    files: Sequence[pathlib.Path]
        The files to format.

    Returns
    -------
    output : str
        The formatted string of filenames.
    """

    output = ''

    nr_files = len(files)

    for idx, f in enumerate(files, start=1):
        output += f'{idx:0>{nr_files}}. {f.name}'

    return output


def move_processed_files(source_dir: Path, error: bool = False) -> OperationResult:
    r"""Move the processed files to a sub-directory.

    Parameters
    ----------
    source_dir : pathlib.Path
        The source directory where the files to move are located.

    error : bool, default False
        True if the files should be moved the error sub-directory and False for the
        success sub-directory.

    Returns
    -------
    result : elsabio.core.OperationResult
        The result of moving the files in `source_dir`.
    """

    target_dir = source_dir / ('error' if error else 'success')
    files, result = move_files(
        source_dir=source_dir, target_dir=target_dir, prepend_move_datetime=True
    )
    if result.ok:
        result = OperationResult(
            ok=True,
            short_msg=f'Moved input files to "{target_dir}":\n{format_list_of_files(files)}\n',
        )
    else:
        result = OperationResult(ok=False, short_msg=result.short_msg)

    return result


def load_data_model_to_import(
    method: ImportMethod, path: Path, conn: duckdb.DuckDBPyConnection
) -> tuple[duckdb.DuckDBPyRelation, OperationResult]:
    r"""Load the data model to import.

    Parameters
    ----------
    method : elsabio.config.ImportMethod
        The import method to use for loading the data.
        Import through :attr:`ImportMethod.PLUGIN` is not implemented yet.

    path : pathlib.Path
        The path to the directory where data files to import are located if
        `method` is :attr:ImportMethod.FILE`, or the directory where the input
        data is temporarily saved before import if `method` is :attr:`ImportMethod.PLUGIN`.

    conn : duckdb.DuckDBPyConnection
        An open DuckDB connection to use for loading the data.

    Returns
    -------
    rel : duckdb.DuckDBPyRelation
        The loaded dataset.

    result : elsabio.core.OperationResult
        The result of loading the data.
    """

    if method == ImportMethod.FILE:
        return read_parquet(path=path, conn=conn)

    if method == ImportMethod.PLUGIN:
        result = OperationResult(
            ok=False, short_msg='Data import through plugins is not implemented yet!'
        )
        return conn.sql('SELECT NULL'), result

    # Guard for possible future import methods
    result = OperationResult(  # type: ignore[unreachable]
        ok=False,
        short_msg=(
            f'Invalid import method "{method}"! '
            f'Valid methods are: {tuple(str(m) for m in ImportMethod)}'
        ),
    )

    return conn.sql('SELECT NULL'), result


def validate_import_model(model: duckdb.DuckDBPyRelation, func: ValidationFunction) -> bool:
    r"""Validate the import data model.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model to validate.

    func : Callable[[duckdb.DuckDBPyRelation], tuple[OperationResult, pd.DataFrame]]
        The validation function to execute.

    Returns
    -------
    bool
        True if `model` is valid and False otherwise.
    """

    result, df_invalid = func(model)

    if not result.ok:
        echo_with_log(
            message=f'{result.short_msg}\n{display_dataframe(df_invalid, as_str=True)}\n',
            log_level=logging.ERROR,
            color=Color.ERROR,
        )
        return False

    return True
