import locale
from .Helpers import Helpers
from .. import __version__


class RequestBehaviour:
    def __init__(self):
        """Initialize request"""
        [rfc1766, _] = locale.getdefaultlocale()
        lang = None
        if rfc1766:
            lang = rfc1766.split("_")[0]

        if lang != "es" or lang != "en":
            lang = "es"

        self.env: str = None
        """Environment identifier (live|test|sandbox)"""

        self.lang: str = lang
        """Transaction response messages language"""

        self.from_type: str = "sdk-python"
        """SDK identifier type"""

        self.sdk_version: str = __version__
        """SDK version"""

    def toJson(self) -> str:
        """Serialize object to JSON string

        Returns:
            str: JSON string
        """

        # because "from" is a reserved keyword,
        # we temporarily change the attribute "from_type" to "from"
        if self.from_type:
            setattr(self, "from", self.from_type)
            delattr(self, "from_type")

        json_output = Helpers.objectToJson(self)

        # restore the previous changes
        from_attr = getattr(self, "from")
        if from_attr:
            setattr(self, "from_type", from_attr)
            delattr(self, "from")

        return json_output
