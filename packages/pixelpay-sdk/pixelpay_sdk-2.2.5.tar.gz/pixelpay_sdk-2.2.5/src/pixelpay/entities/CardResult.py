from __future__ import annotations
from ..base import Response
from ..responses import SuccessResponse

class CardResult:
    def __init__(self):
        self.status: str = None
        """Card status"""

        self.mask: str = None
        """Card number masked"""

        self.network: str = None
        """Card network brand"""

        self.type: str = None
        """Card type (debit/credit)"""

        self.bin: str = None
        """Car bin number"""

        self.last: str = None
        """Card last 4 numbers"""

        self.hash: str = None
        """Card unique hash number"""

        self.address: str = None
        """Billing address"""

        self.country: str = None
        """Billing country"""

        self.state: str = None
        """Billing state"""

        self.city: str = None
        """Billing city"""

        self.zip: str = None
        """Billing postal code"""

        self.email: str = None
        """Billing customer email"""

        self.phone: str = None
        """Billing phone"""

    @staticmethod
    def validateResponse(response: Response) -> bool:
        """Validate if response type is valid for parse

        Args:
            response: Response to validate

        Returns:
            bool: is valid response
        """
        return isinstance(response, SuccessResponse)

    @staticmethod
    def fromResponse(response: Response) -> CardResult:
        """Convert success response to card entity

        Args:
            response: Input response

        Returns:
            CardResult: mapped result
        """
        entity = CardResult()

        if response.data:
            for key in response.data:
                if hasattr(entity, key):
                    setattr(entity, key, response.getData(key))

        return entity
