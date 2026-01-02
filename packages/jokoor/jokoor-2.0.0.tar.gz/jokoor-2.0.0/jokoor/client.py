"""
Main Jokoor SDK client
"""

from typing import Optional

from .http_client import HTTPClient
from .resources import (
    SMSResource,
    CampaignsResource,
    TemplatesResource,
    ContactsResource,
    ContactGroupsResource,
    SenderIDsResource,
    PaymentsResource,
    CheckoutsResource,
    PaymentLinksResource,
    InvoicesResource,
    ReceiptsResource,
    CustomersResource,
    ProductsResource,
    TransactionsResource,
    RefundsResource,
    SubscriptionsResource,
    DonationsResource,
    PayoutsResource,
    BankAccountsResource,
    RecipientsResource,
    WebhooksResource,
    WebhookEventsResource,
)


class Jokoor:
    """
    Main client for interacting with the Jokoor API

    This client provides access to all Jokoor API resources including SMS,
    payments, payouts, and webhooks.

    Example:
        >>> from jokoor import Jokoor
        >>>
        >>> # Initialize client
        >>> client = Jokoor('sk_test_your_api_key')
        >>>
        >>> # Send an SMS
        >>> sms, error = client.sms.send(
        ...     recipient_phone='+2207123456',
        ...     message_body='Hello from Jokoor!'
        ... )
        >>> if error:
        ...     print(f"Error: {error}")
        ... else:
        ...     print(f"SMS sent: {sms['id']}")
        >>>
        >>> # Create a payment link
        >>> link, error = client.payment_links.create(
        ...     title='Product Purchase',
        ...     amount='100.00',
        ...     currency='GMD'
        ... )
        >>> if not error:
        ...     print(f"Payment link: {link['payment_url']}")
        >>>
        >>> # Use context manager for automatic cleanup
        >>> with Jokoor('sk_test_your_api_key') as client:
        ...     sms, error = client.sms.send(
        ...         recipient_phone='+2207123456',
        ...         message_body='Hello!'
        ...     )
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.jokoor.com",
        timeout: int = 30,
        max_retries: int = 3,
        debug: bool = False,
    ) -> None:
        """
        Initialize the Jokoor client

        Args:
            api_key: Your Jokoor API key (sk_test_xxx or sk_live_xxx)
            base_url: API base URL (default: https://api.jokoor.com)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retry attempts (default: 3)
            debug: Enable debug logging (default: False)
        """
        # Initialize HTTP client
        self._http = HTTPClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            debug=debug,
        )

        # Initialize SMS resources
        self.sms = SMSResource(self._http)
        self.campaigns = CampaignsResource(self._http)
        self.templates = TemplatesResource(self._http)
        self.contacts = ContactsResource(self._http)
        self.contact_groups = ContactGroupsResource(self._http)
        self.sender_ids = SenderIDsResource(self._http)

        # Initialize Payment resources
        self.payments = PaymentsResource(self._http)
        self.checkouts = CheckoutsResource(self._http)
        self.payment_links = PaymentLinksResource(self._http)
        self.invoices = InvoicesResource(self._http)
        self.receipts = ReceiptsResource(self._http)
        self.customers = CustomersResource(self._http)
        self.products = ProductsResource(self._http)
        self.transactions = TransactionsResource(self._http)
        self.refunds = RefundsResource(self._http)
        self.subscriptions = SubscriptionsResource(self._http)
        self.donations = DonationsResource(self._http)

        # Initialize Payout resources
        self.payouts = PayoutsResource(self._http)
        self.bank_accounts = BankAccountsResource(self._http)
        self.payout_recipients = RecipientsResource(self._http)

        # Initialize Webhook resources
        self.webhooks = WebhooksResource(self._http)
        self.webhook_events = WebhookEventsResource(self._http)

    def close(self) -> None:
        """Close the HTTP session"""
        self._http.close()

    def __enter__(self) -> "Jokoor":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        """Context manager exit"""
        self.close()
