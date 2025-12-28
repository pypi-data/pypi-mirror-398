"""
Project handler module.

This module provides functionality for managing projects with the Neuralk AI platform,
including creating, retrieving, deleting projects, and managing project users.
"""

from http import HTTPStatus
from typing import Literal, Tuple

from ..exceptions import NeuralkException

from ..model.analysis import Analysis
from ..model.project import Project
from ..model.user import User
from ..utils._request_handler import RequestHandler
from ..utils.project_role import ProjectRole


class ProjectHandler:
    """
    Handler for project operations with the Neuralk AI platform.

    This class manages the creation, retrieval, and deletion of projects,
    as well as user management within projects.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the ProjectHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests
        """
        self._request_handler = request_handler

    def create(self, name: str, exist_ok=False) -> Project:
        """
        Create a new project.

        Args:
            name (str): The name of the project to create
            exist_ok (bool): If True, return the project without errors if it exists.

        Returns:
            Project: The created or found project object

        Raises:
            NeuralkException: If the project creation fails
        """
        if exist_ok:
            project = next((p for p in self.get_list() if p.name == name), None)
            if project is not None:
                return project
        resp = self._request_handler.put("project/create", data={"name": name})
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot create project", resp)

        project = Project._from_json(resp.json())

        return project

    def get(self, project_id: str) -> Project:
        """
        Retrieve a project by its ID.

        Args:
            project_id (str): The ID of the project to retrieve

        Returns:
            Project: The retrieved project object

        Raises:
            NeuralkException: If the project retrieval fails
        """
        resp = self._request_handler.get("project/get", params={"hash_id": project_id})
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get project", resp)

        project = Project._from_json(resp.json())

        return project

    def delete(self, project: str | Project) -> None:
        """
        Delete a project.

        Args:
            project (str | Project): The project object or its id to delete.

        Raises:
            NeuralkException: If the project deletion fails.
        """
        if isinstance(project, Project):
            project = project.id

        resp = self._request_handler.delete(
            "project/delete",
            params={"hash_id": project},
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot delete project", resp)

    def add_user(
        self,
        project: str | Project,
        user_email: str,
        role: Literal["owner", "contributor", "member"] = "member",
    ) -> None:
        """
        Add a user to a project by project ID with a specific role.

        Args:
            project (str|Project): The project to add the user to or its ID .
            user_email (str): The email of the user to add
            role (str): The role to assign to the user. Default is "member".
            Available roles:
            - "owner" (full access to the project)
            - "contributor" (can launch analyses but not delete the project)
            - "member" (can access to existing analyses)

        Raises:
            NeuralkException: If adding the user fails
        """
        if isinstance(project, Project):
            project = project.id

        if role not in ["owner", "contributor", "member"]:
            raise ValueError(
                f"Invalid role. Available roles: owner, contributor, member. Got {role}"
            )
        role = ProjectRole(role)

        resp = self._request_handler.post(
            "project/add-user-to-project",
            data={
                "project_hash_id": project,
                "user_email": user_email,
                "role": role.name,
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot add user to project", resp)

    def delete_user(self, project: str | Project, user_email: str) -> None:
        """
        Remove a user from a project by project ID.

        Args:
            project (str|Project): The project to remove the user from or its ID
            user_email (str): The email of the user to remove

        Raises:
            NeuralkException: If removing the user fails
        """
        if isinstance(project, Project):
            project = project.id
        resp = self._request_handler.delete(
            "project/delete-user-from-project",
            data={
                "project_hash_id": project,
                "user_email": user_email,
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot delete user from project", resp)

    def list_user(self, project: Project | str) -> list[Tuple[str, User]]:
        """
        Get the list of users in a project.

        Args:
            project (Project): The project to get users from or its id

        Returns:
            list[User]: List of users in the project
        """
        if isinstance(project, Project):
            project = project.id

        project = self.get(project)

        return project.user_list

    def get_active_analyses(self, project: Project | str) -> list[Analysis]:
        """
        Retrieve the list of pending or in progress analyses for a project.

        Args:
            project_id (str): The ID of the project or its hash_id

        Returns:
            list[Analysis]: The list of pending analysis

        Raises:
            NeuralkException: If the project retrieval fails
        """
        if isinstance(project, Project):
            project = project.id

        resp = self._request_handler.get(
            "project/get-pending-analysis-list", params={"hash_id": project}
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get pending analysis list", resp)

        resp_json = resp.json()

        analysis_list: list[Analysis] = []
        if "analysis_list" in resp_json:
            for analysis_json in resp_json["analysis_list"]:
                analysis_list.append(Analysis._from_json(analysis_json))

        return analysis_list

    def get_list(self) -> list[Project]:
        """
        Get the list of all projects accessible to the current user.

        Returns:
            list[Project]: List of accessible projects

        Raises:
            NeuralkException: If retrieving the project list fails
        """
        resp = self._request_handler.get("project/get-project-list")
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get project list", resp)

        resp_json = resp.json()

        project_list: list[Project] = []
        if "project_list" in resp_json:
            for project_json in resp_json["project_list"]:
                project_list.append(Project._from_json(project_json))

        return project_list
