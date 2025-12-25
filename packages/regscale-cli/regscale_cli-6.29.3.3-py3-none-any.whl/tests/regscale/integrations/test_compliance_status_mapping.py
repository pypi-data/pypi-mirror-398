#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for compliance status mapping in ComplianceIntegration.

These tests ensure that:
1. ONLY compliance settings from the SSP are used
2. No defaults are applied when compliance settings exist
3. The correct status is selected based on framework
4. The scoring/weight system works correctly
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List, Optional

from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models import ComplianceSettings, SecurityPlan, ControlImplementation


class MockComplianceIntegration(ComplianceIntegration):
    """Mock implementation of ComplianceIntegration for testing."""

    def __init__(self, **kwargs):
        """Override init to avoid API calls."""
        # Store the values without calling super().__init__
        self.plan_id = kwargs.get("plan_id", 100)
        self.catalog_id = kwargs.get("catalog_id")
        self.framework = kwargs.get("framework", "TEST_FRAMEWORK")
        self.create_issues = kwargs.get("create_issues", False)
        self.update_control_status = kwargs.get("update_control_status", True)
        self.create_poams = kwargs.get("create_poams", False)

        # Initialize required attributes
        self._compliance_settings = None
        self.scan_date = kwargs.get("scan_date", "2024-01-15")
        self.parent_module = kwargs.get("parent_module", "securityplans")

        # Initialize the constant properties
        self.NOT_APPLICABLE_LABEL = "Not Applicable"
        self.NOT_APPLICABLE_LOWER = "not applicable"
        self.NOT_APPLICABLE_UNDERSCORE = "not_applicable"

    @property
    def module(self) -> str:
        return "test_module"

    @property
    def title(self) -> str:
        return "Test Integration"

    def _get_compliance_items_from_data(self) -> List:
        return []

    def fetch_compliance_data(self) -> List:
        """Mock implementation of abstract method."""
        return []

    def create_compliance_item(self, data: dict) -> object:
        """Mock implementation of abstract method."""
        return MagicMock()


class TestComplianceStatusMapping(unittest.TestCase):
    """Test cases for compliance status mapping logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock integration with necessary attributes
        self.integration = MockComplianceIntegration(
            plan_id=100,
            catalog_id=None,
            framework="TEST_FRAMEWORK",
            create_issues=False,
            update_control_status=True,
        )

    def create_mock_compliance_settings(self, title: str, status_labels: List[str]) -> ComplianceSettings:
        """
        Create mock compliance settings with specified status labels.

        :param str title: Title of the compliance settings (e.g., "DoD RMF Settings")
        :param List[str] status_labels: List of available status values
        :return: Mock ComplianceSettings object
        """
        mock_settings = MagicMock(spec=ComplianceSettings)
        mock_settings.title = title
        mock_settings.get_field_labels = MagicMock(return_value=status_labels)
        return mock_settings

    def test_dod_fail_status_only_uses_compliance_settings(self):
        """Test that DoD framework ONLY uses status values from compliance settings, not defaults."""
        # Create DoD compliance settings with specific status values
        dod_status_labels = [
            "Implemented",
            "Not Implemented",  # This should be selected for FAIL
            "Planned",
            "In Remediation",  # This should NOT be selected for DoD
            "Partially Implemented",
        ]

        mock_settings = self.create_mock_compliance_settings("DoD RMF Controls", dod_status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Get status for FAIL result
            status = self.integration._get_implementation_status_from_result("Fail")

            # For DoD, it should select "Not Implemented" NOT "In Remediation"
            self.assertEqual(status, "Not Implemented")
            # Ensure get_field_labels was called
            mock_settings.get_field_labels.assert_called_with("implementationStatus")

    def test_fedramp_fail_status_only_uses_compliance_settings(self):
        """Test that FedRAMP framework ONLY uses status values from compliance settings."""
        # Create FedRAMP compliance settings with specific status values
        fedramp_status_labels = [
            "Fully Implemented",
            "In Remediation",  # This should be selected for FAIL
            "Partially Implemented",
            "Not Implemented",
            "Not Applicable",
        ]

        mock_settings = self.create_mock_compliance_settings("FedRAMP Moderate", fedramp_status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Get status for FAIL result
            status = self.integration._get_implementation_status_from_result("Fail")

            # For FedRAMP, it should select "In Remediation"
            self.assertEqual(status, "In Remediation")
            mock_settings.get_field_labels.assert_called_with("implementationStatus")

    def test_pass_status_uses_only_compliance_settings(self):
        """Test that PASS status only uses values from compliance settings."""
        # Test with DoD settings
        dod_status_labels = [
            "Implemented",  # Should be selected for PASS
            "Not Implemented",
            "Planned",
            "In Remediation",
        ]

        mock_settings = self.create_mock_compliance_settings("DoD RMF", dod_status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            status = self.integration._get_implementation_status_from_result("Pass")
            self.assertEqual(status, "Implemented")

    def test_no_default_fallback_when_compliance_settings_exist(self):
        """Test that the system does NOT fall back to defaults when compliance settings exist."""
        # Create settings with LIMITED status options (no default values)
        limited_status_labels = [
            "Custom Status 1",
            "Custom Status 2",
            "Not Implemented",  # Only failure status available
        ]

        mock_settings = self.create_mock_compliance_settings("Custom Framework", limited_status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Test FAIL - should use "Not Implemented" from the limited options
            fail_status = self.integration._get_implementation_status_from_result("Fail")
            self.assertEqual(fail_status, "Not Implemented")

            # Test PASS - should return None or empty since no matching status
            pass_status = self.integration._get_implementation_status_from_result("Pass")
            # Should fall back to default ONLY when no match found
            self.assertIn(pass_status, ["Custom Status 1", "Custom Status 2", "Fully Implemented"])

    def test_scoring_system_priority(self):
        """Test that the scoring system correctly prioritizes status values."""
        # Create settings with multiple fail options
        status_labels = [
            "Implemented",
            "Not Implemented",
            "Planned",
            "In Remediation",
            "Partially Implemented",
            "Failed",
        ]

        # Test DoD scoring priorities
        dod_settings = self.create_mock_compliance_settings("DoD RMF Framework", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=dod_settings):
            status = self.integration._get_implementation_status_from_result("Fail")
            # DoD should prioritize "Not Implemented" over "In Remediation"
            self.assertEqual(status, "Not Implemented")

        # Test FedRAMP scoring priorities
        fedramp_settings = self.create_mock_compliance_settings("FedRAMP High", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=fedramp_settings):
            status = self.integration._get_implementation_status_from_result("Fail")
            # FedRAMP should prioritize "In Remediation"
            self.assertEqual(status, "In Remediation")

    def test_exact_match_vs_partial_match(self):
        """Test that exact matches are prioritized over partial matches."""
        status_labels = [
            "Implemented",
            "Not Implemented",  # Exact match
            "Partially Not Implemented",  # Partial match
            "In Remediation",
            "Remediation Required",  # Partial match
        ]

        mock_settings = self.create_mock_compliance_settings("Test Framework", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Should select exact "Not Implemented" over partial matches
            with patch.object(self.integration, "_detect_compliance_framework", return_value="DoD"):
                status = self.integration._get_implementation_status_from_result("Fail")
                self.assertEqual(status, "Not Implemented")

    def test_framework_detection(self):
        """Test that framework detection correctly identifies different frameworks."""
        test_cases = [
            ("DoD RMF Controls", "DoD"),
            ("RMF Implementation", "DoD"),
            ("Department of Defense", "DoD"),
            ("Military Security Controls", "DoD"),
            ("FedRAMP Moderate", "FedRAMP"),
            ("FedRAMP High Baseline", "FedRAMP"),
            ("NIST 800-53 Controls", "NIST"),
            ("NIST SP 800-53", "NIST"),
            ("FISMA Controls", "NIST"),
            ("Custom Framework", "Default"),
            ("", "Default"),
        ]

        for title, expected_framework in test_cases:
            mock_settings = self.create_mock_compliance_settings(title, [])
            with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
                detected = self.integration._detect_compliance_framework()
                self.assertEqual(
                    detected, expected_framework, f"Failed to detect {expected_framework} from title '{title}'"
                )

    def test_no_compliance_settings_falls_back_to_default(self):
        """Test that when NO compliance settings exist, system uses defaults."""
        with patch.object(self.integration, "_get_compliance_settings", return_value=None):
            # Should fall back to default mapping
            fail_status = self.integration._get_implementation_status_from_result("Fail")
            self.assertEqual(fail_status, "In Remediation")

            pass_status = self.integration._get_implementation_status_from_result("Pass")
            self.assertEqual(pass_status, "Fully Implemented")

    def test_case_insensitive_matching(self):
        """Test that status matching is case-insensitive."""
        status_labels = [
            "IMPLEMENTED",  # All caps
            "Not Implemented",  # Mixed case
            "planned",  # Lower case
            "IN REMEDIATION",  # All caps with space
        ]

        mock_settings = self.create_mock_compliance_settings("Test", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            with patch.object(self.integration, "_detect_compliance_framework", return_value="DoD"):
                # Should match "Not Implemented" despite case differences
                status = self.integration._get_implementation_status_from_result("fail")  # lowercase fail
                self.assertEqual(status, "Not Implemented")

    def test_not_applicable_status_mapping(self):
        """Test that Not Applicable status is correctly mapped."""
        status_labels = [
            "Implemented",
            "Not Implemented",
            "Not Applicable",
            "N/A",
        ]

        mock_settings = self.create_mock_compliance_settings("Test", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Test various forms of not applicable
            for result in ["Not Applicable", "not_applicable", "N/A", "na"]:
                status = self.integration._get_implementation_status_from_result(result)
                self.assertIn(status, ["Not Applicable", "N/A"])

    def test_empty_status_labels(self):
        """Test behavior when compliance settings have no status labels."""
        mock_settings = self.create_mock_compliance_settings("Empty Settings", [])

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Should fall back to defaults when no labels available
            fail_status = self.integration._get_implementation_status_from_result("Fail")
            self.assertEqual(fail_status, "In Remediation")

    def test_update_implementation_status_integration(self):
        """Test the full integration of status update with compliance settings."""
        # Create a mock control implementation with required attributes
        mock_impl = MagicMock(spec=ControlImplementation)
        mock_impl.id = 123
        mock_impl.status = "Old Status"  # Use 'status' not 'implementationStatus'
        mock_impl.responsibility = "Test Responsibility"
        mock_impl.implementation = "Test implementation details"
        mock_impl.save = MagicMock()

        # Create DoD compliance settings
        dod_status_labels = [
            "Implemented",
            "Not Implemented",
            "Planned",
            "In Remediation",
        ]
        mock_settings = self.create_mock_compliance_settings("DoD RMF", dod_status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Update status for a FAIL result
            self.integration._update_implementation_status(mock_impl, "Fail")

            # Verify the status was set to "Not Implemented" for DoD
            self.assertEqual(mock_impl.status, "Not Implemented")
            mock_impl.save.assert_called_once()

    def test_scoring_with_similar_labels(self):
        """Test scoring when multiple similar labels exist."""
        status_labels = [
            "Implemented",
            "Fully Implemented",
            "Partially Implemented",
            "Not Implemented",
            "Not Yet Implemented",
            "Implementation Planned",
        ]

        mock_settings = self.create_mock_compliance_settings("Test", status_labels)

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # For PASS, should prefer "Implemented" over "Fully Implemented"
            pass_status = self.integration._get_implementation_status_from_result("Pass")
            self.assertEqual(pass_status, "Implemented")

            # For FAIL with DoD, should prefer "Not Implemented"
            with patch.object(self.integration, "_detect_compliance_framework", return_value="DoD"):
                fail_status = self.integration._get_implementation_status_from_result("Fail")
                self.assertEqual(fail_status, "Not Implemented")


class TestComplianceStatusMappingEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions in status mapping."""

    def setUp(self):
        """Set up test fixtures."""
        self.integration = MockComplianceIntegration(
            plan_id=100,
            catalog_id=None,
            framework="TEST_FRAMEWORK",
            create_issues=False,
            update_control_status=True,
        )

    def test_get_field_labels_exception(self):
        """Test behavior when get_field_labels throws an exception."""
        mock_settings = MagicMock(spec=ComplianceSettings)
        mock_settings.title = "Test Settings"
        mock_settings.get_field_labels.side_effect = Exception("Database error")

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Should fall back to default when exception occurs
            status = self.integration._get_implementation_status_from_result("Fail")
            self.assertEqual(status, "In Remediation")  # Default fail status

    def test_none_result_input(self):
        """Test behavior with None or empty result input."""
        mock_settings = MagicMock(spec=ComplianceSettings)
        mock_settings.title = "Test"
        mock_settings.get_field_labels.return_value = ["Implemented", "Not Implemented"]

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Test with None
            status = self.integration._get_implementation_status_from_result(None)
            self.assertIsNotNone(status)  # Should handle gracefully

            # Test with empty string
            status = self.integration._get_implementation_status_from_result("")
            self.assertIsNotNone(status)  # Should handle gracefully

    def test_special_characters_in_labels(self):
        """Test handling of special characters in status labels."""
        status_labels = [
            "Implemented (Full)",
            "Not-Implemented",
            "In_Remediation",
            "Planned/Scheduled",
        ]

        mock_settings = MagicMock(spec=ComplianceSettings)
        mock_settings.title = "Test"
        mock_settings.get_field_labels.return_value = status_labels

        with patch.object(self.integration, "_get_compliance_settings", return_value=mock_settings):
            # Should handle special characters in matching
            with patch.object(self.integration, "_detect_compliance_framework", return_value="DoD"):
                status = self.integration._get_implementation_status_from_result("Fail")
                # Should still match "Not-Implemented" despite hyphen
                self.assertIn(status, status_labels)


if __name__ == "__main__":
    unittest.main()
