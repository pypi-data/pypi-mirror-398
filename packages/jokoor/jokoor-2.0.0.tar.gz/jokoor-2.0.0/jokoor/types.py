"""
Type definitions for the Jokoor SDK

This module contains TypedDict definitions for all API request and response types.
"""

from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


# Configuration
class JokoorConfig(TypedDict, total=False):
    """SDK configuration options"""

    api_key: str
    base_url: str
    timeout: int
    max_retries: int
    debug: bool


# Generic Response Types
class PaginatedResponse(TypedDict):
    """Paginated list response"""

    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


# SMS Types
class SMS(TypedDict, total=False):
    """SMS message object"""

    id: str
    organization_id: str
    contact_id: Optional[str]
    campaign_id: Optional[str]
    template_id: Optional[str]
    recipient_phone: str
    message_body: str
    sender_id_used: str  # Actual sender ID used
    status: str  # draft, pending, queued, sending, sent, delivered, failed, undelivered, cancelled
    provider_message_id: Optional[str]
    segments: int
    cost: str
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class SMSSendParams(TypedDict, total=False):
    """Parameters for sending SMS"""

    recipient_phone: Optional[str]
    contact_id: Optional[str]
    message_body: Optional[str]
    template_id: Optional[str]
    template_params: Optional[Dict[str, str]]
    sender_id: Optional[str]
    scheduled_at: Optional[datetime]
    is_draft: bool


# SMS Template Types
class Template(TypedDict, total=False):
    """SMS template object"""

    id: str
    name: str
    body: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


# SMS Contact Types
class Contact(TypedDict, total=False):
    """SMS contact object"""

    id: str
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    custom_fields: Optional[Dict[str, str]]
    created_at: datetime
    updated_at: datetime


# SMS Contact Group Types
class ContactGroup(TypedDict, total=False):
    """SMS contact group object"""

    id: str
    name: str
    description: Optional[str]
    contact_count: int
    created_at: datetime
    updated_at: datetime


# SMS Sender ID Types
class SenderID(TypedDict, total=False):
    """Sender ID object"""

    id: str
    sender_id: str
    status: str  # pending, approved, rejected
    purpose: Optional[str]
    use_case: Optional[str]
    is_default: bool
    created_at: datetime
    updated_at: datetime


# SMS Campaign Types
class CampaignDetails(TypedDict, total=False):
    """Campaign delivery statistics"""

    total_message_count: int
    total_sent_messages: int
    total_failed_messages: int
    total_pending_messages: int
    total_segments_used: int
    delivery_rate: float
    failure_rate: float
    pending_rate: float
    status_breakdown: Dict[str, int]


class CampaignStats(TypedDict, total=False):
    """SMS Campaign statistics"""

    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float


class Campaign(TypedDict, total=False):
    """SMS campaign object"""

    id: str
    organization_id: str
    name: str
    message_template_id: Optional[str]
    sender_id_config_id: Optional[str]
    status: str  # draft, scheduled, sending, completed, failed, cancelled
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[str]
    details: Optional[CampaignDetails]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Payment Types
class PaymentSession(TypedDict, total=False):
    """Payment session object"""

    id: str
    session_id: str
    object_type: str  # payment_link, invoice, checkout, donation, topup
    object_id: str
    payment_method: str  # wave, card, afrimoney
    amount: str
    currency: str
    status: str  # pending, processing, succeeded, failed, cancelled
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    payment_url: Optional[str]
    provider_session_id: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class Transaction(TypedDict, total=False):
    """Transaction object"""

    id: str
    payment_session_id: str
    object_type: str
    object_id: str
    organization_id: str
    customer_id: Optional[str]
    amount: str
    fee: str
    net_amount: str
    currency: str
    status: str  # pending, processing, completed, failed, cancelled, expired, refunded, partially_refunded
    payment_method: str  # wave, card, afrimoney
    payment_method_transaction_id: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_name: Optional[str]
    payment_phone: Optional[str]
    payment_details: Optional[Dict[str, Any]]
    mode: str  # test, live
    livemode: bool
    initiated_at: datetime
    processing_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    refunded_amount: Optional[str]
    failure_reason: Optional[str]
    state_transitions: Optional[List[Dict[str, Any]]]
    payment_method_response: Optional[Dict[str, Any]]
    attempt_count: int
    metadata: Optional[Dict[str, Any]]
    processing_type: Optional[str]
    recording_source: Optional[str]
    recorded_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class Refund(TypedDict, total=False):
    """Refund object"""

    id: str
    transaction_id: str
    amount: str
    currency: str
    reason: Optional[str]
    status: str  # pending, processing, completed, failed
    created_at: datetime
    updated_at: datetime


# Checkout Types
class Checkout(TypedDict, total=False):
    """Checkout session object"""

    id: str
    amount: str
    currency: str
    payment_url: str  # Hosted payment page URL
    client_secret: str  # For SDK integration
    status: str  # pending, completed, expired, cancelled
    available_payment_methods: Optional[List[str]]
    automatic_payment_methods: bool
    customer_id: Optional[str]
    customer_phone: str
    customer_email: Optional[str]
    customer_name: Optional[str]
    expires_at: datetime
    description: Optional[str]
    reference: Optional[str]
    items: Optional[List[Dict[str, Any]]]
    payment_session_id: Optional[str]
    success_url: Optional[str]
    cancel_url: Optional[str]
    metadata: Optional[Dict[str, Any]]
    livemode: bool  # Only livemode, no separate mode field
    transaction: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Payment Link Types
class PaymentLink(TypedDict, total=False):
    """Payment link object"""

    id: str
    organization_id: str
    title: str
    description: Optional[str]
    amount: str
    currency: str
    is_variable_amount: bool
    min_amount: Optional[str]
    max_amount: Optional[str]
    status: str  # active, inactive
    payment_url: str  # Hosted payment page URL
    collect_customer_info: bool
    custom_fields: Optional[List[Dict[str, Any]]]
    success_url: Optional[str]
    failure_url: Optional[str]
    expiration_date: Optional[datetime]
    max_usage_count: Optional[int]
    usage_count: int
    livemode: bool  # Only livemode, no separate mode field
    metadata: Optional[Dict[str, Any]]
    organization: Optional[Dict[str, Any]]  # {id, name, logo}
    products: Optional[List[Dict[str, Any]]]  # Product details
    created_at: datetime
    updated_at: datetime


# Invoice Types
class InvoiceLineItem(TypedDict):
    """Invoice line item"""

    description: str
    quantity: int
    unit_price: str
    amount: str


class Invoice(TypedDict, total=False):
    """Invoice object"""

    id: str
    organization_id: str
    invoice_number: str
    customer_id: Optional[str]
    customer_email: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]
    status: str  # draft, pending, paid, partially_paid, overdue, cancelled
    amount: str  # Base amount before tax
    tax_rate: float  # 0-100
    tax_amount: str
    total_amount: str  # Amount after tax
    paid_amount: str
    remaining_amount: str  # Remaining balance (total_amount - paid_amount)
    currency: str
    notes: Optional[str]
    items: List[InvoiceLineItem]  # Changed from line_items
    due_date: Optional[datetime]
    issued_date: Optional[datetime]
    paid_date: Optional[datetime]
    sent_at: Optional[datetime]
    sent_count: int
    payment_url: Optional[
        str
    ]  # Public payment URL (only for non-draft, non-paid, non-cancelled)
    pdf_url: Optional[str]  # PDF download URL
    receipts: Optional[List[Dict[str, Any]]]  # Payment receipts
    subscription_id: Optional[str]
    livemode: bool  # Only livemode, no separate mode, payment_status, or version
    metadata: Optional[Dict[str, Any]]
    organization: Optional[Dict[str, Any]]  # {id, name, logo_url}
    created_at: datetime
    updated_at: datetime


# Customer Types
class Customer(TypedDict, total=False):
    """Customer object"""

    id: str
    email: Optional[str]
    phone: Optional[str]
    name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Product Types
class Product(TypedDict, total=False):
    """Product object"""

    id: str
    name: str
    description: Optional[str]
    price: str
    currency: str
    active: bool
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Subscription Types
class Subscription(TypedDict, total=False):
    """Subscription object"""

    id: str
    organization_id: str
    customer_id: Optional[str]
    customer_email: str
    customer_name: str
    amount: str  # Base amount before tax
    currency: str
    tax_rate: float  # 0-100
    status: str  # active, paused, cancelled, completed
    interval: str  # day, week, month, year
    interval_count: int
    day_of_month: Optional[int]  # For monthly subscriptions (1-28)
    day_of_week: Optional[int]  # For weekly subscriptions (0-6)
    start_date: datetime
    end_date: Optional[datetime]
    next_invoice_date: datetime
    last_invoice_date: Optional[datetime]
    items: List[InvoiceLineItem]  # Subscription line items
    notes: Optional[str]
    mode: str  # test, live
    version: int
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# Donation Campaign Types
class DonationCampaign(TypedDict, total=False):
    """Donation campaign object"""

    id: str
    organization_id: str
    title: str
    slug: str  # SEO-friendly URL slug
    description: str
    target_amount: Optional[str]  # Goal amount
    current_amount: str  # Amount raised so far
    currency: str
    tags: Optional[List[str]]  # Can be null/empty
    is_recurring: bool
    recurring_interval: Optional[str]
    donor_count: int
    view_count: int
    last_donation_at: Optional[datetime]
    progress_percentage: float
    status: str  # active, inactive, completed
    donation_url: str  # Public donation page URL
    image_url: Optional[str]
    end_date: Optional[datetime]
    mode: str  # test, live
    livemode: bool
    metadata: Optional[Dict[str, Any]]
    organization: Optional[Dict[str, Any]]  # {id, name, logo}
    organizer_details: Optional[Dict[str, Any]]  # Can be null on create
    recent_updates: Optional[List[Dict[str, Any]]]  # Campaign updates
    created_at: datetime
    updated_at: datetime


# Payout Types
class PayoutBalance(TypedDict):
    """Payout balance"""

    available_balance: str
    pending_balance: str
    currency: str


class BankAccount(TypedDict, total=False):
    """Bank account object"""

    id: str
    account_number: str
    account_name: str
    bank_name: str
    bank_code: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class PayoutRequest(TypedDict, total=False):
    """Payout request object"""

    id: str
    amount: str
    currency: str
    bank_account_id: str
    status: str  # pending, processing, completed, failed, cancelled
    reference: str
    failure_reason: Optional[str]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PayoutRecipient(TypedDict, total=False):
    """Payout recipient object (Wave B2P)"""

    id: str
    organization_id: str
    name: str
    email: Optional[str]
    payout_method: str  # wave, afrimoney, etc.
    payout_phone: str  # Phone number for receiving payouts
    recipient_type: str
    internal_reference: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RecipientPayout(TypedDict, total=False):
    """Recipient payout object"""

    id: str
    recipient_id: str
    amount: str
    currency: str
    status: str  # pending, completed, failed, cancelled
    reference: str
    failure_reason: Optional[str]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Webhook Types
class WebhookEndpoint(TypedDict, total=False):
    """Webhook endpoint object"""

    id: str
    url: str
    description: Optional[str]
    api_version: str
    enabled_events: List[str]
    status: str  # active, inactive
    secret: Optional[str]  # Only visible on creation, not on subsequent GET requests
    metadata: Optional[Dict[str, Any]]
    consecutive_failures: int
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    disabled_at: Optional[datetime]
    disable_reason: Optional[str]
    created: datetime  # Note: 'created' not 'created_at' per backend JSON tag
    updated_at: datetime


class WebhookEvent(TypedDict, total=False):
    """Webhook event object"""

    id: str
    type: str
    data: Dict[str, Any]
    webhook_endpoint_id: Optional[str]
    status: str  # pending, delivered, failed
    attempts: int
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Receipt Types
class Receipt(TypedDict, total=False):
    """Payment receipt object"""

    id: str
    receipt_number: str
    invoice_id: Optional[str]
    invoice_payment_id: Optional[str]
    organization_id: str
    amount: str
    currency: str
    payment_method: str  # wave, card, afrimoney
    payment_date: datetime
    transaction_id: Optional[str]
    receipt_url: Optional[str]
    validation_code: str
    customer_name: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]
    org_name: str
    org_address: Optional[str]
    org_phone: Optional[str]
    org_email: Optional[str]
    status: str  # pending, completed, failed
    mode: str  # test, live
    livemode: bool
    created_at: datetime
    updated_at: datetime


# Payout Deposit Types
class DepositTransaction(TypedDict, total=False):
    """Deposit transaction object"""

    id: str
    amount: str
    currency: str
    source: str  # Source of deposit (e.g., "payment", "refund")
    source_id: str  # ID of the source transaction
    description: Optional[str]
    status: str  # pending, completed, failed
    created_at: datetime
    completed_at: Optional[datetime]


# Bulk Payout Types
class BulkPayoutItem(TypedDict):
    """Individual payout item in a bulk payout request"""

    recipient_id: str
    amount: str
    description: Optional[str]


class BulkPayoutStatus(TypedDict, total=False):
    """Status of an individual payout in a bulk batch"""

    id: str
    recipient_id: str
    amount: str
    status: str  # pending, completed, failed, cancelled
    error_message: Optional[str]


class BulkPayoutBatch(TypedDict, total=False):
    """Bulk payout batch object"""

    id: str
    organization_id: str
    total_amount: str
    total_count: int
    successful_count: int
    failed_count: int
    pending_count: int
    status: str  # pending, processing, completed, partially_completed, failed
    payouts: List[BulkPayoutStatus]
    created_at: datetime
    completed_at: Optional[datetime]


class CSVUpload(TypedDict, total=False):
    """CSV upload response object"""

    upload_id: str
    rows_count: int
    total_amount: str
    validation_errors: Optional[List[str]]
