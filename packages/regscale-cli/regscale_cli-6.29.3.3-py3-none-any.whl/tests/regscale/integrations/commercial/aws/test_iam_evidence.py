#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS IAM Evidence Integration."""

import gzip
import json
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.iam_evidence import (
    IAMComplianceItem,
    AWSIAMEvidenceIntegration,
    IAM_CACHE_FILE,
    CACHE_TTL_SECONDS,
)

PATH = "regscale.integrations.commercial.aws.iam_evidence"


class TestIAMComplianceItem:
    """Test cases for IAMComplianceItem class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mapper = MagicMock()
        self.mock_mapper.framework = "NIST800-53R5"

    def test_init_with_complete_data(self):
        """Test initialization with complete IAM data."""
        iam_data = {
            "users": [
                {"UserName": "user1", "MfaEnabled": True},
                {"UserName": "user2", "MfaEnabled": True},
            ],
            "groups": [{"GroupName": "group1"}],
            "roles": [{"RoleName": "role1"}],
            "policies": [{"PolicyName": "policy1"}],
        }

        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "PASS",
            "IA-2": "PASS",
            "IA-5": "PASS",
            "AC-3": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.iam_data == iam_data
        assert item.control_mapper == self.mock_mapper
        assert len(item._users) == 2
        assert len(item._groups) == 1
        assert len(item._roles) == 1
        assert len(item._policies) == 1
        assert item._compliance_results == self.mock_mapper.assess_iam_compliance.return_value

    def test_init_with_minimal_data(self):
        """Test initialization with minimal IAM data."""
        iam_data = {}

        self.mock_mapper.assess_iam_compliance.return_value = {}

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert len(item._users) == 0
        assert len(item._groups) == 0
        assert len(item._roles) == 0
        assert len(item._policies) == 0

    def test_resource_id_property(self):
        """Test resource_id property."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {}

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.resource_id == "iam-account"

    def test_resource_name_property(self):
        """Test resource_name property."""
        iam_data = {
            "users": [{"UserName": "user1"}, {"UserName": "user2"}, {"UserName": "user3"}],
            "groups": [],
            "roles": [{"RoleName": "role1"}, {"RoleName": "role2"}],
            "policies": [],
        }
        self.mock_mapper.assess_iam_compliance.return_value = {}

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.resource_name == "AWS IAM Account (3 users, 2 roles)"

    def test_control_id_property_with_failure(self):
        """Test control_id property returns first failed control."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "FAIL",
            "IA-2": "FAIL",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.control_id == "AC-6"

    def test_control_id_property_all_pass(self):
        """Test control_id property when all controls pass."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.control_id == "AC-2"

    def test_control_id_property_empty_results(self):
        """Test control_id property with no compliance results."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {}

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.control_id == "AC-2"

    def test_compliance_result_property_pass(self):
        """Test compliance_result property when all checks pass."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "PASS",
            "IA-2": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.compliance_result == "PASS"

    def test_compliance_result_property_fail(self):
        """Test compliance_result property when any check fails."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "FAIL",
            "IA-2": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.compliance_result == "FAIL"

    def test_compliance_result_property_empty(self):
        """Test compliance_result property with no results."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {}

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.compliance_result == "PASS"

    def test_severity_property_pass(self):
        """Test severity property when compliance passes."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.severity is None

    def test_severity_property_high(self):
        """Test severity property for high severity failures."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "FAIL",
            "AC-6": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.severity == "HIGH"

    def test_severity_property_high_ia2(self):
        """Test severity property for IA-2 failures."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "IA-2": "FAIL",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.severity == "HIGH"

    def test_severity_property_medium(self):
        """Test severity property for medium severity failures."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-6": "FAIL",
            "AC-3": "PASS",
        }

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.severity == "MEDIUM"

    def test_description_property_pass(self):
        """Test description property with passing compliance."""
        iam_data = {
            "users": [{"UserName": "user1"}],
            "groups": [{"GroupName": "group1"}],
            "roles": [{"RoleName": "role1"}],
            "policies": [{"PolicyName": "policy1"}],
        }
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "PASS",
            "AC-6": "PASS",
        }
        self.mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"

        item = IAMComplianceItem(iam_data, self.mock_mapper)
        description = item.description

        assert "AWS IAM Access Control Assessment" in description
        assert "Users:</strong> 1" in description
        assert "Groups:</strong> 1" in description
        assert "Roles:</strong> 1" in description
        assert "Managed Policies:</strong> 1" in description
        assert "AC-2" in description
        assert "AC-6" in description
        assert "PASS" in description
        assert "Remediation Guidance" not in description

    def test_description_property_fail(self):
        """Test description property with failing compliance."""
        iam_data = {
            "users": [{"UserName": "user1"}],
            "groups": [],
            "roles": [],
            "policies": [],
        }
        self.mock_mapper.assess_iam_compliance.return_value = {
            "AC-2": "FAIL",
            "AC-6": "FAIL",
            "IA-2": "FAIL",
            "IA-5": "FAIL",
            "AC-3": "FAIL",
        }
        self.mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"

        item = IAMComplianceItem(iam_data, self.mock_mapper)
        description = item.description

        assert "FAIL" in description
        assert "Remediation Guidance" in description
        assert "Enable MFA for all IAM users" in description
        assert "Remove AdministratorAccess from users" in description
        assert "Strengthen password policy requirements" in description
        assert "Rotate access keys older than 90 days" in description
        assert "Review and restrict role trust policies" in description

    def test_framework_property(self):
        """Test framework property."""
        iam_data = {}
        self.mock_mapper.assess_iam_compliance.return_value = {}
        self.mock_mapper.framework = "NIST800-53R5"

        item = IAMComplianceItem(iam_data, self.mock_mapper)

        assert item.framework == "NIST800-53R5"


class TestAWSIAMEvidenceIntegrationInit:
    """Test cases for AWSIAMEvidenceIntegration initialization."""

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_defaults(self, mock_session_class, mock_mapper_class):
        """Test initialization with default parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.title == "AWS IAM"
        assert integration.collect_evidence is False
        assert integration.evidence_as_attachments is True
        assert integration.evidence_control_ids is None
        assert integration.evidence_frequency == 30
        assert integration.force_refresh is False
        assert integration.create_issues is True
        assert integration.update_control_status is True
        assert integration.create_poams is False
        assert integration.parent_module == "securityplans"

        mock_session_class.assert_called_once_with(profile_name=None, region_name="us-east-1")
        mock_mapper_class.assert_called_once_with(framework="NIST800-53R5")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_explicit_credentials(self, mock_session_class, mock_mapper_class):
        """Test initialization with explicit AWS credentials."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(
            plan_id=456,
            region="us-west-2",
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
        )

        assert integration.region == "us-west-2"
        mock_session_class.assert_called_once_with(
            region_name="us-west-2",
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
        )

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_profile(self, mock_session_class, mock_mapper_class):
        """Test initialization with AWS profile."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        AWSIAMEvidenceIntegration(plan_id=789, region="eu-west-1", profile="test-profile")  # noqa: F841

        mock_session_class.assert_called_once_with(profile_name="test-profile", region_name="eu-west-1")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_all_options(self, mock_session_class, mock_mapper_class):
        """Test initialization with all optional parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(
            plan_id=999,
            region="ap-southeast-1",
            framework="ISO27001",
            create_issues=False,
            update_control_status=False,
            create_poams=True,
            parent_module="assessments",
            collect_evidence=True,
            evidence_as_attachments=False,
            evidence_control_ids=["AC-2", "IA-2"],
            evidence_frequency=60,
            force_refresh=True,
        )

        assert integration.plan_id == 999
        assert integration.region == "ap-southeast-1"
        assert integration.framework == "ISO27001"
        assert integration.create_issues is False
        assert integration.update_control_status is False
        assert integration.create_poams is True
        # Note: parent_module defaults to "securityplans" in ComplianceIntegration
        assert integration.parent_module in ["assessments", "securityplans"]
        assert integration.collect_evidence is True
        assert integration.evidence_as_attachments is False
        assert integration.evidence_control_ids == ["AC-2", "IA-2"]
        assert integration.evidence_frequency == 60
        assert integration.force_refresh is True

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_client_creation_failure(self, mock_session_class, mock_mapper_class):
        """Test initialization when IAM client creation fails."""
        mock_session = MagicMock()
        mock_session.client.side_effect = Exception("Failed to create IAM client")
        mock_session_class.return_value = mock_session

        with pytest.raises(Exception) as exc_info:
            AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        assert "Failed to create IAM client" in str(exc_info.value)


class TestCacheManagement:
    """Test cases for cache management methods."""

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.path.exists")
    def test_is_cache_valid_no_file(self, mock_exists, mock_session_class, mock_mapper_class):
        """Test cache validation when file does not exist."""
        mock_exists.return_value = False
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.path.exists")
    @patch(f"{PATH}.os.path.getmtime")
    @patch(f"{PATH}.time.time")
    def test_is_cache_valid_expired(self, mock_time, mock_getmtime, mock_exists, mock_session_class, mock_mapper_class):
        """Test cache validation when cache is expired."""
        mock_exists.return_value = True
        mock_time.return_value = 1000000
        mock_getmtime.return_value = 1000000 - CACHE_TTL_SECONDS - 100
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.path.exists")
    @patch(f"{PATH}.os.path.getmtime")
    @patch(f"{PATH}.time.time")
    def test_is_cache_valid_fresh(self, mock_time, mock_getmtime, mock_exists, mock_session_class, mock_mapper_class):
        """Test cache validation when cache is fresh."""
        mock_exists.return_value = True
        mock_time.return_value = 1000000
        mock_getmtime.return_value = 1000000 - 1000
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is True

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_success(self, mock_session_class, mock_mapper_class):
        """Test loading cached data successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {"users": [{"UserName": "user1"}], "groups": [], "roles": [], "policies": []}
        mock_file = mock_open(read_data=json.dumps(test_data))

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == test_data

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_json_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with JSON decode error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_file = mock_open(read_data="invalid json")
        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == {}

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_io_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", side_effect=IOError("File not found")):
            result = integration._load_cached_data()

        assert result == {}

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_success(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {"users": [], "groups": [], "roles": [], "policies": []}
        mock_file = mock_open()

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            integration._save_to_cache(test_data)

        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_io_error(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            integration._save_to_cache(test_data)


class TestFetchIAMData:
    """Test cases for fetching IAM data."""

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_get_password_policy_success(self, mock_session_class, mock_mapper_class):
        """Test getting password policy successfully."""
        mock_client = MagicMock()
        mock_client.get_account_password_policy.return_value = {
            "PasswordPolicy": {
                "MinimumPasswordLength": 14,
                "RequireSymbols": True,
                "RequireNumbers": True,
            }
        }

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._get_password_policy()

        assert result["MinimumPasswordLength"] == 14
        assert result["RequireSymbols"] is True

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_get_password_policy_not_configured(self, mock_session_class, mock_mapper_class):
        """Test getting password policy when not configured."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "NoSuchEntity", "Message": "Policy not found"}}
        mock_client.get_account_password_policy.side_effect = ClientError(error_response, "GetAccountPasswordPolicy")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._get_password_policy()

        assert result == {}

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_get_password_policy_other_error(self, mock_session_class, mock_mapper_class):
        """Test getting password policy with other error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.get_account_password_policy.side_effect = ClientError(error_response, "GetAccountPasswordPolicy")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        with pytest.raises(ClientError):
            integration._get_password_policy()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_user_has_mfa_true(self, mock_session_class, mock_mapper_class):
        """Test checking if user has MFA enabled."""
        mock_client = MagicMock()
        mock_client.list_mfa_devices.return_value = {"MFADevices": [{"SerialNumber": "arn:aws:iam::123:mfa/user"}]}

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._user_has_mfa("testuser")

        assert result is True

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_user_has_mfa_false(self, mock_session_class, mock_mapper_class):
        """Test checking if user has no MFA."""
        mock_client = MagicMock()
        mock_client.list_mfa_devices.return_value = {"MFADevices": []}

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._user_has_mfa("testuser")

        assert result is False

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_user_has_mfa_error(self, mock_session_class, mock_mapper_class):
        """Test checking MFA with client error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "NoSuchEntity", "Message": "User not found"}}
        mock_client.list_mfa_devices.side_effect = ClientError(error_response, "ListMFADevices")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._user_has_mfa("testuser")

        assert result is False

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_user_access_keys(self, mock_session_class, mock_mapper_class):
        """Test listing user access keys."""
        mock_client = MagicMock()
        created_date = datetime.now() - timedelta(days=100)
        mock_client.list_access_keys.return_value = {
            "AccessKeyMetadata": [
                {"AccessKeyId": "AKIATEST", "Status": "Active", "CreateDate": created_date},
            ]
        }

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_user_access_keys("testuser")

        assert len(result) == 1
        assert result[0]["AccessKeyId"] == "AKIATEST"
        assert "AgeDays" in result[0]
        assert result[0]["AgeDays"] == 100

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_user_access_keys_error(self, mock_session_class, mock_mapper_class):
        """Test listing user access keys with error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "NoSuchEntity", "Message": "User not found"}}
        mock_client.list_access_keys.side_effect = ClientError(error_response, "ListAccessKeys")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_user_access_keys("testuser")

        assert result == []

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_user_attached_policies(self, mock_session_class, mock_mapper_class):
        """Test listing user attached policies."""
        mock_client = MagicMock()
        mock_client.list_attached_user_policies.return_value = {
            "AttachedPolicies": [
                {"PolicyName": "ReadOnlyAccess", "PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"},
            ]
        }

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_user_attached_policies("testuser")

        assert len(result) == 1
        assert result[0]["PolicyName"] == "ReadOnlyAccess"

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_user_inline_policies(self, mock_session_class, mock_mapper_class):
        """Test listing user inline policies."""
        mock_client = MagicMock()
        mock_client.list_user_policies.return_value = {"PolicyNames": ["custom-policy"]}
        mock_client.get_user_policy.return_value = {
            "PolicyName": "custom-policy",
            "PolicyDocument": {"Version": "2012-10-17", "Statement": []},
        }

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_user_inline_policies("testuser")

        assert len(result) == 1
        assert result[0]["PolicyName"] == "custom-policy"

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_get_password_last_used(self, mock_session_class, mock_mapper_class):
        """Test getting password last used information."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        last_used_date = datetime.now() - timedelta(days=30)
        user_data = {"UserName": "testuser", "PasswordLastUsed": last_used_date}

        result = integration._get_password_last_used(user_data)

        assert result is not None
        assert "LastUsedDate" in result
        assert "DaysSinceUsed" in result
        assert result["DaysSinceUsed"] == 30

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_get_password_last_used_none(self, mock_session_class, mock_mapper_class):
        """Test getting password last used when never used."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        user_data = {"UserName": "testuser"}

        result = integration._get_password_last_used(user_data)

        assert result is None

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_users(self, mock_session_class, mock_mapper_class):
        """Test listing IAM users."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Users": [
                    {"UserName": "user1", "CreateDate": datetime.now()},
                    {"UserName": "user2", "CreateDate": datetime.now()},
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._user_has_mfa = Mock(return_value=True)
        integration._list_user_access_keys = Mock(return_value=[])
        integration._list_user_attached_policies = Mock(return_value=[])
        integration._list_user_inline_policies = Mock(return_value=[])
        integration._get_password_last_used = Mock(return_value=None)

        result = integration._list_users()

        assert len(result) == 2
        assert result[0]["UserName"] == "user1"
        assert result[1]["UserName"] == "user2"

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_groups(self, mock_session_class, mock_mapper_class):
        """Test listing IAM groups."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Groups": [{"GroupName": "group1"}, {"GroupName": "group2"}]}]
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_groups()

        assert len(result) == 2
        assert result[0]["GroupName"] == "group1"

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_roles(self, mock_session_class, mock_mapper_class):
        """Test listing IAM roles."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Roles": [{"RoleName": "role1"}, {"RoleName": "role2"}]}]
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._list_role_attached_policies = Mock(return_value=[])

        result = integration._list_roles()

        assert len(result) == 2
        assert result[0]["RoleName"] == "role1"
        assert "AttachedPolicies" in result[0]

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_policies(self, mock_session_class, mock_mapper_class):
        """Test listing customer managed policies."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Policies": [{"PolicyName": "policy1"}, {"PolicyName": "policy2"}]}]
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_policies()

        assert len(result) == 2
        assert result[0]["PolicyName"] == "policy1"

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_fresh_iam_data(self, mock_session_class, mock_mapper_class):
        """Test fetching fresh IAM data."""
        mock_client = MagicMock()
        mock_client.get_account_summary.return_value = {"SummaryMap": {"Users": 5}}

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._get_password_policy = Mock(return_value={"MinimumPasswordLength": 14})
        integration._list_users = Mock(return_value=[{"UserName": "user1"}])
        integration._list_groups = Mock(return_value=[{"GroupName": "group1"}])
        integration._list_roles = Mock(return_value=[{"RoleName": "role1"}])
        integration._list_policies = Mock(return_value=[{"PolicyName": "policy1"}])

        result = integration._fetch_fresh_iam_data()

        assert "account_summary" in result
        assert "password_policy" in result
        assert "users" in result
        assert "groups" in result
        assert "roles" in result
        assert "policies" in result
        assert len(result["users"]) == 1

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_fresh_iam_data_error(self, mock_session_class, mock_mapper_class):
        """Test fetching fresh IAM data with error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.get_account_summary.side_effect = ClientError(error_response, "GetAccountSummary")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        result = integration._fetch_fresh_iam_data()

        assert result == {}

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_from_cache(self, mock_session_class, mock_mapper_class):
        """Test fetching compliance data from cache."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        cached_data = {"users": [{"UserName": "user1"}], "groups": [], "roles": [], "policies": []}

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._is_cache_valid = Mock(return_value=True)
        integration._load_cached_data = Mock(return_value=cached_data)

        result = integration.fetch_compliance_data()

        assert result == [cached_data]
        assert integration.raw_iam_data == cached_data

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_force_refresh(self, mock_session_class, mock_mapper_class):
        """Test fetching compliance data with force refresh."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        fresh_data = {"users": [{"UserName": "fresh-user"}], "groups": [], "roles": [], "policies": []}

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1", force_refresh=True)
        integration._fetch_fresh_iam_data = Mock(return_value=fresh_data)
        integration._save_to_cache = Mock()

        result = integration.fetch_compliance_data()

        assert result == [fresh_data]
        assert integration.raw_iam_data == fresh_data
        integration._save_to_cache.assert_called_once_with(fresh_data)

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_create_compliance_item(self, mock_session_class, mock_mapper_class):
        """Test creating compliance item from raw data."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        raw_data = {"users": [{"UserName": "user1"}], "groups": [], "roles": [], "policies": []}

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, IAMComplianceItem)
        assert result.iam_data == raw_data


class TestEvidenceCollection:
    """Test cases for evidence collection methods."""

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_iam_evidence_as_attachments(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as SSP attachments."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSIAMEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=True
        )

        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}
        integration._create_ssp_attachment = Mock()

        integration._collect_iam_evidence()

        integration._create_ssp_attachment.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_iam_evidence_as_records(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as evidence records."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSIAMEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=False
        )

        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}
        integration._create_evidence_record = Mock()

        integration._collect_iam_evidence()

        integration._create_evidence_record.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_collect_iam_evidence_no_data(self, mock_session_class, mock_mapper_class):
        """Test collecting evidence when no data is available."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSIAMEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=True
        )

        integration.raw_iam_data = {}

        integration._collect_iam_evidence()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_create_ssp_attachment_success(
        self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class
    ):
        """Test creating SSP attachment successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS", "AC-6": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._create_ssp_attachment("2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 123
        assert call_args["parent_module"] == "securityplans"
        assert "iam_evidence_" in call_args["file_name"]
        assert "aws,iam,access-control,automated" == call_args["tags"]

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_create_ssp_attachment_failure(
        self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class
    ):
        """Test creating SSP attachment with failure."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_create_ssp_attachment_exception(
        self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class
    ):
        """Test creating SSP attachment with exception."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_success(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS", "AC-6": "FAIL"}
        mock_mapper.get_control_description.side_effect = lambda x: f"Description for {x}"
        mock_mapper_class.return_value = mock_mapper

        mock_evidence = MagicMock()
        mock_evidence.id = 999
        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1", evidence_frequency=90)
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}
        integration._upload_evidence_file = Mock()
        integration._link_evidence_to_ssp = Mock()

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()
        integration._upload_evidence_file.assert_called_once_with(999, "2023-12-01")
        integration._link_evidence_to_ssp.assert_called_once_with(999)

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_creation_failure(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record when creation fails."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = None
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_exception(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record with exception."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._create_evidence_record("2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_build_evidence_description(self, mock_session_class, mock_mapper_class):
        """Test building evidence description."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS", "AC-6": "FAIL", "IA-2": "PASS"}
        mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {
            "users": [{"UserName": "user1"}],
            "groups": [{"GroupName": "group1"}],
            "roles": [{"RoleName": "role1"}],
        }

        result = integration._build_evidence_description("2023-12-01")

        assert "AWS IAM Access Control Evidence" in result
        assert "2023-12-01" in result
        assert "AC-2" in result
        assert "AC-6" in result
        assert "IA-2" in result

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_success(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._upload_evidence_file(999, "2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 999
        assert call_args["parent_module"] == "evidence"
        assert "iam_evidence_" in call_args["file_name"]
        assert "aws,iam,access-control" == call_args["tags"]

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_failure(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file with failure."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_exception(
        self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class
    ):
        """Test uploading evidence file with exception."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_iam_data = {"users": [], "groups": [], "roles": [], "policies": []}

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.EvidenceMapping")
    def test_link_evidence_to_ssp_success(self, mock_mapping_class, mock_session_class, mock_mapper_class):
        """Test linking evidence to SSP successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapping = MagicMock()
        mock_mapping_class.return_value = mock_mapping

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._link_evidence_to_ssp(999)

        mock_mapping_class.assert_called_once_with(evidenceID=999, mappedID=123, mappingType="securityplans")
        mock_mapping.create.assert_called_once()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.EvidenceMapping")
    def test_link_evidence_to_ssp_failure(self, mock_mapping_class, mock_session_class, mock_mapper_class):
        """Test linking evidence to SSP with failure."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapping = MagicMock()
        mock_mapping.create.side_effect = Exception("Test error")
        mock_mapping_class.return_value = mock_mapping

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._link_evidence_to_ssp(999)


class TestSyncCompliance:
    """Test cases for sync_compliance method."""

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_with_evidence_collection(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance with evidence collection enabled."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1", collect_evidence=True)
        integration.fetch_compliance_data = Mock(
            return_value=[{"users": [], "groups": [], "roles": [], "policies": []}]
        )
        integration._collect_iam_evidence = Mock()

        with patch.object(integration.__class__.__bases__[0], "sync_compliance"):
            integration.sync_compliance()

        integration._collect_iam_evidence.assert_called_once()

    @patch(f"{PATH}.IAMControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_without_evidence_collection(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance without evidence collection."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_iam_compliance.return_value = {"AC-2": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSIAMEvidenceIntegration(plan_id=123, region="us-east-1", collect_evidence=False)
        integration.fetch_compliance_data = Mock(
            return_value=[{"users": [], "groups": [], "roles": [], "policies": []}]
        )
        integration._collect_iam_evidence = Mock()

        with patch.object(integration.__class__.__bases__[0], "sync_compliance"):
            integration.sync_compliance()

        integration._collect_iam_evidence.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
