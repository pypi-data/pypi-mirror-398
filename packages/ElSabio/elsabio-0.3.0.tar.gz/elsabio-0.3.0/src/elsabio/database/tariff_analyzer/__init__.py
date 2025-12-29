# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functionality to work with database related features of the Tariff Analyzer module."""

# Local
from .crud import (
    bulk_insert_facilities,
    bulk_insert_facility_contracts,
    bulk_insert_products,
    bulk_update_facilities,
    bulk_update_facility_contracts,
    bulk_update_products,
    load_customer_type_mapping_model,
    load_facility_contract_mapping_model,
    load_facility_mapping_model,
    load_facility_type_mapping_model,
    load_product_mapping_model,
)

# The Public API
__all__ = [
    # crud
    'bulk_insert_facilities',
    'bulk_insert_facility_contracts',
    'bulk_insert_products',
    'bulk_update_facilities',
    'bulk_update_facility_contracts',
    'bulk_update_products',
    'load_customer_type_mapping_model',
    'load_facility_contract_mapping_model',
    'load_facility_mapping_model',
    'load_facility_type_mapping_model',
    'load_product_mapping_model',
]
