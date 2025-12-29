from ..base import Helpers
from ..resources import Environment


class Settings:
    def __init__(self):
        """Initialize service"""

        self.auth_key: str = None
        """Merchant API auth key"""

        self.auth_hash: str = None
        """Merchant API auth hash (MD5 of secret key)"""

        self.auth_user: str = None
        """Merchant API platform auth user (SHA-512 of user email)"""

        self.endpoint: str = "https://pixelpay.app"
        """Merchant API endpoint URL"""

        self.environment: str = None
        """Merchant API environment"""

        self.lang: str = None
        """Settings response messages language"""

        self.headers: dict[str, str] = {}
        """Request headers"""

    def setupEndpoint(self, endpoint: str):
        """Setup API endpoint URL

        Args:
            endpoint (str): new endpoint URL
        """
        self.endpoint = endpoint

    def setupCredentials(self, key: str, hash: str):
        """Setup API Credentials

        Args:
            key (str): new auth key
            hash (str): new auth hash
        """
        self.auth_key = key
        self.auth_hash = hash

    def setupPlatformUser(self, hash: str):
        """Setup API platform user

        Args:
            hash (str): new auth user
        """
        self.auth_user = hash

    def setupEnvironment(self, env: str):
        """Setup API environment

        Args:
            env (str): new environment
        """
        self.environment = env

    def setupSandbox(self):
        """Setup defaults to Sandbox credentials"""
        self.endpoint = "https://pixelpay.dev"
        self.auth_key = "1234567890"
        self.auth_hash = Helpers.hash("MD5", "@s4ndb0x-abcd-1234-n1l4-p1x3l")
        self.environment = Environment.SANDBOX

    def setupLanguage(self, lang: str):
        """Setup response messages language"""
        self.lang = lang

    def setupHeaders(self, headers: dict[str, str]):
        """Setup request headers

        Args:
            headers (dict[str, str]): new request headers
        """
        self.headers = headers
