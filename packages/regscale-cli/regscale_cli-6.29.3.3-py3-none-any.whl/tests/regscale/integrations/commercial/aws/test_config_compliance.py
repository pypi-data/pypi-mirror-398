#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Config Compliance Integration."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

from regscale.integrations.commercial.aws.config_compliance import (
    AWSConfigCompliance,
    AWSConfigComplianceItem,
)


class TestAWSConfigComplianceItem:
    """Test AWS Config Compliance Item."""

    def test_initialization(self):
        """Test compliance item initialization."""
        rule_evaluations = [
            {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0},
            {"rule_name": "test-rule-2", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 5},
        ]

        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations,
            resource_id="123456789012",
            resource_name="Test Account",
        )

        assert item.control_id == "AC-2"
        assert item._control_name == "Account Management"
        assert item.framework == "NIST800-53R5"
        assert len(item.rule_evaluations) == 2
        assert item.resource_id == "123456789012"
        assert item.resource_name == "Test Account"

    def test_compliance_result_fail(self):
        """Test compliance result returns FAIL for non-compliant rules."""
        rule_evaluations = [
            {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0},
            {"rule_name": "test-rule-2", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 5},
        ]

        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations,
        )

        assert item.compliance_result == "FAIL"

    def test_compliance_result_pass(self):
        """Test compliance result returns PASS for all compliant rules."""
        rule_evaluations = [
            {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0},
            {"rule_name": "test-rule-2", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0},
        ]

        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations,
        )

        assert item.compliance_result == "PASS"

    def test_compliance_result_no_data(self):
        """Test compliance result returns None for no data."""
        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=[],
        )

        assert item.compliance_result is None

    def test_severity_for_failed_control(self):
        """Test severity calculation for failed controls."""
        # Test HIGH severity (>= 5 non-compliant rules)
        rule_evaluations_high = [
            {"rule_name": f"test-rule-{i}", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 1}
            for i in range(6)
        ]

        item_high = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations_high,
        )

        assert item_high.severity == "HIGH"

        # Test MEDIUM severity (2-4 non-compliant rules)
        rule_evaluations_medium = [
            {"rule_name": f"test-rule-{i}", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 1}
            for i in range(3)
        ]

        item_medium = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations_medium,
        )

        assert item_medium.severity == "MEDIUM"

        # Test LOW severity (1 non-compliant rule)
        rule_evaluations_low = [
            {"rule_name": "test-rule-1", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 1}
        ]

        item_low = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations_low,
        )

        assert item_low.severity == "LOW"

    def test_severity_for_passed_control(self):
        """Test severity is None for passed controls."""
        rule_evaluations = [
            {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0}
        ]

        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations,
        )

        assert item.severity is None

    def test_description_html_format(self):
        """Test description contains HTML formatting."""
        rule_evaluations = [
            {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0},
            {"rule_name": "test-rule-2", "compliance_type": "NON_COMPLIANT", "non_compliant_resource_count": 5},
        ]

        item = AWSConfigComplianceItem(
            control_id="AC-2",
            control_name="Account Management",
            framework="NIST800-53R5",
            rule_evaluations=rule_evaluations,
        )

        description = item.description

        assert "<h3>" in description
        assert "AC-2" in description
        assert "<strong>" in description
        assert "Total Rules" in description
        assert "Compliant Rules" in description
        assert "Non-Compliant Rules" in description


class TestAWSConfigCompliance:
    """Test AWS Config Compliance Integration."""

    @pytest.fixture
    def mock_boto_session(self):
        """Create a mock boto3 session."""
        with patch("boto3.Session") as mock_session:
            mock_session_instance = MagicMock()
            mock_session.return_value = mock_session_instance

            # Mock clients
            mock_config_client = MagicMock()
            mock_sts_client = MagicMock()

            # Setup client creation
            def get_client(service_name):
                if service_name == "config":
                    return mock_config_client
                elif service_name == "sts":
                    return mock_sts_client
                return MagicMock()

            mock_session_instance.client.side_effect = get_client

            # Mock STS get_caller_identity
            mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}

            yield {
                "session": mock_session_instance,
                "config_client": mock_config_client,
                "sts_client": mock_sts_client,
            }

    def test_initialization(self, mock_boto_session):
        """Test AWS Config Compliance initialization."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(
                plan_id=123,
                region="us-east-1",
                framework="NIST800-53R5",
                create_issues=True,
                update_control_status=True,
            )

            assert scanner.plan_id == 123
            assert scanner.region == "us-east-1"
            assert scanner.framework == "NIST800-53R5"
            assert scanner.create_issues is True
            assert scanner.update_control_status is True
            assert scanner.title == "AWS Config"

    def test_cache_validation(self, mock_boto_session):
        """Test cache validation logic."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(plan_id=123, region="us-east-1")

            # Test with no cache file
            with patch("os.path.exists", return_value=False):
                assert scanner._is_cache_valid() is False

            # Test with valid cache file
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getmtime", return_value=datetime.now().timestamp() - 3600):  # 1 hour old
                    assert scanner._is_cache_valid() is True

            # Test with expired cache file
            with patch("os.path.exists", return_value=True):
                with patch("os.path.getmtime", return_value=datetime.now().timestamp() - (5 * 3600)):  # 5 hours old
                    assert scanner._is_cache_valid() is False

    def test_create_compliance_item(self, mock_boto_session):
        """Test creating compliance item from raw data."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(plan_id=123, region="us-east-1")

            raw_data = {
                "control_id": "AC-2",
                "control_name": "Account Management",
                "rule_evaluations": [
                    {"rule_name": "test-rule-1", "compliance_type": "COMPLIANT", "non_compliant_resource_count": 0}
                ],
                "resource_id": "123456789012",
                "resource_name": "Test Account",
            }

            item = scanner.create_compliance_item(raw_data)

            assert isinstance(item, AWSConfigComplianceItem)
            assert item.control_id == "AC-2"
            assert len(item.rule_evaluations) == 1

    def test_get_aws_account_id(self, mock_boto_session):
        """Test getting AWS account ID."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(plan_id=123, region="us-east-1")

            account_id = scanner._get_aws_account_id()
            assert account_id == "123456789012"

    def test_load_cached_data(self, mock_boto_session):
        """Test loading data from cache."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(plan_id=123, region="us-east-1")

            cached_data = [{"control_id": "AC-2", "rule_evaluations": []}]

            mock_file_content = json.dumps(cached_data)

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                loaded_data = scanner._load_cached_data()
                assert len(loaded_data) == 1
                assert loaded_data[0]["control_id"] == "AC-2"

    def test_save_to_cache(self, mock_boto_session):
        """Test saving data to cache."""
        with patch("boto3.Session", return_value=mock_boto_session["session"]):
            scanner = AWSConfigCompliance(plan_id=123, region="us-east-1")

            compliance_data = [{"control_id": "AC-2", "rule_evaluations": []}]

            with patch("os.makedirs") as mock_makedirs:
                with patch("builtins.open", mock_open()) as mock_file:
                    scanner._save_to_cache(compliance_data)
                    mock_makedirs.assert_called_once()
                    mock_file.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
