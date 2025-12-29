# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The page controller of the sign in and register page."""

# Third party
import streamlit as st

# Local
from elsabio.app._pages import Pages
from elsabio.app.auth import BitwardenPasswordlessClient
from elsabio.app.components import (
    bitwarden_register_form,
    bitwarden_register_form_existing_user,
    bitwarden_sign_in_button,
)
from elsabio.database import Session


def controller(
    session: Session, client: BitwardenPasswordlessClient, is_authenticated: bool = False
) -> None:
    r"""Render the sign in and register page.

    Parameters
    ----------
    session : elsabio.db.Session
        An active session to the ElSabio database.

    client : elsabio.app.auth.BitwardenPasswordlessClient
        The client for interacting with the backend API of Bitwarden Passwordless.dev.

    is_authenticated : bool, default False
        True if the user is authenticated and False otherwise.
    """

    st.title('ElSabio ⚡')

    with st.container(border=True):
        if is_authenticated:
            bitwarden_register_form_existing_user(client=client, db_session=session, border=False)
            return

        bitwarden_register_form(
            client=client,
            db_session=session,
            pre_authorized=True,
            with_displayname=False,
            with_email=False,
            border=False,
            redirect=Pages.HOME,
        )
        st.write('Already have an account?')
        bitwarden_sign_in_button(
            client=client, db_session=session, with_autofill=True, redirect=Pages.HOME
        )
