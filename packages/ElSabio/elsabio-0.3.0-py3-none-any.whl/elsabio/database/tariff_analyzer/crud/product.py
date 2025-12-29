# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `Product` model of Tariff Analyzer."""

# Third party
import pandas as pd
from sqlalchemy import select

# Local
from elsabio.core import OperationResult
from elsabio.database.core import (
    Session,
    bulk_insert_to_table,
    bulk_update_table,
    load_sql_query_as_dataframe,
)
from elsabio.database.models.tariff_analyzer import Product
from elsabio.models.tariff_analyzer import (
    ProductDataFrameModel,
    ProductMappingDataFrameModel,
)


def load_product_mapping_model(
    session: Session,
) -> tuple[ProductMappingDataFrameModel, OperationResult]:
    r"""Load the product mapping model for mapping `external_id` to `product_id`.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.tariff_analyzer.ProductMappingDataFrameModel
        The dataset of the product mappings.

    result : elsabio.core.OperationResult
        The result of loading the product mapping model from the database.
    """

    query = select(
        Product.external_id.label(ProductMappingDataFrameModel.c_external_id),
        Product.product_id.label(ProductMappingDataFrameModel.c_product_id),
    ).order_by(Product.external_id.asc())

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=ProductMappingDataFrameModel.dtypes,
        error_msg='Error loading products from the database!',
    )

    return ProductMappingDataFrameModel(df=df), result


def bulk_insert_products(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk insert products into the product table.

    Parameters
    ----------
    conn : elsabio.db.Session
        An open session to the database.

    Returns
    -------
    elsabio.core.OperationResult
        The result of saving the new products to the database.
    """

    return bulk_insert_to_table(
        session=session,
        table=Product.__tablename__,
        df=df,
        required_cols={ProductDataFrameModel.c_external_id, ProductDataFrameModel.c_name},
    )


def bulk_update_products(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk update existing products.

    Parameters
    ----------
    conn : elsabio.db.Session
        An open session to the database.

    Returns
    -------
    elsabio.core.OperationResult
        The result of updating the existing products in the database.
    """

    return bulk_update_table(
        session=session,
        model=Product,
        df=df,
        required_cols={
            ProductDataFrameModel.c_product_id,
            ProductDataFrameModel.c_external_id,
            ProductDataFrameModel.c_name,
        },
    )
