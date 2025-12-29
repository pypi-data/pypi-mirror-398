# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The entry point of the sub-command `import` of the Tariff Analyzer module."""

# Third party
import click

# Local
from .facility import facility
from .facility_contract import facility_contract
from .meter_data import meter_data
from .product import product


@click.group(name='import')
def import_() -> None:
    """Import data to the ElSabio Tariff Analyzer module

    The import strategy is based on what is defined in the configuration.

    \b
    Examples
    --------
    Import the facilities:
        $ elsabio ta import facility

    \b
    Import the facility contracts:
        $ elsabio ta import facility-contract
    """


for cmd in (product, facility, facility_contract, meter_data):
    import_.add_command(cmd)
