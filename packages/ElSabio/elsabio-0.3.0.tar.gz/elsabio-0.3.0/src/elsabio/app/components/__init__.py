# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The components that make up the web app."""

# Local
from elsabio.app.components.buttons import bitwarden_sign_in_button, sign_out_button
from elsabio.app.components.forms import (
    bitwarden_register_form,
    bitwarden_register_form_existing_user,
)
from elsabio.app.components.icons import ICON_ERROR, ICON_INFO, ICON_SUCCESS, ICON_WARNING
from elsabio.app.components.sidebar import sidebar
from elsabio.app.components.text import user_info_text

# The Public API
__all__ = [
    # buttons
    'bitwarden_sign_in_button',
    'sign_out_button',
    # forms
    'bitwarden_register_form',
    'bitwarden_register_form_existing_user',
    # icons
    'ICON_ERROR',
    'ICON_INFO',
    'ICON_SUCCESS',
    'ICON_WARNING',
    # sidebar
    'sidebar',
    # text
    'user_info_text',
]
