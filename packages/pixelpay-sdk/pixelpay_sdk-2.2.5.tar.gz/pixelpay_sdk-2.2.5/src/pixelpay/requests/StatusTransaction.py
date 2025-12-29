from ..base import RequestBehaviour


class StatusTransaction(RequestBehaviour):
    def __init__(self):
        super().__init__()

        self.payment_uuid: str = None
        """Payment UUID"""
