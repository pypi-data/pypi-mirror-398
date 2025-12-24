from typing import Any, Dict

import pytest

from wallaroo.user import User


@pytest.fixture
def client(mocker, mock_http_client):
    """Fixture providing a mock Client instance."""
    client = mocker.Mock()
    client.mlops.return_value = mocker.Mock()
    client.httpx_client = mock_http_client
    return client


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Fixture providing sample user data."""
    return {
        "id": "123",
        "email": "test@example.com",
        "username": "testuser",
        "enabled": True,
        "createdTimestamp": "2024-01-01T00:00:00Z",
    }


def test_user_initialization(client, sample_user_data):
    """Test that User initializes correctly with valid data."""
    user = User(client, sample_user_data)

    assert user.id() == "123"
    assert user.email() == "test@example.com"
    assert user.username() == "testuser"
    assert user.enabled() is True


@pytest.mark.parametrize(
    "data,expected_email",
    [
        (
            {
                "id": "123",
                "username": "testuser",
                "enabled": True,
                "createdTimestamp": "2024-01-01T00:00:00Z",
            },
            "admin@keycloak",
        ),
        (
            {
                "id": "123",
                "email": "custom@example.com",
                "username": "testuser",
                "enabled": True,
                "createdTimestamp": "2024-01-01T00:00:00Z",
            },
            "custom@example.com",
        ),
    ],
)
def test_user_initialization_email_cases(client, data, expected_email):
    """Test User initialization with different email scenarios."""
    user = User(client, data)
    assert user.email() == expected_email


def test_user_repr(client, sample_user_data):
    """Test the string representation of User."""
    user = User(client, sample_user_data)
    expected_repr = (
        'User({"id": "123", "email": "test@example.com", '
        '"username": "testuser", "enabled": "True")'
    )
    assert repr(user) == expected_repr


def test_list_users_success(client, mocker, mock_http_client):
    """Test successful listing of users."""
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "users": {
            "1": {"id": "1", "username": "user1"},
            "2": {"id": "2", "username": "user2"},
        }
    }

    mock_http_client.post.return_value = mock_response

    users = list(User.list_users(client))

    assert len(users) == 2
    assert users[0]["username"] == "user1"
    assert users[1]["username"] == "user2"


@pytest.mark.parametrize(
    "status_code,expected_error",
    [
        (500, "Failed to list exiting users"),
        (401, "Failed to list exiting users"),
        (403, "Failed to list exiting users"),
    ],
)
def test_list_users_failure(
    client, mocker, mock_http_client, status_code, expected_error
):
    """Test handling of failed user listing."""
    mock_response = mocker.Mock()
    mock_response.status_code = status_code
    mock_http_client.post.return_value = mock_response

    with pytest.raises(Exception) as exc_info:
        User.list_users(client)

    assert expected_error in str(exc_info.value)


def test_invite_user_success(client, mocker, mock_http_client):
    """Test invite user success"""
    # Mock the existing users query (first call to list_users)
    mock_users_response = mocker.Mock()
    mock_users_response.status_code = 200
    mock_users_response.json.return_value = {"users": {}}

    # Mock the invite response (second call)
    mock_invite_response = mocker.Mock()
    mock_invite_response.status_code = 200
    mock_invite_response.json.return_value = {
        "users": {
            "1": {"id": "1", "username": "user1"},
        }
    }

    # Set up the mock to return different responses for different calls
    mock_http_client.post.side_effect = [mock_users_response, mock_invite_response]

    invited_user = User.invite_user(client, "test@example.com", "password")
    assert "users" in invited_user
    assert len(invited_user["users"]) == 1


def test_invite_user_failure(client, mocker):
    """Test invite user failure"""
    # Mock the existing users query (first call to list_users)
    mock_users_response = mocker.Mock()
    mock_users_response.status_code = 200
    mock_users_response.json.return_value = {"users": {}}

    # Mock the invite response with 403
    mock_invite_response = mocker.Mock()
    mock_invite_response.status_code = 403

    # Set up the mock to return different responses for different calls
    client._http_client.post.side_effect = [mock_users_response, mock_invite_response]

    with pytest.raises(Exception) as exc_info:
        User.invite_user(client, "test@example.com", "password")
        assert "Failed to invite user" in str(exc_info.value)
