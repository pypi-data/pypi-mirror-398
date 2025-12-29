# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Unit tests for the module log."""

# ruff: noqa: PLR2004

# Standard library
import logging
import re
from pathlib import Path

# Third party
import pytest

# Local
from elsabio import exceptions
from elsabio.config.log import LoggingConfig, LogHanderType, LogLevel, Stream
from elsabio.log import add_handlers, create_stream_handler, setup_logging

# ==================================================================================================
# Fixtures
# ==================================================================================================


@pytest.fixture
def logging_stderr_3_log_files(tmp_path: Path) -> LoggingConfig:
    r"""A logging configuration configured to log to stdout and 3 log files.

    The file logger named "cli" is disabled.
    """

    return LoggingConfig.model_validate(
        {
            'min_log_level': LogLevel.DEBUG,
            'format': r'%(asctime)s - %(levelname)s - %(message)s',
            'datetime_format': r'%m-%d %H:%M:%S',
            'stream': {
                'stdout': {
                    'stream': Stream.STDOUT,
                    'min_log_level': LogLevel.ERROR,
                },
            },
            'file': {
                'web': {
                    'path': tmp_path / 'web.log',
                    'min_log_level': LogLevel.WARNING,
                    'format': r'%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s',
                    'datetime_format': r'%a, %b %d %H:%M:%S',
                },
                'cli': {
                    'disabled': True,
                    'path': tmp_path / 'cli.log',
                    'min_log_level': LogLevel.DEBUG,
                },
                'api': {
                    'path': tmp_path / 'api.log',
                    'min_log_level': LogLevel.INFO,
                },
            },
        }
    )


def write_log_messages(logger: logging.Logger) -> None:
    r"""Write test log messages."""

    messages = (
        (logging.DEBUG, 'A debug message.'),
        (logging.INFO, 'An info message.'),
        (logging.WARNING, 'A warning message.'),
        (logging.ERROR, 'An error message.'),
        (logging.CRITICAL, 'A critical message.'),
    )
    for level, msg in messages:
        logger.log(level=level, msg=msg)


# ==================================================================================================
# Tests
# ==================================================================================================


class TestSetupLogging:
    r"""Tests for the function `setup_logging`."""

    def test_logging_disabled(self, caplog: pytest.LogCaptureFixture) -> None:
        r"""Test to disable logging completely."""

        # Setup
        # ===========================================================
        logger = setup_logging(config=LoggingConfig(disabled=True))

        # Exercise
        # ===========================================================
        write_log_messages(logger=logger)

        # Verify
        # ===========================================================
        assert len(caplog.record_tuples) == 0

        # Clean up - None
        # ===========================================================

    def test_logging_to_stdout_and_3_log_files(
        self, capsys: pytest.CaptureFixture, logging_stderr_3_log_files: LoggingConfig
    ) -> None:
        r"""Test logging to stdout and 3 log files."""

        # Setup
        # ===========================================================
        setup_logging(config=logging_stderr_3_log_files, logger=logging.getLogger())

        log_file_config = logging_stderr_3_log_files.file
        assert log_file_config is not None, 'log file configuration not found!'

        web_cfg = log_file_config['web']
        cli_cfg = log_file_config['cli']
        api_cfg = log_file_config['api']
        logger = logging.getLogger(__name__)

        # Exercise
        # ===========================================================
        write_log_messages(logger=logger)

        # Verify
        # ===========================================================

        # web log file
        # -----------------------------------------------------------
        assert web_cfg.path.exists(), f'web log file "{web_cfg.path}" does not exist!'
        log_file_lines = web_cfg.path.read_text().splitlines()

        assert len(log_file_lines) == 3, f'web log file "{web_cfg.path}" does not contain 3 lines!'

        for line, log_level in zip(log_file_lines, ('WARNING', 'ERROR', 'CRITICAL'), strict=True):
            assert log_level in line, f'{log_level} not in "{line}" ("{web_cfg.path}")'

        # cli log file (disabled)
        # -----------------------------------------------------------
        assert not cli_cfg.path.exists(), f'cli log file "{api_cfg.path}" exists!'

        # api log file
        # -----------------------------------------------------------
        assert api_cfg.path.exists(), f'api log file "{api_cfg.path}" does not exist!'
        log_file_lines = api_cfg.path.read_text().splitlines()

        assert len(log_file_lines) == 4, f'api log file "{api_cfg.path}" does not contain 4 lines!'

        for line, log_level in zip(
            log_file_lines, ('INFO', 'WARNING', 'ERROR', 'CRITICAL'), strict=True
        ):
            assert log_level in line, f'{log_level} not in "{line}" ("{api_cfg.path}")'

        # stdout
        # -----------------------------------------------------------
        captured = capsys.readouterr()
        log_file_lines = captured.out.splitlines()
        assert len(log_file_lines) == 2, 'stdout does not contain 2 lines!'

        for line, log_level in zip(log_file_lines, ('ERROR', 'CRITICAL'), strict=True):
            assert log_level in line, f'{log_level} not in "{line}" (stdout)'

        # Clean up - None
        # ===========================================================

    def test_exclude_enabled_loggers(
        self, capsys: pytest.CaptureFixture, logging_stderr_3_log_files: LoggingConfig
    ) -> None:
        r"""Test to exclude enabled loggers from being configured."""

        # Setup
        # ===========================================================
        setup_logging(
            config=logging_stderr_3_log_files,
            exclude={LogHanderType.FILE: ('web', 'api')},
        )

        log_file_config = logging_stderr_3_log_files.file
        assert log_file_config is not None, 'log file configuration not found!'

        web_cfg = log_file_config['web']
        cli_cfg = log_file_config['cli']
        api_cfg = log_file_config['api']
        logger = logging.getLogger(__name__)

        # Exercise
        # ===========================================================
        write_log_messages(logger=logger)

        # Verify
        # ===========================================================
        assert not web_cfg.path.exists(), f'web log file "{web_cfg.path}" exists!'
        assert not cli_cfg.path.exists(), f'cli log file "{cli_cfg.path}" exists!'
        assert not api_cfg.path.exists(), f'api log file "{api_cfg.path}" exists!'

        captured = capsys.readouterr()
        log_file_lines = captured.out.splitlines()
        assert len(log_file_lines) == 2, 'stout does not contain 2 lines!'

        for line, log_level in zip(log_file_lines, ('ERROR', 'CRITICAL'), strict=True):
            assert log_level in line, f'{log_level} not in "{line}" (stdout)'

        # Clean up - None
        # ===========================================================

    def test_log_formats(self, logging_stderr_3_log_files: LoggingConfig) -> None:
        r"""Test the configured log formats of different handlers."""

        # Setup
        # ===========================================================
        setup_logging(config=logging_stderr_3_log_files)

        log_file_config = logging_stderr_3_log_files.file
        assert log_file_config is not None, 'log file configuration not found!'

        web_cfg = log_file_config['web']
        api_cfg = log_file_config['api']
        logger = logging.getLogger(__name__)

        # Exercise
        # ===========================================================
        write_log_messages(logger=logger)

        # Verify
        # ===========================================================

        # web log file
        # -----------------------------------------------------------
        assert web_cfg.path.exists(), f'web log file "{web_cfg.path}" does not exist!'
        log_file_lines = web_cfg.path.read_text().splitlines()

        assert len(log_file_lines) == 3, f'web log file "{web_cfg.path}" does not contain 3 lines!'

        pattern_str = (
            r'^\w+, \w+ \d{2} \d{2}:\d{2}:\d{2} - tests.test_log - '
            r'(WARNING|ERROR|CRITICAL) - write_log_messages - [\w\s]+\.$'
        )
        pattern = re.compile(pattern_str)

        for line in log_file_lines:
            assert pattern.match(line) is not None, f'line "{line}" does not match "{pattern_str}"!'

        # api log file
        # -----------------------------------------------------------
        assert api_cfg.path.exists(), f'api log file "{api_cfg.path}" does not exist!'
        log_file_lines = api_cfg.path.read_text().splitlines()

        assert len(log_file_lines) == 4, f'api log file "{api_cfg.path}" does not contain 4 lines!'

        pattern_str = r'^\d{2}-\d{2} \d{2}:\d{2}:\d{2} - (INFO|WARNING|ERROR|CRITICAL) - [\w\s]+\.'
        pattern = re.compile(pattern_str)

        for line in log_file_lines:
            assert pattern.match(line) is not None, f'line "{line}" does not match "{pattern_str}"!'

        # Clean up - None
        # ===========================================================


class TestAddHandlers:
    r"""Tests for the function `add_handlers`."""

    @pytest.mark.raises
    def test_invalid_log_handler_type(self) -> None:
        r"""Test to supply an invalid log handler type."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        with pytest.raises(exceptions.ElSabioError) as exc_info:
            add_handlers(
                logger=logging.getLogger(),
                handler_type='invalid',  # type: ignore [arg-type]
                config={},
                exclude=None,
                default_format=None,
                default_datetime_format='',
            )

        # Verify
        # ===========================================================
        error_msg = exc_info.exconly()
        print(error_msg)

        assert 'invalid' in error_msg

        # Clean up - None
        # ===========================================================


class TestCreateStreamHandler:
    r"""Tests for the function `create_stream_handler`."""

    @pytest.mark.raises
    def test_invalid_stream(self) -> None:
        r"""Test to supply an invalid stream."""

        # Setup - None
        # ===========================================================

        # Exercise
        # ===========================================================
        with pytest.raises(exceptions.ElSabioError) as exc_info:
            create_stream_handler(stream='invalid')  # type: ignore [arg-type]

        # Verify
        # ===========================================================
        error_msg = exc_info.exconly()
        print(error_msg)

        assert 'invalid' in error_msg

        # Clean up - None
        # ===========================================================
