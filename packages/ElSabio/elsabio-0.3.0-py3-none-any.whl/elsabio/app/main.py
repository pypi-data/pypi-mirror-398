# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the ElSabio web app."""

# Standard library
from pathlib import Path

# Third party
import streamlit as st

# Local
from elsabio.app._pages import Pages
from elsabio.app.auth import authenticated
from elsabio.app.components import sidebar

APP_PATH = Path(__file__)


def main() -> None:
    r"""The page router of the ElSabio web app."""

    is_authenticated, user = authenticated()

    pages = [
        st.Page(page=Pages.HOME, title='Home', icon='🏡'),
        st.Page(page=Pages.SIGN_IN, title='Sign in', icon='🔑', default=True),
    ]
    page = st.navigation(pages, position='top' if is_authenticated else 'hidden')

    sidebar(is_authenticated=is_authenticated, user=user)

    page.run()


if __name__ == '__main__':
    main()
