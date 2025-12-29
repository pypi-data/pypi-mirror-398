# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the sub-command `ta import product` of the Tariff Analyzer module."""

# Third party
import click
import duckdb

# Local
from elsabio.cli.core import echo_with_log, exit_program, load_resources
from elsabio.cli.tariff_analyzer.import_.core import (
    load_data_model_to_import,
    move_processed_files,
    validate_import_model,
)
from elsabio.config.tariff_analyzer import DataSource
from elsabio.database.tariff_analyzer import (
    bulk_insert_products,
    bulk_update_products,
    load_product_mapping_model,
)
from elsabio.operations.tariff_analyzer import (
    create_product_upsert_dataframes,
    validate_product_import_data,
)


@click.command(name='product')
@click.pass_context
def product(ctx: click.Context) -> None:
    """Import products to the database of the Tariff Analyzer module"""

    cm, session_factory = load_resources(ctx=ctx)
    cfg = cm.tariff_analyzer.data.get(DataSource.PRODUCT)

    if cfg is None:
        exit_program(
            error=True,
            ctx=ctx,
            message=f'No data configuration found for "tariff_analyzer.data.{DataSource.PRODUCT}"!',
        )

    with session_factory() as session:
        with duckdb.connect() as conn:
            import_model, result = load_data_model_to_import(
                method=cfg.method, path=cfg.path, conn=conn
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            if not validate_import_model(model=import_model, func=validate_product_import_data):
                exit_program(error=True, ctx=ctx)

            product_model, result = load_product_mapping_model(session)
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

            df_insert, df_update, result = create_product_upsert_dataframes(
                import_model=import_model, product_model=product_model, conn=conn
            )
            if not result.ok:
                exit_program(error=True, ctx=ctx, message=result.short_msg)

        result = bulk_insert_products(session=session, df=df_insert)
        if not result.ok:
            exit_program(error=True, ctx=ctx, message=result.short_msg)

        result = bulk_update_products(session=session, df=df_update)
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
                f'Successfully imported {df_insert.shape[0]} new products '
                f'and updated {df_update.shape[0]} existing products!'
            ),
        )
