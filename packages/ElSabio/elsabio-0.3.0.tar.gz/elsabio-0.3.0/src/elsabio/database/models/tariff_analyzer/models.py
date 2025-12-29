# ElSabio
# Copyright (C) 2025-present Anton Lydell
# SPDX-License-Identifier: GPL-3.0-or-later
# See the LICENSE file in the project root for details.

r"""The database tables of the Tariff Analyzer module."""

# Standard library
from datetime import date, datetime
from decimal import Decimal
from typing import ClassVar
from uuid import UUID

# Third party
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import true

# Local
from elsabio.database.models.core import (
    AuditColumnsMixin,
    Base,
    Currency,
    MoneyPrice,
    Ratio,
    SerieType,
    Unit,
)


class FacilityType(AuditColumnsMixin, Base):
    r"""The type of an electricity facility.

    Parameters
    ----------
    facility_type_id : int
        The unique ID of the facility type. The primary key of the table.

    code : str
        The unique code of the facility type. Is indexed. Max length of 64 characters.

    name : str or None
        A descriptive name of the facility type.

    description : str or None
        A description of the facility type.

    updated_at : datetime.datetime or None
        The timestamp at which the facility type was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the facility type.

    created_at : datetime.datetime
        The timestamp at which the facility type was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the facility type.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'facility_type_id',
        'code',
        'name',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_facility_type'

    facility_type_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str | None]
    description: Mapped[str | None]

    facilities: Mapped[list['Facility']] = relationship(back_populates='facility_type')
    customer_groups: Mapped[list['CustomerGroup']] = relationship(back_populates='facility_type')


class CustomerType(AuditColumnsMixin, Base):
    r"""The type of customer associated with a facility contract.

    Parameters
    ----------
    customer_type_id : int
        The unique ID of the customer type. The primary key of the table.

    code : str
        The unique code of the customer type. Is indexed. Max length of 64 characters.

    name : str or None
        A descriptive name of the customer type.

    description : str or None
        A description of the customer type.

    updated_at : datetime.datetime or None
        The timestamp at which the customer type was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the customer type.

    created_at : datetime.datetime
        The timestamp at which the customer type was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the customer type.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'customer_type_id',
        'code',
        'name',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_customer_type'

    customer_type_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str | None]
    description: Mapped[str | None]

    facility_contracts: Mapped[list['FacilityContract']] = relationship(
        back_populates='customer_type'
    )


class Product(AuditColumnsMixin, Base):
    r"""A product that can be associated with a facility contract.

    Parameters
    ----------
    product_id : int
        The unique ID of the product. The primary key of the table.

    external_id : str
        The unique ID of the product in the parent system. Is indexed.
        Max length of 150 characters.

    name : str
        The unique name of the product. Is indexed. Max length of 150 characters.

    description : str or None
        A description of the product.

    updated_at : datetime.datetime or None
        The timestamp at which the product was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the product.

    created_at : datetime.datetime
        The timestamp at which the product was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the product.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'product_id',
        'external_id',
        'name',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_product'

    product_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    external_id: Mapped[str] = mapped_column(String(150), unique=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str | None]

    facility_contracts: Mapped[list['FacilityContract']] = relationship(back_populates='product')
    customer_groups: Mapped[list['CustomerGroup']] = relationship(back_populates='product')


class Facility(AuditColumnsMixin, Base):
    r"""A facility where electricity is delivered as part of a grid contract.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility. The primary key of the table.

    ean : int
        The unique EAN code of the facility. Must be unique. Is indexed.

    ean_prod : int or None
        The unique EAN code of the related production facility if the facility has one. Is indexed.

    facility_type_id : int
        The type of facility. Foreign key to :attr:`FacilityType.facility_type_id`. Is indexed.

    name : str or None
        A descriptive name of the facility.

    description : str or None
        A description of the facility.

    updated_at : datetime.datetime or None
        The timestamp at which the facility was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the facility.

    created_at : datetime.datetime
        The timestamp at which the facility was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the facility.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'facility_id',
        'ean',
        'ean_prod',
        'facility_type_id',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_facility'

    facility_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    ean: Mapped[int] = mapped_column(BigInteger(), unique=True)
    ean_prod: Mapped[int | None] = mapped_column(BigInteger())
    facility_type_id: Mapped[int] = mapped_column(
        ForeignKey(FacilityType.facility_type_id), server_default=text('0')
    )
    name: Mapped[str | None]
    description: Mapped[str | None]

    facility_type: Mapped[FacilityType] = relationship(back_populates='facilities')
    facility_contracts: Mapped[list['FacilityContract']] = relationship(
        back_populates='facility',
        cascade='all, delete-orphan',
        single_parent=True,
        passive_deletes=True,
        order_by='FacilityContract.date_id',
    )
    facility_customer_group_links: Mapped[list['FacilityCustomerGroupLink']] = relationship(
        back_populates='facility',
        cascade='all, delete-orphan',
        single_parent=True,
        passive_deletes=True,
        order_by='FacilityCustomerGroupLink.date_id',
    )


Index(f'{Facility.__tablename__}_ean_prod_ix', Facility.ean_prod)


class FacilityContract(AuditColumnsMixin, Base):
    r"""Contract related information of a facility valid per month.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility. Part of the primary key of the table.
        Foreign key to :attr:`Facility.facility_id`.

    date_id : datetime.date
        The month the contract data is valid for represented as the first day of the month in
        the configured business timezone of the app. Part of the primary key of the table.

    fuse_size : int or None
        The contracted fuse size [A].

    subscribed_power : float or None
        The subscribed active power of the facility [kW].

    connection_power : float or None
        The connection power of the facility [kW].

    account_nr : int or None
        The bookkeeping account of the facility contract.

    customer_type_id : int
        The ID of the type of customer associated with the facility contract. Is indexed.
        Foreign key to :attr:`CustomerType.customer_type_id`.

    product_id : int or None
        The ID of the product associated with the facility contract. Is indexed.
        Foreign key to :attr:`Product.product_id`.

    updated_at : datetime.datetime or None
        The timestamp at which the facility contract was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the facility contract.

    created_at : datetime.datetime
        The timestamp at which the facility contract was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the facility contract.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'facility_id',
        'date_id',
        'fuse_size',
        'subscribed_power',
        'connection_power',
        'account_nr',
        'customer_type_id',
        'product_id',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_facility_contract'

    facility_id: Mapped[int] = mapped_column(
        ForeignKey(Facility.facility_id, ondelete='CASCADE'), primary_key=True
    )
    date_id: Mapped[date] = mapped_column(
        primary_key=True,
        comment=(
            'The month the contract data is valid for represented as the first day of the month in '
            'the configured business timezone of the app. Part of the primary key of the table.'
        ),
    )
    fuse_size: Mapped[int | None]
    subscribed_power: Mapped[float | None]
    connection_power: Mapped[float | None]
    account_nr: Mapped[int | None]
    customer_type_id: Mapped[int] = mapped_column(ForeignKey(CustomerType.customer_type_id))
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey(Product.product_id, ondelete='SET NULL')
    )

    facility: Mapped[Facility] = relationship(back_populates='facility_contracts')
    customer_type: Mapped[CustomerType] = relationship(back_populates='facility_contracts')
    product: Mapped[Product] = relationship(back_populates='facility_contracts')

    __table_args__ = (
        CheckConstraint(func.extract('day', date_id) == 1, name='ck_fc_date_id_first_of_month'),
    )


Index(
    f'{FacilityContract.__tablename__}_date_id__facility_id_ix',
    FacilityContract.date_id,
    FacilityContract.facility_id,
)
Index(f'{FacilityContract.__tablename__}_customer_type_id_ix', FacilityContract.customer_type_id)
Index(f'{FacilityContract.__tablename__}_product_id_ix', FacilityContract.product_id)


class CustomerGroupMappingStrategy(AuditColumnsMixin, Base):
    r"""The strategies for how to associate facilities with customer groups.

    Parameters
    ----------
    mapping_strategy_id : int
        The unique ID of the customer group mapping strategy. The primary key of the table.

    code : str
        The unique code of the customer group mapping strategy. Is indexed.
        Max length of 64 characters.

    name : str or None
        A descriptive name of the customer group mapping strategy.

    description : str or None
        A description of the customer group mapping strategy.

    updated_at : datetime.datetime or None
        The timestamp at which the customer group mapping strategy was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the customer group mapping strategy.

    created_at : datetime.datetime
        The timestamp at which the customer group mapping strategy was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the customer group mapping strategy.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'mapping_strategy_id',
        'code',
        'name',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_customer_group_mapping_strategy'

    mapping_strategy_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str | None]
    description: Mapped[str | None]

    customer_groups: Mapped[list['CustomerGroup']] = relationship(back_populates='mapping_strategy')


class CustomerGroup(AuditColumnsMixin, Base):
    r"""A facility is part of a customer group based on its facility contract information.

    Parameters
    ----------
    customer_group_id : int
       The unique ID of the customer group. The primary key of the table.

    name : str
        The unique name of the customer group. Is indexed. Max length of 150 characters.

    min_fuse_size : int or None
        The minimum fuse size [A] of the customer group.

    max_fuse_size : int or None
        The maximum fuse size [A] of the customer group.

    min_subscribed_power : float or None
        The minimum subscribed power of the customer group [kW].

    max_subscribed_power : float or None
        The maximum subscribed power of the customer group [kW].

    min_connection_power : float or None
        The minimum connection power of the customer group [kW].

    max_connection_power : float or None
        The maximum connection power of the customer group [kW].

    min_bound_included : bool, default True
        True if the minimum bound is included in the range when applying the customer
        group mapping strategy from `mapping_strategy_id` and False to exclude it.

    max_bound_included : bool, default True
        True if the maximum bound is included in the range when applying the customer
        group mapping strategy from `mapping_strategy_id` and False to exclude it.

    facility_type_id : int
        The type of facility that can be associated with the customer group.
        Foreign key to :attr:`FacilityType.facility_type_id`. Is indexed.

    product_id : int or None
        The product of a facility contract associated with the customer group. Used
        for mapping facilities to a customer group based on the product of a facility
        contract. Is indexed. Foreign key to :attr:`Product.product_id`.

    mapping_strategy_id : int
        The ID of the customer group mapping strategy to apply to map facilities to the customer
        group. Is indexed. Foreign key to :attr:`CustomerGroupMappingStrategy.mapping_strategy_id`.

    description : str or None
        A description of the customer group.

    updated_at : datetime.datetime or None
        The timestamp at which the customer group was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the customer group.

    created_at : datetime.datetime
        The timestamp at which the customer group was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the customer group.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'customer_group_id',
        'name',
        'min_fuse_size',
        'max_fuse_size',
        'min_subscribed_power',
        'max_subscribed_power',
        'min_connection_power',
        'max_connection_power',
        'min_bound_included',
        'max_bound_included',
        'facility_type_id',
        'product_id',
        'mapping_strategy_id',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_customer_group'

    customer_group_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    min_fuse_size: Mapped[int | None]
    max_fuse_size: Mapped[int | None]
    min_subscribed_power: Mapped[float | None]
    max_subscribed_power: Mapped[float | None]
    min_connection_power: Mapped[float | None]
    max_connection_power: Mapped[float | None]
    min_bound_included: Mapped[bool] = mapped_column(server_default=true())
    max_bound_included: Mapped[bool] = mapped_column(server_default=true())
    facility_type_id: Mapped[int] = mapped_column(ForeignKey(FacilityType.facility_type_id))
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey(Product.product_id, ondelete='SET NULL')
    )
    mapping_strategy_id: Mapped[int] = mapped_column(
        ForeignKey(CustomerGroupMappingStrategy.mapping_strategy_id)
    )
    description: Mapped[str | None]

    facility_customer_group_links: Mapped[list['FacilityCustomerGroupLink']] = relationship(
        back_populates='customer_group', passive_deletes=True
    )
    tariff_cost_group_customer_group_links: Mapped[list['TariffCostGroupCustomerGroupLink']] = (
        relationship(back_populates='customer_group', passive_deletes=True)
    )
    facility_type: Mapped[FacilityType] = relationship(back_populates='customer_groups')
    product: Mapped[Product] = relationship(back_populates='customer_groups')
    mapping_strategy: Mapped[CustomerGroupMappingStrategy] = relationship(
        back_populates='customer_groups'
    )


Index(f'{CustomerGroup.__tablename__}_facility_type_id_ix', CustomerGroup.facility_type_id)
Index(f'{CustomerGroup.__tablename__}_product_id_ix', CustomerGroup.product_id)
Index(f'{CustomerGroup.__tablename__}_mapping_strategy_id_ix', CustomerGroup.mapping_strategy_id)


class FacilityCustomerGroupLink(AuditColumnsMixin, Base):
    r"""The link between a facility and customer group.

    Parameters
    ----------
    facility_id : int
        The unique ID of the facility. Part of the primary key.
        Foreign key to :attr:`Facility.facility_id`. Is indexed.

    date_id : datetime.date
        The month the link is valid for represented as the first day of the month in the
        configured business timezone of the app. Part of the primary key.

    customer_group_id : int
        The unique ID of the customer group the facility is part of.
        Foreign key to :attr:`CustomerGroup.customer_group_id`. Is indexed.

    updated_at : datetime.datetime or None
        The timestamp at which the facility customer group link was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the facility customer group link.

    created_at : datetime.datetime
        The timestamp at which the facility customer group link was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the facility customer group link.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'facility_id',
        'date_id',
        'customer_group_id',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_facility_customer_group_link'

    facility_id: Mapped[int] = mapped_column(
        ForeignKey(Facility.facility_id, ondelete='CASCADE'), primary_key=True
    )
    date_id: Mapped[datetime] = mapped_column(
        Date,
        primary_key=True,
        comment=(
            'The month the link is valid for represented as the first day of the '
            'month in the configured business timezone of the app.'
        ),
    )
    customer_group_id: Mapped[int] = mapped_column(
        ForeignKey(CustomerGroup.customer_group_id, ondelete='CASCADE')
    )

    facility: Mapped[Facility] = relationship(back_populates='facility_customer_group_links')
    customer_group: Mapped[CustomerGroup] = relationship(
        back_populates='facility_customer_group_links'
    )

    __table_args__ = (
        CheckConstraint(
            func.extract('day', date_id) == 1, name='ck_fcg_link_date_id_first_of_month'
        ),
    )


Index(
    'ta_facility_cg_link_ts_id__cg_id_ix',
    FacilityCustomerGroupLink.date_id,
    FacilityCustomerGroupLink.customer_group_id,
)


class Tariff(AuditColumnsMixin, Base):
    r"""An electricity tariff.

    Parameters
    ----------
    tariff_id : int
        The unique ID of the tariff. The primary key of the table.

    name : str
        The unique name of the tariff. Is indexed. Max length of 150 characters.

    currency_id : int
        The ID of the currency of the tariff.
        Foreign key to :attr:`Currency.currency_id`. Is indexed.

    validity_start : datetime.date or None
        The start date the tariff is valid from (inclusive)
        in the configured business timezone of the app.

    validity_end : datetime.date or None
        The end date the tariff is valid until (exclusive)
        in the configured business timezone of the app.

    high_load_period_start : datetime.date or None
        The start date of the high load period (inclusive)
        in the configured business timezone of the app.

    high_load_period_end : datetime.date or None
        The end date of the high load period (exclusive)
        in the configured business timezone of the app.

    description : str or None
        A description of the tariff.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff.

    created_at : datetime.datetime
        The timestamp at which the tariff was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_id',
        'name',
        'currency_id',
        'validity_start',
        'validity_end',
        'high_load_period_start',
        'high_load_period_end',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff'

    tariff_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    currency_id: Mapped[int] = mapped_column(ForeignKey(Currency.currency_id))
    validity_start: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The start date the tariff is valid from (inclusive) '
            'in the configured business timezone of the app.'
        ),
    )
    validity_end: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The end date the tariff is valid until (exclusive) '
            'in the configured business timezone of the app.'
        ),
    )
    high_load_period_start: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The start date of the high load period (inclusive) '
            'in the configured business timezone of the app.'
        ),
    )
    high_load_period_end: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The end date of the high load period (exclusive) '
            'in the configured business timezone of the app.'
        ),
    )
    description: Mapped[str | None]

    currency: Mapped['Currency'] = relationship()
    tariff_cost_groups: Mapped[list['TariffCostGroup']] = relationship(
        back_populates='tariff',
        cascade='all, delete-orphan',
        passive_deletes=True,
        single_parent=True,
    )

    tariff_tariff_component_type_links: Mapped[set['TariffTariffComponentTypeLink']] = relationship(
        back_populates='tariff',
        cascade='all, delete-orphan',
        passive_deletes=True,
        single_parent=True,
        collection_class=set,
    )
    tariff_component_types: AssociationProxy[set['TariffComponentType']] = association_proxy(
        'tariff_tariff_component_type_links',
        'tariff_component_type',
        creator=lambda tct: TariffTariffComponentTypeLink(tariff_component_type=tct),
    )
    tariff_component_type_ids: AssociationProxy[set[int]] = association_proxy(
        'tariff_tariff_component_type_links',
        'tariff_component_type_id',
        creator=lambda tct_id: TariffTariffComponentTypeLink(tariff_component_type_id=tct_id),
    )

    # A helper relationship for improved queries involving the secondary table.
    tariff_component_types_view: Mapped[set['TariffComponentType']] = relationship(
        secondary=lambda: TariffTariffComponentTypeLink.__table__,
        back_populates='tariffs_view',
        viewonly=True,
        collection_class=set,
    )

    def add_tariff_component_type(
        self,
        tct: 'TariffComponentType',
        updated_by: UUID | None = None,
        created_by: UUID | None = None,
    ) -> 'TariffTariffComponentTypeLink':
        r"""Add a tariff component to the tariff.

        Provides fine grained control over the audit columns `updated_by` and `created_by`.

        Parameters
        ----------
        tct : TariffComponentType
            The tariff component type to add.

        updated_by : uuid.UUID or None
            The ID of the user that last updated the tariff component type link.

        created_by : uuid.UUID or None
            The ID of the user that created the tariff component type link.

        Returns
        -------
        link : TariffTariffComponentTypeLink
            The created tariff tariff component type link.
        """

        link = TariffTariffComponentTypeLink(
            tariff=self, tariff_component_type=tct, updated_by=updated_by, created_by=created_by
        )
        self.tariff_tariff_component_type_links.add(link)

        return link


Index(f'{Tariff.__tablename__}_currency_id_ix', Tariff.currency_id)


class TariffCostGroup(AuditColumnsMixin, Base):
    r"""A tariff cost group contains a set of tariff components.

    Parameters
    ----------
    tariff_cost_group_id : int
        The unique ID of the tariff cost group. The primary key of the table.

    tariff_id : int
        The unique ID of the tariff. The primary key of the table.
        Foreign key to :attr:`Tariff.tariff_id`. Is indexed.

    name : str
        The name of the tariff cost group. Must be unique within each `tariff_id`.
        Max length of 150 characters.

    allowed_reactive_over_active_power_cons : decimal.Decimal, default 1.0
        The ratio of allowed reactive power consumption in relation to subscribed active
        power consumption. The default of 1.0 means that you may consume as much reactive
        power as you consume active power.

    allowed_reactive_over_active_power_prod : decimal.Decimal, default 1.0
        The ratio of allowed reactive power production in relation to the subscribed active
        power consumption. The default of 1.0 means that you may produce as much reactive power
        as you consume active power.

    description : str or None
        A description of the tariff cost group.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff cost group was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff cost group.

    created_at : datetime.datetime
        The timestamp at which the tariff cost group was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff cost group.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_cost_group_id',
        'tariff_id',
        'name',
        'allowed_reactive_over_active_power_cons',
        'allowed_reactive_over_active_power_prod',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff_cost_group'

    tariff_cost_group_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    tariff_id: Mapped[int] = mapped_column(ForeignKey(Tariff.tariff_id, ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(150))
    allowed_reactive_over_active_power_cons: Mapped[Decimal] = mapped_column(
        Ratio, server_default=text('1.0')
    )
    allowed_reactive_over_active_power_prod: Mapped[Decimal] = mapped_column(
        Ratio, server_default=text('1.0')
    )
    description: Mapped[str | None]

    tariff: Mapped[Tariff] = relationship(back_populates='tariff_cost_groups')
    tariff_components: Mapped[list['TariffComponent']] = relationship(
        back_populates='tariff_cost_group',
        cascade='all, delete-orphan',
        passive_deletes=True,
        single_parent=True,
    )
    tariff_cost_group_customer_group_links: Mapped[set['TariffCostGroupCustomerGroupLink']] = (
        relationship(
            back_populates='tariff_cost_group',
            cascade='all, delete-orphan',
            passive_deletes=True,
            single_parent=True,
            collection_class=set,
        )
    )
    customer_groups: AssociationProxy[set['CustomerGroup']] = association_proxy(
        'tariff_cost_group_customer_group_links',
        'customer_group',
        creator=lambda cg: TariffCostGroupCustomerGroupLink(customer_group=cg),
    )
    customer_group_ids: AssociationProxy[set['int']] = association_proxy(
        'tariff_cost_group_customer_group_links',
        'customer_group_id',
        creator=lambda cg_id: TariffCostGroupCustomerGroupLink(customer_group_id=cg_id),
    )


Index(
    f'{TariffCostGroup.__tablename__}_tariff_id__name_uix',
    TariffCostGroup.tariff_id,
    TariffCostGroup.name,
    unique=True,
)


class CalcStrategy(AuditColumnsMixin, Base):
    r"""The strategy for how a tariff component type should be calculated.

    Parameters
    ----------
    calc_strategy_id : int
        The unique ID of the calculation strategy. The primary key of the table.

    code : str
        The unique code of the calculation strategy. Is indexed. Max length of 64 characters.

    name : str or None
        A descriptive name of the calculation strategy.

    description : str or None
        A description of the calculation strategy.

    updated_at : datetime.datetime or None
        The timestamp at which calculation strategy was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated calculation strategy.

    created_at : datetime.datetime
        The timestamp at which calculation strategy was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created calculation strategy.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'calc_strategy_id',
        'code',
        'name',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_calc_strategy'

    calc_strategy_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str | None]
    description: Mapped[str | None]

    tariff_component_types: Mapped[list['TariffComponentType']] = relationship(
        back_populates='calc_strategy'
    )


class TariffComponentType(AuditColumnsMixin, Base):
    r"""The type of a tariff component.

    Parameters
    ----------
    tariff_component_type_id : int
        The unique ID of the tariff component type. The primary key of the table.

    name : str
        The unique name of the tariff component type. Is indexed. Max length of 150 characters.

    unit_id : int
        The unit of the tariff component type. Foreign key to :attr:`Unit.unit_id`.

    calc_strategy_id : int
        The calculation strategy to apply when calculating the revenue/cost
        for tariff components associated with the tariff component type.
        Foreign key to :attr:`CalcStrategy.calc_strategy_id`.

    serie_type_id : int or None
        The ID of the type of meter data serie associated with the tariff component calculations.
        Foreign key to :attr:`SerieType.serie_type_id`.

    is_revenue : bool, default True
        True if the tariff component type represents a revenue for the grid company and False
        for a cost. E.g. a tariff component type representing a compensation fee to production
        units helping the grid should have `is_revenue` set to False.

    description : str or None
        A description of the tariff component type.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff component type was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff component type.

    created_at : datetime.datetime
        The timestamp at which the tariff component type was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff component type.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_component_type_id',
        'name',
        'unit_id',
        'calc_strategy_id',
        'serie_type_id',
        'is_revenue',
        'description',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff_component_type'

    tariff_component_type_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    unit_id: Mapped[int] = mapped_column(ForeignKey(Unit.unit_id))
    calc_strategy_id: Mapped[int] = mapped_column(ForeignKey(CalcStrategy.calc_strategy_id))
    serie_type_id: Mapped[int | None] = mapped_column(ForeignKey(SerieType.serie_type_id))
    is_revenue: Mapped[bool] = mapped_column(
        server_default=text('1'),
        comment=(
            'True if the tariff component represents a revenue '
            'for the grid company and False for a cost.'
        ),
    )
    description: Mapped[str | None]

    unit: Mapped[Unit] = relationship()
    calc_strategy: Mapped[CalcStrategy] = relationship(back_populates='tariff_component_types')
    serie_type: Mapped[SerieType] = relationship()
    tariff_components: Mapped[list['TariffComponent']] = relationship(
        back_populates='tariff_component_type'
    )
    tariff_tariff_component_type_links: Mapped[set['TariffTariffComponentTypeLink']] = relationship(
        back_populates='tariff_component_type', passive_deletes=True, collection_class=set
    )

    # A helper relationship for improved queries involving the secondary table.
    tariffs_view: Mapped[set['Tariff']] = relationship(
        secondary=lambda: TariffTariffComponentTypeLink.__table__,
        back_populates='tariff_component_types_view',
        viewonly=True,
        collection_class=set,
    )


class TariffTariffComponentTypeLink(AuditColumnsMixin, Base):
    r"""The tariff component types available to a tariff.

    Parameters
    ----------
    tariff_id : int
        The ID of the tariff. Part of the primary key. Foreign key to :attr:`Tariff.tariff_id`.

    tariff_component_type_id : int
        The ID of the tariff component type. Part of the primary key.
        Foreign key to :attr:`TariffComponentType.tariff_component_type_id`.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff tariff component type link was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff tariff component type link.

    created_at : datetime.datetime
        The timestamp at which the tariff tariff component type link was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff tariff component type link.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_id',
        'tariff_component_type_id',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff_tariff_component_type_link'

    tariff_id: Mapped[int] = mapped_column(
        ForeignKey(Tariff.tariff_id, ondelete='CASCADE'), primary_key=True
    )
    tariff_component_type_id: Mapped[int] = mapped_column(
        ForeignKey(TariffComponentType.tariff_component_type_id, ondelete='CASCADE'),
        primary_key=True,
    )

    tariff: Mapped[set[Tariff]] = relationship(back_populates='tariff_tariff_component_type_links')
    tariff_component_type: Mapped[set[TariffComponentType]] = relationship(
        back_populates='tariff_tariff_component_type_links'
    )


Index(
    'ta_t_tct_link_tct_id__t_id_ix',
    TariffTariffComponentTypeLink.tariff_component_type_id,
    TariffTariffComponentTypeLink.tariff_id,
)


class TariffComponent(AuditColumnsMixin, Base):
    r"""A tariff component with price information.

    Parameters
    ----------
    tariff_component_id : int
        The unique ID of the tariff component. The primary key of the table.

    tariff_component_type_id : int
        The type of tariff component. Must be unique for each `tariff_cost_group_id`.
        Foreign key to :attr:`TariffComponentType.tariff_component_type_id`. Is indexed.

    tariff_cost_group_id : int
        The tariff cost group that the component belongs to.
        Foreign key to :attr:`TariffCostGroup.tariff_cost_group_id`. Is indexed.

    price : decimal.Decimal
        The price of the component in the currency of the tariff that the component belongs to.

    authority_fee : decimal.Decimal, default 0
        The part of the `price` that is composed of a fee to the authorities.

    price_outside_validity : decimal.Decimal, default 0
        The price of the component outside of its validity range.

    authority_fee_outside_validity : decimal.Decimal, default 0
        The part of the `price` outside of the validity that represents the fee to the authorities.

    validity_start : datetime or None
        The start date the tariff component is valid from (inclusive)
        in the configured business timezone of the app.

    validity_end : datetime or None
        The end date the tariff component is valid until (exclusive)
        in the configured business timezone of the app.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff component was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff component.

    created_at : datetime.datetime
        The timestamp at which the tariff component was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff component.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_component_id',
        'tariff_component_type_id',
        'tariff_cost_group_id',
        'price',
        'authority_fee',
        'price_outside_validity',
        'authority_fee_outside_validity',
        'validity_start',
        'validity_end',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff_component'

    tariff_component_id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    tariff_component_type_id: Mapped[int] = mapped_column(
        ForeignKey(TariffComponentType.tariff_component_type_id)
    )
    tariff_cost_group_id: Mapped[int] = mapped_column(
        ForeignKey(TariffCostGroup.tariff_cost_group_id, ondelete='CASCADE')
    )
    price: Mapped[Decimal] = mapped_column(MoneyPrice)
    authority_fee: Mapped[Decimal] = mapped_column(MoneyPrice, server_default=text('0'))
    price_outside_validity: Mapped[Decimal] = mapped_column(MoneyPrice, server_default=text('0'))
    authority_fee_outside_validity: Mapped[Decimal] = mapped_column(
        MoneyPrice, server_default=text('0')
    )
    validity_start: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The start date the tariff component is valid from (inclusive) '
            'in the configured business timezone of the app.'
        ),
    )
    validity_end: Mapped[date | None] = mapped_column(
        Date,
        comment=(
            'The end date the tariff component is valid until (exclusive) '
            'in the configured business timezone of the app.'
        ),
    )

    tariff_component_type: Mapped[TariffComponentType] = relationship(
        back_populates='tariff_components'
    )
    tariff_cost_group: Mapped[TariffCostGroup] = relationship(
        back_populates='tariff_components', passive_deletes=True
    )


Index(
    f'{TariffComponent.__tablename__}_tariff_component_type_id_uix',
    TariffComponent.tariff_component_type_id,
    TariffComponent.tariff_cost_group_id,
    unique=True,
)

Index(
    f'{TariffComponent.__tablename__}_tariff_cost_group_id_ix', TariffComponent.tariff_cost_group_id
)


class TariffCostGroupCustomerGroupLink(AuditColumnsMixin, Base):
    r"""The link between a tariff cost group and a customer group.

    Parameters
    ----------
    tariff_cost_group_id : int
        The ID of the tariff cost group. Part of the primary key.
        Foreign key to :attr:`TariffCostGroup.tariff_cost_group_id`.

    customer_group_id : int
        The ID of the customer group. Part of the primary key.
        Foreign key to :attr:`CustomerGroup.customer_group_id`.

    updated_at : datetime.datetime or None
        The timestamp at which the tariff cost group customer group link was last updated (UTC).

    updated_by : uuid.UUID or None
        The ID of the user that last updated the tariff cost group customer group link.

    created_at : datetime.datetime
        The timestamp at which the tariff cost group customer group link was created (UTC).
        Defaults to current timestamp.

    created_by : uuid.UUID or None
        The ID of the user that created the tariff cost group customer group link.
    """

    columns__repr__: ClassVar[tuple[str, ...]] = (
        'tariff_cost_group_id',
        'customer_group_id',
        'updated_at',
        'updated_by',
        'created_at',
        'created_by',
    )

    __tablename__ = 'ta_tariff_cost_group_customer_group_link'

    tariff_cost_group_id: Mapped[int] = mapped_column(
        ForeignKey(TariffCostGroup.tariff_cost_group_id, ondelete='CASCADE'), primary_key=True
    )
    customer_group_id: Mapped[int] = mapped_column(
        ForeignKey(CustomerGroup.customer_group_id, ondelete='CASCADE'), primary_key=True
    )

    tariff_cost_group: Mapped[TariffCostGroup] = relationship(
        back_populates='tariff_cost_group_customer_group_links'
    )
    customer_group: Mapped[CustomerGroup] = relationship(
        back_populates='tariff_cost_group_customer_group_links'
    )


Index(
    'ta_tcg_cg_link_cg_id__tcg_id_ix',
    TariffCostGroupCustomerGroupLink.customer_group_id,
    TariffCostGroupCustomerGroupLink.tariff_cost_group_id,
)
