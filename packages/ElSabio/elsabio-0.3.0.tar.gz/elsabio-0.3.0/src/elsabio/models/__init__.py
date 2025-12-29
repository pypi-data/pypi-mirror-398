# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The data models of ElSabio."""

from .core import SerieTypeMappingDataFrameModel, User

# The Public API
__all__ = [
    # core
    'SerieTypeMappingDataFrameModel',
    'User',
]
