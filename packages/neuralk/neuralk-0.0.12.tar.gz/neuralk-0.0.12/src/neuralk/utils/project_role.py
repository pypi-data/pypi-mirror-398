"""
Project role enumeration for Neuralk AI SDK.

This module defines the roles a user can have within a project.
"""

from enum import Enum


class ProjectRole(Enum):
    """
    Enumeration of project roles for the Neuralk AI SDK.
    """

    OWNER = "owner"
    CONTRIBUTOR = "contributor"
    MEMBER = "member"
