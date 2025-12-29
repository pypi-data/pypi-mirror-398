# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The default data of the Tariff Analyzer module."""

# Local
from elsabio.database.core import Session
from elsabio.models.tariff_analyzer import (
    CalcStrategyEnum,
    CustomerGroupMappingStrategyEnum,
    CustomerTypeEnum,
    FacilityTypeEnum,
)

from .models import CalcStrategy, CustomerGroupMappingStrategy, CustomerType, FacilityType

# FacilityType
default_facility_types = (
    {
        'code': FacilityTypeEnum.CONSUMPTION,
        'name': 'Consumption',
        'description': 'A consumption facility.',
    },
    {
        'code': FacilityTypeEnum.PRODUCTION,
        'name': 'Production',
        'description': 'A production facility.',
    },
)

# CustomerType
default_customer_types = (
    {
        'code': CustomerTypeEnum.PRIVATE_PERSON,
        'name': 'Private person',
        'description': 'A private person customer.',
    },
    {
        'code': CustomerTypeEnum.COMPANY,
        'name': 'Company',
        'description': 'A company customer.',
    },
)

# CustomerGroupMappingStrategy
default_customer_group_mapping_strategies = (
    {
        'code': CustomerGroupMappingStrategyEnum.FUSE_SIZE,
        'name': 'Fuse Size',
        'description': 'Map facilities to customer groups based on their contracted fuse size.',
    },
    {
        'code': CustomerGroupMappingStrategyEnum.SUBSCRIBED_POWER,
        'name': 'Subscribed Power',
        'description': 'Map facilities to customer groups based on their subscribed power.',
    },
    {
        'code': CustomerGroupMappingStrategyEnum.CONNECTION_POWER,
        'name': 'Connection Power',
        'description': 'Map facilities to customer groups based on their connection power.',
    },
    {
        'code': CustomerGroupMappingStrategyEnum.PRODUCT,
        'name': 'Product',
        'description': (
            'Map facilities to customer groups based on the product of their facility contract.'
        ),
    },
)

# CalcStrategy
default_calc_strategies = (
    {
        'code': CalcStrategyEnum.PER_UNIT,
        'name': 'Per Unit',
        'description': 'A cost per unit energy or power. E.g. SEK/kWh or SEK/kW',
    },
    {
        'code': CalcStrategyEnum.PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH,
        'name': 'Per Year Periodize Over Month Length',
        'description': (
            'A cost per year that is periodizsed per month based on '
            'the length of the month in proportion to the year. E.g. SEK/year'
        ),
    },
    {
        'code': CalcStrategyEnum.PER_UNIT_PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH,
        'name': 'Per Unit Per Year Periodize Over Month Length',
        'description': (
            'A cost per unit energy or power per year that is periodizsed per month based on '
            'the length of the month in proportion to the year. E.g. SEK/kW/year'
        ),
    },
    {
        'code': CalcStrategyEnum.ACTIVE_POWER_OVERSHOOT_SUBSCRIBED_POWER,
        'name': 'Active Power Overshoot Subscribed Power',
        'description': (
            'A cost for active power exceeding the subscribed power. E.g. SEK/kW/month'
        ),
    },
    {
        'code': CalcStrategyEnum.REACTIVE_POWER_CONS_OVERSHOOT_ACTIVE_POWER_CONS,
        'name': 'Reactive Power Consumption Overshoot Active Power Consumption',
        'description': (
            'A cost for consuming reactive power exceeding the allowed limit '
            'in relation to the active power consumption. E.g. SEK/kVAr/year'
        ),
    },
    {
        'code': CalcStrategyEnum.REACTIVE_POWER_PROD_OVERSHOOT_ACTIVE_POWER_CONS,
        'name': 'Reactive Power Production Overshoot Active Power Consumption',
        'description': (
            'A cost for producing reactive power exceeding the allowed limit '
            'in relation to the active power consumption. E.g. SEK/kVAr/year'
        ),
    },
)


def add_default_tariff_analyzer_models_to_session(session: Session) -> None:
    r"""Add the default Tariff Analyzer models to the database.

    Parameters
    ----------
    session : elsabio.db.Session
        An active database session.
    """

    session.add_all(FacilityType(**item) for item in default_facility_types)
    session.add_all(CustomerType(**item) for item in default_customer_types)
    session.add_all(
        CustomerGroupMappingStrategy(**item) for item in default_customer_group_mapping_strategies
    )
    session.add_all(CalcStrategy(**item) for item in default_calc_strategies)
