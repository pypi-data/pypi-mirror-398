#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive tests for Wiz Click command handlers with focus on uncovered lines."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from regscale.integrations.commercial.wizv2.click import wiz


class TestWizClickComprehensive:
    """Comprehensive tests for Wiz CLI commands focusing on uncovered lines."""

    @pytest.fixture
    def runner(self):
        """Create a Click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_wiz_variables(self):
        """Mock WizVariables to avoid environment dependencies."""
        with patch("regscale.integrations.commercial.wizv2.click.WizVariables") as mock:
            mock.wizClientId = "env_client_id"
            mock.wizClientSecret = "env_client_secret"
            mock.wizInventoryFilterBy = "{}"
            mock.wizIssueFilterBy = "{}"
            yield mock

    # ========================================
    # Test authenticate command (lines 28-30)
    # ========================================

    def test_authenticate_with_provided_credentials(self, runner, mock_wiz_variables):
        """Test authenticate command with provided client_id and client_secret."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            mock_auth.return_value = "test_token"

            result = runner.invoke(
                wiz,
                [
                    "authenticate",
                    "--client_id",
                    "test_client_id",
                    "--client_secret",
                    "test_secret",
                ],
            )

            # Verify wiz_authenticate was called with the provided credentials
            mock_auth.assert_called_once_with("test_client_id", "test_secret")
            assert result.exit_code == 0

    def test_authenticate_without_credentials(self, runner, mock_wiz_variables):
        """Test authenticate command without providing credentials (uses env vars)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            mock_auth.return_value = "test_token"

            result = runner.invoke(wiz, ["authenticate"])

            # Verify wiz_authenticate was called with None values (will use env vars internally)
            mock_auth.assert_called_once_with(None, None)
            assert result.exit_code == 0

    # ========================================
    # Test issues command (lines 143-146)
    # ========================================

    @pytest.fixture
    def mock_wiz_issue(self):
        """Mock the WizIssue scanner."""
        with patch("regscale.integrations.commercial.wizv2.issue.WizIssue") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance

    @pytest.fixture
    def mock_wiz_auth(self):
        """Mock wiz_authenticate."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock:
            yield mock

    @pytest.fixture
    def mock_check_license(self):
        """Mock check_license."""
        with patch("regscale.core.app.utils.app_utils.check_license") as mock:
            yield mock

    def test_issues_with_none_client_secret(
        self,
        runner,
        mock_wiz_variables,
        mock_wiz_issue,
        mock_wiz_auth,
        mock_check_license,
    ):
        """Test issues command when client_secret is None (line 143-144)."""
        result = runner.invoke(
            wiz,
            [
                "issues",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                # Not providing client_secret, so it will be None and use env var
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that wiz_authenticate was called with env credentials
        mock_wiz_auth.assert_called_once_with("env_client_id", "env_client_secret")

    def test_issues_with_none_client_id(
        self,
        runner,
        mock_wiz_variables,
        mock_wiz_issue,
        mock_wiz_auth,
        mock_check_license,
    ):
        """Test issues command when client_id is None (line 145-146)."""
        result = runner.invoke(
            wiz,
            [
                "issues",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--client_secret",
                "provided_secret",
                # Not providing client_id, so it will be None and use env var
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that wiz_authenticate was called with env client_id
        mock_wiz_auth.assert_called_once_with("env_client_id", "provided_secret")

    # ========================================
    # Test attach_sbom command (lines 194-206)
    # ========================================

    def test_attach_sbom_with_none_client_secret(self, runner, mock_wiz_variables):
        """Test attach_sbom command when client_secret is None (lines 197-198)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_sbom_report") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "attach_sbom",
                        "--regscale_ssp_id",
                        "2288",
                        "--report_id",
                        "test-report-id",
                        # Not providing client_secret
                    ],
                )

                # Verify wiz_authenticate was called with env secret
                mock_auth.assert_called_once_with(
                    client_id="env_client_id",
                    client_secret="env_client_secret",
                )
                assert result.exit_code == 0 or "report" in result.output.lower()

    def test_attach_sbom_with_none_client_id(self, runner, mock_wiz_variables):
        """Test attach_sbom command when client_id is None (lines 199-200)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_sbom_report") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "attach_sbom",
                        "--regscale_ssp_id",
                        "2288",
                        "--report_id",
                        "test-report-id",
                        "--client_secret",
                        "provided_secret",
                        # Not providing client_id
                    ],
                )

                # Verify wiz_authenticate was called with env client_id
                mock_auth.assert_called_once_with(
                    client_id="env_client_id",
                    client_secret="provided_secret",
                )
                assert result.exit_code == 0 or "report" in result.output.lower()

    def test_attach_sbom_full_flow(self, runner, mock_wiz_variables):
        """Test attach_sbom command full flow (lines 202-212)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_sbom_report") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "attach_sbom",
                        "--client_id",
                        "test_client",
                        "--client_secret",
                        "test_secret",
                        "--regscale_ssp_id",
                        "2288",
                        "--report_id",
                        "test-report-id",
                        "--standard",
                        "SPDX",
                    ],
                )

                # Verify fetch_sbom_report was called with correct parameters
                mock_fetch.assert_called_once_with(
                    "test-report-id",
                    parent_id=2288,  # parent_id is an integer from click
                    report_file_name="sbom_report",
                    report_file_extension="zip",
                    standard="SPDX",
                )
                assert result.exit_code == 0

    # ========================================
    # Test vulnerabilities command (lines 261-264)
    # ========================================

    @pytest.fixture
    def mock_scanner(self):
        """Mock the WizVulnerabilityIntegration scanner."""
        with patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance

    def test_vulnerabilities_with_none_client_secret(self, runner, mock_wiz_variables, mock_scanner):
        """Test vulnerabilities command when client_secret is None (lines 261-262)."""
        result = runner.invoke(
            wiz,
            [
                "vulnerabilities",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                # Not providing client_secret
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that sync_findings was called with env credentials
        mock_scanner.sync_findings.assert_called_once()
        call_kwargs = mock_scanner.sync_findings.call_args[1]
        assert call_kwargs["client_secret"] == "env_client_secret"

    def test_vulnerabilities_with_none_client_id(self, runner, mock_wiz_variables, mock_scanner):
        """Test vulnerabilities command when client_id is None (lines 263-264)."""
        result = runner.invoke(
            wiz,
            [
                "vulnerabilities",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--client_secret",
                "provided_secret",
                # Not providing client_id
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that sync_findings was called with env client_id
        mock_scanner.sync_findings.assert_called_once()
        call_kwargs = mock_scanner.sync_findings.call_args[1]
        assert call_kwargs["client_id"] == "env_client_id"

    # ========================================
    # Test add_report_evidence command (lines 310-322)
    # ========================================

    def test_add_report_evidence_with_none_client_secret(self, runner, mock_wiz_variables):
        """Test add_report_evidence command when client_secret is None (lines 313-314)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_report_by_id") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "add_report_evidence",
                        "--evidence_id",
                        "123",
                        "--report_id",
                        "test-report-id",
                        # Not providing client_secret
                    ],
                )

                # Verify wiz_authenticate was called with env secret
                mock_auth.assert_called_once_with(
                    client_id="env_client_id",
                    client_secret="env_client_secret",
                )
                assert result.exit_code == 0 or "report" in result.output.lower()

    def test_add_report_evidence_with_none_client_id(self, runner, mock_wiz_variables):
        """Test add_report_evidence command when client_id is None (lines 315-316)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_report_by_id") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "add_report_evidence",
                        "--evidence_id",
                        "123",
                        "--report_id",
                        "test-report-id",
                        "--client_secret",
                        "provided_secret",
                        # Not providing client_id
                    ],
                )

                # Verify wiz_authenticate was called with env client_id
                mock_auth.assert_called_once_with(
                    client_id="env_client_id",
                    client_secret="provided_secret",
                )
                assert result.exit_code == 0 or "report" in result.output.lower()

    def test_add_report_evidence_full_flow(self, runner, mock_wiz_variables):
        """Test add_report_evidence command full flow (lines 318-327)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_report_by_id") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "add_report_evidence",
                        "--client_id",
                        "test_client",
                        "--client_secret",
                        "test_secret",
                        "--evidence_id",
                        "456",
                        "--report_id",
                        "report-789",
                        "--report_file_name",
                        "custom_report",
                        "--report_file_extension",
                        "xlsx",
                    ],
                )

                # Verify fetch_report_by_id was called with correct parameters
                mock_fetch.assert_called_once_with(
                    "report-789",
                    parent_id=456,
                    report_file_name="custom_report",
                    report_file_extension="xlsx",
                )
                assert result.exit_code == 0

    # ========================================
    # Test sync_compliance command (lines 433-468)
    # ========================================

    def test_sync_compliance_list_frameworks_flag(self, runner, mock_wiz_variables):
        """Test sync_compliance command with --list-frameworks flag (lines 437-440)."""
        result = runner.invoke(
            wiz,
            [
                "sync_compliance",
                "--wiz_project_id",
                "test-project",
                "--regscale_id",
                "123",
                "--list-frameworks",
            ],
        )

        # Should output deprecation message and list-frameworks not supported message
        assert "sync_compliance is deprecated" in result.output
        assert "list-frameworks is no longer supported" in result.output
        assert result.exit_code == 0

    def test_sync_compliance_with_none_or_empty_client_secret(self, runner, mock_wiz_variables):
        """Test sync_compliance when client_secret is None or empty (lines 443-444)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "sync_compliance",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "123",
                    # Not providing client_secret
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_secret"] == "env_client_secret"
            assert result.exit_code == 0

    def test_sync_compliance_with_empty_string_client_secret(self, runner, mock_wiz_variables):
        """Test sync_compliance when client_secret is empty string (lines 443-444)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "sync_compliance",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "123",
                    "--client_secret",
                    "",  # Empty string
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_secret"] == "env_client_secret"
            assert result.exit_code == 0

    def test_sync_compliance_with_none_or_empty_client_id(self, runner, mock_wiz_variables):
        """Test sync_compliance when client_id is None or empty (lines 445-446)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "sync_compliance",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "123",
                    # Not providing client_id
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_id"] == "env_client_id"
            assert result.exit_code == 0

    def test_sync_compliance_full_flow(self, runner, mock_wiz_variables):
        """Test sync_compliance command full flow (lines 449-468)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "sync_compliance",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "456",
                    "--client_id",
                    "test_client",
                    "--client_secret",
                    "test_secret",
                    "--framework_id",
                    "wf-id-5",
                    "--create-issues",
                    "--update-control-status",
                    "--create-poams",
                    "--refresh",
                    "--cache-duration",
                    "720",
                ],
            )

            # Verify processor was created with correct parameters
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["plan_id"] == 456
            assert call_kwargs["wiz_project_id"] == "test-project"
            assert call_kwargs["client_id"] == "test_client"
            assert call_kwargs["client_secret"] == "test_secret"
            assert call_kwargs["create_poams"] is True
            assert call_kwargs["create_issues"] is True
            assert call_kwargs["update_control_status"] is True
            assert call_kwargs["force_fresh_report"] is True
            assert call_kwargs["reuse_existing_reports"] is False
            assert call_kwargs["bypass_control_filtering"] is True

            # Verify process_compliance_sync was called
            mock_instance.process_compliance_sync.assert_called_once()
            assert result.exit_code == 0

    # ========================================
    # Test compliance_report command (lines 568-594)
    # ========================================

    def test_compliance_report_with_empty_client_secret(self, runner, mock_wiz_variables):
        """Test compliance_report when client_secret is empty (lines 571-572)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "789",
                    "--client_secret",
                    "",  # Empty string
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_secret"] == "env_client_secret"
            assert result.exit_code == 0

    def test_compliance_report_with_none_client_secret(self, runner, mock_wiz_variables):
        """Test compliance_report when client_secret is None (lines 571-572)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "789",
                    # Not providing client_secret
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_secret"] == "env_client_secret"
            assert result.exit_code == 0

    def test_compliance_report_with_empty_client_id(self, runner, mock_wiz_variables):
        """Test compliance_report when client_id is empty (lines 573-574)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "789",
                    "--client_id",
                    "",  # Empty string
                ],
            )

            # Verify processor was created with env credentials
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["client_id"] == "env_client_id"
            assert result.exit_code == 0

    def test_compliance_report_full_flow(self, runner, mock_wiz_variables):
        """Test compliance_report command full flow (lines 578-594)."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project-2",
                    "--regscale_id",
                    "999",
                    "--client_id",
                    "custom_client",
                    "--client_secret",
                    "custom_secret",
                    "--report_file_path",
                    "/path/to/report.csv",
                    "--create-issues",
                    "--update-control-status",
                    "--create-poams",
                    "--no-reuse-existing-reports",
                    "--force-fresh-report",
                ],
            )

            # Verify processor was created with correct parameters
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["plan_id"] == 999
            assert call_kwargs["wiz_project_id"] == "test-project-2"
            assert call_kwargs["client_id"] == "custom_client"
            assert call_kwargs["client_secret"] == "custom_secret"
            assert call_kwargs["report_file_path"] == "/path/to/report.csv"
            assert call_kwargs["create_poams"] is True
            assert call_kwargs["create_issues"] is True
            assert call_kwargs["update_control_status"] is True
            assert call_kwargs["bypass_control_filtering"] is True
            assert call_kwargs["reuse_existing_reports"] is False
            assert call_kwargs["force_fresh_report"] is True

            # Verify process_compliance_sync was called
            mock_instance.process_compliance_sync.assert_called_once()
            assert result.exit_code == 0

    def test_compliance_report_with_defaults(self, runner, mock_wiz_variables):
        """Test compliance_report command with default values."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project-defaults",
                    "--regscale_id",
                    "111",
                ],
            )

            # Verify processor was created with default values
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["create_issues"] is True  # Default
            assert call_kwargs["update_control_status"] is True  # Default
            assert call_kwargs["create_poams"] is False  # Default
            assert call_kwargs["reuse_existing_reports"] is True  # Default
            assert call_kwargs["force_fresh_report"] is False  # Default
            assert call_kwargs["report_file_path"] is None  # Default

            # Verify process_compliance_sync was called
            mock_instance.process_compliance_sync.assert_called_once()
            assert result.exit_code == 0

    # ========================================
    # Edge cases and error handling
    # ========================================

    def test_inventory_with_filter_override(self, runner, mock_wiz_variables, mock_scanner):
        """Test inventory command with filter_by_override parameter."""
        result = runner.invoke(
            wiz,
            [
                "inventory",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--filter_by_override",
                '{"projectId": ["test-123"]}',
            ],
        )

        # Verify sync_assets was called with the filter
        mock_scanner.sync_assets.assert_called_once()
        call_kwargs = mock_scanner.sync_assets.call_args[1]
        assert call_kwargs["filter_by_override"] == '{"projectId": ["test-123"]}'
        assert result.exit_code == 0

    def test_issues_with_filter_override(
        self,
        runner,
        mock_wiz_variables,
        mock_wiz_issue,
        mock_wiz_auth,
        mock_check_license,
    ):
        """Test issues command with filter_by_override parameter."""
        result = runner.invoke(
            wiz,
            [
                "issues",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--filter_by_override",
                '{"severity": ["CRITICAL"]}',
            ],
        )

        # Verify sync_findings was called
        mock_wiz_issue.sync_findings.assert_called_once()
        assert result.exit_code == 0

    def test_vulnerabilities_with_filter_override(self, runner, mock_wiz_variables, mock_scanner):
        """Test vulnerabilities command with filter_by_override parameter."""
        result = runner.invoke(
            wiz,
            [
                "vulnerabilities",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--filter_by_override",
                '{"type": ["CRITICAL"]}',
            ],
        )

        # Verify sync_findings was called with the filter
        mock_scanner.sync_findings.assert_called_once()
        call_kwargs = mock_scanner.sync_findings.call_args[1]
        assert call_kwargs["filter_by_override"] == '{"type": ["CRITICAL"]}'
        assert result.exit_code == 0

    def test_attach_sbom_with_default_standard(self, runner, mock_wiz_variables):
        """Test attach_sbom command with default standard (CycloneDX)."""
        with patch("regscale.integrations.commercial.wizv2.core.auth.wiz_authenticate") as mock_auth:
            with patch("regscale.integrations.commercial.wizv2.utils.fetch_sbom_report") as mock_fetch:
                mock_auth.return_value = "test_token"
                mock_fetch.return_value = None

                result = runner.invoke(
                    wiz,
                    [
                        "attach_sbom",
                        "--regscale_ssp_id",
                        "2288",
                        "--report_id",
                        "test-report-id",
                        # Not providing --standard, should default to CycloneDX
                    ],
                )

                # Verify fetch_sbom_report was called with default standard
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args[1]
                assert call_args["standard"] == "CycloneDX"
                assert result.exit_code == 0

    def test_sync_compliance_no_create_issues(self, runner, mock_wiz_variables):
        """Test sync_compliance with --no-create-issues flag."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "sync_compliance",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "123",
                    "--no-create-issues",
                ],
            )

            # Verify processor was created with create_issues=False
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["create_issues"] is False
            assert result.exit_code == 0

    def test_compliance_report_no_update_control_status(self, runner, mock_wiz_variables):
        """Test compliance_report with --no-update-control-status flag."""
        with patch(
            "regscale.integrations.commercial.wizv2.compliance_report.WizComplianceReportProcessor"
        ) as mock_processor:
            mock_instance = MagicMock()
            mock_processor.return_value = mock_instance

            result = runner.invoke(
                wiz,
                [
                    "compliance_report",
                    "--wiz_project_id",
                    "test-project",
                    "--regscale_id",
                    "789",
                    "--no-update-control-status",
                ],
            )

            # Verify processor was created with update_control_status=False
            mock_processor.assert_called_once()
            call_kwargs = mock_processor.call_args[1]
            assert call_kwargs["update_control_status"] is False
            assert result.exit_code == 0
