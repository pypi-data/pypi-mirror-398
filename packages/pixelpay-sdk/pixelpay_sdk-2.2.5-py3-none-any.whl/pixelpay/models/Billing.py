class Billing:
    def __init__(self):
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
