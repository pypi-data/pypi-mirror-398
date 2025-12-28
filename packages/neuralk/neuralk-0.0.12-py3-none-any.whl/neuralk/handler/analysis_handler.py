"""
Analysis handler module.

This module provides functionality for managing analysis operations with the Neuralk AI platform,
including creating, retrieving, saving, and deleting analyses.
"""

import json
import os
from functools import wraps
from http import HTTPStatus

import requests

from ..exceptions import NeuralkException
from ..model.analysis import Analysis
from ..model.dataset import Dataset
from ..model.project_file import ProjectFile
from ..utils._configuration import Configuration
from ..utils._request_handler import RequestHandler
from ..utils.execution import Waiter
from .organization_handler import OrganizationHandler
from ..utils import logger

_MAX_RUNNING_ANALYSES = 1


def call_get_rank_in_queue(func):
    """
    Decorator that calls self.get_rank_in_queue after the method executes.
    
    The method should return an Analysis object, which is then passed to
    get_rank_in_queue before returning it.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        analysis = func(self, *args, **kwargs)
        self.get_rank_in_queue(analysis)
        return analysis
    return wrapper


class AnalysisHandler:
    """
    Handler for analysis operations with the Neuralk AI platform.

    This class manages the creation, retrieval, saving, and deletion of analyses.
    It handles file uploads to object storage and manages analysis metadata.

    Args:
        request_handler (RequestHandler): The request handler instance used for making HTTP requests
    """

    def __init__(self, request_handler: RequestHandler):
        """
        Initialize the AnalysisHandler.

        Args:
            request_handler (RequestHandler): The request handler instance used for making HTTP requests
        """
        self._request_handler = request_handler

    @call_get_rank_in_queue
    def create_classifier_fit(
        self,
        dataset: Dataset,
        name: str,
        target_column: str,
        id_columns: list[str] = None,
        feature_column_name_list: list[str] = None,
        fast_nicl_mode: bool = False,
    ) -> Analysis:
        """
        Create a new classifier fit analysis.

        Args:
            dataset (Dataset): The dataset to use for the analysis.
            name (str): The name of the analysis.
            target_column (str): The target column name.
            id_columns (list[str], optional): List of ID column names.
            feature_column_name_list (list[str], optional): List of feature column names.

        Returns:
            Analysis: The created analysis object.

        Raises:
            NeuralkException: If the analysis creation fails.
        """
        self._check_n_analyses()
        resp = self._request_handler.put(
            "analysis/create-classification-fit",
            data={
                "name": name,
                "fast_nicl_mode": json.dumps(fast_nicl_mode),
                "dataset_hash_id": dataset.id,
                "target_column": target_column,
                "id_columns": (json.dumps(id_columns) if id_columns != None else None),
                "feature_column_name_list": (
                    json.dumps(feature_column_name_list)
                    if feature_column_name_list != None
                    else None
                ),
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot create classifier fit analysis", resp
            )

        analysis = Analysis._from_json(resp.json())

        return analysis

    @call_get_rank_in_queue
    def create_classifier_predict(
        self,
        dataset: Dataset,
        name: str,
        classifier_fit_analysis: str | Analysis,
        fast_nicl_mode: bool = False,
    ) -> Analysis:
        """
        Create a new classifier predict analysis from a fit analysis.

        Args:
            dataset (Dataset): The dataset to use for prediction.
            name (str): The name of the prediction analysis.
            classifier_fit_analysis (str | Analysis): The fit analysis object or its id.

        Returns:
            Analysis: The created prediction analysis object.

        Raises:
            NeuralkException: If the analysis creation fails.
        """
        self._check_n_analyses()
        if isinstance(classifier_fit_analysis, Analysis):
            classifier_fit_analysis = classifier_fit_analysis.id

        resp = self._request_handler.put(
            "analysis/create-classification-predict",
            data={
                "name": name,
                "fast_nicl_mode": json.dumps(fast_nicl_mode),
                "dataset_hash_id": dataset.id,
                "fit_analysis_hash_id": classifier_fit_analysis,
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot create classifier fit analysis", resp
            )

        analysis = Analysis._from_json(resp.json())

        return analysis

    @call_get_rank_in_queue
    def create_categorization_fit(
        self,
        dataset: Dataset,
        name: str,
        taxonomy_file: ProjectFile | str = None,
        target_columns: list[str] = None,
        id_columns: list[str] = None,
        categorizer_feature_cols: list[str] = None,
    ) -> Analysis:
        """
        Create a new categorization fit analysis.

        Args:
            dataset (Dataset): The dataset to use for the analysis.
            name (str): The name of the analysis.
            target_columns (list[str], optional): The target column name.
            id_columns (list[str], optional): List of ID column names.
            categorizer_feature_cols (list[str], optional): List of categorizer feature columns.

        Returns:
            Analysis: The created analysis object.

        Raises:
            NeuralkException: If the analysis creation fails.
        """
        self._check_n_analyses()
        if isinstance(taxonomy_file, ProjectFile):
            taxonomy_file = taxonomy_file.id

        resp = self._request_handler.put(
            "analysis/create-categorization-fit",
            data={
                "name": name,
                "dataset_hash_id": dataset.id,
                "target_columns": (
                    json.dumps(target_columns) if target_columns != None else None
                ),
                "id_column": (json.dumps(id_columns) if id_columns != None else None),
                "categorizer_feature_cols": (
                    json.dumps(categorizer_feature_cols)
                    if categorizer_feature_cols != None
                    else None
                ),
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot create categorization fit analysis", resp
            )

        analysis = Analysis._from_json(resp.json())

        return analysis

    @call_get_rank_in_queue
    def create_categorization_predict(
        self,
        dataset: Dataset,
        name: str,
        categorization_fit_analysis: str,
    ) -> Analysis:
        """
        Create a new categorization predict analysis from a fit analysis hash ID.

        Args:
            dataset (Dataset): The dataset to use for prediction.
            name (str): The name of the prediction analysis.
            categorization_fit_analysis (str|Analysis): The object or ID of the fit analysis.

        Returns:
            Analysis: The created prediction analysis object.

        Raises:
            NeuralkException: If the analysis creation fails.
        """
        self._check_n_analyses()
        if isinstance(categorization_fit_analysis, Analysis):
            categorization_fit_analysis = categorization_fit_analysis.id

        resp = self._request_handler.put(
            "analysis/create-categorization-predict",
            data={
                "name": name,
                "dataset_hash_id": dataset.id,
                "fit_analysis_hash_id": categorization_fit_analysis,
            },
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot create categorization predict analysis", resp
            )

        analysis = Analysis._from_json(resp.json())

        return analysis

    def get(self, analysis_id: str) -> Analysis:
        """
        Retrieve an analysis by its ID.

        Args:
            analysis_id (str): The ID of the analysis to retrieve

        Returns:
            Analysis: The retrieved analysis object

        Raises:
            NeuralkException: If the analysis retrieval fails
        """
        resp = self._request_handler.get(
            "analysis/get", params={"hash_id": analysis_id}
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get analysis", resp)

        analysis = Analysis._from_json(resp.json())
        return analysis

    def delete(self, analysis: str | Analysis) -> None:
        """
        Delete an analysis from the platform.

        Args:
            analysis (str | Analysis): The analysis object or its id.

        Raises:
            NeuralkException: If the analysis deletion fails.
        """
        if isinstance(analysis, Analysis):
            analysis = analysis.id

        resp = self._request_handler.delete(
            "analysis/delete", params={"hash_id": analysis}
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot delete analysis", resp)

    def cancel(self, analysis: str | Analysis) -> None:
        """
        Cancel an analysis

        Args:
            analysis (str | Analysis): The analysis object or its id.

        Raises:
            NeuralkException: If the analysis deletion fails.
        """
        if isinstance(analysis, Analysis):
            analysis = analysis.id

        resp = self._request_handler.delete(
            "analysis/cancel", params={"hash_id": analysis}
        )

        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot cancel analysis", resp)

    def download_results(
        self, analysis: str | Analysis, folder_path: str
    ) -> dict[str, str]:
        """
        Save the results of an analysis to a local folder using its ID or object.

        Args:
            analysis (str | Analysis): The analysis object or its id.
            folder_path (str): The folder where to save the result files.

        Raises:
            NeuralkException: If the result download fails.
        """
        if isinstance(analysis, Analysis):
            analysis = analysis.id

        response_download_file = self._request_handler.get(
            "analysis/get-result-download-link",
            params={"hash_id": analysis},
            stream=True,
        )

        if response_download_file.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp(
                "Cannot get download link of analysis result", response_download_file
            )

        ret = {}
        signed_urls = response_download_file.json()["signed_url_list"]
        for signed_url_object in signed_urls:
            signed_url = signed_url_object["signed_url"]
            if Configuration.debug_mode:
                signed_url = signed_url.replace("object-storage", "localhost").replace(
                    "9023", "50023"
                )
            file_from_object_storage = requests.get(signed_url)
            if file_from_object_storage.status_code != HTTPStatus.OK:
                raise NeuralkException.from_resp(
                    "Cannot download file from object storage",
                    file_from_object_storage,
                )
            os.makedirs(folder_path, exist_ok=True)
            filename = signed_url_object["file_name"]

            filepath = os.path.join(folder_path, filename)
            ret[signed_url_object["file_type"].lower()] = filepath
            with open(filepath, "wb") as out_file:
                out_file.write(file_from_object_storage.content)

        return ret

    def wait_until_complete(
        self,
        analysis: str | Analysis,
        refresh_time: float = 5.0,
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

        if isinstance(analysis, str):
            analysis = self.get(analysis)

        waiter = Waiter(
            "Analysis status: ",
            refresh_time,
            timeout=timeout,
            verbose=verbose,
            terminal_statuses=("SUCCEEDED", "FAILED"),
        )

        while waiter.not_complete():
            analysis = self.get(analysis.id)
            status = analysis.status
            waiter.update_status(status)
            waiter.update_rank(self.get_rank_in_queue(analysis, verbose=verbose))

        return analysis

    def _check_n_analyses(self):
        organization_handler = OrganizationHandler(self._request_handler)
        orga = organization_handler.get()
        if not orga.is_limited:
            return

        n_analyses = organization_handler.get_running_job_number()
        if n_analyses >= _MAX_RUNNING_ANALYSES:
            raise RuntimeError(
                "Cannot create new analysis as there are already "
                f"{_MAX_RUNNING_ANALYSES} running on the platform. "
                "Please wait for one analysis to finish."
            )
    
    def get_rank_in_queue(
        self,
        analysis: str | Analysis,
        verbose: bool = True,
    ) -> int:
        """
        Get the rank of an analysis in the queue.

        Args:
            analysis (str | Analysis): The analysis object or its id.
            verbose (bool): whether to display status messages.

        Returns:
            int: The rank of the analysis in the queue.
        """
        if isinstance(analysis, Analysis):
            analysis = analysis.id

        resp = self._request_handler.get(
            "analysis/get-rank-in-queue", params={"hash_id": analysis}
        )
        if resp.status_code != HTTPStatus.OK:
            raise NeuralkException.from_resp("Cannot get rank in queue", resp)
        rank = resp.json()["rank"]
        if verbose:
            logger.info(f"Current position in queue: {rank}.")
        return rank