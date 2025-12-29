# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The data models of the Tariff Analyzer module."""

# Standard library
from enum import StrEnum
from typing import ClassVar

# Local
from elsabio.models.core import BaseDataFrameModel, ColumnList, DtypeMapping


class FacilityTypeEnum(StrEnum):
    r"""The available types of facilities.

    Members
    -------
    CONSUMPTION
        A consumption facility.

    PRODUCTION
        A production facility.
    """

    CONSUMPTION = 'consumption'
    PRODUCTION = 'production'


class CustomerTypeEnum(StrEnum):
    r"""The available types of customers.

    Members
    -------
    PRIVATE_PERSON
        A private person customer.

    COMPANY
        A company customer.
    """

    PRIVATE_PERSON = 'private_person'
    COMPANY = 'company'


class CustomerGroupMappingStrategyEnum(StrEnum):
    r"""The available types of customer group mapping strategies.

    Members
    -------
    FUSE_SIZE
        Map facilities to customer groups based on their contracted fuse size.

    SUBSCRIBED_POWER
        Map facilities to customer groups based on their subscribed power.

    CONNECTION_POWER
        Map facilities to customer groups based on their connection power.

    PRODUCT
        Map facilities to customer groups based on the product of their facility contract.
    """

    FUSE_SIZE = 'fuse_size'
    SUBSCRIBED_POWER = 'subscribed_power'
    CONNECTION_POWER = 'connection_power'
    PRODUCT = 'product'


class CalcStrategyEnum(StrEnum):
    r"""The available strategies for the tariff calculations.

    Members
    -------
    PER_UNIT
        A cost per unit energy or power. E.g. SEK/kWh or SEK/kW

    PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH
        A cost per year that is periodizsed per month based on the
        length of the month in proportion to the year. E.g. SEK/year

    PER_UNIT_PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH
        A cost per unit energy or power per year that is periodizsed per month based on
        the length of the month in proportion to the year. E.g. SEK/kW/year

    ACTIVE_POWER_OVERSHOOT_SUBSCRIBED_POWER
        A cost for active power exceeding the subscribed power. E.g. SEK/kW/month

    REACTIVE_POWER_CONS_OVERSHOOT_ACTIVE_POWER_CONS
        A cost for consuming reactive power exceeding the allowed limit
        in relation to the active power consumption. E.g. SEK/kVAr/year

    REACTIVE_POWER_PROD_OVERSHOOT_ACTIVE_POWER_CONS
        A cost for producing reactive power exceeding the allowed limit
        in relation to the active power consumption. E.g. SEK/kVAr/year
    """

    PER_UNIT = 'per_unit'
    PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH = 'per_year_periodize_over_month_length'
    PER_UNIT_PER_YEAR_PERIODIZE_OVER_MONTH_LENGTH = 'per_unit_per_year_periodize_over_month_length'
    ACTIVE_POWER_OVERSHOOT_SUBSCRIBED_POWER = 'active_power_overshoot_subscribed_power'
    REACTIVE_POWER_CONS_OVERSHOOT_ACTIVE_POWER_CONS = (
        'reactive_power_cons_overshoot_active_power_cons'
    )
    REACTIVE_POWER_PROD_OVERSHOOT_ACTIVE_POWER_CONS = (
        'reactive_power_prod_overshoot_active_power_cons'
    )


class FacilityTypeMappingDataFrameModel(BaseDataFrameModel):
    r"""A model of the facility types for mapping `code` to `facility_type_id`.

    Parameters
    ----------
    facility_type_id : int
        The unique ID of the facility type.

    code : str
        The unique code of the facility type.
    """

    c_facility_type_id: ClassVar[str] = 'facility_type_id'
    c_code: ClassVar[str] = 'code'

    dtypes: ClassVar[DtypeMapping] = {
        c_facility_type_id: 'uint32[pyarrow]',
        c_code: 'string[pyarrow]',
    }


class CustomerTypeMappingDataFrameModel(BaseDataFrameModel):
    r"""A model of the customer types for mapping `code` to `customer_type_id`.

    Parameters
    ----------
    customer_type_id : int
        The unique ID of the customer type.

    code : str
        The unique code of the customer type.
    """

    c_customer_type_id: ClassVar[str] = 'customer_type_id'
    c_code: ClassVar[str] = 'code'

    dtypes: ClassVar[DtypeMapping] = {
        c_customer_type_id: 'uint32[pyarrow]',
        c_code: 'string[pyarrow]',
    }


class FacilityMappingDataFrameModel(BaseDataFrameModel):
    r"""A model of the facilities for mapping `ean` to `facility_id`.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility.

    ean : int
        The unique EAN code of the facility.
    """

    c_facility_id: ClassVar[str] = 'facility_id'
    c_ean: ClassVar[str] = 'ean'

    dtypes: ClassVar[DtypeMapping] = {c_facility_id: 'uint32[pyarrow]', c_ean: 'uint64[pyarrow]'}


class FacilityImportDataFrameModel(BaseDataFrameModel):
    r"""A model of facilities to import to the database.

    Parameters
    ----------
    ean : int
        The unique EAN code of the facility.

    ean_prod : int or None
        The EAN code of the related production facility if the facility has one.

    facility_type_code : str
        The unique code of the type of facility.

    name : str or None
        A descriptive name of the facility.

    description : str or None
        A description of the facility.
    """

    c_ean: ClassVar[str] = 'ean'
    c_ean_prod: ClassVar[str] = 'ean_prod'
    c_facility_type_code: ClassVar[str] = 'facility_type_code'
    c_name: ClassVar[str] = 'name'
    c_description: ClassVar[str] = 'description'

    dtypes: ClassVar[DtypeMapping] = {
        c_ean: 'uint64[pyarrow]',
        c_ean_prod: 'uint64[pyarrow]',
        c_facility_type_code: 'string[pyarrow]',
        c_name: 'string[pyarrow]',
        c_description: 'string[pyarrow]',
    }


class FacilityDataFrameModel(BaseDataFrameModel):
    r"""A model of the facilities represented as a DataFrame.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility.

    ean : int
        The unique EAN code of the facility.

    ean_prod : int or None
        The EAN code of the related production facility if the facility has one.

    facility_type_id : int
        The type of facility.

    name : str or None
        A descriptive name of the facility.

    description : str or None
        A description of the facility.
    """

    c_facility_id: ClassVar[str] = 'facility_id'
    c_ean: ClassVar[str] = 'ean'
    c_ean_prod: ClassVar[str] = 'ean_prod'
    c_facility_type_id: ClassVar[str] = 'facility_type_id'
    c_name: ClassVar[str] = 'name'
    c_description: ClassVar[str] = 'description'

    dtypes: ClassVar[DtypeMapping] = {
        c_facility_id: 'uint32[pyarrow]',
        c_ean: 'uint64[pyarrow]',
        c_ean_prod: 'uint64[pyarrow]',
        c_facility_type_id: 'uint8[pyarrow]',
        c_name: 'string[pyarrow]',
        c_description: 'string[pyarrow]',
    }


class ProductMappingDataFrameModel(BaseDataFrameModel):
    r"""A model of the products for mapping `external_id` to `product_id`.

    Parameters
    ----------
    product_id : int
        The unique ID of the product.

    external_id : str
        The unique ID of the product in the parent system.
    """

    c_product_id: ClassVar[str] = 'product_id'
    c_external_id: ClassVar[str] = 'external_id'

    dtypes: ClassVar[DtypeMapping] = {
        c_product_id: 'uint16[pyarrow]',
        c_external_id: 'string[pyarrow]',
    }


class ProductImportDataFrameModel(BaseDataFrameModel):
    r"""A model of products to import to the database.

    Parameters
    ----------
    external_id : str
        The unique ID of the product in the parent system.

    name : str
        The unique name of the product.

    description : str or None
        A description of the product.
    """

    c_external_id: ClassVar[str] = 'external_id'
    c_name: ClassVar[str] = 'name'
    c_description: ClassVar[str] = 'description'

    dtypes: ClassVar[DtypeMapping] = {
        c_external_id: 'string[pyarrow]',
        c_name: 'string[pyarrow]',
        c_description: 'string[pyarrow]',
    }


class ProductDataFrameModel(BaseDataFrameModel):
    r"""Products that can be associated with facility contracts.

    Parameters
    ----------
    product_id : int
        The unique ID of the product.

    external_id : str
        The unique ID of the product in the parent system.

    name : str
        The unique name of the product.

    description : str or None
        A description of the product.
    """

    c_product_id: ClassVar[str] = 'product_id'
    c_external_id: ClassVar[str] = 'external_id'
    c_name: ClassVar[str] = 'name'
    c_description: ClassVar[str] = 'description'

    dtypes: ClassVar[DtypeMapping] = {
        c_product_id: 'uint16[pyarrow]',
        c_external_id: 'string[pyarrow]',
        c_name: 'string[pyarrow]',
        c_description: 'string[pyarrow]',
    }


class FacilityContractMappingDataFrameModel(BaseDataFrameModel):
    r"""A model for determining existing facility contracts by primary key.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility.

    date_id : datetime.date
        The month the contract data is valid for represented as the first
        day of the month in the configured business timezone of the app.
    """

    c_facility_id: ClassVar[str] = 'facility_id'
    c_date_id: ClassVar[str] = 'date_id'

    dtypes: ClassVar[DtypeMapping] = {c_facility_id: 'uint32[pyarrow]'}

    parse_dates: ClassVar[ColumnList] = [c_date_id]


class FacilityContractImportDataFrameModel(BaseDataFrameModel):
    r"""Contract related information of a facility to import to the database.

    Parameters
    ----------
    ean : int
        The unique EAN code of the facility.

    date_id : datetime.date
        The month the contract data is valid for represented as the first day of the month in
        in the configured business timezone of the app.

    fuse_size : int or None
        The contracted fuse size [A].

    subscribed_power : float or None
        The subscribed power [kW].

    connection_power : float or None
        The connection power of the facility [kW].

    account_nr : int or None
        The bookkeeping account of the facility contract.

    customer_type_code : str
        The unique code of the type of customer associated with the facility contract.

    ext_product_id : int or None
        The external ID of the product that the facility contract belongs to. The ID
        is external from the perspective of ElSabio and internal to the parent system.
    """

    c_ean: ClassVar[str] = 'ean'
    c_date_id: ClassVar[str] = 'date_id'
    c_fuse_size: ClassVar[str] = 'fuse_size'
    c_subscribed_power: ClassVar[str] = 'subscribed_power'
    c_connection_power: ClassVar[str] = 'connection_power'
    c_account_nr: ClassVar[str] = 'account_nr'
    c_customer_type_code: ClassVar[str] = 'customer_type_code'
    c_ext_product_id: ClassVar[str] = 'ext_product_id'

    dtypes: ClassVar[DtypeMapping] = {
        c_ean: 'uint64[pyarrow]',
        c_fuse_size: 'uint16[pyarrow]',
        c_subscribed_power: 'float64[pyarrow]',
        c_connection_power: 'float64[pyarrow]',
        c_account_nr: 'uint16[pyarrow]',
        c_customer_type_code: 'string[pyarrow]',
        c_ext_product_id: 'string[pyarrow]',
    }
    parse_dates: ClassVar[list[str]] = [c_date_id]


class FacilityContractDataFrameModel(BaseDataFrameModel):
    r"""Contract related information of a facility valid per month.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility.

    date_id : datetime.date
        The month the contract data is valid for represented as the first day of the month in
        in the configured business timezone of the app.

    fuse_size : int or None
        The contracted fuse size [A].

    subscribed_power : float or None
        The subscribed power [kW].

    connection_power : float or None
        The connection power of the facility [kW].

    account_nr : int or None
        The bookkeeping account of the facility contract.

    customer_type_id : int
        The ID of the type of customer associated with the facility contract.

    product_id : int or None
        The ID of the product associated with the facility contract.
    """

    c_facility_id: ClassVar[str] = 'facility_id'
    c_date_id: ClassVar[str] = 'date_id'
    c_fuse_size: ClassVar[str] = 'fuse_size'
    c_subscribed_power: ClassVar[str] = 'subscribed_power'
    c_connection_power: ClassVar[str] = 'connection_power'
    c_account_nr: ClassVar[str] = 'account_nr'
    c_customer_type_id: ClassVar[str] = 'customer_type_id'
    c_product_id: ClassVar[str] = 'product_id'

    dtypes: ClassVar[DtypeMapping] = {
        c_facility_id: 'uint32[pyarrow]',
        c_fuse_size: 'uint16[pyarrow]',
        c_subscribed_power: 'float64[pyarrow]',
        c_connection_power: 'float64[pyarrow]',
        c_account_nr: 'uint16[pyarrow]',
        c_customer_type_id: 'uint16[pyarrow]',
        c_product_id: 'uint16[pyarrow]',
    }
    parse_dates: ClassVar[list[str]] = [c_date_id]


class SerieValueImportDataFrameModel(BaseDataFrameModel):
    r"""The values of a meter data serie to import to the parquet hive.

    Parameters
    ----------
    serie_type_code : str
        The unique code of the type of serie the meter data represents.

    ean : int
        The unique EAN code of the facility.

    date_id : datetime.date
        The month the meter data covers represented as the first day of the month
        in the configured business timezone of the app.

    serie_value : float
        The meter data value.

    status_id : str
        The status value of `serie_value`.
    """

    c_serie_type_code: ClassVar[str] = 'serie_type_code'
    c_ean: ClassVar[str] = 'ean'
    c_date_id: ClassVar[str] = 'date_id'
    c_serie_value: ClassVar[str] = 'serie_value'
    c_status_id: ClassVar[str] = 'status_id'

    dtypes: ClassVar[DtypeMapping] = {
        c_serie_type_code: 'string[pyarrow]',
        c_ean: 'uint64[pyarrow]',
        c_serie_value: 'float64[pyarrow]',
        c_status_id: 'string[pyarrow]',
    }

    parse_dates: ClassVar[list[str]] = [c_date_id]


class SerieValueDataFrameModel(BaseDataFrameModel):
    r"""The values of a meter data serie.

    Parameters
    ----------
    serie_type_code : str
        The unique code of the type of serie the meter data represents.

    facility_id : int
        The unique ID of the facility that the serie values belong to.

    ean : int
        The unique EAN code of the facility.

    date_id : datetime.date
        The month the meter data covers represented as the first day of the month
        in the configured business timezone of the app.

    serie_value : float
        The meter data value.

    status_id : str
        The status value of `serie_value`.
    """

    c_serie_type_code: ClassVar[str] = 'serie_type_code'
    c_facility_id: ClassVar[str] = 'facility_id'
    c_ean: ClassVar[str] = 'ean'
    c_date_id: ClassVar[str] = 'date_id'
    c_serie_value: ClassVar[str] = 'serie_value'
    c_status_id: ClassVar[str] = 'status_id'

    dtypes: ClassVar[DtypeMapping] = {
        c_serie_type_code: 'string[pyarrow]',
        c_facility_id: 'uint32[pyarrow]',
        c_ean: 'uint64[pyarrow]',
        c_serie_value: 'float64[pyarrow]',
        c_status_id: 'string[pyarrow]',
    }

    parse_dates: ClassVar[list[str]] = [c_date_id]
