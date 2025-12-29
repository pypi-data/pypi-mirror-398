# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Sidebar components."""

# Third party
import streamlit as st

# Local
from elsabio.app.components.buttons import sign_out_button
from elsabio.app.components.text import user_info_text
from elsabio.models import User


def sidebar(is_authenticated: bool, user: User | None = None) -> None:
    r"""Render the sidebar.

    Parameters
    ----------
    is_authenticated : bool
        True if the `user` is authenticated and False otherwise.

    user : elsabio.models.User or None, default None
        The user accessing the application. If None the user is not signed in yet.
    """

    if not is_authenticated or user is None:
        return

    with st.sidebar:
        user_info_text(user=user)
        st.divider()
        sign_out_button(user=user)
