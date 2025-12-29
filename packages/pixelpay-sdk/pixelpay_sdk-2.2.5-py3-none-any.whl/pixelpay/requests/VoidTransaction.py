from ..base import RequestBehaviour


class VoidTransaction(RequestBehaviour):
    def __init__(self):
        super().__init__()

        self.payment_uuid: str = None
        """Payment UUID"""

        self.void_reason: str = None
        """Reason for void the order"""

        self.void_signature: str = None
        """Required signature for void authentication"""
