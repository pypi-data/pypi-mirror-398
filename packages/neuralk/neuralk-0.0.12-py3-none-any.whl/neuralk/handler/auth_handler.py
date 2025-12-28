"""
Authentication handler module.

This module provides functionality for user authentication with the Neuralk AI platform,
including login and logout operations.
"""

from ..exceptions import NeuralkException

from ..utils._request_handler import RequestHandler


class AuthHandler:
    """
    Handler for authentication operations with the Neuralk AI platform.

    This class manages user authentication, including login and logout operations.
    It uses the provided RequestHandler to make HTTP requests to the authentication endpoints.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the AuthHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests
        """
        self._request_handler = request_handler

    def login(self):
        """
        Authenticate the user with the Neuralk AI platform.

        This method attempts to log in using the credentials provided during initialization.
        Upon successful login, it stores the access and refresh tokens in the request handler.

        Raises:
            NeuralkException: If the login fails due to invalid credentials or other errors
        """
        resp = self._request_handler.post(
            "auth/login",
            data={
                "username": self._request_handler.user_id,
                "password": self._request_handler.password,
            },
        )
        if resp.status_code != 200:
            raise NeuralkException.from_resp("Bad login/password combination", resp)

        self._request_handler.access_token = resp.json()["access_token"]
        self._request_handler.refresh_token = resp.json()["refresh_token"]

    def logout(self):
        """
        Log out the user from the Neuralk AI platform.

        This method invalidates the current session by sending a logout request
        with the refresh token.

        Returns:
            Response: The response from the logout request

        Raises:
            NeuralkException: If the logout fails
        """
        resp = self._request_handler.post(
            "auth/logout", data={"refresh_token": self._request_handler.refresh_token}
        )
        if resp.status_code != 200:
            raise NeuralkException.from_resp("Cannot logout properly", resp)
        return resp
