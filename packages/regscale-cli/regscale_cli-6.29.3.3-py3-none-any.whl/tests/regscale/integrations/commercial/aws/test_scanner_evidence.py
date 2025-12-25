"""Unit tests for AWS Scanner evidence integration."""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.commercial.aws.scanner import AWSInventoryIntegration


class TestScannerEvidenceIntegration(unittest.TestCase):
    """Test cases for scanner evidence integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.plan_id = 123
        self.scanner = AWSInventoryIntegration(plan_id=self.plan_id)

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_with_evidence_native_only(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings with native format only."""
        findings = [
            {
                "Id": "finding-1",
                "Title": "Test Finding 1",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Type": "AwsEc2Instance", "Id": "i-123"}],
            }
        ]

        # Mock parse_finding to return IntegrationFinding objects
        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=False,
                ssp_id=None,
                control_ids=None,
                ocsf_format=False,
            )

            # Verify
            assert len(result_findings) == 1
            assert result_evidence is None
            mock_parse.assert_called_once_with(findings[0])
            mock_mapper.assert_not_called()
            mock_evidence_gen.assert_not_called()

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_with_ocsf_only(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings with OCSF format."""
        findings = [
            {
                "Id": "finding-1",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Type": "AwsEc2Instance", "Id": "i-123"}],
            }
        ]

        # Setup mocks
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.securityhub_to_ocsf.return_value = {"class_uid": 2001}

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=False,
                ocsf_format=True,
            )

            # Verify OCSF mapper called
            mock_mapper_instance.securityhub_to_ocsf.assert_called_once_with(findings[0])
            assert result_evidence is None

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_with_evidence_generation(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings with evidence generation."""
        findings = [
            {
                "Id": "finding-1",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Type": "AwsEc2Instance", "Id": "i-123"}],
            }
        ]

        # Setup mocks
        mock_evidence_instance = MagicMock()
        mock_evidence_instance.id = 12345
        mock_evidence_instance.title = "Test Evidence"

        mock_gen_instance = MagicMock()
        mock_gen_instance.create_evidence_from_scan.return_value = mock_evidence_instance
        mock_evidence_gen.return_value = mock_gen_instance

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=True,
                ssp_id=456,
                control_ids=[789, 790],
                ocsf_format=False,
            )

            # Verify evidence generator called with Api instance
            mock_api.assert_called_once()
            mock_evidence_gen.assert_called_once_with(api=mock_api.return_value, ssp_id=456)
            mock_gen_instance.create_evidence_from_scan.assert_called_once_with(
                service_name="SecurityHub",
                findings=findings,
                ocsf_data=None,
                control_ids=[789, 790],
            )
            assert result_evidence == mock_evidence_instance

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_guardduty_with_ocsf(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing GuardDuty findings with OCSF."""
        findings = [
            {
                "Id": "guardduty-1",
                "Severity": 8.0,
                "Type": "UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom",
            }
        ]

        # Setup mocks
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.guardduty_to_ocsf.return_value = {"class_uid": 2004}

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="GuardDuty",
                ocsf_format=True,
            )

            # Verify GuardDuty mapper called
            mock_mapper_instance.guardduty_to_ocsf.assert_called_once_with(findings[0])

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_cloudtrail_with_ocsf(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing CloudTrail events with OCSF."""
        findings = [
            {
                "EventName": "DescribeInstances",
                "EventSource": "ec2.amazonaws.com",
            }
        ]

        # Setup mocks
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.cloudtrail_event_to_ocsf.return_value = {"class_uid": 3005}

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="CloudTrail",
                ocsf_format=True,
            )

            # Verify CloudTrail mapper called
            mock_mapper_instance.cloudtrail_event_to_ocsf.assert_called_once_with(findings[0])

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_with_both_formats(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings with both native and OCSF formats."""
        findings = [
            {
                "Id": "finding-1",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Type": "AwsEc2Instance", "Id": "i-123"}],
            }
        ]

        # Setup mocks
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.securityhub_to_ocsf.return_value = {"class_uid": 2001}

        mock_evidence_instance = MagicMock()
        mock_gen_instance = MagicMock()
        mock_gen_instance.create_evidence_from_scan.return_value = mock_evidence_instance
        mock_evidence_gen.return_value = mock_gen_instance

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=True,
                ssp_id=456,
                ocsf_format=True,
            )

            # Verify both OCSF mapper and evidence generator called
            mock_mapper_instance.securityhub_to_ocsf.assert_called_once()
            mock_gen_instance.create_evidence_from_scan.assert_called_once()

            # Verify OCSF data passed to evidence generator
            call_kwargs = mock_gen_instance.create_evidence_from_scan.call_args[1]
            assert call_kwargs["ocsf_data"] is not None
            assert len(call_kwargs["ocsf_data"]) == 1

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_multiple_findings(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing multiple findings."""
        findings = [
            {
                "Id": "finding-1",
                "Severity": {"Label": "HIGH"},
                "Resources": [{"Type": "AwsEc2Instance", "Id": "i-123"}],
            },
            {
                "Id": "finding-2",
                "Severity": {"Label": "MEDIUM"},
                "Resources": [{"Type": "AwsS3Bucket", "Id": "bucket-1"}],
            },
            {
                "Id": "finding-3",
                "Severity": {"Label": "LOW"},
                "Resources": [{"Type": "AwsIamRole", "Id": "role-1"}],
            },
        ]

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_integration_finding = MagicMock()
            # Each parse_finding returns a list with one finding
            mock_parse.return_value = [mock_integration_finding]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
            )

            # Verify all findings parsed
            assert mock_parse.call_count == 3
            assert len(result_findings) == 3

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_with_multi_resource_finding(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing finding with multiple resources (yields multiple IntegrationFindings)."""
        findings = [
            {
                "Id": "finding-1",
                "Severity": {"Label": "HIGH"},
                "Resources": [
                    {"Type": "AwsEc2Instance", "Id": "i-123"},
                    {"Type": "AwsEc2Instance", "Id": "i-456"},
                ],
            }
        ]

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            # parse_finding returns multiple IntegrationFindings for multi-resource finding
            mock_finding_1 = MagicMock()
            mock_finding_2 = MagicMock()
            mock_parse.return_value = [mock_finding_1, mock_finding_2]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
            )

            # Verify multiple IntegrationFindings returned
            assert len(result_findings) == 2

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_empty_list(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing empty findings list."""
        with patch.object(self.scanner, "parse_finding") as mock_parse:
            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=[],
                service_name="SecurityHub",
            )

            # Verify no findings processed
            assert len(result_findings) == 0
            assert result_evidence is None
            mock_parse.assert_not_called()

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_no_control_ids(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings without control IDs."""
        findings = [{"Id": "finding-1", "Severity": {"Label": "HIGH"}, "Resources": [{"Type": "AwsEc2Instance"}]}]

        mock_evidence_instance = MagicMock()
        mock_gen_instance = MagicMock()
        mock_gen_instance.create_evidence_from_scan.return_value = mock_evidence_instance
        mock_evidence_gen.return_value = mock_gen_instance

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_parse.return_value = [MagicMock()]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=True,
                control_ids=None,
            )

            # Verify control_ids passed as None
            call_kwargs = mock_gen_instance.create_evidence_from_scan.call_args[1]
            assert call_kwargs["control_ids"] is None

    @patch("regscale.core.app.api.Api")
    @patch("regscale.integrations.commercial.aws.ocsf.mapper.AWSOCSFMapper")
    @patch("regscale.integrations.commercial.aws.evidence_generator.AWSEvidenceGenerator")
    def test_process_findings_no_ssp_id(self, mock_evidence_gen, mock_mapper, mock_api):
        """Test processing findings without SSP ID."""
        findings = [{"Id": "finding-1", "Severity": {"Label": "HIGH"}, "Resources": [{"Type": "AwsEc2Instance"}]}]

        mock_gen_instance = MagicMock()
        mock_evidence_gen.return_value = mock_gen_instance

        with patch.object(self.scanner, "parse_finding") as mock_parse:
            mock_parse.return_value = [MagicMock()]

            result_findings, result_evidence = self.scanner.process_findings_with_evidence(
                findings=findings,
                service_name="SecurityHub",
                generate_evidence=True,
                ssp_id=None,
            )

            # Verify AWSEvidenceGenerator initialized with None SSP ID
            mock_api.assert_called_once()
            mock_evidence_gen.assert_called_once_with(api=mock_api.return_value, ssp_id=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
