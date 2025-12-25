"""Unit tests for AWS GuardDuty collector."""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.guardduty import GuardDutyCollector


class TestGuardDutyCollector(unittest.TestCase):
    """Test cases for GuardDutyCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.region = "us-east-1"
        self.account_id = "123456789012"
        self.collector = GuardDutyCollector(self.mock_session, self.region, self.account_id)

    def test_init(self):
        """Test GuardDutyCollector initialization."""
        assert self.collector.session == self.mock_session
        assert self.collector.region == self.region
        assert self.collector.account_id == self.account_id

    def test_init_without_account_id(self):
        """Test GuardDutyCollector initialization without account ID."""
        collector = GuardDutyCollector(self.mock_session, self.region)
        assert collector.account_id is None

    @patch("regscale.integrations.commercial.aws.inventory.resources.guardduty.logger")
    def test_collect_success(self, mock_logger):
        """Test successful collection of GuardDuty resources."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        detector_id = "test-detector-123"
        mock_client.list_detectors.return_value = {"DetectorIds": [detector_id]}

        mock_client.get_detector.return_value = {
            "Status": "ENABLED",
            "ServiceRole": "arn:aws:iam::123456789012:role/service-role",
            "AccountId": self.account_id,
            "ResponseMetadata": {"RequestId": "test"},
        }

        mock_client.list_findings.return_value = {"FindingIds": ["finding-1", "finding-2"]}

        mock_client.get_findings.return_value = {
            "Findings": [
                {
                    "Id": "finding-1",
                    "Type": "UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom",
                    "Severity": 8.0,
                    "AccountId": self.account_id,
                },
                {"Id": "finding-2", "Type": "Recon:EC2/PortProbeUnprotectedPort", "Severity": 5.0},
            ]
        }

        mock_client.list_members.return_value = {"Members": []}

        # Execute
        result = self.collector.collect()

        # Verify
        assert "Detectors" in result
        assert "Findings" in result
        assert "Members" in result
        assert len(result["Detectors"]) == 1
        assert len(result["Findings"]) == 2
        assert result["Detectors"][0]["DetectorId"] == detector_id
        assert result["Detectors"][0]["Region"] == self.region
        assert "ResponseMetadata" not in result["Detectors"][0]

    @patch("regscale.integrations.commercial.aws.inventory.resources.guardduty.logger")
    def test_collect_filters_by_account_id(self, mock_logger):
        """Test that collection filters detectors by account ID."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        mock_client.list_detectors.return_value = {"DetectorIds": ["detector-1", "detector-2"]}

        # Return different account IDs for each detector
        mock_client.get_detector.side_effect = [
            {"Status": "ENABLED", "AccountId": self.account_id, "ServiceRole": "arn"},
            {"Status": "ENABLED", "AccountId": "999999999999", "ServiceRole": "arn"},
        ]

        mock_client.list_findings.return_value = {"FindingIds": []}
        mock_client.list_members.return_value = {"Members": []}

        # Execute
        result = self.collector.collect()

        # Verify - should only have one detector (the matching account)
        assert len(result["Detectors"]) == 1
        assert result["Detectors"][0]["AccountId"] == self.account_id

    @patch("regscale.integrations.commercial.aws.inventory.resources.guardduty.logger")
    def test_collect_no_account_filter(self, mock_logger):
        """Test collection without account ID filter."""
        # Create collector without account ID
        collector = GuardDutyCollector(self.mock_session, self.region)

        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        mock_client.list_detectors.return_value = {"DetectorIds": ["detector-1", "detector-2"]}

        mock_client.get_detector.side_effect = [
            {"Status": "ENABLED", "AccountId": "111111111111"},
            {"Status": "ENABLED", "AccountId": "222222222222"},
        ]

        mock_client.list_findings.return_value = {"FindingIds": []}
        mock_client.list_members.return_value = {"Members": []}

        # Execute
        result = collector.collect()

        # Verify - should have both detectors
        assert len(result["Detectors"]) == 2

    @patch("regscale.integrations.commercial.aws.inventory.resources.guardduty.logger")
    def test_collect_handles_client_error(self, mock_logger):
        """Test collection handles ClientError."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate ClientError
        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.list_detectors.side_effect = ClientError(error_response, "list_detectors")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Detectors"] == []

    @patch("regscale.integrations.commercial.aws.inventory.resources.guardduty.logger")
    def test_collect_handles_unexpected_error(self, mock_logger):
        """Test collection handles unexpected errors."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate unexpected error
        mock_client.list_detectors.side_effect = Exception("Unexpected error")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Detectors"] == []
        mock_logger.error.assert_called()

    def test_list_detectors_success(self):
        """Test successful listing of detectors."""
        mock_client = MagicMock()
        mock_client.list_detectors.return_value = {"DetectorIds": ["detector-1", "detector-2"]}

        result = self.collector._list_detectors(mock_client)

        assert len(result) == 2
        assert "detector-1" in result

    def test_list_detectors_access_denied(self):
        """Test listing detectors with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_detectors.side_effect = ClientError(error_response, "list_detectors")

        result = self.collector._list_detectors(mock_client)

        assert result == []

    def test_get_detector_success(self):
        """Test successful detector retrieval."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        mock_client.get_detector.return_value = {
            "Status": "ENABLED",
            "ServiceRole": "arn:aws:iam::123456789012:role/service-role",
            "ResponseMetadata": {"RequestId": "test"},
        }

        result = self.collector._get_detector(mock_client, detector_id)

        assert result is not None
        assert result["Status"] == "ENABLED"
        assert "ResponseMetadata" not in result

    def test_get_detector_error(self):
        """Test detector retrieval with error."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        error_response = {"Error": {"Code": "BadRequestException", "Message": "Bad request"}}
        mock_client.get_detector.side_effect = ClientError(error_response, "get_detector")

        result = self.collector._get_detector(mock_client, detector_id)

        assert result is None

    def test_list_and_get_findings_success(self):
        """Test successful findings retrieval."""
        mock_client = MagicMock()
        detector_id = "test-detector"

        mock_client.list_findings.return_value = {"FindingIds": ["finding-1", "finding-2"]}
        mock_client.get_findings.return_value = {
            "Findings": [{"Id": "finding-1", "Severity": 8.0}, {"Id": "finding-2", "Severity": 5.0}]
        }

        result = self.collector._list_and_get_findings(mock_client, detector_id)

        assert len(result) == 2
        assert result[0]["Region"] == self.region
        assert result[0]["DetectorId"] == detector_id

    def test_list_and_get_findings_no_findings(self):
        """Test findings retrieval with no findings."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        mock_client.list_findings.return_value = {"FindingIds": []}

        result = self.collector._list_and_get_findings(mock_client, detector_id)

        assert result == []
        mock_client.get_findings.assert_not_called()

    def test_list_and_get_findings_access_denied(self):
        """Test findings retrieval with access denied."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_findings.side_effect = ClientError(error_response, "list_findings")

        result = self.collector._list_and_get_findings(mock_client, detector_id)

        assert result == []

    def test_list_and_get_findings_with_max_limit(self):
        """Test findings retrieval respects max_findings parameter."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        max_findings = 10

        mock_client.list_findings.return_value = {"FindingIds": ["finding-1"]}
        mock_client.get_findings.return_value = {"Findings": [{"Id": "finding-1"}]}

        self.collector._list_and_get_findings(mock_client, detector_id, max_findings=max_findings)

        # Verify MaxResults was passed
        call_args = mock_client.list_findings.call_args[1]
        assert call_args["MaxResults"] == max_findings

    def test_list_members_success(self):
        """Test successful members listing."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        mock_client.list_members.return_value = {
            "Members": [{"AccountId": "111111111111", "Email": "test@example.com"}]
        }

        result = self.collector._list_members(mock_client, detector_id)

        assert len(result) == 1
        assert result[0]["Region"] == self.region
        assert result[0]["DetectorId"] == detector_id

    def test_list_members_access_denied(self):
        """Test members listing with access denied."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_members.side_effect = ClientError(error_response, "list_members")

        result = self.collector._list_members(mock_client, detector_id)

        assert result == []

    def test_list_members_other_error(self):
        """Test members listing with other error."""
        mock_client = MagicMock()
        detector_id = "test-detector"
        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.list_members.side_effect = ClientError(error_response, "list_members")

        result = self.collector._list_members(mock_client, detector_id)

        assert result == []

    def test_matches_account_id_with_matching_id(self):
        """Test account ID matching with matching ID."""
        assert self.collector._matches_account_id(self.account_id) is True

    def test_matches_account_id_with_non_matching_id(self):
        """Test account ID matching with non-matching ID."""
        assert self.collector._matches_account_id("999999999999") is False

    def test_matches_account_id_without_filter(self):
        """Test account ID matching without account filter."""
        collector = GuardDutyCollector(self.mock_session, self.region)
        assert collector._matches_account_id("999999999999") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
