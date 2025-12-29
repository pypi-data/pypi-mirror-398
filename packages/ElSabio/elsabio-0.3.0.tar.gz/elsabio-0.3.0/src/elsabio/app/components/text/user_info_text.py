# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The user info text component."""

# Standard library
from zoneinfo import ZoneInfo

# Third party
import streamlit as st

# Local
from elsabio.models import User


def user_info_text(user: User) -> None:
    r"""Display info about the signed in user."""

    if (sign_in := user.sign_in) is None:
        passkey_nickname = ''
        sign_in_timestamp = ''
    else:
        passkey_nickname = sign_in.credential_nickname
        target_tz = tz if (tz := st.context.timezone) else 'UTC'
        sign_in_timestamp = sign_in.sign_in_timestamp.astimezone(tz=ZoneInfo(target_tz)).isoformat(
            sep=' ', timespec='seconds'
        )

    user_info = f"""\
## Welcome 👋
👨🏻‍💻 **User :**         {user.displayname}  
🔑 **Passkey :**      {passkey_nickname}  
🕑 **Signed in at :** {sign_in_timestamp}
"""  # noqa: W291

    st.markdown(user_info)
