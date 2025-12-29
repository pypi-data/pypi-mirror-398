# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The business logic for the meter data import to the Tariff Analyzer module."""

# Third party
import duckdb
import pandas as pd

# Local
from elsabio.core import OperationResult, has_required_columns
from elsabio.models import SerieTypeMappingDataFrameModel
from elsabio.models.tariff_analyzer import (
    FacilityMappingDataFrameModel,
    SerieValueImportDataFrameModel,
)
from elsabio.operations.validate import (
    SortOrder,
    validate_at_start_of_month,
    validate_duplicate_rows,
    validate_missing_values,
)


def validate_meter_data_import_model(
    model: duckdb.DuckDBPyRelation,
) -> tuple[OperationResult, pd.DataFrame]:
    r"""Validate the meter data import model.

    Parameters
    ----------
    model : duckdb.DuckDBPyRelation
        The data model with the meter data to import. Should contain at least
        the columns `serie_type_code`, `ean`, `date_id` and `serie_value`
        from the model :class:`elsabio.models.tariff_analyzer.SerieValueImportDataFrameModel`.

    Result
    ------
    result : elsabio.core.OperationResult
        The result of the model validation.

    df_invalid : pandas.DataFrame
        A DataFrame containing the rows with invalid data.
        An empty DataFrame is returned if the data is valid.
    """

    c_ean = SerieValueImportDataFrameModel.c_ean
    c_date_id = SerieValueImportDataFrameModel.c_date_id
    c_serie_type_code = SerieValueImportDataFrameModel.c_serie_type_code
    c_serie_value = SerieValueImportDataFrameModel.c_serie_value

    cols = set(model.columns)
    required_cols = (c_serie_type_code, c_ean, c_date_id, c_serie_value)

    result = has_required_columns(cols=cols, required_cols=set(required_cols))
    if not result.ok:
        return result, pd.DataFrame()

    order_by: tuple[tuple[str, SortOrder], ...] = ((c_ean, 'ASC'), (c_date_id, 'ASC'))
    index_cols = [c_ean, c_date_id]

    result, df_invalid = validate_missing_values(
        model=model,
        cols=required_cols,
        order_by=order_by,
        index_cols=index_cols,
    )
    if not result.ok:
        return result, df_invalid

    result, df_invalid = validate_duplicate_rows(
        model=model,
        cols=(c_serie_type_code, c_ean, c_date_id),
        order_by=order_by,
        index_cols=index_cols,
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


def create_serie_value_model(
    import_model: duckdb.DuckDBPyRelation,
    facility_model: FacilityMappingDataFrameModel,
    serie_type_model: SerieTypeMappingDataFrameModel,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[duckdb.DuckDBPyRelation, OperationResult, pd.DataFrame]:
    r"""Create the meter data serie value model from the import model.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The data model with the meter data to import. Should adhere to the structure
        of :class:`elsabio.models.tariff_analyzer.SerieValueImportDataFrameModel`.

    facility_model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The model with the mapping of the columns `facility_id` to `ean`.

    serie_type_model: elsabio.models.core.SerieTypeMappingDataFrameModel
        The model with the mapping of the columns `serie_type_id` to `serie_type_code`

    conn : duckdb.DuckDBPyConnection
        The DuckDB connection in which the `import_model` relation exists.

    Returns
    -------
    rel : duckdb.DuckDBPyRelation
        The relation object with the serie value model.

    result : elsabio.core.OperationResult
        The result of the creation of the serie value model.

    df_invalid : pandas.DataFrame
        A DataFrame containing the rows with invalid data.
        An empty DataFrame is returned if the data is valid.
    """

    c_facility_id = FacilityMappingDataFrameModel.c_facility_id
    c_ean = FacilityMappingDataFrameModel.c_ean

    c_serie_type_id = SerieTypeMappingDataFrameModel.c_serie_type_id
    c_serie_type_code = SerieTypeMappingDataFrameModel.c_code

    c_serie_type_code_import = SerieValueImportDataFrameModel.c_serie_type_code
    c_ean_import = SerieValueImportDataFrameModel.c_ean
    c_date_id = SerieValueImportDataFrameModel.c_date_id
    c_serie_value = SerieValueImportDataFrameModel.c_serie_value
    c_status_id = SerieValueImportDataFrameModel.c_status_id

    cols = set(import_model.columns)

    i_model_name = 'import_model'
    i_model_prefix = 'i'
    f_model_name = 'facility_mapping'
    f_model_prefix = 'f'
    st_model_name = 'serie_type'
    st_model_prefix = 'st'

    dtypes = {
        c_serie_type_code_import: 'varchar',
        c_ean: 'uint64',
        c_date_id: 'date',
        c_serie_value: 'decimal(18,3)',
        c_status_id: 'varchar',
    }
    cols_select_list = '\n'.join(
        f', {i_model_prefix}.{col}::{dtype} AS {col}'
        for col, dtype in dtypes.items()
        if col in cols
    )

    mapping_query = f"""\
SELECT
    {f_model_prefix}.{c_facility_id}::uint64 AS {c_facility_id}
    , {st_model_prefix}.{c_serie_type_id}::uint16 AS {c_serie_type_id}
    {cols_select_list}

FROM {i_model_name} {i_model_prefix}

LEFT OUTER JOIN {f_model_name} {f_model_prefix}
    ON {f_model_prefix}.{c_ean} = {i_model_prefix}.{c_ean_import}

LEFT OUTER JOIN {st_model_name} {st_model_prefix}
    ON {st_model_prefix}.{c_serie_type_code} = {i_model_prefix}.{c_serie_type_code_import}

ORDER BY
    {i_model_prefix}.{c_date_id} ASC
    , {i_model_prefix}.{c_ean}   ASC
"""  # noqa: S608

    import_model.create_view(i_model_name)
    conn.register(view_name=f_model_name, python_object=facility_model.df)
    conn.register(view_name=st_model_name, python_object=serie_type_model.df)
    rel = conn.sql(query=mapping_query)

    df_invalid = (
        rel.filter(f'{c_facility_id} IS NULL OR  {c_serie_type_id} IS NULL')
        .order(f'{c_ean} ASC, {c_date_id} ASC')
        .to_df(date_as_object=True)
        .set_index([c_ean, c_date_id])
    )
    if (nr_invalid := df_invalid.shape[0]) > 0:
        result = OperationResult(
            ok=False,
            short_msg=(
                f'Found rows ({nr_invalid}) with invalid values '
                f'for columns "{c_serie_type_code_import}" or "{c_ean}"!'
            ),
        )
    else:
        result = OperationResult(ok=True)
        df_invalid = pd.DataFrame()

    rel = rel.select(f'* EXCLUDE({c_serie_type_id})')

    return rel, result, df_invalid
