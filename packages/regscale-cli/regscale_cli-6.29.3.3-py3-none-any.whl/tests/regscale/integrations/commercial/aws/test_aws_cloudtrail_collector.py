"""Unit tests for AWS CloudTrail collector."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.cloudtrail import (
    CloudTrailCollector,
    CloudTrailEventsCollector,
)


class TestCloudTrailCollector(unittest.TestCase):
    """Test cases for CloudTrailCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.region = "us-east-1"
        self.account_id = "123456789012"
        self.collector = CloudTrailCollector(self.mock_session, self.region, self.account_id)

    def test_init(self):
        """Test CloudTrailCollector initialization."""
        assert self.collector.session == self.mock_session
        assert self.collector.region == self.region
        assert self.collector.account_id == self.account_id

    def test_init_without_account_id(self):
        """Test CloudTrailCollector initialization without account ID."""
        collector = CloudTrailCollector(self.mock_session, self.region)
        assert collector.account_id is None

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_success(self, mock_logger):
        """Test successful collection of CloudTrail trails."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Mock trail data
        trail_arn = f"arn:aws:cloudtrail:{self.region}:{self.account_id}:trail/test-trail"
        mock_client.list_trails.return_value = {"Trails": [{"TrailARN": trail_arn, "Name": "test-trail"}]}

        mock_client.describe_trails.return_value = {
            "trailList": [
                {
                    "Name": "test-trail",
                    "TrailARN": trail_arn,
                    "S3BucketName": "test-bucket",
                    "IsMultiRegionTrail": True,
                    "IsOrganizationTrail": False,
                }
            ]
        }

        mock_client.get_trail_status.return_value = {
            "IsLogging": True,
            "LatestDeliveryTime": datetime(2024, 1, 1),
            "ResponseMetadata": {"RequestId": "test"},
        }

        mock_client.get_event_selectors.return_value = {
            "EventSelectors": [{"ReadWriteType": "All", "IncludeManagementEvents": True}]
        }

        # Execute
        result = self.collector.collect()

        # Verify
        assert "Trails" in result
        assert "TrailStatuses" in result
        assert len(result["Trails"]) == 1
        assert result["Trails"][0]["Name"] == "test-trail"
        assert result["Trails"][0]["Region"] == self.region
        assert "Status" in result["Trails"][0]
        assert "EventSelectors" in result["Trails"][0]
        assert result["Trails"][0]["Status"]["IsLogging"] is True

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_filters_by_account_id(self, mock_logger):
        """Test that collection filters trails by account ID."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Mock trails from different accounts
        trail_arn_match = f"arn:aws:cloudtrail:{self.region}:{self.account_id}:trail/test-trail-1"
        trail_arn_no_match = f"arn:aws:cloudtrail:{self.region}:999999999999:trail/test-trail-2"

        mock_client.list_trails.return_value = {
            "Trails": [
                {"TrailARN": trail_arn_match, "Name": "test-trail-1"},
                {"TrailARN": trail_arn_no_match, "Name": "test-trail-2"},
            ]
        }

        mock_client.describe_trails.return_value = {
            "trailList": [{"Name": "test-trail-1", "TrailARN": trail_arn_match}]
        }

        mock_client.get_trail_status.return_value = {"IsLogging": True}
        mock_client.get_event_selectors.return_value = {"EventSelectors": []}

        # Execute
        result = self.collector.collect()

        # Verify - should only have one trail (the matching account)
        assert len(result["Trails"]) == 1
        assert result["Trails"][0]["Name"] == "test-trail-1"
        mock_logger.debug.assert_called()

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_no_account_filter(self, mock_logger):
        """Test collection without account ID filter."""
        # Create collector without account ID
        collector = CloudTrailCollector(self.mock_session, self.region)

        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        trail_arn_1 = f"arn:aws:cloudtrail:{self.region}:111111111111:trail/trail-1"
        trail_arn_2 = f"arn:aws:cloudtrail:{self.region}:222222222222:trail/trail-2"

        mock_client.list_trails.return_value = {
            "Trails": [{"TrailARN": trail_arn_1, "Name": "trail-1"}, {"TrailARN": trail_arn_2, "Name": "trail-2"}]
        }

        mock_client.describe_trails.side_effect = [
            {"trailList": [{"Name": "trail-1", "TrailARN": trail_arn_1}]},
            {"trailList": [{"Name": "trail-2", "TrailARN": trail_arn_2}]},
        ]

        mock_client.get_trail_status.return_value = {"IsLogging": True}
        mock_client.get_event_selectors.return_value = {"EventSelectors": []}

        # Execute
        result = collector.collect()

        # Verify - should have both trails
        assert len(result["Trails"]) == 2

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_handles_access_denied(self, mock_logger):
        """Test collection handles AccessDeniedException."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate AccessDeniedException
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_trails.side_effect = ClientError(error_response, "list_trails")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Trails"] == []
        mock_logger.warning.assert_called()

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_handles_unexpected_error(self, mock_logger):
        """Test collection handles unexpected errors."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate unexpected error
        mock_client.list_trails.side_effect = Exception("Unexpected error")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Trails"] == []
        mock_logger.error.assert_called()

    def test_list_trails_success(self):
        """Test successful listing of trails."""
        mock_client = MagicMock()
        mock_client.list_trails.return_value = {"Trails": [{"TrailARN": "arn:test", "Name": "test"}]}

        result = self.collector._list_trails(mock_client)

        assert len(result) == 1
        assert result[0]["Name"] == "test"

    def test_list_trails_access_denied(self):
        """Test listing trails with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.list_trails.side_effect = ClientError(error_response, "list_trails")

        result = self.collector._list_trails(mock_client)

        assert result == []

    def test_describe_trail_success(self):
        """Test successful trail description."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.describe_trails.return_value = {"trailList": [{"Name": "test", "TrailARN": trail_arn}]}

        result = self.collector._describe_trail(mock_client, trail_arn)

        assert result is not None
        assert result["Name"] == "test"

    def test_describe_trail_not_found(self):
        """Test trail description when trail not found."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/nonexistent"
        error_response = {"Error": {"Code": "TrailNotFoundException", "Message": "Trail not found"}}
        mock_client.describe_trails.side_effect = ClientError(error_response, "describe_trails")

        result = self.collector._describe_trail(mock_client, trail_arn)

        assert result is None

    def test_describe_trail_empty_response(self):
        """Test trail description with empty response."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.describe_trails.return_value = {"trailList": []}

        result = self.collector._describe_trail(mock_client, trail_arn)

        assert result is None

    def test_get_trail_status_success(self):
        """Test successful retrieval of trail status."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.get_trail_status.return_value = {
            "IsLogging": True,
            "LatestDeliveryTime": datetime(2024, 1, 1),
            "ResponseMetadata": {"RequestId": "test"},
        }

        result = self.collector._get_trail_status(mock_client, trail_arn)

        assert "IsLogging" in result
        assert result["IsLogging"] is True
        assert "ResponseMetadata" not in result  # Should be removed

    def test_get_trail_status_error(self):
        """Test trail status retrieval with error."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.get_trail_status.side_effect = ClientError(
            {"Error": {"Code": "TrailNotFoundException", "Message": "Trail not found"}}, "get_trail_status"
        )

        result = self.collector._get_trail_status(mock_client, trail_arn)

        assert result == {}

    def test_get_event_selectors_success(self):
        """Test successful retrieval of event selectors."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.get_event_selectors.return_value = {
            "EventSelectors": [{"ReadWriteType": "All", "IncludeManagementEvents": True}]
        }

        result = self.collector._get_event_selectors(mock_client, trail_arn)

        assert len(result) == 1
        assert result[0]["ReadWriteType"] == "All"

    def test_get_event_selectors_error(self):
        """Test event selectors retrieval with error."""
        mock_client = MagicMock()
        trail_arn = "arn:aws:cloudtrail:us-east-1:123456789012:trail/test"
        mock_client.get_event_selectors.side_effect = ClientError(
            {"Error": {"Code": "TrailNotFoundException", "Message": "Trail not found"}}, "get_event_selectors"
        )

        result = self.collector._get_event_selectors(mock_client, trail_arn)

        assert result == []

    def test_matches_account_id_with_matching_arn(self):
        """Test account ID matching with matching ARN."""
        trail_arn = f"arn:aws:cloudtrail:{self.region}:{self.account_id}:trail/test"
        assert self.collector._matches_account_id(trail_arn) is True

    def test_matches_account_id_with_non_matching_arn(self):
        """Test account ID matching with non-matching ARN."""
        trail_arn = f"arn:aws:cloudtrail:{self.region}:999999999999:trail/test"
        assert self.collector._matches_account_id(trail_arn) is False

    def test_matches_account_id_with_invalid_arn(self):
        """Test account ID matching with invalid ARN."""
        trail_arn = "invalid-arn"
        assert self.collector._matches_account_id(trail_arn) is False

    def test_matches_account_id_without_filter(self):
        """Test account ID matching without account filter."""
        collector = CloudTrailCollector(self.mock_session, self.region)
        trail_arn = f"arn:aws:cloudtrail:{self.region}:999999999999:trail/test"
        assert collector._matches_account_id(trail_arn) is True


class TestCloudTrailEventsCollector(unittest.TestCase):
    """Test cases for CloudTrailEventsCollector."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.region = "us-east-1"
        self.collector = CloudTrailEventsCollector(self.mock_session, self.region)

    def test_init_default_params(self):
        """Test CloudTrailEventsCollector initialization with defaults."""
        assert self.collector.session == self.mock_session
        assert self.collector.region == self.region
        assert self.collector.max_results == 50
        assert self.collector.lookup_attributes == []
        assert self.collector.start_time is None
        assert self.collector.end_time is None

    def test_init_custom_params(self):
        """Test CloudTrailEventsCollector initialization with custom params."""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 31)
        lookup_attributes = [{"AttributeKey": "EventName", "AttributeValue": "CreateBucket"}]

        collector = CloudTrailEventsCollector(
            self.mock_session,
            self.region,
            max_results=25,
            lookup_attributes=lookup_attributes,
            start_time=start_time,
            end_time=end_time,
        )

        assert collector.max_results == 25
        assert collector.lookup_attributes == lookup_attributes
        assert collector.start_time == start_time
        assert collector.end_time == end_time

    def test_init_enforces_max_results_limit(self):
        """Test that max_results is capped at 50."""
        collector = CloudTrailEventsCollector(self.mock_session, self.region, max_results=100)
        assert collector.max_results == 50

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_success(self, mock_logger):
        """Test successful collection of CloudTrail events."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Mock event data
        mock_events = [
            {
                "EventId": "event-1",
                "EventName": "CreateBucket",
                "EventTime": datetime(2024, 1, 1),
                "Username": "test-user",
            },
            {
                "EventId": "event-2",
                "EventName": "PutObject",
                "EventTime": datetime(2024, 1, 2),
                "Username": "test-user",
            },
        ]

        mock_client.lookup_events.return_value = {"Events": mock_events}

        # Execute
        result = self.collector.collect()

        # Verify
        assert "Events" in result
        assert "EventCount" in result
        assert result["EventCount"] == 2
        assert len(result["Events"]) == 2
        assert result["Events"][0]["EventName"] == "CreateBucket"

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_with_pagination(self, mock_logger):
        """Test collection with pagination."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Mock paginated responses
        mock_client.lookup_events.side_effect = [
            {"Events": [{"EventId": "event-1"}], "NextToken": "token-1"},
            {"Events": [{"EventId": "event-2"}], "NextToken": "token-2"},
            {"Events": [{"EventId": "event-3"}]},  # No NextToken
        ]

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["EventCount"] == 3
        assert len(result["Events"]) == 3
        assert mock_client.lookup_events.call_count == 3

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_with_lookup_attributes(self, mock_logger):
        """Test collection with lookup attributes."""
        lookup_attributes = [{"AttributeKey": "EventName", "AttributeValue": "CreateBucket"}]
        collector = CloudTrailEventsCollector(self.mock_session, self.region, lookup_attributes=lookup_attributes)

        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client
        mock_client.lookup_events.return_value = {"Events": [{"EventId": "event-1"}]}

        # Execute
        result = collector.collect()

        # Verify lookup_events was called with correct parameters
        call_args = mock_client.lookup_events.call_args[1]
        assert "LookupAttributes" in call_args
        assert call_args["LookupAttributes"] == lookup_attributes
        assert result["EventCount"] == 1

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_with_time_range(self, mock_logger):
        """Test collection with time range."""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 1, 31)
        collector = CloudTrailEventsCollector(self.mock_session, self.region, start_time=start_time, end_time=end_time)

        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client
        mock_client.lookup_events.return_value = {"Events": [{"EventId": "event-1"}]}

        # Execute
        result = collector.collect()

        # Verify lookup_events was called with correct parameters
        call_args = mock_client.lookup_events.call_args[1]
        assert "StartTime" in call_args
        assert "EndTime" in call_args
        assert call_args["StartTime"] == start_time
        assert call_args["EndTime"] == end_time
        assert result["EventCount"] == 1

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_handles_access_denied(self, mock_logger):
        """Test collection handles AccessDeniedException."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate AccessDeniedException
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.lookup_events.side_effect = ClientError(error_response, "lookup_events")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Events"] == []
        assert result["EventCount"] == 0
        mock_logger.warning.assert_called()

    @patch("regscale.integrations.commercial.aws.inventory.resources.cloudtrail.logger")
    def test_collect_handles_unexpected_error(self, mock_logger):
        """Test collection handles unexpected errors."""
        # Setup mock client
        mock_client = MagicMock()
        self.mock_session.client.return_value = mock_client

        # Simulate unexpected error
        mock_client.lookup_events.side_effect = Exception("Unexpected error")

        # Execute
        result = self.collector.collect()

        # Verify
        assert result["Events"] == []
        mock_logger.error.assert_called()

    def test_lookup_events_success(self):
        """Test successful event lookup."""
        mock_client = MagicMock()
        mock_client.lookup_events.return_value = {"Events": [{"EventId": "event-1"}, {"EventId": "event-2"}]}

        result = self.collector._lookup_events(mock_client)

        assert len(result) == 2
        assert result[0]["EventId"] == "event-1"

    def test_lookup_events_with_pagination(self):
        """Test event lookup with pagination."""
        mock_client = MagicMock()
        mock_client.lookup_events.side_effect = [
            {"Events": [{"EventId": "event-1"}], "NextToken": "token-1"},
            {"Events": [{"EventId": "event-2"}], "NextToken": "token-2"},
            {"Events": [{"EventId": "event-3"}]},
        ]

        result = self.collector._lookup_events(mock_client)

        assert len(result) == 3
        assert mock_client.lookup_events.call_count == 3

    def test_lookup_events_access_denied(self):
        """Test event lookup with access denied."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}
        mock_client.lookup_events.side_effect = ClientError(error_response, "lookup_events")

        result = self.collector._lookup_events(mock_client)

        assert result == []

    def test_lookup_events_other_error(self):
        """Test event lookup with other error."""
        mock_client = MagicMock()
        error_response = {"Error": {"Code": "InternalError", "Message": "Internal error"}}
        mock_client.lookup_events.side_effect = ClientError(error_response, "lookup_events")

        result = self.collector._lookup_events(mock_client)

        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
