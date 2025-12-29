from __future__ import annotations
from ..base import Response
from ..responses import InputErrorResponse
from ..responses import PaymentDeclinedResponse
from ..responses import SuccessResponse
from ..responses import TimeoutResponse

class TransactionResult:
    def __init__(self):
        self.transaction_type: str = None
        """Transaction response type"""

        self.transaction_redeemed_points: float = None
        """Transaction redeemed points"""

        self.transaction_approved_amount: float = None
        """Approved amount on capture/sale"""

        self.transaction_amount: float = None
        """Initial or registered transaction amount"""

        self.transaction_auth: str = None
        """Transaction AUTH reference code"""

        self.transaction_terminal: str = None
        """Transacction network terminal ID"""

        self.transaction_merchant: str = None
        """Transaction network merchant ID"""

        self.response_cvn: str = None
        """CVV2 result response code"""

        self.response_avs: str = None
        """Address verification code response"""

        self.response_cavv: str = None
        """CAVV network evaluation result code"""

        self.transaction_id: str = None
        """Transaction identifier"""

        self.transaction_reference: str = None
        """Transaction STAN, proccesor transacction identifier or transaction reference"""

        self.transaction_time: str = None
        """Transaction result time"""

        self.transaction_date: str = None
        """Transaction result date"""

        self.response_approved: bool = None
        """Response is financial approved"""

        self.response_incomplete: bool = None
        """Response fatal not completed or excecution interrupted"""

        self.response_code: str = None
        """Proccesor response code"""

        self.response_time: str = None
        """Network response time"""

        self.response_reason: str = None
        """Proccesor response message"""

        self.installment_type: str = None
        """Transaction installment type"""

        self.installment_months: str = None
        """Transaction installment value"""

        self.payment_uuid: str = None
        """Payment unique identifier"""

        self.payment_hash: str = None
        """Payment integrity validation hash"""

    @staticmethod
    def validateResponse(response: Response) -> bool:
        """Validate if response type is valid for parse

        Args:
            response: Response to validate

        Returns:
            bool: is valid response
        """
        return isinstance(response, SuccessResponse) or isinstance(response, PaymentDeclinedResponse) or isinstance(response, InputErrorResponse) or isinstance(response, TimeoutResponse)

    @staticmethod
    def fromResponse(response: Response) -> TransactionResult:
        """Convert success response to transaction entity

        Args:
            response: Input response

        Returns:
            TransactionResult: mapped result
        """
        entity = TransactionResult()

        if response.data:
            for key in response.data:
                if hasattr(entity, key):
                    setattr(entity, key, response.getData(key))

        return entity
