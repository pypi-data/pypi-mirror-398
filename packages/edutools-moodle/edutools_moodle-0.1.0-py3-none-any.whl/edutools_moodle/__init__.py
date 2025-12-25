"""
Edutools Moodle - Python package for Moodle API interactions in educational contexts.

Main exports:
    - MoodleAPI: Main facade API client (recommended)
    - MoodleBase: Base class for custom extensions
    - MoodleGroups: Groups and cohorts management
    - MoodleAssignments: Assignments handling
    - MoodleGrades: Grades management
    - MoodleUsers: User account management
    
Exceptions:
    - MoodleAPIError: Base exception for API errors
    - MoodleAuthenticationError: Authentication failures
    - MoodleResourceNotFoundError: Resource not found
"""

from .base import (
    MoodleBase,
    MoodleAPIError,
    MoodleAuthenticationError,
    MoodleResourceNotFoundError
)
from .api import MoodleAPI
from .groups import MoodleGroups
from .assignments import MoodleAssignments
from .grades import MoodleGrades
from .users import MoodleUsers

__version__ = "0.1.0"
__author__ = "Nadiri Abdeljalil"
__email__ = "nadiri@najasoft.com"

__all__ = [
    "MoodleAPI",
    "MoodleBase",
    "MoodleGroups",
    "MoodleAssignments",
    "MoodleGrades",
    "MoodleUsers",
    "MoodleAPIError",
    "MoodleAuthenticationError",
    "MoodleResourceNotFoundError",
]
