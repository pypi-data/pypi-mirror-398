"""
Utility functions used internally by the SDK.

"""
import logging

from .docs import add_submodules_to_docstring


add_submodules_to_docstring(__name__)



# Create logger named "neuralk"
logger = logging.getLogger("neuralk")
logger.setLevel(logging.INFO)

# Add StreamHandler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


