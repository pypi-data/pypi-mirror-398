from ..base import Response
from ..base import ServiceBehaviour
from ..models import Settings
from ..requests import AuthTransaction
from ..requests import SaleTransaction
from ..requests import CaptureTransaction
from ..requests import StatusTransaction
from ..requests import VoidTransaction
from ..requests import PaymentTransaction
from ..responses import PayloadResponse
from ..libraries.RouterManager import RouterManager
from ..exceptions import InvalidTransactionTypeException


class Transaction(ServiceBehaviour):
    def __init__(self, settings: Settings):
        """Initialize service"""
        super().__init__(settings)

    def _evalAuthenticationTransaction(self, transaction: PaymentTransaction):
        if transaction.authentication_request:
            raise InvalidTransactionTypeException("This platform does not support 3DS transactions")

    def doSale(self, transaction: SaleTransaction) -> Response:
        """Send and proccesing SALE transaction

        Args:
            transaction (SaleTransaction): input

        Returns:
            Response: processed response
        """
        self._evalAuthenticationTransaction(transaction)

        response = self._post("api/v2/transaction/sale", transaction)

        if isinstance(response, PayloadResponse):
            transaction_type = getattr(response, "data", {}).get("transaction_type")
            if transaction_type == "router":
                return RouterManager(transaction).init(getattr(response, "data", {}).get("payload", ""))
            else:
                return response
        return response

    def doAuth(self, transaction: AuthTransaction) -> Response:
        """Send and proccesing AUTH transaction

        Args:
            transaction (AuthTransaction): input

        Returns:
            Response: processed response
        """
        self._evalAuthenticationTransaction(transaction)

        response = self._post("api/v2/transaction/auth", transaction)

        if isinstance(response, PayloadResponse):
            transaction_type = getattr(response, "data", {}).get("transaction_type")
            if transaction_type == "router":
                return RouterManager(transaction).init(getattr(response, "data", {}).get("payload", ""))
            else:
                return response
        return response

    def doCapture(self, transaction: CaptureTransaction) -> Response:
        """Send and proccesing CAPTURE transaction

        Args:
            transaction (CaptureTransaction): input

        Returns:
            Response: processed response
        """

        return self._post("api/v2/transaction/capture", transaction)

    def doVoid(self, transaction: VoidTransaction) -> Response:
        """Send and proccesing VOID transaction

        Args:
            transaction (VoidTransaction): input

        Returns:
            Response: processed response
        """

        return self._post("api/v2/transaction/void", transaction)

    def getStatus(self, transaction: StatusTransaction) -> Response:
        """Get transaction status

        Args:
            transaction (StatusTransaction): input

        Returns:
            Response: processed response
        """

        return self._post("api/v2/transaction/status", transaction)
