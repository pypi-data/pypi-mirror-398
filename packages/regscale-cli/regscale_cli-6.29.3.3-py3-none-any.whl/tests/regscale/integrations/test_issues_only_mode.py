"""
Tests for issues_only mode in ScannerIntegration.

This test suite verifies that when issues_only=True is set on a ScannerIntegration,
only Issues are created and no Vulnerabilities are created, regardless of whether
the findings have plugin_name or cve fields.
"""

import pytest
from unittest.mock import MagicMock, patch

from regscale.integrations.scanner_integration import ScannerIntegration
from regscale.integrations.scanner.models import IntegrationFinding
from regscale import models as regscale_models


class ConcreteScannerIntegration(ScannerIntegration):
    """Concrete implementation of ScannerIntegration for testing."""

    def fetch_assets(self):
        """Stub implementation."""
        return []

    def fetch_findings(self):
        """Stub implementation."""
        return []


class TestIssuesOnlyMode:
    """Test suite for issues_only mode functionality."""

    @pytest.fixture
    def issues_only_scanner(self):
        """Create a ScannerIntegration instance with issues_only=True."""
        with patch("regscale.integrations.scanner.context.ScannerContext"):
            scanner = ConcreteScannerIntegration(
                plan_id=1,
                parent_module="securityplans",
                title="Test Scanner",
                issues_only=True,
            )
            return scanner

    @pytest.fixture
    def normal_scanner(self):
        """Create a normal ScannerIntegration instance (issues_only=False)."""
        with patch("regscale.integrations.scanner.context.ScannerContext"):
            scanner = ConcreteScannerIntegration(
                plan_id=1,
                parent_module="securityplans",
                title="Test Scanner",
                issues_only=False,
            )
            return scanner

    @pytest.fixture
    def finding_with_vuln_fields(self):
        """Create a finding with plugin_name and cve (would normally create vulnerability)."""
        return IntegrationFinding(
            control_labels=[],
            title="Test Vulnerability Finding",
            category="Security",
            severity=regscale_models.IssueSeverity.High,
            description="Test finding with CVE",
            status=regscale_models.IssueStatus.Open,
            plugin_name="TestPlugin",
            cve="CVE-2024-12345",
        )

    @pytest.fixture
    def finding_without_vuln_fields(self):
        """Create a finding without plugin_name or cve (would not create vulnerability)."""
        return IntegrationFinding(
            control_labels=[],
            title="Test Issue Finding",
            category="Compliance",
            severity=regscale_models.IssueSeverity.Moderate,
            description="Test finding without CVE",
            status=regscale_models.IssueStatus.Open,
        )

    def test_issues_only_flag_exists(self, issues_only_scanner):
        """Test that issues_only flag can be set on ScannerIntegration."""
        assert hasattr(issues_only_scanner, "issues_only")
        assert issues_only_scanner.issues_only is True

    def test_issues_only_prevents_vulnerability_creation(self, issues_only_scanner, finding_with_vuln_fields):
        """
        Test that when issues_only=True, findings with plugin_name and cve
        do NOT get converted to vulnerabilities.
        """
        scan_history = MagicMock(spec=regscale_models.ScanHistory)
        scan_history.id = 123

        result = issues_only_scanner._try_convert_finding_to_vulnerability(finding_with_vuln_fields, scan_history)

        assert result is None, "issues_only mode should prevent vulnerability creation"

    def test_normal_mode_allows_vulnerability_creation(self, normal_scanner, finding_with_vuln_fields):
        """
        Test that when issues_only=False (default), findings with plugin_name and cve
        DO get converted to vulnerabilities.
        """
        scan_history = MagicMock(spec=regscale_models.ScanHistory)
        scan_history.id = 123
        # Add severity count attributes
        scan_history.vLow = 0
        scan_history.vMedium = 0
        scan_history.vHigh = 0
        scan_history.vCritical = 0
        scan_history.vInfo = 0

        with patch.object(normal_scanner, "_convert_finding_to_vulnerability") as mock_convert:
            mock_convert.return_value = MagicMock(spec=regscale_models.Vulnerability)

            result = normal_scanner._try_convert_finding_to_vulnerability(finding_with_vuln_fields, scan_history)

            assert result is not None, "Normal mode should allow vulnerability creation"
            mock_convert.assert_called_once_with(finding_with_vuln_fields)

    def test_issues_only_still_creates_issues(self, issues_only_scanner, finding_with_vuln_fields):
        """
        Test that issues_only mode still creates Issues from findings.
        """
        with patch.object(issues_only_scanner, "_convert_finding_to_issue") as mock_convert:
            mock_convert.return_value = MagicMock(spec=regscale_models.Issue)

            result = issues_only_scanner._try_convert_finding_to_issue(finding_with_vuln_fields)

            assert result is not None, "issues_only mode should still create Issues"
            mock_convert.assert_called_once_with(finding_with_vuln_fields)

    def test_issues_only_mode_end_to_end(self, issues_only_scanner, finding_with_vuln_fields):
        """
        Integration test: Verify that update_regscale_findings() with issues_only=True
        only creates Issues and no Vulnerabilities.
        """
        findings = [finding_with_vuln_fields]

        with patch.object(issues_only_scanner, "_send_issues_batch") as mock_send_issues, patch.object(
            issues_only_scanner, "_send_vulnerabilities_batch"
        ) as mock_send_vulns, patch.object(issues_only_scanner, "_try_convert_finding_to_issue") as mock_to_issue:

            mock_to_issue.return_value = MagicMock(spec=regscale_models.Issue)

            issues_only_scanner.update_regscale_findings(iter(findings))

            # Verify Issues were sent
            mock_send_issues.assert_called_once()
            issues_sent = mock_send_issues.call_args[0][0]
            assert len(issues_sent) == 1

            # Verify NO Vulnerabilities were sent
            mock_send_vulns.assert_called_once()
            vulns_sent = mock_send_vulns.call_args[0][0]
            assert len(vulns_sent) == 0, "issues_only mode should not send any vulnerabilities"

    def test_default_issues_only_is_false(self, normal_scanner):
        """Test that issues_only defaults to False for backward compatibility."""
        assert normal_scanner.issues_only is False


class TestFedRAMPPOAMUsesIssuesOnly:
    """Test that FedRAMP POAM integration uses issues_only mode."""

    def test_fedramp_poam_sets_issues_only(self):
        """Verify that FedrampPoamIntegration sets issues_only=True."""
        from regscale.integrations.public.fedramp.poam.scanner import FedrampPoamIntegration

        with patch("regscale.integrations.scanner.context.ScannerContext"):
            scanner = FedrampPoamIntegration(
                plan_id=1, parent_module="securityplans", file_path="/tmp/test.xlsx", poam_id_column="POAM ID"
            )

            assert hasattr(scanner, "issues_only"), "FedrampPoamIntegration should have issues_only flag"
            assert scanner.issues_only is True, "FedRAMP POAM should set issues_only=True"
