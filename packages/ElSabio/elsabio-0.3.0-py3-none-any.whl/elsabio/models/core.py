# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core data models of ElSabio."""

# Standard library
from collections.abc import Hashable, Mapping
from enum import StrEnum
from typing import Any, ClassVar

# Third party
import pandas as pd
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, ValidationError
from streamlit_passwordless import User as User

# Local
from elsabio.exceptions import ElSabioError

type DtypeMapping = Mapping[Hashable, str]
type ColumnList = list[str]


class SerieTypeEnum(StrEnum):
    r"""The available meter data serie types.

    Members
    -------
    ACTIVE_ENERGY_CONS
        Active energy consumption.

    ACTIVE_ENERGY_PROD
        Active energy production.

    REACTIVE_ENERGY_CONS
        Reactive energy consumption.

    REACTIVE_ENERGY_PROD
        Reactive energy production.

    APPARENT_ENERGY_CONS
        Apparent energy consumption.

    APPARENT_ENERGY_PROD
        Apparent energy production.

    ACTIVE_POWER_CONS
        Active power consumption.

    ACTIVE_POWER_PROD
        Active power production.

    REACTIVE_POWER_CONS
        Reactive power consumption.

    REACTIVE_POWER_PROD
        Reactive power production.

    APPARENT_POWER_CONS
        Apparent power consumption.

    APPARENT_POWER_PROD
        Apparent power production.

    MAX_ACTIVE_POWER_CONS
        Maximum active power consumption.

    MAX_ACTIVE_POWER_PROD
        Maximum active power production.

    MAX_REACTIVE_POWER_CONS
        Maximum reactive power consumption.

    MAX_REACTIVE_POWER_PROD
        Maximum reactive power production.

    MAX_APPARENT_POWER_CONS
        Maximum apparent power consumption.

    MAX_APPARENT_POWER_PROD
        Maximum apparent power production.

    MAX_DEB_ACTIVE_POWER_CONS_HIGH_LOAD
        Maximum debitable active power consumption during the high load period.

    MAX_DEB_ACTIVE_POWER_CONS_LOW_LOAD
        Maximum debitable active power consumption during the low load period.
    """

    ACTIVE_ENERGY_CONS = 'active_energy_cons'
    ACTIVE_ENERGY_PROD = 'active_energy_prod'
    REACTIVE_ENERGY_CONS = 'reactive_energy_cons'
    REACTIVE_ENERGY_PROD = 'reactive_energy_prod'
    APPARENT_ENERGY_CONS = 'apparent_energy_cons'
    APPARENT_ENERGY_PROD = 'apparent_energy_prod'

    ACTIVE_POWER_CONS = 'active_power_cons'
    ACTIVE_POWER_PROD = 'active_power_prod'
    REACTIVE_POWER_CONS = 'reactive_power_cons'
    REACTIVE_POWER_PROD = 'reactive_power_prod'
    APPARENT_POWER_CONS = 'apparent_power_cons'
    APPARENT_POWER_PROD = 'apparent_power_prod'

    MAX_ACTIVE_POWER_CONS = 'max_active_power_cons'
    MAX_ACTIVE_POWER_PROD = 'max_active_power_prod'
    MAX_REACTIVE_POWER_CONS = 'max_reactive_power_cons'
    MAX_REACTIVE_POWER_PROD = 'max_reactive_power_prod'
    MAX_APPARENT_POWER_CONS = 'max_apparent_power_cons'
    MAX_APPARENT_POWER_PROD = 'max_apparent_power_prod'

    MAX_DEB_ACTIVE_POWER_CONS_HIGH_LOAD = 'max_deb_active_power_cons_high_load'
    MAX_DEB_ACTIVE_POWER_CONS_LOW_LOAD = 'max_deb_active_power_cons_low_load'


class BaseModel(PydanticBaseModel):
    r"""The BaseModel that all models inherit from."""

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, frozen=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            super().__init__(**kwargs)
        except ValidationError as e:
            raise ElSabioError(str(e)) from None


class BaseDataFrameModel(BaseModel):
    r"""The base model that all DataFrame models will inherit from.

    A DataFrame model represents a database table, a query or some other table like structure.
    using a :class:`pandas.DataFrame`. The DataFrame is accessible from the `df` attribute.
    Each column name of the DataFrame should be implemented as a class variable starting with
    the prefix "c_", e.g. `c_name: ClassVar[str] = 'name'` for a name column. The class variables
    listed below should be defined for each subclass of this model.

    Class Variables
    ---------------
    dtypes : ClassVar[dict[str, str]]
        The mapping of column names to their datatypes of the DataFrame.

    index_cols : ClassVar[list[str]]
        The index columns of the DataFrame.

    parse_dates : ClassVar[list[str]]
        The columns of the DataFrame that should be parsed into datetime columns.

    Parameters
    ----------
    df : pandas.DataFrame
        The contents of the model as a DataFrame.
    """

    dtypes: ClassVar[DtypeMapping] = {}
    index_cols: ClassVar[ColumnList] = []
    parse_dates: ClassVar[ColumnList] = []

    df: pd.DataFrame

    @property
    def shape(self) -> tuple[int, int]:
        r"""The shape (rows, cols) of the DataFrame."""

        return self.df.shape

    @property
    def index(self) -> pd.Index:
        r"""The index column(s) of the DataFrame."""

        return self.df.index

    @property
    def row_count(self) -> int:
        r"""The number of rows of the DataFrame."""

        return self.df.shape[0]

    @property
    def empty(self) -> bool:
        r"""Check if the DataFrame is empty or not."""

        return self.row_count == 0

    @property
    def col_dtypes(self) -> pd.Series:
        r"""The dtypes of the columns of the DataFrame."""

        return self.df.dtypes


class SerieTypeMappingDataFrameModel(BaseDataFrameModel):
    r"""A model of the serie types for mapping `code` to `serie_type_id`.

    Parameters
    ----------
    serie_type_id : int
        The unique ID of the serie type.

    code : str
        The unique code of the serie type.
    """

    c_serie_type_id: ClassVar[str] = 'serie_type_id'
    c_code: ClassVar[str] = 'code'

    dtypes: ClassVar[DtypeMapping] = {
        c_serie_type_id: 'uint32[pyarrow]',
        c_code: 'string[pyarrow]',
    }
