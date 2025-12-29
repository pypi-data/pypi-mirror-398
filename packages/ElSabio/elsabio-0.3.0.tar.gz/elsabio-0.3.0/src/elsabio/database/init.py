# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Initialize a database with the default data."""

# Local
from elsabio.core import OperationResult
from elsabio.database.core import Session, commit, create_default_roles
from elsabio.database.models import add_default_core_models_to_session
from elsabio.database.models.tariff_analyzer import add_default_tariff_analyzer_models_to_session


def init(session: Session) -> OperationResult:
    r"""Initialize a database with the default data.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.

    Returns
    -------
    result : elsabio.OperationResult
        The result of initializing the database.
    """

    create_default_roles(session=session, commit=False)
    add_default_core_models_to_session(session=session)
    add_default_tariff_analyzer_models_to_session(session=session)

    return commit(session=session, error_msg='Error initializing database!')
