"""
User model module.

This module defines the User class which represents a user in the Neuralk AI platform.
"""

from dataclasses import dataclass

from .model_base import ModelBase


@dataclass
class User(ModelBase):
    """
    Represents a user in the Neuralk AI platform.

    Attributes:
        id (str): Unique identifier for the user.
        email (str): Email address of the user.
        firstname (str): First name of the user.
        lastname (str): Last name of the user.
    """

    id: str
    email: str
    firstname: str
    lastname: str

    @classmethod
    def _from_json(cls, resp_json) -> "User":
        """
        Create a User instance from a JSON response.

        Args:
            resp_json (dict): The JSON response containing user data.

        Returns:
            User: A new User instance populated with data from the JSON response.
        """
        user = cls(
            id=resp_json["token_id"],
            email=resp_json["email"],
            firstname=resp_json["firstname"],
            lastname=resp_json["lastname"]
        )

        return user
