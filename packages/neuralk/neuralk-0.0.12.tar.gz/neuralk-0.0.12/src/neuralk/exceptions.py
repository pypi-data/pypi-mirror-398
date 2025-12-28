"""
Neuralk exception module.

This module defines the custom exception used throughout the Neuralk AI SDK.
"""

from http import HTTPStatus

import requests


class NeuralkException(RuntimeError):
    """
    Custom exception for errors raised by the Neuralk AI SDK.

    Attributes:
        message (str): The error message.
        status_code (HTTPStatus): The HTTP status code associated with the error.
        details (str): Additional details about the error.
    """

    def __init__(self, message: str, status_code: HTTPStatus, details: str):
        """
        Initialize a NeuralkException instance.

        Args:
            message (str): The error message.
            status_code (HTTPStatus): The HTTP status code associated with the error.
            details (str): Additional details about the error.
        """
        super().__init__(message, status_code, details)
        self.message = message
        self.status_code = status_code
        self.details = details

    @staticmethod
    def from_resp(msg: str, resp: requests.Response) -> "NeuralkException":
        """
        Create a NeuralkException from an HTTP response.

        Args:
            msg (str): The error message.
            resp (requests.Response): The HTTP response object.

        Returns:
            NeuralkException: The constructed exception instance.
        """
        return NeuralkException(msg, resp.status_code, resp.text)
