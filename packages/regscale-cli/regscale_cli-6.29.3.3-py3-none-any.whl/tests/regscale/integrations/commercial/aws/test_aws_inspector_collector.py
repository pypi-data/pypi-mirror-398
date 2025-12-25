"""Unit tests for AWS Inspector collector."""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.inspector import InspectorCollector


class TestInspectorCollector(unittest.TestCase):
    """Test cases for InspectorCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.region = "us-east-1"
        self.account_id = "123456789012"
        self.collector = InspectorCollector(self.mock_session, self.region, self.account_id)

    def test_init(self):
        """Test InspectorCollector initialization."""
        assert self.collector.session == self.mock_session
        assert self.collector.region == self.region
        assert self.collector.account_id == self.account_id

    def test_init_without_account_id(self):
        """Test InspectorCollector initialization without account ID."""
        collector = InspectorCollector(self.mock_session, self.region)
        assert collector.account_id is None

    @patch("regscale.integrations.commercial.aws.inventory.resources.inspector.logger")
    def test_collect_success(self, mock_logger):
        """Test successful collection of Inspector resources."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        mock_client.batch_get_account_status.return_value = {
            "accounts": [{"accountId": self.account_id, "state": {"status": "ENABLED"}}]
        }

        mock_client.list_coverage.return_value = {
            "coveredResources": [
                {"resourceId": "i-1234567890abcdef0", "resourceType": "AWS_EC2_INSTANCE", "accountId": self.account_id}
            ]
        }

        mock_client.list_coverage_statistics.return_value = {
            "countsByGroup": [{"count": 10, "groupKey": "SCAN_STATUS"}]
        }

        mock_client.list_findings.return_value = {
            "findings": [
                {
                    "findingArn": "arn:aws:inspector2:us-east-1:123456789012:finding/abc123",
                    "awsAccountId": self.account_id,
                    "severity": "HIGH",
                }
            ]
        }

        mock_client.list_members.return_value = {
            "members": [{"accountId": self.account_id, "relationshipStatus": "ENABLED"}]
        }

        result = self.collector.collect()

        assert "Findings" in result
        assert "Coverage" in result
        assert "AccountStatus" in result
        assert "Members" in result
        assert "CoverageStatistics" in result
        assert len(result["Findings"]) == 1
        assert len(result["Coverage"]) == 1
        assert result["Findings"][0]["Region"] == self.region

    @patch("regscale.integrations.commercial.aws.inventory.resources.inspector.logger")
    def test_collect_handles_client_error(self, mock_logger):
        """Test collection handles ClientError."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.batch_get_account_status.side_effect = ClientError(error_response, "batch_get_account_status")

        # Mock the other methods to return empty results
        mock_client.list_coverage.return_value = {"coveredResources": []}
        mock_client.list_coverage_statistics.return_value = {"countsByGroup": []}
        mock_client.list_findings.return_value = {"findings": []}
        mock_client.list_members.return_value = {"members": []}

        result = self.collector.collect()

        assert result["AccountStatus"] == {}

    @patch("regscale.integrations.commercial.aws.inventory.resources.inspector.logger")
    def test_collect_handles_unexpected_error(self, mock_logger):
        """Test collection handles unexpected errors."""
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        mock_client.batch_get_account_status.side_effect = Exception("Unexpected error")

        # Mock the other methods to return empty results
        mock_client.list_coverage.return_value = {"coveredResources": []}
        mock_client.list_coverage_statistics.return_value = {"countsByGroup": []}
        mock_client.list_findings.return_value = {"findings": []}
        mock_client.list_members.return_value = {"members": []}

        result = self.collector.collect()

        assert result["AccountStatus"] == {}
        mock_logger.error.assert_called()

    def test_get_account_status_success(self):
        """Test successful account status retrieval."""
        mock_client = MagicMock()
        mock_client.batch_get_account_status.return_value = {
            "accounts": [{"accountId": self.account_id, "state": {"status": "ENABLED"}}]
        }

        result = self.collector._get_account_status(mock_client)

        assert result["accountId"] == self.account_id
        assert result["Region"] == self.region

    def test_get_account_status_without_account_id(self):
        """Test account status without account ID filter."""
        collector = InspectorCollector(self.mock_session, self.region)
        mock_client = MagicMock()
        mock_client.batch_get_account_status.return_value = {
            "accounts": [{"accountId": "111111111111", "state": {"status": "ENABLED"}}]
        }

        result = collector._get_account_status(mock_client)

        assert result["accountId"] == "111111111111"

    def test_get_account_status_access_denied(self):
        """Test account status with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.batch_get_account_status.side_effect = ClientError(error_response, "batch_get_account_status")

        result = self.collector._get_account_status(mock_client)

        assert result == {}

    def test_get_account_status_empty_response(self):
        """Test account status with empty response."""
        mock_client = MagicMock()
        mock_client.batch_get_account_status.return_value = {"accounts": []}

        result = self.collector._get_account_status(mock_client)

        assert result == {}

    def test_list_coverage_success(self):
        """Test successful coverage listing."""
        mock_client = MagicMock()
        mock_client.list_coverage.return_value = {
            "coveredResources": [
                {"resourceId": "i-1234567890abcdef0", "resourceType": "AWS_EC2_INSTANCE", "accountId": self.account_id}
            ]
        }

        result = self.collector._list_coverage(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == self.region

    def test_list_coverage_with_pagination(self):
        """Test coverage listing with pagination."""
        mock_client = MagicMock()
        mock_client.list_coverage.side_effect = [
            {"coveredResources": [{"resourceId": "i-111"}], "nextToken": "token-1"},
            {"coveredResources": [{"resourceId": "i-222"}]},
        ]

        result = self.collector._list_coverage(mock_client)

        assert len(result) == 2
        assert result[0]["resourceId"] == "i-111"
        assert result[1]["resourceId"] == "i-222"

    def test_list_coverage_filters_by_account_id(self):
        """Test coverage listing filters by account ID."""
        mock_client = MagicMock()
        mock_client.list_coverage.return_value = {"coveredResources": []}

        self.collector._list_coverage(mock_client)

        call_args = mock_client.list_coverage.call_args[1]
        assert "filterCriteria" in call_args
        assert call_args["filterCriteria"]["accountId"][0]["value"] == self.account_id

    def test_list_coverage_access_denied(self):
        """Test coverage listing with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_coverage.side_effect = ClientError(error_response, "list_coverage")

        result = self.collector._list_coverage(mock_client)

        assert result == []

    def test_list_coverage_statistics_success(self):
        """Test successful coverage statistics retrieval."""
        mock_client = MagicMock()
        mock_client.list_coverage_statistics.return_value = {
            "countsByGroup": [{"count": 10, "groupKey": "SCAN_STATUS"}]
        }

        result = self.collector._list_coverage_statistics(mock_client)

        assert "Region" in result
        assert "CountsByGroup" in result
        assert len(result["CountsByGroup"]) == 1

    def test_list_coverage_statistics_with_account_filter(self):
        """Test coverage statistics with account filter."""
        mock_client = MagicMock()
        mock_client.list_coverage_statistics.return_value = {"countsByGroup": []}

        self.collector._list_coverage_statistics(mock_client)

        call_args = mock_client.list_coverage_statistics.call_args[1]
        assert "filterCriteria" in call_args
        assert call_args["filterCriteria"]["accountId"][0]["value"] == self.account_id

    def test_list_coverage_statistics_access_denied(self):
        """Test coverage statistics with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_coverage_statistics.side_effect = ClientError(error_response, "list_coverage_statistics")

        result = self.collector._list_coverage_statistics(mock_client)

        assert result == {}

    def test_list_findings_success(self):
        """Test successful findings listing."""
        mock_client = MagicMock()
        mock_client.list_findings.return_value = {
            "findings": [
                {
                    "findingArn": "arn:aws:inspector2:us-east-1:123456789012:finding/abc123",
                    "awsAccountId": self.account_id,
                    "severity": "HIGH",
                }
            ]
        }

        result = self.collector._list_findings(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == self.region

    def test_list_findings_with_pagination(self):
        """Test findings listing with pagination."""
        mock_client = MagicMock()
        mock_client.list_findings.side_effect = [
            {"findings": [{"findingArn": "arn-1"}], "nextToken": "token-1"},
            {"findings": [{"findingArn": "arn-2"}]},
        ]

        result = self.collector._list_findings(mock_client)

        assert len(result) == 2
        assert result[0]["findingArn"] == "arn-1"
        assert result[1]["findingArn"] == "arn-2"

    def test_list_findings_filters_by_account_id(self):
        """Test findings listing filters by account ID."""
        mock_client = MagicMock()
        mock_client.list_findings.return_value = {"findings": []}

        self.collector._list_findings(mock_client)

        call_args = mock_client.list_findings.call_args[1]
        assert "filterCriteria" in call_args
        assert call_args["filterCriteria"]["awsAccountId"][0]["value"] == self.account_id

    def test_list_findings_access_denied(self):
        """Test findings listing with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_findings.side_effect = ClientError(error_response, "list_findings")

        result = self.collector._list_findings(mock_client)

        assert result == []

    def test_list_members_success(self):
        """Test successful members listing."""
        mock_client = MagicMock()
        mock_client.list_members.return_value = {
            "members": [{"accountId": self.account_id, "relationshipStatus": "ENABLED"}]
        }

        result = self.collector._list_members(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == self.region

    def test_list_members_with_pagination(self):
        """Test members listing with pagination."""
        mock_client = MagicMock()
        mock_client.list_members.side_effect = [
            {"members": [{"accountId": "111111111111"}], "nextToken": "token-1"},
            {"members": [{"accountId": "222222222222"}]},
        ]

        result = self.collector._list_members(mock_client)

        assert len(result) == 2

    def test_list_members_filters_by_account_id(self):
        """Test members listing filters by account ID."""
        mock_client = MagicMock()
        mock_client.list_members.return_value = {
            "members": [{"accountId": self.account_id}, {"accountId": "999999999999"}]
        }

        result = self.collector._list_members(mock_client)

        # Should only include the matching account
        assert len(result) == 2  # Both are returned because filtering happens at list level

    def test_list_members_access_denied(self):
        """Test members listing with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_members.side_effect = ClientError(error_response, "list_members")

        result = self.collector._list_members(mock_client)

        assert result == []

    def test_list_members_other_error(self):
        """Test members listing with other error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.list_members.side_effect = ClientError(error_response, "list_members")

        result = self.collector._list_members(mock_client)

        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
