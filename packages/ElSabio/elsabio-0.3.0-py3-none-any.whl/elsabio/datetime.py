# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Date and time functionality of ElSabio."""

# Standard library
import re
from datetime import datetime
from typing import NamedTuple
from zoneinfo import ZoneInfo

# Third party
import pandas as pd

# Local
from elsabio.exceptions import ElSabioError

DEFAULT_TIMEZONE = ZoneInfo('Europe/Stockholm')
RELATIVE_DATETIME_PATTERN = re.compile(
    r'(?P<base>now|CY|CM|CD)(?P<operator>[+-])?(?P<quantifier>\d+)?(?P<period>[YMDhms])?'
)

type DateRange = tuple[datetime, datetime | None]


class RelativeDatePointExpression(NamedTuple):
    r"""A relative date point expression.

    Parameters
    ----------
    datetime : datetime.datetime
        The timestamp of the expression.

    has_offset : bool
        True if the expression has a timedelta offset and False otherwise.

    operator : str or None, default None
        The operator (+, -) of the timedelta offset or None if no offset exists.

    quantifier : int or None, default None
        The numeric quantifier to apply to the offset or None if no offset exists.

    period : str or None, default None
        The time period of the offset or None if no offset exists.
    """

    datetime: datetime
    has_offset: bool
    operator: str | None = None
    quantifier: int | None = None
    period: str | None = None


def get_current_timestamp(tz: ZoneInfo | None = None) -> datetime:
    r"""Get the current timestamp in specified timezone.

    Parameters
    ----------
    tz : zoneinfo.ZoneInfo or None, default None
        The timezone of the current timestamp. If None timezone Europe/Stockholm is used.

    Returns
    -------
    datetime.datetime
        The current timestamp in the timezone of `tz`.
    """

    return datetime.now(tz=DEFAULT_TIMEZONE if tz is None else tz)


def relative_date_point_expression_to_datetime(date_point: RelativeDatePointExpression) -> datetime:
    r"""Convert a date point expression into a timestamp value.

    Parameters
    ----------
    elsabio.datetime.RelativeDatePointExpression
        The relative date point expression to convert into a timestamp value.

    Returns
    -------
    datetime.datetime
        The converted timestamp value.
    """

    match date_point.period:
        case 'Y':  # Year
            pd_period = 'YS'
        case 'M':  # Start of Month
            pd_period = 'MS'
        case 'D':  # Day
            pd_period = 'D'
        case 'h':  # Hour
            pd_period = 'h'
        case 'm':  # Minute
            pd_period = 'min'
        case 's':  # Second
            pd_period = 's'
        case _:
            raise ElSabioError(f'Invalid period selector "{date_point.period}"!')

    date_range = pd.date_range(
        start=date_point.datetime,
        periods=2,
        freq=f'{date_point.operator}{date_point.quantifier}{pd_period}',
    )
    return date_range[1]


def parse_relative_datetime_expression(
    expr: str, now: datetime
) -> RelativeDatePointExpression | None:
    r"""Parse a relative datetime expression.

    Parameters
    ----------
    point : str
        The relative date point expression to parse.

    now : datetime.datetime
        The current timestamp.

    Returns
    -------
    elsabio.datetime.DatePointExpression or None
        The parsed relative date point expression or None if the
        expression did not match the relative date point pattern.
    """

    m = RELATIVE_DATETIME_PATTERN.search(expr)
    if m is None:
        return None

    base = m.group('base')
    if base is None:
        raise ElSabioError('Group "base" is missing from relative date point expression!')

    dt = now if base == 'now' else now.replace(hour=0, minute=0, second=0, microsecond=0)

    if base == 'CY':
        dt = dt.replace(month=1, day=1)
    elif base == 'CM':
        dt = dt.replace(day=1)

    if (quantifier := m.group('quantifier')) is not None:
        quantifier = int(quantifier)

    operator = m.group('operator')
    period = m.group('period')

    if quantifier is None and operator is None and period is None:
        has_offset = False
    elif quantifier and operator and period:
        has_offset = True
    else:
        raise ElSabioError(f'"{expr}" is not a valid relative date point expression')

    return RelativeDatePointExpression(
        datetime=dt,
        has_offset=has_offset,
        operator=m.group('operator'),
        quantifier=quantifier,
        period=m.group('period'),
    )


def parse_datetime_expression(expr: str, now: datetime) -> datetime:
    r"""Parse a datetime expression.

    Parameters
    ----------
    expr : str
        The datetime expression to parse.

    now : datetime.datetime
        The current timestamp.

    Returns
    -------
    datetime.datetime
        The parsed relative or absolute datetime expression.

    Raises
    ------
    elsabio.ElSabioError
        If an invalid datetime expression is supplied.
    """

    if (point := parse_relative_datetime_expression(expr=expr, now=now)) is not None:
        if point.has_offset:
            value = relative_date_point_expression_to_datetime(date_point=point)
        else:
            value = point.datetime

        return value

    try:
        value = datetime.fromisoformat(expr)
    except ValueError:
        raise ElSabioError(f'"{expr}" is not a valid relative or iso-formatted datetime!') from None

    return value.astimezone(tz=now.tzinfo) if value.tzinfo is None else value


def parse_date_range_expression(expr: str) -> DateRange:
    r"""Parse a relative or an absolute iso-formatted date range expression.

    Examples of relative expressions:

    - CY : Start of the current year.
    - CM : Start of the current month.
    - CM-1M..CM+1M : Start of previous month until the start of next month.
    - CD+1h..CD+6h : One hour past midnight today until 6 AM this morning.
    - now-1s..now+1min : One second ago until one minute from now.

    Parameters
    ----------
    expr : str
        The date range expression to parse.

    Returns
    -------
    start : datetime.datetime
        The start timestamp of the date range.

    end : datetime.datetime
        The end timestamp of the date range or None if there is no end of the range.

    Raises
    ------
    elsabio.ElSabioError
        If an invalid datetime expression is supplied.
    """

    date_range = expr.split('..')
    now = get_current_timestamp()

    if (len_date_range := len(date_range)) == 1:
        start = parse_datetime_expression(expr=date_range[0], now=now)
        end = None

    elif len_date_range == 2:  # noqa: PLR2004
        start = parse_datetime_expression(expr=date_range[0], now=now)
        end = parse_datetime_expression(expr=date_range[1], now=now)

        if end < start:
            raise ElSabioError(f'end ({end}) must be >= to start ({start})!')

    else:
        raise ElSabioError(f'Invalid date range expression: "{expr}"!')

    return start, end
