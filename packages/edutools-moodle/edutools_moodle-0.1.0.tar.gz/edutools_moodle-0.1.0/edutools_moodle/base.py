"""
Base class for Moodle API interactions.

Provides core functionality for making API calls to Moodle Web Services.
"""

import requests
import logging
from typing import Dict, Any, Optional


# Custom exceptions
class MoodleAPIError(Exception):
    """Base exception for Moodle API errors"""
    pass


class MoodleAuthenticationError(MoodleAPIError):
    """Authentication/token errors"""
    pass


class MoodleResourceNotFoundError(MoodleAPIError):
    """Resource not found errors"""
    pass


class MoodleBase:
    """
    Base class for interacting with Moodle REST API.
    Provides common functionality for all Moodle API modules.
    """

    def __init__(self, moodle_url: str, token: str, timeout: int = 30, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the Moodle API base client.

        Args:
            moodle_url: Base URL of the Moodle instance (e.g., 'https://moodle.example.com')
            token: Web service token for authentication
            timeout: Request timeout in seconds (default: 30)
            logger: Optional logger instance (will create one if not provided)

        Raises:
            ValueError: If moodle_url or token is empty
        """
        if not moodle_url or not token:
            raise ValueError("Both moodle_url and token are required")

        self.moodle_url = moodle_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """
        Lazy-loaded session for connection pooling and better performance.
        
        Returns:
            Configured requests Session instance
        """
        if self._session is None:
            self._session = requests.Session()
            self.logger.debug("Created new HTTP session for connection pooling")
        return self._session

    def call_api(self, function_name: str, params: Dict[str, Any] = None) -> Any:
        """
        Call a Moodle Web Service API function.

        Args:
            function_name: Name of the Moodle API function to call
            params: Dictionary of parameters to pass to the API function

        Returns:
            API response (parsed JSON)

        Raises:
            MoodleAuthenticationError: If authentication fails
            MoodleAPIError: For Moodle-specific errors
            TimeoutError: If request times out
        """
        endpoint = f"{self.moodle_url}/webservice/rest/server.php"

        # Build the payload with authentication and format
        payload = {
            'wstoken': self.token,
            'moodlewsrestformat': 'json',
            'wsfunction': function_name,
        }

        # Add function-specific parameters
        if params:
            payload.update(params)

        self.logger.debug(f"Calling Moodle API: {function_name}")

        try:
            response = self.session.post(endpoint, data=payload, timeout=self.timeout)
            response.raise_for_status()
            
            json_response = response.json()
            
            # Validate and check for Moodle-specific errors
            return self._validate_response(json_response, function_name)
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout calling {function_name}")
            raise TimeoutError(f"Request to Moodle API timed out for function: {function_name}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                self.logger.error(f"Authentication failed for {function_name}")
                raise MoodleAuthenticationError("Invalid Moodle token or unauthorized access")
            self.logger.error(f"HTTP error calling {function_name}: {e}")
            raise MoodleAPIError(f"HTTP error calling '{function_name}': {e}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error calling {function_name}: {e}")
            raise MoodleAPIError(f"Error calling Moodle API function '{function_name}': {e}")

    def _validate_response(self, response: Any, function_name: str) -> Any:
        """
        Validate Moodle API response and check for errors.

        Args:
            response: API response to validate
            function_name: Name of the function that was called

        Returns:
            Validated response

        Raises:
            MoodleAuthenticationError: If authentication error in response
            MoodleAPIError: If other Moodle error in response
        """
        if response is None:
            self.logger.warning(f"Empty response from {function_name}")
            return response

        # Check for Moodle exception in response
        if isinstance(response, dict):
            if 'exception' in response:
                error_code = response.get('errorcode', '')
                error_msg = response.get('message', 'Unknown error')
                
                self.logger.error(f"{function_name} returned error: {error_msg} (code: {error_code})")
                
                if 'invalidtoken' in error_code or 'accessexception' in error_code:
                    raise MoodleAuthenticationError(f"{function_name}: {error_msg}")
                raise MoodleAPIError(f"{function_name}: {error_msg}")
            
            # Log warnings if present
            if 'warnings' in response and response['warnings']:
                for warning in response['warnings']:
                    self.logger.warning(f"{function_name} warning: {warning.get('message', warning)}")

        self.logger.debug(f"{function_name} completed successfully")
        return response

    def close(self):
        """Close the session and cleanup resources."""
        if self._session:
            self._session.close()
            self._session = None
