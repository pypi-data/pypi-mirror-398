"""
Assignments module for GitHub Classroom API.

This module provides methods to interact with GitHub Classroom assignments,
including listing, filtering, and retrieving assignment details.
"""

from typing import Dict, List, Optional, Any
import logging
from .base import ClassroomBase


class Assignments(ClassroomBase):
    """Handle GitHub Classroom assignment operations."""

    def list(
        self,
        classroom_id: int,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List all assignments for a classroom with pagination.

        Args:
            classroom_id: The ID of the classroom
            page: Page number (default: 1)
            per_page: Number of assignments per page, max 100 (default: 30)

        Returns:
            List of assignment dictionaries with fields:
            - id: Assignment ID
            - title: Assignment title
            - type: "individual" or "group"
            - public_repo: Whether repos are public
            - accepted: Number of accepted assignments
            - submitted: Number of submitted assignments
            - passing: Number of passing assignments
            - slug: Assignment URL slug
            - deadline: Deadline (ISO 8601 format or null)

        Example:
            >>> assignments = classroom_api.assignments.list(12345, per_page=50)
            >>> for assignment in assignments:
            ...     print(f"{assignment['title']}: {assignment['accepted']} accepted")
        """
        self.logger.info(
            f"Listing assignments for classroom {classroom_id} "
            f"(page {page}, per_page {per_page})"
        )
        
        endpoint = f"/classrooms/{classroom_id}/assignments"
        params = {"page": page, "per_page": min(per_page, 100)}
        
        assignments = self.call_api(endpoint, params=params)
        
        self.logger.info(
            f"Retrieved {len(assignments)} assignments for classroom {classroom_id}"
        )
        return assignments

    def get(self, assignment_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific assignment.

        Args:
            assignment_id: The ID of the assignment

        Returns:
            Dictionary with assignment details including:
            - id, title, type, public_repo
            - accepted, submitted, passing counts
            - slug, deadline
            - classroom: Associated classroom info
            - starter_code_repository: Starter code repo (if exists)

        Example:
            >>> assignment = classroom_api.assignments.get(67890)
            >>> print(f"{assignment['title']}: {assignment['accepted']} students")
        """
        self.logger.info(f"Getting assignment {assignment_id}")
        
        endpoint = f"/assignments/{assignment_id}"
        assignment = self.call_api(endpoint)
        
        self.logger.info(
            f"Retrieved assignment: {assignment.get('title', 'Unknown')}"
        )
        return assignment

    def get_all(
        self,
        classroom_id: int,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all assignments for a classroom (auto-pagination).

        Automatically fetches all pages and combines results.

        Args:
            classroom_id: The ID of the classroom
            per_page: Number of assignments per page, max 100 (default: 100)

        Returns:
            Complete list of all assignments for the classroom

        Example:
            >>> all_assignments = classroom_api.assignments.get_all(12345)
            >>> print(f"Total assignments: {len(all_assignments)}")
        """
        self.logger.info(f"Getting all assignments for classroom {classroom_id}")
        
        all_assignments = []
        page = 1
        
        while True:
            assignments = self.list(classroom_id, page=page, per_page=per_page)
            
            if not assignments:
                break
                
            all_assignments.extend(assignments)
            
            if len(assignments) < per_page:
                break
                
            page += 1
        
        self.logger.info(
            f"Retrieved total of {len(all_assignments)} assignments "
            f"for classroom {classroom_id}"
        )
        return all_assignments

    def filter_by_title(
        self,
        classroom_id: int,
        title_pattern: str,
        exclude: bool = False,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter assignments by title pattern.

        Args:
            classroom_id: The ID of the classroom
            title_pattern: Pattern to match in assignment title
            exclude: If True, exclude matching assignments (default: False)
            case_sensitive: Whether to match case-sensitively (default: False)

        Returns:
            List of assignments matching the filter criteria

        Example:
            >>> # Get all assignments containing "atelier"
            >>> ateliers = classroom_api.assignments.filter_by_title(
            ...     12345, "atelier"
            ... )
            >>> 
            >>> # Exclude assignments with "projet" in title
            >>> no_projects = classroom_api.assignments.filter_by_title(
            ...     12345, "projet", exclude=True
            ... )
        """
        self.logger.info(
            f"Filtering assignments for classroom {classroom_id} "
            f"by title pattern '{title_pattern}' (exclude={exclude})"
        )
        
        all_assignments = self.get_all(classroom_id)
        
        filtered = []
        for assignment in all_assignments:
            title = assignment.get("title", "")
            
            if not case_sensitive:
                title = title.lower()
                pattern = title_pattern.lower()
            else:
                pattern = title_pattern
            
            match = pattern in title
            
            if (match and not exclude) or (not match and exclude):
                filtered.append(assignment)
        
        self.logger.info(
            f"Found {len(filtered)} assignments matching filter "
            f"(out of {len(all_assignments)})"
        )
        return filtered

    def get_statistics(self, assignment_id: int) -> Dict[str, Any]:
        """
        Get statistical information about an assignment.

        Args:
            assignment_id: The ID of the assignment

        Returns:
            Dictionary with statistics:
            - title: Assignment title
            - type: "individual" or "group"
            - total_accepted: Number of accepted assignments
            - total_submitted: Number of submitted assignments
            - total_passing: Number of passing assignments
            - submission_rate: Percentage of submitted (out of accepted)
            - pass_rate: Percentage of passing (out of submitted)
            - deadline: Assignment deadline (if set)

        Example:
            >>> stats = classroom_api.assignments.get_statistics(67890)
            >>> print(f"Pass rate: {stats['pass_rate']:.1f}%")
        """
        self.logger.info(f"Getting statistics for assignment {assignment_id}")
        
        assignment = self.get(assignment_id)
        
        accepted = assignment.get("accepted", 0)
        submitted = assignment.get("submitted", 0)
        passing = assignment.get("passing", 0)
        
        submission_rate = (submitted / accepted * 100) if accepted > 0 else 0
        pass_rate = (passing / submitted * 100) if submitted > 0 else 0
        
        stats = {
            "title": assignment.get("title"),
            "type": assignment.get("type"),
            "total_accepted": accepted,
            "total_submitted": submitted,
            "total_passing": passing,
            "submission_rate": round(submission_rate, 2),
            "pass_rate": round(pass_rate, 2),
            "deadline": assignment.get("deadline")
        }
        
        self.logger.info(
            f"Statistics for '{stats['title']}': "
            f"{submitted}/{accepted} submitted ({stats['submission_rate']}%), "
            f"{passing}/{submitted} passing ({stats['pass_rate']}%)"
        )
        
        return stats

    def filter_by_type(
        self,
        classroom_id: int,
        assignment_type: str
    ) -> List[Dict[str, Any]]:
        """
        Filter assignments by type (individual or group).

        Args:
            classroom_id: The ID of the classroom
            assignment_type: Type to filter ("individual" or "group")

        Returns:
            List of assignments of the specified type

        Example:
            >>> individual = classroom_api.assignments.filter_by_type(
            ...     12345, "individual"
            ... )
        """
        if assignment_type not in ["individual", "group"]:
            raise ValueError(
                f"Invalid assignment_type: {assignment_type}. "
                "Must be 'individual' or 'group'"
            )
        
        self.logger.info(
            f"Filtering {assignment_type} assignments for classroom {classroom_id}"
        )
        
        all_assignments = self.get_all(classroom_id)
        filtered = [
            a for a in all_assignments
            if a.get("type") == assignment_type
        ]
        
        self.logger.info(
            f"Found {len(filtered)} {assignment_type} assignments "
            f"(out of {len(all_assignments)})"
        )
        return filtered
