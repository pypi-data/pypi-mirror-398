# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The core functionality of the business logic of the Tariff Analyzer module."""

# Standard library
from typing import NamedTuple

# Third party
import pandas as pd


class UpsertDataFrames(NamedTuple):
    r"""The DataFrames with database records to insert or update.

    Parameters
    ----------
    insert : pandas.DataFrame
        The new records to insert.

    update : pandas.DataFrame
        The existing records to update.

    invalid : pandas.DataFrame
        The records with invalid or missing data.
    """

    insert: pd.DataFrame
    update: pd.DataFrame
    invalid: pd.DataFrame
