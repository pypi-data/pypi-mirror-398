# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `Facility` model of Tariff Analyzer."""

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
from elsabio.database.models.tariff_analyzer import Facility
from elsabio.models.tariff_analyzer import FacilityDataFrameModel, FacilityMappingDataFrameModel


def load_facility_mapping_model(
    session: Session,
) -> tuple[FacilityMappingDataFrameModel, OperationResult]:
    r"""Load the facility mapping model for mapping `ean` to `facility_id`.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.tariff_analyzer.FacilityMappingDataFrameModel
        The dataset of the facility mappings.

    result : elsabio.core.OperationResult
        The result of loading the facility mapping model from the database.
    """

    query = select(
        Facility.ean.label(FacilityMappingDataFrameModel.c_ean),
        Facility.facility_id.label(FacilityMappingDataFrameModel.c_facility_id),
    ).order_by(Facility.ean.asc())

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=FacilityMappingDataFrameModel.dtypes,
        error_msg='Error loading facilities from the database!',
    )

    return FacilityMappingDataFrameModel(df=df), result


def bulk_insert_facilities(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk insert facilities into the facility table.

    Parameters
    ----------
    conn : elsabio.db.Session
        An open session to the database.

    Returns
    -------
    elsabio.core.OperationResult
        The result of saving the new facilities to the database.
    """

    return bulk_insert_to_table(
        session=session,
        table=Facility.__tablename__,
        df=df,
        required_cols={FacilityDataFrameModel.c_ean, FacilityDataFrameModel.c_facility_type_id},
    )


def bulk_update_facilities(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk update existing facilities.

    Parameters
    ----------
    conn : elsabio.db.Session
        An open session to the database.

    Returns
    -------
    elsabio.core.OperationResult
        The result of updating the existing facilities in the database.
    """

    return bulk_update_table(
        session=session, model=Facility, df=df, required_cols={FacilityDataFrameModel.c_facility_id}
    )
