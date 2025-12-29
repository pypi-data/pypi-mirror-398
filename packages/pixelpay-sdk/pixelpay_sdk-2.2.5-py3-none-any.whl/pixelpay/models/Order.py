from typing import Any, Dict, List
from .Item import Item


class Order:
    def __init__(self):
        """Initialize model"""

        self.id: str = None
        """Order ID"""

        self.currency: str = None
        """Order currency code alpha-3"""

        self.amount: float = 0.00
        """Order total amount"""

        self.tax_amount: float = 0.00
        """Order total tax amount"""

        self.shipping_amount: float = 0.00
        """Order total shipping amount"""

        self.content: List[Item] = []
        """Order summary of items or products"""

        self.extras: Dict[str, str] = {}
        """Order extra properties"""

        self.note: str = None
        """Order note or aditional instructions"""

        self.callback_url: str = None
        """Order calback webhook URL"""

        self.customer_name: str = None
        """Order customer name"""

        self.customer_email: str = None
        """Order customer email"""

    def addItem(self, item: Item):
        """Add item to content list of products/items

        Args:
            item (Item): input item

        Returns:
            Order: self
        """
        self.content.append(item)
        self.totalize()

        return self

    def addExtra(self, key: str, value: Any):
        """Add extra property to order

        Args:
            key (str): input key
            value (Any): input value

        Returns:
            Order: self
        """
        self.extras[key] = value

        return self

    def totalize(self):
        """Totalize order amounts and items

        Returns:
            Order: self
        """
        self.amount = 0.00
        self.tax_amount = 0.00

        for item in self.content:
            item.totalize()

            self.amount += item.total
            self.tax_amount += item.tax * item.qty

        return self
