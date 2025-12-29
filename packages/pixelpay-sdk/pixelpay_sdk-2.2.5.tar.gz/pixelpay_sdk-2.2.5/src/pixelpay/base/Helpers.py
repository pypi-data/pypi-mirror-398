import json
import hashlib


class _Object:
    pass


class Helpers:
    def __init__(self):
        """Prevent implicit public contructor

        Raises:
            ValueError: Utility class
        """
        raise ValueError("Utility class")

    @staticmethod
    def objectToJson(value: object) -> str:
        """Serialize object to JSON string without empties

        Args:
            value (object): object to serialize

        Returns:
            str: JSON string
        """
        temp_object = _Object()
        for key, val in value.__dict__.items():
            if val is not None and val != "":
                setattr(temp_object, key.lstrip("_"), val)
        return json.dumps(temp_object, default=lambda o: o.__dict__)

    @staticmethod
    def hash(algorithm: str, value: str) -> str:
        encoded_value = value.encode("utf-8")
        if algorithm == "MD5":
            return hashlib.md5(encoded_value).hexdigest()
        elif algorithm == "SHA-512":
            return hashlib.sha512(encoded_value).hexdigest()
        return ""

    @staticmethod
    def trimValue(value: str) -> str:
        """Trim a string/null value

        Args:
            value (str): input value

        Returns:
            str: trimmed value or empty string
        """
        if value:
            return value.strip()

        return ""

    @staticmethod
    def cleanString(value: str) -> str:
        """Clean whitespaces from string

        Args:
            value (str): input value

        Returns:
            str: trimmed value or empty string
        """
        if value:
            return value.replace(" ", "")

        return ""

    @staticmethod
    def parseAmount(amount: float) -> str:
        """Parse or nullify amount data

        Args:
            amount (float): input amount

        Returns:
            str: parsed amount or empty string
        """
        if amount is None:
            return ""

        if amount > 0:
            return "{:.2f}".format(amount)

        return ""
