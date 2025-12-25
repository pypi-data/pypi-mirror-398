"""
Main Moodle API client.

Provides a unified interface to all Moodle modules through composition.
This is a facade pattern that aggregates specialized modules.
"""

import logging
from typing import Optional
from .groups import MoodleGroups
from .assignments import MoodleAssignments
from .grades import MoodleGrades
from .users import MoodleUsers


class MoodleAPI:
    """
    Main facade class for interacting with Moodle API.
    
    This class aggregates specialized modules for different Moodle functionalities:
    - groups: Group, grouping, and cohort management
    - assignments: Assignment and submission handling
    - grades: Grade management
    - users: User account management
    
    Example:
        >>> moodle = MoodleAPI("https://moodle.example.com", "token")
        >>> moodle.groups.add_user_to_group(group_id=1, user_id=42)
        >>> moodle.users.create_user("johndoe", "pass123", "John", "Doe", "john@example.com")
        >>> moodle.assignments.get_assignments(course_id=123)
    """

    def __init__(self, moodle_url: str, token: str, timeout: int = 30,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Moodle API client with all modules.

        Args:
            moodle_url: Base URL of the Moodle instance (e.g., 'https://moodle.example.com')
            token: Web service token for authentication
            timeout: Request timeout in seconds (default: 30)
            logger: Optional logger instance (will be shared across all modules)

        Raises:
            ValueError: If moodle_url or token is empty
        """
        if not moodle_url or not token:
            raise ValueError("Both moodle_url and token are required")

        # Initialize all specialized modules with shared logger
        self.groups = MoodleGroups(moodle_url, token, timeout=timeout, logger=logger)
        self.assignments = MoodleAssignments(moodle_url, token, timeout=timeout, logger=logger)
        self.grades = MoodleGrades(moodle_url, token, timeout=timeout, logger=logger)
        self.users = MoodleUsers(moodle_url, token, timeout=timeout, logger=logger)

        # Store base module for direct API access
        self._base = self.groups  # Reuse base from one of the modules

    def get_site_info(self) -> dict:
        """
        Get information about the Moodle site including version.
        
        This method retrieves general information about the Moodle site,
        including the Moodle version, site name, and available functions.
        
        Returns:
            Dictionary containing site information with keys:
                - sitename: Name of the Moodle site
                - username: Current user's username
                - firstname: Current user's first name
                - lastname: Current user's last name
                - release: Moodle version (e.g., "4.1.1 (Build: 20230123)")
                - version: Moodle version code
                - functions: List of available web service functions
                
        Example:
            >>> moodle = MoodleAPI("https://moodle.com", "token")
            >>> info = moodle.get_site_info()
            >>> print(f"Moodle version: {info['release']}")
            Moodle version: 4.1.1 (Build: 20230123)
            
        Raises:
            MoodleAuthenticationError: If authentication fails
            MoodleAPIError: If the API call fails
        """
        return self._base.call_api('core_webservice_get_site_info')

    def check_moodle_version(self, min_version: str = "3.9") -> bool:
        """
        Check if the Moodle version meets the minimum requirement.
        
        Args:
            min_version: Minimum required version (e.g., "3.9", "4.0")
            
        Returns:
            True if Moodle version >= min_version, False otherwise
            
        Example:
            >>> moodle = MoodleAPI("https://moodle.com", "token")
            >>> if moodle.check_moodle_version("3.9"):
            ...     print("Moodle version is compatible")
        """
        try:
            info = self.get_site_info()
            release = info.get('release', '')
            # Extract version number (e.g., "4.1.1" from "4.1.1 (Build: 20230123)")
            import re
            match = re.match(r'(\d+\.\d+)', release)
            if match:
                current_version = match.group(1)
                # Simple version comparison
                current_parts = [int(x) for x in current_version.split('.')]
                min_parts = [int(x) for x in min_version.split('.')]
                
                # Pad shorter version with zeros
                while len(current_parts) < len(min_parts):
                    current_parts.append(0)
                while len(min_parts) < len(current_parts):
                    min_parts.append(0)
                    
                return current_parts >= min_parts
        except Exception:
            pass
        return False

    def __repr__(self) -> str:
        """String representation of the MoodleAPI instance."""
        return f"<MoodleAPI: groups, assignments, grades, users>"
