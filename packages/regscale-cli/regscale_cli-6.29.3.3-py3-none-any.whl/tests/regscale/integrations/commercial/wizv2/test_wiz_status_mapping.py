"""
Unit tests for Wiz status mapping functionality.
Tests that Wiz issue statuses are correctly mapped to RegScale IssueStatus.
"""

from unittest.mock import Mock, patch

import pytest

from regscale.integrations.commercial.wizv2.issue import WizIssue
from regscale.integrations.commercial.wizv2.scanner import WizVulnerabilityIntegration
from regscale.models import IssueStatus


class TestWizStatusMapping:
    """Test class for Wiz status mapping functionality."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock app with config."""
        app = Mock()
        app.config = {}
        return app

    @pytest.fixture
    def wiz_integration(self, mock_app):
        """Create a WizVulnerabilityIntegration instance."""
        with patch("regscale.integrations.scanner_integration.ScannerIntegration.__init__"):
            integration = WizVulnerabilityIntegration(app=mock_app, plan_id=1)
            integration.app = mock_app
            integration._compliance_settings = None
            return integration

    @pytest.fixture
    def wiz_issue_integration(self, mock_app):
        """Create a WizIssue instance."""
        with patch("regscale.integrations.scanner_integration.ScannerIntegration.__init__"):
            integration = WizIssue(app=mock_app, plan_id=1)
            integration.app = mock_app
            integration._compliance_settings = None
            return integration

    def test_default_status_mapping_open_statuses(self, wiz_integration):
        """Test that OPEN and IN_PROGRESS statuses map to IssueStatus.Open."""
        open_statuses = ["OPEN", "Open", "open", "IN_PROGRESS", "In_Progress", "in_progress"]

        for status in open_statuses:
            result = wiz_integration._get_default_issue_status_mapping(status)
            assert result == IssueStatus.Open, f"Status '{status}' should map to Open, got {result}"

    def test_default_status_mapping_closed_statuses(self, wiz_integration):
        """Test that RESOLVED and REJECTED statuses map to IssueStatus.Closed."""
        closed_statuses = ["RESOLVED", "Resolved", "resolved", "REJECTED", "Rejected", "rejected"]

        for status in closed_statuses:
            result = wiz_integration._get_default_issue_status_mapping(status)
            assert result == IssueStatus.Closed, f"Status '{status}' should map to Closed, got {result}"

    def test_default_status_mapping_unknown_status(self, wiz_integration):
        """Test that unknown statuses default to IssueStatus.Open."""
        unknown_statuses = ["UNKNOWN", "PENDING", "WEIRD_STATUS", ""]

        for status in unknown_statuses:
            result = wiz_integration._get_default_issue_status_mapping(status)
            assert result == IssueStatus.Open, f"Unknown status '{status}' should default to Open, got {result}"

    def test_map_status_to_issue_status_without_compliance_settings(self, wiz_integration):
        """Test status mapping without compliance settings (uses default mapping)."""
        # Ensure no compliance settings
        wiz_integration._compliance_settings = None

        test_cases = [
            ("OPEN", IssueStatus.Open),
            ("IN_PROGRESS", IssueStatus.Open),
            ("RESOLVED", IssueStatus.Closed),
            ("REJECTED", IssueStatus.Closed),
            ("UNKNOWN", IssueStatus.Open),
        ]

        for wiz_status, expected in test_cases:
            result = wiz_integration.map_status_to_issue_status(wiz_status)
            assert result == expected, f"Status '{wiz_status}' should map to {expected}, got {result}"

    def test_map_status_to_issue_status_with_compliance_settings(self, wiz_integration):
        """Test status mapping with compliance settings."""
        # Mock compliance settings
        mock_compliance = Mock()
        mock_compliance.get_field_labels.return_value = ["Open", "In Progress", "Closed", "Resolved"]
        wiz_integration._compliance_settings = mock_compliance

        # Test that IN_PROGRESS still maps to Open even with compliance settings
        result = wiz_integration.map_status_to_issue_status("IN_PROGRESS")
        assert result == IssueStatus.Open, "IN_PROGRESS should map to Open with compliance settings"

        # Test other statuses
        result = wiz_integration.map_status_to_issue_status("RESOLVED")
        assert result == IssueStatus.Closed, "RESOLVED should map to Closed with compliance settings"

    def test_match_wiz_status_to_label(self, wiz_integration):
        """Test the _match_wiz_status_to_label method."""
        # Test open status mappings
        assert wiz_integration._match_wiz_status_to_label("open", "Open") == IssueStatus.Open
        assert wiz_integration._match_wiz_status_to_label("in_progress", "In Progress") == IssueStatus.Open
        assert wiz_integration._match_wiz_status_to_label("in_progress", "Active") == IssueStatus.Open

        # Test closed status mappings
        assert wiz_integration._match_wiz_status_to_label("resolved", "Closed") == IssueStatus.Closed
        assert wiz_integration._match_wiz_status_to_label("rejected", "Resolved") == IssueStatus.Closed

        # Test non-matching combinations
        assert wiz_integration._match_wiz_status_to_label("open", "Closed") is None
        assert wiz_integration._match_wiz_status_to_label("resolved", "Open") is None

    def test_wiz_issue_status_mapping(self, wiz_issue_integration):
        """Test that WizIssue class uses the same status mapping."""
        test_cases = [
            ("OPEN", IssueStatus.Open),
            ("IN_PROGRESS", IssueStatus.Open),
            ("RESOLVED", IssueStatus.Closed),
            ("REJECTED", IssueStatus.Closed),
        ]

        for wiz_status, expected in test_cases:
            result = wiz_issue_integration.map_status_to_issue_status(wiz_status)
            assert result == expected, f"WizIssue: Status '{wiz_status}' should map to {expected}, got {result}"

    @pytest.mark.parametrize(
        "status,expected",
        [
            ("OPEN", IssueStatus.Open),
            ("Open", IssueStatus.Open),
            ("open", IssueStatus.Open),
            ("IN_PROGRESS", IssueStatus.Open),
            ("In_Progress", IssueStatus.Open),
            ("in_progress", IssueStatus.Open),
            ("RESOLVED", IssueStatus.Closed),
            ("Resolved", IssueStatus.Closed),
            ("resolved", IssueStatus.Closed),
            ("REJECTED", IssueStatus.Closed),
            ("Rejected", IssueStatus.Closed),
            ("rejected", IssueStatus.Closed),
            ("UNKNOWN_STATUS", IssueStatus.Open),
            ("", IssueStatus.Open),
        ],
    )
    def test_comprehensive_status_mapping(self, wiz_integration, status, expected):
        """Comprehensive parameterized test for all status variations."""
        result = wiz_integration.map_status_to_issue_status(status)
        assert result == expected, f"Status '{status}' should map to {expected}, got {result}"
