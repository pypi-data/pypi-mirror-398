# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Unit tests for the module `elsabio.datetime`."""

# Standard library
from datetime import UTC, date, datetime, timedelta, timezone
from unittest.mock import Mock
from zoneinfo import ZoneInfo

# Third party
import pytest

# Local
import elsabio.datetime
from elsabio.datetime import (
    DEFAULT_TIMEZONE,
    DateRange,
    get_current_timestamp,
    parse_date_range_expression,
)
from elsabio.exceptions import ElSabioError


@pytest.fixture
def mocked_current_timestamp(monkeypatch: pytest.MonkeyPatch) -> tuple[date, Mock]:
    r"""Mock the current timestamp to a fixed value.

    Returns
    -------
    d : datetime.datetime
        The mocked current timestamp.

    m : unittest.mock.Mock
        The mock object that mocks the function :func:`elsabio.datetime.get_current_timestamp`.
    """

    d = datetime(2025, 10, 20, 13, 37, 37, tzinfo=ZoneInfo('Europe/Stockholm'))

    m = Mock(spec_set=get_current_timestamp, name='mocked_get_current_timestamp', return_value=d)
    monkeypatch.setattr(elsabio.datetime, 'get_current_timestamp', m)

    return d, m


@pytest.mark.usefixtures('mocked_current_timestamp')
class TestParseDateRangeExpression:
    r"""Tests for the function `parse_date_range_expression`.

    The current timestamp is mocked to 2025-10-20T13:37:37+02:00.
    """

    @pytest.mark.parametrize(
        ('expr', 'exp_value'),
        [
            pytest.param(
                'CY',
                (datetime(2025, 1, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE), None),
                id='CY',
            ),
            pytest.param(
                'CM',
                (datetime(2025, 10, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE), None),
                id='CM',
            ),
            pytest.param(
                'CD',
                (datetime(2025, 10, 20, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE), None),
                id='CD',
            ),
            pytest.param(
                'now',
                (datetime(2025, 10, 20, 13, 37, 37, tzinfo=DEFAULT_TIMEZONE), None),
                id='now',
            ),
            pytest.param(
                'CM..CM',
                (
                    datetime(2025, 10, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                    datetime(2025, 10, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                ),
                id='CM..CM',
            ),
            pytest.param(
                'CM-1M..CM+1M',
                (
                    datetime(2025, 9, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                    datetime(2025, 11, 1, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                ),
                id='CM-1M..CM+1M',
            ),
            pytest.param(
                'CM+1D..CD+1h',
                (
                    datetime(2025, 10, 2, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                    datetime(2025, 10, 20, 1, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                ),
                id='CM+1D..CD+1h',
            ),
            pytest.param(
                'now-1s..now+1min',
                (
                    datetime(2025, 10, 20, 13, 37, 36, tzinfo=DEFAULT_TIMEZONE),
                    datetime(2025, 10, 20, 13, 38, 37, tzinfo=DEFAULT_TIMEZONE),
                ),
                id='now-1s..now+1min',
            ),
            pytest.param(
                '2025-11-29',
                (datetime(2025, 11, 29, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE), None),
                id='2025-11-29',
            ),
            pytest.param(
                '2025-11-29T20:10',
                (datetime(2025, 11, 29, 20, 10, 0, tzinfo=DEFAULT_TIMEZONE), None),
                id='2025-11-29T20:10',
            ),
            pytest.param(
                '2025-11-29 20:10:14',
                (datetime(2025, 11, 29, 20, 10, 14, tzinfo=DEFAULT_TIMEZONE), None),
                id='2025-11-29 20:10:14',
            ),
            pytest.param(
                '2025-11-29T20:11:15Z',
                (datetime(2025, 11, 29, 20, 11, 15, tzinfo=UTC), None),
                id='2025-11-29T20:11:15Z',
            ),
            pytest.param(
                '2025-11-29..2025-11-30T14:35:24+01:00',
                (
                    datetime(2025, 11, 29, 0, 0, 0, tzinfo=DEFAULT_TIMEZONE),
                    datetime(2025, 11, 30, 14, 35, 24, tzinfo=timezone(timedelta(seconds=3600))),
                ),
                id='2025-11-29..2025-11-30T14:35:24+01:00',
            ),
        ],
    )
    def test_parse_date_range_expression(self, expr: str, exp_value: DateRange) -> None:
        r"""Test to parse valid range expressions."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        result = parse_date_range_expression(expr=expr)

        # Verify
        # ===========================================================
        print(f'Result:\n{result}\n\nExpected Result:\n{exp_value}')

        assert result == exp_value

        # Clean up - None
        # ===========================================================

    @pytest.mark.raises
    @pytest.mark.parametrize(
        ('expr', 'exp_msg'),
        [
            pytest.param(
                'X',
                '"X" is not a valid relative or iso-formatted datetime!',
                id='X',
            ),
            pytest.param(
                'CX/b..CM+1D',
                '"CX/b" is not a valid relative or iso-formatted datetime!',
                id='CX/b..CM+1D',
            ),
            pytest.param(
                'CM-1M..CM+1D..CM',
                'Invalid date range expression: "CM-1M..CM+1D..CM"!',
                id='CM-1M..CM+1D..CM',
            ),
            pytest.param(
                'CM-1h..CM-2h',
                'end (2025-09-30 22:00:00+02:00) must be >= to start (2025-09-30 23:00:00+02:00)!',
                id='CM-1h..CM-2h',
            ),
            pytest.param(
                '2025-2-2',
                '"2025-2-2" is not a valid relative or iso-formatted datetime!',
                id='2025-2-2',
            ),
            pytest.param(
                '2025/02/12 13.12',
                '"2025/02/12 13.12" is not a valid relative or iso-formatted datetime!',
                id='2025/02/12 13.12',
            ),
        ],
    )
    def test_invalid_range_expression(self, expr: str, exp_msg: DateRange) -> None:
        r"""Test to parse invalid date range expressions."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        with pytest.raises(ElSabioError) as exc_info:
            parse_date_range_expression(expr=expr)

        # Verify
        # ===========================================================
        error_msg = exc_info.value.args[0]
        print(exc_info.exconly())

        assert error_msg == exp_msg

        # Clean up - None
        # ===========================================================
