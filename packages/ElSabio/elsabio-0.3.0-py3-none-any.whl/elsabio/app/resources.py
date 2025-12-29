# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Setup the resources needed by the ElSabio web app."""

# Standard library
import logging

# Third party
import streamlit as st
import streamlit_passwordless as stp

# Local
from elsabio import exceptions
from elsabio.app.components.icons import ICON_ERROR
from elsabio.config import load_config
from elsabio.database import SQLAlchemyError, create_session_factory
from elsabio.database.models import Base
from elsabio.log import setup_logging

logger = logging.getLogger(__name__)


try:
    cm = load_config()
except exceptions.ConfigError as e:
    logger.exception(str(e))
    st.error('Error loading configuration! Check the logs for more details.', icon=ICON_ERROR)
    st.stop()

setup_logging(config=cm.logging)

try:
    session_factory = create_session_factory(
        url=cm.database.url,
        autoflush=cm.database.autoflush,
        expire_on_commit=cm.database.expire_on_commit,
        create_database=True,
        base=Base,
        connect_args=cm.database.connect_args,
        **cm.database.engine_config,
    )
except SQLAlchemyError as e:
    logger.exception(f'Error creating session factory:\n{e!s}')
    st.error('Error connecting to database! Check the logs for more details.', icon=ICON_ERROR)
    st.stop()

bwp_client = stp.BitwardenPasswordlessClient(
    public_key=cm.bwp.public_key, private_key=cm.bwp.private_key
)
