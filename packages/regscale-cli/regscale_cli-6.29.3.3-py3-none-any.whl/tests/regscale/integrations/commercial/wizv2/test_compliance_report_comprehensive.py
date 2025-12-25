#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for Wiz Compliance Report Integration.

This test suite provides extensive coverage of WizComplianceReportItem and
WizComplianceReportProcessor classes, focusing on:
- CSV parsing and data transformation
- Control mapping and categorization
- Issue creation from compliance items
- Report file management
- Control implementation status updates
"""

import csv
import gzip
import os
import tempfile
import unittest
from collections import defaultdict
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, PropertyMock, call, mock_open, patch

import pytest

from regscale.integrations.commercial.wizv2.compliance_report import (
    WizComplianceReportItem,
    WizComplianceReportProcessor,
)
from regscale.models import regscale_models


class TestWizComplianceReportItemComprehensive(unittest.TestCase):
    """Comprehensive test suite for WizComplianceReportItem class."""

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

    def test_get_status_pass(self):
        """Test get_status returns 'Satisfied' for Pass result."""
        item = WizComplianceReportItem(self.sample_csv_row)
        self.assertEqual(item.get_status(), "Satisfied")

    def test_get_status_fail(self):
        """Test get_status returns 'Other Than Satisfied' for Fail result."""
        csv_row = {**self.sample_csv_row, "Result": "Fail"}
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_status(), "Other Than Satisfied")

    def test_get_implementation_status_pass(self):
        """Test get_implementation_status returns 'Implemented' for Pass result."""
        item = WizComplianceReportItem(self.sample_csv_row)
        self.assertEqual(item.get_implementation_status(), "Implemented")

    def test_get_implementation_status_fail(self):
        """Test get_implementation_status returns 'In Remediation' for Fail result."""
        csv_row = {**self.sample_csv_row, "Result": "Failed"}
        item = WizComplianceReportItem(csv_row)
        self.assertEqual(item.get_implementation_status(), "In Remediation")

    def test_get_severity_mapping(self):
        """Test get_severity correctly maps Wiz severities to RegScale severities."""
        test_cases = [
            ("CRITICAL", "High"),
            ("HIGH", "High"),
            ("MEDIUM", "Moderate"),
            ("LOW", "Low"),
            ("INFORMATIONAL", "Low"),
            ("unknown", "Low"),
        ]

        for wiz_severity, expected_regscale_severity in test_cases:
            csv_row = {**self.sample_csv_row, "Severity": wiz_severity}
            item = WizComplianceReportItem(csv_row)
            self.assertEqual(item.get_severity(), expected_regscale_severity)

    def test_get_unique_resource_name_with_region(self):
        """Test get_unique_resource_name includes region when available."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_unique_resource_name()
        self.assertIn("test-vm-001", result)
        self.assertIn("East US", result)

    def test_get_unique_resource_name_no_region(self):
        """Test get_unique_resource_name works without region."""
        csv_row = {**self.sample_csv_row, "Resource Region": ""}
        item = WizComplianceReportItem(csv_row)
        result = item.get_unique_resource_name()
        self.assertIn("test-vm-001", result)

    def test_get_unique_resource_name_with_resource_id(self):
        """Test get_unique_resource_name includes resource ID suffix."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_unique_resource_name()
        # Should include the last part of the resource ID
        self.assertIn("test-vm-001", result)

    def test_get_unique_resource_name_no_name(self):
        """Test get_unique_resource_name defaults to 'Unknown Resource' when name is empty."""
        csv_row = {**self.sample_csv_row, "Resource Name": ""}
        item = WizComplianceReportItem(csv_row)
        result = item.get_unique_resource_name()
        self.assertIn("Unknown Resource", result)

    def test_get_unique_resource_name_truncates_long_ids(self):
        """Test get_unique_resource_name truncates long resource IDs."""
        csv_row = {
            **self.sample_csv_row,
            "Resource ID": "/subscriptions/12345/resourceGroups/rg-test/providers/Microsoft.Compute/virtualMachines/very-long-resource-name-that-should-be-truncated",
        }
        item = WizComplianceReportItem(csv_row)
        result = item.get_unique_resource_name()
        # Should truncate to 12 chars
        self.assertIn("[", result)
        self.assertIn("]", result)

    def test_get_unique_issue_identifier(self):
        """Test get_unique_issue_identifier creates unique identifier for deduplication."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_unique_issue_identifier()
        self.assertIn("|", result)
        self.assertIn("policy-disk-encryption-001", result)

    def test_get_title(self):
        """Test get_title returns formatted title."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_title()
        self.assertIn("AC-2(1)", result)
        self.assertIn("Ensure VM disk encryption is enabled", result)

    def test_get_description(self):
        """Test get_description returns formatted description."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_description()
        self.assertIn("Wiz compliance assessment", result)
        self.assertIn("Ensure VM disk encryption is enabled", result)

    def test_get_finding_details(self):
        """Test get_finding_details returns formatted details."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_finding_details()
        self.assertIn("Resource:", result)
        self.assertIn("Cloud Provider:", result)
        self.assertIn("Azure", result)
        self.assertIn("Result:", result)
        self.assertIn("Remediation:", result)

    def test_get_finding_details_with_subscription(self):
        """Test get_finding_details includes subscription when present."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_finding_details()
        self.assertIn("Subscription:", result)
        self.assertIn("Dev Subscription", result)

    def test_get_asset_identifier(self):
        """Test get_asset_identifier returns correct identifier."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.get_asset_identifier()
        self.assertEqual(result, self.sample_csv_row["Cloud Provider ID"])

    def test_affected_controls_single_control(self):
        """Test affected_controls property with single control."""
        item = WizComplianceReportItem(self.sample_csv_row)
        result = item.affected_controls
        self.assertEqual(result, "AC-2(1)")

    def test_affected_controls_multiple_controls(self):
        """Test affected_controls property with multiple controls."""
        csv_row = {
            **self.sample_csv_row,
            "Compliance Check Name (Wiz Subcategory)": "AC-2(1) Account Management, AC-3 Access Enforcement",
        }
        item = WizComplianceReportItem(csv_row)
        result = item.affected_controls
        self.assertEqual(result, "AC-2(1),AC-3")


@pytest.mark.no_parallel
@patch("regscale.integrations.compliance_integration.ComplianceIntegration.__init__", return_value=None)
class TestWizComplianceReportProcessorComprehensive(unittest.TestCase):
    """Comprehensive test suite for WizComplianceReportProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_plan_id = 12345
        self.test_project_id = "test-project-123"
        self.test_client_id = "test-client-id"
        self.test_client_secret = "test-client-secret"

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.WizReportManager")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.ControlMatcher")
    def test_init_successful(self, mock_control_matcher, mock_report_manager, mock_auth, mock_parent_init):
        """Test successful initialization of WizComplianceReportProcessor."""
        mock_auth.return_value = "test-access-token"
        mock_parent_init.return_value = None

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        self.assertEqual(processor.wiz_project_id, self.test_project_id)
        mock_auth.assert_called_once_with(self.test_client_id, self.test_client_secret)
        mock_report_manager.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    @patch("regscale.integrations.commercial.wizv2.compliance_report.error_and_exit")
    def test_init_authentication_failure(self, mock_error_exit, mock_auth, mock_parent_init):
        """Test initialization handles authentication failure."""
        mock_auth.return_value = None
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            WizComplianceReportProcessor(
                plan_id=self.test_plan_id,
                wiz_project_id=self.test_project_id,
                client_id=self.test_client_id,
                client_secret=self.test_client_secret,
            )

        mock_error_exit.assert_called_once_with("Failed to authenticate with Wiz")

    def test_parse_csv_report(self, mock_parent_init):
        """Test parse_csv_report successfully parses CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(
                temp_file,
                fieldnames=[
                    "Resource Name",
                    "Cloud Provider",
                    "Cloud Provider ID",
                    "Resource ID",
                    "Resource Region",
                    "Subscription",
                    "Subscription Name",
                    "Policy Name",
                    "Policy ID",
                    "Result",
                    "Severity",
                    "Compliance Check Name (Wiz Subcategory)",
                    "Framework",
                    "Remediation Steps",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Resource Name": "test-vm",
                    "Cloud Provider": "Azure",
                    "Cloud Provider ID": "test-id",
                    "Resource ID": "test-resource-id",
                    "Resource Region": "East US",
                    "Subscription": "sub-123",
                    "Subscription Name": "Test Sub",
                    "Policy Name": "Test Policy",
                    "Policy ID": "policy-123",
                    "Result": "Pass",
                    "Severity": "HIGH",
                    "Compliance Check Name (Wiz Subcategory)": "AC-2 Account Management",
                    "Framework": "NIST 800-53",
                    "Remediation Steps": "Fix it",
                }
            )
            temp_file.flush()

            try:
                with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate") as mock_auth:
                    mock_auth.return_value = "test-token"
                    processor = WizComplianceReportProcessor(
                        plan_id=self.test_plan_id,
                        wiz_project_id=self.test_project_id,
                        client_id=self.test_client_id,
                        client_secret=self.test_client_secret,
                    )

                    items = processor.parse_csv_report(temp_file.name)
                    self.assertEqual(len(items), 1)
                    self.assertIsInstance(items[0], WizComplianceReportItem)
                    self.assertEqual(items[0]._resource_name, "test-vm")
            finally:
                os.unlink(temp_file.name)

    def test_parse_csv_report_gzipped(self, mock_parent_init):
        """Test parse_csv_report handles gzipped files."""
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as temp_file:
            with gzip.open(temp_file.name, "wt", encoding="utf-8") as gz_file:
                writer = csv.DictWriter(
                    gz_file,
                    fieldnames=[
                        "Resource Name",
                        "Cloud Provider",
                        "Cloud Provider ID",
                        "Resource ID",
                        "Resource Region",
                        "Subscription",
                        "Subscription Name",
                        "Policy Name",
                        "Policy ID",
                        "Result",
                        "Severity",
                        "Compliance Check Name (Wiz Subcategory)",
                        "Framework",
                        "Remediation Steps",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Resource Name": "test-vm",
                        "Cloud Provider": "Azure",
                        "Cloud Provider ID": "test-id",
                        "Resource ID": "test-resource-id",
                        "Resource Region": "East US",
                        "Subscription": "sub-123",
                        "Subscription Name": "Test Sub",
                        "Policy Name": "Test Policy",
                        "Policy ID": "policy-123",
                        "Result": "Pass",
                        "Severity": "HIGH",
                        "Compliance Check Name (Wiz Subcategory)": "AC-2 Account Management",
                        "Framework": "NIST 800-53",
                        "Remediation Steps": "Fix it",
                    }
                )

            try:
                with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate") as mock_auth:
                    mock_auth.return_value = "test-token"
                    processor = WizComplianceReportProcessor(
                        plan_id=self.test_plan_id,
                        wiz_project_id=self.test_project_id,
                        client_id=self.test_client_id,
                        client_secret=self.test_client_secret,
                    )

                    items = processor.parse_csv_report(temp_file.name)
                    self.assertEqual(len(items), 1)
                    self.assertIsInstance(items[0], WizComplianceReportItem)
            finally:
                os.unlink(temp_file.name)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.logger")
    def test_parse_csv_report_error_handling(self, mock_logger, mock_parent_init):
        """Test parse_csv_report handles errors gracefully."""
        with patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate") as mock_auth:
            mock_auth.return_value = "test-token"
            processor = WizComplianceReportProcessor(
                plan_id=self.test_plan_id,
                wiz_project_id=self.test_project_id,
                client_id=self.test_client_id,
                client_secret=self.test_client_secret,
            )

            items = processor.parse_csv_report("/nonexistent/file.csv")
            self.assertEqual(len(items), 0)
            mock_logger.error.assert_called()

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_fetch_compliance_data_with_provided_file(self, mock_auth, mock_parent_init):
        """Test fetch_compliance_data uses provided report file path."""
        mock_auth.return_value = "test-token"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(
                temp_file,
                fieldnames=[
                    "Resource Name",
                    "Cloud Provider",
                    "Cloud Provider ID",
                    "Resource ID",
                    "Resource Region",
                    "Subscription",
                    "Subscription Name",
                    "Policy Name",
                    "Policy ID",
                    "Result",
                    "Severity",
                    "Compliance Check Name (Wiz Subcategory)",
                    "Framework",
                    "Remediation Steps",
                ],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "Resource Name": "test-vm",
                    "Cloud Provider": "Azure",
                    "Cloud Provider ID": "test-id",
                    "Resource ID": "test-resource-id",
                    "Resource Region": "East US",
                    "Subscription": "sub-123",
                    "Subscription Name": "Test Sub",
                    "Policy Name": "Test Policy",
                    "Policy ID": "policy-123",
                    "Result": "Pass",
                    "Severity": "HIGH",
                    "Compliance Check Name (Wiz Subcategory)": "AC-2 Account Management",
                    "Framework": "NIST 800-53",
                    "Remediation Steps": "Fix it",
                }
            )
            temp_file.flush()

            try:
                processor = WizComplianceReportProcessor(
                    plan_id=self.test_plan_id,
                    wiz_project_id=self.test_project_id,
                    client_id=self.test_client_id,
                    client_secret=self.test_client_secret,
                    report_file_path=temp_file.name,
                )

                raw_data = processor.fetch_compliance_data()
                self.assertEqual(len(raw_data), 1)
                self.assertEqual(raw_data[0]["Resource Name"], "test-vm")
            finally:
                os.unlink(temp_file.name)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_create_compliance_item(self, mock_auth, mock_parent_init):
        """Test create_compliance_item creates WizComplianceReportItem."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        raw_data = {
            "Resource Name": "test-vm",
            "Cloud Provider": "Azure",
            "Cloud Provider ID": "test-id",
            "Resource ID": "test-resource-id",
            "Resource Region": "East US",
            "Subscription": "sub-123",
            "Subscription Name": "Test Sub",
            "Policy Name": "Test Policy",
            "Policy ID": "policy-123",
            "Result": "Pass",
            "Severity": "HIGH",
            "Compliance Check Name (Wiz Subcategory)": "AC-2 Account Management",
            "Framework": "NIST 800-53",
            "Remediation Steps": "Fix it",
        }

        item = processor.create_compliance_item(raw_data)
        self.assertIsInstance(item, WizComplianceReportItem)
        self.assertEqual(item._resource_name, "test-vm")

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_map_string_severity_to_enum(self, mock_auth, mock_parent_init):
        """Test _map_string_severity_to_enum correctly maps severities."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        test_cases = [
            ("CRITICAL", regscale_models.IssueSeverity.Critical),
            ("HIGH", regscale_models.IssueSeverity.High),
            ("MEDIUM", regscale_models.IssueSeverity.Moderate),
            ("MODERATE", regscale_models.IssueSeverity.Moderate),
            ("LOW", regscale_models.IssueSeverity.Low),
            ("INFORMATIONAL", regscale_models.IssueSeverity.Low),
            ("unknown", regscale_models.IssueSeverity.Low),
        ]

        for severity_str, expected_enum in test_cases:
            result = processor._map_string_severity_to_enum(severity_str)
            self.assertEqual(result, expected_enum)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_process_compliance_data_with_bypass(self, mock_auth, mock_parent_init):
        """Test process_compliance_data uses bypass logic when enabled."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
            bypass_control_filtering=True,
        )

        with patch.object(processor, "_process_compliance_data_without_filtering") as mock_method:
            processor.process_compliance_data()
            mock_method.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_reset_compliance_state(self, mock_auth, mock_parent_init):
        """Test _reset_compliance_state clears all state variables."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Add some data
        processor.all_compliance_items = [Mock()]
        processor.failed_compliance_items = [Mock()]
        processor.passing_controls = {"ac-2": Mock()}
        processor.failing_controls = {"ac-3": Mock()}
        processor.asset_compliance_map = defaultdict(list)
        processor.asset_compliance_map["asset-1"] = [Mock()]

        # Reset state
        processor._reset_compliance_state()

        self.assertEqual(len(processor.all_compliance_items), 0)
        self.assertEqual(len(processor.failed_compliance_items), 0)
        self.assertEqual(len(processor.passing_controls), 0)
        self.assertEqual(len(processor.failing_controls), 0)
        self.assertEqual(len(processor.asset_compliance_map), 0)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_is_valid_compliance_item_for_processing(self, mock_auth, mock_parent_init):
        """Test _is_valid_compliance_item_for_processing validates items correctly."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Valid item
        valid_item = Mock()
        valid_item.control_id = "AC-2"
        valid_item.resource_id = "resource-123"
        self.assertTrue(processor._is_valid_compliance_item_for_processing(valid_item))

        # Missing control_id
        invalid_item = Mock()
        invalid_item.control_id = ""
        invalid_item.resource_id = "resource-123"
        self.assertFalse(processor._is_valid_compliance_item_for_processing(invalid_item))

        # Missing resource_id
        invalid_item = Mock()
        invalid_item.control_id = "AC-2"
        invalid_item.resource_id = ""
        self.assertFalse(processor._is_valid_compliance_item_for_processing(invalid_item))

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_add_compliance_item_to_collections(self, mock_auth, mock_parent_init):
        """Test _add_compliance_item_to_collections adds items correctly."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Initialize attributes that would normally be set by parent __init__
        processor.all_compliance_items = []
        processor.failed_compliance_items = []
        processor.asset_compliance_map = defaultdict(list)
        processor.FAIL_STATUSES = ["Fail", "Failed"]

        # Create a mock compliance item
        compliance_item = Mock()
        compliance_item.resource_id = "resource-123"
        compliance_item.compliance_result = "Fail"

        processor._add_compliance_item_to_collections(compliance_item)

        self.assertEqual(len(processor.all_compliance_items), 1)
        self.assertEqual(len(processor.failed_compliance_items), 1)
        self.assertEqual(len(processor.asset_compliance_map["resource-123"]), 1)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_get_control_ids_for_item(self, mock_auth, mock_parent_init):
        """Test _get_control_ids_for_item extracts control IDs."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Item with get_all_control_ids method
        item_with_method = Mock()
        item_with_method.get_all_control_ids.return_value = ["AC-2", "AC-3"]
        result = processor._get_control_ids_for_item(item_with_method)
        self.assertEqual(result, ["AC-2", "AC-3"])

        # Item without get_all_control_ids method
        item_without_method = Mock(spec=["control_id"])
        item_without_method.control_id = "AC-2"
        result = processor._get_control_ids_for_item(item_without_method)
        self.assertEqual(result, ["AC-2"])

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_is_compliance_item_failing(self, mock_auth, mock_parent_init):
        """Test _is_compliance_item_failing correctly identifies failing items."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        processor.FAIL_STATUSES = ["Fail", "Failed", "Error"]

        # Failing item
        failing_item = Mock()
        failing_item.compliance_result = "Fail"
        self.assertTrue(processor._is_compliance_item_failing(failing_item))

        # Passing item
        passing_item = Mock()
        passing_item.compliance_result = "Pass"
        self.assertFalse(processor._is_compliance_item_failing(passing_item))

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_remove_duplicate_items(self, mock_auth, mock_parent_init):
        """Test _remove_duplicate_items removes duplicates while preserving order."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Create duplicate items
        item1 = Mock()
        item1.resource_id = "resource-1"
        item1.control_id = "AC-2"

        item2 = Mock()
        item2.resource_id = "resource-2"
        item2.control_id = "AC-3"

        item3 = Mock()
        item3.resource_id = "resource-1"
        item3.control_id = "AC-2"

        items = [item1, item2, item3]
        result = processor._remove_duplicate_items(items)

        self.assertEqual(len(result), 2)
        self.assertIn(item1, result)
        self.assertIn(item2, result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_map_severity_to_priority(self, mock_auth, mock_parent_init):
        """Test _map_severity_to_priority maps severities to priorities."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # The method uses hasattr(severity, "value") to check if it's an enum
        # When it's an enum, it converts it to string which gives the value attribute
        # Since the enum value is complex (e.g., "0 - Critical - Critical Deficiency"),
        # it won't match the priority map and will default to "Low"
        # The method is designed to work with string severities like "Critical", "High", etc.

        # Test with string severities (actual use case)
        test_cases_strings = [
            ("Critical", "High"),
            ("High", "High"),
            ("Moderate", "Moderate"),
            ("Low", "Low"),
            ("Unknown", "Low"),  # Default case
        ]

        for severity_str, expected_priority in test_cases_strings:
            # Create a mock object with a value attribute to simulate an enum
            mock_severity = Mock()
            mock_severity.value = severity_str
            result = processor._map_severity_to_priority(mock_severity)
            self.assertEqual(result, expected_priority)

        # Test with direct string (no value attribute)
        for severity_str, expected_priority in test_cases_strings:
            result = processor._map_severity_to_priority(severity_str)
            self.assertEqual(result, expected_priority)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_determine_highest_severity(self, mock_auth, mock_parent_init):
        """Test _determine_highest_severity returns highest severity."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Test with CRITICAL
        result = processor._determine_highest_severity(["LOW", "MEDIUM", "CRITICAL", "HIGH"])
        self.assertEqual(result, "CRITICAL")

        # Test with HIGH
        result = processor._determine_highest_severity(["LOW", "MEDIUM", "HIGH"])
        self.assertEqual(result, "HIGH")

        # Test with empty list
        result = processor._determine_highest_severity([])
        self.assertEqual(result, "HIGH")

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_collect_resource_information(self, mock_auth, mock_parent_init):
        """Test _collect_resource_information aggregates resource info."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Create mock failed items
        item1 = Mock()
        item1.resource_name = "resource-1"
        item1.severity = "HIGH"
        item1.description = "Description 1"

        item2 = Mock()
        item2.resource_name = "resource-2"
        item2.severity = "MEDIUM"
        item2.description = "Description 2"

        failed_items = [item1, item2]
        result = processor._collect_resource_information(failed_items)

        self.assertIn("resource-1", result["affected_resources"])
        self.assertIn("resource-2", result["affected_resources"])
        self.assertIn("HIGH", result["severities"])
        self.assertIn("MEDIUM", result["severities"])
        self.assertEqual(len(result["descriptions"]), 2)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_build_consolidated_description(self, mock_auth, mock_parent_init):
        """Test _build_consolidated_description formats description correctly."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        resource_info = {
            "affected_resources": {"resource-1", "resource-2"},
            "descriptions": ["- resource-1: Description 1", "- resource-2: Description 2"],
        }

        result = processor._build_consolidated_description("AC-2", resource_info)

        self.assertIn("Control AC-2", result)
        self.assertIn("2 resource(s)", result)
        self.assertIn("Description 1", result)
        self.assertIn("Description 2", result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_build_consolidated_description_truncates_long_lists(self, mock_auth, mock_parent_init):
        """Test _build_consolidated_description truncates long resource lists."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        # Create 15 descriptions
        descriptions = [f"- resource-{i}: Description {i}" for i in range(15)]
        resource_info = {"affected_resources": set([f"resource-{i}" for i in range(15)]), "descriptions": descriptions}

        result = processor._build_consolidated_description("AC-2", resource_info)

        self.assertIn("15 resource(s)", result)
        self.assertIn("and 5 more resources", result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_is_control_already_processed(self, mock_auth, mock_parent_init):
        """Test _is_control_already_processed checks for duplicates."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        processed_controls = {"ac-2", "ac-3"}

        # Test with processed control (case insensitive)
        self.assertTrue(processor._is_control_already_processed("AC-2", processed_controls))
        self.assertTrue(processor._is_control_already_processed("ac-2", processed_controls))

        # Test with unprocessed control
        self.assertFalse(processor._is_control_already_processed("AC-4", processed_controls))

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_find_recent_report_finds_recent_file(self, mock_auth, mock_parent_init):
        """Test _find_recent_report finds recent report file."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a recent report file
            report_file = os.path.join(temp_dir, f"compliance_report_{self.test_project_id}_20231201_120000.csv")
            with open(report_file, "w") as f:
                f.write("test")

            with patch("regscale.integrations.commercial.wizv2.compliance_report.os.path.exists") as mock_exists:
                with patch("regscale.integrations.commercial.wizv2.compliance_report.os.listdir") as mock_listdir:
                    mock_exists.return_value = True
                    mock_listdir.return_value = [os.path.basename(report_file)]

                    with patch(
                        "regscale.integrations.commercial.wizv2.compliance_report.os.path.getmtime"
                    ) as mock_mtime:
                        # Set modification time to now
                        mock_mtime.return_value = datetime.now().timestamp()

                        result = processor._find_recent_report(max_age_hours=24)
                        self.assertIsNotNone(result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_find_recent_report_no_directory(self, mock_auth, mock_parent_init):
        """Test _find_recent_report returns None when directory doesn't exist."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        with patch("regscale.integrations.commercial.wizv2.compliance_report.os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = processor._find_recent_report()
            self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.compliance_report.wiz_authenticate")
    def test_process_compliance_sync(self, mock_auth, mock_parent_init):
        """Test process_compliance_sync calls sync_compliance."""
        mock_auth.return_value = "test-token"

        processor = WizComplianceReportProcessor(
            plan_id=self.test_plan_id,
            wiz_project_id=self.test_project_id,
            client_id=self.test_client_id,
            client_secret=self.test_client_secret,
        )

        with patch.object(processor, "sync_compliance") as mock_sync:
            processor.process_compliance_sync()
            mock_sync.assert_called_once()


if __name__ == "__main__":
    unittest.main()
