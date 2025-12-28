"""
Request type enumeration for Neuralk AI SDK.

This module defines the HTTP request types used by the SDK.
"""

from enum import Enum


class RequestType(Enum):
    """
    Enumeration of HTTP request types for the Neuralk AI SDK.
    """

    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4
