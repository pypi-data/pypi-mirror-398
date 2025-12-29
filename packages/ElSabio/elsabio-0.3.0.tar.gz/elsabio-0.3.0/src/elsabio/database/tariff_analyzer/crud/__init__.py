# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""Functions to perform CREATE, READ, UPDATE and DELETE operations for Tariff Analyzer."""

# Local
from .customer_type import load_customer_type_mapping_model
from .facility import bulk_insert_facilities, bulk_update_facilities, load_facility_mapping_model
from .facility_contract import (
    bulk_insert_facility_contracts,
    bulk_update_facility_contracts,
    load_facility_contract_mapping_model,
)
from .facility_type import load_facility_type_mapping_model
from .product import bulk_insert_products, bulk_update_products, load_product_mapping_model

# The Public API
__all__ = [
    # customer_type
    'load_customer_type_mapping_model',
    # facility
    'bulk_insert_facilities',
    'bulk_update_facilities',
    'load_facility_mapping_model',
    # facility_contract
    'bulk_insert_facility_contracts',
    'bulk_update_facility_contracts',
    'load_facility_contract_mapping_model',
    # facility_type
    'load_facility_type_mapping_model',
    # product
    'bulk_insert_products',
    'bulk_update_products',
    'load_product_mapping_model',
]
