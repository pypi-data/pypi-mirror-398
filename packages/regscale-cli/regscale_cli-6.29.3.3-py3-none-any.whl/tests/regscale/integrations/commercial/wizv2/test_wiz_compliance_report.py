#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for Wiz Compliance Report Integration.

This test suite covers both WizComplianceReportItem and WizComplianceReportProcessor
classes with extensive mocking and edge case testing.
"""

import csv
import gzip
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.commercial.wizv2.compliance_report import (
    WizComplianceReportItem,
    WizComplianceReportProcessor,
)
from regscale.integrations.compliance_integration import ComplianceIntegration


@pytest.mark.no_parallel
class TestWizComplianceReportItem(unittest.TestCase):
    """Test suite for WizComplianceReportItem class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_csv_row = {
            "Resource Name": "test-vm-001",
            "Cloud Provider": "Azure",
            "Cloud Provider ID": "subscriptions/12345/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/test-vm-001",
            "Resource ID": "/subscriptions/12345/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/test-vm-001",
            "Resource Region": "East US",
            "Subscription": "subscription-123",
            "Subscription Name": "Dev Subscription",
            "Policy Name": "Ensure VM disk encryption is enabled",
            "Policy ID": "policy-disk-encryption-001",
            "Result": "Pass",
            "Severity": "HIGH",
            "Compliance Check Name (Wiz Subcategory)": "AC-2(1) Account Management | Automated System Account Management",
            "Framework": "NIST SP 800-53 Revision 5",
            "Remediation Steps": "Enable disk encryption on the VM through Azure portal",
        }

        self.failing_csv_row = {
            **self.sample_csv_row,
            "Result": "Failed",
            "Resource Name": "test-vm-002",
            "Cloud Provider ID": "subscriptions/12345/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/test-vm-002",
        }

    def test_init_with_valid_csv_row(self):
        """Test initialization with valid CSV row data."""
        item = WizComplianceReportItem(self.sample_csv_row)

        self.assertEqual(item._resource_name, "test-vm-001")
        self.assertEqual(item.cloud_provider, "Azure")
        self.assertEqual(
            item.cloud_provider_id,
            "subscriptions/12345/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/test-vm-001",
        )
        self.assertEqual(item.result, "Pass")
        self.assertEqual(item._severity, "HIGH")
        self.assertEqual(item.policy_name, "Ensure VM disk encryption is enabled")

    def test_resource_id_property_priority(self):
        """Test resource_id property uses correct priority: cloud_provider_id > _resource_id > _resource_name."""
        # Test with all values present
        item = WizComplianceReportItem(self.sample_csv_row)
        self.assertEqual(item.resource_id, self.sample_csv_row["Cloud Provider ID"])

        # Test with cloud_provider_id missing
        csv_row_no_cloud_id = {**self.sample_csv_row, "Cloud Provider ID": ""}
        item = WizComplianceReportItem(csv_row_no_cloud_id)
        self.assertEqual(item.resource_id, self.sample_csv_row["Resource ID"])

        # Test with both cloud_provider_id and resource_id missing
        csv_row_no_ids = {**self.sample_csv_row, "Cloud Provider ID": "", "Resource ID": ""}
        item = WizComplianceReportItem(csv_row_no_ids)
        self.assertEqual(item.resource_id, "test-vm-001")

        # Test with all missing
        csv_row_all_empty = {**self.sample_csv_row, "Cloud Provider ID": "", "Resource ID": "", "Resource Name": ""}
        item = WizComplianceReportItem(csv_row_all_empty)
        self.assertEqual(item.resource_id, "Unknown")

    def test_resource_name_property(self):
        """Test resource_name property calls get_unique_resource_name."""
        item = WizComplianceReportItem(self.sample_csv_row)
        with patch.object(item, "get_unique_resource_name", return_value="mocked_name") as mock_method:
            result = item.resource_name
            self.assertEqual(result, "mocked_name")
            mock_method.assert_called_once()

    def test_control_id_property(self):
        """Test control_id property calls get_control_id."""
        item = WizComplianceReportItem(self.sample_csv_row)
        with patch.object(item, "get_control_id", return_value="AC-2(1)") as mock_method:
            result = item.control_id
            self.assertEqual(result, "AC-2(1)")
            mock_method.assert_called_once()

    def test_compliance_result_property(self):
        """Test compliance_result property returns result."""
        item = WizComplianceReportItem(self.sample_csv_row)
        self.assertEqual(item.compliance_result, "Pass")

    def test_severity_property(self):
        """Test severity property returns _severity or None if empty."""
        item = WizComplianceReportItem(self.sample_csv_row)
        self.assertEqual(item.severity, "HIGH")

        # Test with empty severity
        csv_row_no_severity = {**self.sample_csv_row, "Severity": ""}
        item = WizComplianceReportItem(csv_row_no_severity)
        self.assertIsNone(item.severity)

    def test_description_property(self):
        """Test description property calls get_finding_details."""
        item = WizComplianceReportItem(self.sample_csv_row)
        with patch.object(item, "get_finding_details", return_value="mocked_details") as mock_method:
            result = item.description
            self.assertEqual(result, "mocked_details")
            mock_method.assert_called_once()

    def test_framework_property_default(self):
        """Test framework property returns NIST800-53R5 as default."""
        csv_row_no_framework = {**self.sample_csv_row, "Framework": ""}
        item = WizComplianceReportItem(csv_row_no_framework)
        self.assertEqual(item.framework, "NIST800-53R5")

    def test_framework_property_mapping(self):
        """Test framework property maps Wiz framework names to RegScale format."""
        test_cases = [
            ("NIST SP 800-53 Revision 5", "NIST800-53R5"),
            ("NIST SP 800-53 Rev 5", "NIST800-53R5"),
            ("NIST SP 800-53 R5", "NIST800-53R5"),
            ("NIST 800-53 Revision 5", "NIST800-53R5"),
            ("NIST 800-53 Rev 5", "NIST800-53R5"),
            ("NIST 800-53 R5", "NIST800-53R5"),
            ("Unknown Framework", "Unknown Framework"),
        ]

        for wiz_framework, expected_regscale_framework in test_cases:
            csv_row = {**self.sample_csv_row, "Framework": wiz_framework}
            item = WizComplianceReportItem(csv_row)
            self.assertEqual(item.framework, expected_regscale_framework)

    def test_get_control_id_single_control(self):
        """Test get_control_id returns first control ID from compliance check name."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_control_id()
        self.assertEqual(result, "AC-2(1)")

    def test_get_control_id_empty_compliance_check_name(self):
        """Test get_control_id returns empty string when compliance check name is empty."""
        csv_row_no_compliance_check = {**self.sample_csv_row, "Compliance Check Name (Wiz Subcategory)": ""}
        item = WizComplianceReportItem(csv_row_no_compliance_check)
        result = item.get_control_id()
        self.assertEqual(result, "")

    def test_get_all_control_ids_single_control(self):
        """Test get_all_control_ids extracts control IDs correctly."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_all_control_ids()
        self.assertEqual(result, ["AC-2(1)"])

    def test_get_all_control_ids_multiple_controls(self):
        """Test get_all_control_ids extracts multiple control IDs."""
        csv_row_multiple_controls = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-2(4) Account Management | Automated Audit Actions, AC-6(9) Least Privilege | Log Use of Privileged Functions",
        }
        item = WizComplianceReportItem(csv_row_multiple_controls)
        result = item.get_all_control_ids()
        self.assertEqual(result, ["AC-2(4)", "AC-6(9)"])

    def test_get_all_control_ids_base_controls_without_enhancements(self):
        """Test get_all_control_ids handles base controls without enhancements."""
        csv_row_base_controls = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-3 Access Enforcement, AC-4 Information Flow Enforcement",
        }
        item = WizComplianceReportItem(csv_row_base_controls)
        result = item.get_all_control_ids()
        self.assertEqual(result, ["AC-3", "AC-4"])

    def test_get_all_control_ids_mixed_controls(self):
        """Test get_all_control_ids handles mixed base and enhanced controls."""
        csv_row_mixed_controls = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-3 Access Enforcement, AC-4(2) Information Flow Enforcement | Processing Domains",
        }
        item = WizComplianceReportItem(csv_row_mixed_controls)
        result = item.get_all_control_ids()
        self.assertEqual(result, ["AC-3", "AC-4(2)"])

    def test_get_all_control_ids_empty_compliance_check_name(self):
        """Test get_all_control_ids returns empty list when compliance check name is empty."""
        csv_row_no_compliance_check = {**self.sample_csv_row, "Compliance Check Name (Wiz Subcategory)": ""}
        item = WizComplianceReportItem(csv_row_no_compliance_check)
        result = item.get_all_control_ids()
        self.assertEqual(result, [])

    def test_control_id_normalization_leading_zeros(self):
        """Test that control IDs with leading zeros are properly normalized."""
        # Test base control with leading zeros
        csv_row = {**self.sample_csv_row, "Compliance Check Name (Wiz Subcategory)": "AC-01 Access Control Policy"}
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_control_id(), "AC-1")
        self.assertEqual(item.get_all_control_ids(), ["AC-1"])

        # Test enhancement with leading zeros in base control
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-01(04) Access Control Policy Enhancement",
        }
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_control_id(), "AC-1(4)")
        self.assertEqual(item.get_all_control_ids(), ["AC-1(4)"])

        # Test multiple controls with various leading zero patterns
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-01(04) Access Control, AU-003(001) Audit Content, SI-04(020) Monitoring",
        }
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_all_control_ids(), ["AC-1(4)", "AU-3(1)", "SI-4(20)"])

    def test_enhancement_normalization(self):
        """Test that enhancement numbers are normalized to remove leading zeros."""
        # Single digit enhancement with leading zeros
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-2(01) Account Management Enhancement",
        }
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_control_id(), "AC-2(1)")

        # Double digit enhancement with leading zeros
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "SI-4(020) System Monitoring Enhancement",
        }
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_control_id(), "SI-4(20)")

        # Triple leading zeros
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-2(001) Account Management Enhancement",
        }
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_control_id(), "AC-2(1)")

    def test_affected_controls_property_normalized(self):
        """Test that affected_controls property returns normalized comma-separated list."""
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-01(04) Account Management, AC-06(009) Least Privilege",
        }
        item = WizComplianceReportItem(csv_row)

        # affected_controls should return all normalized control IDs as comma-separated string
        self.assertEqual(item.affected_controls, "AC-1(4),AC-6(9)")

    def test_normalize_base_control_method(self):
        """Test the _normalize_base_control method directly."""
        csv_row = {**self.sample_csv_row}
        item = WizComplianceReportItem(csv_row)

        # Test various base control formats
        self.assertEqual(item._normalize_base_control("AC-01"), "AC-1")
        self.assertEqual(item._normalize_base_control("AC-1"), "AC-1")
        self.assertEqual(item._normalize_base_control("AU-003"), "AU-3")
        self.assertEqual(item._normalize_base_control("SI-004"), "SI-4")
        self.assertEqual(item._normalize_base_control("sc-7"), "SC-7")  # lowercase
        self.assertEqual(item._normalize_base_control("PM-10"), "PM-10")  # no leading zero

    def test_format_control_id_method(self):
        """Test the _format_control_id method directly."""
        csv_row = {**self.sample_csv_row}
        item = WizComplianceReportItem(csv_row)

        # Test enhancement normalization
        self.assertEqual(item._format_control_id("AC-1", "04"), "AC-1(4)")
        self.assertEqual(item._format_control_id("AC-2", "001"), "AC-2(1)")
        self.assertEqual(item._format_control_id("SI-4", "020"), "SI-4(20)")

        # Test without enhancement
        self.assertEqual(item._format_control_id("AC-1", ""), "AC-1")
        self.assertEqual(item._format_control_id("AC-1", None), "AC-1")

        # Test with already normalized enhancement
        self.assertEqual(item._format_control_id("AC-1", "4"), "AC-1(4)")
        self.assertEqual(item._format_control_id("AC-2", "12"), "AC-2(12)")

    def test_get_status_case_insensitive(self):
        """Test get_status handles case-insensitive result values."""
        test_cases = [
            ("pass", "Satisfied"),
            ("Pass", "Satisfied"),
            ("PASS", "Satisfied"),
            ("fail", "Other Than Satisfied"),
            ("Failed", "Other Than Satisfied"),
            ("FAILED", "Other Than Satisfied"),
            ("unknown", "Other Than Satisfied"),
        ]

        for result_value, expected_status in test_cases:
            with self.subTest(result_value=result_value):
                csv_row = {**self.sample_csv_row, "Result": result_value}
                item = WizComplianceReportItem(csv_row)
                result = item.get_status()
                self.assertEqual(result, expected_status)

    def test_get_implementation_status_case_insensitive(self):
        """Test get_implementation_status handles case-insensitive result values."""
        test_cases = [
            ("pass", "Implemented"),
            ("Pass", "Implemented"),
            ("PASS", "Implemented"),
            ("fail", "In Remediation"),
            ("Failed", "In Remediation"),
            ("FAILED", "In Remediation"),
            ("unknown", "In Remediation"),
        ]

        for result_value, expected_status in test_cases:
            with self.subTest(result_value=result_value):
                csv_row = {**self.sample_csv_row, "Result": result_value}
                item = WizComplianceReportItem(csv_row)
                result = item.get_implementation_status()
                self.assertEqual(result, expected_status)

    def test_get_severity_mapping(self):
        """Test get_severity maps Wiz severity to RegScale severity."""
        test_cases = [
            ("CRITICAL", "High"),
            ("HIGH", "High"),
            ("MEDIUM", "Moderate"),
            ("LOW", "Low"),
            ("INFORMATIONAL", "Low"),
            ("unknown", "Low"),
            ("", "Low"),
        ]

        for severity_value, expected_severity in test_cases:
            with self.subTest(severity_value=severity_value):
                csv_row = {**self.sample_csv_row, "Severity": severity_value}
                item = WizComplianceReportItem(csv_row)
                result = item.get_severity()
                self.assertEqual(result, expected_severity)

    def test_get_unique_resource_name_full_details(self):
        """Test get_unique_resource_name with all details present."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_unique_resource_name()
        # The method should not add duplicate suffixes when resource_id is same as resource_name
        self.assertEqual(result, "test-vm-001 (East US)")

    def test_get_unique_resource_name_no_resource_name(self):
        """Test get_unique_resource_name when resource name is empty."""
        csv_row_no_name = {**self.sample_csv_row, "Resource Name": ""}
        item = WizComplianceReportItem(csv_row_no_name)
        result = item.get_unique_resource_name()
        self.assertTrue(result.startswith("Unknown Resource"))

    def test_get_unique_resource_name_no_region(self):
        """Test get_unique_resource_name without region."""
        csv_row_no_region = {**self.sample_csv_row, "Resource Region": ""}
        item = WizComplianceReportItem(csv_row_no_region)
        result = item.get_unique_resource_name()
        # Should not add duplicate suffix when resource_id contains resource_name
        self.assertEqual(result, "test-vm-001")

    def test_get_unique_resource_name_azure_resource_id_truncation(self):
        """Test get_unique_resource_name truncates long Azure resource IDs."""
        csv_row_long_id = {
            **self.sample_csv_row,
            "Resource ID": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/very-long-resource-group-name/providers/Microsoft.Compute/virtualMachines/very-long-vm-name-that-should-be-truncated",
        }
        item = WizComplianceReportItem(csv_row_long_id)
        result = item.get_unique_resource_name()
        # Should truncate the resource ID to 12 characters
        self.assertIn("[very-long-vm]", result)

    def test_get_unique_resource_name_avoids_duplicate_suffix(self):
        """Test get_unique_resource_name avoids adding suffix if already present."""
        csv_row_duplicate_suffix = {
            **self.sample_csv_row,
            "Resource Name": "test-vm-001",
            "Resource ID": "test-vm-001",  # Same as resource name
        }
        item = WizComplianceReportItem(csv_row_duplicate_suffix)
        result = item.get_unique_resource_name()
        # Should not duplicate the resource name
        self.assertEqual(result.count("test-vm-001"), 1)

    def test_get_unique_issue_identifier(self):
        """Test get_unique_issue_identifier creates unique identifier."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_unique_issue_identifier()
        expected_parts = [
            self.sample_csv_row["Resource ID"],
            self.sample_csv_row["Policy ID"],
            "AC-2(1)",  # Expected control ID
        ]
        expected = "|".join(expected_parts)
        self.assertEqual(result, expected)

    def test_get_unique_issue_identifier_fallback_values(self):
        """Test get_unique_issue_identifier uses fallback values when primary ones are missing."""
        csv_row_fallbacks = {
            **self.sample_csv_row,
            "Resource ID": "",
            "Policy ID": "",
        }
        item = WizComplianceReportItem(csv_row_fallbacks)
        result = item.get_unique_issue_identifier()
        # Should use cloud_provider_id for resource and policy_name for policy
        expected_parts = [self.sample_csv_row["Cloud Provider ID"], self.sample_csv_row["Policy Name"], "AC-2(1)"]
        expected = "|".join(expected_parts)
        self.assertEqual(result, expected)

    def test_get_title(self):
        """Test get_title returns control ID and policy name."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_title()
        self.assertEqual(result, "AC-2(1) - Ensure VM disk encryption is enabled")

    def test_get_description(self):
        """Test get_description returns assessment description."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_description()
        expected = "Wiz compliance assessment for test-vm-001 (East US) - Ensure VM disk encryption is enabled"
        self.assertEqual(result, expected)

    def test_get_finding_details(self):
        """Test get_finding_details returns formatted finding details."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_finding_details()

        expected_lines = [
            "Resource: test-vm-001 (East US)",
            "Cloud Provider: Azure",
            "Subscription: Dev Subscription",
            "Result: Pass",
            "Remediation: Enable disk encryption on the VM through Azure portal",
        ]

        for line in expected_lines:
            self.assertIn(line, result)

    def test_get_finding_details_no_subscription(self):
        """Test get_finding_details without subscription name."""
        csv_row_no_sub = {**self.sample_csv_row, "Subscription Name": ""}
        item = WizComplianceReportItem(csv_row_no_sub)
        result = item.get_finding_details()

        # Should not include subscription line
        self.assertNotIn("Subscription:", result)

    def test_get_asset_identifier(self):
        """Test get_asset_identifier returns correct priority identifier."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_asset_identifier()
        self.assertEqual(result, self.sample_csv_row["Cloud Provider ID"])

    def test_get_asset_identifier_fallbacks(self):
        """Test get_asset_identifier uses fallback values."""
        csv_row_fallbacks = {**self.sample_csv_row, "Cloud Provider ID": "", "Resource ID": "", "Resource Name": ""}
        item = WizComplianceReportItem(csv_row_fallbacks)
        result = item.get_asset_identifier()
        self.assertEqual(result, "Unknown")


@pytest.mark.no_parallel
@patch("regscale.integrations.compliance_integration.ComplianceIntegration.__init__", return_value=None)
class TestWizComplianceReportProcessor(unittest.TestCase):
    """Test suite for WizComplianceReportProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.plan_id = 123
        self.wiz_project_id = "test-project-123"
        self.client_id = "test-client-id"
        self.client_secret = "test-client-secret"

        # Sample CSV data matching expected results
        self.sample_csv_data = [
            {
                "Resource Name": "vm-001",
                "Cloud Provider": "Azure",
                "Cloud Provider ID": "vm-001-id",
                "Resource ID": "vm-001-id",
                "Resource Region": "East US",
                "Subscription": "subscription-1",
                "Subscription Name": "Dev Subscription",
                "Policy Name": "Policy 1",
                "Policy ID": "policy-001",
                "Result": "Pass",
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": "AC-2(1) Account Management",
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this issue",
            },
            {
                "Resource Name": "vm-002",
                "Cloud Provider": "Azure",
                "Cloud Provider ID": "vm-002-id",
                "Resource ID": "vm-002-id",
                "Resource Region": "West US",
                "Subscription": "subscription-1",
                "Subscription Name": "Dev Subscription",
                "Policy Name": "Policy 2",
                "Policy ID": "policy-002",
                "Result": "Failed",
                "Severity": "MEDIUM",
                "Compliance Check Name (Wiz Subcategory)": "AC-3 Access Enforcement",
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this issue",
            },
        ]

    def _initialize_processor_attributes(self, processor):
        """Initialize parent class attributes that would normally be set by __init__."""
        from collections import defaultdict

        processor.all_compliance_items = []
        processor.failed_compliance_items = []
        processor.passing_controls = {}
        processor.failing_controls = {}
        processor.asset_compliance_map = defaultdict(list)
        processor.plan_id = self.plan_id
        processor.title = "Wiz Compliance"

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_init_successful_authentication(self, mock_auth, mock_report_manager, mock_parent_init):
        """Test successful initialization with authentication."""
        mock_auth.return_value = "test-token"
        mock_report_manager_instance = MagicMock()
        mock_report_manager.return_value = mock_report_manager_instance

        processor = WizComplianceReportProcessor(
            plan_id=self.plan_id,
            wiz_project_id=self.wiz_project_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self._initialize_processor_attributes(processor)

        mock_auth.assert_called_once_with(self.client_id, self.client_secret)
        mock_report_manager.assert_called_once()
        self.assertEqual(processor.plan_id, self.plan_id)
        self.assertEqual(processor.wiz_project_id, self.wiz_project_id)
        self.assertEqual(processor.title, "Wiz Compliance")

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.error_and_exit")
    def test_init_failed_authentication(self, mock_error_exit, mock_auth, mock_report_manager, mock_parent_init):
        """Test initialization with failed authentication."""
        mock_auth.return_value = None
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            WizComplianceReportProcessor(
                plan_id=self.plan_id,
                wiz_project_id=self.wiz_project_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

        mock_error_exit.assert_called_once_with("Failed to authenticate with Wiz")

    def test_parse_csv_report_regular_file(self, mock_parent_init):
        """Test parse_csv_report with regular CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self.sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(self.sample_csv_data)
            temp_file_path = temp_file.name

        try:
            # Create processor with mocked dependencies
            with patch(
                "regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"
            ):
                with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                    processor = WizComplianceReportProcessor(
                        plan_id=self.plan_id,
                        wiz_project_id=self.wiz_project_id,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                    )

            items = processor.parse_csv_report(temp_file_path)

            self.assertEqual(len(items), 2)
            self.assertIsInstance(items[0], WizComplianceReportItem)
            self.assertIsInstance(items[1], WizComplianceReportItem)
            self.assertEqual(items[0]._resource_name, "vm-001")
            self.assertEqual(items[1]._resource_name, "vm-002")

        finally:
            os.unlink(temp_file_path)

    def test_parse_csv_report_gzipped_file(self, mock_parent_init):
        """Test parse_csv_report with gzipped CSV file."""
        # Create temporary gzipped CSV file
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as temp_file:
            temp_file_path = temp_file.name

        with gzip.open(temp_file_path, "wt", encoding="utf-8") as gz_file:
            writer = csv.DictWriter(gz_file, fieldnames=self.sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(self.sample_csv_data)

        try:
            # Create processor with mocked dependencies
            with patch(
                "regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"
            ):
                with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                    processor = WizComplianceReportProcessor(
                        plan_id=self.plan_id,
                        wiz_project_id=self.wiz_project_id,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                    )

            items = processor.parse_csv_report(temp_file_path)

            self.assertEqual(len(items), 2)
            self.assertIsInstance(items[0], WizComplianceReportItem)

        finally:
            os.unlink(temp_file_path)

    def test_parse_csv_report_file_not_found(self, mock_parent_init):
        """Test parse_csv_report with non-existent file."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        items = processor.parse_csv_report("non_existent_file.csv")
        self.assertEqual(len(items), 0)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_fetch_compliance_data_with_existing_report(self, mock_auth, mock_report_manager, mock_parent_init):
        """Test fetch_compliance_data with existing report file."""
        mock_auth.return_value = "test-token"

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self.sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(self.sample_csv_data)
            temp_file_path = temp_file.name

        try:
            processor = WizComplianceReportProcessor(
                plan_id=self.plan_id,
                wiz_project_id=self.wiz_project_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
                report_file_path=temp_file_path,
            )

            raw_data = processor.fetch_compliance_data()

            self.assertEqual(len(raw_data), 2)
            self.assertEqual(raw_data[0]["Resource Name"], "vm-001")
            self.assertEqual(raw_data[1]["Resource Name"], "vm-002")

        finally:
            os.unlink(temp_file_path)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_fetch_compliance_data_report_creation(self, mock_auth, mock_report_manager, mock_parent_init):
        """Test fetch_compliance_data creates new report when none exists."""
        mock_auth.return_value = "test-token"

        # Create temporary CSV file for the mock report
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self.sample_csv_data[0].keys())
            writer.writeheader()
            writer.writerows(self.sample_csv_data)
            temp_file_path = temp_file.name

        try:
            processor = WizComplianceReportProcessor(
                plan_id=self.plan_id,
                wiz_project_id=self.wiz_project_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Mock the report creation process
            with patch.object(processor, "_get_or_create_report", return_value=temp_file_path):
                raw_data = processor.fetch_compliance_data()

                self.assertEqual(len(raw_data), 2)

        finally:
            os.unlink(temp_file_path)

    def test_fetch_compliance_data_file_read_error(self, mock_parent_init):
        """Test fetch_compliance_data handles file read errors."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        # Mock file operations to raise an exception
        with patch("builtins.open", side_effect=IOError("File read error")):
            with patch.object(processor, "_get_or_create_report", return_value="test_file.csv"):
                raw_data = processor.fetch_compliance_data()
                self.assertEqual(len(raw_data), 0)

    def test_create_compliance_item(self, mock_parent_init):
        """Test create_compliance_item creates WizComplianceReportItem."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        item = processor.create_compliance_item(self.sample_csv_data[0])
        self.assertIsInstance(item, WizComplianceReportItem)
        self.assertEqual(item._resource_name, "vm-001")

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_process_compliance_data_bypass_filtering(self, mock_auth, mock_report_manager, mock_parent_init):
        """Test process_compliance_data with bypass_control_filtering=True."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.plan_id,
            wiz_project_id=self.wiz_project_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            bypass_control_filtering=True,
        )

        with patch.object(processor, "_process_compliance_data_without_filtering") as mock_without_filtering:
            processor.process_compliance_data()
            mock_without_filtering.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_process_compliance_data_normal_filtering(self, mock_auth, mock_report_manager, mock_parent_init):
        """Test process_compliance_data with normal filtering."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.plan_id,
            wiz_project_id=self.wiz_project_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
            bypass_control_filtering=False,
        )

        # Mock the parent's process_compliance_data method
        with patch.object(ComplianceIntegration, "process_compliance_data") as mock_parent:
            processor.process_compliance_data()
            mock_parent.assert_called_once()

    def test_process_compliance_data_without_filtering_categorization(self, mock_parent_init):
        """Test _process_compliance_data_without_filtering categorizes controls correctly."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
        self._initialize_processor_attributes(processor)

        # Mock fetch_compliance_data to return our test data
        with patch.object(processor, "fetch_compliance_data", return_value=self.sample_csv_data):
            with patch.object(processor, "_categorize_controls_fail_first") as mock_categorize:
                processor._process_compliance_data_without_filtering()

                # Should have processed 2 items
                self.assertEqual(len(processor.all_compliance_items), 2)
                # Should have 1 failed item (Result="Failed")
                self.assertEqual(len(processor.failed_compliance_items), 1)
                # Should call fail-first categorization
                mock_categorize.assert_called_once()

    def test_process_compliance_sync(self, mock_parent_init):
        """Test process_compliance_sync calls sync_compliance."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        with patch.object(processor, "sync_compliance") as mock_sync:
            processor.process_compliance_sync()
            mock_sync.assert_called_once()

    def test_get_or_create_report_existing_recent_report(self, mock_parent_init):
        """Test _get_or_create_report uses existing recent report."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        with patch.object(processor, "_find_recent_report", return_value="existing_report.csv"):
            result = processor._get_or_create_report()
            self.assertEqual(result, "existing_report.csv")

    def test_get_or_create_report_creates_new_report(self, mock_parent_init):
        """Test _get_or_create_report creates new report when none exists."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        with patch.object(processor, "_find_recent_report", return_value=None):
            with patch.object(processor, "_create_and_download_report", return_value="new_report.csv"):
                result = processor._get_or_create_report()
                self.assertEqual(result, "new_report.csv")

    def test_find_recent_report_no_artifacts_dir(self, mock_parent_init):
        """Test _find_recent_report returns None when artifacts directory doesn't exist."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        with patch("os.path.exists", return_value=False):
            result = processor._find_recent_report()
            self.assertIsNone(result)

    def test_find_recent_report_finds_recent_file(self, mock_parent_init):
        """Test _find_recent_report finds and returns recent file."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        recent_time = datetime.now().timestamp()
        expected_filename = f"compliance_report_{self.wiz_project_id}_test.csv"

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=[expected_filename]):
                with patch("os.path.getmtime", return_value=recent_time):
                    result = processor._find_recent_report()
                    expected_path = f"artifacts/wiz/{expected_filename}"
                    self.assertEqual(result, expected_path)

    def test_find_recent_report_ignores_old_files(self, mock_parent_init):
        """Test _find_recent_report ignores files older than max_age_hours."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        # File older than 24 hours
        old_time = (datetime.now() - timedelta(hours=25)).timestamp()
        expected_filename = f"compliance_report_{self.wiz_project_id}_test.csv"

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=[expected_filename]):
                with patch("os.path.getmtime", return_value=old_time):
                    result = processor._find_recent_report(max_age_hours=24)
                    self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.ReportFileCleanup")
    @patch("os.makedirs")
    def test_create_and_download_report_success(self, mock_makedirs, mock_cleanup, mock_parent_init):
        """Test _create_and_download_report successful report creation."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            mock_report_manager = MagicMock()
            with patch(
                "regscale.integrations.commercial.wizv2.compliance_report.WizReportManager",
                return_value=mock_report_manager,
            ):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        # Mock successful report creation flow
        mock_report_manager.create_compliance_report.return_value = "report-123"
        mock_report_manager.wait_for_report_completion.return_value = "http://download.url"  # NOSONAR
        mock_report_manager.download_report.return_value = True

        result = processor._create_and_download_report()

        self.assertIsNotNone(result)
        self.assertTrue(result.startswith("artifacts/wiz/compliance_report_"))
        self.assertTrue(result.endswith(".csv"))
        mock_makedirs.assert_called_once()
        mock_cleanup.cleanup_old_files.assert_called_once()

    def test_create_and_download_report_creation_failure(self, mock_parent_init):
        """Test _create_and_download_report handles report creation failure."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            mock_report_manager = MagicMock()
            with patch(
                "regscale.integrations.commercial.wizv2.compliance_report.WizReportManager",
                return_value=mock_report_manager,
            ):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        # Mock failed report creation
        mock_report_manager.create_compliance_report.return_value = None

        result = processor._create_and_download_report()
        self.assertIsNone(result)

    def test_create_and_download_report_download_failure(self, mock_parent_init):
        """Test _create_and_download_report handles download failure."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            mock_report_manager = MagicMock()
            with patch(
                "regscale.integrations.commercial.wizv2.compliance_report.WizReportManager",
                return_value=mock_report_manager,
            ):
                processor = WizComplianceReportProcessor(
                    plan_id=self.plan_id,
                    wiz_project_id=self.wiz_project_id,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )

        # Mock successful creation but failed download
        mock_report_manager.create_compliance_report.return_value = "report-123"
        mock_report_manager.wait_for_report_completion.return_value = "http://download.url"  # NOSONAR
        mock_report_manager.download_report.return_value = False

        with patch("os.makedirs"):
            result = processor._create_and_download_report()
            self.assertIsNone(result)


@pytest.mark.no_parallel
@patch("regscale.integrations.compliance_integration.ComplianceIntegration.__init__", return_value=None)
class TestWizComplianceStatusMatching(unittest.TestCase):
    """Test suite for status matching and case-insensitive logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_csv_row = {
            "Resource Name": "test-vm",
            "Cloud Provider": "Azure",
            "Cloud Provider ID": "vm-id",
            "Resource ID": "vm-id",
            "Resource Region": "East US",
            "Subscription": "sub-1",
            "Subscription Name": "Test Sub",
            "Policy Name": "Test Policy",
            "Policy ID": "policy-001",
            "Result": "Pass",
            "Severity": "HIGH",
            "Compliance Check Name (Wiz Subcategory)": "AC-2(1) Account Management",
            "Framework": "NIST SP 800-53 Revision 5",
            "Remediation Steps": "Fix this",
        }

    def _initialize_processor_attributes(self, processor):
        """Initialize parent class attributes that would normally be set by __init__."""
        from collections import defaultdict

        processor.all_compliance_items = []
        processor.failed_compliance_items = []
        processor.passing_controls = {}
        processor.failing_controls = {}
        processor.asset_compliance_map = defaultdict(list)

    def test_pass_status_matching_case_insensitive(self, mock_parent_init):
        """Test that pass statuses are matched case-insensitively."""
        # Current implementation supports: Pass, PASS, pass but not Passed, PASSED, passed
        pass_values = ["Pass", "PASS", "pass"]
        fail_values = ["Passed", "PASSED", "passed"]  # These don't work with current implementation

        # Test values that currently work
        for result_value in pass_values:
            with self.subTest(result_value=result_value):
                csv_row = {**self.sample_csv_row, "Result": result_value}
                item = WizComplianceReportItem(csv_row)

                self.assertEqual(item.get_status(), "Satisfied")
                self.assertEqual(item.get_implementation_status(), "Implemented")

        # Test values that currently don't work (ones ending with 'ed')
        for result_value in fail_values:
            with self.subTest(result_value=result_value):
                csv_row = {**self.sample_csv_row, "Result": result_value}
                item = WizComplianceReportItem(csv_row)

                # These return "Other Than Satisfied" because they're not in PASS_STATUSES
                self.assertEqual(item.get_status(), "Other Than Satisfied")
                self.assertEqual(item.get_implementation_status(), "In Remediation")

    def test_fail_status_matching_case_insensitive(self, mock_parent_init):
        """Test that fail statuses are matched case-insensitively."""
        fail_values = ["Fail", "FAIL", "fail", "Failed", "FAILED", "failed"]

        for result_value in fail_values:
            with self.subTest(result_value=result_value):
                csv_row = {**self.sample_csv_row, "Result": result_value}
                item = WizComplianceReportItem(csv_row)

                self.assertEqual(item.get_status(), "Other Than Satisfied")
                self.assertEqual(item.get_implementation_status(), "In Remediation")

    def test_status_categorization_in_processor(self, mock_parent_init):
        """Test that WizComplianceReportProcessor correctly categorizes statuses."""
        # Test data with mixed case statuses
        test_data = [
            {**self.sample_csv_row, "Result": "Pass", "Compliance Check Name (Wiz Subcategory)": "AC-2(1)"},
            {**self.sample_csv_row, "Result": "PASS", "Compliance Check Name (Wiz Subcategory)": "AC-3"},
            {**self.sample_csv_row, "Result": "pass", "Compliance Check Name (Wiz Subcategory)": "AC-4"},
            {**self.sample_csv_row, "Result": "Failed", "Compliance Check Name (Wiz Subcategory)": "SI-2"},
            {**self.sample_csv_row, "Result": "FAILED", "Compliance Check Name (Wiz Subcategory)": "SI-3"},
            {**self.sample_csv_row, "Result": "fail", "Compliance Check Name (Wiz Subcategory)": "SI-4"},
        ]

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,  # Use threshold-based logic
                )
        self._initialize_processor_attributes(processor)

        # Mock fetch_compliance_data to return test data
        with patch.object(processor, "fetch_compliance_data", return_value=test_data):
            processor._process_compliance_data_without_filtering()

        # Should correctly categorize 6 items total: 3 passing, 3 failing
        self.assertEqual(len(processor.all_compliance_items), 6)
        self.assertEqual(len(processor.failed_compliance_items), 3)

        # Verify that the failed items have the correct results (case-insensitive matching)
        failed_results = [item.compliance_result for item in processor.failed_compliance_items]
        expected_failed_results = ["Failed", "FAILED", "fail"]
        self.assertEqual(sorted(failed_results), sorted(expected_failed_results))


@pytest.mark.no_parallel
@patch("regscale.integrations.compliance_integration.ComplianceIntegration.__init__", return_value=None)
class TestWizComplianceControlCategorization(unittest.TestCase):
    """Test suite for control categorization and aggregation logic."""

    def _initialize_processor_attributes(self, processor):
        """Initialize parent class attributes that would normally be set by __init__."""
        from collections import defaultdict

        processor.all_compliance_items = []
        processor.failed_compliance_items = []
        processor.passing_controls = {}
        processor.failing_controls = {}
        processor.asset_compliance_map = defaultdict(list)

    def test_control_categorization_all_pass(self, mock_parent_init):
        """Test control categorization when all items pass."""
        test_data = [
            {
                "Result": "Pass",
                "Compliance Check Name (Wiz Subcategory)": "AC-2(1)",
                "Resource Name": "vm1",
                "Cloud Provider ID": "id1",
            },
            {
                "Result": "PASS",
                "Compliance Check Name (Wiz Subcategory)": "AC-2(1)",
                "Resource Name": "vm2",
                "Cloud Provider ID": "id2",
            },
            {
                "Result": "pass",
                "Compliance Check Name (Wiz Subcategory)": "AC-2(1)",
                "Resource Name": "vm3",
                "Cloud Provider ID": "id3",
            },
        ]

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,  # Use threshold-based logic
                )
        self._initialize_processor_attributes(processor)

        # Fill in required fields for test data
        full_test_data = []
        for item in test_data:
            full_item = {
                "Resource Name": item["Resource Name"],
                "Cloud Provider": "Azure",
                "Cloud Provider ID": item["Cloud Provider ID"],
                "Resource ID": item["Cloud Provider ID"],
                "Resource Region": "East US",
                "Subscription": "sub-1",
                "Subscription Name": "Test Sub",
                "Policy Name": "Test Policy",
                "Policy ID": "policy-001",
                "Result": item["Result"],
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": item["Compliance Check Name (Wiz Subcategory)"],
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this",
            }
            full_test_data.append(full_item)

        with patch.object(processor, "fetch_compliance_data", return_value=full_test_data):
            processor.process_compliance_data()  # This will use threshold-based logic since bypass_control_filtering=False

        # Should have AC-2(1) as passing control since all items pass
        self.assertEqual(len(processor.passing_controls), 1)
        self.assertEqual(len(processor.failing_controls), 0)
        self.assertIn("ac-2(1)", processor.passing_controls)

    def test_control_categorization_all_fail(self, mock_parent_init):
        """Test control categorization when all items fail."""
        test_data = [
            {
                "Result": "Failed",
                "Compliance Check Name (Wiz Subcategory)": "AC-3",
                "Resource Name": "vm1",
                "Cloud Provider ID": "id1",
            },
            {
                "Result": "FAILED",
                "Compliance Check Name (Wiz Subcategory)": "AC-3",
                "Resource Name": "vm2",
                "Cloud Provider ID": "id2",
            },
            {
                "Result": "fail",
                "Compliance Check Name (Wiz Subcategory)": "AC-3",
                "Resource Name": "vm3",
                "Cloud Provider ID": "id3",
            },
        ]

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,  # Use threshold-based logic
                )
        self._initialize_processor_attributes(processor)

        # Fill in required fields for test data
        full_test_data = []
        for item in test_data:
            full_item = {
                "Resource Name": item["Resource Name"],
                "Cloud Provider": "Azure",
                "Cloud Provider ID": item["Cloud Provider ID"],
                "Resource ID": item["Cloud Provider ID"],
                "Resource Region": "East US",
                "Subscription": "sub-1",
                "Subscription Name": "Test Sub",
                "Policy Name": "Test Policy",
                "Policy ID": "policy-001",
                "Result": item["Result"],
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": item["Compliance Check Name (Wiz Subcategory)"],
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this",
            }
            full_test_data.append(full_item)

        with patch.object(processor, "fetch_compliance_data", return_value=full_test_data):
            processor.process_compliance_data()  # This will use threshold-based logic since bypass_control_filtering=False

        # Should have AC-3 as failing control since all items fail
        self.assertEqual(len(processor.passing_controls), 0)
        self.assertEqual(len(processor.failing_controls), 1)
        self.assertIn("ac-3", processor.failing_controls)

    def test_control_categorization_mixed_results_high_failure_rate(self, mock_parent_init):
        """Test control categorization with mixed results above failure threshold."""
        # 5 items: 2 pass, 3 fail = 60% failure rate (above default 20% threshold)
        test_data = [
            {"Result": "Pass", "Resource Name": "vm1", "Cloud Provider ID": "id1"},
            {"Result": "Pass", "Resource Name": "vm2", "Cloud Provider ID": "id2"},
            {"Result": "Failed", "Resource Name": "vm3", "Cloud Provider ID": "id3"},
            {"Result": "Failed", "Resource Name": "vm4", "Cloud Provider ID": "id4"},
            {"Result": "Failed", "Resource Name": "vm5", "Cloud Provider ID": "id5"},
        ]

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,  # Use threshold-based logic
                )
        self._initialize_processor_attributes(processor)

        # Fill in required fields - all same control
        full_test_data = []
        for item in test_data:
            full_item = {
                "Resource Name": item["Resource Name"],
                "Cloud Provider": "Azure",
                "Cloud Provider ID": item["Cloud Provider ID"],
                "Resource ID": item["Cloud Provider ID"],
                "Resource Region": "East US",
                "Subscription": "sub-1",
                "Subscription Name": "Test Sub",
                "Policy Name": "Test Policy",
                "Policy ID": "policy-001",
                "Result": item["Result"],
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": "AC-4 Information Flow Enforcement",
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this",
            }
            full_test_data.append(full_item)

        with patch.object(processor, "fetch_compliance_data", return_value=full_test_data):
            processor.process_compliance_data()  # This will use threshold-based logic since bypass_control_filtering=False

        # Should categorize as failing due to high failure rate (60% > 20% threshold)
        self.assertEqual(len(processor.passing_controls), 0)
        self.assertEqual(len(processor.failing_controls), 1)
        self.assertIn("ac-4", processor.failing_controls)

    def test_control_categorization_mixed_results_fail_first(self, mock_parent_init):
        """Test control categorization with mixed results using fail-first logic."""
        # 10 items: 9 pass, 1 fail - with fail-first logic, any failure makes the control fail
        test_data = []
        for i in range(9):
            test_data.append({"Result": "Pass", "Resource Name": f"vm{i + 1}", "Cloud Provider ID": f"id{i + 1}"})
        test_data.append({"Result": "Failed", "Resource Name": "vm10", "Cloud Provider ID": "id10"})

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,
                )
        self._initialize_processor_attributes(processor)

        # Fill in required fields - all same control
        full_test_data = []
        for item in test_data:
            full_item = {
                "Resource Name": item["Resource Name"],
                "Cloud Provider": "Azure",
                "Cloud Provider ID": item["Cloud Provider ID"],
                "Resource ID": item["Cloud Provider ID"],
                "Resource Region": "East US",
                "Subscription": "sub-1",
                "Subscription Name": "Test Sub",
                "Policy Name": "Test Policy",
                "Policy ID": "policy-001",
                "Result": item["Result"],
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": "SI-2 Flaw Remediation",
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this",
            }
            full_test_data.append(full_item)

        with patch.object(processor, "fetch_compliance_data", return_value=full_test_data):
            processor.process_compliance_data()

        # With fail-first logic, any failure makes the control fail (1 failure out of 10)
        self.assertEqual(len(processor.passing_controls), 0)
        self.assertEqual(len(processor.failing_controls), 1)
        self.assertIn("si-2", processor.failing_controls)

    def test_control_categorization_fail_first_logic(self, mock_parent_init):
        """Test that Wiz compliance uses fail-first logic regardless of bypass_control_filtering setting."""
        # 10 items: 7 pass, 3 fail - with fail-first logic, this should be a failing control
        test_data = []
        for i in range(7):
            test_data.append({"Result": "Pass", "Resource Name": f"vm{i + 1}", "Cloud Provider ID": f"id{i + 1}"})
        for i in range(3):
            test_data.append({"Result": "Failed", "Resource Name": f"vm{i + 8}", "Cloud Provider ID": f"id{i + 8}"})

        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate", return_value="token"):
            with patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager"):
                processor = WizComplianceReportProcessor(
                    plan_id=123,
                    wiz_project_id="test-project",
                    client_id="client",
                    client_secret="secret",
                    bypass_control_filtering=False,
                )
        self._initialize_processor_attributes(processor)

        # Fill in required fields - all same control
        full_test_data = []
        for item in test_data:
            full_item = {
                "Resource Name": item["Resource Name"],
                "Cloud Provider": "Azure",
                "Cloud Provider ID": item["Cloud Provider ID"],
                "Resource ID": item["Cloud Provider ID"],
                "Resource Region": "East US",
                "Subscription": "sub-1",
                "Subscription Name": "Test Sub",
                "Policy Name": "Test Policy",
                "Policy ID": "policy-001",
                "Result": item["Result"],
                "Severity": "HIGH",
                "Compliance Check Name (Wiz Subcategory)": "CM-3 Configuration Change Control",
                "Framework": "NIST SP 800-53 Revision 5",
                "Remediation Steps": "Fix this",
            }
            full_test_data.append(full_item)

        with patch.object(processor, "fetch_compliance_data", return_value=full_test_data):
            processor.process_compliance_data()

        # With fail-first logic, any failures make the control fail
        self.assertEqual(len(processor.passing_controls), 0)
        self.assertEqual(len(processor.failing_controls), 1)
        self.assertIn("cm-3", processor.failing_controls)


if __name__ == "__main__":
    unittest.main()
