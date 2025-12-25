"""
Grades module for GitHub Classroom API.

This module provides methods to interact with assignment grades in GitHub Classroom.
"""

from typing import Dict, List, Optional, Any
import csv
import logging
from pathlib import Path
from .base import ClassroomBase


class Grades(ClassroomBase):
    """Handle GitHub Classroom grading operations."""

    def get(self, assignment_id: int) -> List[Dict[str, Any]]:
        """
        Get all grades for an assignment.

        Args:
            assignment_id: The ID of the assignment

        Returns:
            List of grade dictionaries with fields:
            - assignment_name: Name of the assignment
            - assignment_url: URL to the assignment
            - starter_code_url: URL to starter code (if exists)
            - github_username: Student's GitHub username
            - roster_identifier: Student identifier from roster
            - student_repository_name: Name of student's repository
            - student_repository_url: URL to student's repository
            - submission_timestamp: When submitted (ISO 8601 or empty)
            - points_awarded: Points awarded (integer or empty)
            - points_available: Total points available (integer)
            - group_name: Group name for group assignments (or empty)

        Example:
            >>> grades = classroom_api.grades.get(67890)
            >>> for grade in grades:
            ...     print(f"{grade['github_username']}: {grade['points_awarded']}/{grade['points_available']}")
        """
        self.logger.info(f"Getting grades for assignment {assignment_id}")
        
        endpoint = f"/assignments/{assignment_id}/grades"
        grades = self.call_api(endpoint)
        
        self.logger.info(
            f"Retrieved {len(grades)} grades for assignment {assignment_id}"
        )
        return grades

    def export_to_csv(
        self,
        assignment_id: int,
        file_path: str,
        encoding: str = "utf-8"
    ) -> None:
        """
        Export grades to a CSV file.

        Args:
            assignment_id: The ID of the assignment
            file_path: Path where to save the CSV file
            encoding: Character encoding (default: "utf-8")

        Example:
            >>> classroom_api.grades.export_to_csv(
            ...     67890,
            ...     "grades_atelier1.csv"
            ... )
        """
        self.logger.info(
            f"Exporting grades for assignment {assignment_id} to {file_path}"
        )
        
        grades = self.get(assignment_id)
        
        if not grades:
            self.logger.warning("No grades to export")
            return
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        with open(file_path, "w", newline="", encoding=encoding) as csvfile:
            fieldnames = grades[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(grades)
        
        self.logger.info(
            f"Exported {len(grades)} grades to {file_path}"
        )

    def get_by_student(
        self,
        assignment_id: int,
        github_username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific student's grade for an assignment.

        Args:
            assignment_id: The ID of the assignment
            github_username: GitHub username of the student

        Returns:
            Grade dictionary if found, None otherwise

        Example:
            >>> grade = classroom_api.grades.get_by_student(67890, "student123")
            >>> if grade:
            ...     print(f"Score: {grade['points_awarded']}/{grade['points_available']}")
        """
        self.logger.info(
            f"Getting grade for student '{github_username}' "
            f"in assignment {assignment_id}"
        )
        
        grades = self.get(assignment_id)
        
        for grade in grades:
            if grade.get("github_username") == github_username:
                self.logger.info(
                    f"Found grade for '{github_username}': "
                    f"{grade.get('points_awarded', 'N/A')}/{grade.get('points_available', 'N/A')}"
                )
                return grade
        
        self.logger.warning(
            f"No grade found for student '{github_username}' "
            f"in assignment {assignment_id}"
        )
        return None

    def get_statistics(self, assignment_id: int) -> Dict[str, Any]:
        """
        Get statistical information about grades for an assignment.

        Args:
            assignment_id: The ID of the assignment

        Returns:
            Dictionary with statistics:
            - total_students: Total number of students
            - graded_count: Number of students with grades
            - ungraded_count: Number of students without grades
            - avg_score: Average score (points_awarded)
            - avg_percentage: Average percentage (awarded/available)
            - max_score: Maximum score
            - min_score: Minimum score (excluding ungraded)
            - points_available: Total points available

        Example:
            >>> stats = classroom_api.grades.get_statistics(67890)
            >>> print(f"Average: {stats['avg_percentage']:.1f}%")
            >>> print(f"Graded: {stats['graded_count']}/{stats['total_students']}")
        """
        self.logger.info(f"Getting grade statistics for assignment {assignment_id}")
        
        grades = self.get(assignment_id)
        
        total_students = len(grades)
        
        # Filter graded students (those with points_awarded set)
        graded = [
            g for g in grades
            if g.get("points_awarded") not in [None, ""]
        ]
        
        graded_count = len(graded)
        ungraded_count = total_students - graded_count
        
        if graded:
            scores = [
                int(g["points_awarded"])
                for g in graded
                if g.get("points_awarded") not in [None, ""]
            ]
            
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            # Calculate percentage (assuming points_available is the same for all)
            points_available = graded[0].get("points_available")
            if points_available:
                points_available = int(points_available)
                avg_percentage = (avg_score / points_available * 100) if points_available > 0 else 0
            else:
                avg_percentage = 0
                points_available = None
        else:
            avg_score = 0
            max_score = 0
            min_score = 0
            avg_percentage = 0
            points_available = None
        
        stats = {
            "total_students": total_students,
            "graded_count": graded_count,
            "ungraded_count": ungraded_count,
            "avg_score": round(avg_score, 2),
            "avg_percentage": round(avg_percentage, 2),
            "max_score": max_score,
            "min_score": min_score,
            "points_available": points_available
        }
        
        self.logger.info(
            f"Grade statistics: {graded_count}/{total_students} graded, "
            f"avg {stats['avg_score']}/{points_available} ({stats['avg_percentage']}%)"
        )
        
        return stats

    def filter_by_status(
        self,
        assignment_id: int,
        graded: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter grades by grading status.

        Args:
            assignment_id: The ID of the assignment
            graded: If True, return only graded; if False, only ungraded

        Returns:
            List of grade records matching the filter

        Example:
            >>> # Get students who haven't been graded yet
            >>> ungraded = classroom_api.grades.filter_by_status(
            ...     67890, graded=False
            ... )
            >>> for student in ungraded:
            ...     print(f"Not graded: {student['github_username']}")
        """
        self.logger.info(
            f"Filtering grades for assignment {assignment_id} "
            f"(graded={graded})"
        )
        
        grades = self.get(assignment_id)
        
        filtered = []
        for grade in grades:
            points_awarded = grade.get("points_awarded")
            has_grade = points_awarded not in [None, ""]
            
            if (graded and has_grade) or (not graded and not has_grade):
                filtered.append(grade)
        
        self.logger.info(
            f"Found {len(filtered)} {'graded' if graded else 'ungraded'} students "
            f"(out of {len(grades)})"
        )
        return filtered

    def get_by_roster_identifier(
        self,
        assignment_id: int,
        roster_identifier: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a student's grade by their roster identifier.

        Args:
            assignment_id: The ID of the assignment
            roster_identifier: Roster identifier of the student

        Returns:
            Grade dictionary if found, None otherwise

        Example:
            >>> grade = classroom_api.grades.get_by_roster_identifier(
            ...     67890, "12345678"
            ... )
        """
        self.logger.info(
            f"Getting grade for roster identifier '{roster_identifier}' "
            f"in assignment {assignment_id}"
        )
        
        grades = self.get(assignment_id)
        
        for grade in grades:
            if grade.get("roster_identifier") == roster_identifier:
                self.logger.info(
                    f"Found grade for roster '{roster_identifier}': "
                    f"{grade.get('github_username')}"
                )
                return grade
        
        self.logger.warning(
            f"No grade found for roster identifier '{roster_identifier}' "
            f"in assignment {assignment_id}"
        )
        return None
