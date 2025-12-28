"""
API call handlers for model objects.

This submodule provides functions and classes responsible for interfacing with the remote API.
It takes core SDK model objects as input, serializes them as needed, and executes the corresponding
HTTP requests (e.g., POST, GET) to the backend services.
"""

from ..utils.docs import add_submodules_to_docstring


add_submodules_to_docstring(__name__)
