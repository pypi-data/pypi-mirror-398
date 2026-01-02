"""
Resource modules for the Jokoor SDK
"""

from .sms import SMSResource
from .campaigns import CampaignsResource
from .templates import TemplatesResource
from .contacts import ContactsResource
from .contact_groups import ContactGroupsResource
from .sender_ids import SenderIDsResource
from .payments import PaymentsResource
from .checkouts import CheckoutsResource
from .payment_links import PaymentLinksResource
from .invoices import InvoicesResource
from .receipts import ReceiptsResource
from .customers import CustomersResource
from .products import ProductsResource
from .transactions import TransactionsResource
from .refunds import RefundsResource
from .subscriptions import SubscriptionsResource
from .donations import DonationsResource
from .payouts import PayoutsResource
from .bank_accounts import BankAccountsResource
from .recipients import RecipientsResource
from .webhooks import WebhooksResource
from .webhook_events import WebhookEventsResource

__all__ = [
    "SMSResource",
    "CampaignsResource",
    "TemplatesResource",
    "ContactsResource",
    "ContactGroupsResource",
    "SenderIDsResource",
    "PaymentsResource",
    "CheckoutsResource",
    "PaymentLinksResource",
    "InvoicesResource",
    "ReceiptsResource",
    "CustomersResource",
    "ProductsResource",
    "TransactionsResource",
    "RefundsResource",
    "SubscriptionsResource",
    "DonationsResource",
    "PayoutsResource",
    "BankAccountsResource",
    "RecipientsResource",
    "WebhooksResource",
    "WebhookEventsResource",
]
