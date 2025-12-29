from typing import Any, Dict, List, Optional
from .Helpers import Helpers


class Response:
    def __init__(self):
        self._status: int = None
        """HTTP response status code"""

        self._action: str = None
        """Response 'action to' format"""

        self._exception: dict = None
        """Exception response details"""

        self.success: bool = None
        """Response status success"""

        self.message: str = None
        """Response friendly message"""

        self.data: dict = None
        """Response data payload"""

        self.errors: Dict[str, List[str]] = None
        """Response input validation felds errors"""

    def setStatus(self, status: int):
        """Define HTTP status code response

        Args:
            status (int): status code
        """
        self._status = status

    def getStatus(self) -> int:
        """Get HTTP status code

        Returns:
            int: status code
        """
        return self._status

    def inputHasError(self, key: str) -> bool:
        """Verify input has error

        Args:
            key (str): input key

        Returns:
            bool: input on key has errors or not
        """
        if self.errors is None:
            return False

        return key in self.errors

    def getData(self, key: str) -> Optional[Any]:
        """Get data payload by key

        Args:
            key (str): input key

        Returns:
            Any: data or None
        """
        if self.data is None:
            return None

        if key not in self.data:
            return None

        return self.data[key]

    def toJson(self) -> str:
        """Serialize object to JSON string

        Returns:
            str: JSON string
        """
        return Helpers.objectToJson(self)
