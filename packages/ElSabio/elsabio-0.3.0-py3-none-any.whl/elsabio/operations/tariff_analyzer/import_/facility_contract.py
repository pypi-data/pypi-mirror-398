# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The business logic for the facility contract data to import to the Tariff Analyzer module."""

# ruff: noqa: S608

# Standard library
from datetime import date

# Third party
import duckdb
import pandas as pd

# Local
from elsabio.core import OperationResult, has_required_columns
from elsabio.models.tariff_analyzer import (
    CustomerTypeMappingDataFrameModel,
    FacilityContractImportDataFrameModel,
    FacilityContractMappingDataFrameModel,
    FacilityMappingDataFrameModel,
    ProductMappingDataFrameModel,
)
from elsabio.operations.core import UpsertDataFrames
from elsabio.operations.validate import (
    SortOrder,
    validate_at_start_of_month,
    validate_duplicate_rows,
    validate_missing_values,
)


def validate_facility_contract_import_data(
    model: duckdb.DuckDBPyRelation,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Validate the facility contract import data.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model with the facility contracts to import. Should contain
        at least the columns `ean`, `date_id` and `customer_type_code` from the model
        :class:`elsabio.models.tariff_analyzer.FacilityContractImportDataFrameModel`.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df_invalid : pandas.DataFrame
        A DataFrame containing the rows with invalid data.
        An empty DataFrame is returned if the data is valid.
    """

    c_ean = FacilityContractImportDataFrameModel.c_ean
    c_date_id = FacilityContractImportDataFrameModel.c_date_id
    c_customer_type_code_import = FacilityContractImportDataFrameModel.c_customer_type_code

    cols = set(model.columns)
    required_cols = (c_ean, c_date_id, c_customer_type_code_import)

    result = has_required_columns(cols=cols, required_cols=set(required_cols))
    if not result.ok:
        return result, pd.DataFrame()

    order_by: tuple[tuple[str, SortOrder], ...] = ((c_ean, 'ASC'), (c_date_id, 'ASC'))
    index_cols = [c_ean, c_date_id]

    result, df_invalid = validate_missing_values(
        model=model, cols=required_cols, order_by=order_by, index_cols=index_cols
    )
    if not result.ok:
        return result, df_invalid

    result, df_invalid = validate_duplicate_rows(
        model=model, cols=(c_ean, c_date_id), order_by=order_by, index_cols=index_cols
    )
    if not result.ok:
        return result, df_invalid

    result, df_invalid = validate_at_start_of_month(
        model=model,
        date_col=c_date_id,
        display_cols=required_cols,
        order_by=order_by,
        index_cols=index_cols,
    )
    if not result.ok:
        return result, df_invalid

    return OperationResult(ok=True), pd.DataFrame()


def get_facility_contract_import_interval(
    import_model: duckdb.DuckDBPyRelation,
) -> tuple[date, date, OperationResult]:
    r"""Get the facility contract import interval.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The facility contract data model to analyze. Should adhere to the structure
        of :class:`elsabio.models.tariff_analyzer.FacilityContractImportDataFrameModel`.

    Result
    ------
    start_date : datetime.date
        The earliest month of facility contracts in `import_model`.

    end_date : datetime.date
        The latest month of facility contracts in `import_model`.

    result : elsabio.core.OperationResult
        The result of computing `start_date` and `end_date` from `import_model`.
    """

    c_date_id = FacilityContractImportDataFrameModel.c_date_id
    interval = import_model.aggregate(f'MIN({c_date_id})::date, MAX({c_date_id})::date').fetchone()

    if interval is None:
        result = OperationResult(
            ok=False,
            short_msg=('Could not compute facility contract interval!'),
        )
        return date.today(), date.today(), result

    start_date, end_date = interval

    return start_date, end_date, OperationResult(ok=True)


def create_facility_contract_upsert_dataframes(
    import_model: duckdb.DuckDBPyRelation,
    facility_contract_model: FacilityContractMappingDataFrameModel,
    facility_model: FacilityMappingDataFrameModel,
    customer_type_model: CustomerTypeMappingDataFrameModel,
    product_model: ProductMappingDataFrameModel,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[UpsertDataFrames, OperationResult]:
    r"""Create the DataFrames for inserting new and updating existing facility contracts.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The data model with the facility contracts to import. Should adhere to the structure
        of :class:`elsabio.models.tariff_analyzer.FacilityContractImportDataFrameModel`.

    facility_model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The model with the mapping of `facility_id` to `ean`. Used to determine the
        existing facilities from `import_model` to update and the new ones to import.

    customer_type_model: elsabio.models.tariff_analyzer.CustomerTypeMappingDataFrameModel
        The model with the mapping of `customer_type_id` to `customer_type_code`. Used to
        derive the `customer_type_id` of the facility contracts to import or update.

    product_model : elsabio.models.tariff_analyzer.ProductMappingDataFrameModel
        The model with the mapping of `product_id` to `external_id`. Used to
        derive the `product_id` of the facility contracts to import or update.

    conn : duckdb.DuckDBPyConnection
        The DuckDB connection in which the `import_model` relation exists.

    Returns
    -------
    dfs : elsabio.operations.core.UpsertDataFrames
        The DataFrames with facility contracts to insert or update.

    result : elsabio.core.OperationResult
        The result of the creation of the upsert DataFrames.
    """

    # Columns
    c_facility_id = FacilityMappingDataFrameModel.c_facility_id

    c_ean = FacilityContractImportDataFrameModel.c_ean
    c_date_id = FacilityContractImportDataFrameModel.c_date_id
    c_fuse_size = FacilityContractImportDataFrameModel.c_fuse_size
    c_subscribed_power = FacilityContractImportDataFrameModel.c_subscribed_power
    c_connection_power = FacilityContractImportDataFrameModel.c_connection_power
    c_account_nr = FacilityContractImportDataFrameModel.c_account_nr
    c_customer_type_code_import = FacilityContractImportDataFrameModel.c_customer_type_code
    c_product_ext_id_import = FacilityContractImportDataFrameModel.c_ext_product_id

    c_customer_type_code = CustomerTypeMappingDataFrameModel.c_code
    c_customer_type_id = CustomerTypeMappingDataFrameModel.c_customer_type_id

    c_product_id = ProductMappingDataFrameModel.c_product_id
    c_ext_product_id = ProductMappingDataFrameModel.c_external_id

    c_to_insert = 'to_insert'

    df_facility_contract = facility_contract_model.df
    df_facility = facility_model.df
    df_customer_type = customer_type_model.df
    df_product = product_model.df
    cols = set(import_model.columns)

    i_model_name = 'import_model'
    i_model_prefix = 'i'
    fc_model_name = 'facility_contract_mapping'
    fc_model_prefix = 'fc'
    f_model_name = 'facility_mapping'
    f_model_prefix = 'f'
    ct_model_name = 'customer_type'
    ct_model_prefix = 'ct'
    p_model_name = 'product_mapping'
    p_model_prefix = 'p'

    dtypes = {  # To ensure compatible dtypes with SQLAlchemy
        c_ean: 'int64',
        c_date_id: 'date',
        c_fuse_size: 'int16',
        c_subscribed_power: 'double',
        c_connection_power: 'double',
        c_account_nr: 'int32',
        c_customer_type_code_import: 'varchar',
        c_product_ext_id_import: 'varchar',
    }
    cols_select_list = '\n'.join(
        f', {i_model_prefix}.{col}::{dtype} AS {col}'
        for col, dtype in dtypes.items()
        if col in cols
    )

    mapping_query = f"""\
SELECT
    {f_model_prefix}.{c_facility_id}::int64 AS {c_facility_id}
    , {ct_model_prefix}.{c_customer_type_id}::int16 AS {c_customer_type_id}
    , {p_model_prefix}.{c_product_id}::int32 AS {c_product_id}
    , CASE
        WHEN (
            {fc_model_prefix}.{c_date_id} IS NULL
            AND {fc_model_prefix}.{c_facility_id} IS NULL
        ) THEN
            true
        ELSE
            false
      END AS {c_to_insert}
    {cols_select_list}

FROM {i_model_name} {i_model_prefix}

LEFT OUTER JOIN {f_model_name} {f_model_prefix}
    ON {f_model_prefix}.{c_ean} = {i_model_prefix}.{c_ean}

LEFT OUTER JOIN {fc_model_name} {fc_model_prefix}
    ON {fc_model_prefix}.{c_facility_id} = {f_model_prefix}.{c_facility_id}
       AND {fc_model_prefix}.{c_date_id} = {i_model_prefix}.{c_date_id}

LEFT OUTER JOIN {ct_model_name} {ct_model_prefix}
    ON {ct_model_prefix}.{c_customer_type_code} = {i_model_prefix}.{c_customer_type_code_import}

LEFT OUTER JOIN {p_model_name} {p_model_prefix}
    ON {p_model_prefix}.{c_ext_product_id} = {i_model_prefix}.{c_product_ext_id_import}

ORDER BY
    {i_model_prefix}.{c_date_id} ASC
    , {i_model_prefix}.{c_ean}   ASC
"""

    import_model.create_view(i_model_name)
    conn.register(view_name=fc_model_name, python_object=df_facility_contract)
    conn.register(view_name=f_model_name, python_object=df_facility)
    conn.register(view_name=ct_model_name, python_object=df_customer_type)
    conn.register(view_name=p_model_name, python_object=df_product)
    rel = conn.sql(query=mapping_query)

    select_columns = (
        f'* EXCLUDE ({c_ean}, '
        f'{c_customer_type_code_import}, {c_product_ext_id_import}, {c_to_insert})'
    )
    df_insert = (
        rel.filter(f'{c_to_insert} = true').select(select_columns).to_df(date_as_object=True)
    )
    df_update = (
        rel.filter(f'{c_to_insert} = false').select(select_columns).to_df(date_as_object=True)
    )
    df_invalid = (
        rel.filter(f'{c_customer_type_id} IS NULL')
        .select(
            f'{c_facility_id}, {c_ean}, {c_date_id}, '
            f'{c_customer_type_id}, {c_customer_type_code_import}'
        )
        .order(f'{c_ean} ASC, {c_date_id} ASC')
        .to_df(date_as_object=True)
        .set_index(c_facility_id)
    )

    if (nr_invalid := df_invalid.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=(
                f'Found facility contracts ({nr_invalid}) with '
                f'invalid values for column "{c_customer_type_code_import}"!'
            ),
        )
    else:
        result = OperationResult(ok=True)

    dfs = UpsertDataFrames(insert=df_insert, update=df_update, invalid=df_invalid)

    return dfs, result
