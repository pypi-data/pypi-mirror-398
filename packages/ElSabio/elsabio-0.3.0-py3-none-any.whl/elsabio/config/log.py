# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The logging configuration of ElSabio."""

# Standard library
from enum import StrEnum
from pathlib import Path
from typing import Annotated
from uuid import uuid4

# Third party
from pydantic import (
    AfterValidator,
    Field,
    ValidationInfo,
    field_validator,
)

# Local
from elsabio.config.core import PROG_NAME, BaseConfigModel

LOGGING_DEFAULT_DIR = Path.home() / 'logs' / 'ElSabio'

LOGGING_DEFAULT_FILENAME = f'{PROG_NAME}.log'

LOGGING_DEFAULT_FILE_PATH = LOGGING_DEFAULT_DIR / LOGGING_DEFAULT_FILENAME

LOGGING_DEFAULT_FORMAT = r'%(asctime)s|%(name)s|%(levelname)s|%(message)s'

LOGGING_DEFAULT_FORMAT_DEBUG = (
    r'%(asctime)s|%(name)s|%(levelname)s|%(funcName)s|Line:%(lineno)s|%(message)s'
)

LOGGING_DEFAULT_DATETIME_FORMAT = r'%Y-%m-%dT%H:%M:%S'

# ==================================================================================================
# Enums
# ==================================================================================================


class LogLevel(StrEnum):
    r"""The available log levels."""

    NOTSET = 'NOTSET'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class Stream(StrEnum):
    r"""The available input and output streams."""

    STDIN = 'stdin'
    STDOUT = 'stdout'
    STDERR = 'stderr'


class LogHanderType(StrEnum):
    r"""The available types of log handlers."""

    STREAM = 'stream'
    FILE = 'file'
    EMAIL = 'email'


# ==================================================================================================
# Validators
# ==================================================================================================


def set_format_based_on_log_level(_format: str | None, info: ValidationInfo) -> str:
    r"""Set the default format based on the log level."""

    if _format is not None:
        return _format

    if info.data.get('min_log_level') == LogLevel.DEBUG:
        return LOGGING_DEFAULT_FORMAT_DEBUG

    return LOGGING_DEFAULT_FORMAT


LogFormatBasedOnLogLevel = Annotated[str | None, AfterValidator(set_format_based_on_log_level)]


# ==================================================================================================
# Models
# ==================================================================================================


class LogHandler(BaseConfigModel):
    r"""The base model of a log handler.

    A log handler handles the log messages produced by the program.

    Parameters
    ----------
    disabled : bool, default False
        True if the log handler should be disabled and False to keep it active.

    min_log_level : elsabio.config.LogLevel, default elsabio.config.LogLevel.INFO
        The minimum log level sent to the log handler.

    format : str or None, default None
        The format string of the log message.
        See https://docs.python.org/3/library/logging.html#logrecord-attributes
        for a syntax reference. If None the default log format is used.

    datetime_format : str, default elsabio.config.LOGGING_DEFAULT_DATETIME_FORMAT
        The format string of the logging timestamp.
        Uses :func:`time.strftime` syntax. See https://docs.python.org/3/library/time.html#time.strftime
        for a syntax reference.
    """

    disabled: bool = False
    min_log_level: LogLevel = LogLevel.INFO
    format: LogFormatBasedOnLogLevel = Field(default=None, validate_default=True)
    datetime_format: str = LOGGING_DEFAULT_DATETIME_FORMAT


class StreamLogHandler(LogHandler):
    r"""The stream log handler logs messages to an output stream.

    Parameters
    ----------
    stream : elsabio.config.Stream, default elsabio.config.Stream.STDOUT
        The output stream to send the log messages to.
    """

    stream: Stream = Stream.STDOUT


class FileLogHandler(LogHandler):
    r"""The file log handler logs messages to a log file.

    Parameters
    ----------
    unique : bool, default False
        If True a unique log file will be created by prepending
        a uuid to the log filename of `path`.

    path : pathlib.Path, default "~/logs/ElSabio/ElSabio.log"
        The path to the log file.

    max_bytes : int default 1_000_000
        The maximum size in bytes of the log file before it gets rotated to a new file.

    backup_count : int default 4
        The number of backups of old log files that have been rotated to keep around.

    mode : str, default 'a'
        The mode to use for writing to the log file. The default 'a' appends to the file.

    encoding : str, default 'UTF-8'
        The character encoding to use for the log file.

    disabled : bool, default False
        True if the log handler should be disabled and False to keep it active.

    min_log_level : elsabio.LogLevel, default elsabio.config.LogLevel.INFO
        The minimum log level sent to the log handler.

    format : str or None, default None
        The format string of the log message.
        See https://docs.python.org/3/library/logging.html#logrecord-attributes
        for a syntax reference. If None the default log format is used.

    datetime_format : str, default elsabio.config.LOGGING_DEFAULT_DATETIME_FORMAT
        The format string of the logging timestamp.
        Uses :func:`time.strftime` syntax. See https://docs.python.org/3/library/time.html#time.strftime
        for a syntax reference.
    """

    unique: bool = False
    path: Path = Field(default=LOGGING_DEFAULT_FILE_PATH, validate_default=True)
    max_bytes: int = Field(default=1_000_000, ge=0)
    backup_count: int = Field(default=4, ge=0)
    mode: str = 'a'
    encoding: str = 'UTF-8'

    @field_validator('path')
    @classmethod
    def set_path(cls, path: Path, info: ValidationInfo) -> Path:
        r"""Set the `path` field and create the log directory if needed."""

        if path.is_dir():
            path = path / LOGGING_DEFAULT_FILENAME

        if info.data['unique'] is True:
            path = path.with_name(f'{uuid4()}_{path.name}')

        path = path.expanduser().resolve()
        path.parent.mkdir(exist_ok=True, parents=True)

        return path


class EmailLogHandler(LogHandler):
    r"""The email log handler sends emails with log messages.

    Parameters
    ----------
    host : str
        The email host.

    port : int, default 25
        The port the email host listens to.

    subject : str, default 'ElSabio'
        The subject of the email.

    from_address : str
        The address from which to send the email log messages.

    to_addresses : list[str]
        The email addresses to send the log messages to.

    timeout : int, default 5
        The maximum number of seconds to wait before aborting sending an email.

    disabled : bool, default True
        True if the log handler should be disabled and False to keep it active.

    min_log_level : elsabio.config.LogLevel, default elsabio.config.LogLevel.INFO
        The minimum log level sent to the log handler.

    format : str or None, default None
        The format string of the log message.
        See https://docs.python.org/3/library/logging.html#logrecord-attributes
        for a syntax reference. If None the default log format is used.

    datetime_format : str, default elsabio.config.LOGGING_DEFAULT_DATETIME_FORMAT
        The format string of the logging timestamp.
        Uses :func:`time.strftime` syntax. See https://docs.python.org/3/library/time.html#time.strftime
        for a syntax reference.
    """

    host: str
    port: int = 25
    subject: str = 'ElSabio'
    from_address: str
    to_addresses: list[str]
    timeout: int = Field(5, ge=0)
    disabled: bool = True
    min_log_level: LogLevel = LogLevel.WARNING


class LoggingConfig(BaseConfigModel):
    r"""The logging configuration of ElSabio.

    Parameters
    ----------
    disabled : bool, default False
        True if all log handlers should be disabled and False otherwise.

    min_log_level : elsabio.LogLevel, default elsabio.LogLevel.INFO
        The minimum log level sent to the log handlers. Used as a fallback
        if a minimum log level is not set on a log handler.

    format : str, default elsabio.config.LOGGING_DEFAULT_FORMAT.
        The format string of the log message. If specified it will apply to all log handlers
        where a format string has not been explicitly defined.
        See https://docs.python.org/3/library/logging.html#logrecord-attributes
        for a syntax reference.

    datetime_format : str, default elsabio.config.LOGGING_DEFAULT_DATETIME_FORMAT
        The format string of the logging timestamp. If specified it will apply to all log
        handlers where a datetime format string has not been explicitly defined.
        Uses :func:`time.strftime` syntax. See https://docs.python.org/3/library/time.html#time.strftime
        for a syntax reference.

    stream : dict[str, elsabio.config.StreamLogHandler] or None, default None
        The configuration of the stream log handlers.
        Each key corresponds to a stream log handler section in the config file.
        If None no stream log handler is added.

    file : dict[str, elsabio.config.FileLogHandler] or None, default None
        The configuration of the file log handlers.
        Each key corresponds to a log file section in the config file.
        If None no file log handler is added.

    email : dict[str, elsabio.config.EmailLogHandler] or None, default None
        The configuration of the email log handler.
        Each key corresponds to an email section in the config file.
        If None no email log handler is added.
    """

    disabled: bool = False
    min_log_level: LogLevel = LogLevel.INFO
    format: LogFormatBasedOnLogLevel = Field(default=None, validate_default=True)
    datetime_format: str = LOGGING_DEFAULT_DATETIME_FORMAT
    stream: dict[str, StreamLogHandler] | None = None
    file: dict[str, FileLogHandler] | None = None
    email: dict[str, EmailLogHandler] | None = None
