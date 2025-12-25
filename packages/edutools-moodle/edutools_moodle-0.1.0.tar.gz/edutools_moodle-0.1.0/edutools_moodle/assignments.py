"""
Assignments module for Moodle API.

Handles operations related to assignments and submissions.
"""

from .base import MoodleBase
from typing import List, Dict, Any, Optional


class MoodleAssignments(MoodleBase):
    """
    Class for managing assignments in Moodle.
    """

    def get_assignments(self, course_id: int, include_not_enrolled: bool = True) -> List[Dict[str, Any]]:
        """
        Get all assignments in a course.

        Args:
            course_id: ID of the course
            include_not_enrolled: Include assignments from courses user is not enrolled in

        Returns:
            List of assignment dictionaries
        """
        params = {
            'courseids[0]': course_id,
            'includenotenrolledcourses': 1 if include_not_enrolled else 0
        }
        response = self.call_api('mod_assign_get_assignments', params)

        # The response typically has a 'courses' key with assignment data
        if isinstance(response, dict) and 'courses' in response:
            courses = response.get('courses', [])
            if courses:
                return courses[0].get('assignments', [])

        return []

    def get_assignment_id_by_cmid(self, cmid: int, course_id: int) -> Optional[int]:
        """
        Find assignment ID from its course module ID (cmid).

        Args:
            cmid: Course module ID (visible in URLs)
            course_id: ID of the course

        Returns:
            Assignment ID if found, None otherwise
        """
        assignments = self.get_assignments(course_id)
        
        for assignment in assignments:
            if assignment.get('cmid') == cmid:
                return assignment.get('id')
        
        return None

    def get_submissions(
        self,
        assignment_id: int,
        status: str = "",
        since: int = 0,
        before: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get student submissions for a specific assignment.

        Args:
            assignment_id: ID of the Moodle assignment
            status: Submission status (e.g., 'submitted', 'draft', etc.)
            since: Get submissions made after this date (UNIX timestamp)
            before: Get submissions made before this date (UNIX timestamp)

        Returns:
            List of student submissions
        """
        params = {
            "assignmentids[0]": assignment_id,
            "status": status,
            "since": since,
            "before": before
        }
        
        response = self.call_api("mod_assign_get_submissions", params)
        
        if "assignments" not in response or not response["assignments"]:
            return []

        return response["assignments"][0].get("submissions", [])

    def get_assignment_submissions(self, assignment_id: int) -> List[Dict[str, Any]]:
        """
        Get all submissions for an assignment (alias for get_submissions).

        Args:
            assignment_id: ID of the assignment

        Returns:
            List of submission dictionaries
        """
        return self.get_submissions(assignment_id)

    def get_user_submission(self, assignment_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get a specific user's submission for an assignment.

        Args:
            assignment_id: ID of the assignment
            user_id: ID of the user

        Returns:
            Submission dictionary or empty dict if not found
        """
        submissions = self.get_assignment_submissions(assignment_id)

        for submission in submissions:
            if submission.get('userid') == user_id:
                return submission

        return {}
