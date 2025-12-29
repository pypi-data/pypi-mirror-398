# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the sub-command `ta import meter-data` of the Tariff Analyzer module."""

# Standard library
import logging

# Third party
import click
import duckdb

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
from elsabio.database.crud import load_serie_type_mapping_model
from elsabio.database.tariff_analyzer import (
    load_facility_mapping_model,
)
from elsabio.models import SerieTypeMappingDataFrameModel
from elsabio.models.tariff_analyzer import (
    FacilityMappingDataFrameModel,
    SerieValueDataFrameModel,
)
from elsabio.operations.file import write_parquet
from elsabio.operations.tariff_analyzer import (
    create_serie_value_model,
    validate_meter_data_import_model,
)

METER_DATA_SOURCES = (
    DataSource.ACTIVE_ENERGY_CONS,
    DataSource.ACTIVE_ENERGY_PROD,
    DataSource.MAX_ACTIVE_POWER_CONS,
    DataSource.MAX_ACTIVE_POWER_PROD,
    DataSource.MAX_REACTIVE_POWER_CONS,
    DataSource.MAX_REACTIVE_POWER_PROD,
    DataSource.MAX_DEB_ACTIVE_POWER_CONS_HIGH_LOAD,
    DataSource.MAX_DEB_ACTIVE_POWER_CONS_LOW_LOAD,
)


def _create_serie_value_model(
    import_model: duckdb.DuckDBPyRelation,
    facility_model: FacilityMappingDataFrameModel,
    serie_type_model: SerieTypeMappingDataFrameModel,
    conn: duckdb.DuckDBPyConnection,
) -> tuple[duckdb.DuckDBPyRelation, OperationResult]:
    r"""Create the meter data serie value model from the import model.

    Parameters
    ----------
    import_model : duckdb.DuckDBPyRelation
        The data model with the meter data to import. Should adhere to the structure
        of :class:`elsabio.models.tariff_analyzer.SerieValueImportDataFrameModel`.

    facility_model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The model with the mapping of columns `facility_id` to `ean`.

    serie_type_model: elsabio.models.core.SerieTypeMappingDataFrameModel
        The model with the mapping of columns `serie_type_id` to `serie_type_code`.

    conn : duckdb.DuckDBPyConnection
        The DuckDB connection in which the `import_model` relation exists.

    Returns
    -------
    rel : duckdb.DuckDBPyRelation
        The relation object with the serie value model.

    result : elsabio.core.OperationResult
        The result of the creation of the serie value model.
    """

    serie_value_rel, result, df_invalid = create_serie_value_model(
        import_model=import_model,
        facility_model=facility_model,
        serie_type_model=serie_type_model,
        conn=conn,
    )
    if not result.ok:
        echo_with_log(
            message=f'{result.short_msg}\n{display_dataframe(df_invalid, as_str=True)}\n',
            log_level=logging.ERROR,
            color=Color.ERROR,
        )

    return serie_value_rel, result


@click.command()
@click.pass_context
@click.argument(
    'sources',
    nargs=-1,
    type=click.Choice(METER_DATA_SOURCES, case_sensitive=False),
)
def meter_data(ctx: click.Context, sources: tuple[DataSource, ...] | None) -> None:  # noqa: C901
    """Import meter data to the Tariff Analyzer module

    \b
    Examples
    --------
    \b
    Import meter data for all available sources:
        $ elsabio ta import meter-data

    \b
    Import meter data for active energy consumption and production:
        $ elsabio ta import meter-data active_energy_cons active_energy_prod
    """

    cm, session_factory = load_resources(ctx=ctx)
    sources = sources if sources else METER_DATA_SOURCES

    with session_factory() as session:
        facility_model, result = load_facility_mapping_model(session)
        if not result.ok:
            exit_program(error=True, ctx=ctx, message=result.short_msg)

        serie_type_model, result = load_serie_type_mapping_model(session)
        if not result.ok:
            exit_program(error=True, ctx=ctx, message=result.short_msg)

    data_dir = cm.tariff_analyzer.data_dir / 'meter_data'
    processed_sources_success: list[str] = []

    with duckdb.connect() as conn:
        for source in sources:
            cfg = cm.tariff_analyzer.data.get(source)
            if cfg is None:
                click.echo(f'No configuration found for "tariff_analyzer.data.{source}"!')
                continue

            echo_with_log(message=f'Processing data source : {source}')

            input_path = cfg.path
            echo_with_log(message=f'Loading data from : {input_path}')

            import_model, result = load_data_model_to_import(
                method=cfg.method, path=input_path, conn=conn
            )
            if not result.ok:
                echo_with_log(message=result.short_msg, log_level=logging.ERROR, color=Color.ERROR)
                continue

            if not validate_import_model(model=import_model, func=validate_meter_data_import_model):
                continue

            serie_value_rel, result = _create_serie_value_model(
                import_model=import_model,
                facility_model=facility_model,
                serie_type_model=serie_type_model,
                conn=conn,
            )
            if not result.ok:
                continue

            result = write_parquet(
                rel=serie_value_rel,
                path=data_dir,
                partition_by=[
                    SerieValueDataFrameModel.c_serie_type_code,
                    SerieValueDataFrameModel.c_date_id,
                ],
                overwrite=True,
            )
            if not result.ok:
                echo_with_log(message=result.short_msg, log_level=logging.ERROR, color=Color.ERROR)
                continue

            result = move_processed_files(source_dir=cfg.path, error=False)
            if result.ok:
                echo_with_log(result.short_msg)
            else:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            processed_sources_success.append(source.value)

    if processed_sources_success:
        message = (
            f'Successfully processed meter data for sources: {tuple(processed_sources_success)}'
        )
        error = False
    else:
        message = None
        error = True

    exit_program(error=error, ctx=ctx, message=message)
