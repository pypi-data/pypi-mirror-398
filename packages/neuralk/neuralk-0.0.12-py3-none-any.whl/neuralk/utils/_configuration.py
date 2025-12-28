"""
Configuration module for Neuralk AI SDK.

This module provides configuration constants and the Configuration class for the SDK.
"""
import os

NEURALK_TIMEOUT = 15
"""Default timeout (in seconds) for API requests."""
NEURALK_REFRESH_TOKEN_RETRY = 3
"""Number of times to retry refreshing the token on expiration."""


class Configuration:
    """
    Configuration options for the Neuralk AI SDK.

    Attributes:
        debug_mode (bool): Enable or disable debug mode.
        neuralk_endpoint (str): The API endpoint for the Neuralk platform.
    """

    debug_mode = False
    neuralk_endpoint = os.environ.get("NEURALK_URL", "https://api.neuralk-ai.com")
