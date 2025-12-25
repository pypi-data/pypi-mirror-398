#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS KMS Evidence Integration."""

import gzip
import json
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.kms_evidence import (
    AWSKMSEvidenceIntegration,
    KMSComplianceItem,
    CACHE_TTL_SECONDS,
    KMS_CACHE_FILE,
)

PATH = "regscale.integrations.commercial.aws.kms_evidence"


class TestKMSComplianceItem:
    """Test cases for KMSComplianceItem class."""

    @patch(f"{PATH}.KMSControlMapper")
    def test_init_with_complete_data(self, mock_mapper_class):
        """Test initialization with complete KMS key data."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "PASS",
            "SC-28": "PASS",
        }
        mock_mapper.get_control_description.side_effect = lambda x: f"{x} description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "12345678-1234-1234-1234-123456789012",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
            "KeyState": "Enabled",
            "RotationEnabled": True,
            "KeyManager": "CUSTOMER",
            "Description": "Test KMS Key",
            "Tags": [{"TagKey": "Name", "TagValue": "TestKey"}],
        }

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.resource_id == "12345678-1234-1234-1234-123456789012"
        assert "TestKey" in item.resource_name
        assert item.control_id in ["SC-12", "SC-13", "SC-28"]
        assert item.compliance_result == "PASS"
        assert item.severity is None
        assert item.framework == "NIST800-53R5"

    @patch(f"{PATH}.KMSControlMapper")
    def test_init_with_minimal_data(self, mock_mapper_class):
        """Test initialization with minimal KMS key data."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper.get_control_description.return_value = "Test description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.resource_id == ""
        assert "KMS Key" in item.resource_name
        assert item.control_id == "SC-12"
        assert item.compliance_result == "PASS"

    @patch(f"{PATH}.KMSControlMapper")
    def test_resource_name_with_tag(self, mock_mapper_class):
        """Test resource name extraction with tags."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "12345678-1234-1234-1234-123456789012",
            "Tags": [{"TagKey": "Name", "TagValue": "ProductionKey"}],
        }

        item = KMSComplianceItem(key_data, mock_mapper)

        assert "ProductionKey" in item.resource_name
        assert "12345678" in item.resource_name

    @patch(f"{PATH}.KMSControlMapper")
    def test_resource_name_with_description(self, mock_mapper_class):
        """Test resource name extraction with description."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "12345678-1234-1234-1234-123456789012",
            "Description": "Key for encrypting sensitive data in production environment",
        }

        item = KMSComplianceItem(key_data, mock_mapper)

        assert "Key for encrypting sensitive data in production" in item.resource_name
        assert "12345678" in item.resource_name

    @patch(f"{PATH}.KMSControlMapper")
    def test_control_id_first_failing_control(self, mock_mapper_class):
        """Test control_id property returns first failing control."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "FAIL",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.control_id == "SC-13"

    @patch(f"{PATH}.KMSControlMapper")
    def test_control_id_all_passing(self, mock_mapper_class):
        """Test control_id property when all controls pass."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "PASS",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.control_id in ["SC-12", "SC-13", "SC-28"]

    @patch(f"{PATH}.KMSControlMapper")
    def test_compliance_result_fail(self, mock_mapper_class):
        """Test compliance_result property with failures."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "FAIL",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.compliance_result == "FAIL"

    @patch(f"{PATH}.KMSControlMapper")
    def test_compliance_result_pass(self, mock_mapper_class):
        """Test compliance_result property with all passing."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "PASS",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.compliance_result == "PASS"

    @patch(f"{PATH}.KMSControlMapper")
    def test_severity_sc12_failure(self, mock_mapper_class):
        """Test severity for SC-12 failure."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "FAIL",
            "SC-13": "PASS",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.severity == "HIGH"

    @patch(f"{PATH}.KMSControlMapper")
    def test_severity_sc13_failure(self, mock_mapper_class):
        """Test severity for SC-13 failure."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "FAIL",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.severity == "MEDIUM"

    @patch(f"{PATH}.KMSControlMapper")
    def test_severity_sc28_failure(self, mock_mapper_class):
        """Test severity for SC-28 failure."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "PASS",
            "SC-28": "FAIL",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.severity == "MEDIUM"

    @patch(f"{PATH}.KMSControlMapper")
    def test_severity_pass(self, mock_mapper_class):
        """Test severity when all controls pass."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "PASS",
            "SC-13": "PASS",
            "SC-28": "PASS",
        }
        mock_mapper.framework = "NIST800-53R5"

        key_data = {"KeyId": "test-key"}

        item = KMSComplianceItem(key_data, mock_mapper)

        assert item.severity is None

    @patch(f"{PATH}.KMSControlMapper")
    def test_description_property(self, mock_mapper_class):
        """Test description property generates HTML."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "FAIL",
            "SC-13": "PASS",
        }
        mock_mapper.get_control_description.side_effect = lambda x: f"{x} description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "12345678-1234-1234-1234-123456789012",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
            "KeyState": "Enabled",
            "RotationEnabled": False,
            "KeyManager": "CUSTOMER",
            "Description": "Test key",
        }

        item = KMSComplianceItem(key_data, mock_mapper)
        description = item.description

        assert "AWS KMS Key Compliance Assessment" in description
        assert "12345678-1234-1234-1234-123456789012" in description
        assert "Rotation Enabled" in description
        assert "No" in description
        assert "Control Compliance Results" in description
        assert "SC-12" in description
        assert "FAIL" in description
        assert "Remediation Guidance" in description

    @patch(f"{PATH}.KMSControlMapper")
    def test_description_with_remediation_rotation(self, mock_mapper_class):
        """Test description includes rotation remediation."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "FAIL",
        }
        mock_mapper.get_control_description.return_value = "SC-12 description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "test-key",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/test-key",
            "KeyState": "Enabled",
            "RotationEnabled": False,
            "KeyManager": "CUSTOMER",
        }

        item = KMSComplianceItem(key_data, mock_mapper)
        description = item.description

        assert "Enable automatic key rotation" in description

    @patch(f"{PATH}.KMSControlMapper")
    def test_description_with_remediation_key_state(self, mock_mapper_class):
        """Test description includes key state remediation."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-12": "FAIL",
        }
        mock_mapper.get_control_description.return_value = "SC-12 description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "test-key",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/test-key",
            "KeyState": "PendingDeletion",
            "RotationEnabled": True,
            "KeyManager": "CUSTOMER",
        }

        item = KMSComplianceItem(key_data, mock_mapper)
        description = item.description

        assert "Key is PendingDeletion" in description
        assert "review key lifecycle" in description

    @patch(f"{PATH}.KMSControlMapper")
    def test_description_with_remediation_key_spec(self, mock_mapper_class):
        """Test description includes key spec remediation."""
        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {
            "SC-13": "FAIL",
        }
        mock_mapper.get_control_description.return_value = "SC-13 description"
        mock_mapper.framework = "NIST800-53R5"

        key_data = {
            "KeyId": "test-key",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/test-key",
            "KeyState": "Enabled",
            "RotationEnabled": True,
            "KeyManager": "CUSTOMER",
            "KeySpec": "RSA_1024",
        }

        item = KMSComplianceItem(key_data, mock_mapper)
        description = item.description

        assert "Review key specification" in description
        assert "RSA_1024" in description
        assert "FIPS-validated" in description

    @patch(f"{PATH}.KMSControlMapper")
    def test_extract_region_from_arn(self, mock_mapper_class):
        """Test extracting region from ARN."""
        result = KMSComplianceItem._extract_region_from_arn("arn:aws:kms:us-west-2:123456789012:key/test-key")
        assert result == "us-west-2"

    @patch(f"{PATH}.KMSControlMapper")
    def test_extract_region_from_invalid_arn(self, mock_mapper_class):
        """Test extracting region from invalid ARN."""
        result = KMSComplianceItem._extract_region_from_arn("invalid-arn")
        assert result == "unknown"

    @patch(f"{PATH}.KMSControlMapper")
    def test_extract_account_from_arn(self, mock_mapper_class):
        """Test extracting account from ARN."""
        result = KMSComplianceItem._extract_account_from_arn("arn:aws:kms:us-east-1:123456789012:key/test-key")
        assert result == "123456789012"

    @patch(f"{PATH}.KMSControlMapper")
    def test_extract_account_from_invalid_arn(self, mock_mapper_class):
        """Test extracting account from invalid ARN."""
        result = KMSComplianceItem._extract_account_from_arn("invalid-arn")
        assert result == "unknown"


class TestAWSKMSEvidenceIntegrationInit:
    """Test cases for AWSKMSEvidenceIntegration initialization."""

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_defaults(self, mock_session_class, mock_mapper_class):
        """Test initialization with default parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.title == "AWS KMS"
        assert integration.collect_evidence is False
        assert integration.evidence_as_attachments is True
        assert integration.evidence_control_ids is None
        assert integration.evidence_frequency == 30
        assert integration.force_refresh is False
        assert integration.account_id is None
        assert integration.tags == {}
        assert integration.raw_kms_data == []

        mock_session_class.assert_called_once()
        mock_mapper_class.assert_called_once_with(framework="NIST800-53R5")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_explicit_credentials(self, mock_session_class, mock_mapper_class):
        """Test initialization with explicit AWS credentials."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(
            plan_id=123,
            region="us-west-2",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            aws_session_token="session-token",
        )

        assert integration.region == "us-west-2"

        mock_session_class.assert_called_once_with(
            region_name="us-west-2",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            aws_session_token="session-token",
        )

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_profile(self, mock_session_class, mock_mapper_class):
        """Test initialization with AWS profile."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        AWSKMSEvidenceIntegration(plan_id=123, profile="test-profile")

        mock_session_class.assert_called_once_with(profile_name="test-profile", region_name="us-east-1")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_with_all_options(self, mock_session_class, mock_mapper_class):
        """Test initialization with all optional parameters."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(
            plan_id=456,
            region="eu-west-1",
            framework="ISO27001",
            create_issues=False,
            update_control_status=False,
            create_poams=True,
            parent_module="assessments",
            collect_evidence=True,
            evidence_as_attachments=False,
            evidence_control_ids=["SC-12", "SC-13"],
            evidence_frequency=60,
            force_refresh=True,
            account_id="123456789012",
            tags={"Environment": "Production"},
        )

        assert integration.plan_id == 456
        assert integration.region == "eu-west-1"
        assert integration.framework == "ISO27001"
        assert integration.create_issues is False
        assert integration.update_control_status is False
        assert integration.create_poams is True
        assert integration.collect_evidence is True
        assert integration.evidence_as_attachments is False
        assert integration.evidence_control_ids == ["SC-12", "SC-13"]
        assert integration.evidence_frequency == 60
        assert integration.force_refresh is True
        assert integration.account_id == "123456789012"
        assert integration.tags == {"Environment": "Production"}

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_init_client_creation_failure(self, mock_session_class, mock_mapper_class):
        """Test initialization when client creation fails."""
        mock_session = MagicMock()
        mock_session.client.side_effect = Exception("Failed to create KMS client")
        mock_session_class.return_value = mock_session

        with pytest.raises(Exception) as exc_info:
            AWSKMSEvidenceIntegration(plan_id=123)

        assert "Failed to create KMS client" in str(exc_info.value)


class TestCacheManagement:
    """Test cases for cache management methods."""

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.path.exists")
    def test_is_cache_valid_no_file(self, mock_exists, mock_session_class, mock_mapper_class):
        """Test cache validation when file does not exist."""
        mock_exists.return_value = False
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.KMSControlMapper")
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

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        assert integration._is_cache_valid() is False

    @patch(f"{PATH}.KMSControlMapper")
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

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        assert integration._is_cache_valid() is True

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_success(self, mock_session_class, mock_mapper_class):
        """Test loading cached data successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [{"KeyId": "test-key", "KeyState": "Enabled"}]
        mock_file = mock_open(read_data=json.dumps(test_data))

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == test_data

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_json_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with JSON decode error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_file = mock_open(read_data="invalid json")
        integration = AWSKMSEvidenceIntegration(plan_id=123)

        with patch("builtins.open", mock_file):
            result = integration._load_cached_data()

        assert result == []

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_load_cached_data_io_error(self, mock_session_class, mock_mapper_class):
        """Test loading cached data with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        with patch("builtins.open", side_effect=IOError("File not found")):
            result = integration._load_cached_data()

        assert result == []

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_success(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [{"KeyId": "test-key"}]
        mock_file = mock_open()

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        with patch("builtins.open", mock_file):
            integration._save_to_cache(test_data)

        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.os.makedirs")
    def test_save_to_cache_io_error(self, mock_makedirs, mock_session_class, mock_mapper_class):
        """Test saving data to cache with IO error."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [{"KeyId": "test-key"}]

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            integration._save_to_cache(test_data)


class TestFetchKMSData:
    """Test cases for fetching KMS data."""

    @patch("regscale.integrations.commercial.aws.inventory.resources.kms.KMSCollector")
    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_fresh_kms_data(self, mock_session_class, mock_mapper_class, mock_collector_class):
        """Test fetching fresh KMS data."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [
            {"KeyId": "key-1", "KeyState": "Enabled"},
            {"KeyId": "key-2", "KeyState": "Enabled"},
        ]

        mock_collector = MagicMock()
        mock_collector.collect.return_value = {"Keys": test_data}
        mock_collector_class.return_value = mock_collector

        integration = AWSKMSEvidenceIntegration(plan_id=123, region="us-east-1")

        result = integration._fetch_fresh_kms_data()

        assert len(result) == 2
        assert result[0]["KeyId"] == "key-1"
        mock_collector_class.assert_called_once()

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_with_valid_cache(self, mock_session_class, mock_mapper_class):
        """Test fetching compliance data when cache is valid."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [{"KeyId": "cached-key"}]

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration._is_cache_valid = Mock(return_value=True)
        integration._load_cached_data = Mock(return_value=test_data)

        result = integration.fetch_compliance_data()

        assert result == test_data
        assert integration.raw_kms_data == test_data

    @patch("regscale.integrations.commercial.aws.inventory.resources.kms.KMSCollector")
    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_force_refresh(self, mock_session_class, mock_mapper_class, mock_collector_class):
        """Test fetching compliance data with force refresh."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        test_data = [{"KeyId": "fresh-key"}]

        mock_collector = MagicMock()
        mock_collector.collect.return_value = {"Keys": test_data}
        mock_collector_class.return_value = mock_collector

        integration = AWSKMSEvidenceIntegration(plan_id=123, force_refresh=True)
        integration._save_to_cache = Mock()

        result = integration.fetch_compliance_data()

        assert result == test_data
        integration._save_to_cache.assert_called_once_with(test_data)

    @patch("regscale.integrations.commercial.aws.inventory.resources.kms.KMSCollector")
    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_fetch_compliance_data_client_error(self, mock_session_class, mock_mapper_class, mock_collector_class):
        """Test fetching compliance data with ClientError."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_collector = MagicMock()
        mock_collector.collect.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListKeys"
        )
        mock_collector_class.return_value = mock_collector

        integration = AWSKMSEvidenceIntegration(plan_id=123, force_refresh=True)

        result = integration.fetch_compliance_data()

        assert result == []


class TestComplianceItem:
    """Test cases for compliance item creation."""

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_create_compliance_item(self, mock_session_class, mock_mapper_class):
        """Test creating a compliance item from raw data."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {"SC-12": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        raw_data = {"KeyId": "test-key", "KeyState": "Enabled"}

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, KMSComplianceItem)
        assert result.resource_id == "test-key"

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_map_resource_type_to_asset_type(self, mock_session_class, mock_mapper_class):
        """Test mapping resource type to asset type."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        mock_item = MagicMock()
        result = integration._map_resource_type_to_asset_type(mock_item)

        assert result == "AWS KMS Key"


class TestSyncCompliance:
    """Test cases for sync_compliance method."""

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_without_evidence(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance without evidence collection."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123, collect_evidence=False)

        with patch.object(integration.__class__.__bases__[0], "sync_compliance") as mock_super_sync:
            integration.sync_compliance()

        mock_super_sync.assert_called_once()

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_sync_compliance_with_evidence(self, mock_session_class, mock_mapper_class):
        """Test sync_compliance with evidence collection."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123, collect_evidence=True)
        integration._collect_kms_evidence = Mock()

        with patch.object(integration.__class__.__bases__[0], "sync_compliance"):
            integration.sync_compliance()

        integration._collect_kms_evidence.assert_called_once()


class TestEvidenceCollection:
    """Test cases for evidence collection methods."""

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_kms_evidence_as_attachments(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as SSP attachments."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSKMSEvidenceIntegration(plan_id=123, collect_evidence=True, evidence_as_attachments=True)

        integration.raw_kms_data = [{"KeyId": "test-key"}]
        integration._create_ssp_attachment = Mock()

        integration._collect_kms_evidence()

        integration._create_ssp_attachment.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.get_current_datetime")
    def test_collect_kms_evidence_as_records(self, mock_get_datetime, mock_session_class, mock_mapper_class):
        """Test collecting evidence as evidence records."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_get_datetime.return_value = "2023-12-01"

        integration = AWSKMSEvidenceIntegration(plan_id=123, collect_evidence=True, evidence_as_attachments=False)

        integration.raw_kms_data = [{"KeyId": "test-key"}]
        integration._create_evidence_record = Mock()

        integration._collect_kms_evidence()

        integration._create_evidence_record.assert_called_once_with("2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_collect_kms_evidence_no_data(self, mock_session_class, mock_mapper_class):
        """Test collecting evidence when no data is available."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        integration = AWSKMSEvidenceIntegration(plan_id=123, collect_evidence=True)

        integration.raw_kms_data = []

        integration._collect_kms_evidence()

    @patch(f"{PATH}.KMSControlMapper")
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
        mock_mapper.assess_key_compliance.return_value = {"SC-12": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSKMSEvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")
        integration.raw_kms_data = [{"KeyId": "test-key"}]

        integration._create_ssp_attachment("2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 123
        assert call_args["parent_module"] == "securityplans"
        assert "kms_evidence_123456789012_" in call_args["file_name"]
        assert call_args["file_name"].endswith(".jsonl.gz")

    @patch(f"{PATH}.KMSControlMapper")
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
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = [{"KeyId": "test-key"}]

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
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
        mock_mapper.assess_key_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = [{"KeyId": "test-key"}]

        integration._create_ssp_attachment("2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_success(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {"SC-12": "PASS"}
        mock_mapper.get_control_description.return_value = "SC-12 description"
        mock_mapper.get_mapped_controls.return_value = ["SC-12", "SC-13", "SC-28"]
        mock_mapper_class.return_value = mock_mapper

        mock_evidence = MagicMock()
        mock_evidence.id = 999
        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSKMSEvidenceIntegration(plan_id=123, evidence_frequency=60)
        integration.raw_kms_data = [{"KeyId": "test-key"}]
        integration._upload_evidence_file = Mock()
        integration._link_evidence_to_ssp = Mock()

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()
        integration._upload_evidence_file.assert_called_once_with(999, "2023-12-01")
        integration._link_evidence_to_ssp.assert_called_once_with(999)

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_creation_failure(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record when creation fails."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper.get_mapped_controls.return_value = []
        mock_mapper_class.return_value = mock_mapper

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = None
        mock_evidence_class.return_value = mock_evidence_instance

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = []

        integration._create_evidence_record("2023-12-01")

        mock_evidence_instance.create.assert_called_once()

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Evidence")
    def test_create_evidence_record_exception(self, mock_evidence_class, mock_session_class, mock_mapper_class):
        """Test creating evidence record with exception."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = []

        integration._create_evidence_record("2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    def test_build_evidence_description(self, mock_session_class, mock_mapper_class):
        """Test building evidence description."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {"SC-12": "PASS", "SC-13": "FAIL", "SC-28": "PASS"}
        mock_mapper.get_control_description.side_effect = lambda x: f"{x} description"
        mock_mapper.get_mapped_controls.return_value = ["SC-12", "SC-13", "SC-28"]
        mock_mapper_class.return_value = mock_mapper

        integration = AWSKMSEvidenceIntegration(
            plan_id=123, region="us-east-1", account_id="123456789012", tags={"Environment": "Production"}
        )
        integration.raw_kms_data = [
            {"KeyId": "key-1", "RotationEnabled": True, "KeyManager": "CUSTOMER"},
            {"KeyId": "key-2", "RotationEnabled": False, "KeyManager": "CUSTOMER"},
        ]

        result = integration._build_evidence_description("2023-12-01")

        assert "AWS KMS Evidence" in result
        assert "2023-12-01" in result
        assert "us-east-1" in result
        assert "123456789012" in result
        assert "Environment=Production" in result
        assert "Total Keys" in result
        assert "SC-12" in result
        assert "SC-13" in result

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_success(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {"SC-12": "PASS"}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = True

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = [{"KeyId": "test-key"}]

        integration._upload_evidence_file(999, "2023-12-01")

        mock_file_class.upload_file_to_regscale.assert_called_once()
        call_args = mock_file_class.upload_file_to_regscale.call_args[1]
        assert call_args["parent_id"] == 999
        assert call_args["parent_module"] == "evidence"

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_upload_evidence_file_failure(self, mock_file_class, mock_api_class, mock_session_class, mock_mapper_class):
        """Test uploading evidence file with failure."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapper = MagicMock()
        mock_mapper.assess_key_compliance.return_value = {}
        mock_mapper_class.return_value = mock_mapper

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_file_class.upload_file_to_regscale.return_value = False

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = []

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
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
        mock_mapper.assess_key_compliance.side_effect = Exception("Test error")
        mock_mapper_class.return_value = mock_mapper

        integration = AWSKMSEvidenceIntegration(plan_id=123)
        integration.raw_kms_data = []

        integration._upload_evidence_file(999, "2023-12-01")

    @patch(f"{PATH}.KMSControlMapper")
    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.EvidenceMapping")
    def test_link_evidence_to_ssp_success(self, mock_mapping_class, mock_session_class, mock_mapper_class):
        """Test linking evidence to SSP successfully."""
        mock_session = MagicMock()
        mock_session.client.return_value = MagicMock()
        mock_session_class.return_value = mock_session

        mock_mapping = MagicMock()
        mock_mapping_class.return_value = mock_mapping

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        integration._link_evidence_to_ssp(999)

        mock_mapping_class.assert_called_once_with(evidenceID=999, mappedID=123, mappingType="securityplans")
        mock_mapping.create.assert_called_once()

    @patch(f"{PATH}.KMSControlMapper")
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

        integration = AWSKMSEvidenceIntegration(plan_id=123)

        integration._link_evidence_to_ssp(999)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
