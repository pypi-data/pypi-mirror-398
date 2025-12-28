"""
Analysis model module.

This module defines the Analysis class which represents an analysis in the Neuralk AI platform.
"""

from dataclasses import dataclass

from .model_base import ModelBase


@dataclass
class Analysis(ModelBase):
    """
    Represents an analysis in the Neuralk AI platform.

    Attributes:
        id (str): Unique identifier for the analysis.
        name (str): Name of the analysis.
        advancement (int): Progress percentage (0-100).
        error (str): Error message if the analysis failed.
    """

    id: str
    name: str
    error: str
    advancement: int
    status: str
    is_canceled: bool

    @classmethod
    def _from_json(cls, resp_json) -> "Analysis":
        """
        Create an Analysis instance from a JSON response.

        Args:
            resp_json (dict): The JSON response containing analysis data.

        Returns:
            Analysis: A new Analysis instance populated with data from the JSON response.
        """
        analysis = cls(
            id=resp_json["hash_id"],
            name=resp_json["name"],
            error=resp_json["error"],
            advancement=resp_json["advancement"],
            status=resp_json["status"],
            is_canceled=resp_json["is_canceled"]
        )
        return analysis
