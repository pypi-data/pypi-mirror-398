# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `CustomerType` model of Tariff Analyzer."""

# Third party
from sqlalchemy import select

# Local
from elsabio.core import OperationResult
from elsabio.database.core import Session, load_sql_query_as_dataframe
from elsabio.database.models.tariff_analyzer import CustomerType
from elsabio.models.tariff_analyzer import (
    CustomerTypeMappingDataFrameModel,
)


def load_customer_type_mapping_model(
    session: Session,
) -> tuple[CustomerTypeMappingDataFrameModel, OperationResult]:
    r"""Load the customer type model for mapping the column `code` to `customer_type_id`.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.tariff_analyzer.CustomerTypeMappingDataFrameModel
        The dataset of the customer type mapping.

    result : elsabio.core.OperationResult
        The result of loading the customer type mapping model from the database.
    """

    query = select(
        CustomerType.code.label(CustomerTypeMappingDataFrameModel.c_code),
        CustomerType.customer_type_id.label(CustomerTypeMappingDataFrameModel.c_customer_type_id),
    ).order_by(CustomerType.code.asc())

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=CustomerTypeMappingDataFrameModel.dtypes,
        error_msg='Error loading customer types from the database!',
    )

    return CustomerTypeMappingDataFrameModel(df=df), result
