# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""User authentication and authorization."""

# Third party
from streamlit_passwordless import AdminRole as AdminRole
from streamlit_passwordless import BitwardenPasswordlessClient as BitwardenPasswordlessClient
from streamlit_passwordless import SuperUserRole as SuperUserRole
from streamlit_passwordless import UserRole as UserRole
from streamlit_passwordless import ViewerRole as ViewerRole
from streamlit_passwordless import authenticated as authenticated
from streamlit_passwordless import authorized as authorized
from streamlit_passwordless import get_current_user as get_current_user
