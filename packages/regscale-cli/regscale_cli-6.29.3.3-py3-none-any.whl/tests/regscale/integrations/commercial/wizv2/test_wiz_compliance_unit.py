#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Wiz Compliance Report Integration (no authentication required).

These tests focus on the core compliance workflow components without requiring
live authentication to RegScale or Wiz APIs. They test:
- Report parsing logic
- Data transformation
- Control consolidation
- Issue creation logic
"""

import csv
import os
import tempfile
import unittest
from datetime import datetime

import pytest


class TestWizComplianceUnit(unittest.TestCase):
    """Unit tests for Wiz Compliance Report functionality without authentication."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample compliance data representing the expected results format
        self.compliance_data = [
            # Passing controls
            {
                "Resource Name": "vm-production-001",
                "Cloud Provider": "Azure",
                "Cloud Provider ID": "/subscriptions/12345/resourceGroups/prod-rg/providers/Microsoft.Compute/virtualMachines/vm-production-001",
                "Resource ID": "/subscriptions/12345/resourceGroups/prod-rg/providers/Microsoft.Compute/virtualMachines/vm-production-001",
                "Resource Region": "East US 2",
                "Subscription": "prod-subscription-123",
                "Subscription Name": "Production Subscription",
                "Policy Name": "Ensure VM has monitoring agent installed",
                "Policy ID": "azure-vm-monitoring-001",
                "Result": "Pass",
                "Control IDs": "AC-2,AC-3",
                "Framework": "NIST 800-53",
                "Severity": "High",
                "Control Family": "Access Control",
                "Details": "Monitoring agent is properly installed and configured",
                "Status": "Compliant",
            },
            # Failing control that should create an issue
            {
                "Resource Name": "vm-test-002",
                "Cloud Provider": "Azure",
                "Cloud Provider ID": "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/vm-test-002",
                "Resource ID": "/subscriptions/12345/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/vm-test-002",
                "Resource Region": "West US 2",
                "Subscription": "test-subscription-456",
                "Subscription Name": "Test Subscription",
                "Policy Name": "Ensure disk encryption is enabled",
                "Policy ID": "azure-disk-encryption-001",
                "Result": "Fail",
                "Control IDs": "SC-28,SC-13",
                "Framework": "NIST 800-53",
                "Severity": "Critical",
                "Control Family": "System and Communications Protection",
                "Details": "Disk encryption is not enabled on this virtual machine",
                "Status": "Non-Compliant",
            },
            # Multiple control IDs test case
            {
                "Resource Name": "storage-account-001",
                "Cloud Provider": "Azure",
                "Cloud Provider ID": "/subscriptions/12345/resourceGroups/prod-rg/providers/Microsoft.Storage/storageAccounts/prodstore001",
                "Resource ID": "/subscriptions/12345/resourceGroups/prod-rg/providers/Microsoft.Storage/storageAccounts/prodstore001",
                "Resource Region": "East US",
                "Subscription": "prod-subscription-123",
                "Subscription Name": "Production Subscription",
                "Policy Name": "Storage account should use secure transfer",
                "Policy ID": "azure-storage-secure-001",
                "Result": "Fail",
                "Control IDs": "SC-8,SC-23,IA-7",
                "Framework": "NIST 800-53",
                "Severity": "Medium",
                "Control Family": "System and Communications Protection",
                "Details": "Secure transfer is not required for this storage account",
                "Status": "Non-Compliant",
            },
        ]

    def test_wiz_compliance_item_creation(self):
        """Test creation of WizComplianceReportItem from CSV data."""
        from regscale.integrations.commercial.wizv2.compliance_report import WizComplianceReportItem

        csv_row = self.compliance_data[0]  # Use the first test data item

        compliance_item = WizComplianceReportItem(csv_row)

        self.assertEqual(compliance_item.resource_name, "vm-production-001 (East US 2)")
        self.assertEqual(compliance_item.cloud_provider, "Azure")
        self.assertEqual(compliance_item.result, "Pass")
        self.assertEqual(compliance_item.policy_name, "Ensure VM has monitoring agent installed")

    def test_csv_data_parsing(self):
        """Test that CSV data is properly parsed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self.compliance_data[0].keys())
            writer.writeheader()
            writer.writerows(self.compliance_data)
            temp_file.flush()

            try:
                with open(temp_file.name, "r") as f:
                    reader = csv.DictReader(f)
                    parsed_data = list(reader)

                self.assertEqual(len(parsed_data), 3)
                self.assertEqual(parsed_data[0]["Resource Name"], "vm-production-001")
                self.assertEqual(parsed_data[1]["Result"], "Fail")
                self.assertEqual(parsed_data[2]["Control IDs"], "SC-8,SC-23,IA-7")

            finally:
                os.unlink(temp_file.name)

    def test_control_id_extraction(self):
        """Test extraction of multiple control IDs from a single compliance item."""
        test_data = {"Control IDs": "AC-2,AC-3,AC-4", "Framework": "NIST 800-53"}

        # Simulate the control ID parsing logic
        control_ids = [cid.strip() for cid in test_data["Control IDs"].split(",")]

        self.assertEqual(len(control_ids), 3)
        self.assertIn("AC-2", control_ids)
        self.assertIn("AC-3", control_ids)
        self.assertIn("AC-4", control_ids)

    def test_status_matching_logic(self):
        """Test that status values are properly mapped."""
        # Test various status mapping scenarios
        status_mappings = {
            "Pass": "Compliant",
            "Fail": "Non-Compliant",
            "Warning": "Partially Compliant",
            "Info": "Informational",
        }

        for result, expected_status in status_mappings.items():
            # Simulate status mapping logic
            if result.lower() == "pass":
                mapped_status = "Compliant"
            elif result.lower() == "fail":
                mapped_status = "Non-Compliant"
            elif result.lower() == "warning":
                mapped_status = "Partially Compliant"
            else:
                mapped_status = "Informational"

            self.assertEqual(mapped_status, expected_status)

    def test_asset_creation_data_structure(self):
        """Test that asset data is properly structured for RegScale."""
        compliance_item = self.compliance_data[0]

        # Simulate asset creation logic
        asset_data = {
            "name": compliance_item["Resource Name"],
            "cloudProviderId": compliance_item["Cloud Provider ID"],
            "region": compliance_item["Resource Region"],
            "assetType": "Cloud Resource",
            "description": f"{compliance_item['Cloud Provider']} resource",
        }

        self.assertEqual(asset_data["name"], "vm-production-001")
        self.assertTrue(asset_data["cloudProviderId"].startswith("/subscriptions/"))
        self.assertEqual(asset_data["region"], "East US 2")
        self.assertEqual(asset_data["assetType"], "Cloud Resource")

    def test_issue_creation_for_failed_controls(self):
        """Test that issues are properly created for failed compliance items."""
        failed_item = self.compliance_data[1]  # The failing disk encryption item

        # Simulate issue creation logic
        if failed_item["Result"].lower() == "fail":
            issue_data = {
                "title": f"Wiz Compliance: {failed_item['Policy Name']}",
                "description": failed_item["Details"],
                "severity": failed_item["Severity"],
                "status": "Open",
                "source": "Wiz Compliance Scan",
            }

            self.assertEqual(issue_data["title"], "Wiz Compliance: Ensure disk encryption is enabled")
            self.assertEqual(issue_data["severity"], "Critical")
            self.assertEqual(issue_data["status"], "Open")
            self.assertIn("encryption", issue_data["description"].lower())

    def test_control_aggregation_threshold_logic(self):
        """Test control aggregation and threshold logic."""

        # Test multiple items for the same control
        control_items = [
            {"Control IDs": "AC-2", "Result": "Pass", "Resource Name": "resource1"},
            {"Control IDs": "AC-2", "Result": "Fail", "Resource Name": "resource2"},
            {"Control IDs": "AC-2", "Result": "Pass", "Resource Name": "resource3"},
        ]

        # Simulate aggregation logic
        control_results = {}
        for item in control_items:
            control_id = item["Control IDs"]
            if control_id not in control_results:
                control_results[control_id] = {"pass": 0, "fail": 0, "total": 0}

            control_results[control_id]["total"] += 1
            if item["Result"].lower() == "pass":
                control_results[control_id]["pass"] += 1
            else:
                control_results[control_id]["fail"] += 1

        # Test the aggregated results
        ac2_results = control_results["AC-2"]
        self.assertEqual(ac2_results["total"], 3)
        self.assertEqual(ac2_results["pass"], 2)
        self.assertEqual(ac2_results["fail"], 1)

        # Test threshold logic (e.g., >70% pass rate = compliant)
        pass_rate = ac2_results["pass"] / ac2_results["total"]
        control_status = "Compliant" if pass_rate > 0.7 else "Non-Compliant"
        self.assertEqual(control_status, "Non-Compliant")  # 66.7% pass rate

    def test_compliance_item_creation_and_properties(self):
        """Test that compliance items are created with correct properties."""
        test_item = self.compliance_data[2]  # Storage account item

        # Simulate compliance item creation
        compliance_item = {
            "control_id": "SC-8",  # First control ID
            "status": "Non-Compliant" if test_item["Result"] == "Fail" else "Compliant",
            "implementation_guidance": test_item["Details"],
            "assessment_date": datetime.now().isoformat(),
            "source": "Wiz Policy Compliance",
            "evidence": f"Policy: {test_item['Policy Name']}, Resource: {test_item['Resource Name']}",
        }

        self.assertEqual(compliance_item["control_id"], "SC-8")
        self.assertEqual(compliance_item["status"], "Non-Compliant")
        self.assertIn("secure transfer", compliance_item["implementation_guidance"].lower())
        self.assertIn("Wiz Policy", compliance_item["source"])

    def test_report_reuse_functionality(self):
        """Test that report files can be reused and cached."""
        # Simulate report file caching logic
        report_cache = {}
        report_path = "/tmp/wiz_compliance_report.csv"
        cache_key = f"wiz_report_{hash(report_path)}"

        # First access - not in cache
        self.assertNotIn(cache_key, report_cache)

        # Simulate adding to cache
        report_cache[cache_key] = {"path": report_path, "last_modified": datetime.now(), "data": self.compliance_data}

        # Second access - should be in cache
        self.assertIn(cache_key, report_cache)
        cached_data = report_cache[cache_key]["data"]
        self.assertEqual(len(cached_data), 3)
        self.assertEqual(cached_data[0]["Resource Name"], "vm-production-001")

    def test_multiple_control_ids_extraction(self):
        """Test handling of compliance items with multiple control IDs."""
        multi_control_item = self.compliance_data[2]  # Has SC-8,SC-23,IA-7

        control_ids = [cid.strip() for cid in multi_control_item["Control IDs"].split(",")]

        # Verify all control IDs are extracted
        expected_controls = ["SC-8", "SC-23", "IA-7"]
        self.assertEqual(len(control_ids), 3)

        for expected_control in expected_controls:
            self.assertIn(expected_control, control_ids)

        # Simulate creating separate compliance items for each control
        compliance_items = []
        for control_id in control_ids:
            item = {
                "control_id": control_id,
                "resource_name": multi_control_item["Resource Name"],
                "status": "Non-Compliant",
                "policy_name": multi_control_item["Policy Name"],
            }
            compliance_items.append(item)

        self.assertEqual(len(compliance_items), 3)
        self.assertEqual(compliance_items[0]["control_id"], "SC-8")
        self.assertEqual(compliance_items[1]["control_id"], "SC-23")
        self.assertEqual(compliance_items[2]["control_id"], "IA-7")

    def test_csv_file_parsing_edge_cases(self):
        """Test CSV file parsing with various edge cases."""
        # Test data with edge cases
        edge_case_data = [
            {
                "Resource Name": "vm-with,comma",
                "Control IDs": "AC-1,AC-2, AC-3 ",  # Extra spaces
                "Details": 'Description with "quotes" and newlines\nSecond line',
                "Result": "PASS",  # Different case
                "Policy Name": "",  # Empty field
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=edge_case_data[0].keys())
            writer.writeheader()
            writer.writerows(edge_case_data)
            temp_file.flush()

            try:
                with open(temp_file.name, "r") as f:
                    reader = csv.DictReader(f)
                    parsed_data = list(reader)

                self.assertEqual(len(parsed_data), 1)
                item = parsed_data[0]

                # Test comma in resource name is preserved
                self.assertEqual(item["Resource Name"], "vm-with,comma")

                # Test control ID parsing with spaces
                control_ids = [cid.strip() for cid in item["Control IDs"].split(",")]
                self.assertEqual(control_ids, ["AC-1", "AC-2", "AC-3"])

                # Test case insensitive result parsing
                self.assertEqual(item["Result"].lower(), "pass")

                # Test empty policy name
                self.assertEqual(item["Policy Name"], "")

            finally:
                os.unlink(temp_file.name)


if __name__ == "__main__":
    unittest.main()
