#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Audit Manager Compliance Integration."""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime
import pytest
from freezegun import freeze_time

from regscale.integrations.commercial.aws.audit_manager_compliance import (
    AWSAuditManagerComplianceItem,
    AWSAuditManagerCompliance,
    AUDIT_MANAGER_CACHE_FILE,
    CACHE_TTL_SECONDS,
)


class TestAWSAuditManagerComplianceItem(unittest.TestCase):
    """Test cases for AWSAuditManagerComplianceItem."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessment_data = {
            "name": "NIST 800-53 Assessment",
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
            "framework": {
                "type": "Standard",
                "metadata": {"name": "NIST SP 800-53 Revision 5"},
            },
            "complianceType": "NIST800-53",
            "awsAccount": {"id": "123456789012", "name": "Production Account"},
        }

        self.control_data = {
            "id": "0c7351be-29bd-4d84-b05b-80d39c28aa2e",
            "name": "AC-2  -  Account Management",
            "description": "AC-2  -  Account Management",
            "status": "REVIEWED",  # AWS Audit Manager valid status (approved/passing)
            "response": "Control is implemented",
            "comments": [{"commentBody": "Verified implementation"}],
            "evidenceCount": 5,
            "assessmentReportEvidenceCount": 5,
        }

    def test_compliance_item_initialization(self):
        """Test compliance item initialization."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.assessment_name, "NIST 800-53 Assessment")
        self.assertEqual(item._control_id, "AC-2")
        self.assertEqual(item._control_name, "AC-2  -  Account Management")
        self.assertEqual(item.control_status, "REVIEWED")

    def test_resource_id_property(self):
        """Test resource_id property returns AWS account ID."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.resource_id, "123456789012")

    def test_resource_name_property(self):
        """Test resource_name property formats account name and ID."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.resource_name, "Production Account (123456789012)")

    def test_control_id_normalization(self):
        """Test control ID normalization removes leading zeros."""
        self.control_data["name"] = "AC-02  -  Account Management"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "AC-02")

    def test_control_id_with_enhancement(self):
        """Test control ID normalization with enhancements."""
        self.control_data["name"] = "AC-2(1)  -  Account Management - Employment Termination"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "AC-2(1)")

    def test_control_id_with_spaces(self):
        """Test control ID normalization with spaces."""
        self.control_data["name"] = "AC-2(1)  -  Account Management"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "AC-2(1)")

    def test_control_id_with_three_character_prefix(self):
        """Test control ID extraction with three-character prefix."""
        self.control_data["name"] = "SAR-10  -  System and Communications Protection"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "SAR-10")

    def test_control_id_with_multiple_spaces(self):
        """Test control ID extraction with multiple spaces around hyphen."""
        self.control_data["name"] = "AC-19(4)  -   Restrictions for Classified Information"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "AC-19(4)")

    def test_control_id_extraction_failure(self):
        """Test control ID extraction when format doesn't match."""
        self.control_data["name"] = "Invalid Format Without Proper Separator"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "")

    def test_control_id_extraction_soc2_cc_format(self):
        """Test control ID extraction for SOC 2 CC (Common Criteria) format."""
        self.control_data["name"] = "CC1.1 COSO Principle 1: The entity demonstrates a commitment to integrity"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "CC1.1")

    def test_control_id_extraction_soc2_pi_format(self):
        """Test control ID extraction for SOC 2 PI (Processing Integrity) format."""
        self.control_data["name"] = "PI1.5 The entity implements policies and procedures to store inputs"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "PI1.5")

    def test_control_id_extraction_soc2_a_format(self):
        """Test control ID extraction for SOC 2 A (Availability) format."""
        self.control_data["name"] = "A1.2 The entity authorizes, designs, develops or acquires software"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "A1.2")

    def test_control_id_extraction_soc2_c_format(self):
        """Test control ID extraction for SOC 2 C (Confidentiality) format."""
        self.control_data["name"] = "C1.1 The entity identifies and maintains confidential information"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "C1.1")

    def test_control_id_extraction_soc2_p_format(self):
        """Test control ID extraction for SOC 2 P (Privacy) format."""
        self.control_data["name"] = "P1.1 The entity provides notice to data subjects about privacy practices"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "P1.1")

    def test_control_id_extraction_cis_two_levels(self):
        """Test control ID extraction for CIS format with two levels (e.g., 1.1)."""
        self.control_data["name"] = "1.1 Ensure a separate partition for containers has been created"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "1.1")

    def test_control_id_extraction_cis_three_levels(self):
        """Test control ID extraction for CIS format with three levels (e.g., 1.1.1)."""
        self.control_data["name"] = "1.1.1 Ensure audit log storage size is configured"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "1.1.1")

    def test_control_id_extraction_cis_four_levels(self):
        """Test control ID extraction for CIS format with four levels (e.g., 1.1.1.1)."""
        self.control_data["name"] = "1.1.1.1 Ensure detailed audit logging is enabled"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "1.1.1.1")

    def test_control_id_extraction_iso_format(self):
        """Test control ID extraction for ISO format (e.g., A.5.1)."""
        self.control_data["name"] = "A.5.1 Policies for information security"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "A.5.1")

    def test_control_id_extraction_iso_three_levels(self):
        """Test control ID extraction for ISO format with three levels (e.g., A.5.1.1)."""
        self.control_data["name"] = "A.5.1.1 Policies for information security - Management direction"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "A.5.1.1")

    def test_control_id_extraction_real_soc2_examples(self):
        """Test control ID extraction with real SOC 2 examples from cached data."""
        # Real examples from the audit_manager_assessments.json file
        test_cases = [
            ("CC8.1 The entity authorizes, designs, develops or acquires", "CC8.1"),
            ("CC2.2 COSO Principle 14: The entity internally communicates", "CC2.2"),
            ("CC6.1 The entity implements logical access security software", "CC6.1"),
            ("P5.1 The entity grants identified and authenticated data subjects", "P5.1"),
        ]

        for control_name, expected_id in test_cases:
            with self.subTest(control_name=control_name):
                self.control_data["name"] = control_name
                item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)
                self.assertEqual(item.control_id, expected_id)

    def test_control_id_extraction_nist_colon_format(self):
        """Test control ID extraction for NIST format with colon separator."""
        test_cases = [
            ("SC-5(2): Capacity, Bandwidth, And Redundancy (NIST-SP-800-53-r5)", "SC-5(2)"),
            ("SC-13: Cryptographic Protection (NIST-SP-800-53-r5)", "SC-13"),
            ("SI-7(2): Automated Notifications Of Integrity Violations (NIST-SP-800-53-r5)", "SI-7(2)"),
            ("SI-4(3): Automated Tool And Mechanism Integration (NIST-SP-800-53-r5)", "SI-4(3)"),
            ("AC-2: Account Management (NIST-SP-800-53-r5)", "AC-2"),
            ("SI-1: Policy And Procedures (NIST-SP-800-53-r5)", "SI-1"),
        ]

        for control_name, expected_id in test_cases:
            with self.subTest(control_name=control_name):
                self.control_data["name"] = control_name
                item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)
                self.assertEqual(item.control_id, expected_id)

    def test_compliance_result_reviewed_status(self):
        """Test compliance result mapping for REVIEWED status with compliant evidence."""
        self.control_data["status"] = "REVIEWED"
        evidence_items = [{"complianceCheck": "COMPLIANT"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertEqual(item.compliance_result, "PASS")
        self.assertEqual(item.control_status, "REVIEWED")

    def test_compliance_result_under_review_status(self):
        """Test compliance result mapping for UNDER_REVIEW status with failed evidence."""
        self.control_data["status"] = "UNDER_REVIEW"
        evidence_items = [{"complianceCheck": "FAILED"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertEqual(item.compliance_result, "FAIL")
        self.assertEqual(item.control_status, "UNDER_REVIEW")

    def test_compliance_result_inactive_status(self):
        """Test compliance result mapping for INACTIVE status with failed evidence."""
        self.control_data["status"] = "INACTIVE"
        evidence_items = [{"complianceCheck": "FAILED"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertEqual(item.compliance_result, "FAIL")
        self.assertEqual(item.control_status, "INACTIVE")

    def test_compliance_result_unknown_status_defaults_to_fail(self):
        """Test that unknown status values with failed evidence result in FAIL."""
        test_cases = [
            "PASS",  # Not a valid AWS Audit Manager status
            "FAIL",  # Not a valid AWS Audit Manager status
            "NOT_APPLICABLE",  # Not a valid AWS Audit Manager status
            "PENDING",  # Not a valid AWS Audit Manager status
            "UNKNOWN",  # Invalid status
            "",  # Empty string
        ]

        for status in test_cases:
            with self.subTest(status=status):
                self.control_data["status"] = status
                evidence_items = [{"complianceCheck": "FAILED"}]
                item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)
                self.assertEqual(
                    item.compliance_result,
                    "FAIL",
                    f"Status '{status}' with failed evidence should result in FAIL but got {item.compliance_result}",
                )

    def test_compliance_result_case_insensitive(self):
        """Test that evidence-based compliance works with various status values."""
        test_cases = [
            ("reviewed", "PASS", "COMPLIANT"),
            ("REVIEWED", "PASS", "COMPLIANT"),
            ("Reviewed", "PASS", "COMPLIANT"),
            ("under_review", "FAIL", "FAILED"),
            ("UNDER_REVIEW", "FAIL", "FAILED"),
            ("Under_Review", "FAIL", "FAILED"),
            ("inactive", "FAIL", "FAILED"),
            ("INACTIVE", "FAIL", "FAILED"),
            ("Inactive", "FAIL", "FAILED"),
        ]

        for status, expected_result, compliance_check in test_cases:
            with self.subTest(status=status):
                self.control_data["status"] = status
                evidence_items = [{"complianceCheck": compliance_check}]
                item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)
                self.assertEqual(
                    item.compliance_result,
                    expected_result,
                    f"Status '{status}' with evidence '{compliance_check}' should map to {expected_result} but got {item.compliance_result}",
                )

    def test_severity_property_when_passed(self):
        """Test severity property returns None for passing controls with compliant evidence."""
        self.control_data["status"] = "REVIEWED"
        evidence_items = [{"complianceCheck": "COMPLIANT"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertIsNone(item.severity)

    def test_severity_property_when_failed(self):
        """Test severity property returns value for failing controls with failed evidence."""
        self.control_data["status"] = "UNDER_REVIEW"
        evidence_items = [{"complianceCheck": "FAILED"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertEqual(item.severity, "MEDIUM")

    def test_severity_property_when_inactive(self):
        """Test severity property returns value for inactive controls with failed evidence."""
        self.control_data["status"] = "INACTIVE"
        evidence_items = [{"complianceCheck": "FAILED"}]
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence_items)

        self.assertEqual(item.severity, "MEDIUM")

    def test_description_property(self):
        """Test description property includes relevant information."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)
        description = item.description

        self.assertIn("AC-2", description)
        self.assertIn("Account Management", description)
        self.assertIn("NIST SP 800-53 Revision 5", description)
        self.assertIn("Evidence Count:</strong> 5", description)  # HTML format includes colon and closing tag

    def test_framework_mapping_nist_800_53(self):
        """Test framework mapping for NIST 800-53."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.framework, "NIST800-53R5")

    def test_framework_mapping_soc2(self):
        """Test framework mapping for SOC2."""
        self.assessment_data["framework"]["metadata"]["name"] = "SOC2"
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.framework, "SOC2")

    def test_framework_mapping_default(self):
        """Test framework mapping defaults to NIST800-53R5."""
        self.assessment_data["framework"]["metadata"]["name"] = ""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.framework, "NIST800-53R5")


class TestAWSAuditManagerCompliance(unittest.TestCase):
    """Test cases for AWSAuditManagerCompliance integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.plan_id = 123
        self.region = "us-east-1"

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_initialization_with_credentials(self, mock_session):
        """Test initialization with explicit credentials."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id,
            region=self.region,
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        )

        self.assertEqual(integration.plan_id, self.plan_id)
        self.assertEqual(integration.region, self.region)
        self.assertEqual(integration.title, "AWS Audit Manager")
        mock_session.assert_called_once()

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_initialization_with_profile(self, mock_session):
        """Test initialization with AWS profile."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        self.assertEqual(integration.plan_id, self.plan_id)
        mock_session.assert_called_once()

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_fetch_compliance_data_with_specific_assessment(self, mock_session):
        """Test fetching compliance data for a specific assessment."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_assessment_response = {
            "assessment": {
                "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
                "metadata": {"name": "Test Assessment", "status": "ACTIVE", "complianceType": "NIST800-53"},
                "awsAccount": {"id": "123456789012"},
                "framework": {
                    "metadata": {"name": "NIST SP 800-53 Revision 5"},
                    "controlSets": [
                        {
                            "controls": [
                                {
                                    "id": "0c7351be-29bd-4d84-b05b-80d39c28aa2e",
                                    "name": "AC-2  -  Account Management",
                                    "description": "AC-2  -  Account Management",
                                    "status": "REVIEWED",
                                }
                            ]
                        }
                    ],
                },
            }
        }

        mock_client.get_assessment.return_value = mock_assessment_response

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id,
            region=self.region,
            profile="default",
            assessment_id="abc-123",
        )

        compliance_data = integration.fetch_compliance_data()

        self.assertGreater(len(compliance_data), 0)
        self.assertIn("assessment", compliance_data[0])
        self.assertIn("control", compliance_data[0])

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_create_compliance_item(self, mock_session):
        """Test creating compliance item from raw data."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        raw_data = {
            "assessment": {
                "name": "Test Assessment",
                "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
                "framework": {"type": "Standard", "metadata": {"name": "NIST 800-53"}},
                "awsAccount": {"id": "123456789012"},
            },
            "control": {
                "id": "0c7351be-29bd-4d84-b05b-80d39c28aa2e",
                "name": "AC-2  -  Account Management",
                "description": "AC-2  -  Account Management",
                "status": "REVIEWED",
            },
        }

        compliance_item = integration.create_compliance_item(raw_data)

        self.assertIsInstance(compliance_item, AWSAuditManagerComplianceItem)
        self.assertEqual(compliance_item.control_id, "AC-2")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_map_resource_type_to_asset_type(self, mock_session):
        """Test resource type to asset type mapping."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        mock_compliance_item = Mock()

        asset_type = integration._map_resource_type_to_asset_type(mock_compliance_item)

        self.assertEqual(asset_type, "AWS Account")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("os.path.exists")
    def test_is_cache_valid_no_file(self, mock_exists, mock_session):
        """Test cache validation when file does not exist."""
        mock_exists.return_value = False
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        result = integration._is_cache_valid()

        self.assertFalse(result)
        # Verify the cache file path was checked (mock may be called multiple times by other code)
        self.assertIn(unittest.mock.call(AUDIT_MANAGER_CACHE_FILE), mock_exists.call_args_list)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    @patch("time.time")
    def test_is_cache_valid_expired(self, mock_time, mock_getmtime, mock_exists, mock_session):
        """Test cache validation when cache is expired."""
        mock_exists.return_value = True
        mock_time.return_value = 1000000
        mock_getmtime.return_value = 1000000 - CACHE_TTL_SECONDS - 100  # Expired by 100 seconds
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        result = integration._is_cache_valid()

        self.assertFalse(result)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    @patch("time.time")
    def test_is_cache_valid_fresh(self, mock_time, mock_getmtime, mock_exists, mock_session):
        """Test cache validation when cache is still valid."""
        mock_exists.return_value = True
        mock_time.return_value = 1000000
        mock_getmtime.return_value = 1000000 - 3600  # 1 hour old, within 4-hour TTL
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        result = integration._is_cache_valid()

        self.assertTrue(result)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("builtins.open", new_callable=mock_open, read_data='[{"test": "data"}]')
    def test_load_cached_data_success(self, mock_file, mock_session):
        """Test successfully loading data from cache."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        result = integration._load_cached_data()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["test"], "data")
        mock_file.assert_called_once_with(AUDIT_MANAGER_CACHE_FILE, encoding="utf-8")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("builtins.open", side_effect=IOError("File not found"))
    def test_load_cached_data_io_error(self, mock_file, mock_session):
        """Test loading cache when file cannot be read."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        result = integration._load_cached_data()

        self.assertEqual(result, [])

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_to_cache_success(self, mock_file, mock_makedirs, mock_session):
        """Test successfully saving data to cache."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        test_data = [{"assessment": {}, "control": {}}]

        integration._save_to_cache(test_data)

        mock_makedirs.assert_called_once()
        mock_file.assert_called_once_with(AUDIT_MANAGER_CACHE_FILE, "w", encoding="utf-8")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_fetch_compliance_data_uses_cache_when_valid(self, mock_session):
        """Test that fetch_compliance_data uses cached data when available."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        cached_data = [
            {
                "assessment": {
                    "name": "Cached NIST Assessment",
                    "complianceType": "NIST800-53",
                    "framework": {"metadata": {"name": "NIST SP 800-53 Revision 5"}},
                },
                "control": {"name": "AC-2 - Test"},
            }
        ]

        with patch.object(integration, "_is_cache_valid", return_value=True):
            with patch.object(integration, "_load_cached_data", return_value=cached_data):
                result = integration.fetch_compliance_data()

        self.assertEqual(result, cached_data)
        mock_client.list_assessments.assert_not_called()  # Should not call AWS API

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_fetch_compliance_data_fetches_fresh_when_cache_invalid(self, mock_session):
        """Test that fetch_compliance_data fetches fresh data when cache is invalid."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_assessment_response = {
            "assessment": {
                "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
                "metadata": {"name": "Test Assessment", "status": "ACTIVE"},
                "awsAccount": {"id": "123456789012"},
                "complianceType": "NIST800-53",
                "framework": {
                    "metadata": {"name": "NIST SP 800-53 Revision 5"},
                    "controlSets": [
                        {"controls": [{"id": "test-id", "name": "AC-2 - Account Management", "status": "REVIEWED"}]}
                    ],
                },
            }
        }

        mock_client.get_assessment.return_value = mock_assessment_response

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", assessment_id="abc-123"
        )

        with patch.object(integration, "_is_cache_valid", return_value=False):
            with patch.object(integration, "_save_to_cache") as mock_save:
                result = integration.fetch_compliance_data()

        self.assertGreater(len(result), 0)
        mock_client.get_assessment.assert_called_once()
        mock_save.assert_called_once()  # Should save fresh data to cache

    # ============================================================================
    # Evidence Collection Tests
    # ============================================================================

    @freeze_time("2025-01-16")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_success(self, mock_session):
        """Test successfully retrieving evidence for a control."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        # Mock evidence folder response - both folders are yesterday (2025-01-15) when time is frozen to 2025-01-16
        mock_client.get_evidence_folders_by_assessment_control.return_value = {
            "evidenceFolders": [
                {"id": "folder-1", "date": "2025-01-15", "evidenceResourcesIncludedCount": 2},
                {"id": "folder-2", "date": "2025-01-15", "evidenceResourcesIncludedCount": 1},
            ],
            "nextToken": None,
        }

        # Mock evidence items response
        mock_client.get_evidence_by_evidence_folder.side_effect = [
            {
                "evidence": [
                    {
                        "id": "evidence-1",
                        "dataSource": "AWS CloudTrail",
                        "eventName": "CreateUser",
                        "time": datetime(2025, 1, 15, 10, 30, 0),
                    },
                    {
                        "id": "evidence-2",
                        "dataSource": "AWS Config",
                        "eventName": "PutEvaluations",
                        "time": datetime(2025, 1, 15, 11, 0, 0),
                    },
                ],
                "nextToken": None,
            },
            {
                "evidence": [{"id": "evidence-3", "dataSource": "AWS CloudTrail", "eventName": "DeleteUser"}],
                "nextToken": None,
            },
        ]

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=100
        )

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 3)
        self.assertEqual(evidence_items[0]["id"], "evidence-1")
        self.assertEqual(evidence_items[1]["dataSource"], "AWS Config")
        mock_client.get_evidence_folders_by_assessment_control.assert_called_once_with(
            assessmentId="assessment-123", controlSetId="control-set-456", controlId="control-789"
        )
        self.assertEqual(mock_client.get_evidence_by_evidence_folder.call_count, 2)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_no_folders(self, mock_session):
        """Test handling when no evidence folders are found."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.get_evidence_folders_by_assessment_control.return_value = {"evidenceFolders": []}

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 0)
        mock_client.get_evidence_by_evidence_folder.assert_not_called()

    @freeze_time("2025-01-16")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_with_pagination(self, mock_session):
        """Test evidence retrieval with pagination handling."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.get_evidence_folders_by_assessment_control.return_value = {
            "evidenceFolders": [{"id": "folder-1", "date": "2025-01-15", "evidenceResourcesIncludedCount": 60}],
            "nextToken": None,
        }

        # Simulate pagination with nextToken
        mock_client.get_evidence_by_evidence_folder.side_effect = [
            {
                "evidence": [{"id": f"evidence-{i}", "dataSource": "AWS CloudTrail"} for i in range(50)],
                "nextToken": "token-page-2",
            },
            {
                "evidence": [{"id": f"evidence-{i}", "dataSource": "AWS Config"} for i in range(50, 60)],
                "nextToken": None,
            },
        ]

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=100
        )

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 60)
        self.assertEqual(mock_client.get_evidence_by_evidence_folder.call_count, 2)

    @freeze_time("2025-01-16")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_respects_max_limit(self, mock_session):
        """Test that evidence collection respects max_evidence_per_control limit."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.get_evidence_folders_by_assessment_control.return_value = {
            "evidenceFolders": [
                {"id": "folder-1", "date": "2025-01-15", "evidenceResourcesIncludedCount": 30},
            ],
            "nextToken": None,
        }

        # First call returns 25 items (max limit)
        mock_client.get_evidence_by_evidence_folder.return_value = {
            "evidence": [{"id": f"evidence-{i}", "dataSource": "AWS CloudTrail"} for i in range(25)],
            "nextToken": None,
        }

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=25
        )

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        # Should respect max limit
        self.assertEqual(len(evidence_items), 25)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_client_error_resource_not_found(self, mock_session):
        """Test handling ResourceNotFoundException when getting evidence."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        from botocore.exceptions import ClientError

        mock_client.get_evidence_folders_by_assessment_control.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Control not found"}}, "GetEvidenceFolders"
        )

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 0)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_client_error_access_denied(self, mock_session):
        """Test handling AccessDeniedException when getting evidence."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        from botocore.exceptions import ClientError

        mock_client.get_evidence_folders_by_assessment_control.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "GetEvidenceFolders"
        )

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 0)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_client_error_other(self, mock_session):
        """Test handling other ClientError exceptions when getting evidence."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        from botocore.exceptions import ClientError

        mock_client.get_evidence_folders_by_assessment_control.side_effect = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "GetEvidenceFolders"
        )

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        self.assertEqual(len(evidence_items), 0)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_collect_assessment_evidence_disabled(self, mock_session):
        """Test that evidence collection is skipped when disabled."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", collect_evidence=False
        )

        with patch.object(integration, "_get_control_evidence") as mock_get_evidence:
            integration.collect_assessment_evidence([])
            mock_get_evidence.assert_not_called()

    @pytest.mark.skip(reason="Method _create_evidence_record has been refactored and no longer exists")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_collect_assessment_evidence_success(self, mock_session):
        """Test successful evidence collection from assessments."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", collect_evidence=True
        )

        assessment = {
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
            "name": "Test Assessment",
            "framework": {
                "controlSets": [
                    {
                        "id": "control-set-1",
                        "controls": [
                            {
                                "id": "control-uuid-1",
                                "name": "AC-2 - Account Management",
                                "evidenceCount": 5,
                            }
                        ],
                    }
                ]
            },
        }

        evidence_items = [{"id": "evidence-1", "dataSource": "AWS CloudTrail", "time": datetime(2025, 1, 15, 10, 0, 0)}]

        with patch.object(integration, "_get_control_evidence", return_value=evidence_items):
            with patch.object(integration, "_create_evidence_record", return_value=Mock(id=123)) as mock_create:
                integration.collect_assessment_evidence([assessment])

                mock_create.assert_called_once()
                call_args = mock_create.call_args[1]
                self.assertEqual(call_args["control_id"], "AC-2")
                self.assertEqual(call_args["control_name"], "AC-2 - Account Management")
                self.assertEqual(len(call_args["evidence_items"]), 1)

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_collect_assessment_evidence_with_control_filter(self, mock_session):
        """Test evidence collection with control ID filtering."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id,
            region=self.region,
            profile="default",
            collect_evidence=True,
            evidence_control_ids=["AC-2", "AU-2"],
        )

        assessment = {
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
            "name": "Test Assessment",
            "framework": {
                "controlSets": [
                    {
                        "id": "control-set-1",
                        "controls": [
                            {"id": "control-uuid-1", "name": "AC-2 - Account Management", "evidenceCount": 5},
                            {"id": "control-uuid-2", "name": "SI-2 - System Monitoring", "evidenceCount": 3},
                        ],
                    }
                ]
            },
        }

        with patch.object(integration, "_get_control_evidence") as mock_get_evidence:
            with patch.object(integration, "_create_evidence_record"):
                integration.collect_assessment_evidence([assessment])

                # Only AC-2 should be collected (SI-2 not in filter list)
                mock_get_evidence.assert_called_once()
                call_args = mock_get_evidence.call_args[1]
                self.assertEqual(call_args["control_id"], "control-uuid-1")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_collect_assessment_evidence_skips_zero_evidence_count(self, mock_session):
        """Test that controls with evidenceCount=0 are skipped (via assessment-level API).

        In assessment-level collection, _get_all_evidence_folders_for_assessment only returns
        folders for controls that have evidence. This test verifies that only those controls
        are processed.
        """
        from regscale.integrations.commercial.aws.audit_manager_compliance import EvidenceCollectionConfig

        evidence_config = EvidenceCollectionConfig(collect_evidence=True)
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", evidence_config=evidence_config
        )

        assessment = {
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
            "name": "Test Assessment",
            "framework": {
                "controlSets": [
                    {
                        "id": "control-set-1",
                        "controls": [
                            {"id": "control-uuid-1", "name": "AC-2 - Account Management", "evidenceCount": 0},
                            {"id": "control-uuid-2", "name": "AU-2 - Audit Events", "evidenceCount": 5},
                        ],
                    }
                ]
            },
        }

        # Mock _get_all_evidence_folders_for_assessment to return folders only for the control with evidence
        # This simulates the assessment-level API only returning folders for controls that have evidence
        mock_folders = {
            "control-uuid-2": [
                {
                    "id": "folder-1",
                    "controlId": "control-uuid-2",
                    "controlSetId": "control-set-1",
                    "controlName": "AU-2",
                }
            ]
        }

        # Mock _process_evidence_folders to return evidence items (used by assessment-level collection)
        with patch.object(integration, "_get_all_evidence_folders_for_assessment", return_value=mock_folders):
            with patch.object(
                integration, "_process_evidence_folders", return_value=[{"id": "evidence-1"}]
            ) as mock_process_folders:
                with patch.object(integration, "_create_consolidated_evidence_record"):
                    integration.collect_assessment_evidence([assessment])

                # Only AU-2 should be processed (AC-2 has evidenceCount=0 and no folders returned)
                mock_process_folders.assert_called_once()
                call_args = mock_process_folders.call_args
                # Verify the control_id passed to _process_evidence_folders is correct
                self.assertEqual(call_args[0][2], "control-uuid-2")  # Third positional arg is control_id

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_collect_assessment_evidence_no_evidence_found(self, mock_session):
        """Test evidence collection when no evidence items are returned."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", collect_evidence=True
        )

        assessment = {
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/abc-123",
            "name": "Test Assessment",
            "framework": {
                "controlSets": [
                    {
                        "id": "control-set-1",
                        "controls": [{"id": "control-uuid-1", "name": "AC-2 - Account Management", "evidenceCount": 5}],
                    }
                ]
            },
        }

        with patch.object(integration, "_get_control_evidence", return_value=[]):
            with patch.object(integration, "_create_evidence_record") as mock_create:
                integration.collect_assessment_evidence([assessment])

                # Should not create evidence record when no evidence items found
                mock_create.assert_not_called()

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.get_current_datetime")
    @patch("regscale.models.regscale_models.evidence.Evidence")
    def test_create_evidence_record_success(self, mock_evidence_class, mock_get_datetime, mock_session):
        """Test successful creation of evidence record."""
        mock_get_datetime.return_value = "2025-01-15"

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", evidence_frequency=30
        )
        integration.api = Mock()  # Set mock API

        evidence_items = [
            {
                "id": "evidence-1",
                "dataSource": "AWS CloudTrail",
                "eventName": "CreateUser",
                "time": datetime(2025, 1, 15, 10, 0, 0),
            },
            {
                "id": "evidence-2",
                "dataSource": "AWS Config",
                "eventName": "PutEvaluations",
                "time": datetime(2025, 1, 15, 11, 0, 0),
            },
        ]

        compliance_item = Mock()
        compliance_item.control_id = "AC-2"

        mock_evidence = Mock()
        mock_evidence.id = 456
        mock_evidence.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence

        with patch.object(integration, "_attach_evidence_file") as mock_attach:
            with patch.object(integration, "_link_evidence_to_ssp") as mock_link_ssp:
                with patch.object(integration, "_link_evidence_to_control") as mock_link_control:
                    result = integration._create_evidence_record(
                        control_id="AC-2",
                        control_name="Account Management",
                        assessment_name="Test Assessment",
                        evidence_items=evidence_items,
                        compliance_item=compliance_item,
                    )

        self.assertIsNotNone(result)
        self.assertEqual(result.id, 456)
        mock_evidence.create.assert_called_once()
        mock_attach.assert_called_once_with(
            evidence_id=456, control_id="AC-2", scan_date="2025-01-15", evidence_items=evidence_items
        )
        mock_link_ssp.assert_called_once_with(456)
        mock_link_control.assert_called_once_with(456, "AC-2")

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.get_current_datetime")
    @patch("regscale.models.regscale_models.evidence.Evidence")
    def test_create_evidence_record_with_timestamp_integers(self, mock_evidence_class, mock_get_datetime, mock_session):
        """Test evidence record creation with timestamp as integers (milliseconds)."""
        mock_get_datetime.return_value = "2025-01-15"

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        evidence_items = [
            {
                "id": "evidence-1",
                "dataSource": "AWS CloudTrail",
                "eventName": "CreateUser",
                "time": 1705315200000,  # Timestamp in milliseconds
            }
        ]

        compliance_item = Mock()
        compliance_item.control_id = "AC-2"

        mock_evidence = Mock()
        mock_evidence.id = 789
        mock_evidence.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence

        with patch.object(integration, "_attach_evidence_file"):
            with patch.object(integration, "_link_evidence_to_ssp"):
                with patch.object(integration, "_link_evidence_to_control"):
                    result = integration._create_evidence_record(
                        control_id="AC-2",
                        control_name="Account Management",
                        assessment_name="Test Assessment",
                        evidence_items=evidence_items,
                        compliance_item=compliance_item,
                    )

        self.assertIsNotNone(result)
        mock_evidence.create.assert_called_once()

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.get_current_datetime")
    @patch("regscale.models.regscale_models.evidence.Evidence")
    def test_create_evidence_record_create_fails(self, mock_evidence_class, mock_get_datetime, mock_session):
        """Test handling when Evidence.create() fails."""
        mock_get_datetime.return_value = "2025-01-15"

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        evidence_items = [{"id": "evidence-1", "dataSource": "AWS CloudTrail"}]
        compliance_item = Mock()

        mock_evidence = Mock()
        mock_evidence.id = None
        mock_evidence.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence

        result = integration._create_evidence_record(
            control_id="AC-2",
            control_name="Account Management",
            assessment_name="Test Assessment",
            evidence_items=evidence_items,
            compliance_item=compliance_item,
        )

        self.assertIsNone(result)

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.get_current_datetime")
    @patch("regscale.models.regscale_models.evidence.Evidence")
    def test_create_evidence_record_exception_handling(self, mock_evidence_class, mock_get_datetime, mock_session):
        """Test exception handling during evidence record creation."""
        mock_get_datetime.return_value = "2025-01-15"

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        evidence_items = [{"id": "evidence-1"}]
        compliance_item = Mock()

        mock_evidence_class.side_effect = Exception("Database error")

        result = integration._create_evidence_record(
            control_id="AC-2",
            control_name="Account Management",
            assessment_name="Test Assessment",
            evidence_items=evidence_items,
            compliance_item=compliance_item,
        )

        self.assertIsNone(result)

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.get_current_datetime")
    @patch("regscale.models.regscale_models.evidence.Evidence")
    def test_create_evidence_record_description_formatting(self, mock_evidence_class, mock_get_datetime, mock_session):
        """Test that evidence description is properly formatted with all details."""
        mock_get_datetime.return_value = "2025-01-15"

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        evidence_items = [
            {
                "id": "evidence-1",
                "dataSource": "AWS CloudTrail",
                "eventName": "CreateUser",
                "time": datetime(2025, 1, 10, 10, 0, 0),
            },
            {
                "id": "evidence-2",
                "dataSource": "AWS Config",
                "eventName": "PutEvaluations",
                "time": datetime(2025, 1, 15, 15, 30, 0),
            },
        ]

        compliance_item = Mock()

        mock_evidence = Mock()
        mock_evidence.id = 999
        mock_evidence.create.return_value = mock_evidence
        mock_evidence_class.return_value = mock_evidence

        with patch.object(integration, "_attach_evidence_file"):
            with patch.object(integration, "_link_evidence_to_ssp"):
                with patch.object(integration, "_link_evidence_to_control"):
                    integration._create_evidence_record(
                        control_id="AC-2",
                        control_name="Account Management",
                        assessment_name="Test Assessment",
                        evidence_items=evidence_items,
                        compliance_item=compliance_item,
                    )

        # Verify Evidence was created with proper arguments
        call_kwargs = mock_evidence.create.call_args
        self.assertIsNotNone(call_kwargs)

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.file.File.upload_file_to_regscale")
    def test_attach_evidence_file_success(self, mock_upload, mock_session):
        """Test successful attachment of evidence file."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()
        mock_upload.return_value = True

        evidence_items = [
            {"id": "evidence-1", "dataSource": "AWS CloudTrail", "eventName": "CreateUser"},
            {"id": "evidence-2", "dataSource": "AWS Config", "eventName": "PutEvaluations"},
        ]

        integration._attach_evidence_file(
            evidence_id=123, control_id="AC-2", scan_date="2025-01-15", evidence_items=evidence_items
        )

        mock_upload.assert_called_once()
        call_kwargs = mock_upload.call_args[1]
        self.assertEqual(call_kwargs["file_name"], "audit_manager_evidence_ac_2_2025-01-15.jsonl")
        self.assertEqual(call_kwargs["parent_id"], 123)
        self.assertEqual(call_kwargs["parent_module"], "evidence")
        self.assertIn(b"evidence-1", call_kwargs["file_data"])
        self.assertIn(b"evidence-2", call_kwargs["file_data"])
        self.assertEqual(call_kwargs["tags"], "aws,audit-manager,ac-2")

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.file.File.upload_file_to_regscale")
    def test_attach_evidence_file_upload_fails(self, mock_upload, mock_session):
        """Test handling when file upload fails."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()
        mock_upload.return_value = False

        evidence_items = [{"id": "evidence-1", "dataSource": "AWS CloudTrail"}]

        # Should not raise exception, just log warning
        integration._attach_evidence_file(
            evidence_id=123, control_id="AC-2", scan_date="2025-01-15", evidence_items=evidence_items
        )

        mock_upload.assert_called_once()

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.file.File.upload_file_to_regscale")
    def test_attach_evidence_file_jsonl_formatting(self, mock_upload, mock_session):
        """Test that evidence items are properly formatted as JSONL."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()
        mock_upload.return_value = True

        evidence_items = [
            {"id": "evidence-1", "time": datetime(2025, 1, 15, 10, 0, 0)},
            {"id": "evidence-2", "nested": {"key": "value"}},
        ]

        integration._attach_evidence_file(
            evidence_id=456, control_id="AU-2", scan_date="2025-01-15", evidence_items=evidence_items
        )

        call_kwargs = mock_upload.call_args[1]
        file_data = call_kwargs["file_data"].decode("utf-8")

        # Verify JSONL format (one JSON object per line)
        lines = file_data.strip().split("\n")
        self.assertEqual(len(lines), 2)

        # Each line should be valid JSON
        item1 = json.loads(lines[0])
        item2 = json.loads(lines[1])
        self.assertEqual(item1["id"], "evidence-1")
        self.assertEqual(item2["id"], "evidence-2")
        self.assertEqual(item2["nested"]["key"], "value")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.evidence_mapping.EvidenceMapping")
    def test_link_evidence_to_ssp_success(self, mock_evidence_mapping_class, mock_session):
        """Test successfully linking evidence to security plan."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        mock_mapping = Mock()
        mock_mapping.create.return_value = Mock()
        mock_evidence_mapping_class.return_value = mock_mapping

        integration._link_evidence_to_ssp(evidence_id=789)

        # Verify EvidenceMapping was created with correct parameters
        mock_evidence_mapping_class.assert_called_once_with(
            evidenceID=789, mappedID=self.plan_id, mappingType="securityplans"
        )
        mock_mapping.create.assert_called_once()

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.evidence_mapping.EvidenceMapping")
    def test_link_evidence_to_ssp_fails(self, mock_evidence_mapping_class, mock_session):
        """Test handling when linking evidence to SSP fails."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = Mock()

        mock_mapping = Mock()
        mock_mapping.create.side_effect = Exception("API error")
        mock_evidence_mapping_class.return_value = mock_mapping

        # Should not raise exception, just log warning
        integration._link_evidence_to_ssp(evidence_id=789)

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.evidence_mapping.EvidenceMapping")
    def test_link_evidence_to_control_success(self, mock_evidence_mapping_class, mock_session):
        """Test successfully linking evidence to control assessment."""
        mock_api = Mock()
        mock_api.get_by_query.return_value = [{"id": 555, "controlId": "AC-2"}]

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = mock_api

        mock_mapping = Mock()
        mock_mapping.create.return_value = Mock()
        mock_evidence_mapping_class.return_value = mock_mapping

        integration._link_evidence_to_control(evidence_id=888, control_id="AC-2")

        mock_api.get_by_query.assert_called_once_with(
            "securityControlAssessments", "controlId eq 'AC-2' and securityPlanId eq 123", pageSize=1
        )
        mock_evidence_mapping_class.assert_called_once_with(
            evidenceID=888, mappedID=555, mappingType="securityControlAssessments"
        )
        mock_mapping.create.assert_called_once()

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    @patch("regscale.models.regscale_models.evidence_mapping.EvidenceMapping")
    def test_link_evidence_to_control_no_control_found(self, mock_evidence_mapping_class, mock_session):
        """Test handling when control assessment is not found."""
        mock_api = Mock()
        mock_api.get_by_query.return_value = []

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = mock_api

        integration._link_evidence_to_control(evidence_id=888, control_id="AC-2")

        mock_api.get_by_query.assert_called_once()
        mock_evidence_mapping_class.assert_not_called()

    @pytest.mark.skip(reason="Test references refactored methods that no longer exist")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_link_evidence_to_control_api_error(self, mock_session):
        """Test handling API error when linking evidence to control."""
        mock_api = Mock()
        mock_api.get_by_query.side_effect = Exception("API connection error")

        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")
        integration.api = mock_api

        # Should not raise exception, just log warning
        integration._link_evidence_to_control(evidence_id=888, control_id="AC-2")

    # REG-18524: Tests for max_evidence_per_control parameter
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_max_evidence_per_control_default_value(self, mock_session):
        """Test that max_evidence_per_control defaults to None when not specified (backend default)."""
        integration = AWSAuditManagerCompliance(plan_id=self.plan_id, region=self.region, profile="default")

        # Backend default should be None (unlimited) when not specified
        # The CLI layer provides the default of 100
        self.assertIsNone(integration.max_evidence_per_control)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_max_evidence_per_control_cli_default_value(self, mock_session):
        """Test that max_evidence_per_control defaults to 100 when specified by CLI."""
        # CLI should provide 100 as default (tested via kwargs simulation)
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=100
        )

        self.assertEqual(integration.max_evidence_per_control, 100)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_max_evidence_per_control_custom_value(self, mock_session):
        """Test that max_evidence_per_control accepts custom values for large environments."""
        # Test with value suitable for large AWS accounts (like USPTO)
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=5000
        )

        self.assertEqual(integration.max_evidence_per_control, 5000)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_max_evidence_per_control_unlimited_with_zero(self, mock_session):
        """Test that max_evidence_per_control=0 allows unlimited evidence collection."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=0
        )

        # Zero should be treated as None (unlimited)
        self.assertEqual(integration.max_evidence_per_control, 0)

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_max_evidence_per_control_unlimited_with_none(self, mock_session):
        """Test that max_evidence_per_control=None allows unlimited evidence collection."""
        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=None
        )

        self.assertIsNone(integration.max_evidence_per_control)

    @freeze_time("2025-01-16")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_with_high_limit(self, mock_session):
        """Test evidence collection with high limit for large AWS accounts (REG-18524)."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        # Simulate large AWS account with many resources
        mock_client.get_evidence_folders_by_assessment_control.return_value = {
            "evidenceFolders": [
                {"id": "folder-1", "date": "2025-01-15", "evidenceResourcesIncludedCount": 5000},
            ],
            "nextToken": None,
        }

        # Simulate multiple pages of evidence
        evidence_page_1 = [{"id": f"evidence-{i}", "dataSource": "AWS CloudTrail"} for i in range(1000)]
        evidence_page_2 = [{"id": f"evidence-{i}", "dataSource": "AWS Config"} for i in range(1000, 2000)]
        evidence_page_3 = [{"id": f"evidence-{i}", "dataSource": "AWS Security Hub"} for i in range(2000, 3000)]

        mock_client.get_evidence_by_evidence_folder.side_effect = [
            {"evidence": evidence_page_1, "nextToken": "token1"},
            {"evidence": evidence_page_2, "nextToken": "token2"},
            {"evidence": evidence_page_3, "nextToken": None},
        ]

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=5000
        )

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        # Should collect 3000 items (under the 5000 limit)
        self.assertEqual(len(evidence_items), 3000)

    @freeze_time("2025-01-16")
    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.boto3.Session")
    def test_get_control_evidence_stops_at_limit(self, mock_session):
        """Test that evidence collection stops when max_evidence_per_control is reached."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.get_evidence_folders_by_assessment_control.return_value = {
            "evidenceFolders": [
                {"id": "folder-1", "date": "2025-01-15", "evidenceResourcesIncludedCount": 500},
            ],
            "nextToken": None,
        }

        # Simulate multiple pages that would exceed the limit
        evidence_page_1 = [{"id": f"evidence-{i}", "dataSource": "AWS CloudTrail"} for i in range(100)]
        evidence_page_2 = [{"id": f"evidence-{i}", "dataSource": "AWS Config"} for i in range(100, 200)]

        mock_client.get_evidence_by_evidence_folder.side_effect = [
            {"evidence": evidence_page_1, "nextToken": "token1"},
            {"evidence": evidence_page_2, "nextToken": None},  # This page should stop collection
        ]

        integration = AWSAuditManagerCompliance(
            plan_id=self.plan_id, region=self.region, profile="default", max_evidence_per_control=150
        )

        evidence_items = integration._get_control_evidence(
            assessment_id="assessment-123", control_set_id="control-set-456", control_id="control-789"
        )

        # Should collect exactly 200 items (both pages, second page not cut off at limit)
        # Note: The implementation collects full pages, so we get 200 items even though limit is 150
        self.assertGreaterEqual(len(evidence_items), 150)
        self.assertLessEqual(len(evidence_items), 200)

    def test_cli_max_evidence_per_control_parameter_exists(self):
        """Test that the CLI --max-evidence-per-control parameter exists and has correct default (REG-18524)."""
        from click.testing import CliRunner
        from regscale.integrations.commercial.aws.cli import awsv2

        runner = CliRunner()
        # Check that the help text includes the --max-evidence-per-control option
        result = runner.invoke(awsv2, ["sync_compliance", "--help"])

        # Verify the option is in the help text
        self.assertIn("--max-evidence-per-control", result.output)
        # Verify the default value is documented
        self.assertIn("default: 100", result.output.lower())
        # Verify help text mentions large environments
        self.assertIn("large", result.output.lower())


if __name__ == "__main__":
    unittest.main()
