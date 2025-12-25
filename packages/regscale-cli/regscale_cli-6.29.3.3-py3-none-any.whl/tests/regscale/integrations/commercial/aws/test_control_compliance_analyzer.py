#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for ControlComplianceAnalyzer class.

Tests the control pass/fail determination logic based on AWS Audit Manager evidence insights.
"""

import unittest
from unittest.mock import MagicMock, patch

from regscale.integrations.commercial.aws.control_compliance_analyzer import (
    ComplianceAnalysis,
    ComplianceStatus,
    ControlComplianceAnalyzer,
    EvidenceInsight,
    EvidenceType,
)


class TestControlComplianceAnalyzer(unittest.TestCase):
    """Test cases for ControlComplianceAnalyzer."""

    def setUp(self):
        """Set up test fixtures."""
        self.control_id = "AC-2"
        self.analyzer = ControlComplianceAnalyzer(self.control_id)

    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertEqual(self.analyzer.control_id, "AC-2")
        self.assertEqual(len(self.analyzer.evidence_insights), 0)
        self.assertEqual(self.analyzer._compliant_count, 0)
        self.assertEqual(self.analyzer._noncompliant_count, 0)
        self.assertEqual(self.analyzer._inconclusive_count, 0)
        self.assertEqual(self.analyzer._not_applicable_count, 0)

    def test_pass_status_all_compliant(self):
        """Test PASS status when all evidence is compliant."""
        # Add compliant evidence
        evidence_data = {
            "id": "evidence-1",
            "dataSource": "AWS Security Hub",
            "complianceCheck": "PASS",
            "time": "2025-01-15T10:00:00Z",
        }
        self.analyzer.add_evidence_insight(evidence_data)

        evidence_data2 = {
            "id": "evidence-2",
            "dataSource": "AWS Config",
            "complianceCheck": "COMPLIANT",
            "time": "2025-01-15T10:01:00Z",
        }
        self.analyzer.add_evidence_insight(evidence_data2)

        status, details = self.analyzer.determine_control_status()

        self.assertEqual(status, "PASS")
        self.assertEqual(details["reason"], "All evidence indicates compliance")
        self.assertEqual(details["compliant_count"], 2)
        # Non-compliant count not included in PASS status details

    def test_fail_status_any_noncompliant(self):
        """Test FAIL status when any evidence is non-compliant."""
        # Add mixed evidence
        compliant_evidence = {
            "id": "evidence-1",
            "dataSource": "AWS Security Hub",
            "complianceCheck": "PASS",
        }
        self.analyzer.add_evidence_insight(compliant_evidence)

        noncompliant_evidence = {
            "id": "evidence-2",
            "dataSource": "AWS Config",
            "complianceCheck": "NON_COMPLIANT",
        }
        self.analyzer.add_evidence_insight(noncompliant_evidence)

        status, details = self.analyzer.determine_control_status()

        self.assertEqual(status, "FAIL")
        self.assertEqual(details["reason"], "Evidence indicates non-compliance")
        self.assertEqual(details["noncompliant_count"], 1)
        self.assertEqual(details["compliant_count"], 1)

    def test_inconclusive_status_only_inconclusive(self):
        """Test INCONCLUSIVE status when only inconclusive evidence exists."""
        # Add inconclusive evidence
        evidence_data = {
            "id": "evidence-1",
            "dataSource": "AWS CloudTrail",
            "complianceCheck": "",  # Empty means inconclusive
        }
        self.analyzer.add_evidence_insight(evidence_data)

        evidence_data2 = {
            "id": "evidence-2",
            "dataSource": "Manual",
            "complianceCheck": "UNKNOWN",
        }
        self.analyzer.add_evidence_insight(evidence_data2)

        status, details = self.analyzer.determine_control_status()

        self.assertEqual(status, "INCONCLUSIVE")
        self.assertEqual(details["reason"], "Only inconclusive evidence available")
        self.assertEqual(details["inconclusive_count"], 2)

    def test_no_data_status(self):
        """Test NO_DATA status when no evidence is available."""
        status, details = self.analyzer.determine_control_status()

        self.assertEqual(status, "NO_DATA")
        self.assertEqual(details["reason"], "No evidence available for assessment")
        self.assertEqual(details["total_evidence_checked"], 0)

    def test_not_applicable_status(self):
        """Test NOT_APPLICABLE status when all evidence is not applicable."""
        # Add not applicable evidence
        evidence_data = {
            "id": "evidence-1",
            "dataSource": "AWS Config",
            "complianceCheck": "NOT_APPLICABLE",
        }
        self.analyzer.add_evidence_insight(evidence_data)

        evidence_data2 = {
            "id": "evidence-2",
            "dataSource": "AWS Security Hub",
            "complianceCheck": "N/A",
        }
        self.analyzer.add_evidence_insight(evidence_data2)

        status, details = self.analyzer.determine_control_status()

        self.assertEqual(status, "NOT_APPLICABLE")
        self.assertEqual(details["reason"], "Evidence is not applicable to this control")
        self.assertEqual(details["not_applicable_count"], 2)

    def test_compliance_normalization(self):
        """Test compliance check value normalization."""
        test_cases = [
            ("PASS", "COMPLIANT"),
            ("pass", "COMPLIANT"),
            ("PASSED", "COMPLIANT"),
            ("SUCCESS", "COMPLIANT"),
            ("COMPLIANT", "COMPLIANT"),
            ("FAIL", "NON_COMPLIANT"),
            ("fail", "NON_COMPLIANT"),
            ("FAILED", "NON_COMPLIANT"),
            ("NON_COMPLIANT", "NON_COMPLIANT"),
            ("NON-COMPLIANT", "NON_COMPLIANT"),
            ("Non-compliant", "NON_COMPLIANT"),
            ("NOT_APPLICABLE", "NOT_APPLICABLE"),
            ("NOT-APPLICABLE", "NOT_APPLICABLE"),
            ("N/A", "NOT_APPLICABLE"),
            ("NA", "NOT_APPLICABLE"),
            ("", "INCONCLUSIVE"),
            ("UNKNOWN", "INCONCLUSIVE"),
            ("SOMETHING_ELSE", "INCONCLUSIVE"),
        ]

        for input_value, expected in test_cases:
            result = self.analyzer._normalize_compliance_check(input_value)
            self.assertEqual(result, expected, f"Failed to normalize '{input_value}' to '{expected}', got '{result}'")

    def test_add_evidence_from_insights_api(self):
        """Test adding evidence from AWS Audit Manager Control Insights API."""
        insights_data = {
            "evidenceInsights": {
                "compliantEvidenceCount": 15,
                "noncompliantEvidenceCount": 2,
                "inconclusiveEvidenceCount": 5,
            }
        }

        self.analyzer.add_evidence_from_insights_api(insights_data)

        # Check counts
        self.assertEqual(self.analyzer._compliant_count, 15)
        self.assertEqual(self.analyzer._noncompliant_count, 2)
        self.assertEqual(self.analyzer._inconclusive_count, 5)

        # Check status determination (should be FAIL due to non-compliant evidence)
        status, details = self.analyzer.determine_control_status()
        self.assertEqual(status, "FAIL")

    def test_compliance_score_calculation(self):
        """Test compliance score calculation."""
        # All compliant = score 1.0
        self.analyzer._compliant_count = 10
        self.analyzer._noncompliant_count = 0
        self.analyzer._inconclusive_count = 0
        score = self.analyzer.get_compliance_score()
        self.assertEqual(score, 1.0)

        # Any non-compliant = score 0.0
        self.analyzer._noncompliant_count = 1
        score = self.analyzer.get_compliance_score()
        self.assertEqual(score, 0.0)

        # Only inconclusive = score 0.5
        self.analyzer._compliant_count = 0
        self.analyzer._noncompliant_count = 0
        self.analyzer._inconclusive_count = 5
        score = self.analyzer.get_compliance_score()
        self.assertEqual(score, 0.5)

        # Mixed compliant and inconclusive
        self.analyzer._compliant_count = 7
        self.analyzer._noncompliant_count = 0
        self.analyzer._inconclusive_count = 3
        score = self.analyzer.get_compliance_score()
        self.assertEqual(score, 0.7)

    def test_confidence_level_calculation(self):
        """Test confidence level calculation."""
        # Add evidence with different confidence levels
        high_confidence_evidence = {
            "id": "evidence-1",
            "dataSource": "AWS Security Hub",  # 0.95 confidence
            "complianceCheck": "PASS",
        }
        self.analyzer.add_evidence_insight(high_confidence_evidence)

        medium_confidence_evidence = {
            "id": "evidence-2",
            "dataSource": "AWS CloudTrail",  # 0.75 confidence
            "complianceCheck": "PASS",
        }
        self.analyzer.add_evidence_insight(medium_confidence_evidence)

        low_confidence_evidence = {
            "id": "evidence-3",
            "dataSource": "Manual",  # 0.60 confidence
            "complianceCheck": "PASS",
        }
        self.analyzer.add_evidence_insight(low_confidence_evidence)

        confidence = self.analyzer.get_confidence_level()

        # Should be weighted average with quantity factor
        # Average confidence: (0.95 + 0.75 + 0.60) / 3 = 0.766...
        # Quantity factor: min(1.0, 3/10) = 0.3
        # Final: (0.766 * 0.7) + (0.3 * 0.3) = 0.536 + 0.09 = 0.626
        self.assertAlmostEqual(confidence, 0.626, places=2)

    def test_get_compliance_analysis(self):
        """Test getting comprehensive compliance analysis."""
        # Add mixed evidence
        evidence1 = {
            "id": "evidence-1",
            "dataSource": "AWS Security Hub",
            "complianceCheck": "PASS",
        }
        self.analyzer.add_evidence_insight(evidence1)

        evidence2 = {
            "id": "evidence-2",
            "dataSource": "AWS Config",
            "complianceCheck": "COMPLIANT",
        }
        self.analyzer.add_evidence_insight(evidence2)

        evidence3 = {
            "id": "evidence-3",
            "dataSource": "AWS CloudTrail",
            "complianceCheck": "",  # Inconclusive
        }
        self.analyzer.add_evidence_insight(evidence3)

        analysis = self.analyzer.get_compliance_analysis()

        self.assertIsInstance(analysis, ComplianceAnalysis)
        self.assertEqual(analysis.control_id, "AC-2")
        self.assertEqual(analysis.compliance_status, ComplianceStatus.PASS)
        self.assertEqual(analysis.compliant_evidence_count, 2)
        self.assertEqual(analysis.noncompliant_evidence_count, 0)
        self.assertEqual(analysis.inconclusive_evidence_count, 1)
        self.assertEqual(analysis.total_evidence_count, 3)
        # Check that reason mentions inconclusive evidence
        self.assertIn("some evidence inconclusive", analysis.reasoning)
        self.assertIn("AWS Security Hub", analysis.evidence_sources)
        self.assertIn("AWS Config", analysis.evidence_sources)
        self.assertIn("AWS CloudTrail", analysis.evidence_sources)

    def test_evidence_sources_tracking(self):
        """Test tracking of unique evidence sources."""
        # Add evidence from same source multiple times
        for i in range(3):
            evidence = {
                "id": f"evidence-{i}",
                "dataSource": "AWS Security Hub",
                "complianceCheck": "PASS",
            }
            self.analyzer.add_evidence_insight(evidence)

        # Add from different source
        evidence = {
            "id": "evidence-4",
            "dataSource": "AWS Config",
            "complianceCheck": "COMPLIANT",
        }
        self.analyzer.add_evidence_insight(evidence)

        analysis = self.analyzer.get_compliance_analysis()

        # Should only have 2 unique sources
        self.assertEqual(len(analysis.evidence_sources), 2)
        self.assertIn("AWS Security Hub", analysis.evidence_sources)
        self.assertIn("AWS Config", analysis.evidence_sources)

    def test_fail_priority_over_pass(self):
        """Test that any failure overrides passing evidence."""
        # Add 10 compliant evidence items
        for i in range(10):
            evidence = {
                "id": f"compliant-{i}",
                "dataSource": "AWS Security Hub",
                "complianceCheck": "PASS",
            }
            self.analyzer.add_evidence_insight(evidence)

        # Add 1 non-compliant evidence
        fail_evidence = {
            "id": "fail-1",
            "dataSource": "AWS Config",
            "complianceCheck": "NON_COMPLIANT",
        }
        self.analyzer.add_evidence_insight(fail_evidence)

        status, details = self.analyzer.determine_control_status()

        # Should be FAIL despite 10 passing evidences
        self.assertEqual(status, "FAIL")
        self.assertEqual(details["compliant_count"], 10)
        self.assertEqual(details["noncompliant_count"], 1)

    def test_mixed_evidence_with_not_applicable(self):
        """Test mixed evidence including not applicable items."""
        # Add various types of evidence
        self.analyzer.add_evidence_insight({"id": "1", "dataSource": "AWS Security Hub", "complianceCheck": "PASS"})
        self.analyzer.add_evidence_insight({"id": "2", "dataSource": "AWS Config", "complianceCheck": "NOT_APPLICABLE"})
        self.analyzer.add_evidence_insight({"id": "3", "dataSource": "Manual", "complianceCheck": ""})

        status, details = self.analyzer.determine_control_status()

        # Should be PASS (compliant evidence with no failures)
        self.assertEqual(status, "PASS")
        self.assertEqual(details["compliant_count"], 1)
        self.assertEqual(details["not_applicable_count"], 1)
        self.assertEqual(details["inconclusive_count"], 1)

    def test_evidence_with_resource_level_compliance(self):
        """Test evidence with resource-level compliance information."""
        evidence = {
            "id": "evidence-1",
            "dataSource": "AWS Config",
            "complianceCheck": "NON_COMPLIANT",
            "resourceArn": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
            "attributes": {"ruleName": "ec2-instance-managed-by-systems-manager"},
        }
        self.analyzer.add_evidence_insight(evidence)

        # Check that resource information is preserved
        self.assertEqual(len(self.analyzer.evidence_insights), 1)
        insight = self.analyzer.evidence_insights[0]
        self.assertEqual(insight.resource_arn, "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0")
        self.assertEqual(insight.attributes["ruleName"], "ec2-instance-managed-by-systems-manager")


if __name__ == "__main__":
    unittest.main()
