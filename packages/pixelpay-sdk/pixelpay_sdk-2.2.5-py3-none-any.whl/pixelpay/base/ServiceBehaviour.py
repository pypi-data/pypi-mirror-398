import requests
from .Response import Response
from ..exceptions import InvalidCredentialsException
from ..responses import ErrorResponse
from ..responses import FailureResponse
from ..responses import InputErrorResponse
from ..responses import NetworkFailureResponse
from ..responses import NoAccessResponse
from ..responses import NotFoundResponse
from ..responses import PayloadResponse
from ..responses import PaymentDeclinedResponse
from ..responses import PreconditionalResponse
from ..responses import SuccessResponse
from ..responses import TimeoutResponse
from ..base import RequestBehaviour
from ..models import Settings
from ..resources import Environment


class ServiceBehaviour:
    def __init__(self, settings: Settings):
        """Initialize service"""

        self._settings: Settings = settings
        """Settings service model"""

        self.__session: requests.Session = None
        """Request session for current service instance"""

    def close(self):
        if self.__session is not None:
            self.__session.close()

    def __parseResponse(self, response: requests.Response) -> Response:
        """Mapping and cast HTTP response

        Args:
            response: Response object from "requests" library

        Returns:
            Response: parsed Response
        """
        bag = Response()

        status = response.status_code

        if status == 200:
            bag = SuccessResponse()
        elif status == 202:
            bag = PayloadResponse()
        elif status == 400:
            bag = ErrorResponse()
        elif status == 401 or status == 403:
            bag = NoAccessResponse()
        elif status == 402:
            bag = PaymentDeclinedResponse()
        elif status == 404 or status == 405 or status == 406:
            bag = NotFoundResponse()
        elif status == 408:
            bag = TimeoutResponse()
        elif status == 412 or status == 418:
            bag = PreconditionalResponse()
        elif status == 422:
            bag = InputErrorResponse()
        elif status == 500:
            bag = FailureResponse()
        elif status > 500:
            bag = NetworkFailureResponse()

        data = response.json()

        bag.setStatus(status)
        bag.success = data["success"] if "success" in data else False
        bag.message = data["message"] if "message" in data else None
        bag.data = data["data"] if "data" in data else None
        bag.errors = data["errors"] if "errors" in data else None

        return bag

    def __exceptionResponse(self, e: Exception) -> Response:
        """Process the exception to Response object

        Args:
            e (Exception): thrown exception

        Returns:
            Response: processed response
        """
        response = FailureResponse()
        response.success = False
        response.message = str(e)
        response.setStatus(520)

        return response

    def __buildRequest(self, url: str, method: str, transaction: RequestBehaviour) -> requests.PreparedRequest:
        """Build HTTP request to API

        Args:
            url (str): request url
            method (str): HTTP method
            transaction (RequestBehaviour): body object

        Raises:
            InvalidCredentialsException: raised if no credentials found

        Returns:
            requests.PreparedRequest: built request
        """
        if not self._settings.auth_key or not self._settings.auth_hash:
            raise InvalidCredentialsException(
                "The merchant credentials are not definied (key/hash).")

        if self._settings.environment is not None:
            transaction.env = self._settings.environment

        if self._settings.lang is not None:
            transaction.lang = self._settings.lang

        headers = self._settings.headers.copy()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "PixelPay Python SDK/2",
            "x-auth-key": self._settings.auth_key,
            "x-auth-hash": self._settings.auth_hash,
        }

        if self._settings.auth_user:
            headers["x-auth-user"] = self._settings.auth_user

        full_route = self.__getRoute(url)
        body = transaction.toJson()

        request = requests.Request(url=full_route, headers=headers).prepare()
        request.prepare_method(method)
        request.prepare_body(body, None)

        return request

    def __getRoute(self, route: str):
        """Get API route

        Args:
            route (str): input route

        Returns:
            str: API route
        """
        return self._settings.endpoint + "/" + route

    def _post(self, url: str, body: RequestBehaviour) -> Response:
        """API POST request

        Args:
            url (str): input url
            body (RequestBehaviour): input body object

        Returns:
            Response: parsed response
        """
        try:
            env = Environment.ENV
            verify_cert = False if env == "test" else True

            self.__session = requests.Session()

            request = self.__buildRequest(url, "POST", body)
            response = self.__session.send(request, timeout=60, verify=verify_cert)
            self.close()

            return self.__parseResponse(response)
        except Exception as e:
            return self.__exceptionResponse(e)

    def _put(self, url: str, body: RequestBehaviour) -> Response:
        """API PUT request

        Args:
            url (str): input url
            body (RequestBehaviour): input body object

        Returns:
            Response: parsed response
        """
        try:
            env = Environment.ENV
            verify_cert = False if env == "test" else True

            self.__session = requests.Session()

            request = self.__buildRequest(url, "PUT", body)
            response = self.__session.send(request, timeout=60, verify=verify_cert)
            self.close()

            return self.__parseResponse(response)
        except Exception as e:
            return self.__exceptionResponse(e)

    def _delete(self, url: str, body: RequestBehaviour) -> Response:
        """API DELETE request

        Args:
            url (str): input url
            body (RequestBehaviour): input body object

        Returns:
            Response: parsed response
        """
        try:
            env = Environment.ENV
            verify_cert = False if env == "test" else True

            self.__session = requests.Session()

            request = self.__buildRequest(url, "DELETE", body)
            response = self.__session.send(request, timeout=60, verify=verify_cert)
            self.close()

            return self.__parseResponse(response)
        except Exception as e:
            return self.__exceptionResponse(e)

    def _get(self, url: str, body: RequestBehaviour) -> Response:
        """API GET request

        Args:
            url (str): input url
            body (RequestBehaviour): input body object

        Returns:
            Response: parsed response
        """
        try:
            env = Environment.ENV
            verify_cert = False if env == "test" else True

            self.__session = requests.Session()

            request = self.__buildRequest(url, "GET", body)
            response = self.__session.send(request, timeout=60, verify=verify_cert)
            self.close()

            return self.__parseResponse(response)
        except Exception as e:
            return self.__exceptionResponse(e)
