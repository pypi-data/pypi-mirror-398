# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The configuration of ElSabio."""

from elsabio.config.config import ConfigManager, load_config
from elsabio.config.core import (
    BITWARDEN_PASSWORDLESS_API_URL,
    CONFIG_DIR,
    CONFIG_FILE_ENV_VAR,
    CONFIG_FILE_PATH,
    CONFIG_FILENAME,
    HOME_DIR,
    PROG_NAME,
    SECRETS_FILE_ENV_VAR,
    BaseConfigModel,
    BitwardenPasswordlessConfig,
    DatabaseConfig,
    ImportMethod,
    Language,
    PluginConfig,
    PluginType,
)
from elsabio.config.log import (
    LOGGING_DEFAULT_DATETIME_FORMAT,
    LOGGING_DEFAULT_DIR,
    LOGGING_DEFAULT_FILE_PATH,
    LOGGING_DEFAULT_FILENAME,
    LOGGING_DEFAULT_FORMAT,
    LOGGING_DEFAULT_FORMAT_DEBUG,
    EmailLogHandler,
    FileLogHandler,
    LoggingConfig,
    LogHanderType,
    LogHandler,
    LogLevel,
    Stream,
    StreamLogHandler,
)
from elsabio.config.tariff_analyzer import TariffAnalyzerConfig

# The Public API
__all__ = [
    # config
    'ConfigManager',
    'load_config',
    # core
    'BITWARDEN_PASSWORDLESS_API_URL',
    'CONFIG_DIR',
    'CONFIG_FILE_ENV_VAR',
    'CONFIG_FILE_PATH',
    'CONFIG_FILENAME',
    'HOME_DIR',
    'PROG_NAME',
    'SECRETS_FILE_ENV_VAR',
    'BaseConfigModel',
    'BitwardenPasswordlessConfig',
    'DatabaseConfig',
    'ImportMethod',
    'Language',
    'PluginConfig',
    'PluginType',
    # log
    'LOGGING_DEFAULT_DATETIME_FORMAT',
    'LOGGING_DEFAULT_DIR',
    'LOGGING_DEFAULT_FILE_PATH',
    'LOGGING_DEFAULT_FILENAME',
    'LOGGING_DEFAULT_FORMAT',
    'LOGGING_DEFAULT_FORMAT_DEBUG',
    'EmailLogHandler',
    'FileLogHandler',
    'LoggingConfig',
    'LogHanderType',
    'LogHandler',
    'LogLevel',
    'Stream',
    'StreamLogHandler',
    # tariff_analyzer
    'TariffAnalyzerConfig',
]
