"""
    Supplier model
"""
import logging

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from caerp.models.base import DBBASE, default_table_args

from .services.supplier import SupplierService
from .third_party import ThirdParty


class Supplier(ThirdParty):
    __tablename__ = "supplier"
    __table_args__ = default_table_args
    __mapper_args__ = {"polymorphic_identity": "supplier"}
    _caerp_service = SupplierService

    id = Column(
        ForeignKey("third_party.id"),
        primary_key=True,
        info={"colanderalchemy": {"exclude": True, "title": "Identifiant"}},
    )

    company = relationship(
        "Company",
        primaryjoin="Company.id==Supplier.company_id",
        back_populates="suppliers",
        info={
            "colanderalchemy": {"exclude": True},
            "export": {"exclude": True},
        },
    )
    orders = relationship(
        "SupplierOrder",
        primaryjoin="SupplierOrder.supplier_id==Supplier.id",
        back_populates="supplier",
        info={
            "colanderalchemy": {"exclude": True},
            "export": {"exclude": True},
        },
    )
    invoices = relationship(
        "SupplierInvoice",
        primaryjoin="SupplierInvoice.supplier_id==Supplier.id",
        back_populates="supplier",
        info={
            "colanderalchemy": {"exclude": True},
            "export": {"exclude": True},
        },
    )

    def get_invoices(self):
        return self._caerp_service.get_invoices(self)

    def get_expenselines(self):
        return self._caerp_service.get_expenselines(self)

    def get_orders(
        self,
        waiting_only=False,
        invoiced_only=False,
        pending_invoice_only=False,
        internal=True,
    ):
        return self._caerp_service.get_orders(
            self,
            waiting_only=waiting_only,
            invoiced_only=invoiced_only,
            pending_invoice_only=pending_invoice_only,
            internal=internal,
        )

    def has_orders(self):
        return self._caerp_service.count_orders(self) > 0

    def is_deletable(self):
        return self.archived and not self.has_orders()
