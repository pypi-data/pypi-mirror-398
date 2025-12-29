from ..base.Helpers import Helpers
from ..base.RequestBehaviour import RequestBehaviour
from ..models.Billing import Billing
from ..models.Card import Card


class CardTokenization(RequestBehaviour):
    def __init__(self):
        super().__init__()

        self.number: str = None
        """Card number or PAN"""

        self.cvv2: str = None
        """Card security code"""

        self.expire_month: str = None
        """Card expire month date (MM)"""

        self.expire_year: str = None
        """Card expire year date (YYYY)"""

        self.customer: str = None
        """Tokenized customer identifier (C-* format)"""

        self.cardholder: str = None
        """Cardholder name"""

        self.address: str = None
        """Customer billing address"""

        self.country: str = None
        """Customer billing country alpha-2 code (ISO 3166-1)"""

        self.state: str = None
        """Customer billing state alpha code (ISO 3166-2)"""

        self.city: str = None
        """Customer billing city"""

        self.zip: str = None
        """Customer billing postal code"""

        self.phone: str = None
        """Customer billing phone"""

        self.email: str = None
        """Customer email"""

    def setCard(self, card: Card):
        """Associate and mapping Card model properties to transaction

        Args:
            card (Card): input Card
        """
        self.number = Helpers.cleanString(card.number)
        self.cvv2 = card.cvv2
        self.cardholder = Helpers.trimValue(card.cardholder)

        if card.expire_month != 0:
            self.expire_month = "{:02d}".format(card.expire_month)

        if card.expire_year != 0:
            self.expire_year = str(card.expire_year)

    def setBilling(self, billing: Billing):
        self.address = Helpers.trimValue(billing.address)
        self.country = billing.country
        self.state = billing.state
        self.city = Helpers.trimValue(billing.city)
        self.zip = billing.zip
        self.phone = billing.phone

    def setCustomerToken(self, customer: str):
        """Setup customer token

        Args:
            customer (str): Tokenized customer identifier (C-* format)
        """
        self.customer = customer
