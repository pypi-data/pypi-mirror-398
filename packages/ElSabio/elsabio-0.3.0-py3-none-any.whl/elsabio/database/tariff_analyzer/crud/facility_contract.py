# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions for working with the `FacilityContract` model of Tariff Analyzer."""

# Standard library
from collections.abc import Sequence
from datetime import date

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
from elsabio.database.models.tariff_analyzer import FacilityContract
from elsabio.models.tariff_analyzer import (
    FacilityContractDataFrameModel,
    FacilityContractMappingDataFrameModel,
)


def load_facility_contract_mapping_model(
    session: Session, date_ids: Sequence[date]
) -> tuple[FacilityContractMappingDataFrameModel, OperationResult]:
    r"""Load the facility contract mapping model for locating existing facility contracts.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    model : elsabio.models.tariff_analyzer.FacilityContractMappingDataFrameModel
        The dataset of the facility contract mappings.

    result : elsabio.core.OperationResult
        The result of loading the facility contract mapping model from the database.
    """

    query = (
        select(
            FacilityContract.facility_id.label(FacilityContractMappingDataFrameModel.c_facility_id),
            FacilityContract.date_id.label(FacilityContractMappingDataFrameModel.c_date_id),
        )
        .where(FacilityContract.date_id.in_(date_ids))
        .order_by(FacilityContract.date_id.asc(), FacilityContract.facility_id.asc())
    )

    df, result = load_sql_query_as_dataframe(
        query=query,
        session=session,
        dtypes=FacilityContractMappingDataFrameModel.dtypes,
        parse_dates=FacilityContractMappingDataFrameModel.parse_dates,
        error_msg='Error loading facility contracts from the database!',
    )

    return FacilityContractMappingDataFrameModel(df=df), result


def bulk_insert_facility_contracts(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk insert facility contracts into the facility_contract table.

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
        table=FacilityContract.__tablename__,
        df=df,
        required_cols={
            FacilityContractDataFrameModel.c_date_id,
            FacilityContractDataFrameModel.c_customer_type_id,
        },
    )


def bulk_update_facility_contracts(session: Session, df: pd.DataFrame) -> OperationResult:
    r"""Bulk update existing facility contracts.

    Parameters
    ----------
    conn : elsabio.db.Session
        An open session to the database.

    Returns
    -------
    elsabio.core.OperationResult
        The result of updating the existing facility contracts in the database.
    """

    return bulk_update_table(
        session=session,
        model=FacilityContract,
        df=df,
        required_cols={
            FacilityContractDataFrameModel.c_facility_id,
            FacilityContractDataFrameModel.c_date_id,
            FacilityContractDataFrameModel.c_customer_type_id,
        },
    )
