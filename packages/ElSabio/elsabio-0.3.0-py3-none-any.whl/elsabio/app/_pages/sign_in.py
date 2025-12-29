# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the sign in page."""

# Third party
import streamlit as st

# Local
from elsabio.app.auth import authenticated
from elsabio.app.controllers.sign_in import controller
from elsabio.app.info import (
    APP_HOME_PAGE_URL,
    APP_ISSUES_PAGE_URL,
    MAINTAINER_INFO,
)
from elsabio.app.resources import bwp_client, session_factory

ABOUT = f"""Sign in to ElSabio or register an account.

{MAINTAINER_INFO}
"""


def sign_in_page() -> None:
    r"""Run the sign in and register page of ElSabio."""

    is_authenticated, _ = authenticated()

    st.set_page_config(
        page_title='ElSabio - Sign in',
        layout='centered',
        menu_items={
            'Get Help': APP_HOME_PAGE_URL,
            'Report a bug': APP_ISSUES_PAGE_URL,
            'About': ABOUT,
        },
        initial_sidebar_state='auto' if is_authenticated else 'collapsed',
    )

    with session_factory() as session:
        controller(session=session, client=bwp_client, is_authenticated=is_authenticated)


if __name__ in {'__main__', '__page__'}:
    sign_in_page()
