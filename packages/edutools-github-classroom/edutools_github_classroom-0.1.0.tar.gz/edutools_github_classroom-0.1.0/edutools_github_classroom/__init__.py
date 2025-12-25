"""
edutools-github-classroom

A Python library for interacting with the GitHub Classroom REST API.
This package provides a clean, Pythonic interface to manage classrooms,
assignments, submissions, and grades.
"""

__version__ = "0.1.0"

from .classroom_api import ClassroomAPI
from .base import (
    ClassroomAPIError,
    ClassroomAuthenticationError,
    ClassroomResourceNotFoundError
)

__all__ = [
    "ClassroomAPI",
    "ClassroomAPIError",
    "ClassroomAuthenticationError",
    "ClassroomResourceNotFoundError",
    "__version__"
]
