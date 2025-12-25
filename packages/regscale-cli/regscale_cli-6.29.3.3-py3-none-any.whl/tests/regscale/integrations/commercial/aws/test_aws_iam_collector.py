"""Unit tests for AWS IAM collector."""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.iam import IAMCollector


class TestIAMCollector(unittest.TestCase):
    """Test cases for IAMCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.region = "us-east-1"
        self.account_id = "123456789012"
        self.collector = IAMCollector(self.mock_session, self.region, self.account_id)

    def test_init(self):
        """Test IAMCollector initialization."""
        assert self.collector.session == self.mock_session
        assert self.collector.region == self.region
        assert self.collector.account_id == self.account_id

    def test_init_without_account_id(self):
        """Test IAMCollector initialization without account ID."""
        collector = IAMCollector(self.mock_session, self.region)
        assert collector.account_id is None

    @patch("regscale.integrations.commercial.aws.inventory.resources.iam.logger")
    def test_collect_success(self, mock_logger):
        """Test successful collection of IAM resources."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Mock account summary
        mock_client.get_account_summary.return_value = {"SummaryMap": {"Users": 5, "Roles": 10}}

        # Mock password policy
        mock_client.get_account_password_policy.return_value = {
            "PasswordPolicy": {"MinimumPasswordLength": 14, "RequireSymbols": True}
        }

        # Mock users
        user_arn = f"arn:aws:iam::{self.account_id}:user/test-user"
        mock_client.get_paginator.return_value.paginate.return_value = [
            {"Users": [{"UserName": "test-user", "UserId": "AIDAI123", "Arn": user_arn, "CreateDate": "2024-01-01"}]}
        ]

        # Mock access keys and MFA devices
        mock_client.list_access_keys.return_value = {
            "AccessKeyMetadata": [{"AccessKeyId": "AKIAI123", "Status": "Active", "CreateDate": "2024-01-01"}]
        }
        mock_client.list_mfa_devices.return_value = {
            "MFADevices": [{"SerialNumber": "arn:aws:iam::123:mfa/device", "EnableDate": "2024-01-01"}]
        }

        result = self.collector.collect()

        assert "Users" in result
        assert "Roles" in result
        assert "Groups" in result
        assert "Policies" in result
        assert "AccessKeys" in result
        assert "MFADevices" in result
        assert "AccountSummary" in result
        assert "PasswordPolicy" in result

    @patch("regscale.integrations.commercial.aws.inventory.resources.iam.logger")
    def test_collect_handles_client_error(self, mock_logger):
        """Test collection handles ClientError."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.get_account_summary.side_effect = ClientError(error_response, "get_account_summary")

        result = self.collector.collect()

        assert result["AccountSummary"] == {}

    @patch("regscale.integrations.commercial.aws.inventory.resources.iam.logger")
    def test_collect_handles_unexpected_error(self, mock_logger):
        """Test collection handles unexpected errors."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        mock_client.get_account_summary.side_effect = Exception("Unexpected error")

        self.collector.collect()

        mock_logger.error.assert_called()

    def test_get_account_summary_success(self):
        """Test successful account summary retrieval."""
        mock_client = MagicMock()
        mock_client.get_account_summary.return_value = {"SummaryMap": {"Users": 5, "Roles": 10}}

        result = self.collector._get_account_summary(mock_client)

        assert result["Users"] == 5
        assert result["Roles"] == 10
        assert result["Region"] == self.region

    def test_get_account_summary_access_denied(self):
        """Test account summary with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.get_account_summary.side_effect = ClientError(error_response, "get_account_summary")

        result = self.collector._get_account_summary(mock_client)

        assert result == {}

    def test_get_password_policy_success(self):
        """Test successful password policy retrieval."""
        mock_client = MagicMock()
        mock_client.get_account_password_policy.return_value = {
            "PasswordPolicy": {"MinimumPasswordLength": 14, "RequireSymbols": True}
        }

        result = self.collector._get_password_policy(mock_client)

        assert result["MinimumPasswordLength"] == 14
        assert result["RequireSymbols"] is True
        assert result["Region"] == self.region

    def test_get_password_policy_no_policy(self):
        """Test password policy when no policy exists."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "NoSuchEntity", "Message": "No policy"}}
        mock_client.get_account_password_policy.side_effect = ClientError(error_response, "get_account_password_policy")

        result = self.collector._get_password_policy(mock_client)

        assert result == {}

    def test_list_users_success(self):
        """Test successful users listing."""
        mock_client = MagicMock()
        user_arn = f"arn:aws:iam::{self.account_id}:user/test-user"
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Users": [{"UserName": "test-user", "UserId": "AIDAI123", "Arn": user_arn, "CreateDate": "2024-01-01"}]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_users(mock_client)

        assert len(result) == 1
        assert result[0]["UserName"] == "test-user"
        assert result[0]["Region"] == self.region

    def test_list_users_filters_by_account_id(self):
        """Test users listing filters by account ID."""
        mock_client = MagicMock()
        user_arn_match = f"arn:aws:iam::{self.account_id}:user/test-user"
        user_arn_no_match = "arn:aws:iam::999999999999:user/other-user"

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Users": [
                    {"UserName": "test-user", "UserId": "AIDAI123", "Arn": user_arn_match, "CreateDate": "2024-01-01"},
                    {
                        "UserName": "other-user",
                        "UserId": "AIDAI456",
                        "Arn": user_arn_no_match,
                        "CreateDate": "2024-01-01",
                    },
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_users(mock_client)

        assert len(result) == 1
        assert result[0]["UserName"] == "test-user"

    def test_list_users_access_denied(self):
        """Test users listing with access denied."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "list_users")
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_users(mock_client)

        assert result == []

    def test_list_roles_success(self):
        """Test successful roles listing."""
        mock_client = MagicMock()
        role_arn = f"arn:aws:iam::{self.account_id}:role/test-role"
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Roles": [{"RoleName": "test-role", "RoleId": "AIDAI123", "Arn": role_arn, "CreateDate": "2024-01-01"}]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_roles(mock_client)

        assert len(result) == 1
        assert result[0]["RoleName"] == "test-role"
        assert result[0]["Region"] == self.region

    def test_list_roles_filters_by_account_id(self):
        """Test roles listing filters by account ID."""
        mock_client = MagicMock()
        role_arn_match = f"arn:aws:iam::{self.account_id}:role/test-role"
        role_arn_no_match = "arn:aws:iam::999999999999:role/other-role"

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Roles": [
                    {"RoleName": "test-role", "RoleId": "AIDAI123", "Arn": role_arn_match, "CreateDate": "2024-01-01"},
                    {
                        "RoleName": "other-role",
                        "RoleId": "AIDAI456",
                        "Arn": role_arn_no_match,
                        "CreateDate": "2024-01-01",
                    },
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_roles(mock_client)

        assert len(result) == 1
        assert result[0]["RoleName"] == "test-role"

    def test_list_roles_access_denied(self):
        """Test roles listing with access denied."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "list_roles")
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_roles(mock_client)

        assert result == []

    def test_list_groups_success(self):
        """Test successful groups listing."""
        mock_client = MagicMock()
        group_arn = f"arn:aws:iam::{self.account_id}:group/test-group"
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Groups": [
                    {"GroupName": "test-group", "GroupId": "AIDAI123", "Arn": group_arn, "CreateDate": "2024-01-01"}
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_groups(mock_client)

        assert len(result) == 1
        assert result[0]["GroupName"] == "test-group"
        assert result[0]["Region"] == self.region

    def test_list_groups_filters_by_account_id(self):
        """Test groups listing filters by account ID."""
        mock_client = MagicMock()
        group_arn_match = f"arn:aws:iam::{self.account_id}:group/test-group"
        group_arn_no_match = "arn:aws:iam::999999999999:group/other-group"

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Groups": [
                    {
                        "GroupName": "test-group",
                        "GroupId": "AIDAI123",
                        "Arn": group_arn_match,
                        "CreateDate": "2024-01-01",
                    },
                    {
                        "GroupName": "other-group",
                        "GroupId": "AIDAI456",
                        "Arn": group_arn_no_match,
                        "CreateDate": "2024-01-01",
                    },
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_groups(mock_client)

        assert len(result) == 1
        assert result[0]["GroupName"] == "test-group"

    def test_list_groups_access_denied(self):
        """Test groups listing with access denied."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "list_groups")
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_groups(mock_client)

        assert result == []

    def test_list_policies_success(self):
        """Test successful policies listing."""
        mock_client = MagicMock()
        policy_arn = f"arn:aws:iam::{self.account_id}:policy/test-policy"
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Policies": [
                    {
                        "PolicyName": "test-policy",
                        "PolicyId": "ANPAI123",
                        "Arn": policy_arn,
                        "CreateDate": "2024-01-01",
                        "UpdateDate": "2024-01-01",
                    }
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_policies(mock_client)

        assert len(result) == 1
        assert result[0]["PolicyName"] == "test-policy"
        assert result[0]["Region"] == self.region

    def test_list_policies_filters_by_account_id(self):
        """Test policies listing filters by account ID."""
        mock_client = MagicMock()
        policy_arn_match = f"arn:aws:iam::{self.account_id}:policy/test-policy"
        policy_arn_no_match = "arn:aws:iam::999999999999:policy/other-policy"

        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Policies": [
                    {
                        "PolicyName": "test-policy",
                        "PolicyId": "ANPAI123",
                        "Arn": policy_arn_match,
                        "CreateDate": "2024-01-01",
                        "UpdateDate": "2024-01-01",
                    },
                    {
                        "PolicyName": "other-policy",
                        "PolicyId": "ANPAI456",
                        "Arn": policy_arn_no_match,
                        "CreateDate": "2024-01-01",
                        "UpdateDate": "2024-01-01",
                    },
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_policies(mock_client)

        assert len(result) == 1
        assert result[0]["PolicyName"] == "test-policy"

    def test_list_policies_access_denied(self):
        """Test policies listing with access denied."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "list_policies")
        mock_client.get_paginator.return_value = mock_paginator

        result = self.collector._list_policies(mock_client)

        assert result == []

    def test_list_access_keys_success(self):
        """Test successful access keys listing."""
        mock_client = MagicMock()
        mock_client.list_access_keys.return_value = {
            "AccessKeyMetadata": [{"AccessKeyId": "AKIAI123", "Status": "Active", "CreateDate": "2024-01-01"}]
        }

        result = self.collector._list_access_keys(mock_client, "test-user")

        assert len(result) == 1
        assert result[0]["AccessKeyId"] == "AKIAI123"
        assert result[0]["UserName"] == "test-user"
        assert result[0]["Region"] == self.region

    def test_list_access_keys_access_denied(self):
        """Test access keys listing with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.list_access_keys.side_effect = ClientError(error_response, "list_access_keys")

        result = self.collector._list_access_keys(mock_client, "test-user")

        assert result == []

    def test_list_mfa_devices_success(self):
        """Test successful MFA devices listing."""
        mock_client = MagicMock()
        mock_client.list_mfa_devices.return_value = {
            "MFADevices": [{"SerialNumber": "arn:aws:iam::123:mfa/device", "EnableDate": "2024-01-01"}]
        }

        result = self.collector._list_mfa_devices(mock_client, "test-user")

        assert len(result) == 1
        assert result[0]["SerialNumber"] == "arn:aws:iam::123:mfa/device"
        assert result[0]["UserName"] == "test-user"
        assert result[0]["Region"] == self.region

    def test_list_mfa_devices_access_denied(self):
        """Test MFA devices listing with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.list_mfa_devices.side_effect = ClientError(error_response, "list_mfa_devices")

        result = self.collector._list_mfa_devices(mock_client, "test-user")

        assert result == []

    def test_matches_account_id_with_matching_arn(self):
        """Test account ID matching with matching ARN."""
        arn = f"arn:aws:iam::{self.account_id}:user/test-user"
        assert self.collector._matches_account_id(arn) is True

    def test_matches_account_id_with_non_matching_arn(self):
        """Test account ID matching with non-matching ARN."""
        arn = "arn:aws:iam::999999999999:user/test-user"
        assert self.collector._matches_account_id(arn) is False

    def test_matches_account_id_with_invalid_arn(self):
        """Test account ID matching with invalid ARN."""
        arn = "invalid-arn"
        assert self.collector._matches_account_id(arn) is False

    def test_matches_account_id_without_filter(self):
        """Test account ID matching without account filter."""
        collector = IAMCollector(self.mock_session, self.region)
        arn = "arn:aws:iam::999999999999:user/test-user"
        assert collector._matches_account_id(arn) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
