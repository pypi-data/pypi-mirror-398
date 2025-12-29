# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""ElSabio - The Simple Electricity Meter Data Analysis Platform

ElSabio ("el sabio" means "the wise" in Spanish) helps you unlock insights hidden in your
electricity meter data. Use it to understand your grid and customers better to ultimately
make smarter decisions.
"""

# Local
from elsabio import database as db
from elsabio.app import APP_PATH
from elsabio.core import OperationResult
from elsabio.exceptions import (
    ConfigError,
    ConfigFileNotFoundError,
    ElSabioError,
    ParseConfigError,
    PluginError,
    SecretsFileNotFoundError,
)
from elsabio.metadata import (
    __releasedate__,
    __version__,
    __versiontuple__,
)

# The Public API
__all__ = [
    # app
    'APP_PATH',
    # core
    'OperationResult',
    # database
    'db',
    # exceptions
    'ConfigError',
    'ConfigFileNotFoundError',
    'ElSabioError',
    'ParseConfigError',
    'PluginError',
    'SecretsFileNotFoundError',
    # metadata
    '__releasedate__',
    '__version__',
    '__versiontuple__',
]
