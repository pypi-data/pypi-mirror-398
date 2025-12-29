"""
InvoiceAI SDK Type Definitions
"""

from typing import Optional, List, TypedDict
from datetime import datetime


class InvoiceItem(TypedDict, total=False):
    id: str
    invoice_id: str
    product_id: Optional[str]
    description: str
    quantity: int
    price_cents: int
    vat_rate: float
    total_cents: int


class Client(TypedDict, total=False):
    id: str
    user_id: str
    name: str
    email: Optional[str]
    company: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    created_at: str
    updated_at: str


class Invoice(TypedDict, total=False):
    id: str
    user_id: str
    client_id: Optional[str]
    invoice_number: str
    issue_date: str
    due_date: str
    subtotal_cents: int
    vat_cents: int
    total_cents: int
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    clients: Optional[Client]
    invoice_items: Optional[List[InvoiceItem]]


class Product(TypedDict, total=False):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    price_cents: int
    vat_rate: float
    unit: str
    created_at: str
    updated_at: str


class QuoteItem(TypedDict, total=False):
    id: str
    quote_id: str
    product_id: Optional[str]
    description: str
    quantity: int
    price_cents: int
    vat_rate: float
    total_cents: int


class Quote(TypedDict, total=False):
    id: str
    user_id: str
    client_id: Optional[str]
    quote_number: str
    issue_date: str
    expiry_date: str
    subtotal_cents: int
    vat_cents: int
    total_cents: int
    status: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    clients: Optional[Client]
    quote_items: Optional[List[QuoteItem]]


class Profile(TypedDict, total=False):
    id: str
    user_id: str
    business_name: Optional[str]
    business_address: Optional[str]
    business_phone: Optional[str]
    business_email: Optional[str]
    business_reg_number: Optional[str]
    vat_number: Optional[str]
    bank_name: Optional[str]
    bank_account_number: Optional[str]
    bank_branch_code: Optional[str]
    company_logo: Optional[str]
    created_at: str
    updated_at: str


class Stats(TypedDict):
    total_invoices: int
    total_clients: int
    total_products: int
    revenue_this_month: float
    pending_invoices: int
    overdue_invoices: int


class PaginatedInvoices(TypedDict):
    invoices: List[Invoice]
    total: int
    limit: int
    offset: int


class PaginatedClients(TypedDict):
    clients: List[Client]
    total: int
    limit: int
    offset: int


class PaginatedProducts(TypedDict):
    products: List[Product]
    total: int
    limit: int
    offset: int


class PaginatedQuotes(TypedDict):
    quotes: List[Quote]
    total: int
    limit: int
    offset: int
