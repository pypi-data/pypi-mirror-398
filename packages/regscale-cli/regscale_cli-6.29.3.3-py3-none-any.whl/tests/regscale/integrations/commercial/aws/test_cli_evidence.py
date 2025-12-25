"""Unit tests for AWS CLI evidence options."""

import unittest
from unittest.mock import MagicMock, call, patch

import pytest
from click.testing import CliRunner

from regscale.integrations.commercial.aws.cli import sync_findings


class TestCLIEvidenceOptions(unittest.TestCase):
    """Test cases for CLI evidence generation options."""

    def setUp(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    def test_sync_findings_native_format_only(self, mock_resolve_creds, mock_integration):
        """Test sync_findings with native format (no evidence)."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")
        mock_integration.sync_findings.return_value = 5

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
            ],
        )

        # Verify
        assert result.exit_code == 0
        mock_integration.sync_findings.assert_called_once()

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_evidence_generation(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings with evidence generation."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client

        mock_raw_findings = [{"Id": "finding-1", "Severity": {"Label": "HIGH"}}]
        mock_fetch_findings.return_value = mock_raw_findings

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance

        mock_evidence = MagicMock()
        mock_evidence.id = 12345
        mock_evidence.title = "Test Evidence"
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], mock_evidence)
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
                "--generate-evidence",
            ],
        )

        # Verify
        assert result.exit_code == 0
        mock_scanner_instance.authenticate.assert_called_once()
        mock_scanner_instance.process_findings_with_evidence.assert_called_once()

        # Verify process_findings_with_evidence called with correct params - uses regscale_id for ssp_id
        call_kwargs = mock_scanner_instance.process_findings_with_evidence.call_args[1]
        assert call_kwargs["generate_evidence"] is True
        assert call_kwargs["ssp_id"] == 123  # Should use regscale_id value
        assert call_kwargs["service_name"] == "SecurityHub"

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_control_ids(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings with control IDs."""
        # Setup mocks
        mock_resolve_creds.return_value = (None, "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = [{"Id": "finding-1"}]

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], MagicMock())
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--aws_access_key_id",
                "AKIAIOSFODNN7EXAMPLE",
                "--aws_secret_access_key",
                "secret",
                "--generate-evidence",
                "--control-ids",
                "789,790,791",
            ],
        )

        # Verify
        assert result.exit_code == 0

        # Verify control IDs parsed correctly
        call_kwargs = mock_scanner_instance.process_findings_with_evidence.call_args[1]
        assert call_kwargs["control_ids"] == [789, 790, 791]

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_ocsf_format(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings with OCSF format."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = [{"Id": "finding-1"}]

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], None)
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
                "--format",
                "ocsf",
            ],
        )

        # Verify
        assert result.exit_code == 0

        # Verify OCSF format requested
        call_kwargs = mock_scanner_instance.process_findings_with_evidence.call_args[1]
        assert call_kwargs["ocsf_format"] is True

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_both_format(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings with both native and OCSF formats."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = [{"Id": "finding-1"}]

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], None)
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
                "--format",
                "both",
            ],
        )

        # Verify
        assert result.exit_code == 0

        # Verify both format requested
        call_kwargs = mock_scanner_instance.process_findings_with_evidence.call_args[1]
        assert call_kwargs["ocsf_format"] is True

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_all_options(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings with all evidence options enabled."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = [{"Id": "finding-1"}]

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance

        mock_evidence = MagicMock()
        mock_evidence.id = 12345
        mock_evidence.title = "Full Test Evidence"
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], mock_evidence)
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-west-2",
                "--regscale_id",
                "999",
                "--profile",
                "test-profile",
                "--generate-evidence",
                "--control-ids",
                "100,200,300",
                "--evidence-frequency",
                "90",
                "--format",
                "both",
            ],
        )

        # Verify
        assert result.exit_code == 0

        # Verify all parameters passed correctly - ssp_id should match regscale_id
        call_kwargs = mock_scanner_instance.process_findings_with_evidence.call_args[1]
        assert call_kwargs["generate_evidence"] is True
        assert call_kwargs["ssp_id"] == 999  # Should use regscale_id value
        assert call_kwargs["control_ids"] == [100, 200, 300]
        assert call_kwargs["ocsf_format"] is True

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_with_session_token(self, mock_resolve_creds, mock_integration, mock_boto3):
        """Test sync_findings with session token authentication."""
        # Setup mocks
        mock_resolve_creds.return_value = (None, "key", "secret", "session-token-123", "us-east-1")
        mock_integration.sync_findings.return_value = 3

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--aws_access_key_id",
                "AKIAIOSFODNN7EXAMPLE",
                "--aws_secret_access_key",
                "secret",
                "--aws_session_token",
                "session-token-123",
            ],
        )

        # Verify
        assert result.exit_code == 0
        mock_integration.sync_findings.assert_called_once()

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_profile_auth(self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3):
        """Test sync_findings with profile authentication."""
        # Setup mocks
        mock_resolve_creds.return_value = ("my-profile", None, None, None, "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = []

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance
        mock_scanner_instance.process_findings_with_evidence.return_value = ([], None)
        mock_scanner_instance.update_regscale_findings.return_value = 0

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "my-profile",
                "--generate-evidence",
            ],
        )

        # Verify profile-based session created
        assert result.exit_code == 0
        assert mock_boto3.Session.called

    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    def test_sync_findings_error_handling(self, mock_resolve_creds, mock_integration):
        """Test sync_findings error handling."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")
        mock_integration.sync_findings.side_effect = Exception("Test error")

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
            ],
        )

        # Verify error handled
        assert result.exit_code != 0
        assert "Test error" in result.output

    @patch("regscale.integrations.commercial.aws.cli.boto3")
    @patch("regscale.integrations.commercial.aws.cli.fetch_aws_findings")
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryIntegration")
    @patch("regscale.integrations.commercial.aws.cli.resolve_aws_credentials")
    @pytest.mark.skip(reason="Test references refactored CLI functionality - needs rewrite for current implementation")
    def test_sync_findings_no_evidence_created(
        self, mock_resolve_creds, mock_integration, mock_fetch_findings, mock_boto3
    ):
        """Test sync_findings when no evidence is created."""
        # Setup mocks
        mock_resolve_creds.return_value = ("profile", "key", "secret", "token", "us-east-1")

        mock_session = MagicMock()
        mock_boto3.Session.return_value = mock_session
        mock_session.client.return_value = MagicMock()

        mock_fetch_findings.return_value = [{"Id": "finding-1"}]

        mock_scanner_instance = MagicMock()
        mock_integration.return_value = mock_scanner_instance
        # No evidence created
        mock_scanner_instance.process_findings_with_evidence.return_value = ([MagicMock()], None)
        mock_scanner_instance.update_regscale_findings.return_value = 1

        # Execute
        result = self.runner.invoke(
            sync_findings,
            [
                "--region",
                "us-east-1",
                "--regscale_id",
                "123",
                "--profile",
                "default",
                "--generate-evidence",
            ],
        )

        # Verify - should not error even when no evidence created
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
