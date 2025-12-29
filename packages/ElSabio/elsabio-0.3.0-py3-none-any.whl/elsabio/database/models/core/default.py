# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The default data of the core tables."""

# Local

from elsabio.database.core import Session
from elsabio.models.core import SerieTypeEnum

from .models import Currency, SerieType, Unit

# Currency
default_currencies = (
    {
        'iso_code': 'SEK',
        'name': 'Svenska enkronor',
        'minor_unit_name': 'öre',
        'minor_per_major': 100,
        'display_decimals': 2,
        'symbol': 'kr',
        'symbol_minor_unit': None,
    },
    {
        'iso_code': 'EUR',
        'name': 'Euro',
        'minor_unit_name': 'euro cent',
        'minor_per_major': 100,
        'display_decimals': 2,
        'symbol': '€',
        'symbol_minor_unit': 'c',
    },
)

# Unit
default_units = (
    # Energy units
    {'code': 'kWh', 'display_name': 'kWh', 'description': 'kilo Watt hour'},
    {'code': 'kVArh', 'display_name': 'kVArh', 'description': 'kilo Volt Ampere reactive hour'},
    {'code': 'kVAh', 'display_name': 'kVAh', 'description': 'kilo Volt Ampere hour'},
    {'code': 'MWh', 'display_name': 'MWh', 'description': 'Mega Watt hour'},
    {'code': 'MVArh', 'display_name': 'MVArh', 'description': 'Mega Volt Ampere reactive hour'},
    {'code': 'MVAh', 'display_name': 'MVAh', 'description': 'Mega Volt Ampere hour'},
    {'code': 'GWh', 'display_name': 'GWh', 'description': 'Giga Watt hour'},
    {'code': 'GVArh', 'display_name': 'GVArh', 'description': 'Giga Volt Ampere reactive hour'},
    {'code': 'GVAh', 'display_name': 'GVAh', 'description': 'Giga Volt Ampere hour'},
    {'code': 'TWh', 'display_name': 'TWh', 'description': 'Terra Watt hour'},
    {'code': 'TVArh', 'display_name': 'TVArh', 'description': 'Terra Volt Ampere reactive hour'},
    {'code': 'TVAh', 'display_name': 'TVAh', 'description': 'Terra Volt Ampere hour'},
    # Power units
    {'code': 'kW', 'display_name': 'kW', 'description': 'kilo Watt'},
    {'code': 'kVAr', 'display_name': 'kVAr', 'description': 'kilo Volt Ampere reactive'},
    {'code': 'kVA', 'display_name': 'kVA', 'description': 'kilo Volt Ampere'},
    {'code': 'MW', 'display_name': 'MW', 'description': 'Mega Watt'},
    {'code': 'MVAr', 'display_name': 'MVAr', 'description': 'Mega Volt Ampere reactive'},
    {'code': 'MVA', 'display_name': 'MVA', 'description': 'Mega Volt Ampere'},
    {'code': 'GW', 'display_name': 'GW', 'description': 'Giga Watt'},
    {'code': 'GVAr', 'display_name': 'GVAr', 'description': 'Giga Volt Ampere reactive'},
    {'code': 'GVA', 'display_name': 'GVA', 'description': 'Giga Volt Ampere'},
    {'code': 'TW', 'display_name': 'TW', 'description': 'Terra Watt'},
    {'code': 'TVAr', 'display_name': 'TVAr', 'description': 'Terra Volt Ampere reactive'},
    {'code': 'TVA', 'display_name': 'TVA', 'description': 'Terra Volt Ampere'},
    # Temperature
    {'code': 'degrees_celsius', 'display_name': '°C', 'description': 'Degrees Celsius'},
    # Per-time units
    {'code': 'per_month', 'display_name': '/month', 'description': 'A unit per month.'},
    {'code': 'per_year', 'display_name': '/year', 'description': 'A unit per year.'},
    # Per energy/power units
    {'code': 'per_kWh', 'display_name': '/kWh', 'description': 'A unit per kilo Watt hour.'},
    {
        'code': 'per_kVArh',
        'display_name': '/kVArh',
        'description': 'A unit per kilo Volt Ampere reactive hour.',
    },
    {
        'code': 'per_kW_per_month',
        'display_name': '/kW/month',
        'description': 'A unit per kilo Watt per month.',
    },
    {
        'code': 'per_kVAr_per_month',
        'display_name': '/kVAr/month',
        'description': 'A unit per kilo Volt Ampere reactive per month.',
    },
    {
        'code': 'per_kW_per_year',
        'display_name': 'kW/year',
        'description': 'A unit per kilo Watt per year.',
    },
    {
        'code': 'per_kVAr_per_year',
        'display_name': '/kVAr/year',
        'description': 'A unit per kilo Volt Ampere reactive per year.',
    },
)

# SerieType
default_serie_types = (
    {'code': SerieTypeEnum.ACTIVE_ENERGY_CONS, 'name': 'Active Energy Consumption'},
    {'code': SerieTypeEnum.ACTIVE_ENERGY_PROD, 'name': 'Active Energy Production'},
    {'code': SerieTypeEnum.REACTIVE_ENERGY_CONS, 'name': 'Reactive Energy Consumption'},
    {'code': SerieTypeEnum.REACTIVE_ENERGY_PROD, 'name': 'Reactive Energy Production'},
    {'code': SerieTypeEnum.APPARENT_ENERGY_CONS, 'name': 'Apparent Energy Consumption'},
    {'code': SerieTypeEnum.APPARENT_ENERGY_PROD, 'name': 'Apparent Energy Production'},
    {'code': SerieTypeEnum.ACTIVE_POWER_CONS, 'name': 'Active Power Consumption'},
    {'code': SerieTypeEnum.ACTIVE_POWER_PROD, 'name': 'Active Power Production'},
    {'code': SerieTypeEnum.REACTIVE_POWER_CONS, 'name': 'Reactive Power Consumption'},
    {'code': SerieTypeEnum.REACTIVE_POWER_PROD, 'name': 'Reactive Power Production'},
    {'code': SerieTypeEnum.APPARENT_POWER_CONS, 'name': 'Apparent Power Consumption'},
    {'code': SerieTypeEnum.APPARENT_POWER_PROD, 'name': 'Apparent Power Production'},
    {'code': SerieTypeEnum.MAX_ACTIVE_POWER_CONS, 'name': 'Max Active Power Consumption'},
    {'code': SerieTypeEnum.MAX_ACTIVE_POWER_PROD, 'name': 'Max Active Power Production'},
    {'code': SerieTypeEnum.MAX_REACTIVE_POWER_CONS, 'name': 'Max Reactive Power Consumption'},
    {'code': SerieTypeEnum.MAX_REACTIVE_POWER_PROD, 'name': 'Max Reactive Power Production'},
    {'code': SerieTypeEnum.MAX_APPARENT_POWER_CONS, 'name': 'Max Apparent Power Consumption'},
    {'code': SerieTypeEnum.MAX_APPARENT_POWER_PROD, 'name': 'Max Apparent Power Production'},
    {
        'code': SerieTypeEnum.MAX_DEB_ACTIVE_POWER_CONS_HIGH_LOAD,
        'name': 'Max Debitable Active Power Consumption High Load',
    },
    {
        'code': SerieTypeEnum.MAX_DEB_ACTIVE_POWER_CONS_LOW_LOAD,
        'name': 'Max Debitable Active Power Consumption Low Load',
    },
)


def add_default_core_models_to_session(session: Session) -> None:
    r"""Add the default core models to the database.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.
    """

    session.add_all(Currency(**item) for item in default_currencies)
    session.add_all(Unit(**item) for item in default_units)
    session.add_all(SerieType(**item) for item in default_serie_types)
