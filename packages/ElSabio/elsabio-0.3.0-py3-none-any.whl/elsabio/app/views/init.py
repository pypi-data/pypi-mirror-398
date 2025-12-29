# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The views of the init page."""

# Third party
import streamlit as st
import streamlit_passwordless as stp

# Local
from elsabio.app.components import ICON_SUCCESS, ICON_WARNING
from elsabio.database import URL, Session, init


def title() -> None:
    r"""Render the title view of the init page."""

    st.title('Initialize ElSabio')
    st.divider()


@st.cache_resource
def initialize(_session: Session, db_url: str | URL) -> None:
    r"""Render the initialize view of the init page.

    Initialize the database with the default data and
    warn the user if the database is already initialized.

    Parameters
    ----------
    session : elsabio.db.Session
        An active session to the database to initialize.

    db_url : str or elsabio.db.URL
        The database url of the database being initialized.
    """

    result = init(session=_session)

    if result.ok:
        st.success(f'Successfully initialized database : "{db_url}"!', icon=ICON_SUCCESS)
    else:
        st.warning(
            f'Database "{db_url}" already initialized! {result.short_msg}', icon=ICON_WARNING
        )

    st.divider()


def create_admin_user(session: Session) -> None:
    r"""Render the create admin user view of the init page.

    Parameters
    ----------
    session : elsabio.db.Session
        An active session to the database to initialize.
    """

    stp.create_user_form(
        db_session=session,
        with_ad_username=True,
        with_custom_roles=False,
        role_preselected=3,
        clear_on_submit=True,
        title='Create admin user',
    )
