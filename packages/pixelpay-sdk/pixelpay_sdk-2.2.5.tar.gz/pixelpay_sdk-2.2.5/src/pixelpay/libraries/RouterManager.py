from ..requests import PaymentTransaction, SaleTransaction
from ..services import Transaction
from ..models import Settings
from ..base import Response
import base64
import json

class RouterManager:
    """
    RouterManager handles payment and sale transactions.
    """

    def __init__(self, request: PaymentTransaction):
        """
        Initialize service.
        :param request: PaymentTransaction
        """
        self.transaction: PaymentTransaction = request
        self.identifier: str | None = None
        self.transaction.source = 'router'

    def init(self, payload: str) -> Response:
        """
        Initialize manager.
        :param payload: str
        :return: Response
        """
        service = Transaction(self.parse_payload(payload))

        if isinstance(self.transaction, SaleTransaction):
            return service.doSale(self.transaction)
        else:
            return service.doAuth(self.transaction)

    def parse_payload(self, payload: str) -> Settings:
        """
        Parse the payload string to Settings object.
        :param payload: str
        :return: Settings
        """
        obj_payload = json.loads(base64.b64decode(payload).decode('utf-8'))
        settings = Settings()

        settings.setupEnvironment(obj_payload.get('env'))
        settings.setupCredentials(obj_payload.get('auth_key'), obj_payload.get('auth_hash'))
        settings.setupEndpoint(obj_payload.get('endpoint'))
        settings.setupLanguage(getattr(self.transaction, 'lang', None))

        if obj_payload.get('auth_user'):
            settings.setupPlatformUser(obj_payload['auth_user'])

        return settings
