"""Test the login module."""

from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from regscale.core.login import get_regscale_token
from regscale.core.app.api import Api
from regscale.core.app.application import Application


@patch("regscale.core.login.Api.post")
@patch.dict("os.environ", {"REGSCALE_DOMAIN": "example_value"})
def test_get_regscale_token(mock_post):
    """Test get_regscale_token with fallback to old API (backward compatibility)"""
    api = Api()

    # Mock responses for fallback scenario
    mock_response_v2 = MagicMock()
    mock_response_v2.status_code = 400
    mock_response_v2.raise_for_status.side_effect = HTTPError()

    mock_response_v1 = MagicMock()
    mock_response_v1.status_code = 200
    mock_response_v1.url = "example_value/api/authentication/login"
    mock_response_v1.json.return_value = {
        "id": "example_id",
        "auth_token": "example_token",
    }

    # Set up side_effect for multiple calls
    mock_post.side_effect = [
        mock_response_v2,
        mock_response_v1,  # First call
        mock_response_v2,
        mock_response_v1,  # Second call
        mock_response_v2,
        mock_response_v1,  # Third call
    ]

    result = get_regscale_token(api=api, username="example_user", password="example_password")
    result2 = get_regscale_token(
        api=api,
        username="example_user",
        password="example_password",
        domain="example2_domain",
    )
    result3 = get_regscale_token(
        api=api,
        username="example_user",
        password="example_password",
        domain="example3_domain",
        mfa_token="123456",
    )

    assert result == ("example_id", "example_token")
    assert result2 == ("example_id", "example_token")
    assert result3 == ("example_id", "example_token")


@patch("regscale.core.login.Api.post")
@patch.dict("os.environ", {"REGSCALE_DOMAIN": "https://example.com"})
def test_get_regscale_token_with_app_id_success(mock_post):
    """Test successful authentication with app_id (API version 2.0)"""
    api = Api()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/api/authentication/login"
    mock_response.json.return_value = {
        "accessToken": {
            "id": "new_user_id",
            "authToken": "new_auth_token",
        }
    }
    mock_post.return_value = mock_response

    result = get_regscale_token(
        api=api,
        username="test_user",
        password="test_password",
        domain="https://example.com",
        app_id=1,
    )

    assert result == ("new_user_id", "new_auth_token")
    assert mock_post.call_count == 1
    call_args = mock_post.call_args
    assert call_args[1]["json"]["appId"] == 1
    assert call_args[1]["headers"] == {"X-Api-Version": "2.0"}


@patch("regscale.core.login.Api.post")
@patch.dict("os.environ", {"REGSCALE_DOMAIN": "https://example.com"})
def test_get_regscale_token_with_custom_app_id(mock_post):
    """Test authentication with custom app_id value"""
    api = Api()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/api/authentication/login"
    mock_response.json.return_value = {
        "accessToken": {
            "id": "custom_user_id",
            "authToken": "custom_auth_token",
        }
    }
    mock_post.return_value = mock_response

    result = get_regscale_token(
        api=api,
        username="test_user",
        password="test_password",
        domain="https://example.com",
        app_id=5,
    )

    assert result == ("custom_user_id", "custom_auth_token")
    call_args = mock_post.call_args
    assert call_args[1]["json"]["appId"] == 5
    assert call_args[1]["headers"] == {"X-Api-Version": "2.0"}


@patch("regscale.core.login.Api.post")
@patch.dict("os.environ", {"REGSCALE_DOMAIN": "https://example.com"})
def test_get_regscale_token_fallback_to_old_api(mock_post):
    """Test fallback to old API version when app_id authentication fails"""
    import copy

    api = Api()

    # Capture the arguments passed to each call
    captured_calls = []

    def capture_and_respond(*args, **kwargs):
        # Make a deep copy of the json argument to preserve its state at call time
        captured_calls.append({"json": copy.deepcopy(kwargs.get("json", {})), "headers": kwargs.get("headers", {})})

        # First call raises HTTPError
        if len(captured_calls) == 1:
            mock_response_v2 = MagicMock()
            mock_response_v2.status_code = 400
            mock_response_v2.raise_for_status.side_effect = HTTPError()
            return mock_response_v2
        # Second call succeeds
        else:
            mock_response_v1 = MagicMock()
            mock_response_v1.status_code = 200
            mock_response_v1.url = "https://example.com/api/authentication/login"
            mock_response_v1.json.return_value = {
                "id": "old_user_id",
                "auth_token": "old_auth_token",
            }
            return mock_response_v1

    mock_post.side_effect = capture_and_respond

    result = get_regscale_token(
        api=api,
        username="test_user",
        password="test_password",
        domain="https://example.com",
        app_id=1,
    )

    assert result == ("old_user_id", "old_auth_token")
    assert mock_post.call_count == 2

    # Verify first call had app_id
    assert captured_calls[0]["json"]["appId"] == 1
    assert captured_calls[0]["headers"] == {"X-Api-Version": "2.0"}

    # Verify second call did not have app_id
    assert "appId" not in captured_calls[1]["json"]
    assert captured_calls[1]["headers"] == {}


@patch("regscale.core.login.Api.post")
@patch.dict("os.environ", {"REGSCALE_DOMAIN": "https://example.com"})
def test_get_regscale_token_with_mfa_and_app_id(mock_post):
    """Test authentication with both MFA token and app_id"""
    api = Api()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.url = "https://example.com/api/authentication/login"
    mock_response.json.return_value = {
        "accessToken": {
            "id": "mfa_user_id",
            "authToken": "mfa_auth_token",
        }
    }
    mock_post.return_value = mock_response

    result = get_regscale_token(
        api=api,
        username="test_user",
        password="test_password",
        domain="https://example.com",
        mfa_token="123456",
        app_id=2,
    )

    assert result == ("mfa_user_id", "mfa_auth_token")
    call_args = mock_post.call_args
    assert call_args[1]["json"]["mfaToken"] == "123456"
    assert call_args[1]["json"]["appId"] == 2
    assert call_args[1]["headers"] == {"X-Api-Version": "2.0"}
