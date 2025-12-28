from dataclasses import dataclass, field

from .analysis import Analysis
from .model_base import ModelBase


@dataclass
class Dataset(ModelBase):
    """
    Represents a dataset in the Neuralk AI platform.

    Attributes:
        id (str): Unique identifier for the dataset.
        name (str): Name of the dataset.
        file_name (str): File name of the dataset.
        analysis_list (list[Analysis]): List of analyses associated with the dataset.
    """

    id: str
    name: str
    file_name: str
    status: str
    analysis_list: list[Analysis] = field(default_factory=list)

    @classmethod
    def _from_json(cls, resp_json) -> "Dataset":
        """
        Create a Dataset instance from a JSON response.

        Args:
            resp_json (dict): The JSON response containing dataset data.

        Returns:
            Dataset: A new Dataset instance populated with data from the JSON response.
        """
        dataset = cls(
            id=resp_json["hash_id"],
            name=resp_json["name"],
            file_name=resp_json["file_name"],
            status=resp_json["status"],
        )

        if "analysis_list" in resp_json:
            for analysis_resp in resp_json["analysis_list"]:
                dataset.analysis_list.append(Analysis._from_json(analysis_resp))

        return dataset
