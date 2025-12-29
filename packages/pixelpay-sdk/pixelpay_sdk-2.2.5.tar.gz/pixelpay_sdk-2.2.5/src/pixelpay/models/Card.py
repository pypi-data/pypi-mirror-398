class Card:
    def __init__(self):
        self.number: str = None
        """Card number or PAN"""

        self.cvv2: str = None
        """Card security code"""

        self.expire_month: int = 00
        """Card expire month date (MM)"""

        self.expire_year: int = 0000
        """Card expire year date (YYYY)"""

        self.cardholder: str = None
        """Cardholder name"""

    def getExpireFormat(self) -> str:
        """Get expire ISO format (YYMM)

        Returns:
            str: formatted expire
        """
        year = str(self.expire_year)
        month = "{:02d}".format(self.expire_month)

        return year[2:] + month
