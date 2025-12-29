# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the Tariff Analyzer module command `ta`."""

# Third party
import click

# Local
from .import_.import_ import import_


@click.group(name='ta')
def tariff_analyzer() -> None:
    r"""Manage the Tariff Analyzer module"""


for cmd in (import_,):
    tariff_analyzer.add_command(cmd)
