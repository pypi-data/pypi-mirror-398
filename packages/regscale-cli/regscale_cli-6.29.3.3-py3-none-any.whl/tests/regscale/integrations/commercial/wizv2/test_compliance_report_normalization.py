#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for Wiz compliance report control ID normalization."""

import pytest
from unittest.mock import MagicMock

from regscale.integrations.commercial.wizv2.compliance_report import WizComplianceReportItem


class TestWizControlNormalization:
    """Test control ID normalization in WizComplianceReportItem."""

    def test_normalize_base_control(self):
        """Test normalization of base control IDs with leading zeros."""
        # Create a mock CSV row
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "Test", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)

        # Test cases
        assert item._normalize_base_control("AC-01") == "AC-1"
        assert item._normalize_base_control("AC-1") == "AC-1"
        assert item._normalize_base_control("AU-003") == "AU-3"
        assert item._normalize_base_control("SI-004") == "SI-4"
        assert item._normalize_base_control("sc-7") == "SC-7"  # lowercase
        assert item._normalize_base_control("PM-10") == "PM-10"  # no leading zero

    def test_format_control_id_with_enhancement_normalization(self):
        """Test that enhancement numbers are normalized to remove leading zeros."""
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "Test", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)

        # Enhancement with leading zeros should be normalized
        assert item._format_control_id("AC-1", "04") == "AC-1(4)"
        assert item._format_control_id("AC-2", "001") == "AC-2(1)"
        assert item._format_control_id("SI-4", "020") == "SI-4(20)"

        # Enhancement without leading zeros should remain unchanged
        assert item._format_control_id("AC-1", "4") == "AC-1(4)"
        assert item._format_control_id("AC-2", "12") == "AC-2(12)"

        # No enhancement
        assert item._format_control_id("AC-1", "") == "AC-1"
        assert item._format_control_id("AC-1", None) == "AC-1"

    def test_get_all_control_ids_single_control(self):
        """Test extraction of single control ID."""
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "AC-3 Access Enforcement", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)

        control_ids = item.get_all_control_ids()
        assert control_ids == ["AC-3"]

    def test_get_all_control_ids_with_enhancement(self):
        """Test extraction of control ID with enhancement."""
        csv_row = {
            "Compliance Check Name (Wiz Subcategory)": "AC-2(4) Account Management | Automated Audit Actions",
            "Result": "Pass",
        }
        item = WizComplianceReportItem(csv_row)

        control_ids = item.get_all_control_ids()
        assert control_ids == ["AC-2(4)"]

    def test_get_all_control_ids_multiple_controls(self):
        """Test extraction of multiple control IDs from comma-separated list."""
        csv_row = {
            "Compliance Check Name (Wiz Subcategory)": "AC-2(4) Account Management | Automated Audit Actions, "
            "AC-6(9) Least Privilege | Log Use of Privileged Functions, "
            "AU-12 Audit Record Generation",
            "Result": "Fail",
        }
        item = WizComplianceReportItem(csv_row)

        control_ids = item.get_all_control_ids()
        assert control_ids == ["AC-2(4)", "AC-6(9)", "AU-12"]

    def test_get_all_control_ids_with_leading_zeros(self):
        """Test that control IDs with leading zeros are properly normalized."""
        # Test with leading zeros in base control
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "AC-01 Access Control", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)
        assert item.get_all_control_ids() == ["AC-1"]

        # Test with leading zeros in enhancement
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "AC-01(04) Access Control Enhancement", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)
        assert item.get_all_control_ids() == ["AC-1(4)"]

        # Test multiple controls with various leading zero patterns
        csv_row = {
            "Compliance Check Name (Wiz Subcategory)": "AC-01(04) Access Control, AU-3(1) Audit Content, SI-04(020) Monitoring",
            "Result": "Pass",
        }
        item = WizComplianceReportItem(csv_row)
        assert item.get_all_control_ids() == ["AC-1(4)", "AU-3(1)", "SI-4(20)"]

    def test_get_control_id_returns_first(self):
        """Test that get_control_id returns only the first control ID."""
        csv_row = {
            "Compliance Check Name (Wiz Subcategory)": "AC-2(4) Account Management, AC-6(9) Least Privilege, AU-12 Audit",
            "Result": "Pass",
        }
        item = WizComplianceReportItem(csv_row)

        # get_control_id should return only the first
        assert item.get_control_id() == "AC-2(4)"

        # get_all_control_ids should return all
        assert item.get_all_control_ids() == ["AC-2(4)", "AC-6(9)", "AU-12"]

    def test_affected_controls_property(self):
        """Test that affected_controls property returns comma-separated list."""
        csv_row = {
            "Compliance Check Name (Wiz Subcategory)": "AC-2(4) Account Management, AC-6(9) Least Privilege",
            "Result": "Fail",
        }
        item = WizComplianceReportItem(csv_row)

        # affected_controls should return all control IDs as comma-separated string
        assert item.affected_controls == "AC-2(4),AC-6(9)"

    def test_empty_compliance_check_name(self):
        """Test handling of empty compliance check name."""
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)

        assert item.get_control_id() == ""
        assert item.get_all_control_ids() == []
        assert item.affected_controls == ""

    def test_control_id_property(self):
        """Test the control_id property returns normalized first control."""
        csv_row = {"Compliance Check Name (Wiz Subcategory)": "AC-01(04) Access Control, AU-3 Audit", "Result": "Pass"}
        item = WizComplianceReportItem(csv_row)

        # control_id property should return the first normalized control
        assert item.control_id == "AC-1(4)"
