from dataclasses import dataclass
from .model_base import ModelBase


@dataclass
class ProjectFile(ModelBase):
    """
    Represents a project file in the Neuralk AI platform.

    Attributes:
        id (str): Unique identifier for the project file.
        name (str): Name of the project file.
        file_name (str): File name of the project file.
    """

    id: str
    name: str
    file_name: str

    @classmethod
    def _from_json(cls, resp_json) -> "ProjectFile":
        """
        Create a ProjectFile instance from a JSON response.

        Args:
            resp_json (dict): The JSON response containing project file data.

        Returns:
            ProjectFile: A new ProjectFile instance populated with data from the JSON response.
        """
        file = cls(
            id=resp_json["hash_id"],
            name=resp_json["name"],
            file_name=resp_json["file_name"]
        )

        return file
