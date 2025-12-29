# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The database of ElSabio."""

# Local
from . import models
from .core import (
    URL,
    Session,
    SessionFactory,
    SQLAlchemyError,
    SQLQuery,
    bulk_insert_to_table,
    bulk_update_table,
    commit,
    create_default_roles,
    create_session_factory,
    load_sql_query_as_dataframe,
    make_url,
)
from .init import init

# The Public API
__all__ = [
    # core
    'URL',
    'Session',
    'SessionFactory',
    'SQLAlchemyError',
    'SQLQuery',
    'bulk_insert_to_table',
    'bulk_update_table',
    'commit',
    'create_default_roles',
    'create_session_factory',
    'load_sql_query_as_dataframe',
    'make_url',
    # init
    'init',
    # models
    'models',
]
