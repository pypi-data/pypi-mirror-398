# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The business logic for the facility data import to the Tariff Analyzer module."""

# ruff: noqa: S608

# Third party
import duckdb
import pandas as pd

# Local
from elsabio.core import OperationResult, has_required_columns
from elsabio.models.tariff_analyzer import (
    FacilityDataFrameModel,
    FacilityImportDataFrameModel,
    FacilityMappingDataFrameModel,
    FacilityTypeMappingDataFrameModel,
)
from elsabio.operations.core import UpsertDataFrames
from elsabio.operations.validate import validate_duplicate_rows, validate_missing_values


def validate_facility_import_model(
    model: duckdb.DuckDBPyRelation,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Validate the facility import model.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model with the facilities to import. Should contain
        at least the columns `ean` and `facility_type_code` from the model
        :class:`elsabio.models.tariff_analyzer.FacilityImportDataFrameModel`.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df_invalid : pandas.DataFrame
        A DataFrame containing the rows with invalid data.
        An empty DataFrame is returned if the data is valid.
    """

    c_ean = FacilityImportDataFrameModel.c_ean
    c_ean_prod = FacilityImportDataFrameModel.c_ean_prod
    c_facility_type_code = FacilityImportDataFrameModel.c_facility_type_code

    cols = set(model.columns)
    required_cols = (c_ean, c_facility_type_code)

    result = has_required_columns(cols=cols, required_cols=set(required_cols))
    if not result.ok:
        return result, pd.DataFrame()

    result, df_invalid = validate_missing_values(
        model=model,
        cols=required_cols,
        order_by=((c_ean, 'ASC'), (c_facility_type_code, 'ASC')),
        index_cols=c_ean,
    )
    if not result.ok:
        return result, df_invalid

    result, df_invalid = validate_duplicate_rows(
        model=model,
        cols=(c_ean,),
        order_by=((c_ean, 'ASC'),),
        index_cols=c_ean,
    )
    if not result.ok:
        return result, df_invalid

    result, df_invalid = validate_duplicate_rows(
        model=model,
        cols=(c_ean_prod,),
        exclude_rows_with_nulls=(c_ean_prod,),
        order_by=((c_ean_prod, 'ASC'),),
        index_cols=c_ean_prod,
    )
    if not result.ok:
        return result, df_invalid

    return OperationResult(ok=True), pd.DataFrame()


def create_facility_upsert_dataframes(
    import_model: duckdb.DuckDBPyRelation,
    facility_model: FacilityMappingDataFrameModel,
    facility_type_model: FacilityTypeMappingDataFrameModel,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[UpsertDataFrames, OperationResult]:
    r"""Create the DataFrames for inserting new and updating existing facilities.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The data model with the facilities to import. Should contain
        at least the columns `ean` and `facility_type_code` from the model
        :class:`elsabio.models.tariff_analyzer.FacilityImportDataFrameModel`.

    facility_model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The model with the mapping of `facility_id` to `ean`. Used to determine the
        existing facilities from `import_model` to update and the new ones to import.

    facility_type_model : elsabio.models.tariff_analyzer.FacilityTypeMappingDataFrameModel
        The model with the mapping of `facility_type_id` to `facility_type_code`. Used to
        derive the `facility_type_id` of the facilities to import or update.

    conn : duckdb.DuckDBPyConnection
        The DuckDB connection in which the `import_model` relation exists.

    Returns
    -------
    dfs : elsabio.operations.core.UpsertDataFrames
        The DataFrames with facilities to insert or update.

    result : elsabio.core.OperationResult
        The result of the creation of the upsert DataFrames.
    """

    # Columns
    c_facility_id = FacilityMappingDataFrameModel.c_facility_id
    c_ean = FacilityDataFrameModel.c_ean
    c_ean_prod = FacilityDataFrameModel.c_ean_prod
    c_facility_type_id = FacilityDataFrameModel.c_facility_type_id
    c_name = FacilityDataFrameModel.c_name
    c_description = FacilityDataFrameModel.c_description
    c_facility_type_code_import = FacilityImportDataFrameModel.c_facility_type_code
    c_facility_type_code = FacilityTypeMappingDataFrameModel.c_code

    cols = set(import_model.columns)

    i_model_name = 'import_model'
    i_model_prefix = 'i'
    f_model_name = 'facility_mapping'
    f_model_prefix = 'm'
    ft_model_name = 'facility_type'
    ft_model_prefix = 'ft'

    dtypes = {  # To ensure compatible dtypes with SQLAlchemy
        c_ean: 'int64',
        c_ean_prod: 'int64',
        c_facility_type_code_import: 'varchar',
        c_name: 'varchar',
        c_description: 'varchar',
    }
    cols_select_list = '\n'.join(
        f', {i_model_prefix}.{col}::{dtype} AS {col}'
        for col, dtype in dtypes.items()
        if col in cols
    )

    mapping_query = f"""\
SELECT
    {f_model_prefix}.{c_facility_id}::int64 AS {c_facility_id}
    , {ft_model_prefix}.{c_facility_type_id}::int8 AS {c_facility_type_id}
    {cols_select_list}

FROM {i_model_name} {i_model_prefix}

LEFT OUTER JOIN {f_model_name} {f_model_prefix}
    ON {f_model_prefix}.{c_ean} = {i_model_prefix}.{c_ean}

LEFT OUTER JOIN {ft_model_name} {ft_model_prefix}
    ON {ft_model_prefix}.{c_facility_type_code} = {i_model_prefix}.{c_facility_type_code_import}

ORDER BY
    {i_model_prefix}.{c_ean} ASC
"""

    import_model.create_view(i_model_name)
    conn.register(view_name=f_model_name, python_object=facility_model.df)
    conn.register(view_name=ft_model_name, python_object=facility_type_model.df)
    rel = conn.sql(query=mapping_query)

    df_insert = (
        rel.filter(f'{c_facility_id} IS NULL')
        .select(f'* EXCLUDE ({c_facility_id}, {c_facility_type_code_import})')
        .to_df()
    )
    df_update = (
        rel.filter(f'{c_facility_id} IS NOT NULL')
        .select(f'* EXCLUDE ({c_facility_type_code_import})')
        .to_df()
    )
    df_invalid = (
        rel.filter(f'{c_facility_type_id} IS NULL')
        .select(f'{c_facility_id}, {c_ean}, {c_facility_type_id}, {c_facility_type_code_import}')
        .to_df()
        .set_index(c_facility_id)
    )

    if (nr_invalid := df_invalid.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=(
                f'Found facilities ({nr_invalid}) with invalid '
                f'values for column "{c_facility_type_code_import}"!'
            ),
        )
    else:
        result = OperationResult(ok=True)

    dfs = UpsertDataFrames(insert=df_insert, update=df_update, invalid=df_invalid)

    return dfs, result
