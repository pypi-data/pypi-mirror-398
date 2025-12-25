#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Organizations Evidence Integration."""

import gzip
import json
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.org_evidence import (
    OrgComplianceItem,
    AWSOrganizationsEvidenceIntegration,
    ORG_CACHE_FILE,
    CACHE_TTL_SECONDS,
)

PATH = "regscale.integrations.commercial.aws.org_evidence"


class TestOrgComplianceItem:
    """Test cases for OrgComplianceItem class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_mapper = MagicMock()
        self.mock_mapper.framework = "NIST800-53R5"

    def test_init_with_complete_data(self):
        """Test initialization with complete organization data."""
        org_data = {
            "Id": "o-abc123xyz456",
            "Arn": "arn:aws:organizations::123456789012:organization/o-abc123xyz456",
            "MasterAccountId": "123456789012",
            "accounts": [
                {"Id": "111111111111", "Name": "Account1", "Status": "ACTIVE", "Email": "account1@example.com"},
                {"Id": "222222222222", "Name": "Account2", "Status": "ACTIVE", "Email": "account2@example.com"},
            ],
            "organizational_units": [
                {"Id": "ou-abc1-11111111", "Name": "Production"},
                {"Id": "ou-abc1-22222222", "Name": "Development"},
            ],
            "service_control_policies": [
                {"Id": "p-FullAWSAccess", "Name": "FullAWSAccess", "Type": "SERVICE_CONTROL_POLICY"},
                {"Id": "p-DenyS3", "Name": "DenyS3Access", "Type": "SERVICE_CONTROL_POLICY"},
            ],
        }

        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
            "AC-2": "PASS",
            "AC-6": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.org_data == org_data
        assert item.control_mapper == self.mock_mapper
        assert item._org_id == "o-abc123xyz456"
        assert item._org_arn == "arn:aws:organizations::123456789012:organization/o-abc123xyz456"
        assert item._master_account_id == "123456789012"
        assert len(item._accounts) == 2
        assert len(item._ous) == 2
        assert len(item._scps) == 2
        assert item._compliance_results == self.mock_mapper.assess_organization_compliance.return_value

    def test_init_with_minimal_data(self):
        """Test initialization with minimal organization data."""
        org_data = {}

        self.mock_mapper.assess_organization_compliance.return_value = {}

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item._org_id == ""
        assert item._org_arn == ""
        assert item._master_account_id == ""
        assert len(item._accounts) == 0
        assert len(item._ous) == 0
        assert len(item._scps) == 0

    def test_resource_id_property(self):
        """Test resource_id property."""
        org_data = {"Id": "o-testorg123"}
        self.mock_mapper.assess_organization_compliance.return_value = {}

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.resource_id == "o-testorg123"

    def test_resource_name_property(self):
        """Test resource_name property."""
        org_data = {"Id": "o-abc123xyz456789"}
        self.mock_mapper.assess_organization_compliance.return_value = {}

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.resource_name == "AWS Organization o-abc123xyz4..."

    def test_control_id_property_with_failure(self):
        """Test control_id property returns first failed control."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "FAIL",
            "AC-2": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.control_id == "PM-9"

    def test_control_id_property_all_pass(self):
        """Test control_id property when all controls pass."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.control_id == "AC-1"

    def test_control_id_property_empty_results(self):
        """Test control_id property with no compliance results."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {}

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.control_id == "AC-1"

    def test_compliance_result_property_pass(self):
        """Test compliance_result property when all checks pass."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
            "AC-2": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.compliance_result == "PASS"

    def test_compliance_result_property_fail(self):
        """Test compliance_result property when any check fails."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "FAIL",
            "AC-2": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.compliance_result == "FAIL"

    def test_compliance_result_property_empty(self):
        """Test compliance_result property with no results."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {}

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.compliance_result == "PASS"

    def test_severity_property_pass(self):
        """Test severity property when compliance passes."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.severity is None

    def test_severity_property_high_ac1_fail(self):
        """Test severity property for AC-1 failures."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "FAIL",
            "PM-9": "PASS",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.severity == "HIGH"

    def test_severity_property_high_pm9_fail(self):
        """Test severity property for PM-9 failures."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "FAIL",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.severity == "HIGH"

    def test_severity_property_medium_ac6_fail(self):
        """Test severity property for AC-6 failures."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
            "AC-6": "FAIL",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.severity == "MEDIUM"

    def test_severity_property_medium_ac2_fail(self):
        """Test severity property for AC-2 failures."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "AC-2": "FAIL",
        }

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.severity == "MEDIUM"

    def test_description_property_pass(self):
        """Test description property with passing compliance."""
        org_data = {
            "Id": "o-testorg",
            "Arn": "arn:aws:organizations::123456789012:organization/o-testorg",
            "MasterAccountId": "123456789012",
            "accounts": [{"Id": "111111111111"}],
            "organizational_units": [{"Id": "ou-1"}],
            "service_control_policies": [{"Id": "p-1"}],
        }
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "PASS",
            "PM-9": "PASS",
        }
        self.mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"

        item = OrgComplianceItem(org_data, self.mock_mapper)
        description = item.description

        assert "AWS Organizations Governance Assessment" in description
        assert "o-testorg" in description
        assert "123456789012" in description
        assert "Total Accounts:</strong> 1" in description
        assert "Organizational Units:</strong> 1" in description
        assert "Service Control Policies:</strong> 1" in description
        assert "AC-1" in description
        assert "PM-9" in description
        assert "PASS" in description
        assert "Remediation Guidance" not in description

    def test_description_property_fail_with_remediation(self):
        """Test description property with failing compliance and remediation guidance."""
        org_data = {
            "Id": "o-testorg",
            "Arn": "arn:aws:organizations::123456789012:organization/o-testorg",
            "MasterAccountId": "123456789012",
            "accounts": [
                {"Id": "111111111111", "Status": "ACTIVE"},
                {"Id": "222222222222", "Status": "SUSPENDED"},
            ],
            "organizational_units": [{"Id": "ou-root"}],
            "service_control_policies": [{"Id": "p-FullAWSAccess", "Name": "FullAWSAccess"}],
        }
        self.mock_mapper.assess_organization_compliance.return_value = {
            "AC-1": "FAIL",
            "PM-9": "FAIL",
            "AC-2": "FAIL",
            "AC-6": "FAIL",
        }
        self.mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"

        item = OrgComplianceItem(org_data, self.mock_mapper)
        description = item.description

        assert "FAIL" in description
        assert "Remediation Guidance" in description
        assert "Create organizational units (OUs) for governance structure" in description
        assert "Attach Service Control Policies to enforce access controls" in description
        assert "Organize accounts by risk profile" in description
        assert "Review and activate or remove 1 suspended accounts" in description
        assert "Implement least privilege SCPs" in description

    def test_framework_property(self):
        """Test framework property."""
        org_data = {}
        self.mock_mapper.assess_organization_compliance.return_value = {}
        self.mock_mapper.framework = "NIST800-53R5"

        item = OrgComplianceItem(org_data, self.mock_mapper)

        assert item.framework == "NIST800-53R5"


class TestAWSOrganizationsEvidenceIntegrationInit:
    """Test cases for AWSOrganizationsEvidenceIntegration initialization."""

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_defaults(self, mock_session_class, mock_mapper_class):
        """Test initialization with default parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.title == "AWS Organizations"
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

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_explicit_credentials(self, mock_session_class, mock_mapper_class):
        """Test initialization with explicit AWS credentials."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(
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

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_profile(self, mock_session_class, mock_mapper_class):
        """Test initialization with AWS profile."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        AWSOrganizationsEvidenceIntegration(plan_id=789, region="eu-west-1", profile="test-profile")  # noqa: F841

        mock_session_class.assert_called_once_with(profile_name="test-profile", region_name="eu-west-1")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_all_options(self, mock_session_class, mock_mapper_class):
        """Test initialization with all optional parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(
            plan_id=999,
            region="ap-southeast-1",
            framework="ISO27001",
            create_issues=False,
            update_control_status=False,
            create_poams=True,
            parent_module="assessments",
            collect_evidence=True,
            evidence_as_attachments=False,
            evidence_control_ids=["AC-1", "PM-9"],
            evidence_frequency=60,
            force_refresh=True,
        )

        assert integration.plan_id == 999
        assert integration.region == "ap-southeast-1"
        assert integration.framework == "ISO27001"
        assert integration.create_issues is False
        assert integration.update_control_status is False
        assert integration.create_poams is True
        assert integration.collect_evidence is True
        assert integration.evidence_as_attachments is False
        assert integration.evidence_control_ids == ["AC-1", "PM-9"]
        assert integration.evidence_frequency == 60
        assert integration.force_refresh is True

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_client_creation_failure(self, mock_session_class, mock_mapper_class):
        """Test initialization when Organizations client creation fails."""
        mock_session = MagicMock()
        mock_session.client.side_effect = Exception("Failed to create Organizations client")
        mock_session_class.return_value = mock_session

        with pytest.raises(Exception) as exc_info:
            AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        assert "Failed to create Organizations client" in str(exc_info.value)


class TestCacheManagement:
    """Test cases for cache management methods."""

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.path.exists")
    def test_is_cache_valid_no_file(self, mock_exists, mock_session_class, mock_mapper_class):
        """Test cache validation when file does not exist."""
        mock_exists.return_value = False
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.OrgControlMapper")
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

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.OrgControlMapper")
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

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        assert integration._is_cache_valid() is True

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_success(self, mock_session_class, mock_mapper_class):
        """Test loading cached data successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {
            "Id": "o-testorg",
            "accounts": [{"Id": "111111111111"}],
            "organizational_units": [],
            "service_control_policies": [],
        }
        mock_file = mock_open(read_data=json.dumps(test_data))

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == test_data

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_json_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with JSON decode error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_file = mock_open(read_data="invalid json")
        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == {}

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_io_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", side_effect=IOError("File not found")):
            result = integration._load_cached_data()

        assert result == {}

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_success(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {"Id": "o-testorg", "accounts": [], "organizational_units": [], "service_control_policies": []}
        mock_file = mock_open()

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", mock_file):
            integration._save_to_cache(test_data)

        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_io_error(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = {"Id": "o-testorg"}

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            integration._save_to_cache(test_data)


class TestFetchOrganizationData:
    """Test cases for fetching organization data."""

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_organizational_units_success(self, mock_session_class, mock_mapper_class):
        """Test listing organizational units successfully."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = [
            [{"OrganizationalUnits": [{"Id": "ou-1", "Name": "OU1"}]}],
            [{"OrganizationalUnits": []}],
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_client.list_roots.return_value = {"Roots": [{"Id": "r-root"}]}

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_organizational_units()

        assert len(result) == 1
        assert result[0]["Id"] == "ou-1"

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_organizational_units_error(self, mock_session_class, mock_mapper_class):
        """Test listing organizational units with error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.list_roots.side_effect = ClientError(error_response, "ListRoots")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_organizational_units()

        assert result == []

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_service_control_policies_success(self, mock_session_class, mock_mapper_class):
        """Test listing service control policies successfully."""
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {
                "Policies": [
                    {"Id": "p-1", "Name": "Policy1"},
                    {"Id": "p-2", "Name": "Policy2"},
                ]
            }
        ]
        mock_client.get_paginator.return_value = mock_paginator
        mock_client.describe_policy.side_effect = [
            {"Policy": {"Id": "p-1", "Name": "Policy1", "Content": "{}"}},
            {"Policy": {"Id": "p-2", "Name": "Policy2", "Content": "{}"}},
        ]

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_service_control_policies()

        assert len(result) == 2
        assert result[0]["Id"] == "p-1"

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_list_service_control_policies_error(self, mock_session_class, mock_mapper_class):
        """Test listing service control policies with error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = ClientError(error_response, "ListPolicies")
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._list_service_control_policies()

        assert result == []

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_fresh_org_data_success(self, mock_session_class, mock_mapper_class):
        """Test fetching fresh organization data successfully."""
        mock_client = MagicMock()
        mock_client.describe_organization.return_value = {
            "Organization": {
                "Id": "o-testorg",
                "Arn": "arn:aws:organizations::123456789012:organization/o-testorg",
                "MasterAccountId": "123456789012",
            }
        }
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Accounts": [{"Id": "111111111111", "Name": "Account1", "Status": "ACTIVE"}]}
        ]
        mock_client.get_paginator.return_value = mock_paginator

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._list_organizational_units = Mock(return_value=[{"Id": "ou-1"}])
        integration._list_service_control_policies = Mock(return_value=[{"Id": "p-1"}])

        result = integration._fetch_fresh_org_data()

        assert "Id" in result
        assert result["Id"] == "o-testorg"
        assert "accounts" in result
        assert len(result["accounts"]) == 1
        assert "organizational_units" in result
        assert "service_control_policies" in result

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_fresh_org_data_error(self, mock_session_class, mock_mapper_class):
        """Test fetching fresh organization data with error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        mock_client.describe_organization.side_effect = ClientError(error_response, "DescribeOrganization")

        mock_session = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        result = integration._fetch_fresh_org_data()

        assert result == {}

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_from_cache(self, mock_session_class, mock_mapper_class):
        """Test fetching compliance data from cache."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        cached_data = {"Id": "o-testorg", "accounts": [], "organizational_units": [], "service_control_policies": []}

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration._is_cache_valid = Mock(return_value=True)
        integration._load_cached_data = Mock(return_value=cached_data)

        result = integration.fetch_compliance_data()

        assert result == [cached_data]
        assert integration.raw_org_data == cached_data

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_force_refresh(self, mock_session_class, mock_mapper_class):
        """Test fetching compliance data with force refresh."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        fresh_data = {"Id": "o-freshorg", "accounts": [], "organizational_units": [], "service_control_policies": []}

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1", force_refresh=True)
        integration._fetch_fresh_org_data = Mock(return_value=fresh_data)
        integration._save_to_cache = Mock()

        result = integration.fetch_compliance_data()

        assert result == [fresh_data]
        assert integration.raw_org_data == fresh_data
        integration._save_to_cache.assert_called_once_with(fresh_data)

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_create_compliance_item(self, mock_session_class, mock_mapper_class):
        """Test creating compliance item from raw data."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        raw_data = {"Id": "o-testorg", "accounts": [], "organizational_units": [], "service_control_policies": []}

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, OrgComplianceItem)
        assert result.org_data == raw_data


class TestEvidenceCollection:
    """Test cases for evidence collection methods."""

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_org_evidence_as_attachments(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as SSP attachments."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSOrganizationsEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=True
        )

        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }
        integration._create_ssp_attachment = Mock()

        integration._collect_org_evidence()

        integration._create_ssp_attachment.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_org_evidence_as_records(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as evidence records."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSOrganizationsEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=False
        )

        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }
        integration._create_evidence_record = Mock()

        integration._collect_org_evidence()

        integration._create_evidence_record.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_collect_org_evidence_no_data(self, mock_session_class, mock_mapper_class):
        """Test collecting evidence when no data is available."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSOrganizationsEvidenceIntegration(
            plan_id=123, region="us-east-1", collect_evidence=True, evidence_as_attachments=True
        )

        integration.raw_org_data = {}

        integration._collect_org_evidence()

    @patch(f"{PATH}.OrgControlMapper")
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
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS", "PM-9": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._create_ssp_attachment("2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 123
        assert call_args["parent_module"] == "securityplans"
        assert "org_evidence_" in call_args["file_name"]
        assert "aws,organizations,governance,automated" == call_args["tags"]

    @patch(f"{PATH}.OrgControlMapper")
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
        mock_mapper.assess_organization_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
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
        mock_mapper.assess_organization_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_success(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS", "PM-9": "FAIL"}
        mock_mapper.get_control_description.side_effect = lambda x: f"Description for {x}"
        mock_mapper_class.return_value = mock_mapper

        mock_evidence = MagicMock()
        mock_evidence.id = 999
        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1", evidence_frequency=90)
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }
        integration._upload_evidence_file = Mock()
        integration._link_evidence_to_ssp = Mock()

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()
        integration._upload_evidence_file.assert_called_once_with(999, "2023-12-01")
        integration._link_evidence_to_ssp.assert_called_once_with(999)

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_creation_failure(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record when creation fails."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = None
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_exception(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record with exception."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._create_evidence_record("2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_build_evidence_description(self, mock_session_class, mock_mapper_class):
        """Test building evidence description."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS", "PM-9": "FAIL", "AC-2": "PASS"}
        mock_mapper.get_control_description.side_effect = lambda x: f"{x} Description"
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "accounts": [{"Id": "111111111111"}],
            "organizational_units": [{"Id": "ou-1"}],
            "service_control_policies": [{"Id": "p-1"}],
        }

        result = integration._build_evidence_description("2023-12-01")

        assert "AWS Organizations Governance Evidence" in result
        assert "2023-12-01" in result
        assert "AC-1" in result
        assert "PM-9" in result
        assert "AC-2" in result

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_success(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._upload_evidence_file(999, "2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 999
        assert call_args["parent_module"] == "evidence"
        assert "org_evidence_" in call_args["file_name"]
        assert "aws,organizations,governance" == call_args["tags"]

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_failure(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file with failure."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
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
        mock_mapper.assess_organization_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")
        integration.raw_org_data = {
            "Id": "o-testorg",
            "accounts": [],
            "organizational_units": [],
            "service_control_policies": [],
        }

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.EvidenceMapping")
    def test_link_evidence_to_ssp_success(self, mock_mapping_class, mock_session_class, mock_mapper_class):
        """Test linking evidence to SSP successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapping = MagicMock()
        mock_mapping_class.return_value = mock_mapping

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._link_evidence_to_ssp(999)

        mock_mapping_class.assert_called_once_with(evidenceID=999, mappedID=123, mappingType="securityplans")
        mock_mapping.create.assert_called_once()

    @patch(f"{PATH}.OrgControlMapper")
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

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._link_evidence_to_ssp(999)


class TestSyncCompliance:
    """Test cases for sync_compliance method."""

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_with_evidence_collection(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance with evidence collection enabled."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1", collect_evidence=True)
        integration.fetch_compliance_data = Mock(
            return_value=[
                {"Id": "o-testorg", "accounts": [], "organizational_units": [], "service_control_policies": []}
            ]
        )
        integration._collect_org_evidence = Mock()

        with patch.object(integration.__class__.__bases__[0], "sync_compliance"):
            integration.sync_compliance()

        integration._collect_org_evidence.assert_called_once()

    @patch(f"{PATH}.OrgControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_without_evidence_collection(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance without evidence collection."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_organization_compliance.return_value = {"AC-1": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSOrganizationsEvidenceIntegration(plan_id=123, region="us-east-1", collect_evidence=False)
        integration.fetch_compliance_data = Mock(
            return_value=[
                {"Id": "o-testorg", "accounts": [], "organizational_units": [], "service_control_policies": []}
            ]
        )
        integration._collect_org_evidence = Mock()

        with patch.object(integration.__class__.__bases__[0], "sync_compliance"):
            integration.sync_compliance()

        integration._collect_org_evidence.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
