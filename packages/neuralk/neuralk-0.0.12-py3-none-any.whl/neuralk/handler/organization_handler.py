import os
from email.quoprimime import body_check
from http import HTTPStatus

import requests

from ..exceptions import NeuralkException

from ..model.organization import Organization
from ..utils._request_handler import RequestHandler


class OrganizationHandler:
    """
    Handler for organization operations with the Neuralk AI platform.

    This class manages the retrieval of organization information.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests.
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the OrganizationHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests.
        """
        self._request_handler = request_handler

    def get(self) -> Organization:
        """
        Retrieve the current organization information.

        Returns:
            Organization: The current organization object.

        Raises:
            NeuralkException: If retrieving the organization information fails.
        """
        resp = self._request_handler.get("organization/get")
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get organization", resp)

        project = Organization._from_json(resp.json())

        return project

    def get_running_job_number(self) -> int:
        """
        Retrieve the number of running and pending analyses for an organization.

        Returns:
            int: The number of pending and running analyses.

        Raises:
            NeuralkException: If retrieving the organization information fails.
        """
        resp = self._request_handler.get("organization/get-running-jobs")
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get organization", resp)

        return resp.json()["running_job_number"]
    
    def get_credits_available(self) -> float:
        """
        Retrieve the number of credits available for an organization.

        Returns:
            float: The number of credits available.
        """
        organization = self.get()
        return organization.credits
