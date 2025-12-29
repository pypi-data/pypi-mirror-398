from ..base import RequestBehaviour


class CaptureTransaction(RequestBehaviour):
    def __init__(self):
        super().__init__()

        self.payment_uuid: str = None
        """Payment UUID"""

        self.transaction_approved_amount: str = None
        """The total amount to capture,
        equal to or less than the authorized amount.
        """
