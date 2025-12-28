"""
User handler module.

This module provides functionality for managing user information with the Neuralk AI platform,
including retrieving and updating user details.
"""

from http import HTTPStatus

from ..exceptions import NeuralkException
from ..model.organization import Organization
from ..model.user import User
from ..utils._request_handler import RequestHandler
from ..utils.organization_role import OrganizationRole


class UserHandler:
    """
    Handler for user operations with the Neuralk AI platform.

    This class manages user information, including retrieving and updating user details.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the UserHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests
        """
        self._request_handler = request_handler

    def create(
        self,
        email: str,
        firstname: str,
        lastname: str,
        password: str,
    ) -> User:
        """
        Create a new user in the Neuralk AI platform.

        Args:
            email (str): The email address of the new user.
            firstname (str): The first name of the new user.
            lastname (str): The last name of the new user.
            password (str): The password for the new user.

        Returns:
            User: The created user object.

        Raises:
            NeuralkException: If user creation fails.
        """
        resp = self._request_handler.put(
            "user/create",
            data={
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "password": password,
            },
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot create user", resp)

        user = User._from_json(resp.json())

        return user

    def get(self) -> User:
        """
        Get information about the currently authenticated user.

        Returns:
            User: The current user object

        Raises:
            NeuralkException: If retrieving the user information fails
        """
        resp = self._request_handler.get("user/current")

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get user info", resp)

        user = User._from_json(resp.json())

        return user

    def delete(self, email: str):
        """
        Delete a user from the Neuralk AI platform.

        Args:
            email (str): The email address of the user to delete.

        Raises:
            NeuralkException: If user deletion fails.
        """
        resp = self._request_handler.delete(
            "user/delete",
            data={
                "email": email,
            },
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot create user", resp)

    def update_info(self, user: User) -> User:
        """
        Update user information.

        Args:
            user (User): The user object containing updated information

        Returns:
            User: The updated user object

        Raises:
            NeuralkException: If updating the user information fails
        """

        resp = self._request_handler.post(
            "user/update-info",
            data={
                "firstname": user.firstname,
                "lastname": user.lastname,
            },
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot update user info", resp)

        user = User._from_json(resp.json())

        return user

    def change_password(self, new_password: str) -> None:
        """
        Update user password.

        Args:
            new_password (str): The new password

        Raises:
            NeuralkException: If updating the user password fails
        """

        resp = self._request_handler.post(
            "user/change-password",
            data={"new_password": new_password},
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot update user password", resp)
