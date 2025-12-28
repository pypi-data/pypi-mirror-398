"""
Project model module.

This module defines the Project class which represents a project in the Neuralk AI platform.
"""

from dataclasses import dataclass, field

from .analysis import Analysis
from .dataset import Dataset
from .model_base import ModelBase
from .project_file import ProjectFile
from .user import User

@dataclass
class Project(ModelBase):
    """
    Represents a project in the Neuralk AI platform.

    Attributes:
        id (str): Unique identifier for the project.
        name (str): Name of the project.
        dataset_list (list[Dataset]): List of datasets associated with the project.
        user_list (list[User]): List of users associated with the project.
        project_file_list (list[ProjectFile]): List of project files associated with the project.
        analysis_list (list[Analysis]): List of analyses associated with the project.
    """

    name: str
    id: str
    dataset_list: list[Dataset] = field(default_factory=list)
    user_list: list[tuple[str, User]] = field(default_factory=list)
    project_file_list: list[ProjectFile] = field(default_factory=list)
    analysis_list: list[Analysis] = field(default_factory=list)

    @classmethod
    def _from_json(cls, resp_json) -> "Project":
        """
        Create a Project instance from a JSON response.

        Args:
            resp_json (dict): The JSON response containing project data.

        Returns:
            Project: A new Project instance populated with data from the JSON response.
        """
        project = cls(
            name=resp_json["name"],
            id=resp_json["hash_id"],
        )

        if "dataset_list" in resp_json:
            for resp in resp_json["dataset_list"]:
                project.dataset_list.append(Dataset._from_json(resp))

        if "user_list" in resp_json:
            for resp in resp_json["user_list"]:
                project.user_list.append((resp[0], User._from_json(resp[1])))

        if "project_file_list" in resp_json:
            for resp in resp_json["project_file_list"]:
                project.project_file_list.append(ProjectFile._from_json(resp))
        
        if "analysis_list" in resp_json:
            for resp in resp_json["analysis_list"]:
                project.analysis_list.append(Analysis._from_json(resp))

        return project
