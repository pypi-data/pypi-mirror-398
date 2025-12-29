from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from caerp.models.expense.sheet import ExpenseLine
from caerp.models.supply.supplier_invoice import SupplierInvoice, SupplierInvoiceLine
from caerp.models.supply.supplier_order import SupplierOrder, SupplierOrderLine
from caerp.models.third_party.supplier import Supplier

from .third_party import get_cae_third_parties_sirens, get_third_parties_from_siren


def is_supplier_deletable(request, supplier: Supplier) -> bool:
    q1 = select(func.count(SupplierOrder.id)).where(
        SupplierOrder.supplier_id == supplier.id
    )
    q2 = select(func.count(SupplierInvoice.id)).where(
        SupplierInvoice.supplier_id == supplier.id
    )
    q3 = select(func.count(ExpenseLine.id)).where(
        ExpenseLine.supplier_id == supplier.id
    )
    return (
        supplier.archived
        and request.dbsession.execute(q1).scalar() == 0
        and request.dbsession.execute(q2).scalar() == 0
        and request.dbsession.execute(q3).scalar() == 0
    )


def get_suppliers_from_siren(request, siren: str) -> list:
    """
    Return list of supplier instances that match the given SIREN
    """
    return get_third_parties_from_siren(request, siren, Supplier)


def get_cae_suppliers_sirens(request) -> list:
    """
    Return a list with all the distinct suppliers SIREN used in the CAE
    """
    return get_cae_third_parties_sirens(request, Supplier)


def get_global_total_supplier_invoice_value(
    request,
    siren: Optional[str] = None,
    supplier_id: Optional[int] = None,
    fieldname="ht",
) -> int:
    """
    Return the global total HT of supplier invoices
    for a global supplier (SIREN) OR a company supplier (ID)
    """
    supplier_invoice = aliased(SupplierInvoice)
    supplier = aliased(Supplier)
    query = (
        select(func.sum(getattr(SupplierInvoiceLine, fieldname)))
        .join(
            supplier_invoice,
            supplier_invoice.id == SupplierInvoiceLine.supplier_invoice_id,
        )
        .join(supplier, supplier.id == supplier_invoice.supplier_id)
    )
    if siren:
        query = query.where(supplier.siret.like(f"{siren}%"))
    elif supplier_id:
        query = query.where(supplier.id == supplier_id)
    else:
        raise ValueError("Either siren or supplier_id must be provided")

    query = query.where(supplier_invoice.status == "valid")
    return request.dbsession.execute(query).scalar() or 0


def get_global_total_supplier_order_value(
    request,
    siren: Optional[str] = None,
    supplier_id: Optional[int] = None,
    fieldname="ht",
) -> int:
    """
    Return the global total HT of supplier orders
    for a global supplier (SIREN) OR a company supplier (ID)
    """
    supplier_order = aliased(SupplierOrder)
    supplier = aliased(Supplier)
    query = select(func.sum(getattr(SupplierOrderLine, fieldname)))
    query = query.join(
        supplier_order, supplier_order.id == SupplierOrderLine.supplier_order_id
    ).join(supplier, supplier.id == supplier_order.supplier_id)

    return request.dbsession.execute(query).scalar() or 0
