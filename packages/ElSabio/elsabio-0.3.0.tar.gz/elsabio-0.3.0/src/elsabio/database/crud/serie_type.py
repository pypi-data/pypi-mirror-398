# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `SerieType` model."""

# Third party
from sqlalchemy import select

# Local
from elsabio.core import OperationResult
from elsabio.database.core import Session, load_sql_query_as_dataframe
from elsabio.database.models.core import SerieType
from elsabio.models.core import SerieTypeMappingDataFrameModel


def load_serie_type_mapping_model(
    session: Session,
) -> tuple[SerieTypeMappingDataFrameModel, OperationResult]:
    r"""Load the serie type model for mapping the column `code` to `serie_type_id`.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.core.SerieTypeMappingDataFrameModel
        The dataset of the serie type mapping model.

    result : elsabio.core.OperationResult
        The result of loading the serie type mapping model from the database.
    """

    query = select(
        SerieType.code.label(SerieTypeMappingDataFrameModel.c_code),
        SerieType.serie_type_id.label(SerieTypeMappingDataFrameModel.c_serie_type_id),
    ).order_by(SerieType.code.asc())

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=SerieTypeMappingDataFrameModel.dtypes,
        error_msg='Error loading serie types from the database!',
    )

    return SerieTypeMappingDataFrameModel(df=df), result
