"""
NeuralkAI SDK main module.

This module provides the main interface for interacting with the Neuralk AI platform.
It handles authentication and provides access to various services through specialized handlers.
"""

import logging
from pathlib import Path

from ._classifier import Classifier
from ._on_premise_classifier import OnPremiseClassifier
from .exceptions import NeuralkException
from .model.analysis import Analysis
from .model.dataset import Dataset
from .model.organization import Organization
from .model.project import Project
from .model.project_file import ProjectFile
from .neuralk import Neuralk
from .utils.docs import add_submodules_to_docstring

VERSION_PATH = Path(__file__).resolve().parent / "VERSION.txt"
__version__ = VERSION_PATH.read_text(encoding="utf-8").strip()


__all__ = [
    "Neuralk",
    "Analysis",
    "Dataset",
    "Organization",
    "Project",
    "ProjectFile",
    "NeuralkException",
    "Classifier",
    "OnPremiseClassifier",
    "logger",
]
