"""Unit tests for AWS Evidence Generator."""

import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

from regscale.integrations.commercial.aws.evidence_generator import AWSEvidenceGenerator


class TestAWSEvidenceGenerator(unittest.TestCase):
    """Test cases for AWSEvidenceGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_api = MagicMock()
        self.ssp_id = 456
        self.generator = AWSEvidenceGenerator(api=self.mock_api, ssp_id=self.ssp_id)

    def test_init(self):
        """Test AWSEvidenceGenerator initialization."""
        assert self.generator.api == self.mock_api
        assert self.generator.ssp_id == self.ssp_id

    def test_init_without_ssp_id(self):
        """Test AWSEvidenceGenerator initialization without SSP ID."""
        generator = AWSEvidenceGenerator(api=self.mock_api)
        assert generator.api == self.mock_api
        assert generator.ssp_id is None

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    @patch("regscale.integrations.commercial.aws.evidence_generator.Evidence")
    @patch("regscale.integrations.commercial.aws.evidence_generator.File")
    @patch("regscale.integrations.commercial.aws.evidence_generator.datetime")
    def test_create_evidence_from_scan_success(self, mock_datetime, mock_file, mock_evidence, mock_evidence_mapping):
        """Test successful evidence creation from scan."""
        # Setup mocks
        mock_now = datetime(2025, 10, 13, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        findings = [
            {
                "Severity": {"Label": "HIGH"},
                "Title": "Test Finding 1",
            },
            {
                "Severity": {"Label": "MEDIUM"},
                "Title": "Test Finding 2",
            },
        ]

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.id = 12345
        mock_evidence_instance.title = "SecurityHub Findings Scan - 2025-10-13"
        mock_evidence.return_value = mock_evidence_instance
        mock_evidence_instance.create.return_value = mock_evidence_instance

        mock_file.upload_file_to_regscale.return_value = True

        # Mock EvidenceMapping
        mock_mapping_instance = MagicMock()
        mock_evidence_mapping.return_value = mock_mapping_instance

        # Execute
        result = self.generator.create_evidence_from_scan(
            service_name="SecurityHub",
            findings=findings,
            ocsf_data=None,
            update_frequency=30,
            control_ids=None,
        )

        # Verify evidence created
        assert result == mock_evidence_instance
        mock_evidence_instance.create.assert_called_once()

        # Verify file uploads called
        assert mock_file.upload_file_to_regscale.call_count == 1

        # Verify SSP linking called (since self.ssp_id = 456 in setUp)
        mock_evidence_mapping.assert_called_once()

    @patch("regscale.integrations.commercial.aws.evidence_generator.logger")
    def test_create_evidence_from_scan_no_findings(self, mock_logger):
        """Test evidence creation with no findings."""
        result = self.generator.create_evidence_from_scan(
            service_name="SecurityHub",
            findings=[],
            ocsf_data=None,
        )

        assert result is None
        mock_logger.warning.assert_called_once()

    @patch("regscale.integrations.commercial.aws.evidence_generator.Evidence")
    @patch("regscale.integrations.commercial.aws.evidence_generator.datetime")
    def test_create_evidence_from_scan_creation_failure(self, mock_datetime, mock_evidence):
        """Test evidence creation failure."""
        mock_now = datetime(2025, 10, 13, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        findings = [{"Severity": {"Label": "HIGH"}}]

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.create.return_value = None
        mock_evidence.return_value = mock_evidence_instance

        result = self.generator.create_evidence_from_scan(
            service_name="SecurityHub",
            findings=findings,
        )

        assert result is None

    @patch("regscale.integrations.commercial.aws.evidence_generator.Evidence")
    @patch("regscale.integrations.commercial.aws.evidence_generator.datetime")
    def test_create_evidence_from_scan_exception(self, mock_datetime, mock_evidence):
        """Test evidence creation with exception."""
        mock_now = datetime(2025, 10, 13, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        findings = [{"Severity": {"Label": "HIGH"}}]

        mock_evidence.side_effect = Exception("Test error")

        result = self.generator.create_evidence_from_scan(
            service_name="SecurityHub",
            findings=findings,
        )

        assert result is None

    def test_count_severities_guardduty(self):
        """Test severity counting for GuardDuty findings."""
        findings = [
            {"Severity": 8.0},  # HIGH
            {"Severity": 7.5},  # HIGH
            {"Severity": 5.0},  # MEDIUM
            {"Severity": 4.0},  # MEDIUM
            {"Severity": 2.0},  # LOW
        ]

        result = self.generator._count_severities(findings, "GuardDuty")

        assert result["HIGH"] == 2
        assert result["MEDIUM"] == 2
        assert result["LOW"] == 1
        assert result["CRITICAL"] == 0

    def test_count_severities_securityhub(self):
        """Test severity counting for Security Hub findings."""
        findings = [
            {"Severity": {"Label": "CRITICAL"}},
            {"Severity": {"Label": "HIGH"}},
            {"Severity": {"Label": "MEDIUM"}},
            {"Severity": {"Label": "LOW"}},
            {"Severity": {"Label": "INFORMATIONAL"}},
        ]

        result = self.generator._count_severities(findings, "SecurityHub")

        assert result["CRITICAL"] == 1
        assert result["HIGH"] == 1
        assert result["MEDIUM"] == 1
        assert result["LOW"] == 1
        assert result["INFO"] == 0

    def test_count_severities_cloudtrail(self):
        """Test severity counting for CloudTrail events."""
        findings = [
            {"EventName": "DescribeInstances"},
            {"EventName": "CreateBucket"},
        ]

        result = self.generator._count_severities(findings, "CloudTrail")

        assert result["INFO"] == 2
        assert result["HIGH"] == 0

    def test_build_evidence_description(self):
        """Test building evidence description."""
        severity_counts = {
            "CRITICAL": 2,
            "HIGH": 5,
            "MEDIUM": 10,
            "LOW": 3,
            "INFO": 0,
        }

        result = self.generator._build_evidence_description(
            service_name="SecurityHub",
            total_findings=20,
            severity_counts=severity_counts,
            ocsf_data=None,
        )

        assert "SecurityHub" in result
        assert "Total findings: 20" in result
        assert "CRITICAL: 2" in result
        assert "HIGH: 5" in result
        assert "MEDIUM: 10" in result
        assert "LOW: 3" in result
        assert "INFO: 0" not in result  # Should not show zero counts
        assert "securityhub_findings_native.jsonl" in result
        assert "securityhub_findings_ocsf.jsonl" not in result

    def test_build_evidence_description_with_ocsf(self):
        """Test building evidence description with OCSF data."""
        severity_counts = {"HIGH": 5}
        ocsf_data = [{"class_uid": 2004}]

        result = self.generator._build_evidence_description(
            service_name="SecurityHub",
            total_findings=5,
            severity_counts=severity_counts,
            ocsf_data=ocsf_data,
        )

        assert "securityhub_findings_ocsf.jsonl" in result

    @patch("regscale.integrations.commercial.aws.evidence_generator.File")
    def test_attach_findings_files_native_only(self, mock_file):
        """Test attaching findings files (native only)."""
        findings = [
            {"Id": "finding-1", "Title": "Test 1"},
            {"Id": "finding-2", "Title": "Test 2"},
        ]

        mock_file.upload_file_to_regscale.return_value = True

        self.generator._attach_findings_files(
            evidence_id=123,
            findings=findings,
            ocsf_data=None,
            service_name="SecurityHub",
        )

        # Verify native file uploaded
        assert mock_file.upload_file_to_regscale.call_count == 1
        call_args = mock_file.upload_file_to_regscale.call_args
        assert call_args[1]["parent_id"] == 123
        assert call_args[1]["parent_module"] == "evidence"
        assert "securityhub_findings_native.jsonl" in call_args[1]["file_name"]
        assert "aws,securityhub,native" in call_args[1]["tags"]

    @patch("regscale.integrations.commercial.aws.evidence_generator.File")
    def test_attach_findings_files_with_ocsf(self, mock_file):
        """Test attaching findings files with OCSF."""
        findings = [{"Id": "finding-1"}]
        ocsf_data = [{"class_uid": 2004}]

        mock_file.upload_file_to_regscale.return_value = True

        self.generator._attach_findings_files(
            evidence_id=123,
            findings=findings,
            ocsf_data=ocsf_data,
            service_name="SecurityHub",
        )

        # Verify both files uploaded
        assert mock_file.upload_file_to_regscale.call_count == 2

    @patch("regscale.integrations.commercial.aws.evidence_generator.File")
    @patch("regscale.integrations.commercial.aws.evidence_generator.logger")
    def test_attach_findings_files_upload_failure(self, mock_logger, mock_file):
        """Test file attachment with upload failure."""
        findings = [{"Id": "finding-1"}]
        mock_file.upload_file_to_regscale.return_value = False

        self.generator._attach_findings_files(
            evidence_id=123,
            findings=findings,
            ocsf_data=None,
            service_name="SecurityHub",
        )

        # Verify warning logged
        assert mock_logger.warning.called

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    def test_link_to_ssp_success(self, mock_mapping):
        """Test linking evidence to SSP."""
        mock_mapping_instance = MagicMock()
        mock_mapping.return_value = mock_mapping_instance

        self.generator._link_to_ssp(evidence_id=123)

        # Verify mapping created
        mock_mapping.assert_called_once_with(
            evidenceID=123,
            mappedID=self.ssp_id,
            mappingType="securityplans",
        )
        mock_mapping_instance.create.assert_called_once()

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    @patch("regscale.integrations.commercial.aws.evidence_generator.logger")
    def test_link_to_ssp_failure(self, mock_logger, mock_mapping):
        """Test linking evidence to SSP with failure."""
        mock_mapping_instance = MagicMock()
        mock_mapping_instance.create.side_effect = Exception("Test error")
        mock_mapping.return_value = mock_mapping_instance

        self.generator._link_to_ssp(evidence_id=123)

        # Verify warning logged
        mock_logger.warning.assert_called_once()

    def test_link_to_ssp_no_ssp_id(self):
        """Test linking to SSP when no SSP ID configured."""
        generator = AWSEvidenceGenerator(api=self.mock_api)
        # Should not raise exception
        generator._link_to_ssp(evidence_id=123)

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    def test_link_to_controls_success(self, mock_mapping):
        """Test linking evidence to controls."""
        control_ids = [789, 790, 791]
        mock_mapping_instance = MagicMock()
        mock_mapping.return_value = mock_mapping_instance

        self.generator._link_to_controls(evidence_id=123, control_ids=control_ids)

        # Verify all mappings created
        assert mock_mapping.call_count == 3
        assert mock_mapping_instance.create.call_count == 3

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    @patch("regscale.integrations.commercial.aws.evidence_generator.logger")
    def test_link_to_controls_partial_failure(self, mock_logger, mock_mapping):
        """Test linking to controls with partial failure."""
        control_ids = [789, 790]
        mock_mapping_instance = MagicMock()
        mock_mapping_instance.create.side_effect = [None, Exception("Test error")]
        mock_mapping.return_value = mock_mapping_instance

        self.generator._link_to_controls(evidence_id=123, control_ids=control_ids)

        # Verify warning logged for failure
        mock_logger.warning.assert_called_once()
        assert mock_mapping.call_count == 2

    @patch("regscale.integrations.commercial.aws.evidence_generator.EvidenceMapping")
    @patch("regscale.integrations.commercial.aws.evidence_generator.Evidence")
    @patch("regscale.integrations.commercial.aws.evidence_generator.File")
    @patch("regscale.integrations.commercial.aws.evidence_generator.datetime")
    def test_create_evidence_with_all_options(self, mock_datetime, mock_file, mock_evidence, mock_evidence_mapping):
        """Test evidence creation with all options enabled."""
        mock_now = datetime(2025, 10, 13, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        findings = [{"Severity": {"Label": "HIGH"}}]
        ocsf_data = [{"class_uid": 2004}]
        control_ids = [789, 790]

        mock_evidence_instance = MagicMock()
        mock_evidence_instance.id = 12345
        mock_evidence.return_value = mock_evidence_instance
        mock_evidence_instance.create.return_value = mock_evidence_instance

        mock_file.upload_file_to_regscale.return_value = True

        # Mock EvidenceMapping
        mock_mapping_instance = MagicMock()
        mock_evidence_mapping.return_value = mock_mapping_instance

        result = self.generator.create_evidence_from_scan(
            service_name="SecurityHub",
            findings=findings,
            ocsf_data=ocsf_data,
            update_frequency=90,
            control_ids=control_ids,
        )

        assert result is not None
        # Verify both file uploads called
        assert mock_file.upload_file_to_regscale.call_count == 2
        # Verify SSP and control mappings called
        assert mock_evidence_mapping.call_count == 3  # 1 SSP + 2 controls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
