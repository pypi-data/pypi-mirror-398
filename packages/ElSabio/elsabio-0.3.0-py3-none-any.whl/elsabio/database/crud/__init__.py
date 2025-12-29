# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions to perform CREATE, READ, UPDATE and DELETE operations on the core database models."""

# Local
from .serie_type import load_serie_type_mapping_model

# The Public API
__all__ = [
    # serie_type
    'load_serie_type_mapping_model',
]
