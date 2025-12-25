"""
Tests for REG-19179: Duplicate issue creation prevention in ScannerIntegration.

This test verifies that processing ONE finding results in exactly ONE issue
being created, not duplicates.

The bug was: process_finding() was creating issues twice - once via the
vulnerability path (_handle_associated_issue) and once via queue_issue_from_finding.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from collections import defaultdict

from regscale import models as regscale_models
from regscale.integrations.scanner.models import IntegrationFinding


class TestDuplicateIssuePrevention:
    """Test suite for REG-19179: Duplicate issue creation prevention."""

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding with vulnerability fields."""
        return IntegrationFinding(
            control_labels=[],
            title="Test Vulnerability",
            category="Security",
            severity=regscale_models.IssueSeverity.High,
            description="Test finding",
            status=regscale_models.IssueStatus.Open,
            plugin_name="TestPlugin",
            plugin_id="12345",
            cve="CVE-2024-12345",
            asset_identifier="test-asset-001",
            external_id="EXT-001",
        )

    def test_one_finding_creates_one_issue(self, sample_finding):
        """
        REG-19179: Processing ONE finding should create exactly ONE issue.

        This is the behavior we care about - not which internal methods call what,
        but that the end result is correct: 1 finding = 1 issue, not 2.
        """
        from regscale.integrations.scanner_integration import ScannerIntegration, ScannerIntegrationType

        # Create concrete subclass for testing
        class TestScanner(ScannerIntegration):
            def fetch_assets(self):
                return []

            def fetch_findings(self):
                return []

        with patch.object(ScannerIntegration, "__init__", lambda self, **kwargs: None):
            scanner = TestScanner.__new__(TestScanner)

            # Set required attributes for process_finding to work
            scanner.plan_id = 1
            scanner.title = "Test Scanner"
            scanner.type = ScannerIntegrationType.VULNERABILITY
            scanner.issues_only = False
            scanner._pending_control_updates = set()
            scanner.scan_date = "2024-01-01"
            scanner.enable_finding_date_update = False

            # Mock asset lookup to return a valid asset
            mock_asset = MagicMock()
            mock_asset.id = 100
            scanner.get_asset_by_identifier = MagicMock(return_value=mock_asset)

            # Mock vulnerability creation path
            scanner.create_vulnerability_from_finding = MagicMock()
            scanner._has_required_vulnerability_fields = MagicMock(return_value=True)
            scanner._check_asset_requirements = MagicMock(return_value=True)
            scanner._handle_vulnerability_creation_error = MagicMock()
            scanner.set_severity_count_for_scan = MagicMock()
            scanner.scan_history_lock = MagicMock()

            # Mock checklist path (not used but needed)
            scanner.handle_failing_checklist = MagicMock()

            # Track issue creation - THIS IS THE KEY MEASUREMENT
            issue_creation_calls = []

            def track_issue_creation(title, finding):
                issue_creation_calls.append({"title": title, "finding_id": finding.external_id})
                return MagicMock(controlImplementationIds=[])

            scanner.create_or_update_issue_from_finding = MagicMock(side_effect=track_issue_creation)

            # Mock date update
            scanner.update_integration_finding_dates = MagicMock(return_value=sample_finding)

            # Process ONE finding
            scan_history = MagicMock()
            scan_history.id = 123
            current_vulnerabilities = defaultdict(set)

            scanner.process_finding(sample_finding, scan_history, current_vulnerabilities)

            # THE CRITICAL ASSERTION: 1 finding should create exactly 1 issue
            assert len(issue_creation_calls) == 1, (
                f"Processing 1 finding should create exactly 1 issue. "
                f"Got {len(issue_creation_calls)} issue creation calls instead. "
                f"This indicates duplicate issue creation (REG-19179)."
            )

    def test_five_findings_create_five_issues(self):
        """
        REG-19179: Processing N findings should create exactly N issues.

        Extended test to verify the fix works across multiple findings.
        """
        from regscale.integrations.scanner_integration import ScannerIntegration, ScannerIntegrationType

        class TestScanner(ScannerIntegration):
            def fetch_assets(self):
                return []

            def fetch_findings(self):
                return []

        with patch.object(ScannerIntegration, "__init__", lambda self, **kwargs: None):
            scanner = TestScanner.__new__(TestScanner)

            # Set required attributes
            scanner.plan_id = 1
            scanner.title = "Test Scanner"
            scanner.type = ScannerIntegrationType.VULNERABILITY
            scanner.issues_only = False
            scanner._pending_control_updates = set()
            scanner.scan_date = "2024-01-01"
            scanner.enable_finding_date_update = False

            mock_asset = MagicMock()
            mock_asset.id = 100
            scanner.get_asset_by_identifier = MagicMock(return_value=mock_asset)

            scanner.create_vulnerability_from_finding = MagicMock()
            scanner._has_required_vulnerability_fields = MagicMock(return_value=True)
            scanner._check_asset_requirements = MagicMock(return_value=True)
            scanner._handle_vulnerability_creation_error = MagicMock()
            scanner.set_severity_count_for_scan = MagicMock()
            scanner.scan_history_lock = MagicMock()
            scanner.handle_failing_checklist = MagicMock()

            # Track all issue creation calls
            issue_creation_calls = []

            def track_issue_creation(title, finding):
                issue_creation_calls.append({"title": title, "finding_id": finding.external_id})
                return MagicMock(controlImplementationIds=[])

            scanner.create_or_update_issue_from_finding = MagicMock(side_effect=track_issue_creation)

            def passthrough_finding(finding, existing_issues_dict, scan_history):
                return finding

            scanner.update_integration_finding_dates = MagicMock(side_effect=passthrough_finding)

            # Create 5 findings
            findings = [
                IntegrationFinding(
                    control_labels=[],
                    title=f"Vulnerability {i}",
                    category="Security",
                    severity=regscale_models.IssueSeverity.High,
                    description=f"Test finding {i}",
                    status=regscale_models.IssueStatus.Open,
                    plugin_name="TestPlugin",
                    plugin_id=str(i),
                    asset_identifier="test-asset-001",
                    external_id=f"EXT-{i:03d}",
                )
                for i in range(5)
            ]

            scan_history = MagicMock()
            scan_history.id = 123
            current_vulnerabilities = defaultdict(set)

            # Process all 5 findings
            for finding in findings:
                scanner.process_finding(finding, scan_history, current_vulnerabilities)

            # 5 findings should create exactly 5 issues (not 10)
            assert len(issue_creation_calls) == 5, (
                f"Processing 5 findings should create exactly 5 issues. "
                f"Got {len(issue_creation_calls)} issue creation calls instead. "
                f"This indicates duplicate issue creation (REG-19179)."
            )
