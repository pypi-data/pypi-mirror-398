class Item:
    def __init__(self):
        """Initialize model"""

        self.code: str = None
        """Item identifier code or UPC/EAN"""

        self.title: str = None
        """Item product title"""

        self.price: float = 0.00
        """Item per unit price"""

        self.qty: int = 1
        """Item quantity"""

        self.tax: float = 0.00
        """Item tax amount per unit"""

        self.total: float = 0.00
        """Item total value"""

    def totalize(self):
        """Totalize item price by quantity

        Returns:
            Item: self
        """
        self.total = self.price * self.qty

        return self
