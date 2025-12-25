#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Microsoft Defender API integration"""
import json
from datetime import datetime
from json import JSONDecodeError
from unittest.mock import MagicMock, patch

import pytest
from pathlib import Path
from requests import Response

from regscale.integrations.commercial.microsoft_defender.defender_api import DefenderApi
from tests import CLITestFixture


class TestDefenderApi(CLITestFixture):
    PATH = "regscale.integrations.commercial.microsoft_defender.defender_api"
    cloud_token = "azureCloudAccessToken"
    cloud_tenant_id = "azureCloudTenantId"
    cloud_client_id = "azureCloudClientId"
    cloud_secret = "azureCloudSecret"
    cloud_subscription_id = "azureCloudSubscriptionId"
    azure_365_tenant_id = "azure365TenantId"
    azure_365_client_id = "azure365ClientId"
    azure_365_secret = "azure365Secret"
    azure_365_access_token = "azure365AccessToken"
    azure_entra_tenant_id = "azureEntraTenantId"
    azure_entra_client_id = "azureEntraClientId"
    azure_entra_secret = "azureEntraSecret"
    azure_entra_access_token = "azureEntraAccessToken"

    def setup_mock_api(self, mock_api):
        """Helper method to setup mock API with required Azure configuration"""
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "test-sub",
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        # Mock the post response for token retrieval during initialization
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_api.post.return_value = mock_token_response

        # Mock app.save_config to avoid config changes
        mock_api.app.save_config = MagicMock()

        return mock_api

    def test_init(self):
        """Test init file and config"""
        self.verify_config(
            [
                self.azure_365_tenant_id,
                self.azure_365_client_id,
                self.azure_365_secret,
                self.cloud_tenant_id,
                self.cloud_client_id,
                self.cloud_secret,
                self.cloud_subscription_id,
            ]
        )

    @patch(f"{PATH}.Api")
    def test_defender_api_init_365(self, mock_api_class):
        """Test DefenderApi initialization for 365"""
        mock_api = MagicMock()
        mock_api.config = self.config
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="365")

        assert defender_api.system == "365"
        assert defender_api.api == mock_api
        assert defender_api.decode_error == "JSON Decode error"
        assert defender_api.skip_token_key == "$skipToken"

    @patch(f"{PATH}.Api")
    def test_defender_api_init_cloud(self, mock_api_class):
        """Test DefenderApi initialization for cloud"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudAccessToken": "Bearer test-token",
            "azureCloudTenantId": "test-tenant",
            "azureCloudClientId": "test-client",
            "azureCloudSecret": "test-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        # Mock the post method for token operations
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"access_token": "test-token"}
        mock_api.post.return_value = mock_post_response

        defender_api = DefenderApi(system="cloud")

        assert defender_api.system == "cloud"
        assert defender_api.api == mock_api
        assert defender_api.config == mock_api.config

    @patch(f"{PATH}.Api")
    def test_set_headers(self, mock_api_class):
        """Test setting headers"""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="365")

        with patch.object(defender_api, "check_token", return_value="Bearer test-token"):
            headers = defender_api.set_headers()

            assert headers["Content-Type"] == "application/json"
            assert headers["Authorization"] == "Bearer test-token"

    @patch(f"{PATH}.Api")
    def test_get_token_365(self, mock_api_class):
        """Test getting token for Defender 365"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer existing-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="365")

        # Reset the post mock after initialization
        mock_api.post.reset_mock()

        with patch.object(defender_api, "_parse_and_save_token", return_value="Bearer test-access-token") as mock_parse:
            token = defender_api.get_token()

            expected_url = "https://login.windows.net/test-tenant/oauth2/token"
            expected_data = {
                "resource": "https://api.securitycenter.windows.com",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "grant_type": "client_credentials",
            }

            mock_api.post.assert_called_once_with(
                url=expected_url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=expected_data
            )
            mock_parse.assert_called_once_with(mock_response, "azure365AccessToken")
            assert token == "Bearer test-access-token"

    @patch(f"{PATH}.Api")
    def test_get_token_cloud(self, mock_api_class):
        """Test getting token for Defender for Cloud"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer existing-token",
            "azureCloudTenantId": "test-tenant",
            "azureCloudClientId": "test-client",
            "azureCloudSecret": "test-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        # Reset the post mock after initialization
        mock_api.post.reset_mock()

        with patch.object(defender_api, "_parse_and_save_token", return_value="Bearer test-access-token") as mock_parse:
            token = defender_api.get_token()

            expected_url = "https://login.microsoftonline.com/test-tenant/oauth2/token"
            expected_data = {
                "resource": "https://management.azure.com",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "grant_type": "client_credentials",
            }

            mock_api.post.assert_called_once_with(
                url=expected_url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=expected_data
            )
            mock_parse.assert_called_once_with(mock_response, "azureCloudAccessToken")
            assert token == "Bearer test-access-token"

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_token_key_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test get_token with KeyError"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer existing-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid_client"}
        mock_response.text = "Invalid client"
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="365")

        with patch.object(defender_api, "_parse_and_save_token", side_effect=KeyError("access_token")):
            defender_api.get_token()

            mock_error_exit.assert_called_once()
            args = mock_error_exit.call_args[0][0]
            assert "Didn't receive token from Azure" in args
            assert "Invalid client" in args

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_token_json_decode_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test get_token with JSONDecodeError"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer existing-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.text = "Invalid JSON"
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="365")

        with patch.object(defender_api, "_parse_and_save_token", side_effect=JSONDecodeError("msg", "doc", 0)):
            defender_api.get_token()

            mock_error_exit.assert_called_once()
            args = mock_error_exit.call_args[0][0]
            assert "Unable to authenticate with Azure" in args

    @patch(f"{PATH}.Api")
    def test_check_token_valid_cloud(self, mock_api_class):
        """Test checking valid token for cloud"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer valid-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_api.get.return_value = mock_response

        # Mock app.save_config to avoid changes to the config
        mock_api.app.save_config = MagicMock()

        defender_api = DefenderApi(system="cloud")

        # Ensure config retains the expected value for the token test
        defender_api.config["azureCloudAccessToken"] = "Bearer valid-token"

        token = defender_api.check_token(url="https://test.com")

        assert token == "Bearer valid-token"

    @patch(f"{PATH}.Api")
    def test_check_token_valid_365(self, mock_api_class):
        """Test checking valid token for 365"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer valid-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
        }
        mock_api_class.return_value = mock_api

        # Mock the response for the token validation check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_api.get.return_value = mock_response

        # Mock the post method for potential token refresh (shouldn't be called)
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"access_token": "new-token"}
        mock_api.post.return_value = mock_post_response

        defender_api = DefenderApi(system="365")

        # Reset the config after initialization to ensure we use the expected token
        defender_api.config["azure365AccessToken"] = "Bearer valid-token"

        token = defender_api.check_token(url="https://test.com")

        assert token == "Bearer valid-token"

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_check_token_permission_error(self, mock_api_class, mock_error_exit):
        """Test checking token with permission error"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudAccessToken": "Bearer invalid-token",
            "azureCloudTenantId": "test-tenant",
            "azureCloudClientId": "test-client",
            "azureCloudSecret": "test-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        mock_response.text = "Access denied"
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.check_token(url="https://test.com")

        mock_error_exit.assert_called_once()
        args = mock_error_exit.call_args[0][0]
        assert "Incorrect permissions" in args

    @patch(f"{PATH}.Api")
    def test_check_token_invalid_need_refresh(self, mock_api_class):
        """Test checking invalid token that needs refresh"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudAccessToken": "Bearer expired-token",
            "azureCloudTenantId": "test-tenant",
            "azureCloudClientId": "test-client",
            "azureCloudSecret": "test-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        with patch.object(defender_api, "get_token", return_value="Bearer new-token") as mock_get_token:
            token = defender_api.check_token(url="https://test.com")

            mock_get_token.assert_called_once()
            assert token == "Bearer new-token"

    @patch(f"{PATH}.Api")
    def test_check_token_empty_get_new(self, mock_api_class):
        """Test checking empty token - should get new one"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudAccessToken": "",
            "azureCloudTenantId": "test-tenant",
            "azureCloudClientId": "test-client",
            "azureCloudSecret": "test-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="cloud")

        with patch.object(defender_api, "get_token", return_value="Bearer new-token") as mock_get_token:
            token = defender_api.check_token()

            mock_get_token.assert_called_once()
            assert token == "Bearer new-token"

    @patch(f"{PATH}.error_and_exit")
    def test_check_token_unsupported_system(self, mock_error_exit):
        """Test checking token with unsupported system"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        with patch(f"{self.PATH}.Api") as mock_api_class:
            mock_api = MagicMock()
            mock_api.config = {
                "azure365AccessToken": "Bearer 365-token",
                "azure365TenantId": "365-tenant",
                "azure365ClientId": "365-client",
                "azure365Secret": "365-secret",
                "azureCloudAccessToken": "Bearer cloud-token",
                "azureCloudTenantId": "cloud-tenant",
                "azureCloudClientId": "cloud-client",
                "azureCloudSecret": "cloud-secret",
                "azureCloudSubscriptionId": "cloud-sub",
            }
            mock_api_class.return_value = mock_api

            # Use a proper type annotation bypass for the test
            defender_api = DefenderApi.__new__(DefenderApi)
            defender_api.system = "unsupported"  # type: ignore
            defender_api.api = mock_api
            defender_api.config = mock_api.config

            # This should raise SystemExit due to error_and_exit being called
            with pytest.raises(SystemExit):
                defender_api.check_token(url="https://test.com")

            mock_error_exit.assert_called_once()
            args = mock_error_exit.call_args[0][0]
            assert "Unsupported is not supported" in args

    @patch(f"{PATH}.Api")
    def test_parse_and_save_token(self, mock_api_class):
        """Test parsing and saving token"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api.app.save_config = MagicMock()
        mock_api_class.return_value = mock_api

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-token"}

        defender_api = DefenderApi(system="365")

        token = defender_api._parse_and_save_token(response=mock_response, key="testKey")

        assert token == "Bearer test-token"
        assert mock_api.config["testKey"] == "Bearer test-token"
        # save_config should be called at least once (during initialization and potentially during test)
        assert mock_api.app.save_config.call_count >= 1

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_execute_resource_graph_query_error_response(self, mock_api_class, mock_error_exit):
        """Test execute_resource_graph_query with error response"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid query"
        mock_api.post.return_value = mock_response

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        defender_api.execute_resource_graph_query(query="invalid query")

        mock_error_exit.assert_called_once()
        args = mock_error_exit.call_args[0][0]
        assert "Received unexpected response" in args

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.Api")
    def test_execute_resource_graph_query_success(self, mock_api_class, mock_set_headers):
        """Test execute_resource_graph_query with successful response"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {"azureCloudSubscriptionId": "test-sub"}
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "resource1"}, {"id": "resource2"}],
            "totalRecords": 2,
            "count": 2,
        }
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        result = defender_api.execute_resource_graph_query(query="resources | limit 10")

        assert len(result) == 2
        assert result[0]["id"] == "resource1"
        assert result[1]["id"] == "resource2"

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.Api")
    def test_execute_resource_graph_query_with_pagination(self, mock_api_class, mock_set_headers):
        """Test execute_resource_graph_query with pagination"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {"azureCloudSubscriptionId": "test-sub"}
        mock_api_class.return_value = mock_api

        # First response with skip token
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "data": [{"id": "resource1"}],
            "totalRecords": 2,
            "count": 1,
            "$skipToken": "skip-token-123",
        }

        # Second response without skip token
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"data": [{"id": "resource2"}], "totalRecords": 2, "count": 1}

        mock_api.post.side_effect = [mock_response1, mock_response2]

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        result = defender_api.execute_resource_graph_query(query="resources")

        assert len(result) == 2
        assert result[0]["id"] == "resource1"
        assert result[1]["id"] == "resource2"
        assert mock_api.post.call_count == 2

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_execute_resource_graph_query_json_decode_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test execute_resource_graph_query with JSON decode error"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {"azureCloudSubscriptionId": "test-sub"}
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.execute_resource_graph_query(query="resources")

        mock_error_exit.assert_called_once_with("JSON Decode error")

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_execute_resource_graph_query_key_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test execute_resource_graph_query with KeyError"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {"azureCloudSubscriptionId": "test-sub"}
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.text = "Missing data field"
        mock_response.json.return_value = {"error": "missing data"}
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.execute_resource_graph_query(query="resources")

        mock_error_exit.assert_called_once()
        args = mock_error_exit.call_args[0][0]
        assert "Received unexpected response" in args

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_items_from_azure_error_response(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test get_items_from_azure with error response"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {}
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Server error"
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="365")
        defender_api.headers = {"Authorization": "Bearer test"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.get_items_from_azure(url="https://test.com")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.Api")
    def test_get_items_from_azure_success(self, mock_api_class, mock_set_headers):
        """Test get_items_from_azure with successful response"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer existing-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        # Mock response without nextLink to avoid infinite recursion
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "value": [{"id": "item1"}, {"id": "item2"}]
            # No nextLink to avoid pagination recursion
        }
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="365")

        result = defender_api.get_items_from_azure(url="https://test.com")

        assert len(result) == 2
        assert result[0]["id"] == "item1"
        assert result[1]["id"] == "item2"

    @patch(f"{PATH}.Api")
    def test_get_items_from_azure_with_pagination(self, mock_api_class):
        """Test get_items_from_azure with pagination"""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        # First response with next link
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"value": [{"id": "item1"}], "nextLink": "https://test.com?skip=1"}

        # Second response without next link
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"value": [{"id": "item2"}]}

        mock_api.get.side_effect = [mock_response1, mock_response2]

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        defender_api = DefenderApi(system="365")
        defender_api.headers = {"Authorization": "Bearer test"}

        result = defender_api.get_items_from_azure(url="https://test.com")

        assert len(result) == 2
        assert result[0]["id"] == "item1"
        assert result[1]["id"] == "item2"

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_items_from_azure_json_decode_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test get_items_from_azure with JSON decode error"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)

        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {}
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("msg", "doc", 0)
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="365")
        defender_api.headers = {"Authorization": "Bearer test"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.get_items_from_azure(url="https://test.com")

        mock_error_exit.assert_called_once_with("JSON Decode error")

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_items_from_azure_key_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test get_items_from_azure with KeyError"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer existing-token",
            "azure365TenantId": "test-tenant",
            "azure365ClientId": "test-client",
            "azure365Secret": "test-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        # Mock response that will cause KeyError - missing "value" key
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Missing value field"
        mock_response.json.return_value = {"error": "missing value"}  # No "value" key
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="365")
        defender_api.headers = {"Authorization": "Bearer test"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.get_items_from_azure(url="https://test.com")

        mock_error_exit.assert_called_once()
        args = mock_error_exit.call_args[0][0]
        assert "Received unexpected response" in args

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.Api")
    def test_fetch_queries_from_azure_success(self, mock_api_class, mock_set_headers):
        """Test fetching queries from Azure successfully"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudSubscriptionId": "test-sub",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None  # Success case
        mock_response.json.return_value = {"value": [{"name": "Query1", "id": "1"}, {"name": "Query2", "id": "2"}]}
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        result = defender_api.fetch_queries_from_azure()

        assert len(result) == 2
        assert result[0]["name"] == "Query1"
        assert result[1]["name"] == "Query2"

        expected_url = (
            "https://management.azure.com/subscriptions/test-sub/"
            "providers/Microsoft.ResourceGraph/queries?api-version=2024-04-01"
        )
        mock_api.get.assert_called_with(
            url=expected_url, headers={"Content-Type": "application/json", "Authorization": "Bearer test"}
        )

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_fetch_queries_from_azure_error(self, mock_api_class, mock_error_exit):
        """Test fetching queries from Azure with error"""
        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid request"
        mock_response.raise_for_status.return_value = True  # Indicates error
        mock_api.get.return_value = mock_response

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        defender_api = DefenderApi(system="cloud")
        defender_api.headers = {"Authorization": "Bearer test"}

        defender_api.fetch_queries_from_azure()

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.Api")
    def test_fetch_and_run_query_success(self, mock_api_class, mock_set_headers):
        """Test fetching and running query successfully"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "cloud-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None  # Success case
        mock_response.json.return_value = {"properties": {"query": "resources | limit 10"}}
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        # Mock the execute_resource_graph_query method
        with patch.object(
            defender_api, "execute_resource_graph_query", return_value=[{"id": "resource1"}]
        ) as mock_execute:
            query = {"subscriptionId": "test-sub", "resourceGroup": "test-rg", "name": "test-query"}

            result = defender_api.fetch_and_run_query(query=query)

            expected_url = (
                "https://management.azure.com/subscriptions/test-sub/resourceGroups/"
                "test-rg/providers/Microsoft.ResourceGraph/queries/test-query"
                "?api-version=2024-04-01"
            )
            mock_api.get.assert_called_once_with(
                url=expected_url, headers={"Content-Type": "application/json", "Authorization": "Bearer test"}
            )
            mock_execute.assert_called_once_with(query="resources | limit 10")
            assert len(result) == 1
            assert result[0]["id"] == "resource1"

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_fetch_and_run_query_error(self, mock_api_class, mock_error_exit, mock_set_headers):
        """Test fetching and running query with error"""
        # Make error_and_exit raise SystemExit to properly simulate exit behavior
        mock_error_exit.side_effect = SystemExit(1)
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}

        mock_api = MagicMock()
        mock_api.config = {
            "azure365AccessToken": "Bearer 365-token",
            "azure365TenantId": "365-tenant",
            "azure365ClientId": "365-client",
            "azure365Secret": "365-secret",
            "azureCloudAccessToken": "Bearer cloud-token",
            "azureCloudTenantId": "cloud-tenant",
            "azureCloudClientId": "cloud-client",
            "azureCloudSecret": "cloud-secret",
            "azureCloudSubscriptionId": "test-sub",
        }
        mock_api_class.return_value = mock_api

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Query not found"
        mock_response.raise_for_status.return_value = True  # Error case
        mock_api.get.return_value = mock_response

        defender_api = DefenderApi(system="cloud")

        query = {"subscriptionId": "test-sub", "resourceGroup": "test-rg", "name": "nonexistent-query"}

        # This should raise SystemExit due to error_and_exit being called
        with pytest.raises(SystemExit):
            defender_api.fetch_and_run_query(query=query)

        # Should be called exactly once for the query fetch error
        assert mock_error_exit.call_count == 1
        args = mock_error_exit.call_args[0][0]
        assert "Received unexpected response" in args

    # ==============================
    # NEW TESTS FOR ENTRA FUNCTIONALITY
    # ==============================

    @patch(f"{PATH}.Api")
    def test_defender_api_init_entra(self, mock_api_class):
        """Test DefenderApi initialization for entra"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        # Mock the post method for token operations
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"access_token": "test-token"}
        mock_api.post.return_value = mock_post_response

        defender_api = DefenderApi(system="entra")

        assert defender_api.system == "entra"
        assert defender_api.api == mock_api
        assert defender_api.config == mock_api.config

    @patch(f"{PATH}.Api")
    def test_get_token_entra(self, mock_api_class):
        """Test getting token for Azure Entra"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer existing-token",
            "azureEntraTenantId": "test-tenant",
            "azureEntraClientId": "test-client",
            "azureEntraSecret": "test-secret",
        }
        mock_api_class.return_value = mock_api

        # Mock the initial get call for check_token to return 200 (valid token)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_api.get.return_value = mock_get_response

        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_api.post.return_value = mock_response

        defender_api = DefenderApi(system="entra")

        # Reset the post mock after initialization
        mock_api.post.reset_mock()

        with patch.object(defender_api, "_parse_and_save_token", return_value="Bearer test-access-token") as mock_parse:
            token = defender_api.get_token()

            expected_url = "https://login.microsoftonline.com/test-tenant/oauth2/v2.0/token"
            expected_data = {
                "scope": "https://graph.microsoft.com/.default",
                "client_id": "test-client",
                "client_secret": "test-secret",
                "grant_type": "client_credentials",
            }

            mock_api.post.assert_called_once_with(
                url=expected_url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=expected_data
            )
            mock_parse.assert_called_once_with(mock_response, "azureEntraAccessToken")
            assert token == "Bearer test-access-token"

    @patch(f"{PATH}.Api")
    def test_check_token_valid_entra(self, mock_api_class):
        """Test checking valid token for entra"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer valid-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        # Mock the response for the token validation check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_api.get.return_value = mock_response

        # Mock the post method for potential token refresh (shouldn't be called)
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"access_token": "new-token"}
        mock_api.post.return_value = mock_post_response

        defender_api = DefenderApi(system="entra")

        # Reset the config after initialization to ensure we use the expected token
        defender_api.config["azureEntraAccessToken"] = "Bearer valid-token"

        token = defender_api.check_token(url="https://test.com")

        assert token == "Bearer valid-token"

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_success(
        self, mock_api_class, mock_check_file_path, mock_save_data, mock_get_datetime, mock_set_headers
    ):
        """Test get_and_save_entra_evidence with successful response"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}
        mock_get_datetime.return_value = "20230101"

        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock get_items_from_azure
        with patch.object(
            defender_api, "get_items_from_azure", return_value=[{"id": "user1", "displayName": "Test User"}]
        ) as mock_get_items:
            result = defender_api.get_and_save_entra_evidence("users")

            # Verify the correct endpoint was called
            expected_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,userPrincipalName,accountEnabled,userType,createdDateTime&$top=999"
            mock_get_items.assert_called_once_with(url=expected_url, parse_value=True)

            # Verify save_data_to was called
            mock_save_data.assert_called_once()

            # Verify result is a list of paths
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Path)

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_wrong_system(self, mock_api_class, mock_error_exit):
        """Test get_and_save_entra_evidence with wrong system"""
        mock_error_exit.side_effect = SystemExit(1)

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="365")

        with pytest.raises(SystemExit):
            defender_api.get_and_save_entra_evidence("users")

        mock_error_exit.assert_called_once_with("This method can only be used with system='entra'")

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_unknown_endpoint(self, mock_api_class, mock_error_exit):
        """Test get_and_save_entra_evidence with unknown endpoint"""
        mock_error_exit.side_effect = SystemExit(1)

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        with pytest.raises(SystemExit):
            defender_api.get_and_save_entra_evidence("invalid_endpoint")

        mock_error_exit.assert_called_once_with("Unknown endpoint key: invalid_endpoint")

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_with_parameters(
        self, mock_api_class, mock_check_file_path, mock_save_data, mock_get_datetime, mock_set_headers
    ):
        """Test get_and_save_entra_evidence with URL parameters"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}
        mock_get_datetime.return_value = "20230101"

        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock get_items_from_azure
        with patch.object(
            defender_api, "get_items_from_azure", return_value=[{"id": "log1", "activityDateTime": "2023-01-01"}]
        ) as mock_get_items:
            result = defender_api.get_and_save_entra_evidence("sign_in_logs", start_date="2023-01-01T00:00:00Z")

            # Verify the correct endpoint was called with parameters
            expected_url = "https://graph.microsoft.com/v1.0/auditLogs/signIns?$filter=createdDateTime ge 2023-01-01T00:00:00Z&$top=1000"
            mock_get_items.assert_called_once_with(url=expected_url, parse_value=True)

            assert len(result) == 1

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_missing_required_param(self, mock_api_class, mock_error_exit):
        """Test get_and_save_entra_evidence with missing required parameter"""
        mock_error_exit.side_effect = SystemExit(1)

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        with pytest.raises(SystemExit):
            defender_api.get_and_save_entra_evidence("access_review_instances")

        mock_error_exit.assert_called_once_with("def_id parameter is required for this endpoint")

    @patch(f"{PATH}.DefenderApi.get_and_save_entra_evidence")
    @patch(f"{PATH}.DefenderApi.collect_entra_access_reviews")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_collect_all_entra_evidence_success(
        self, mock_api_class, mock_check_file_path, mock_collect_access_reviews, mock_get_and_save_evidence
    ):
        """Test collect_all_entra_evidence with successful response"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock return values
        mock_get_and_save_evidence.return_value = [Path("/test/path.csv")]
        mock_collect_access_reviews.return_value = [Path("/test/access_reviews.csv")]

        result = defender_api.collect_all_entra_evidence(days_back=30)

        # Verify all expected evidence types are in the result
        expected_keys = [
            "users",
            "users_delta",
            "guest_users",
            "groups_and_members",
            "security_groups",
            "role_assignments",
            "role_definitions",
            "pim_assignments",
            "pim_eligibility",
            "conditional_access",
            "auth_methods_policy",
            "user_mfa_registration",
            "mfa_registered_users",
            "sign_in_logs",
            "directory_audits",
            "provisioning_logs",
            "access_review_definitions",
        ]
        for key in expected_keys:
            assert key in result

        # Verify check_file_path was called
        mock_check_file_path.assert_called_once()

    @patch(f"{PATH}.DefenderApi.get_and_save_entra_evidence")
    @patch(f"{PATH}.DefenderApi.collect_entra_access_reviews")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_collect_all_entra_evidence_with_exceptions(
        self, mock_api_class, mock_check_file_path, mock_collect_access_reviews, mock_get_and_save_evidence
    ):
        """Test collect_all_entra_evidence handles exceptions gracefully"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Make get_and_save_entra_evidence raise an exception for some calls
        def side_effect(endpoint_key, **kwargs):
            if endpoint_key in ["users", "sign_in_logs"]:
                raise Exception("API Error")
            return [Path("/test/path.csv")]

        mock_get_and_save_evidence.side_effect = side_effect
        mock_collect_access_reviews.return_value = [Path("/test/access_reviews.csv")]

        result = defender_api.collect_all_entra_evidence(days_back=30)

        # Verify that failed evidence types return empty lists
        assert result["users"] == []
        assert result["sign_in_logs"] == []
        # Verify that the method was called and completed (even with exceptions)
        assert "guest_users" in result
        assert "access_review_definitions" in result
        mock_collect_access_reviews.assert_called_once()

    @patch(f"{PATH}.DefenderApi.get_items_from_azure")
    @patch(f"{PATH}.DefenderApi._flatten_access_review_definition")
    @patch(f"{PATH}.DefenderApi._flatten_access_review_instance")
    @patch(f"{PATH}.DefenderApi._flatten_access_review_decision")
    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.Api")
    def test_collect_entra_access_reviews_success(
        self,
        mock_api_class,
        mock_get_datetime,
        mock_save_data,
        mock_flatten_decision,
        mock_flatten_instance,
        mock_flatten_definition,
        mock_get_items,
    ):
        """Test collect_entra_access_reviews with successful response"""
        mock_get_datetime.return_value = "2023-01-01"
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock data
        mock_definition = {"id": "def1", "displayName": "Test Review"}
        mock_instance = {"id": "inst1", "status": "InProgress"}
        mock_decision = {"id": "dec1", "decision": "Approve"}

        # Setup return values
        mock_get_items.side_effect = [
            [mock_definition],  # definitions
            [mock_instance],  # instances
            [mock_decision],  # decisions
        ]
        mock_flatten_definition.return_value = {"flattened": "definition"}
        mock_flatten_instance.return_value = {"flattened": "instance"}
        mock_flatten_decision.return_value = {"flattened": "decision"}

        result = defender_api.collect_entra_access_reviews()

        # Verify calls were made
        assert mock_get_items.call_count == 3
        mock_flatten_definition.assert_called_once_with(mock_definition)
        mock_flatten_instance.assert_called_once_with("def1", mock_instance)
        mock_flatten_decision.assert_called_once_with("def1", "inst1", mock_decision)

        # Verify save_data_to was called for all three types
        assert mock_save_data.call_count == 3

        # Verify result is a list of paths
        assert isinstance(result, list)
        assert len(result) == 3

    def test_flatten_access_review_definition(self):
        """Test _flatten_access_review_definition static method"""
        definition = {
            "id": "def-123",
            "displayName": "Test Review",
            "status": "Active",
            "createdDateTime": "2023-01-01T00:00:00Z",
            "createdBy": {"displayName": "Admin", "id": "user1", "userPrincipalName": "admin@test.com"},
            "scope": {"@odata.type": "test-type", "query": "test-query"},
            "settings": {
                "defaultDecision": "Approve",
                "autoApplyDecisionsEnabled": True,
                "instanceDurationInDays": 30,
                "recurrence": {"pattern": {"type": "weekly", "interval": 1}},
            },
        }

        result = DefenderApi._flatten_access_review_definition(definition)

        assert result["id"] == "def-123"
        assert result["displayName"] == "Test Review"
        assert result["status"] == "Active"
        assert result["createdBy_displayName"] == "Admin"
        assert result["scope_type"] == "test-type"
        assert result["settings_defaultDecision"] == "Approve"
        assert result["settings_recurrence_type"] == "weekly"
        assert result["settings_recurrence_interval"] == 1

    def test_flatten_access_review_instance(self):
        """Test _flatten_access_review_instance static method"""
        instance = {
            "id": "inst-123",
            "status": "InProgress",
            "startDateTime": "2023-01-01T00:00:00Z",
            "endDateTime": "2023-01-31T23:59:59Z",
            "scope": {"@odata.type": "instance-type"},
            "reviewers": [{"id": "rev1"}, {"id": "rev2"}],
            "fallbackReviewers": [{"id": "fallback1"}],
        }

        result = DefenderApi._flatten_access_review_instance("def-123", instance)

        assert result["definition_id"] == "def-123"
        assert result["id"] == "inst-123"
        assert result["status"] == "InProgress"
        assert result["startDateTime"] == "2023-01-01T00:00:00Z"
        assert result["reviewers_count"] == 2
        assert result["fallbackReviewers_count"] == 1

    def test_flatten_access_review_decision(self):
        """Test _flatten_access_review_decision static method"""
        decision = {
            "id": "dec-123",
            "decision": "Approve",
            "recommendation": "Deny",
            "justification": "Test justification",
            "reviewedBy": {"id": "reviewer1", "displayName": "Reviewer", "userPrincipalName": "reviewer@test.com"},
            "target": {"@odata.type": "target-type", "userId": "target-user", "userDisplayName": "Target User"},
            "principal": {"@odata.type": "principal-type", "id": "principal1", "displayName": "Principal"},
        }

        result = DefenderApi._flatten_access_review_decision("def-123", "inst-123", decision)

        assert result["definition_id"] == "def-123"
        assert result["instance_id"] == "inst-123"
        assert result["decision_id"] == "dec-123"
        assert result["decision"] == "Approve"
        assert result["reviewedBy_displayName"] == "Reviewer"
        assert result["target_type"] == "target-type"
        assert result["principal_id"] == "principal1"

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_required_group_id_missing(self, mock_api_class, mock_error_exit):
        """Test get_and_save_entra_evidence with missing group_id parameter"""
        mock_error_exit.side_effect = SystemExit(1)

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        with pytest.raises(SystemExit):
            defender_api.get_and_save_entra_evidence("access_review_decisions")

        mock_error_exit.assert_called_once_with("def_id parameter is required for this endpoint")

    @patch(f"{PATH}.DefenderApi.set_headers")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_get_and_save_entra_evidence_parse_value_false(
        self, mock_api_class, mock_check_file_path, mock_save_data, mock_get_datetime, mock_set_headers
    ):
        """Test get_and_save_entra_evidence with parse_value=False"""
        mock_set_headers.return_value = {"Content-Type": "application/json", "Authorization": "Bearer test"}
        mock_get_datetime.return_value = "20230101"

        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock get_items_from_azure
        with patch.object(defender_api, "get_items_from_azure", return_value={"policy": "data"}) as mock_get_items:
            result = defender_api.get_and_save_entra_evidence("auth_methods_policy", parse_value=False)

            # Verify parse_value=False was passed
            mock_get_items.assert_called_once_with(
                url="https://graph.microsoft.com/v1.0/policies/authenticationMethodsPolicy", parse_value=False
            )

            assert len(result) == 1

    @patch(f"{PATH}.DefenderApi.collect_entra_access_reviews")
    @patch(f"{PATH}.DefenderApi.get_and_save_entra_evidence")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_collect_all_entra_evidence_custom_days_back(
        self, mock_api_class, mock_check_file_path, mock_get_and_save_evidence, mock_collect_access_reviews
    ):
        """Test collect_all_entra_evidence with custom days_back parameter"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock return values
        mock_get_and_save_evidence.return_value = [Path("/test/path.csv")]
        mock_collect_access_reviews.return_value = [Path("/test/access_reviews.csv")]

        result = defender_api.collect_all_entra_evidence(days_back=60)
        assert result

        # Verify that start_date was calculated correctly for 60 days back
        calls_with_start_date = [
            call
            for call in mock_get_and_save_evidence.call_args_list
            if len(call.kwargs) > 0 and "start_date" in call.kwargs
        ]

        # Should have 3 calls with start_date (sign_in_logs, directory_audits, provisioning_logs)
        assert len(calls_with_start_date) == 3

        # Verify the date format is correct (should be 60 days back)
        for call in calls_with_start_date:
            start_date = call.kwargs["start_date"]
            assert start_date.endswith("T00:00:00Z")
            # Should be a valid date format
            datetime.strptime(start_date.replace("T00:00:00Z", ""), "%Y-%m-%d")

    @patch(f"{PATH}.DefenderApi.collect_entra_access_reviews")
    @patch(f"{PATH}.DefenderApi.get_and_save_entra_evidence")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.Api")
    def test_collect_all_entra_evidence_partial_failure_recovery(
        self, mock_api_class, mock_check_file_path, mock_get_and_save_evidence, mock_collect_access_reviews
    ):
        """Test collect_all_entra_evidence handles partial failures and continues processing"""
        mock_api = MagicMock()
        mock_api.config = {
            "azureEntraAccessToken": "Bearer entra-token",
            "azureEntraTenantId": "entra-tenant",
            "azureEntraClientId": "entra-client",
            "azureEntraSecret": "entra-secret",
        }
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock different failure scenarios
        def side_effect(endpoint_key, **kwargs):
            if endpoint_key in ["users", "role_assignments", "auth_methods_policy"]:
                raise Exception(f"API Error for {endpoint_key}")
            return [Path(f"/test/{endpoint_key}.csv")]

        mock_get_and_save_evidence.side_effect = side_effect
        mock_collect_access_reviews.side_effect = Exception("Access reviews API error")

        result = defender_api.collect_all_entra_evidence(days_back=30)

        # Verify that failed evidence types return empty lists (grouped by category)
        # Users group failure affects all user-related evidence
        assert result["users"] == []
        assert result["users_delta"] == []
        assert result["guest_users"] == []
        assert result["groups_and_members"] == []
        assert result["security_groups"] == []

        # RBAC/PIM group failure affects all RBAC-related evidence
        assert result["role_assignments"] == []
        assert result["role_definitions"] == []
        assert result["pim_assignments"] == []
        assert result["pim_eligibility"] == []

        # Auth methods group failure affects all auth-related evidence
        assert result["auth_methods_policy"] == []
        assert result["user_mfa_registration"] == []
        assert result["mfa_registered_users"] == []

        # Access reviews failure
        assert result["access_review_definitions"] == []

        # Verify that successful evidence types have data
        assert len(result["conditional_access"]) == 1
        assert len(result["sign_in_logs"]) == 1
        assert len(result["directory_audits"]) == 1

        # Verify that all expected keys are present
        expected_keys = [
            "users",
            "users_delta",
            "guest_users",
            "groups_and_members",
            "security_groups",
            "role_assignments",
            "role_definitions",
            "pim_assignments",
            "pim_eligibility",
            "conditional_access",
            "auth_methods_policy",
            "user_mfa_registration",
            "mfa_registered_users",
            "sign_in_logs",
            "directory_audits",
            "provisioning_logs",
            "access_review_definitions",
        ]
        for key in expected_keys:
            assert key in result

    @patch(f"{PATH}.DefenderApi.get_items_from_azure")
    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.Api")
    def test_collect_entra_access_reviews_multiple_definitions(
        self, mock_api_class, mock_get_datetime, mock_save_data, mock_get_items
    ):
        """Test collect_entra_access_reviews with multiple access review definitions"""
        mock_get_datetime.return_value = "2023-01-01"
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock multiple definitions with different scenarios
        mock_definitions = [
            {"id": "def1", "displayName": "Review 1"},
            {"id": "def2", "displayName": "Review/With/Slashes"},
            {"id": "def3", "displayName": "Review With Spaces"},
        ]
        mock_instances = [{"id": "inst1", "status": "InProgress"}, {"id": "inst2", "status": "Completed"}]
        mock_decisions = [{"id": "dec1", "decision": "Approve"}, {"id": "dec2", "decision": "Deny"}]

        # Setup return values for each definition
        mock_get_items.side_effect = [
            mock_definitions,  # definitions call
            # For def1
            mock_instances,  # instances call
            mock_decisions,  # decisions call for inst1
            mock_decisions,  # decisions call for inst2
            # For def2
            mock_instances,  # instances call
            mock_decisions,  # decisions call for inst1
            mock_decisions,  # decisions call for inst2
            # For def3
            mock_instances,  # instances call
            mock_decisions,  # decisions call for inst1
            mock_decisions,  # decisions call for inst2
        ]

        result = defender_api.collect_entra_access_reviews()

        # Verify the correct number of API calls were made
        # 1 for definitions + 3 instances + 6 decisions (2 per definition) = 10 calls
        assert mock_get_items.call_count == 10

        # Verify save_data_to was called for each definition (3 definitions * 3 file types each)
        assert mock_save_data.call_count == 9

        # Verify result contains all file paths (3 definitions * 3 files each)
        assert len(result) == 9

        # Verify all results are Path objects
        for file_path in result:
            assert isinstance(file_path, Path)

    @patch(f"{PATH}.Api")
    def test_collect_entra_access_reviews_empty_definitions(self, mock_api_class):
        """Test collect_entra_access_reviews with no access review definitions"""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        defender_api = DefenderApi(system="entra")

        # Mock get_items_from_azure to return empty list
        with patch.object(defender_api, "get_items_from_azure", return_value=[]) as mock_get_items:
            result = defender_api.collect_entra_access_reviews()

            # Should only call once for definitions
            mock_get_items.assert_called_once()

            # Should return empty list
            assert result == []

    def test_flatten_access_review_definition_with_missing_fields(self):
        """Test _flatten_access_review_definition with missing optional fields"""
        definition = {
            "id": "def-123",
            "displayName": "Test Review",
            "status": "Active",
            # Missing most optional fields
        }

        result = DefenderApi._flatten_access_review_definition(definition)

        # Verify required fields are present
        assert result["id"] == "def-123"
        assert result["displayName"] == "Test Review"
        assert result["status"] == "Active"

        # Verify missing fields are handled gracefully (should be None)
        assert result["createdDateTime"] is None
        assert result["createdBy_displayName"] is None
        assert result["scope_type"] is None
        assert result["settings_defaultDecision"] is None

    def test_flatten_access_review_instance_with_minimal_data(self):
        """Test _flatten_access_review_instance with minimal required data"""
        instance = {
            "id": "inst-123",
            "status": "InProgress",
            # Missing most optional fields
        }

        result = DefenderApi._flatten_access_review_instance("def-123", instance)

        assert result["definition_id"] == "def-123"
        assert result["id"] == "inst-123"
        assert result["status"] == "InProgress"

        # Missing fields should be handled gracefully
        assert result["startDateTime"] is None
        assert result["reviewers_count"] == 0  # Empty list length
        assert result["fallbackReviewers_count"] == 0

    def test_flatten_access_review_decision_with_minimal_data(self):
        """Test _flatten_access_review_decision with minimal required data"""
        decision = {
            "id": "dec-123",
            "decision": "Approve",
            # Missing most optional fields
        }

        result = DefenderApi._flatten_access_review_decision("def-123", "inst-123", decision)

        assert result["definition_id"] == "def-123"
        assert result["instance_id"] == "inst-123"
        assert result["decision_id"] == "dec-123"
        assert result["decision"] == "Approve"

        # Missing fields should be handled gracefully
        assert result["reviewedBy_displayName"] is None
        assert result["target_type"] is None
        assert result["principal_id"] is None
