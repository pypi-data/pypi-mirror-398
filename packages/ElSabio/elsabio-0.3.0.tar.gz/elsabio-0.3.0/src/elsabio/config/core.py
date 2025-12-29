# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core config models."""

# Standard library
from enum import StrEnum
from pathlib import Path
from typing import Any

# Third party
import streamlit_passwordless as stp
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
)

# Local
from elsabio import exceptions
from elsabio.database import URL, SQLAlchemyError, make_url

PROG_NAME = 'ElSabio'

HOME_DIR = Path.home() / '.elsabio'

CONFIG_DIR = Path.home() / '.config' / PROG_NAME

CONFIG_FILENAME = f'{PROG_NAME}.toml'

CONFIG_FILE_PATH = CONFIG_DIR / CONFIG_FILENAME

CONFIG_FILE_ENV_VAR = 'ELSABIO_CONFIG_FILE'

SECRETS_FILE_ENV_VAR = 'ELSABIO_SECRETS_FILE'

BITWARDEN_PASSWORDLESS_API_URL = stp.BITWARDEN_PASSWORDLESS_API_URL


class Language(StrEnum):
    r"""The available languages of ElSabio.

    Uses ISO 639 two letter abbreviations.
    """

    EN = 'en'
    SV = 'sv'


class ImportMethod(StrEnum):
    r"""The available data import methods."""

    PLUGIN = 'plugin'
    FILE = 'file'


class PluginType(StrEnum):
    r"""The available types of plugins."""

    SQLALCHEMY = 'sqlalchemy'
    GENERIC = 'generic'


class BaseConfigModel(BaseModel):
    r"""The base model that all configuration models inherit from."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            super().__init__(**kwargs)
        except ValidationError as e:
            raise exceptions.ConfigError(str(e)) from None


class PluginConfig(BaseConfigModel):  # type: ignore [no-redef]
    r"""The configuration of a plugin.

    Parameters
    ----------
    name : str
        The name of the plugin.

    type : elsabio.config.PluginType, default elsabio.config.PluginType.GENERIC
        The type of plugin.

    kwargs : dict[str, Any], default {}
        The keyword arguments to pass along to the plugin.
    """

    name: str
    type: PluginType = PluginType.GENERIC
    kwargs: dict[str, Any] = Field(default_factory=dict)

    @field_validator('kwargs')
    @classmethod
    def validate_kwargs(cls, v: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        r"""Validate the keyword arguments to the plugin."""

        if info.data.get('type') != PluginType.SQLALCHEMY:
            return v

        if 'db_url' not in v:
            raise ValueError(
                f'Missing required kwarg "db_url" for SQLAlchemy plugin with name "{info.data["name"]}"!'
            )

        try:
            v['db_url'] = make_url(v['db_url'])
        except SQLAlchemyError as e:
            raise ValueError(f'{type(e).__name__} : {e!s}') from None

        return v


class DatabaseConfig(BaseConfigModel):
    r"""The database configuration for ElSabio.

    Parameters
    ----------
    url : str or sqlalchemy.URL, default 'sqlite:///ElSabio.db'
        The SQLAlchemy database url of the ElSabio database.

    autoflush : bool, default False
        Automatically flush pending changes within the session
        to the database before executing new SQL statements.

    expire_on_commit : bool, default False
        If True make the connection between the models and the database expire
        after a transaction within a session has been committed and if False make
        the database models accessible after the commit.

    create_database : bool, default True
        If True the database table schema will be created if it does not exist.

    connect_args : dict[Any, Any], default dict()
        Additional arguments sent to the database driver upon
        connection that further customizes the connection.

    engine_config : dict[str, Any], default dict()
        Additional keyword arguments passed to the :func:`sqlalchemy.create_engine` function.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    url: str | URL = Field(default='sqlite:///ElSabio.db', validate_default=True)
    autoflush: bool = False
    expire_on_commit: bool = False
    create_database: bool = True
    connect_args: dict[Any, Any] = Field(default_factory=dict)
    engine_config: dict[str, Any] = Field(default_factory=dict)

    @field_validator('url')
    @classmethod
    def validate_url(cls, url: str | URL) -> URL:
        r"""Validate the database url."""

        try:
            return make_url(url)
        except SQLAlchemyError as e:
            raise ValueError(f'{type(e).__name__} : {e!s}') from None


class BitwardenPasswordlessConfig(BaseConfigModel):
    r"""The configuration for Bitwarden Passwordless.dev.

    Bitwarden Passwordless.dev handles the passkey registration and authentication.

    Parameters
    ----------
    public_key : str
         The public key of the Bitwarden Passwordless.dev backend API.

    private_key : str
         The private key of the Bitwarden Passwordless.dev backend API.

    url : pydantic.AnyHttpUrl or str, default default 'https://v4.passwordless.dev'
        The base url of the backend API of Bitwarden Passwordless.dev. Specify this url
        if you are self-hosting Bitwarden Passwordless.dev.
    """

    public_key: str
    private_key: str
    url: AnyHttpUrl = stp.BITWARDEN_PASSWORDLESS_API_URL
