# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The ConfigManager and the config loading functions."""

# Standard library
import os
import sys
import tomllib
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Third party
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

# Local
from elsabio import exceptions
from elsabio.config.core import (
    CONFIG_FILE_ENV_VAR,
    CONFIG_FILE_PATH,
    SECRETS_FILE_ENV_VAR,
    BitwardenPasswordlessConfig,
    DatabaseConfig,
    Language,
)
from elsabio.config.log import LoggingConfig
from elsabio.config.tariff_analyzer import TariffAnalyzerConfig


class ConfigManager(BaseSettings):
    r"""Handles the configuration of ElSabio.

    Parameters
    ----------
    config_file_path : pathlib.Path or None, default None
        The path to the config file from which the configuration was loaded.
        The special path '-' specifies that the config was loaded from stdin.
        If None the default configuration was loaded.

    timezone : zoneinfo.ZoneInfo, default zoneinfo.ZoneInfo('Europe/Stockholm')
        The timezone where the application is used.

    languages : tuple[elsabio.config.Language, ...], default (elsabio.config.Language.EN,)
        The languages to make available to the application. The default is English.

    default_language : elsabio.config.Language, default elsabio.config.Language.EN
        The default language to use when the application first loads. The default is English.

    database : elsabio.config.DatabaseConfig
        The database configuration.

    bwp : elsabio.config.BitwardenPasswordlessConfig
        The configuration for Bitwarden Passwordless.dev.

    tariff_analyzer : elsabio.config.TariffAnalyzerConfig
        The configuration for the Tariff Analyzer module.

    logging : elsabio.config.LoggingConfig
        The logging configuration.
    """

    model_config = SettingsConfigDict(frozen=True, env_prefix='elsabio_', env_nested_delimiter='__')

    config_file_path: Path | None = None
    timezone: ZoneInfo = Field(default=cast(ZoneInfo, None), validate_default=True)
    languages: tuple[Language, ...] = (Language.EN,)
    default_language: Language = Language.EN
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    bwp: BitwardenPasswordlessConfig
    tariff_analyzer: TariffAnalyzerConfig = Field(default_factory=TariffAnalyzerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    def __init__(self, **kwargs: Any) -> None:
        try:
            super().__init__(**kwargs)
        except ValidationError as e:
            raise exceptions.ConfigError(str(e)) from None
        except tomllib.TOMLDecodeError as e:  # Can be raised when parsing the secrets file.
            secrets_file = os.getenv(SECRETS_FILE_ENV_VAR)
            raise exceptions.ParseConfigError(
                f'Toml syntax error in secrets file : "{secrets_file}"!\n{e!s}'
            ) from None

    @staticmethod
    def get_secrets_file() -> Path | None:
        r"""Get the secrets file from the environment variable ELSABIO_SECRETS_FILE.

        Returns
        -------
        secrets_file : Path or None
            The path to the secrets file or None if the environment variable
            ELSABIO_SECRETS_FILE is not set.

        Raises
        ------
        elsabio.SecretsFileNotFoundError
            If the secrets file could not be found.

        elsabio.ParseConfigError
            If there are syntax errors in the secrets file.
        """

        _secrets_file = os.getenv(SECRETS_FILE_ENV_VAR)

        if _secrets_file is None:
            return _secrets_file

        secrets_file = Path(_secrets_file)

        if secrets_file.is_dir():
            error_msg = f'The secrets file "{secrets_file}" must be a file not a directory!'
            raise exceptions.SecretsFileNotFoundError(message=error_msg, data=secrets_file)

        if not secrets_file.exists():
            error_msg = f'The secrets file "{secrets_file}" does not exist!'
            raise exceptions.SecretsFileNotFoundError(message=error_msg, data=secrets_file)

        return secrets_file

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        r"""Customize the order in which settings are loaded.

        The order in which the options will override each other:
        1. Class constructor arguments.
        2. Environment variables.
        3. Environment variables loaded from dotenv files.
        4. Settings loaded from a secrets file.
        """

        secrets_settings = TomlConfigSettingsSource(
            settings_cls=settings_cls, toml_file=cls.get_secrets_file()
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            secrets_settings,
        )

    @field_validator('timezone', mode='before')
    @classmethod
    def validate_timezone(cls, v: Any) -> ZoneInfo:
        r"""Validate the timezone field and set the default value."""

        if isinstance(v, ZoneInfo):
            return v

        default = 'Europe/Stockholm'

        if v is None:
            key = default
        elif isinstance(v, str):
            key = v.strip() or default
        else:
            raise ValueError(
                f'Invalid timezone: "{v}". '
                f'Expected str or zoneinfo.ZoneInfo, got "{type(v).__name__}".'
            )

        try:
            return ZoneInfo(key)
        except ZoneInfoNotFoundError:
            raise ValueError(
                f'Failed to load timezone "{key}". Either the IANA timezone key is invalid '
                'or the system timezone database is missing. Install the tzdata package '
                'for your system or provide a valid timezone like "Europe/Stockholm".'
            ) from None


def _load_config_from_stdin() -> str:
    r"""Load the configuration from stdin."""

    content = ''

    if not sys.stdin.isatty():  # Content piped to stdin.
        for line in sys.stdin:
            content = f'{content}\n{line}'

    return content


def _load_config_from_file(path: Path) -> str:
    r"""Load the configuration from a config file."""

    content = ''

    if path.is_dir():
        error_msg = f'The config file "{path}" must be a file not a directory!'
        raise exceptions.ConfigFileNotFoundError(message=error_msg, data=path)

    if path == CONFIG_FILE_PATH:
        if path.exists():
            content = path.read_text()
    elif not path.exists():
        raise exceptions.ConfigFileNotFoundError(
            message=f'The config file "{path}" does not exist!', data=path
        )
    else:
        content = path.read_text()

    return content


def load_config(path: Path | None = None) -> ConfigManager:
    r"""Load the configuration of ElSabio.

    The configuration can be loaded from five different sources listed
    below in the order in which they will override each other:

    1. A specified config file to `path` parameter.

    2. From stdin by specifying the `path` `pathlib.Path('-')`.

    3. A config file specified in environment variable ELSABIO_CONFIG_FILE.

    4. From the default config file location "~/.config/ElSabio/ElSabio.toml".

    5. From the secrets file specified in environment variable ELSABIO_SECRETS_FILE.

    Parameters
    ----------
    path : pathlib.Path or None, default None
        The path to the config file. Specify `Path('-')` for stdin. If None the configuration
        will be loaded from the config file environment variable ELSABIO_CONFIG_FILE if it
        exists otherwise from the default config file at "~/.config/ElSabio/ElSabio.toml".
        If none of these sources exist stdin will be searched for configuration and if no
        configuration is found :exc:`elsabio.ConfigError` will be raised.

    Returns
    -------
    elsabio.config.ConfigManager
        An instance of the program's configuration.

    Raises
    ------
    elsabio.ConfigError
        If the configuration is invalid or if no configuration was found.

    elsabio.ConfigFileNotFoundError
        If the configuration file could not be found.

    elsabio.ParseConfigError
        If there are syntax errors in the config or secrets file.

    elsabio.SecretsFileNotFoundError
        If the secrets file could not be found when specified.
    """

    file_path: Path | None = None
    file_path_str = ''
    config_content = ''

    if path is None:
        if (_file_path := os.getenv(CONFIG_FILE_ENV_VAR)) is None:
            file_path = CONFIG_FILE_PATH
        else:
            file_path = Path(_file_path)
    elif path.name == '-':  # stdin
        file_path = None
    else:
        file_path = path

    if file_path is not None:
        config_content = _load_config_from_file(path=file_path)
        file_path_str = str(file_path)

    if not config_content:
        config_content = _load_config_from_stdin()
        file_path_str = '-'

    if not config_content:
        raise exceptions.ConfigError('No configuration found! Check your sources!')

    config_content = f"config_file_path = '{file_path_str}'\n{config_content}"

    try:
        config_from_toml = tomllib.loads(config_content)
    except (tomllib.TOMLDecodeError, TypeError) as e:
        error_msg = f'Syntax error in config : {e.args[0]}'
        raise exceptions.ParseConfigError(error_msg) from None

    return ConfigManager.model_validate(config_from_toml)
