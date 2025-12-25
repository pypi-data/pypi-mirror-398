"""
Users management module for Moodle API.

Handles operations related to user accounts, authentication, and user information.
"""

from .base import MoodleBase
from typing import List, Dict, Any, Optional


class MoodleUsers(MoodleBase):
    """
    Class for managing users in Moodle.
    """

    def get_student_name(self, user_id: int) -> Optional[str]:
        """
        Retrieve the full name of a student from Moodle.

        Args:
            user_id: ID of the user

        Returns:
            Full name (firstname + lastname) or None if not found
        """
        response = self.call_api(
            "core_user_get_users",
            {"criteria[0][key]": "id", "criteria[0][value]": user_id}
        )

        if not response or "users" not in response or not response["users"]:
            return None

        user = response["users"][0]
        return f"{user['firstname']} {user['lastname']}".strip()

    def get_users_by_field(self, field: str, value: str) -> List[Dict[str, Any]]:
        """
        Search for users by a specific field.

        Args:
            field: Search field (e.g., 'email', 'username', 'id')
            value: Value to search for

        Returns:
            List of user dictionaries matching the criteria
        """
        params = {
            "criteria[0][key]": field,
            "criteria[0][value]": value
        }

        response = self.call_api("core_user_get_users", params)

        if response and "users" in response:
            return response["users"]
        return []

    def create_user(
        self,
        username: str,
        password: str,
        firstname: str,
        lastname: str,
        email: str,
        city: str = "Marrakech",
        country: str = "MA",
        send_email: bool = True
    ) -> Optional[int]:
        """
        Create a new user in Moodle.

        Args:
            username: Unique username
            password: User password
            firstname: First name
            lastname: Last name
            email: Email address
            city: City (default: Marrakech)
            country: Country code (default: MA for Morocco)
            send_email: If True, Moodle will send a welcome email

        Returns:
            ID of created user or None if error occurred
        """
        params = {
            'users[0][username]': username,
            'users[0][password]': password,
            'users[0][firstname]': firstname,
            'users[0][lastname]': lastname,
            'users[0][email]': email
        }

        try:
            response = self.call_api('core_user_create_users', params)

            if response and isinstance(response, list) and len(response) > 0 and 'id' in response[0]:
                return response[0]['id']
            elif response and isinstance(response, dict) and 'exception' in response:
                self.logger.error(f"API error for {username}: {response.get('message', 'Unknown error')}")
                return None
            else:
                self.logger.error(f"Error creating user {username}: {response}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
            return None

    def check_username_exists(self, username: str) -> bool:
        """
        Check if a username already exists.

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        try:
            response = self.call_api("core_user_get_users", {
                "criteria[0][key]": "username",
                "criteria[0][value]": username
            })

            return response and "users" in response and len(response["users"]) > 0
        except Exception as e:
            self.logger.error(f"Error checking username {username}: {e}")
            return False

    def send_notification(self, user_id: int, subject: str, message: str) -> bool:
        """
        Send a notification/message to a user.

        Args:
            user_id: ID of the recipient user
            subject: Message subject
            message: Message content

        Returns:
            True if sent successfully, False otherwise
        """
        params = {
            'messages[0][touserid]': user_id,
            'messages[0][subject]': subject,
            'messages[0][text]': message,
            'messages[0][textformat]': 1  # Text format
        }

        try:
            response = self.call_api('core_message_send_instant_messages', params)
            return response is not None
        except Exception as e:
            self.logger.error(f"Failed to send notification to user {user_id}: {str(e).replace('core_message_send_instant_messages: ', '')}")
            return False

    def enroll_user_in_course(
        self,
        course_id: int,
        user_id: int,
        role_id: int = 5,
        timestart: int = 0,
        timeend: int = 0,
        suspend: int = 0
    ) -> bool:
        """
        Enroll a user in a course.

        Args:
            course_id: ID of the course
            user_id: ID of the user to enroll
            role_id: ID of the role (5 = student by default)
            timestart: Enrollment start timestamp (0 for immediate)
            timeend: Enrollment end timestamp (0 for unlimited)
            suspend: 0 for active, 1 for suspended

        Returns:
            True if enrollment succeeds, False otherwise
        """
        params = {
            "enrolments[0][roleid]": role_id,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][timestart]": timestart,
            "enrolments[0][timeend]": timeend,
            "enrolments[0][suspend]": suspend
        }

        response = self.call_api("enrol_manual_enrol_users", params)

        if response and "warnings" in response and response["warnings"]:
            self.logger.warning(f"Warnings during enrollment: {response['warnings']}")
            return False
        return True

    def is_user_enrolled(self, course_id: int, user_id: int) -> bool:
        """
        Check if a user is enrolled in a course.

        Args:
            course_id: ID of the course
            user_id: ID of the user

        Returns:
            True if user is enrolled, False otherwise
        """
        try:
            response = self.call_api('core_enrol_get_users_courses', {'userid': user_id})

            if not isinstance(response, list):
                raise Exception(f"Unexpected response: {response}")

            for course in response:
                if isinstance(course, dict) and course.get('id') == course_id:
                    return True

            return False
        except Exception as e:
            raise Exception(f"Error checking enrollment of user {user_id} in course {course_id}: {e}")
