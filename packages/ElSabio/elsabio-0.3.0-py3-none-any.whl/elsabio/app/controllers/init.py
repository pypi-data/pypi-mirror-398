# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The controller of the init page."""

# Local
from elsabio.app.views.init import create_admin_user, initialize, title
from elsabio.database import URL, Session


def controller(session: Session, db_url: str | URL) -> None:
    r"""Render the initialization page.

    Parameters
    ----------
    session : elsabio.db.Session
        An active session to the ElSabio database.

    db_url : str or elsabio.db.URL
        The database url of the database to initialize.
    """

    title()
    initialize(_session=session, db_url=db_url)
    create_admin_user(session=session)
