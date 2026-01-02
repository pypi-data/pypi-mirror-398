"""Pydantic schemas for invoice generation.

Common schemas are imported here for convenience.
Advanced schemas require explicit import.

Common usage:
    from pydantic_invoices.schemas import Invoice, InvoiceCreate, Client, ClientCreate

Advanced usage:
    from pydantic_invoices.schemas.company import Company, CompanyCreate
    from pydantic_invoices.schemas.product import Product, ProductCreate
    from pydantic_invoices.schemas.payment_note import PaymentNote, PaymentNoteCreate
    from pydantic_invoices.schemas.audit_log import AuditLog
"""

# Common schemas - used in most operations
from .invoice import Invoice, InvoiceCreate, InvoiceUpdate
from .invoice_line import InvoiceLine, InvoiceLineCreate
from .client import Client, ClientCreate, ClientUpdate
from .payment import Payment, PaymentCreate

__all__ = [
    # Invoice
    "Invoice",
    "InvoiceCreate",
    "InvoiceUpdate",
    # Invoice Line
    "InvoiceLine",
    "InvoiceLineCreate",
    # Client
    "Client",
    "ClientCreate",
    "ClientUpdate",
    # Payment
    "Payment",
    "PaymentCreate",
]

# Advanced schemas - import explicitly:
# from pydantic_invoices.schemas.company import Company, CompanyCreate, CompanyUpdate
# from pydantic_invoices.schemas.product import Product, ProductCreate, ProductUpdate
# from pydantic_invoices.schemas.payment_note import PaymentNote, PaymentNoteCreate, PaymentNoteUpdate
# from pydantic_invoices.schemas.audit_log import AuditLog
