import os
from http import HTTPStatus

import requests

from ..exceptions import NeuralkException
from ..model.dataset import Dataset
from ..model.project import Project
from ..utils._configuration import Configuration
from ..utils._files import get_file_format
from ..utils._request_handler import RequestHandler
from ..utils.execution import Waiter


class DatasetHandler:
    """
    Handler for dataset operations with the Neuralk AI platform.

    This class manages the creation, retrieval, and deletion of datasets.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests.
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the DatasetHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests.
        """
        self._request_handler = request_handler

    def create_from_url(
        self,
        project: Project | str,
        name: str,
        file_name: str,
        file_url: str,
        file_format: str,
    ) -> Dataset:
        """
        Create a new dataset from a distant url

        Args:
            project (Project): The project to which the dataset belongs or its hash_id.
            name (str): The name of the dataset.
            file_name (str): The name of the uploaded file.
            file_url (str): The url of the uploaded file.
            file_format (str): The format of the uploaded file.

        Returns:
            Dataset: The created dataset object.

        Raises:
            NeuralkException: If the dataset creation or upload fails.
        """
        if isinstance(project, Project):
            project = project.id

        response_upload_csv = self._request_handler.post(
            "dataset/upload-from-url",
            data={
                "project_hash_id": project,
                "name": name,
                "file_url": file_url,
                "file_format": file_format,
                "file_name": file_name,
            },
        )
        if response_upload_csv.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot upload file", response_upload_csv)
        return Dataset._from_json(response_upload_csv.json())

    def _get_upload_url(self, project_id: str, name: str, file_path: str) -> str:
        file_size = os.path.getsize(file_path)
        file_format = get_file_format(file_path)
        response_upload_csv = self._request_handler.post(
            "dataset/get-upload-csv-link",
            data={
                "file_size": file_size,
                "project_hash_id": project_id,
                "name": name,
                "file_format": file_format,
                "file_name": os.path.basename(file_path),
            },
        )
        if response_upload_csv.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot get pre-signed upload url", response_upload_csv
            )
        return response_upload_csv

    def create(self, project: Project | str, name: str, file_path: str) -> Dataset:
        """
        Create a new dataset and upload its file to object storage.

        Args:
            project (Project): The project to which the dataset belongs or its hash_id.
            name (str): The name of the dataset.
            file_path (str): The path to the dataset file.

        Returns:
            Dataset: The created dataset object.

        Raises:
            NeuralkException: If the dataset creation or upload fails.
        """
        if isinstance(project, Project):
            project = project.id

        response_upload_csv = self._get_upload_url(project, name, file_path)

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
        return Dataset._from_json(response_upload_csv.json()["dataset"])

    def get(self, dataset_id: str) -> Dataset:
        """
        Retrieve a dataset by its ID.

        Args:
            dataset_id (str): The ID of the dataset to retrieve.

        Returns:
            Dataset: The retrieved dataset object.

        Raises:
            NeuralkException: If the dataset retrieval fails.
        """
        resp = self._request_handler.get("dataset/get", params={"hash_id": dataset_id})
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get dataset", resp)

        dataset = Dataset._from_json(resp.json())

        return dataset

    def delete(self, dataset: str | Dataset) -> None:
        """
        Delete a dataset.

        Args:
            dataset (str | Dataset): The dataset object or its id to delete.

        Raises:
            NeuralkException: If the dataset deletion fails.
        """
        if isinstance(dataset, Dataset):
            dataset = dataset.id

        resp = self._request_handler.delete(
            "dataset/delete",
            params={"hash_id": dataset},
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot delete dataset", resp)

    def wait_until_complete(
        self,
        dataset: str | Dataset,
        refresh_time: float = 1.0,
        timeout: float = None,
        verbose: bool = False,
    ):
        """
        Wait for analysis until it is finished.

        Args:
            analysis (Analysis or str): the analysis to wait for, or its ID.
            refresh_time (float): time (in seconds) between status checks.
            timeout (float, optional): maximum time to wait in seconds.
            verbose (bool): whether to display status messages.

        Returns:
            Analysis: the final analysis object.
        """

        if isinstance(dataset, str):
            dataset = self.get(dataset)

        waiter = Waiter(
            "Dataset status: ",
            refresh_time,
            timeout=timeout,
            verbose=verbose,
            terminal_statuses=["OK", "ERROR_MISSING_FILE"],
        )

        while waiter.not_complete():
            dataset = self.get(dataset.id)
            status = dataset.status
            waiter.update_status(status)

        return dataset
