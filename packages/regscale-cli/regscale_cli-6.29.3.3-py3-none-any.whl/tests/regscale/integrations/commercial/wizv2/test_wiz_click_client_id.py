#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Wiz Click command client_id parameter handling."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from regscale.integrations.commercial.wizv2.click import wiz


class TestWizClientIdHandling:
    """Test that client_id parameters are properly recognized when passed via CLI."""

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

    @pytest.fixture
    def mock_scanner(self):
        """Mock the WizVulnerabilityIntegration scanner."""
        with patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration") as mock:
            instance = MagicMock()
            mock.return_value = instance
            yield instance

    def test_inventory_cli_client_id_overrides_env(self, runner, mock_wiz_variables, mock_scanner):
        """Test that CLI-provided client_id overrides environment variable."""
        result = runner.invoke(
            wiz,
            [
                "inventory",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--client_id",
                "cli_provided_client_id",
                "--client_secret",
                "cli_provided_secret",
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that sync_assets was called with CLI-provided credentials
        mock_scanner.sync_assets.assert_called_once()
        call_kwargs = mock_scanner.sync_assets.call_args[1]
        assert call_kwargs["client_id"] == "cli_provided_client_id"
        assert call_kwargs["client_secret"] == "cli_provided_secret"

    def test_inventory_uses_env_when_no_cli_args(self, runner, mock_wiz_variables, mock_scanner):
        """Test that environment variables are used when CLI args not provided."""
        result = runner.invoke(
            wiz,
            [
                "inventory",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that sync_assets was called with environment credentials
        mock_scanner.sync_assets.assert_called_once()
        call_kwargs = mock_scanner.sync_assets.call_args[1]
        assert call_kwargs["client_id"] == "env_client_id"
        assert call_kwargs["client_secret"] == "env_client_secret"

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

    def test_issues_cli_client_id_overrides_env(
        self,
        runner,
        mock_wiz_variables,
        mock_wiz_issue,
        mock_wiz_auth,
        mock_check_license,
    ):
        """Test that CLI-provided client_id overrides environment variable for issues command."""
        result = runner.invoke(
            wiz,
            [
                "issues",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--client_id",
                "cli_client_id",
                "--client_secret",
                "cli_secret",
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that wiz_authenticate was called with CLI credentials
        mock_wiz_auth.assert_called_once_with("cli_client_id", "cli_secret")

        # Verify that sync_findings was called with CLI credentials
        mock_wiz_issue.sync_findings.assert_called_once()
        call_kwargs = mock_wiz_issue.sync_findings.call_args[1]
        assert call_kwargs["client_id"] == "cli_client_id"
        assert call_kwargs["client_secret"] == "cli_secret"

    def test_vulnerabilities_cli_client_id_overrides_env(self, runner, mock_wiz_variables, mock_scanner):
        """Test that CLI-provided client_id overrides environment variable for vulnerabilities command."""
        result = runner.invoke(
            wiz,
            [
                "vulnerabilities",
                "--wiz_project_id",
                "test-project",
                "--regscale_ssp_id",
                "2288",
                "--client_id",
                "cli_vuln_client_id",
                "--client_secret",
                "cli_vuln_secret",
            ],
        )

        # Check that the command ran
        assert result.exit_code == 0 or "successfully" in result.output.lower()

        # Verify that sync_findings was called with CLI-provided credentials
        mock_scanner.sync_findings.assert_called_once()
        call_kwargs = mock_scanner.sync_findings.call_args[1]
        assert call_kwargs["client_id"] == "cli_vuln_client_id"
        assert call_kwargs["client_secret"] == "cli_vuln_secret"
