# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `FacilityType` model of Tariff Analyzer."""

# Third party
from sqlalchemy import select

# Local
from elsabio.core import OperationResult
from elsabio.database.core import Session, load_sql_query_as_dataframe
from elsabio.database.models.tariff_analyzer import FacilityType
from elsabio.models.tariff_analyzer import (
    FacilityTypeMappingDataFrameModel,
)


def load_facility_type_mapping_model(
    session: Session,
) -> tuple[FacilityTypeMappingDataFrameModel, OperationResult]:
    r"""Load the facility type model for mapping the column `code` to `facility_type_id`.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The dataset of the facility type mapping.

    result : elsabio.core.OperationResult
        The result of loading the facility type mapping model from the database.
    """

    query = select(
        FacilityType.code.label(FacilityTypeMappingDataFrameModel.c_code),
        FacilityType.facility_type_id.label(FacilityTypeMappingDataFrameModel.c_facility_type_id),
    ).order_by(FacilityType.code.asc())

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=FacilityTypeMappingDataFrameModel.dtypes,
        error_msg='Error loading facility types from the database!',
    )

    return FacilityTypeMappingDataFrameModel(df=df), result
