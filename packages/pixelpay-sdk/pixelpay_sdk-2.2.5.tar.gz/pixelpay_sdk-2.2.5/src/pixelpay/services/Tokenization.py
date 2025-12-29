from typing import List
from ..base import Response
from ..base import ServiceBehaviour
from ..base import RequestBehaviour
from ..models import Settings
from ..requests import CardTokenization


BASE_CARD_PATH = "api/v2/tokenization/card"


class Tokenization(ServiceBehaviour):
    def __init__(self, settings: Settings):
        """Initialize service"""
        super().__init__(settings)

    def vaultCard(self, card: CardTokenization) -> Response:
        """Vault credit/debit card and obtain a
        token card identifier (T-* format)

        Args:
            card (CardTokenization): input card

        Returns:
            Response: processed response
        """
        return self._post(BASE_CARD_PATH, card)

    def updateCard(self, token: str, card: CardTokenization) -> Response:
        """Update credit/debit card by token card identifier

        Args:
            token (str): input token
            card (CardTokenization): input card

        Returns:
            Response: processed response
        """
        return self._put(BASE_CARD_PATH + "/" + token, card)

    def showCard(self, token: str) -> Response:
        """Show credit/debit card metadata by token card identifier

        Args:
            token (str): input token

        Returns:
            Response: processed response
        """
        return self._get(BASE_CARD_PATH + "/" + token, RequestBehaviour())

    def showCards(self, tokens: List[str]) -> Response:
        """Show multiple credit/debit cards metadata by token card identifiers

        Args:
            tokens (list): input tokens

        Returns:
            Response: processed response
        """

        return self._get(BASE_CARD_PATH + "/" + ":".join(tokens), RequestBehaviour())

    def deleteCard(self, token: str) -> Response:
        """Delete credit/debit card metadata by token card identifier

        Args:
            token (str): input token

        Returns:
            Response: processed response
        """
        return self._delete(BASE_CARD_PATH + "/" + token, RequestBehaviour())
