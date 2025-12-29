# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core functionality of the CLI."""

# Standard library
import logging
from enum import StrEnum
from typing import NoReturn

# Third party
import click

# Local
from elsabio.config import ConfigManager
from elsabio.database import SessionFactory
from elsabio.exceptions import ElSabioError

logger = logging.getLogger(__name__)


class Obj(StrEnum):
    r"""The available keys of the context object."""

    CONFIG = 'config'
    SESSION_FACTORY = 'session_factory'


class Color(StrEnum):
    r"""Terminal colors."""

    SUCCESS = 'green'
    WARNING = 'yellow'
    ERROR = 'red'


def exit_program(
    error: bool,
    ctx: click.Context | None = None,
    message: str | None = None,
    color: Color | None = None,
) -> NoReturn:
    """Exit the program with an exit code and an optional message.

    Parameters
    ----------
    error : bool
        True if an error occurred and the exit code will
        be 1 and False for success and the exit code 0.

    ctx : click.Context or None, default None
        The context of the program. If None the program will exit with
        :exc:`SystemExit` instead of :func:`click.Context.exit`.

    message : str or None, default None
        An optional message to print before exiting. If None no message is printed.

    color : elsabio.cli.Color or None, default None
        If specified it will override the default color of the `message`, which is
        red for error and green for success.
    """

    if error:
        exit_code = 1
        _color = Color.ERROR if color is None else color
        log_level = logging.ERROR
    else:
        exit_code = 0
        _color = Color.SUCCESS if color is None else color
        log_level = logging.INFO

    if message:
        click.secho(message=message, fg=_color)
        logger.log(level=log_level, msg=message)

    if ctx is not None:
        ctx.exit(code=exit_code)
    else:
        raise SystemExit(exit_code)


def echo_with_log(message: str, log_level: int = logging.INFO, color: Color | None = None) -> None:
    """Echo a message to the terminal and write it as a log statement.

    Parameters
    ----------
    log_level : int, default logging.INFO
        The log level to use.

    color : elsabio.cli.Color or None, default None
        The terminal foreground color to use for the terminal message.
    """

    click.secho(message=message, fg=color)
    logger.log(level=log_level, msg=message)


def load_resources(ctx: click.Context) -> tuple[ConfigManager, SessionFactory]:
    r"""Load the resources of the program.

    Parameters
    ----------
    ctx : click.Context
        The context of the program.

    Returns
    -------
    cm : elsabio.config.ConfigManager
        The configuration of the program.

    session_factory : elsabio.db.SessionFactory
        The session factory that can produce new database sessions.

    Raises
    ------
    elsabio.ElSabioError
        If the configuration or the session factory were not found in the context of the program.
    """

    cm: ConfigManager | None = ctx.obj.get(Obj.CONFIG)
    if cm is None:
        raise ElSabioError('The configuration was not found in the context of the program!')

    session_factory: SessionFactory | None = ctx.obj.get(Obj.SESSION_FACTORY)
    if session_factory is None:
        raise ElSabioError('The session_factory was not found in the context of the program!')

    return cm, session_factory
