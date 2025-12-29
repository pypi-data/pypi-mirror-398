# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Configure the logging for ElSabio."""

# Standard Library
import logging
import sys
from collections.abc import Callable, Mapping, Sequence
from logging.handlers import RotatingFileHandler, SMTPHandler
from pathlib import Path
from typing import Any

# Local
from elsabio import exceptions
from elsabio.config import (
    LoggingConfig,
    LogHanderType,
    LogHandler,
    Stream,
)

type CreateLogHandlerFunc = Callable[..., logging.Handler]


def create_stream_handler(stream: Stream, **_kwargs: Any) -> logging.StreamHandler:
    r"""Create a stream log handler.

    Parameters
    ----------
    stream : elsabio.config.Stream
        The stream to send log messages to.

    **_kwargs : Any
        Additional key-word arguments that are not used by the function.

    Returns
    -------
    logging.StreamHandler
        The configured stream handler.

    Raises
    ------
    elsabio.ElSabioError
        If a an invalid `stream` is supplied.
    """

    streams = {Stream.STDOUT: sys.stdout, Stream.STDERR: sys.stderr}
    selected_stream = streams.get(stream)

    if selected_stream is None:
        raise exceptions.ElSabioError(
            f'{stream=} is not a valid option! Valid streams are : {tuple(streams.keys())}'
        )

    return logging.StreamHandler(stream=selected_stream)


def create_file_handler(
    path: Path,
    max_bytes: int = 1_000_000,
    backup_count: int = 4,
    mode: str = 'a',
    encoding: str = 'UTF-8',
    **_kwargs: Any,
) -> RotatingFileHandler:
    r"""Create a log file handler.

    Parameters
    ----------
    path : pathlib.Path
        The full path to the log file.

    max_bytes : int, default 1_000_000
        The maximum size [Bytes] of the log file before rotating to a new file.

    backup_count : int, default 4
        The number of backups of rotated log files to keep.

    mode : str, default 'a'
        The mode to use when writing to the log file.
        The default of 'a' means to append to the file.

    encoding : str, default 'UTF-8'
        The character encoding of the log file.

    **_kwargs : Any
        Additional key-word arguments that are not used by the function.

    Returns
    -------
    logging.handlers.RotatingFileHandler
        The configured file handler.
    """

    return RotatingFileHandler(
        filename=path,
        mode=mode,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding,
    )


def create_email_handler(
    host: str,
    from_address: str,
    to_addresses: list[str],
    subject: str,
    port: int = 25,
    timeout: int = 5,
    **_kwargs: Any,
) -> SMTPHandler:
    r"""Create an email log handler.

    Parameters
    ----------
    host : str
        The host of the email server.

    from_address : str
        The email address from which to send the log messages.

    to_addresses : list[str]
        The email addresses that will receive the log messages.

    subject : str
        The subject of the email containing the log messages.

    port : int, default 25
        The port of the email server.

    timeout : int, default 5
        The number of seconds to wait until a timeout is reached
        if the email server does not respond.

    **_kwargs : Any
        Additional key-word arguments that are not used by the function.

    Returns
    -------
    logging.handlers.SMTPHandler
        The configured email handler.
    """

    return SMTPHandler(
        mailhost=(host, port),
        fromaddr=from_address,
        toaddrs=to_addresses,
        subject=subject,
        timeout=timeout,
    )


def add_handlers(
    logger: logging.Logger,
    handler_type: LogHanderType,
    config: Mapping[str, LogHandler] | None,
    exclude: Sequence[str] | None,
    default_format: str | None,
    default_datetime_format: str,
) -> None:
    r"""Add handlers to a logger.

    Parameters
    ----------
    logger : logging.Logger
        The logger for which to add log handlers.

    handler_type : elsabio.config.LogHanderType
        The type of handlers to add.

    config : dict[str, elsabio.config.LogHandler] or None
        The configuration of the handlers to add. The keys are the names of the log handlers.
        If None no handlers are added.

    exclude : Sequence[str] or None
        The names of the log handlers to exclude from being added to `logger`.
        The names should correspond to the keys of `config`. If None no log
        handlers are excluded.

    default_format : str or None
        The default log format to assign to a handler if no
        format has been specified for a handler.

    default_datetime_format : str
        The default log datetime format to assign to a handler if no datetime format
        has been specified for a handler.

    Returns
    -------
    None

    Raises
    ------
    elsabio.ElSabioError
        If a `handler_type` without a "create handler function" is supplied.
    """

    if config is None:
        return

    handler_funcs: dict[LogHanderType, CreateLogHandlerFunc] = {
        LogHanderType.STREAM: create_stream_handler,
        LogHanderType.FILE: create_file_handler,
        LogHanderType.EMAIL: create_email_handler,
    }

    func = handler_funcs.get(handler_type)
    if func is None:
        error_msg = (
            f'LogHandlerType "{handler_type}" has no create log handler function!\n'
            f'Supported log handlers: {tuple(handler_funcs.keys())}'
        )
        raise exceptions.ElSabioError(error_msg)

    _exclude = {} if exclude is None else set(exclude)

    for name, cfg in config.items():
        if name in _exclude or cfg.disabled:
            continue

        handler = func(**cfg.model_dump())
        handler.setLevel(cfg.min_log_level)

        fmt = cfg.format if 'format' in cfg.model_fields_set else default_format
        dfmt = (
            cfg.datetime_format
            if 'datetime_format' in cfg.model_fields_set
            else default_datetime_format
        )
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=dfmt))

        logger.addHandler(handler)


def setup_logging(
    config: LoggingConfig,
    logger: logging.Logger | None = None,
    exclude: dict[LogHanderType, Sequence[str]] | None = None,
) -> logging.Logger:
    r"""Setup and configure a logger.

    Parameters
    ----------
    config : elsabio.config.LoggingConfig
        The logging configuration.

    logger : logging.Logger or None, default None
        The logger to configure. If not specified the root logger is configured.

    exclude : dict[elsabio.config.LogHanderType, Sequence[str]] or None
        The names of the log handlers per log handler type to exclude from being added to `logger`.

    Returns
    -------
    logger : logging.Logger
        The configured logger.
    """

    logger = logging.getLogger() if logger is None else logger

    if config.disabled:
        logger.setLevel(logging.CRITICAL + 1)  # Disable logging completely.
        return logger

    logger.setLevel(config.min_log_level)

    exclude = {} if exclude is None else exclude

    handlers = (
        (LogHanderType.STREAM, config.stream),
        (LogHanderType.FILE, config.file),
        (LogHanderType.EMAIL, config.email),
    )
    for handler_type, handler_config in handlers:
        add_handlers(
            logger=logger,
            handler_type=handler_type,
            config=handler_config,
            exclude=exclude.get(handler_type),
            default_format=config.format,
            default_datetime_format=config.datetime_format,
        )

    return logger
