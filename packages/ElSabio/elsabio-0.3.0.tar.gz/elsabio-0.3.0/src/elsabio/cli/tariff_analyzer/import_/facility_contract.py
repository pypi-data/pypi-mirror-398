# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the sub-command `ta import facility-contract` of the Tariff Analyzer module."""

# Standard library
import logging

# Third party
import click
import duckdb
import pandas as pd

# Local
from elsabio.cli.core import Color, echo_with_log, exit_program, load_resources
from elsabio.cli.display import display_dataframe
from elsabio.cli.tariff_analyzer.import_.core import (
    load_data_model_to_import,
    move_processed_files,
    validate_import_model,
)
from elsabio.config.tariff_analyzer import DataSource
from elsabio.core import OperationResult
from elsabio.database import Session
from elsabio.database.tariff_analyzer import (
    bulk_insert_facility_contracts,
    bulk_update_facility_contracts,
    load_customer_type_mapping_model,
    load_facility_contract_mapping_model,
    load_facility_mapping_model,
    load_product_mapping_model,
)
from elsabio.models.tariff_analyzer import (
    CustomerTypeMappingDataFrameModel,
    FacilityContractMappingDataFrameModel,
    FacilityMappingDataFrameModel,
    ProductMappingDataFrameModel,
)
from elsabio.operations.tariff_analyzer import (
    create_facility_contract_upsert_dataframes,
    get_facility_contract_import_interval,
    validate_facility_contract_import_data,
)


def _upsert_facility_contracts(
    session: Session, df_insert: pd.DataFrame, df_update: pd.DataFrame
) -> OperationResult:
    r"""Insert new and update existing facility contracts.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    df_insert : pandas.DataFrame
        The DataFrame with facility contracts to insert.

    df_update : pandas.DataFrame
        The DataFrame with facility contracts to update.

    Returns
    -------
    result : elsabio.core.OperationResult
        The result of inserting and updating the facility contracts.
    """

    result = bulk_insert_facility_contracts(session=session, df=df_insert)
    if not result.ok:
        return result

    return bulk_update_facility_contracts(session=session, df=df_update)


def _create_upsert_dataframes(
    import_model: duckdb.DuckDBPyRelation,
    facility_contract_model: FacilityContractMappingDataFrameModel,
    facility_model: FacilityMappingDataFrameModel,
    customer_type_model: CustomerTypeMappingDataFrameModel,
    product_model: ProductMappingDataFrameModel,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[pd.DataFrame, pd.DataFrame, OperationResult]:
    r"""Create the DataFrames to insert new and update existing facility contracts.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The data model with the facility contracts to import. Should adhere to the structure
        of :class:`elsabio.models.tariff_analyzer.FacilityContractImportDataFrameModel`.

    facility_model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The model of the available facilities.

    customer_type_model : elsabio.models.tariff_analyzer.CustomerTypeMappingDataFrameModel
        The model of the available customer types.

    product_model : elsabio.models.tariff_analyzer.ProductMappingDataFrameModel
        The model of the available products.

    conn : duckdb.DuckDBPyConnection
        The DuckDB connection in which the `import_model` relation exists.

    Returns
    -------
    df_insert : pandas.DataFrame
        The DataFrame with facility contracts to insert.

    df_update : pandas.DataFrame
        The DataFrame with facility contracts to update.

    result : elsabio.core.OperationResult
        The result of the creation of the upsert DataFrames.
    """

    dfs, result = create_facility_contract_upsert_dataframes(
        import_model=import_model,
        facility_contract_model=facility_contract_model,
        facility_model=facility_model,
        customer_type_model=customer_type_model,
        product_model=product_model,
        conn=conn,
    )
    if not result.ok:
        echo_with_log(
            message=f'{result.short_msg}\n{display_dataframe(dfs.invalid, as_str=True)}\n',
            log_level=logging.ERROR,
            color=Color.ERROR,
        )

    return dfs.insert, dfs.update, result


@click.command()
@click.pass_context
def facility_contract(ctx: click.Context) -> None:  # noqa: C901
    """Import facility contracts to the database of the Tariff Analyzer module"""

    cm, session_factory = load_resources(ctx=ctx)
    cfg = cm.tariff_analyzer.data.get(DataSource.FACILITY_CONTRACT)

    if cfg is None:
        exit_program(
            error=True,
            ctx=ctx,
            message='No data configuration found for "tariff_analyzer.data.facility_contract"!',
        )

    with session_factory() as session:
        with duckdb.connect() as conn:
            import_model, result = load_data_model_to_import(
                method=cfg.method, path=cfg.path, conn=conn
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            if not validate_import_model(
                model=import_model, func=validate_facility_contract_import_data
            ):
                exit_program(error=True, ctx=ctx)

            start_date, end_date, result = get_facility_contract_import_interval(
                import_model=import_model
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            facility_contract_model, result = load_facility_contract_mapping_model(
                session=session, date_ids=(start_date, end_date)
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            facility_model, result = load_facility_mapping_model(session)
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            customer_type_model, result = load_customer_type_mapping_model(session=session)
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            product_model, result = load_product_mapping_model(session)
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            df_insert, df_update, result = _create_upsert_dataframes(
                import_model=import_model,
                facility_contract_model=facility_contract_model,
                facility_model=facility_model,
                customer_type_model=customer_type_model,
                product_model=product_model,
                conn=conn,
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx)

        result = _upsert_facility_contracts(
            session=session, df_insert=df_insert, df_update=df_update
        )
        if not result.ok:
            exit_program(error=True, ctx=ctx, message=result.short_msg)

    result = move_processed_files(source_dir=cfg.path, error=False)
    if result.ok:
        echo_with_log(result.short_msg)
    else:
        exit_program(error=True, ctx=ctx, message=result.short_msg)

    exit_program(
        error=False,
        ctx=ctx,
        message=(
            f'Successfully imported {df_insert.shape[0]} new facility contracts '
            f'and updated {df_update.shape[0]} existing facility contracts '
            f'in interval {start_date} - {end_date}!'
        ),
    )
