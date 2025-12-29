# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the initialization page."""

# Third party
import streamlit as st

# Local
from elsabio.app.controllers.init import controller
from elsabio.app.info import APP_HOME_PAGE_URL, APP_ISSUES_PAGE_URL, MAINTAINER_INFO
from elsabio.app.resources import cm, session_factory

ABOUT = f"""Initialize the database of ElSabio and create an admin user.

{MAINTAINER_INFO}
"""


def init_page() -> None:
    r"""Run the initialization page of ElSabio."""

    st.set_page_config(
        page_title='ElSabio - Initialize',
        page_icon=':sparkles:',
        layout='wide',
        menu_items={
            'Get Help': APP_HOME_PAGE_URL,
            'Report a bug': APP_ISSUES_PAGE_URL,
            'About': ABOUT,
        },
    )

    with session_factory() as session:
        controller(session=session, db_url=cm.database.url)


if __name__ in {'__main__', '__page__'}:
    init_page()
