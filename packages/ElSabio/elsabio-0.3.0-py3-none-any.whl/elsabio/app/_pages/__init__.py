# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The pages of the ElSabio web app."""

# Standard library
from enum import StrEnum


class Pages(StrEnum):
    r"""The pages of the application."""

    INIT = '_pages/init.py'
    HOME = '_pages/home.py'
    SIGN_IN = '_pages/sign_in.py'
