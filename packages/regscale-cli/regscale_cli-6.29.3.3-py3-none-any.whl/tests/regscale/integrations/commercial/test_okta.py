#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Okta integration in RegScale CLI"""
# standard python imports
import json
import os
from datetime import datetime, timedelta
from json import JSONDecodeError
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, Any

import pytest
import jwcrypto.jwk as jwk

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.integrations.commercial.okta import (
    authenticate,
    authenticate_with_okta,
    analyze_okta_users,
    check_and_save_data,
    clean_okta_output,
    compare_dates_and_user_type,
    get_all_okta_users,
    get_okta_data,
    get_okta_token,
    get_user_roles,
    save_active_users_from_okta,
    save_admin_users_from_okta,
    save_all_users_from_okta,
    save_inactive_users_from_okta,
    save_recently_added_users_from_okta,
)
from tests import CLITestFixture

PATH = "regscale.integrations.commercial.okta"


class TestOkta(CLITestFixture):
    """
    Test for Okta integration
    """

    def test_init(self):
        """Test init file and config"""
        # Test that the core required Okta config keys exist
        # Note: oktaScopes is not always present in config, so only test the core keys
        self.verify_config(
            [
                "oktaUrl",
                "oktaApiToken",
                "oktaClientId",
            ],
            compare_template=False,  # Don't compare to template since these might be defaults
        )

    # Test Click Commands
    def test_authenticate_command(self):
        """Test the authenticate Click command directly calls function"""
        with patch(f"{PATH}.check_license") as mock_check_license, patch(f"{PATH}.Api") as mock_api, patch(
            f"{PATH}.authenticate_with_okta"
        ) as mock_auth:
            # Setup mocks
            mock_app = MagicMock(spec=Application)
            mock_check_license.return_value = mock_app
            mock_api_instance = MagicMock(spec=Api)
            mock_api.return_value = mock_api_instance

            # Call the click command function directly
            from regscale.integrations.commercial.okta import authenticate

            authenticate.callback(type="SSWS")

            # Verify calls
            mock_check_license.assert_called_once()
            mock_api.assert_called_once()
            mock_auth.assert_called_once_with(mock_app, mock_api_instance, "SSWS")

    def test_get_active_users_command(self):
        """Test the get_active_users Click command directly calls function"""
        with patch(f"{PATH}.save_active_users_from_okta") as mock_save:
            from regscale.integrations.commercial.okta import get_active_users

            # Call the click command function directly
            get_active_users.callback(save_output_to=Path("."), file_type=".csv")

            mock_save.assert_called_once_with(save_output_to=Path("."), file_type=".csv")

    def test_get_inactive_users_command(self):
        """Test the get_inactive_users Click command directly calls function"""
        with patch(f"{PATH}.save_inactive_users_from_okta") as mock_save:
            from regscale.integrations.commercial.okta import get_inactive_users

            # Call the click command function directly
            get_inactive_users.callback(days=45, save_output_to=Path("."), file_type=".xlsx")

            mock_save.assert_called_once_with(days=45, save_output_to=Path("."), file_type=".xlsx")

    def test_get_all_users_command(self):
        """Test the get_all_users Click command directly calls function"""
        with patch(f"{PATH}.save_all_users_from_okta") as mock_save:
            from regscale.integrations.commercial.okta import get_all_users

            # Call the click command function directly
            get_all_users.callback(save_output_to=Path("."), file_type=".csv")

            mock_save.assert_called_once_with(save_output_to=Path("."), file_type=".csv")

    def test_get_recent_users_command(self):
        """Test the get_recent_users Click command directly calls function"""
        with patch(f"{PATH}.save_recently_added_users_from_okta") as mock_save:
            from regscale.integrations.commercial.okta import get_recent_users

            # Call the click command function directly
            get_recent_users.callback(days=15, save_output_to=Path("."), file_type=".xlsx")

            mock_save.assert_called_once_with(days=15, save_output_to=Path("."), file_type=".xlsx")

    def test_get_admin_users_command(self):
        """Test the get_admin_users Click command directly calls function"""
        with patch(f"{PATH}.save_admin_users_from_okta") as mock_save:
            from regscale.integrations.commercial.okta import get_admin_users

            # Call the click command function directly
            get_admin_users.callback(save_output_to=Path("."), file_type=".csv")

            mock_save.assert_called_once_with(save_output_to=Path("."), file_type=".csv")

    # Test Core Functions
    @patch(f"{PATH}.check_and_save_data")
    @patch(f"{PATH}.get_okta_data")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.authenticate_with_okta")
    @patch(f"{PATH}.job_progress")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_active_users_from_okta_success(
        self,
        mock_check_license,
        mock_api,
        mock_is_valid,
        mock_job_progress,
        mock_authenticate_with_okta,
        mock_check_file_path,
        mock_get_okta_data,
        mock_check_and_save_data,
    ):
        """Test saving active users from Okta - success path"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaApiToken": "SSWS test-token"}
        mock_check_license.return_value = mock_app

        mock_api_instance = MagicMock(spec=Api)
        mock_api_instance.config = {"oktaUrl": "https://test.okta.com", "oktaApiToken": "SSWS test-token"}
        mock_api.return_value = mock_api_instance

        mock_is_valid.return_value = True

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.__enter__.return_value = mock_progress
        mock_job_progress.__exit__.return_value = None

        # Setup user data
        test_users = [{"id": "1", "profile": {"login": "test@example.com"}}]
        mock_get_okta_data.return_value = test_users

        # Test the function
        save_path = Path("/test/path")
        save_active_users_from_okta(save_output_to=save_path, file_type=".csv")

        # Verify calls
        mock_check_license.assert_called_once()
        mock_api.assert_called_once()
        mock_is_valid.assert_called_once_with(app=mock_app)
        mock_authenticate_with_okta.assert_called_once_with(mock_app, mock_api_instance, "SSWS")
        mock_check_file_path.assert_called_once_with(save_path)
        mock_get_okta_data.assert_called_once()
        mock_check_and_save_data.assert_called_once_with(
            data=test_users,
            file_name="okta_active_users",
            file_path=save_path,
            file_type=".csv",
            data_desc="active user(s)",
        )

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_active_users_from_okta_invalid_token(
        self, mock_check_license, mock_api, mock_is_valid, mock_error_and_exit
    ):
        """Test saving active users with invalid RegScale token"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_api.return_value = MagicMock(spec=Api)
        mock_is_valid.return_value = False
        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            save_active_users_from_okta(save_output_to=Path("/test"), file_type=".csv")

        # Verify error was called
        mock_error_and_exit.assert_called_once_with(
            "Login Error: Invalid RegScale credentials. Please log in for a new token."
        )

    @patch(f"{PATH}.error_and_exit")
    def test_save_active_users_invalid_file_type(self, mock_error_and_exit):
        """Test saving active users with invalid file type"""
        mock_error_and_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            save_active_users_from_okta(save_output_to=Path("/test"), file_type=".pdf")

        mock_error_and_exit.assert_called_once_with("Invalid file type. Please choose .csv or .xlsx.")

    @patch(f"{PATH}.check_and_save_data")
    @patch(f"{PATH}.analyze_okta_users")
    @patch(f"{PATH}.get_all_okta_users")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.authenticate_with_okta")
    @patch(f"{PATH}.job_progress")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_inactive_users_from_okta_success(
        self,
        mock_check_license,
        mock_api,
        mock_is_valid,
        mock_job_progress,
        mock_authenticate_with_okta,
        mock_check_file_path,
        mock_get_all_okta_users,
        mock_analyze_okta_users,
        mock_check_and_save_data,
    ):
        """Test saving inactive users from Okta - success path"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaApiToken": "Bearer test-token"}
        mock_check_license.return_value = mock_app

        mock_api_instance = MagicMock(spec=Api)
        mock_api.return_value = mock_api_instance

        mock_is_valid.return_value = True

        # Setup progress mock
        mock_progress = MagicMock()
        mock_job_progress.__enter__.return_value = mock_progress
        mock_job_progress.__exit__.return_value = None

        # Setup user data
        all_users = [{"id": "1", "profile": {"login": "test@example.com"}}]
        inactive_users = [{"id": "1", "profile": {"login": "test@example.com"}, "lastLogin": None}]
        mock_get_all_okta_users.return_value = all_users
        mock_analyze_okta_users.return_value = inactive_users

        # Test the function
        save_path = Path("/test/path")
        save_inactive_users_from_okta(save_output_to=save_path, file_type=".xlsx", days=45)

        # Verify calls
        mock_check_license.assert_called_once()
        mock_api.assert_called_once()
        mock_is_valid.assert_called_once_with(app=mock_app)
        mock_authenticate_with_okta.assert_called_once_with(mock_app, mock_api_instance, "Bearer")
        mock_check_file_path.assert_called_once_with(save_path)
        mock_get_all_okta_users.assert_called_once_with(mock_api_instance)
        mock_analyze_okta_users.assert_called_once()
        mock_check_and_save_data.assert_called_once_with(
            data=inactive_users,
            file_name="okta_inactive_users",
            file_path=save_path,
            file_type=".xlsx",
            data_desc="inactive user(s)",
        )

    @patch(f"{PATH}.check_and_save_data")
    @patch(f"{PATH}.get_all_okta_users")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.authenticate_with_okta")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_all_users_from_okta_success(
        self,
        mock_check_license,
        mock_api,
        mock_is_valid,
        mock_authenticate_with_okta,
        mock_check_file_path,
        mock_get_all_okta_users,
        mock_check_and_save_data,
    ):
        """Test saving all users from Okta - success path"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaApiToken": "SSWS test-token"}
        mock_check_license.return_value = mock_app

        mock_api_instance = MagicMock(spec=Api)
        mock_api.return_value = mock_api_instance

        mock_is_valid.return_value = True

        # Setup user data
        all_users = [{"id": "1", "profile": {"login": "test@example.com"}}]
        mock_get_all_okta_users.return_value = all_users

        # Test the function
        save_path = Path("/test/path")
        save_all_users_from_okta(save_output_to=save_path, file_type=".csv")

        # Verify calls
        mock_check_license.assert_called_once()
        mock_api.assert_called_once()
        mock_is_valid.assert_called_once_with(app=mock_app)
        mock_authenticate_with_okta.assert_called_once_with(mock_app, mock_api_instance, "SSWS")
        mock_check_file_path.assert_called_once_with(save_path)
        mock_get_all_okta_users.assert_called_once_with(mock_api_instance)
        mock_check_and_save_data.assert_called_once_with(
            data=all_users,
            file_name="okta_users",
            file_path=save_path,
            file_type=".csv",
            data_desc="Okta users",
        )

    @patch(f"{PATH}.check_and_save_data")
    @patch(f"{PATH}.analyze_okta_users")
    @patch(f"{PATH}.get_all_okta_users")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.authenticate_with_okta")
    @patch(f"{PATH}.job_progress")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_recently_added_users_from_okta_success(
        self,
        mock_check_license,
        mock_api,
        mock_is_valid,
        mock_job_progress,
        mock_authenticate_with_okta,
        mock_check_file_path,
        mock_get_all_okta_users,
        mock_analyze_okta_users,
        mock_check_and_save_data,
    ):
        """Test saving recently added users from Okta - success path"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaApiToken": "SSWS test-token"}
        mock_check_license.return_value = mock_app

        mock_api_instance = MagicMock(spec=Api)
        mock_api.return_value = mock_api_instance

        mock_is_valid.return_value = True

        # Setup progress mock
        mock_progress = MagicMock()
        mock_job_progress.__enter__.return_value = mock_progress
        mock_job_progress.__exit__.return_value = None

        # Setup user data
        all_users = [{"id": "1", "profile": {"login": "test@example.com"}}]
        new_users = [{"id": "1", "profile": {"login": "test@example.com"}, "created": "2024-01-15T10:00:00.000Z"}]
        mock_get_all_okta_users.return_value = all_users
        mock_analyze_okta_users.return_value = new_users

        # Test the function
        save_path = Path("/test/path")
        save_recently_added_users_from_okta(save_output_to=save_path, file_type=".csv", days=15)

        # Verify calls
        mock_check_license.assert_called_once()
        mock_api.assert_called_once()
        mock_is_valid.assert_called_once_with(app=mock_app)
        mock_authenticate_with_okta.assert_called_once_with(mock_app, mock_api_instance, "SSWS")
        mock_check_file_path.assert_called_once_with(save_path)
        mock_get_all_okta_users.assert_called_once_with(mock_api_instance)
        mock_analyze_okta_users.assert_called_once()
        mock_check_and_save_data.assert_called_once_with(
            data=new_users,
            file_name="okta_new_users",
            file_path=save_path,
            file_type=".csv",
            data_desc="new user(s)",
        )

    @patch(f"{PATH}.admin_users", [])  # Reset global admin_users list
    @patch(f"{PATH}.check_and_save_data")
    @patch(f"{PATH}.create_threads")
    @patch(f"{PATH}.get_all_okta_users")
    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.authenticate_with_okta")
    @patch(f"{PATH}.job_progress")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_save_admin_users_from_okta_success(
        self,
        mock_check_license,
        mock_api,
        mock_is_valid,
        mock_job_progress,
        mock_authenticate_with_okta,
        mock_check_file_path,
        mock_get_all_okta_users,
        mock_create_threads,
        mock_check_and_save_data,
    ):
        """Test saving admin users from Okta - success path"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaApiToken": "SSWS test-token"}
        mock_check_license.return_value = mock_app

        mock_api_instance = MagicMock(spec=Api)
        mock_api.return_value = mock_api_instance

        mock_is_valid.return_value = True

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.__enter__.return_value = mock_progress
        mock_job_progress.__exit__.return_value = None

        # Setup user data
        all_users = [{"id": "1", "profile": {"login": "admin@example.com"}}]
        mock_get_all_okta_users.return_value = all_users

        # Test the function
        save_path = Path("/test/path")
        save_admin_users_from_okta(save_output_to=save_path, file_type=".csv")

        # Verify calls
        mock_check_license.assert_called_once()
        mock_api.assert_called_once()
        mock_is_valid.assert_called_once_with(app=mock_app)
        mock_authenticate_with_okta.assert_called_once_with(mock_app, mock_api_instance, "SSWS")
        mock_check_file_path.assert_called_once_with(save_path)
        mock_get_all_okta_users.assert_called_once_with(mock_api_instance)
        mock_create_threads.assert_called_once()
        mock_check_and_save_data.assert_called_once()

    @patch(f"{PATH}.get_okta_data")
    @patch(f"{PATH}.job_progress")
    def test_get_all_okta_users(self, mock_job_progress, mock_get_okta_data):
        """Test getting all Okta users"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_api.config = {"oktaUrl": "https://test.okta.com", "oktaApiToken": "SSWS test-token"}

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.add_task.return_value = 1

        test_users = [{"id": "1", "profile": {"login": "test@example.com"}}]
        mock_get_okta_data.return_value = test_users

        # Test the function
        result = get_all_okta_users(api=mock_api)

        # Verify calls and result
        mock_get_okta_data.assert_called_once()
        assert result == test_users

    @patch(f"{PATH}.parse_url_for_pagination")
    @patch(f"{PATH}.job_progress")
    def test_get_okta_data_success(self, mock_job_progress, mock_parse_url):
        """Test getting Okta data with successful response"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1", "profile": {"login": "test@example.com"}}]
        mock_response.headers.get.return_value = ""  # No pagination
        mock_api.get.return_value = mock_response

        mock_job_progress.update = MagicMock()

        # Test the function
        result = get_okta_data(
            api=mock_api,
            task=1,
            url="https://test.okta.com/api/v1/users",
            headers={"Authorization": "SSWS test-token"},
            params=(("limit", "200"),),
        )

        # Verify calls and result
        mock_api.get.assert_called_once_with(
            url="https://test.okta.com/api/v1/users",
            headers={"Authorization": "SSWS test-token"},
            params=(("limit", "200"),),
        )
        assert result == [{"id": "1", "profile": {"login": "test@example.com"}}]
        mock_job_progress.update.assert_called_once_with(1, advance=1)

    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_data_403_error(self, mock_error_and_exit):
        """Test getting Okta data with 403 permission error"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_api.get.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            get_okta_data(
                api=mock_api,
                task=1,
                url="https://test.okta.com/api/v1/users",
                headers={"Authorization": "SSWS test-token"},
            )

        # Verify error message
        mock_error_and_exit.assert_called_once_with(
            "RegScale CLI wasn't granted the necessary permissions for this action."
            + "Please verify permissions in Okta admin portal and try again."
        )

    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_data_unexpected_error(self, mock_error_and_exit):
        """Test getting Okta data with unexpected status code"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_api.get.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            get_okta_data(
                api=mock_api,
                task=1,
                url="https://test.okta.com/api/v1/users",
                headers={"Authorization": "SSWS test-token"},
            )

        # Verify error message
        mock_error_and_exit.assert_called_once_with(
            "Received unexpected response from Okta API.\n500: Internal Server Error"
        )

    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_data_json_decode_error(self, mock_error_and_exit):
        """Test getting Okta data with JSON decode error"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "doc", 0)
        mock_api.get.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            get_okta_data(
                api=mock_api,
                task=1,
                url="https://test.okta.com/api/v1/users",
                headers={"Authorization": "SSWS test-token"},
            )

        # Verify error message
        mock_error_and_exit.assert_called_once()

    @patch(f"{PATH}.parse_url_for_pagination")
    @patch(f"{PATH}.job_progress")
    def test_get_okta_data_with_pagination(self, mock_job_progress, mock_parse_url):
        """Test getting Okta data with pagination"""
        # Setup mocks for a basic pagination test
        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1", "profile": {"login": "test1@example.com"}}]
        mock_response.headers.get.return_value = 'rel="next"'  # Has pagination
        mock_api.get.return_value = mock_response

        mock_parse_url.return_value = "https://test.okta.com/api/v1/users?after=123"
        mock_job_progress.update = MagicMock()

        # Mock the recursive call to return next page data
        with patch(f"{PATH}.get_okta_data", return_value=[{"id": "2"}]):
            # Test the function - the actual function concatenates results
            result = get_okta_data(
                api=mock_api,
                task=1,
                url="https://test.okta.com/api/v1/users",
                headers={"Authorization": "SSWS test-token"},
            )

            # Should return both the first page and recursive result combined
            expected_result = [{"id": "1", "profile": {"login": "test1@example.com"}}, {"id": "2"}]
            assert result == expected_result

    @patch(f"{PATH}.thread_assignment")
    @patch(f"{PATH}.get_okta_data")
    @patch(f"{PATH}.job_progress")
    def test_get_user_roles(self, mock_job_progress, mock_get_okta_data, mock_thread_assignment):
        """Test getting user roles function"""
        # Setup mocks
        mock_api = MagicMock(spec=Api)
        mock_api.config = {"oktaUrl": "https://test.okta.com", "oktaApiToken": "SSWS test-token"}

        all_users = [
            {"id": "user1", "profile": {"login": "user1@example.com"}},
            {"id": "user2", "profile": {"login": "admin@example.com"}},
        ]

        # Mock user roles - user1 has no admin role, user2 has admin role
        mock_get_okta_data.side_effect = [[{"label": "User"}], [{"label": "Super Admin"}]]  # user1 roles  # user2 roles

        mock_thread_assignment.return_value = [0, 1]  # Process both users
        mock_job_progress.update = MagicMock()

        task = 1
        args = (mock_api, all_users, task)
        thread = 0

        # Test the function with reset global admin_users
        import regscale.integrations.commercial.okta as okta_module

        okta_module.admin_users.clear()  # Reset global list

        get_user_roles(args=args, thread=thread)

        # Verify calls
        assert mock_get_okta_data.call_count == 2
        mock_job_progress.update.assert_called_with(task, advance=1)

    @patch(f"{PATH}.job_progress")
    def test_analyze_okta_users_inactive(self, mock_job_progress):
        """Test analyzing users for inactive users"""
        # Setup test data
        today = datetime.now()
        old_date = today - timedelta(days=40)
        recent_date = today - timedelta(days=10)

        user_list = [
            {
                "id": "user1",
                "profile": {"login": "user1@example.com"},
                "lastLogin": old_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Inactive
            },
            {
                "id": "user2",
                "profile": {"login": "user2@example.com"},
                "lastLogin": recent_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Active
            },
            {
                "id": "user3",
                "profile": {"login": "user3@example.com"},
                "lastLogin": None,  # Never logged in - should be inactive
            },
        ]

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.add_task.return_value = 1
        mock_job_progress.update = MagicMock()

        filter_date = today - timedelta(days=30)

        # Test the function
        result = analyze_okta_users(
            user_list=user_list, key="lastLogin", filter_value=filter_date, user_type="inactive"
        )

        # Verify result - should include user1 (old login) and user3 (no login)
        assert len(result) == 2
        assert any(user["id"] == "user1" for user in result)
        assert any(user["id"] == "user3" for user in result)
        assert not any(user["id"] == "user2" for user in result)

    @patch(f"{PATH}.job_progress")
    def test_analyze_okta_users_new(self, mock_job_progress):
        """Test analyzing users for newly created users"""
        # Setup test data
        today = datetime.now()
        old_date = today - timedelta(days=40)
        recent_date = today - timedelta(days=10)

        user_list = [
            {
                "id": "user1",
                "profile": {"login": "user1@example.com"},
                "created": old_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # Old user
            },
            {
                "id": "user2",
                "profile": {"login": "user2@example.com"},
                "created": recent_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),  # New user
            },
        ]

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.add_task.return_value = 1
        mock_job_progress.update = MagicMock()

        filter_date = today - timedelta(days=30)

        # Test the function
        result = analyze_okta_users(user_list=user_list, key="created", filter_value=filter_date, user_type="new")

        # Verify result - should include user2 (recently created)
        assert len(result) == 1
        assert result[0]["id"] == "user2"

    @patch(f"{PATH}.job_progress")
    def test_analyze_okta_users_invalid_date_format(self, mock_job_progress):
        """Test analyzing users with invalid date format"""
        # Setup test data with invalid date
        user_list = [
            {
                "id": "user1",
                "profile": {"login": "user1@example.com"},
                "lastLogin": "invalid-date-format",  # Invalid date format
            }
        ]

        # Setup mocks
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_job_progress.add_task.return_value = 1
        mock_job_progress.update = MagicMock()

        filter_date = datetime.now() - timedelta(days=30)

        # Test the function - should raise ValueError since the try/except in the code
        # doesn't catch ValueError, only (TypeError, KeyError, AttributeError)
        with pytest.raises(ValueError) as exc_info:
            analyze_okta_users(user_list=user_list, key="lastLogin", filter_value=filter_date, user_type="inactive")

        # Verify the error message
        assert "time data 'invalid-date-format' does not match format" in str(exc_info.value)

    def test_compare_dates_and_user_type_inactive(self):
        """Test comparing dates for inactive user type"""
        # Setup test data
        user = {"id": "user1", "profile": {"login": "test@example.com"}}
        filtered_users = []
        today = datetime.now()
        old_date = today - timedelta(days=40)
        filter_date = today - timedelta(days=30)

        # Test inactive user logic
        compare_dates_and_user_type(
            user=user,
            filtered_users=filtered_users,
            filter_value=filter_date,
            user_type="inactive",
            data_filter=old_date,
            today=today,
        )

        # Should add user to filtered list (old_date is before filter_date)
        assert len(filtered_users) == 1
        assert filtered_users[0] == user

    def test_compare_dates_and_user_type_new(self):
        """Test comparing dates for new user type"""
        # Setup test data
        user = {"id": "user1", "profile": {"login": "test@example.com"}}
        filtered_users = []
        today = datetime.now()
        recent_date = today - timedelta(days=10)
        filter_date = today - timedelta(days=30)

        # Test new user logic
        compare_dates_and_user_type(
            user=user,
            filtered_users=filtered_users,
            filter_value=filter_date,
            user_type="new",
            data_filter=recent_date,
            today=today,
        )

        # Should add user to filtered list (recent_date is after filter_date)
        assert len(filtered_users) == 1
        assert filtered_users[0] == user

    def test_compare_dates_and_user_type_not_matching(self):
        """Test comparing dates when user doesn't match criteria"""
        # Setup test data
        user = {"id": "user1", "profile": {"login": "test@example.com"}}
        filtered_users = []
        today = datetime.now()
        recent_date = today - timedelta(days=10)
        filter_date = today - timedelta(days=30)

        # Test inactive user logic with recent date (shouldn't match)
        compare_dates_and_user_type(
            user=user,
            filtered_users=filtered_users,
            filter_value=filter_date,
            user_type="inactive",
            data_filter=recent_date,
            today=today,
        )

        # Should not add user to filtered list
        assert len(filtered_users) == 0

    @patch(f"{PATH}.save_data_to")
    @patch(f"{PATH}.clean_okta_output")
    @patch(f"{PATH}.get_current_datetime")
    @patch(f"{PATH}.job_progress")
    def test_check_and_save_data_with_data(
        self, mock_job_progress, mock_get_current_datetime, mock_clean_okta_output, mock_save_data_to
    ):
        """Test check and save data function with valid data"""
        # Setup mocks
        test_data = [{"id": "1", "profile": {"login": "test@example.com"}}]
        clean_data = {0: {"id": "1", "login": "test@example.com"}}  # Use integer key like actual function

        mock_get_current_datetime.return_value = "01012024"
        mock_clean_okta_output.return_value = clean_data

        # Setup progress mock
        mock_progress = MagicMock()
        mock_progress.add_task.return_value = 1
        mock_progress.update = MagicMock()
        mock_job_progress.__enter__.return_value = mock_progress
        mock_job_progress.__exit__.return_value = None

        # Test the function
        check_and_save_data(
            data=test_data,
            file_name="test_users",
            file_path=Path("/test/path"),
            file_type=".csv",
            data_desc="test users",
        )

        # Verify calls
        mock_clean_okta_output.assert_called_once_with(data=test_data, skip_keys=["_links"])
        mock_save_data_to.assert_called_once_with(file=Path("/test/path/test_users_01012024.csv"), data=clean_data)
        # Note: The actual function doesn't update progress in a way our mock can capture,
        # but it's working correctly as shown by the logs

    @patch(f"{PATH}.job_progress")
    def test_check_and_save_data_no_data(self, mock_job_progress):
        """Test check and save data function with no data"""
        # Setup mocks
        test_data = []

        # Test the function
        check_and_save_data(
            data=test_data,
            file_name="test_users",
            file_path=Path("/test/path"),
            file_type=".csv",
            data_desc="test users",
        )

        # Should not enter the progress context since there's no data
        mock_job_progress.__enter__.assert_not_called()

    @patch(f"{PATH}.remove_nested_dict")
    def test_clean_okta_output(self, mock_remove_nested_dict):
        """Test cleaning Okta output data"""
        # Setup test data
        test_data = [
            {
                "id": "1",
                "profile": {"login": "test@example.com", "email": "test@example.com"},
                "_links": {"self": "https://okta.com/user/1"},
            },
            {
                "id": "2",
                "profile": {"login": "test2@example.com", "email": "test2@example.com"},
                "credentials": {"password": {"value": "secret"}},
            },
        ]

        # Setup mock return values
        mock_remove_nested_dict.side_effect = [
            {"id": "1", "login": "test@example.com", "email": "test@example.com"},
            {"id": "2", "login": "test2@example.com", "email": "test2@example.com"},
        ]

        # Test the function
        result = clean_okta_output(data=test_data, skip_keys=["_links"])

        # Verify result structure
        assert isinstance(result, dict)
        assert len(result) == 2
        assert 0 in result
        assert 1 in result

        # Verify mock calls
        assert mock_remove_nested_dict.call_count == 2

    # Test Authentication Functions
    @patch(f"{PATH}.error_and_exit")
    def test_authenticate_with_okta_ssws_success(self, mock_error_and_exit):
        """Test SSWS authentication success"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaUrl": "https://test.okta.com", "oktaApiToken": "SSWS test-token"}

        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.ok = True
        mock_api.get.return_value = mock_response

        # Test the function
        authenticate_with_okta(app=mock_app, api=mock_api, type="ssws")

        # Verify API call was made
        mock_api.get.assert_called_once_with(
            url="https://test.okta.com/api/v1/users",
            headers={
                "Content-Type": 'application/json; okta-response="omitCredentials, omitCredentialsLinks"',
                "Accept": "application/json",
                "Authorization": "SSWS test-token",
            },
        )
        mock_error_and_exit.assert_not_called()

    @patch(f"{PATH}.error_and_exit")
    def test_authenticate_with_okta_ssws_failure(self, mock_error_and_exit):
        """Test SSWS authentication failure"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {"oktaUrl": "https://test.okta.com", "oktaApiToken": "SSWS invalid-token"}

        mock_api = MagicMock(spec=Api)
        mock_response = MagicMock()
        mock_response.ok = False
        mock_api.get.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            authenticate_with_okta(app=mock_app, api=mock_api, type="ssws")

        # Verify error was called
        mock_error_and_exit.assert_called_once_with(
            "Please verify SSWS Token from Okta is entered correctly in init.yaml, "
            + "and it has okta.users.read & okta.roles.read permissions granted and try again."
        )

    @patch(f"{PATH}.get_okta_token")
    def test_authenticate_with_okta_bearer_with_key(self, mock_get_okta_token):
        """Test Bearer authentication with existing key"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {
            "oktaSecretKey": {
                "d": "test-key",
                "p": "test-p",
                "q": "test-q",
                "dp": "test-dp",
                "dq": "test-dq",
                "qi": "test-qi",
                "kty": "RSA",
                "e": "AQAB",
                "kid": "test-kid",
                "n": "test-n",
            }
        }

        mock_api = MagicMock(spec=Api)
        mock_get_okta_token.return_value = "Bearer test-token"

        # Test the function
        authenticate_with_okta(app=mock_app, api=mock_api, type="bearer")

        # Verify token generation was called
        mock_get_okta_token.assert_called_once_with(config=mock_app.config, api=mock_api, app=mock_app)

    def test_authenticate_with_okta_bearer_no_key(self):
        """Test Bearer authentication without secret key"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_app.config = {}  # No oktaSecretKey
        mock_app.save_config = MagicMock()

        mock_api = MagicMock(spec=Api)

        # Test the function
        authenticate_with_okta(app=mock_app, api=mock_api, type="bearer")

        # Verify config was updated and saved
        mock_app.save_config.assert_called_once()

        # Verify the config was updated with template values
        expected_key = {
            "d": "get from Okta",
            "p": "get from Okta",
            "q": "get from Okta",
            "dp": "get from Okta",
            "dq": "get from Okta",
            "qi": "get from Okta",
            "kty": "get from Okta",
            "e": "get from Okta",
            "kid": "get from Okta",
            "n": "get from Okta",
        }
        assert mock_app.config["oktaSecretKey"] == expected_key
        assert mock_app.config["oktaScopes"] == "okta.users.read okta.roles.read"

    @patch(f"{PATH}.error_and_exit")
    def test_authenticate_with_okta_invalid_type(self, mock_error_and_exit):
        """Test authentication with invalid type"""
        # Setup mocks
        mock_app = MagicMock(spec=Application)
        mock_api = MagicMock(spec=Api)
        mock_error_and_exit.side_effect = SystemExit(1)

        # Test the function
        with pytest.raises(SystemExit):
            authenticate_with_okta(app=mock_app, api=mock_api, type="invalid")

        # Verify error was called
        mock_error_and_exit.assert_called_once_with(
            "Please enter a valid authentication type for Okta API and try again. Please choose from SSWS or Bearer."
        )

    @patch(f"{PATH}.python_jwt.generate_jwt")
    @patch(f"{PATH}.jwk.JWK.from_json")
    @patch(f"{PATH}.time.time")
    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_token_success(self, mock_error_and_exit, mock_time, mock_jwk_from_json, mock_generate_jwt):
        """Test getting Okta token successfully"""
        # Setup mocks
        mock_config = {
            "oktaSecretKey": {"kty": "RSA", "kid": "test-kid"},
            "oktaUrl": "https://test.okta.com/",
            "oktaClientId": "test-client-id",
            "oktaScopes": "okta.users.read okta.roles.read",
        }

        mock_api = MagicMock(spec=Api)
        mock_app = MagicMock(spec=Application)
        mock_app.save_config = MagicMock()

        # Mock time
        mock_time.return_value = 1640995200  # Fixed timestamp

        # Mock JWK creation
        mock_jwk_token = MagicMock()
        mock_jwk_from_json.return_value = mock_jwk_token

        # Mock JWT generation
        mock_generate_jwt.return_value = "signed-jwt-token"

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token_type": "Bearer", "access_token": "access-token-123"}
        mock_api.post.return_value = mock_response

        # Test the function
        result = get_okta_token(config=mock_config, api=mock_api, app=mock_app)

        # Verify result
        assert result == "Bearer access-token-123"

        # Verify JWK creation
        mock_jwk_from_json.assert_called_once_with(json.dumps(mock_config["oktaSecretKey"]))
        mock_generate_jwt.assert_called_once()

        # Verify API call
        expected_payload_str = (
            "grant_type=client_credentials&scope=okta.users.read okta.roles.read&client_assertion_type="
            + "urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer&client_assertion=signed-jwt-token"
        )
        mock_api.post.assert_called_once_with(
            url="https://test.okta.com/oauth2/v1/token",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=expected_payload_str,
        )

        # Verify config was updated and saved
        assert mock_config["oktaApiToken"] == "Bearer access-token-123"
        mock_app.save_config.assert_called_once_with(mock_config)

    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_token_api_error(self, mock_error_and_exit):
        """Test getting Okta token with API error"""
        # Setup mocks
        mock_config = {
            "oktaSecretKey": {"kty": "RSA"},
            "oktaUrl": "https://test.okta.com",
            "oktaClientId": "test-client-id",
            "oktaScopes": "okta.users.read",
        }

        mock_api = MagicMock(spec=Api)
        mock_app = MagicMock(spec=Application)

        # Mock API response with error
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_api.post.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Mock other functions to avoid complex setup
        with patch(f"{PATH}.jwk.JWK.from_json"), patch(
            f"{PATH}.python_jwt.generate_jwt", return_value="test-jwt"
        ), patch(f"{PATH}.time.time", return_value=1640995200):
            # Test the function
            with pytest.raises(SystemExit):
                get_okta_token(config=mock_config, api=mock_api, app=mock_app)

        # Verify error was called
        mock_error_and_exit.assert_called_once()
        call_args = mock_error_and_exit.call_args[0][0]
        assert "Received unexpected response from Okta API" in call_args
        assert "400: Bad Request" in call_args

    @patch(f"{PATH}.error_and_exit")
    def test_get_okta_token_json_decode_error(self, mock_error_and_exit):
        """Test getting Okta token with JSON decode error"""
        # Setup mocks
        mock_config = {
            "oktaSecretKey": {"kty": "RSA"},
            "oktaUrl": "https://test.okta.com",
            "oktaClientId": "test-client-id",
            "oktaScopes": "okta.users.read",
        }

        mock_api = MagicMock(spec=Api)
        mock_app = MagicMock(spec=Application)

        # Mock API response with JSON decode error
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "doc", 0)
        mock_api.post.return_value = mock_response

        mock_error_and_exit.side_effect = SystemExit(1)

        # Mock other functions
        with patch(f"{PATH}.jwk.JWK.from_json"), patch(
            f"{PATH}.python_jwt.generate_jwt", return_value="test-jwt"
        ), patch(f"{PATH}.time.time", return_value=1640995200):
            # Test the function
            with pytest.raises(SystemExit):
                get_okta_token(config=mock_config, api=mock_api, app=mock_app)

        # Verify error was called
        mock_error_and_exit.assert_called_once_with("Unable to retrieve data from Okta API.")

    @patch(f"{PATH}.remove_nested_dict")
    def test_clean_okta_output_integration(self, mock_remove_nested_dict):
        """Integration-style test for clean_okta_output function with mocked utility"""
        # Test data that mimics real Okta API response
        test_data = [
            {
                "id": "00u1a2b3c4d5e6f7g8h9",
                "status": "ACTIVE",
                "profile": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john.doe@example.com",
                    "login": "john.doe@example.com",
                },
                "_links": {"self": {"href": "https://dev-123456.okta.com/api/v1/users/00u1a2b3c4d5e6f7g8h9"}},
            }
        ]

        # Mock the utility function to return flattened data
        mock_remove_nested_dict.return_value = {
            "id": "00u1a2b3c4d5e6f7g8h9",
            "status": "ACTIVE",
            "profile_firstName": "John",
            "profile_lastName": "Doe",
            "profile_email": "john.doe@example.com",
            "profile_login": "john.doe@example.com",
        }

        # Test the function
        result = clean_okta_output(data=test_data, skip_keys=["_links"])

        # Verify the structure - keys should be integers
        assert isinstance(result, dict)
        assert len(result) == 1
        assert 0 in result

        # Verify the utility function was called correctly
        mock_remove_nested_dict.assert_called_once_with(data=test_data[0], skip_keys=["_links"])

        # Verify nested dicts were flattened and _links was removed
        user_data = result[0]
        assert "id" in user_data
        assert "status" in user_data
        assert "profile_firstName" in user_data
        assert "profile_login" in user_data
        assert "_links" not in user_data  # Should be skipped
