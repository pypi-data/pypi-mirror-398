#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Audit Manager Evidence-Based Compliance Aggregation."""

import unittest

from regscale.integrations.commercial.aws.audit_manager_compliance import AWSAuditManagerComplianceItem


class TestEvidenceAggregation(unittest.TestCase):
    """Test cases for evidence-based compliance aggregation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessment_data = {
            "name": "Test Assessment",
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/test",
            "framework": {"type": "Standard", "metadata": {"name": "NIST SP 800-53 Revision 5"}},
            "complianceType": "NIST800-53",
            "awsAccount": {"id": "123456789012", "name": "Test Account"},
        }

        self.control_data = {
            "id": "test-control-id",
            "name": "CP-10(2) - Transaction Recovery",
            "description": "Control description",
            "status": "REVIEWED",  # Workflow status - not used for compliance
            "evidenceCount": 8,
        }

    def test_all_compliant_evidence_passes(self):
        """Test that all COMPLIANT evidence results in PASS."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "PASS")

    def test_any_failed_evidence_fails_control(self):
        """Test that ANY FAILED evidence causes control to FAIL."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},  # ONE failure
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "FAIL")

    def test_multiple_failed_evidence_fails_control(self):
        """Test that multiple FAILED evidence items causes control to FAIL."""
        evidence = [
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "FAIL")

    def test_all_failed_evidence_fails_control(self):
        """Test that all FAILED evidence results in FAIL."""
        evidence = [
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "FAIL")

    def test_no_evidence_returns_none(self):
        """Test that no evidence results in None (control should not be updated)."""
        evidence = []

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.compliance_result)

    def test_none_evidence_returns_none(self):
        """Test that None evidence results in None (control should not be updated)."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, None)
        self.assertIsNone(item.compliance_result)

    def test_inconclusive_evidence_only_returns_none(self):
        """Test that only inconclusive evidence (null checks) results in None (control should not be updated)."""
        evidence = [
            {"dataSource": "AWS CloudTrail"},  # No complianceCheck field
            {"complianceCheck": None, "dataSource": "Manual"},
            {"dataSource": "API Call"},  # No complianceCheck field
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.compliance_result)

    def test_compliant_with_inconclusive_passes(self):
        """Test that COMPLIANT evidence with some inconclusive results in PASS."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"dataSource": "AWS CloudTrail"},  # No complianceCheck
            {"complianceCheck": None, "dataSource": "Manual"},  # Null check
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "PASS")

    def test_failed_with_inconclusive_fails(self):
        """Test that FAILED evidence with inconclusive results in FAIL."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"dataSource": "AWS CloudTrail"},  # No complianceCheck
            {"complianceCheck": None, "dataSource": "Manual"},  # Null check
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "FAIL")

    def test_real_world_mixed_evidence_cp10(self):
        """Test real-world scenario: CP-10(2) with 4 COMPLIANT and 4 FAILED."""
        # Based on actual audit_manager_evidence_cp_10(2)_2025-10-17.jsonl data
        evidence = [
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        # Should FAIL because there are FAILED evidence items
        self.assertEqual(item.compliance_result, "FAIL")

    def test_workflow_status_not_used_for_compliance(self):
        """Test that control workflow status (REVIEWED) does NOT determine compliance."""
        # Control marked as REVIEWED (workflow status) but has failing evidence
        self.control_data["status"] = "REVIEWED"
        evidence = [
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        # Should FAIL based on evidence, not REVIEWED status
        self.assertEqual(item.compliance_result, "FAIL")
        # Verify workflow status is still REVIEWED
        self.assertEqual(item.control_status, "REVIEWED")

    def test_under_review_with_passing_evidence(self):
        """Test that UNDER_REVIEW workflow status with passing evidence results in PASS."""
        self.control_data["status"] = "UNDER_REVIEW"
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Security Hub"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        # Should PASS based on evidence, regardless of UNDER_REVIEW status
        self.assertEqual(item.compliance_result, "PASS")
        # Verify workflow status is still UNDER_REVIEW
        self.assertEqual(item.control_status, "UNDER_REVIEW")

    def test_compliance_result_caching(self):
        """Test that compliance result is cached after first calculation."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)

        # First call
        result1 = item.compliance_result
        self.assertEqual(result1, "PASS")

        # Verify cached value is used
        self.assertEqual(item._aggregated_compliance_result, "PASS")

        # Second call should return same cached result
        result2 = item.compliance_result
        self.assertEqual(result2, "PASS")

    def test_severity_when_passed(self):
        """Test that severity is None when control passes."""
        evidence = [
            {"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.severity)

    def test_severity_when_failed(self):
        """Test that severity is set when control fails."""
        evidence = [
            {"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.severity, "MEDIUM")


class TestEvidenceAggregationEdgeCases(unittest.TestCase):
    """Test edge cases for evidence aggregation."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessment_data = {
            "name": "Edge Case Assessment",
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/test",
            "framework": {"type": "Standard", "metadata": {"name": "NIST SP 800-53 Revision 5"}},
            "complianceType": "NIST800-53",
            "awsAccount": {"id": "123456789012"},
        }

        self.control_data = {
            "id": "test-control-id",
            "name": "AC-2 - Account Management",
            "description": "Control description",
            "status": "REVIEWED",
        }

    def test_case_sensitivity_compliant(self):
        """Test that complianceCheck is case-sensitive (COMPLIANT vs compliant)."""
        evidence = [
            {"complianceCheck": "compliant", "dataSource": "AWS Config"},  # lowercase
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        # Lowercase "compliant" should NOT match "COMPLIANT", treated as inconclusive
        self.assertIsNone(item.compliance_result)

    def test_case_insensitivity_failed(self):
        """Test that complianceCheck is case-insensitive (FAILED == failed)."""
        evidence = [
            {"complianceCheck": "failed", "dataSource": "AWS Security Hub"},  # lowercase
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        # Lowercase "failed" should match "FAILED" case-insensitively, resulting in FAIL
        self.assertEqual(item.compliance_result, "FAIL")

    def test_empty_string_compliance_check(self):
        """Test that empty string complianceCheck is treated as inconclusive."""
        evidence = [
            {"complianceCheck": "", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.compliance_result)

    def test_whitespace_compliance_check(self):
        """Test that whitespace-only complianceCheck is treated as inconclusive."""
        evidence = [
            {"complianceCheck": "   ", "dataSource": "AWS Config"},
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.compliance_result)

    def test_unexpected_compliance_check_value(self):
        """Test that unexpected values are treated as inconclusive."""
        evidence = [
            {"complianceCheck": "UNKNOWN", "dataSource": "AWS Config"},
            {"complianceCheck": "PENDING", "dataSource": "AWS Config"},
            {"complianceCheck": 123, "dataSource": "AWS Config"},  # Number instead of string
        ]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertIsNone(item.compliance_result)

    def test_large_number_of_evidence_items(self):
        """Test aggregation with large number of evidence items."""
        # Create 1000 evidence items
        evidence = [{"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"} for _ in range(1000)]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "PASS")

    def test_large_number_with_one_failure(self):
        """Test that one failure in many evidence items still causes FAIL."""
        evidence = [{"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"} for _ in range(999)]
        evidence.append({"complianceCheck": "FAILED", "dataSource": "AWS Security Hub"})  # One failure

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)
        self.assertEqual(item.compliance_result, "FAIL")


class TestComplianceItemCreation(unittest.TestCase):
    """Test creating compliance items with evidence."""

    def setUp(self):
        """Set up test fixtures."""
        self.assessment_data = {
            "name": "Test Assessment",
            "arn": "arn:aws:auditmanager:us-east-1:123456789012:assessment/test",
            "framework": {"type": "Standard", "metadata": {"name": "NIST 800-53"}},
            "awsAccount": {"id": "123456789012"},
        }

        self.control_data = {
            "id": "test-id",
            "name": "AC-2 - Account Management",
            "status": "REVIEWED",
        }

    def test_create_with_evidence(self):
        """Test creating compliance item with evidence."""
        evidence = [{"complianceCheck": "COMPLIANT", "dataSource": "AWS Config"}]

        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, evidence)

        self.assertEqual(item.control_id, "AC-2")
        self.assertEqual(len(item.evidence_items), 1)
        self.assertEqual(item.compliance_result, "PASS")

    def test_create_without_evidence(self):
        """Test creating compliance item without evidence (backward compatibility)."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data)

        self.assertEqual(item.control_id, "AC-2")
        self.assertEqual(len(item.evidence_items), 0)
        self.assertIsNone(item.compliance_result)  # No evidence = None (skip update)

    def test_create_with_explicit_none_evidence(self):
        """Test creating compliance item with explicit None evidence."""
        item = AWSAuditManagerComplianceItem(self.assessment_data, self.control_data, None)

        self.assertEqual(item.control_id, "AC-2")
        self.assertEqual(len(item.evidence_items), 0)
        self.assertIsNone(item.compliance_result)  # No evidence = None (skip update)


if __name__ == "__main__":
    unittest.main()
