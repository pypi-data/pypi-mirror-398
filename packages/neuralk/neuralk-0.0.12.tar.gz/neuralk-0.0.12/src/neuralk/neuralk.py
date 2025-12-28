"""
Neuralk SDK main module.

This module provides the main interface for interacting with the Neuralk AI platform.
It handles authentication and provides access to various services through specialized handlers.
"""

import os
from http import HTTPStatus

import requests

from .exceptions import NeuralkException
from .handler.analysis_handler import AnalysisHandler
from .handler.auth_handler import AuthHandler
from .handler.dataset_handler import DatasetHandler
from .handler.organization_handler import OrganizationHandler
from .handler.project_file_handler import ProjectFileHandler
from .handler.project_handler import ProjectHandler
from .handler.user_handler import UserHandler
from .model.organization import Organization
from .utils._configuration import NEURALK_TIMEOUT, Configuration
from .utils._request_handler import RequestHandler


class HandlerDescriptor:
    def __init__(self, handler_type):
        self.handler_type = handler_type

    def __get__(self, instance, owner=None):
        if instance is None:
            return self.handler_type
        return self.handler_type(instance._request_handler)


class Neuralk:
    """
    Main class for interacting with the Neuralk AI platform.

    This class serves as the primary interface for the Neuralk SDK, providing access to
    various services through specialized handlers. It manages authentication and provides
    access to analysis, project, and user management functionality.

    Attributes:
        analysis (AnalysisHandler): Handler for analysis operations
        projects (ProjectHandler): Handler for project management operations
        users (UserHandler): Handler for user management operations
        project_files (ProjectFileHandler): Handler for project file management operations
        organization (OrganizationHandler): Handler for organization management operations

    Args:
        user_id (str): The user ID for authentication
        password (str): The password for authentication
        timeout (int, optional): Request timeout in seconds. Defaults to NEURALK_TIMEOUT s.
    """

    analysis = HandlerDescriptor(AnalysisHandler)
    projects = HandlerDescriptor(ProjectHandler)
    users = HandlerDescriptor(UserHandler)
    datasets = HandlerDescriptor(DatasetHandler)
    project_files = HandlerDescriptor(ProjectFileHandler)
    organization = HandlerDescriptor(OrganizationHandler)

    def __init__(
        self,
        user_id: str = None,
        password: str = None,
        timeout=NEURALK_TIMEOUT,
    ):
        """
        Initialize the Neuralk client.

        Args:
            user_id (str): The user ID for authentication
            password (str): The password for authentication
            timeout (int, optional): Request timeout in seconds. Defaults to NEURALK_TIMEOUT
        """
        user_id = user_id or os.environ.get("NEURALK_USERNAME", None)
        if not user_id:
            raise RuntimeError("Please set the NEURALK_USERNAME environment variable")
        password = password or os.environ.get("NEURALK_PASSWORD", None)
        if not password:
            raise RuntimeError("Please set the NEURALK_PASSWORD environment variable")
        self._request_handler = RequestHandler(user_id, password, timeout)
        self.auth_handler = AuthHandler(self._request_handler)
        self.auth_handler.login()

    def logout(self):
        """
        Log out from the Neuralk AI platform.

        Returns:
            bool: True if logout was successful, False otherwise
        """
        return self.auth_handler.logout()

    def __del__(self):
        try:
            self.logout()
        except Exception:
            pass


Neuralk.__doc__ = Neuralk.__doc__.replace("NEURALK_TIMEOUT", str(NEURALK_TIMEOUT))

_NEURALK_CLIENT = None


def get_client(user_id=None, password=None):
    global _NEURALK_CLIENT
    if _NEURALK_CLIENT is None:
        _NEURALK_CLIENT = Neuralk(user_id, password)
    return _NEURALK_CLIENT


def create_account(
    access_code: str,
    organization_name: str,
    email: str,
    firstname: str,
    lastname: str,
    password: str,
) -> Organization:
    """
    Creates an account and an organization using a specific access code.

    Args:
        access_code (str): The access code given by Neuralk
        organization_name (str): The name of the organization
        email (str): The email of the user
        firstname (str): The firstname of the user
        lastname (str): The lastname of the user
        password (str): The password of the user

    Returns:
        Organization: The created organization

    Raises:
        NeuralkException: If creating the organization fails
    """
    resp = requests.put(
        f"{Configuration.neuralk_endpoint}/auth/create-account",
        data={
            "access_code": access_code,
            "organization_name": organization_name,
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "password": password,
        },
    )

    if resp.status_code != HTTPStatus.OK:
        raise NeuralkException.from_resp("Cannot create organization", resp)

    organization = Organization._from_json(resp.json())

    return organization
