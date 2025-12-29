from typing import Dict, List
from ..base import Helpers
from ..base import RequestBehaviour
from ..models import Billing
from ..models import Card
from ..models import Item
from ..models import Order


class PaymentTransaction(RequestBehaviour):
    def __init__(self):
        super().__init__()

        self.payment_uuid: str = None
        """Payment UUID"""

        self.card_token: str = None
        """Tokenized card identifier (T-* format)"""

        self.card_number: str = None
        """Card number or PAN"""

        self.card_cvv: str = None
        """Card security code"""

        self.card_expire: str = None
        """Card expire year/month date (YYMM)"""

        self.card_holder: str = None
        """Cardholder name"""

        self.billing_address: str = None
        """Customer billing address"""

        self.billing_country: str = None
        """Customer billing country alpha-2 code (ISO 3166-1)"""

        self.billing_state: str = None
        """Customer billing state alpha code (ISO 3166-2)"""

        self.billing_city: str = None
        """Customer billing city"""

        self.billing_zip: str = None
        """Customer billing postal code"""

        self.billing_phone: str = None
        """Customer billing phone"""

        self.customer_name: str = None
        """Order customer name"""

        self.customer_email: str = None
        """Order customer email"""

        self.order_id: str = None
        """Order ID"""

        self.order_currency: str = None
        """Order currency code alpha-3"""

        self.order_amount: str = None
        """Order total amount"""

        self.order_tax_amount: str = None
        """Order total tax amount"""

        self.order_shipping_amount: str = None
        """Order total shipping amount"""

        self.order_content: List[Item] = []
        """Order summary of items or products"""

        self.order_extras: Dict[str, str] = {}
        """Order extra properties"""

        self.order_note: str = None
        """Order note or aditional instructions"""

        self.order_callback: str = None
        """Order calback webhook URL"""

        self.authentication_request: bool = False
        """Activate authentication request (3DS/EMV)"""

        self.authentication_identifier: str = None
        """Authentication transaction identifier"""

        self.source: str = None
        """Internal processing flow of the transaction (e.g. router, proxy, etc)"""

    def setCard(self, card: Card):
        """Associate and mapping Card model properties to transaction

        Args:
            card (Card): input Card
        """
        self.card_number = Helpers.cleanString(card.number)
        self.card_cvv = card.cvv2
        self.card_expire = card.getExpireFormat()
        self.card_holder = Helpers.trimValue(card.cardholder)

    def setCardToken(self, token: str):
        """Associate and card token string to transaction

        Args:
            card (str): input card token
        """
        self.card_token = token

    def setBilling(self, billing: Billing):
        """Associate and mapping Billing model properties to transaction

        Args:
            billing (Billing): input Billing
        """
        self.billing_address = Helpers.trimValue(billing.address)
        self.billing_country = billing.country
        self.billing_state = billing.state
        self.billing_city = Helpers.trimValue(billing.city)
        self.billing_zip = billing.zip
        self.billing_phone = billing.phone

    def setOrder(self, order: Order):
        """Associate and mapping Order model properties to transaction

        Args:
            order (Order): input Order
        """
        self.order_id = order.id
        self.order_currency = order.currency
        self.order_amount = Helpers.parseAmount(order.amount)
        self.order_tax_amount = Helpers.parseAmount(order.tax_amount)
        self.order_shipping_amount = Helpers.parseAmount(order.shipping_amount)
        self.order_content = order.content
        self.order_extras = order.extras
        self.order_note = Helpers.trimValue(order.note)
        self.order_callback = order.callback_url

        self.customer_name = Helpers.trimValue(order.customer_name)
        self.customer_email = order.customer_email

    def withAuthenticationRequest(self):
        """Enable 3DS/EMV authentication request"""
        self.authentication_request = True
