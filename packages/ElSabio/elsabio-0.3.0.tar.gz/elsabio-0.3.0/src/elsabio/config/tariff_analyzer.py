# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The Tariff Analyzer config models."""

# Standard library
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

# Third party
from pydantic import Field, ValidationInfo, field_validator

# Local
from elsabio.config.core import HOME_DIR, BaseConfigModel, ImportMethod, PluginConfig
from elsabio.datetime import parse_date_range_expression
from elsabio.exceptions import ElSabioError

TARIFF_ANALYZER_DIR = HOME_DIR / 'tariff_analyzer'
DEFAULT_DATA_DIR = TARIFF_ANALYZER_DIR / 'data'


class DataSource(StrEnum):
    r"""The available data sources of the Tariff Analyzer module."""

    PRODUCT = 'product'
    FACILITY = 'facility'
    FACILITY_CONTRACT = 'facility_contract'
    ACTIVE_ENERGY_CONS = 'active_energy_cons'
    ACTIVE_ENERGY_PROD = 'active_energy_prod'
    MAX_ACTIVE_POWER_CONS = 'max_active_power_cons'
    MAX_ACTIVE_POWER_PROD = 'max_active_power_prod'
    MAX_REACTIVE_POWER_CONS = 'max_reactive_power_cons'
    MAX_REACTIVE_POWER_PROD = 'max_reactive_power_prod'
    MAX_DEB_ACTIVE_POWER_CONS_HIGH_LOAD = 'max_deb_active_power_cons_high_load'
    MAX_DEB_ACTIVE_POWER_CONS_LOW_LOAD = 'max_deb_active_power_cons_low_load'


class DataSourceConfig(BaseConfigModel):
    r"""The configuration of an importable data source.

    Parameters
    ----------
    method : elsabio.config.ImportMethod
        The method for importing the data needed by Tariff Analyzer.

    path : pathlib.Path
        The path to the directory where data files to import are located if
        `method` is :attr:ImportMethod.FILE`, or the directory where the input
        data is temporarily saved before import if `method` is :attr:ImportMethod.PLUGIN`.

    interval : tuple[date, date | None] | None, default None
        The interval in which to import data if `method` is :attr:ImportMethod.PLUGIN`.

    plugin : elsabio.config.PluginConfig or None, default None
        The configuration of the plugin to use for importing data if `method` is
        :attr:ImportMethod.PLUGIN`.
    """

    method: ImportMethod
    path: Path
    interval: tuple[date, date | None] | None = None
    plugin: PluginConfig | None = Field(default=None, validate_default=True)

    @field_validator('path')
    @classmethod
    def validate_path(cls, path: Path) -> Path | None:
        r"""Validate the `path` attribute."""

        path = path.expanduser().resolve()

        if not path.exists():
            raise ValueError(f'The import path = "{path}" does not exist!')

        if not path.is_dir():
            raise ValueError(f'The import path = "{path}" is not a directory!')

        return path

    @field_validator('interval', mode='before')
    @classmethod
    def validate_interval(cls, interval: Any) -> tuple[date, date | None] | None:
        r"""Validate the plugin configuration."""

        if interval is None:
            return interval

        if isinstance(interval, str):
            try:
                start, end = parse_date_range_expression(expr=interval)
            except ElSabioError as e:
                raise ValueError(str(e)) from None

            return start.date(), end if end is None else end.date()

        raise ValueError(f'Invalid interval "{interval}"!')

    @field_validator('plugin')
    @classmethod
    def validate_plugin(cls, v: PluginConfig | None, info: ValidationInfo) -> PluginConfig | None:
        r"""Validate the plugin configuration."""

        method = info.data.get('method')

        if v is None:
            if method == ImportMethod.PLUGIN:
                raise ValueError(f'No plugin configuration found and method = "{method}"!')
        elif info.data.get('interval') is None:
            raise ValueError(f'No interval specified and method = "{method}"!')

        return v


class TariffAnalyzerConfig(BaseConfigModel):
    r"""The configuration of the Tariff Analyzer module.

    Parameters
    ----------
    enabled : bool, default True
        True if the Tariff Analyzer module is enabled and False otherwise.

    data_dir : pathlib.Path, default '~/.elsabio/tariff_analyzer/data'
        The path to the data directory of the Tariff Analyzer module
        where the imported meter data will reside.

    data : dict[elsabio.config.tariff_analyzer.DataSource, elsabio.config.tariff_analyzer.DataSourceConfig], default {}
        The data sources needed by Tariff Analyzer.
    """

    enabled: bool = True
    data_dir: Path = DEFAULT_DATA_DIR
    data: dict[DataSource, DataSourceConfig] = Field(default={})

    @field_validator('data_dir')
    @classmethod
    def validate_data_dir(cls, data_dir: Path) -> Path:
        r"""Validate the `data_dir` field."""

        data_dir = data_dir.expanduser().resolve()

        if data_dir == DEFAULT_DATA_DIR:
            return data_dir

        if not data_dir.exists():
            raise ValueError(f'The tariff_analyzer.data_dir = "{data_dir}" does not exist!')

        if not data_dir.is_dir():
            raise ValueError(f'tariff_analyzer.data_dir = "{data_dir}" must be a directory!')

        return data_dir
