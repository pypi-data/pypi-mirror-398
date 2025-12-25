"""
Submissions module for GitHub Classroom API.

This module provides methods to interact with assignment submissions
(accepted assignments) in GitHub Classroom.
"""

from typing import Dict, List, Optional, Any
import logging
from .base import ClassroomBase


class Submissions(ClassroomBase):
    """Handle GitHub Classroom assignment submission operations."""

    def list(
        self,
        assignment_id: int,
        page: int = 1,
        per_page: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List accepted assignments (submissions) with pagination.

        Args:
            assignment_id: The ID of the assignment
            page: Page number (default: 1)
            per_page: Number of submissions per page, max 100 (default: 30)

        Returns:
            List of submission dictionaries with fields:
            - id: Submission ID
            - students: List of student objects (login, id, etc.)
            - repository: Repository info (id, name, full_name, html_url)
            - commit_count: Number of commits
            - grade: Current grade (points)
            - passing: Whether the submission passes tests
            - submitted: Whether the assignment is submitted

        Example:
            >>> submissions = classroom_api.submissions.list(67890, per_page=50)
            >>> for sub in submissions:
            ...     student = sub['students'][0]['login']
            ...     repo = sub['repository']['name']
            ...     print(f"{student}: {repo} ({sub['commit_count']} commits)")
        """
        self.logger.info(
            f"Listing submissions for assignment {assignment_id} "
            f"(page {page}, per_page {per_page})"
        )
        
        endpoint = f"/assignments/{assignment_id}/accepted_assignments"
        params = {"page": page, "per_page": min(per_page, 100)}
        
        submissions = self.call_api(endpoint, params=params)
        
        self.logger.info(
            f"Retrieved {len(submissions)} submissions for assignment {assignment_id}"
        )
        return submissions

    def get_all(
        self,
        assignment_id: int,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all submissions for an assignment (auto-pagination).

        Automatically fetches all pages and combines results.

        Args:
            assignment_id: The ID of the assignment
            per_page: Number of submissions per page, max 100 (default: 100)

        Returns:
            Complete list of all submissions for the assignment

        Example:
            >>> all_subs = classroom_api.submissions.get_all(67890)
            >>> print(f"Total submissions: {len(all_subs)}")
        """
        self.logger.info(f"Getting all submissions for assignment {assignment_id}")
        
        all_submissions = []
        page = 1
        
        while True:
            submissions = self.list(assignment_id, page=page, per_page=per_page)
            
            if not submissions:
                break
                
            all_submissions.extend(submissions)
            
            if len(submissions) < per_page:
                break
                
            page += 1
        
        self.logger.info(
            f"Retrieved total of {len(all_submissions)} submissions "
            f"for assignment {assignment_id}"
        )
        return all_submissions

    def get_by_student(
        self,
        assignment_id: int,
        github_username: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific student's submission for an assignment.

        Args:
            assignment_id: The ID of the assignment
            github_username: GitHub username of the student

        Returns:
            Submission dictionary if found, None otherwise

        Example:
            >>> sub = classroom_api.submissions.get_by_student(67890, "student123")
            >>> if sub:
            ...     print(f"Commits: {sub['commit_count']}")
            ...     print(f"Grade: {sub['grade']}")
        """
        self.logger.info(
            f"Getting submission for student '{github_username}' "
            f"in assignment {assignment_id}"
        )
        
        all_submissions = self.get_all(assignment_id)
        
        for submission in all_submissions:
            students = submission.get("students", [])
            for student in students:
                if student.get("login") == github_username:
                    self.logger.info(
                        f"Found submission for '{github_username}': "
                        f"{submission['repository']['name']}"
                    )
                    return submission
        
        self.logger.warning(
            f"No submission found for student '{github_username}' "
            f"in assignment {assignment_id}"
        )
        return None

    def filter_by_status(
        self,
        assignment_id: int,
        submitted: Optional[bool] = None,
        passing: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter submissions by submission/passing status.

        Args:
            assignment_id: The ID of the assignment
            submitted: If True, only submitted; if False, only not submitted;
                      if None, all (default: None)
            passing: If True, only passing; if False, only not passing;
                    if None, all (default: None)

        Returns:
            List of submissions matching the filter criteria

        Example:
            >>> # Get all submitted assignments
            >>> submitted = classroom_api.submissions.filter_by_status(
            ...     67890, submitted=True
            ... )
            >>> 
            >>> # Get submitted but not passing
            >>> needs_help = classroom_api.submissions.filter_by_status(
            ...     67890, submitted=True, passing=False
            ... )
        """
        self.logger.info(
            f"Filtering submissions for assignment {assignment_id} "
            f"(submitted={submitted}, passing={passing})"
        )
        
        all_submissions = self.get_all(assignment_id)
        
        filtered = []
        for submission in all_submissions:
            if submitted is not None and submission.get("submitted") != submitted:
                continue
            if passing is not None and submission.get("passing") != passing:
                continue
            filtered.append(submission)
        
        self.logger.info(
            f"Found {len(filtered)} submissions matching filter "
            f"(out of {len(all_submissions)})"
        )
        return filtered

    def get_repository_urls(
        self,
        assignment_id: int,
        url_type: str = "html"
    ) -> Dict[str, str]:
        """
        Get a mapping of student usernames to repository URLs.

        Args:
            assignment_id: The ID of the assignment
            url_type: Type of URL to return:
                     - "html": Web URL (default)
                     - "clone": Git clone URL (https)
                     - "ssh": SSH clone URL

        Returns:
            Dictionary mapping GitHub username to repository URL

        Example:
            >>> urls = classroom_api.submissions.get_repository_urls(67890)
            >>> for student, url in urls.items():
            ...     print(f"{student}: {url}")
        """
        if url_type not in ["html", "clone", "ssh"]:
            raise ValueError(
                f"Invalid url_type: {url_type}. "
                "Must be 'html', 'clone', or 'ssh'"
            )
        
        self.logger.info(
            f"Getting {url_type} repository URLs for assignment {assignment_id}"
        )
        
        all_submissions = self.get_all(assignment_id)
        
        urls = {}
        for submission in all_submissions:
            repository = submission.get("repository", {})
            students = submission.get("students", [])
            
            # Get the URL based on type
            if url_type == "html":
                url = repository.get("html_url")
            elif url_type == "clone":
                url = repository.get("clone_url") or repository.get("html_url") + ".git"
            else:  # ssh
                # Convert https URL to SSH format
                html_url = repository.get("html_url", "")
                url = html_url.replace("https://github.com/", "git@github.com:")
                if url and not url.endswith(".git"):
                    url += ".git"
            
            # Map each student to the repository URL
            for student in students:
                username = student.get("login")
                if username:
                    urls[username] = url
        
        self.logger.info(
            f"Retrieved {len(urls)} repository URLs for assignment {assignment_id}"
        )
        return urls

    def get_statistics(self, assignment_id: int) -> Dict[str, Any]:
        """
        Get statistical information about submissions for an assignment.

        Args:
            assignment_id: The ID of the assignment

        Returns:
            Dictionary with statistics:
            - total_accepted: Total number of accepted assignments
            - total_submitted: Number with submitted=True
            - total_passing: Number with passing=True
            - avg_commit_count: Average number of commits
            - students_with_commits: Number of students with at least 1 commit
            - students_without_commits: Number with 0 commits

        Example:
            >>> stats = classroom_api.submissions.get_statistics(67890)
            >>> print(f"Average commits: {stats['avg_commit_count']:.1f}")
            >>> print(f"Passing rate: {stats['total_passing']}/{stats['total_submitted']}")
        """
        self.logger.info(f"Getting statistics for assignment {assignment_id} submissions")
        
        all_submissions = self.get_all(assignment_id)
        
        total_accepted = len(all_submissions)
        total_submitted = sum(1 for s in all_submissions if s.get("submitted"))
        total_passing = sum(1 for s in all_submissions if s.get("passing"))
        
        commit_counts = [s.get("commit_count", 0) for s in all_submissions]
        avg_commit_count = sum(commit_counts) / len(commit_counts) if commit_counts else 0
        
        students_with_commits = sum(1 for c in commit_counts if c > 0)
        students_without_commits = sum(1 for c in commit_counts if c == 0)
        
        stats = {
            "total_accepted": total_accepted,
            "total_submitted": total_submitted,
            "total_passing": total_passing,
            "avg_commit_count": round(avg_commit_count, 2),
            "students_with_commits": students_with_commits,
            "students_without_commits": students_without_commits
        }
        
        self.logger.info(
            f"Submission statistics: {total_accepted} accepted, "
            f"{total_submitted} submitted, {total_passing} passing, "
            f"avg {stats['avg_commit_count']} commits"
        )
        
        return stats
