import os
from email.quoprimime import body_check
from http import HTTPStatus

import requests

from ..exceptions import NeuralkException
from ..model.project import Project
from ..model.project_file import ProjectFile
from ..utils._configuration import Configuration
from ..utils._files import get_file_format
from ..utils._request_handler import RequestHandler


class ProjectFileHandler:
    """
    Handler for project file operations with the Neuralk AI platform.

    This class manages the upload of project files (e.g., taxonomy, schema) to object storage.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests.
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the ProjectFileHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests.
        """
        self._request_handler = request_handler

    def create(self, project: Project, name: str, file_path: str) -> ProjectFile:
        """
        Create a new project file and upload it to object storage.

        Args:
            project (Project): The project to which the file belongs.
            name (str): The name of the file.
            file_path (str): The path to the file.

        Returns:
            ProjectFile: The created project file object.

        Raises:
            NeuralkException: If the file upload fails.
        """
        file_size = os.path.getsize(file_path)
        file_format = get_file_format(file_path)
        response_upload_csv = self._request_handler.post(
            "project-file/get-taxonomy-upload-file-link",
            data={
                "file_size": file_size,
                "project_hash_id": project.id,
                "name": name,
                "file_format": file_format,
                "file_name": os.path.basename(file_path),
            },
        )
        if response_upload_csv.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot get pre-signed upload url", response_upload_csv
            )

        with open(file_path, "rb") as file_data:
            signed_url = response_upload_csv.json()["signed_url"]

            if Configuration.debug_mode:
                signed_url = signed_url.replace("object-storage", "localhost").replace(
                    "9023", "50023"
                )
            response_gcp = requests.put(
                signed_url,
                data=file_data,
                headers={"Content-Type": "text/csv"},
            )

            if response_gcp.status_code != HTTPStatus.OK:
                raise NeuralkException.from_resp(
                    "Cannot upload file to the object-storage", response_upload_csv
                )
        return ProjectFile._from_json(response_upload_csv.json()["project_file"])

    def delete(self, project_file: str | ProjectFile) -> None:
        """
        Delete a project file.

        Args:
            project_file (str | ProjectFile): The project file object or its id to delete.

        Raises:
            NeuralkException: If the project file deletion fails.
        """
        if isinstance(project_file, ProjectFile):
            project_file = project_file.id

        resp = self._request_handler.delete(
            "project-file/delete",
            params={"hash_id": project_file},
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot delete project file", resp)
