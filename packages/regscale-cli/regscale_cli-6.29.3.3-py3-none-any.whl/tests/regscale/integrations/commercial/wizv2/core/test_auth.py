#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for Wiz Authentication Module"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import requests

from regscale.integrations.commercial.wizv2.core.auth import (
    wiz_authenticate,
    get_token,
    generate_authentication_params,
    AUTH0_URLS,
    COGNITO_URLS,
)

PATH = "regscale.integrations.commercial.wizv2.core.auth"


class TestGenerateAuthenticationParams:
    """Test the generate_authentication_params function"""

    def test_auth0_url_generates_correct_params(self):
        """Test that Auth0 URLs generate correct authentication parameters"""
        client_id = "test_client_id"
        client_secret = "test_client_secret"

        for auth0_url in AUTH0_URLS:
            params = generate_authentication_params(client_id, client_secret, auth0_url)
            assert params == {
                "grant_type": "client_credentials",
                "audience": "beyond-api",
                "client_id": client_id,
                "client_secret": client_secret,
            }

    def test_cognito_url_generates_correct_params(self):
        """Test that Cognito URLs generate correct authentication parameters"""
        client_id = "test_client_id"
        client_secret = "test_client_secret"

        for cognito_url in COGNITO_URLS:
            params = generate_authentication_params(client_id, client_secret, cognito_url)
            assert params == {
                "grant_type": "client_credentials",
                "audience": "wiz-api",
                "client_id": client_id,
                "client_secret": client_secret,
            }

    def test_invalid_url_raises_error(self):
        """Test that an invalid URL raises ValueError"""
        client_id = "test_client_id"
        client_secret = "test_client_secret"
        invalid_url = "https://invalid.example.com/oauth/token"

        with pytest.raises(ValueError, match="Invalid Token URL"):
            generate_authentication_params(client_id, client_secret, invalid_url)

    def test_empty_credentials_still_processed(self):
        """Test that empty credentials are still processed correctly"""
        client_id = ""
        client_secret = ""

        params = generate_authentication_params(client_id, client_secret, AUTH0_URLS[0])
        assert params["client_id"] == ""
        assert params["client_secret"] == ""


class TestGetToken:
    """Test the get_token function"""

    @patch(f"{PATH}.Api")
    def test_successful_token_retrieval_first_url(self, mock_api_class):
        """Test successful token retrieval on first URL attempt"""
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()
        mock_api.app.save_config = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "scope": "read:all write:all",
        }
        mock_api.post.return_value = mock_response

        token, scope = get_token(
            api=mock_api,
            client_id="test_client",
            client_secret="test_secret",
            token_url=AUTH0_URLS[0],
        )

        assert token == "test_token_123"
        assert scope == "read:all write:all"
        mock_api.post.assert_called_once()

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_unauthorized_fallback_to_cognito(self, mock_api_class, mock_error_exit):
        """Test fallback to Cognito URL on unauthorized response"""
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()
        mock_api.app.save_config = MagicMock()

        # First response: Unauthorized
        mock_response_unauthorized = MagicMock()
        mock_response_unauthorized.ok = False
        mock_response_unauthorized.status_code = requests.codes.unauthorized
        mock_response_unauthorized.reason = "Unauthorized"

        # Second response: Success with Cognito
        mock_response_success = MagicMock()
        mock_response_success.ok = True
        mock_response_success.status_code = 200
        mock_response_success.reason = "OK"
        mock_response_success.json.return_value = {
            "access_token": "cognito_token_456",
            "scope": "wiz-api",
        }

        mock_api.post.side_effect = [mock_response_unauthorized, mock_response_success]

        token, scope = get_token(
            api=mock_api,
            client_id="test_client",
            client_secret="test_secret",
            token_url=AUTH0_URLS[0],
        )

        assert token == "cognito_token_456"
        assert scope == "wiz-api"
        assert mock_api.post.call_count == 2
        mock_api.app.save_config.assert_called_once()
        assert mock_api.config["wizAuthUrl"] == COGNITO_URLS[0]

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_unauthorized_fallback_fails_with_request_exception(self, mock_api_class, mock_error_exit):
        """Test that RequestException during fallback is handled properly"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        # First response: Unauthorized
        mock_response_unauthorized = MagicMock()
        mock_response_unauthorized.ok = False
        mock_response_unauthorized.status_code = requests.codes.unauthorized
        mock_response_unauthorized.reason = "Unauthorized"
        mock_response_unauthorized.text = "Invalid credentials"

        # Second call raises RequestException
        mock_api.post.side_effect = [mock_response_unauthorized, requests.RequestException("Network error")]

        with pytest.raises(SystemExit):
            get_token(
                api=mock_api,
                client_id="test_client",
                client_secret="test_secret",
                token_url=AUTH0_URLS[0],
            )

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_non_200_status_code_error(self, mock_api_class, mock_error_exit):
        """Test that non-200 status codes trigger error_and_exit"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error occurred"
        mock_api.post.return_value = mock_response

        with pytest.raises(SystemExit):
            get_token(
                api=mock_api,
                client_id="test_client",
                client_secret="test_secret",
                token_url=AUTH0_URLS[0],
            )

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "Error authenticating to Wiz" in error_message
        assert "500" in error_message

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_missing_access_token_in_response(self, mock_api_class, mock_error_exit):
        """Test error when access_token is missing from response"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {
            "scope": "read:all",
            "message": "Token generation failed",
        }
        mock_api.post.return_value = mock_response

        with pytest.raises(SystemExit):
            get_token(
                api=mock_api,
                client_id="test_client",
                client_secret="test_secret",
                token_url=AUTH0_URLS[0],
            )

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "Could not retrieve token from Wiz" in error_message

    @patch(f"{PATH}.Api")
    def test_response_with_null_scope(self, mock_api_class):
        """Test successful token retrieval when scope is None"""
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "scope": None,
        }
        mock_api.post.return_value = mock_response

        token, scope = get_token(
            api=mock_api,
            client_id="test_client",
            client_secret="test_secret",
            token_url=AUTH0_URLS[0],
        )

        assert token == "test_token_123"
        assert scope is None

    @patch(f"{PATH}.Api")
    def test_cognito_url_direct_success(self, mock_api_class):
        """Test successful authentication directly with Cognito URL"""
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": COGNITO_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {
            "access_token": "cognito_direct_token",
            "scope": "wiz-api full",
        }
        mock_api.post.return_value = mock_response

        token, scope = get_token(
            api=mock_api,
            client_id="cognito_client",
            client_secret="cognito_secret",
            token_url=COGNITO_URLS[0],
        )

        assert token == "cognito_direct_token"
        assert scope == "wiz-api full"


class TestWizAuthenticate:
    """Test the wiz_authenticate function"""

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_successful_authentication_with_env_variables(
        self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token
    ):
        """Test successful authentication using environment variables"""
        mock_app = MagicMock()
        mock_app.config = {
            "wizAuthUrl": AUTH0_URLS[0],
        }
        mock_app.save_config = MagicMock()
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        mock_get_token.return_value = ("test_token_789", "read:all write:all")

        token = wiz_authenticate()

        assert token == "test_token_789"
        mock_get_token.assert_called_once_with(
            api=mock_api,
            client_id="env_client_id",
            client_secret="env_client_secret",
            token_url=AUTH0_URLS[0],
        )
        mock_app.save_config.assert_called_once()
        saved_config = mock_app.save_config.call_args[0][0]
        assert saved_config["wizAccessToken"] == "test_token_789"
        assert saved_config["wizScope"] == "read:all write:all"

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_successful_authentication_with_cli_parameters(
        self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token
    ):
        """Test successful authentication using CLI-provided parameters"""
        mock_app = MagicMock()
        mock_app.config = {
            "wizAuthUrl": COGNITO_URLS[0],
        }
        mock_app.save_config = MagicMock()
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        mock_get_token.return_value = ("cli_token_999", "wiz-api")

        token = wiz_authenticate(client_id="cli_client_id", client_secret="cli_client_secret")

        assert token == "cli_token_999"
        mock_get_token.assert_called_once_with(
            api=mock_api,
            client_id="cli_client_id",
            client_secret="cli_client_secret",
            token_url=COGNITO_URLS[0],
        )

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_missing_client_id_error(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_error_exit):
        """Test error when client ID is missing"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = None
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        with pytest.raises(SystemExit):
            wiz_authenticate()

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "No Wiz Client ID provided" in error_message

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_missing_client_secret_error(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_error_exit):
        """Test error when client secret is missing"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = None

        with pytest.raises(SystemExit):
            wiz_authenticate()

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "No Wiz Client Secret provided" in error_message

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_missing_auth_url_error(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_error_exit):
        """Test error when wizAuthUrl is missing from config"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock()
        mock_app.config = {}
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        with pytest.raises(SystemExit):
            wiz_authenticate()

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "No Wiz Authentication URL provided" in error_message

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_empty_string_credentials_treated_as_missing(
        self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token
    ):
        """Test that empty string credentials are treated as missing"""
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        # Empty strings should be treated as falsy
        mock_wiz_vars.wizClientId = ""
        mock_wiz_vars.wizClientSecret = "valid_secret"

        # Since empty string client_id is provided via CLI, it should override env
        # But empty strings are falsy, so error should trigger
        from regscale.core.app.utils.app_utils import error_and_exit

        with patch(f"{PATH}.error_and_exit") as mock_error_exit:
            mock_error_exit.side_effect = SystemExit(1)

            with pytest.raises(SystemExit):
                wiz_authenticate(client_id="", client_secret="valid_secret")

            mock_error_exit.assert_called()

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_cli_parameters_override_environment_variables(
        self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token
    ):
        """Test that CLI parameters override environment variables"""
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_app.save_config = MagicMock()
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        mock_get_token.return_value = ("override_token", "override_scope")

        wiz_authenticate(client_id="cli_client_id", client_secret="cli_client_secret")

        # Verify CLI parameters were used, not env variables
        mock_get_token.assert_called_once_with(
            api=mock_api,
            client_id="cli_client_id",
            client_secret="cli_client_secret",
            token_url=AUTH0_URLS[0],
        )

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_token_and_scope_saved_to_config(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token):
        """Test that token and scope are properly saved to config"""
        mock_app = MagicMock()
        mock_app.config = {
            "wizAuthUrl": AUTH0_URLS[0],
            "existingKey": "existingValue",
        }
        mock_app.save_config = MagicMock()
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        mock_get_token.return_value = ("new_token_123", "full_scope")

        wiz_authenticate()

        mock_app.save_config.assert_called_once()
        saved_config = mock_app.save_config.call_args[0][0]
        assert saved_config["wizAccessToken"] == "new_token_123"
        assert saved_config["wizScope"] == "full_scope"
        assert saved_config["existingKey"] == "existingValue"
        assert saved_config["wizAuthUrl"] == AUTH0_URLS[0]

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_partial_cli_parameters(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token):
        """Test authentication with partial CLI parameters (only client_id)"""
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_app.save_config = MagicMock()
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "env_client_id"
        mock_wiz_vars.wizClientSecret = "env_client_secret"

        mock_get_token.return_value = ("partial_token", "partial_scope")

        wiz_authenticate(client_id="cli_client_id")

        # CLI client_id should be used, env client_secret should be used
        mock_get_token.assert_called_once_with(
            api=mock_api,
            client_id="cli_client_id",
            client_secret="env_client_secret",
            token_url=AUTH0_URLS[0],
        )


class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""

    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_complete_auth_flow_with_all_urls(self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token):
        """Test complete authentication flow with all supported URLs"""
        all_urls = AUTH0_URLS + COGNITO_URLS

        for url in all_urls:
            mock_app = MagicMock()
            mock_app.config = {"wizAuthUrl": url}
            mock_app.save_config = MagicMock()
            mock_check_license.return_value = mock_app

            mock_api = MagicMock()
            mock_api_class.return_value = mock_api

            mock_wiz_vars.wizClientId = "test_client"
            mock_wiz_vars.wizClientSecret = "test_secret"

            mock_get_token.return_value = (f"token_for_{url}", "scope")

            token = wiz_authenticate()

            assert token == f"token_for_{url}"
            mock_get_token.assert_called_with(
                api=mock_api,
                client_id="test_client",
                client_secret="test_secret",
                token_url=url,
            )

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.get_token")
    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_get_token_failure_propagates_to_wiz_authenticate(
        self, mock_check_license, mock_api_class, mock_wiz_vars, mock_get_token, mock_error_exit
    ):
        """Test that get_token failures properly propagate to wiz_authenticate"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock()
        mock_app.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_check_license.return_value = mock_app

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_wiz_vars.wizClientId = "test_client"
        mock_wiz_vars.wizClientSecret = "test_secret"

        mock_get_token.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            wiz_authenticate()


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_auth0_urls_list_not_empty(self):
        """Test that AUTH0_URLS is not empty"""
        assert len(AUTH0_URLS) > 0

    def test_cognito_urls_list_not_empty(self):
        """Test that COGNITO_URLS is not empty"""
        assert len(COGNITO_URLS) > 0

    def test_all_auth0_urls_are_unique(self):
        """Test that all Auth0 URLs are unique"""
        assert len(AUTH0_URLS) == len(set(AUTH0_URLS))

    def test_all_cognito_urls_are_unique(self):
        """Test that all Cognito URLs are unique"""
        assert len(COGNITO_URLS) == len(set(COGNITO_URLS))

    def test_no_url_overlap_between_auth0_and_cognito(self):
        """Test that Auth0 and Cognito URLs don't overlap"""
        auth0_set = set(AUTH0_URLS)
        cognito_set = set(COGNITO_URLS)
        assert len(auth0_set.intersection(cognito_set)) == 0

    def test_all_urls_are_strings(self):
        """Test that all URLs are strings"""
        for url in AUTH0_URLS + COGNITO_URLS:
            assert isinstance(url, str)

    def test_all_urls_are_https(self):
        """Test that all URLs use HTTPS"""
        for url in AUTH0_URLS + COGNITO_URLS:
            assert url.startswith("https://")

    @patch(f"{PATH}.Api")
    def test_get_token_handles_response_without_scope(self, mock_api_class):
        """Test get_token when response doesn't include scope key"""
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        # Response without scope key
        mock_response.json.return_value = {
            "access_token": "token_without_scope",
        }
        mock_api.post.return_value = mock_response

        token, scope = get_token(
            api=mock_api,
            client_id="test_client",
            client_secret="test_secret",
            token_url=AUTH0_URLS[0],
        )

        assert token == "token_without_scope"
        assert scope is None

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_token_handles_empty_json_response(self, mock_api_class, mock_error_exit):
        """Test get_token when response JSON is empty"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_api = MagicMock()
        mock_api.config = {"wizAuthUrl": AUTH0_URLS[0]}
        mock_api.app = MagicMock()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {}
        mock_api.post.return_value = mock_response

        with pytest.raises(SystemExit):
            get_token(
                api=mock_api,
                client_id="test_client",
                client_secret="test_secret",
                token_url=AUTH0_URLS[0],
            )

        mock_error_exit.assert_called_once()
