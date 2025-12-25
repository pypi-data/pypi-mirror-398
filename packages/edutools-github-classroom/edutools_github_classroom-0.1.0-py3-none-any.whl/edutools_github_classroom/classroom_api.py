"""
Main ClassroomAPI facade for GitHub Classroom.

This module provides the main entry point for interacting with the GitHub Classroom API.
"""

import logging
from typing import Optional
from .base import ClassroomBase
from .classrooms import Classrooms
from .assignments import Assignments
from .submissions import Submissions
from .grades import Grades


class ClassroomAPI:
    """
    Main API client for GitHub Classroom.

    This class provides access to all GitHub Classroom API modules through
    a unified interface.

    Args:
        token: GitHub personal access token (classic or fine-grained)
        logger: Optional custom logger (defaults to module logger)

    Example:
        >>> from edutools_github_classroom import ClassroomAPI
        >>> 
        >>> # Initialize the API client
        >>> api = ClassroomAPI("ghp_your_token_here")
        >>> 
        >>> # List classrooms
        >>> classrooms = api.classrooms.list()
        >>> 
        >>> # Get assignments for a classroom
        >>> assignments = api.assignments.get_all(classroom_id=12345)
        >>> 
        >>> # Filter assignments
        >>> ateliers = api.assignments.filter_by_title(
        ...     classroom_id=12345,
        ...     title_pattern="atelier"
        ... )
        >>> 
        >>> # Get submissions
        >>> submissions = api.submissions.get_all(assignment_id=67890)
        >>> 
        >>> # Get grades
        >>> grades = api.grades.get(assignment_id=67890)
        >>> 
        >>> # Export grades to CSV
        >>> api.grades.export_to_csv(67890, "grades.csv")
        >>> 
        >>> # Use context manager
        >>> with ClassroomAPI("ghp_token") as api:
        ...     classrooms = api.classrooms.get_all()

    Attributes:
        classrooms: Access to classroom operations
        assignments: Access to assignment operations
        submissions: Access to submission operations
        grades: Access to grading operations
    """

    def __init__(
        self,
        token: str,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the ClassroomAPI client.

        Args:
            token: GitHub personal access token
            logger: Optional custom logger
        """
        if not token:
            raise ValueError("GitHub token is required")

        # Setup logger
        if logger is None:
            logger = logging.getLogger(__name__)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)

        self.logger = logger
        self._token = token

        # Initialize API modules
        self._classrooms = Classrooms(token, logger)
        self._assignments = Assignments(token, logger)
        self._submissions = Submissions(token, logger)
        self._grades = Grades(token, logger)

        self.logger.info("ClassroomAPI initialized")

    @property
    def classrooms(self) -> Classrooms:
        """Access to classroom operations."""
        return self._classrooms

    @property
    def assignments(self) -> Assignments:
        """Access to assignment operations."""
        return self._assignments

    @property
    def submissions(self) -> Submissions:
        """Access to submission operations."""
        return self._submissions

    @property
    def grades(self) -> Grades:
        """Access to grading operations."""
        return self._grades

    def close(self) -> None:
        """
        Close all API sessions.

        This should be called when you're done using the API to properly
        clean up resources.
        """
        self.logger.info("Closing ClassroomAPI sessions")
        self._classrooms.close()
        self._assignments.close()
        self._submissions.close()
        self._grades.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
