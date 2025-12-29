# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The exception hierarchy of ElSabio."""

# Standard library
from typing import Any


class ElSabioError(Exception):
    r"""The base Exception of ElSabio.

    Parameters
    ----------
    message : str
        The error message.

    data : Any, default None
        Optional extra data to include in the exception.
    """

    def __init__(self, message: str, data: Any = None) -> None:
        self.message = message
        self.data = data
        super().__init__(message)


class ConfigError(ElSabioError):
    r"""Errors related to the configuration of ElSabio."""


class ConfigFileNotFoundError(ConfigError):
    r"""If the config file cannot be found."""


class ParseConfigError(ConfigError):
    r"""If the config or secrets file cannot be parsed correctly."""


class SecretsFileNotFoundError(ConfigError):
    r"""If the secrets file cannot be found."""


class PluginError(ElSabioError):
    r"""Errors related to working with plugins to ElSabio."""
