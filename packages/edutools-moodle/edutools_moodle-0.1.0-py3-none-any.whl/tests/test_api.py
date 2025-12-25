"""
Tests for MoodleAPI facade and modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from edutools_moodle import MoodleAPI, MoodleBase, MoodleGroups, MoodleUsers
from edutools_moodle.base import (
    MoodleAPIError,
    MoodleAuthenticationError,
    MoodleResourceNotFoundError
)


class TestMoodleBase:
    """Tests for MoodleBase class."""

    def test_initialization(self):
        """Test MoodleBase initialization."""
        base = MoodleBase("https://moodle.example.com", "test_token")
        assert base.moodle_url == "https://moodle.example.com"
        assert base.token == "test_token"
        assert base.timeout == 30  # default timeout

    def test_initialization_with_custom_timeout(self):
        """Test MoodleBase initialization with custom timeout."""
        base = MoodleBase("https://moodle.example.com", "test_token", timeout=60)
        assert base.timeout == 60

    def test_initialization_with_logger(self):
        """Test MoodleBase initialization with custom logger."""
        import logging
        logger = logging.getLogger("test")
        base = MoodleBase("https://moodle.example.com", "test_token", logger=logger)
        assert base.logger == logger

    def test_initialization_strips_trailing_slash(self):
        """Test that trailing slash is removed from URL."""
        base = MoodleBase("https://moodle.example.com/", "test_token")
        assert base.moodle_url == "https://moodle.example.com"

    def test_initialization_requires_url(self):
        """Test that initialization fails without URL."""
        with pytest.raises(ValueError):
            MoodleBase("", "test_token")

    def test_initialization_requires_token(self):
        """Test that initialization fails without token."""
        with pytest.raises(ValueError):
            MoodleBase("https://moodle.example.com", "")

    def test_session_property_lazy_loading(self):
        """Test that session is created on first access."""
        base = MoodleBase("https://moodle.example.com", "test_token")
        
        # Session should be None initially
        assert base._session is None
        
        # Accessing session property should create it
        session = base.session
        assert session is not None
        assert base._session is session

    @patch('edutools_moodle.base.requests.Session.post')
    def test_call_api_success(self, mock_post):
        """Test successful API call."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        base = MoodleBase("https://moodle.example.com", "test_token")
        result = base.call_api("test_function", {"param": "value"})

        assert result == {"status": "success"}
        mock_post.assert_called_once()

    @patch('edutools_moodle.base.requests.Session.post')
    def test_call_api_with_error_response(self, mock_post):
        """Test API call with Moodle error in response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "exception": "invalid_parameter_exception",
            "errorcode": "invalidparameter",
            "message": "Invalid parameter value"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        base = MoodleBase("https://moodle.example.com", "test_token")

        with pytest.raises(MoodleAPIError):
            base.call_api("test_function", {})

    @patch('edutools_moodle.base.requests.Session.post')
    def test_call_api_authentication_error(self, mock_post):
        """Test API call with authentication error."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "exception": "webservice_access_exception",
            "errorcode": "accessexception",
            "message": "Invalid token"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        base = MoodleBase("https://moodle.example.com", "test_token")

        with pytest.raises(MoodleAuthenticationError):
            base.call_api("test_function", {})

    @patch('edutools_moodle.base.requests.Session.post')
    def test_call_api_timeout(self, mock_post):
        """Test API call with timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout()

        base = MoodleBase("https://moodle.example.com", "test_token")

        with pytest.raises(MoodleAPIError):
            base.call_api("test_function", {})

    def test_close_method(self):
        """Test close method closes session."""
        base = MoodleBase("https://moodle.example.com", "test_token")
        
        # Access session to create it
        session = base.session
        session.close = Mock()
        
        # Close should close the session
        base.close()
        session.close.assert_called_once()


class TestMoodleAPI:
    """Tests for MoodleAPI facade class."""

    def test_initialization(self):
        """Test that MoodleAPI initializes all modules."""
        api = MoodleAPI("https://moodle.example.com", "test_token")
        
        assert isinstance(api.groups, MoodleGroups)
        assert isinstance(api.users, MoodleUsers)
        assert hasattr(api, 'assignments')
        assert hasattr(api, 'grades')

    def test_initialization_requires_credentials(self):
        """Test that MoodleAPI requires URL and token."""
        with pytest.raises(ValueError):
            MoodleAPI("", "token")
        
        with pytest.raises(ValueError):
            MoodleAPI("https://moodle.example.com", "")

    def test_repr(self):
        """Test string representation."""
        api = MoodleAPI("https://moodle.example.com", "test_token")
        repr_str = repr(api)
        assert "MoodleAPI" in repr_str
        assert "groups" in repr_str


class TestMoodleGroups:
    """Tests for MoodleGroups module."""

    @patch('edutools_moodle.base.requests.post')
    def test_get_course_groups(self, mock_post):
        """Test getting course groups."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 1, "name": "Group A"},
            {"id": 2, "name": "Group B"}
        ]
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        result = groups.get_course_groups(123)

        assert len(result) == 2
        assert result[0]["name"] == "Group A"

    @patch('edutools_moodle.base.requests.Session.post')
    def test_get_group_id_by_name_found(self, mock_post):
        """Test finding group by name when it exists."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 1, "name": "Group A"},
            {"id": 2, "name": "Group B"}
        ]
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        group_id = groups.get_group_id_by_name(123, "Group B")

        assert group_id == 2

    @patch('edutools_moodle.base.requests.Session.post')
    def test_get_group_id_by_name_not_found(self, mock_post):
        """Test finding group by name when it doesn't exist."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 1, "name": "Group A"}
        ]
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        group_id = groups.get_group_id_by_name(123, "Group X")

        assert group_id is None

    @patch('edutools_moodle.base.requests.Session.post')
    def test_create_or_get_group_existing(self, mock_post):
        """Test create_or_get_group when group exists."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": 5, "name": "Existing Group"}
        ]
        mock_response.raise_for_status = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        group_id = groups.create_or_get_group(123, "Existing Group")

        assert group_id == 5

    @patch('edutools_moodle.base.requests.Session.post')
    def test_get_user_groups(self, mock_post):
        """Test getting all groups for a user."""
        # First call returns all groups
        # Second call returns members for group 1
        # Third call returns members for group 2
        mock_response_groups = Mock()
        mock_response_groups.json.return_value = [
            {"id": 1, "name": "Group A"},
            {"id": 2, "name": "Group B"}
        ]
        mock_response_groups.status_code = 200

        mock_response_members_1 = Mock()
        mock_response_members_1.json.return_value = [
            {"userids": [10, 20]}
        ]
        mock_response_members_1.status_code = 200

        mock_response_members_2 = Mock()
        mock_response_members_2.json.return_value = [
            {"userids": [30]}
        ]
        mock_response_members_2.status_code = 200

        mock_post.side_effect = [
            mock_response_groups,
            mock_response_members_1,
            mock_response_members_2
        ]

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        user_groups = groups.get_user_groups(123, 10)

        # User 10 should only be in Group A
        assert len(user_groups) == 1
        assert user_groups[0]["name"] == "Group A"

    @patch('edutools_moodle.base.requests.Session.post')
    def test_add_user_to_group(self, mock_post):
        """Test adding user to group."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        groups = MoodleGroups("https://moodle.example.com", "test_token")
        result = groups.add_user_to_group(1, 42)

        assert result["status"] == "success"


class TestMoodleUsers:
    """Tests for MoodleUsers module."""

    @patch('edutools_moodle.base.requests.post')
    def test_check_username_exists_true(self, mock_post):
        """Test checking existing username."""
        mock_response = Mock()
        mock_response.json.return_value = {"users": [{"id": 1, "username": "johndoe"}]}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        users = MoodleUsers("https://moodle.example.com", "test_token")
        exists = users.check_username_exists("johndoe")

        assert exists is True

    @patch('edutools_moodle.base.requests.post')
    def test_check_username_exists_false(self, mock_post):
        """Test checking non-existing username."""
        mock_response = Mock()
        mock_response.json.return_value = {"users": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        users = MoodleUsers("https://moodle.example.com", "test_token")
        exists = users.check_username_exists("johndoe")

        assert exists is False


class TestIntegration:
    """Integration tests for MoodleAPI facade."""

    @patch('edutools_moodle.base.requests.post')
    def test_facade_groups_access(self, mock_post):
        """Test accessing groups through facade."""
        mock_response = Mock()
        mock_response.json.return_value = [{"id": 1, "name": "Group A"}]
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        api = MoodleAPI("https://moodle.example.com", "test_token")
        groups = api.groups.get_course_groups(123)

        assert len(groups) == 1
        assert groups[0]["name"] == "Group A"

    @patch('edutools_moodle.base.requests.post')
    def test_facade_users_access(self, mock_post):
        """Test accessing users through facade."""
        mock_response = Mock()
        mock_response.json.return_value = {"users": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        api = MoodleAPI("https://moodle.example.com", "test_token")
        exists = api.users.check_username_exists("testuser")

        assert exists is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
