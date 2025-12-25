"""
Groups management module for Moodle API.

Handles operations related to groups, groupings, and cohorts.
"""

from .base import MoodleBase
from typing import List, Dict, Any, Optional


class MoodleGroups(MoodleBase):
    """
    Class for managing groups, groupings, and cohorts in Moodle.
    """

    # ========== Groups Methods ==========

    def get_course_groups(self, course_id: int) -> List[Dict[str, Any]]:
        """
        Get all groups in a course.

        Args:
            course_id: ID of the course

        Returns:
            List of group dictionaries
        """
        params = {'courseid': course_id}
        return self.call_api('core_group_get_groups', params)

    def get_group_by_name(self, course_id: int, group_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a group by name in a course.

        Args:
            course_id: ID of the course
            group_name: Name of the group

        Returns:
            Group dictionary if found, None otherwise
        """
        groups = self.get_course_groups(course_id)
        for group in groups:
            if group.get('name') == group_name:
                return group
        return None

    def get_group_id_by_name(self, course_id: int, group_name: str) -> Optional[int]:
        """
        Retrieve the ID of a group by its name in a specific course.

        Args:
            course_id: ID of the course
            group_name: Name of the group to find

        Returns:
            Group ID if found, None otherwise
        """
        params = {'courseid': course_id}
        response = self.call_api('core_group_get_groups', params)

        for group in response:
            if group.get('name') == group_name:
                return group.get('id')

        return None

    def create_group(self, course_id: int, group_name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new group in a course.

        Args:
            course_id: ID of the course
            group_name: Name for the new group
            description: Optional description for the group

        Returns:
            API response with created group information
        """
        params = {
            'groups[0][courseid]': course_id,
            'groups[0][name]': group_name,
        }
        if description:
            params['groups[0][description]'] = description

        return self.call_api('core_group_create_groups', params)

    def delete_group(self, group_id: int) -> Dict[str, Any]:
        """
        Delete a group.

        Args:
            group_id: ID of the group to delete

        Returns:
            API response

        Raises:
            Exception: If the deletion operation fails
        """
        params = {'groupids[0]': group_id}
        return self.call_api('core_group_delete_groups', params)

    def add_user_to_group(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """
        Add a user to a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user

        Returns:
            API response
        """
        params = {
            'members[0][groupid]': group_id,
            'members[0][userid]': user_id,
        }
        return self.call_api('core_group_add_group_members', params)

    def remove_member_from_group(self, group_id: int, user_id: int) -> Dict[str, Any]:
        """
        Remove a member from a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user

        Returns:
            API response with warnings if any

        Raises:
            Exception: If the removal operation fails
        """
        try:
            params = {
                'members[0][groupid]': group_id,
                'members[0][userid]': user_id,
            }

            response = self.call_api('core_group_delete_group_members', params)

            if 'warnings' in response and response['warnings']:
                self.logger.warning(f"Warnings when removing user {user_id} from group {group_id}: {response['warnings']}")
            else:
                self.logger.info(f"User {user_id} successfully removed from group {group_id}")

            return response

        except Exception as e:
            raise Exception(f"Error removing user {user_id} from group {group_id}: {e}")

    def get_group_members(self, group_id: int) -> List[int]:
        """
        Get all members of a group.

        Args:
            group_id: ID of the group

        Returns:
            List of user IDs in the group
        """
        params = {'groupids[0]': group_id}
        response = self.call_api('core_group_get_group_members', params)

        user_ids = []
        if isinstance(response, list):
            for group_data in response:
                user_ids.extend(group_data.get('userids', []))

        return user_ids

    def get_group_members_info(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed information about all members of a group.

        Args:
            group_id: ID of the group

        Returns:
            List of dictionaries with user information (id, fullname, email, etc.)
        """
        params = {'groupids[0]': group_id}
        response = self.call_api('core_group_get_group_members', params)

        if isinstance(response, list) and response:
            return response[0].get('users', [])

        return []

    def get_user_groups(self, course_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all groups that a user belongs to in a specific course.

        Args:
            course_id: ID of the course
            user_id: ID of the user

        Returns:
            List of group dictionaries the user is a member of
        """
        all_groups = self.get_course_groups(course_id)
        user_groups = []

        for group in all_groups:
            group_id = group.get('id')
            if group_id and self.is_user_in_group(group_id, user_id):
                user_groups.append(group)

        return user_groups

    def create_or_get_group(
        self,
        course_id: int,
        group_name: str,
        description: str = ""
    ) -> int:
        """
        Create a group or return its ID if it already exists.

        Args:
            course_id: ID of the course
            group_name: Name of the group
            description: Optional description

        Returns:
            Group ID (existing or newly created)

        Raises:
            Exception: If group creation fails
        """
        # Check if group already exists
        existing_group = self.get_group_by_name(course_id, group_name)
        if existing_group:
            return existing_group['id']

        # Create new group
        response = self.create_group(course_id, group_name, description)
        
        if isinstance(response, list) and len(response) > 0 and 'id' in response[0]:
            return response[0]['id']
        
        raise Exception(f"Failed to create group '{group_name}': {response}")

    def move_user_to_group(
        self,
        course_id: int,
        user_id: int,
        old_group_id: Optional[int],
        new_group_id: int
    ) -> bool:
        """
        Move a user from one group to another.

        Args:
            course_id: ID of the course
            user_id: ID of the user
            old_group_id: ID of the current group (can be None if user not in a group)
            new_group_id: ID of the target group

        Returns:
            True if move was successful

        Raises:
            Exception: If the operation fails
        """
        try:
            # Remove from old group if specified
            if old_group_id is not None:
                self.remove_member_from_group(old_group_id, user_id)

            # Add to new group
            self.add_user_to_group(new_group_id, user_id)
            
            return True

        except Exception as e:
            raise Exception(f"Error moving user {user_id} to group {new_group_id}: {e}")

    def batch_enroll_users_to_groups(
        self,
        course_id: int,
        enrollments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enroll multiple users to groups in batch.

        Args:
            course_id: ID of the course
            enrollments: List of dicts with 'user_id', 'group_name' keys

        Returns:
            Dictionary with 'success' count and 'errors' list

        Example:
            enrollments = [
                {'user_id': 123, 'group_name': 'Group A'},
                {'user_id': 456, 'group_name': 'Group B'}
            ]
        """
        results = {'success': 0, 'errors': []}

        for enrollment in enrollments:
            user_id = enrollment.get('user_id')
            group_name = enrollment.get('group_name')

            try:
                # Get or create group
                group_id = self.create_or_get_group(course_id, group_name)
                
                # Add user to group
                self.add_user_to_group(group_id, user_id)
                results['success'] += 1

            except Exception as e:
                results['errors'].append({
                    'user_id': user_id,
                    'group_name': group_name,
                    'error': str(e)
                })

        return results

    def send_message_to_group(self, group_id: int, subject: str, message: str) -> Dict[str, Any]:
        """
        Send a message to all members of a group.

        Args:
            group_id: ID of the group
            subject: Subject of the message
            message: Content of the message (HTML supported)

        Returns:
            API response with sent message IDs

        Raises:
            Exception: If the group has no members or message sending fails
        """
        members = self.get_group_members_info(group_id)

        if not members:
            raise Exception(f"Group {group_id} has no members")

        full_message = f"<strong>{subject}</strong><br>{message}"

        params = {}
        for i, member in enumerate(members):
            params[f'messages[{i}][touserid]'] = member['id']
            params[f'messages[{i}][text]'] = full_message
            params[f'messages[{i}][textformat]'] = '1'  # HTML format

        return self.call_api('core_message_send_instant_messages', params)

    def get_user_groups_with_names(self, course_id: int, user_id: int) -> List[str]:
        """
        Get list of group names that a user belongs to in a course.

        Args:
            course_id: ID of the course
            user_id: ID of the user

        Returns:
            List of group names
        """
        user_groups = self.get_user_groups(course_id, user_id)
        return [group.get('name') for group in user_groups if 'name' in group]

    def get_all_course_groups_dict(self, course_id: int) -> Dict[str, int]:
        """
        Get all groups in a course as a dictionary mapping names to IDs.

        Args:
            course_id: ID of the course

        Returns:
            Dictionary with group names as keys and IDs as values
            Example: {'Group A': 1, 'Group B': 2}
        """
        groups = self.get_course_groups(course_id)
        return {group['name']: group['id'] for group in groups if 'name' in group and 'id' in group}

    def is_user_in_group(self, group_id: int, user_id: int) -> bool:
        """
        Check if a user is a member of a specific group.

        Args:
            group_id: ID of the group
            user_id: ID of the user

        Returns:
            True if user is in the group, False otherwise
        """
        try:
            members = self.get_group_members(group_id)
            return user_id in members
        except Exception as e:
            self.logger.error(f"Error checking if user {user_id} is in group {group_id}: {e}")
            return False

    # ========== Groupings Methods ==========

    def create_or_get_grouping(
        self,
        course_id: int,
        grouping_name: str,
        description: str = ""
    ) -> Optional[int]:
        """
        Create a grouping in a course or return its ID if it already exists.

        Args:
            course_id: ID of the course
            grouping_name: Name of the grouping
            description: Description of the grouping (default empty)

        Returns:
            ID of the grouping

        Raises:
            Exception: If creation or retrieval fails
        """
        try:
            # Check if grouping already exists
            params_get = {'courseid': course_id}
            response = self.call_api('core_group_get_course_groupings', params_get)

            for grouping in response:
                if grouping.get('name') == grouping_name:
                    return grouping['id']

            # Create grouping if it doesn't exist
            params_create = {
                'groupings[0][courseid]': course_id,
                'groupings[0][name]': grouping_name,
                'groupings[0][idnumber]': grouping_name,
                'groupings[0][description]': description,
                'groupings[0][descriptionformat]': 1,  # HTML format
            }
            response_create = self.call_api('core_group_create_groupings', params_create)

            if isinstance(response_create, list) and len(response_create) > 0 and 'id' in response_create[0]:
                grouping_id = response_create[0]['id']
                self.logger.info(f"Grouping '{grouping_name}' created with ID {grouping_id}")
                return grouping_id
            else:
                raise Exception(f"Unexpected API response when creating grouping: {response_create}")

        except Exception as e:
            raise Exception(f"Error creating or retrieving grouping: {e}")

    # ========== Cohorts Methods ==========

    def is_user_in_cohort(self, user_id: int, cohort_name: str = "IIR2425") -> bool:
        """
        Check if a user is enrolled in a specific cohort.

        Args:
            user_id: ID of the user in Moodle
            cohort_name: Name of the cohort to check

        Returns:
            True if the user is in the cohort, False otherwise
        """
        response = self.call_api("core_cohort_get_cohorts", {})

        if not isinstance(response, list):
            self.logger.error(f"Unexpected response for core_cohort_get_cohorts: {response}")
            return False

        # Find the cohort by name
        cohort_id = None
        for cohort in response:
            if isinstance(cohort, dict) and cohort.get("name") == cohort_name:
                cohort_id = cohort.get("id")
                break

        if not cohort_id:
            self.logger.warning(f"Cohort '{cohort_name}' not found")
            return False

        # Get cohort members
        params = {'cohortids[0]': cohort_id}
        members_response = self.call_api("core_cohort_get_cohort_members", params)

        if not isinstance(members_response, list):
            self.logger.error(f"Unexpected response for core_cohort_get_cohort_members: {members_response}")
            return False

        # Check if user is in the members list
        for cohort_data in members_response:
            if cohort_data.get('cohortid') == cohort_id:
                return user_id in cohort_data.get('userids', [])

        return False

    def enroll_user_in_cohort(self, user_id: int, cohort_name: str = "IIR2425") -> bool:
        """
        Enroll a user in a specific cohort.

        Args:
            user_id: ID of the user in Moodle
            cohort_name: Name of the cohort to enroll the user in

        Returns:
            True if enrollment succeeds, False otherwise
        """
        response = self.call_api("core_cohort_get_cohorts", {})
        cohort_id = None

        # Find cohort ID
        for cohort in response:
            if cohort.get("name") == cohort_name:
                cohort_id = cohort.get("id")
                break

        if cohort_id is None:
            self.logger.warning(f"Cohort '{cohort_name}' not found")
            return False

        # Enroll user
        enroll_response = self.call_api("core_cohort_add_cohort_members", {
            "members[0][cohorttype][type]": "id",
            "members[0][cohorttype][value]": cohort_id,
            "members[0][usertype][type]": "id",
            "members[0][usertype][value]": user_id
        })

        # Check for Moodle warnings
        if "warnings" in enroll_response and enroll_response["warnings"]:
            self.logger.warning(f"Warnings during enrollment: {enroll_response['warnings']}")
            return False

        return True
