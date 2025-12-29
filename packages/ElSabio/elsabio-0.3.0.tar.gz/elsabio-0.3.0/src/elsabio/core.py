# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core functionality of the package."""

# Standard library
from typing import NamedTuple


class OperationResult(NamedTuple):
    r"""The result of a function or method call.

    Should be returned from a function or method call to provide
    context weather the operation was successful or not.

    Parameters
    ----------
    ok : bool, default True
        True if the operation was successful and False otherwise.

    short_msg : str, default ''
        A short optional message that describes the reason for the result.
        Safe to display to the user.

    long_msg : str, default ''
        An longer message that further describes the result. May contain
        sensitive information and should not be displayed to the user.

    code : str or None, default None
        An optional machine-friendly code to better understand the result.
    """

    ok: bool = True
    short_msg: str = ''
    long_msg: str = ''
    code: str | None = None


def has_required_columns(cols: set[str], required_cols: set[str]) -> OperationResult:
    r"""Check if the supplied columns contain the required columns.

    Parameters
    ----------
    cols : set[str]
        The columns to analyze.

    required_cols : set[str]
        The columns that must exist in `cols`.

    Returns
    -------
    result : elsabio.core.OperationResult
        The result of the validation.
    """

    if missing_cols := required_cols.difference(cols):
        error_msg = (
            'Missing the required columns!\n'
            f'Missing required columns : {tuple(sorted(missing_cols))}\n'
            f'Required columns         : {tuple(sorted(required_cols))}\n'
            f'Available columns        : {tuple(sorted(cols))}'
        )
        result = OperationResult(ok=False, short_msg=error_msg, long_msg=error_msg)
    else:
        result = OperationResult(ok=True)

    return result
