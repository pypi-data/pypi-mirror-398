"""AWS CloudTrail resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class CloudTrailCollector(BaseCollector):
    """Collector for AWS CloudTrail resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize CloudTrail collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}

    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudTrail resources.

        :return: Dictionary containing CloudTrail trails and their status
        :rtype: Dict[str, Any]
        """
        result = {"Trails": [], "TrailStatuses": {}}

        try:
            client = self._get_client("cloudtrail")

            # List all trails
            trails = self._list_trails(client)

            # Get detailed information for each trail
            for trail in trails:
                trail_arn = trail.get("TrailARN", "")

                # Filter by account ID if specified
                if self.account_id and not self._matches_account_id(trail_arn):
                    logger.debug(f"Skipping trail {trail_arn} - does not match account ID {self.account_id}")
                    continue

                # Get detailed trail information
                trail_details = self._describe_trail(client, trail_arn)
                if trail_details:
                    # Get tags for filtering
                    trail_tags = self._get_trail_tags(client, trail_arn)

                    # Filter by tags if specified
                    if self.tags and not self._matches_tags(trail_tags):
                        logger.debug(f"Skipping trail {trail_arn} - does not match tag filters")
                        continue

                    trail_details["Tags"] = trail_tags
                    # Get trail status
                    trail_status = self._get_trail_status(client, trail_arn)
                    trail_details["Status"] = trail_status

                    # Get event selectors
                    event_selectors = self._get_event_selectors(client, trail_arn)
                    trail_details["EventSelectors"] = event_selectors

                    # Add region information
                    trail_details["Region"] = self.region

                    result["Trails"].append(trail_details)
                    result["TrailStatuses"][trail_arn] = trail_status

            logger.info(f"Collected {len(result['Trails'])} CloudTrail trail(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "CloudTrail trails")
        except Exception as e:
            logger.error(f"Unexpected error collecting CloudTrail trails: {e}", exc_info=True)

        return result

    def _list_trails(self, client: Any) -> List[Dict[str, Any]]:
        """
        List all CloudTrail trails.

        :param client: CloudTrail client
        :return: List of trail summaries
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.list_trails()
            return response.get("Trails", [])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list CloudTrail trails in {self.region}")
                return []
            raise

    def _describe_trail(self, client: Any, trail_arn: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: Trail details or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = client.describe_trails(trailNameList=[trail_arn])
            trails = response.get("trailList", [])
            return trails[0] if trails else None
        except ClientError as e:
            if e.response["Error"]["Code"] == "TrailNotFoundException":
                logger.warning(f"Trail not found: {trail_arn}")
                return None
            logger.error(f"Error describing trail {trail_arn}: {e}")
            return None

    def _get_trail_status(self, client: Any, trail_arn: str) -> Dict[str, Any]:
        """
        Get the status of a CloudTrail trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: Trail status information
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_trail_status(Name=trail_arn)
            # Remove ResponseMetadata from the result
            response.pop("ResponseMetadata", None)
            return response
        except ClientError as e:
            logger.error(f"Error getting status for trail {trail_arn}: {e}")
            return {}

    def _get_event_selectors(self, client: Any, trail_arn: str) -> List[Dict[str, Any]]:
        """
        Get event selectors for a trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: List of event selectors
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.get_event_selectors(TrailName=trail_arn)
            return response.get("EventSelectors", [])
        except ClientError as e:
            logger.error(f"Error getting event selectors for trail {trail_arn}: {e}")
            return []

    def _get_trail_tags(self, client: Any, trail_arn: str) -> Dict[str, str]:
        """
        Get tags for a CloudTrail trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: Dictionary of tags (TagKey -> TagValue)
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags(ResourceIdList=[trail_arn])
            resource_tag_list = response.get("ResourceTagList", [])
            if resource_tag_list:
                tags_list = resource_tag_list[0].get("TagsList", [])
                return {tag["Key"]: tag["Value"] for tag in tags_list}
            return {}
        except ClientError as e:
            logger.debug(f"Error getting tags for trail {trail_arn}: {e}")
            return {}

    def _matches_account_id(self, trail_arn: str) -> bool:
        """
        Check if trail ARN matches the specified account ID.

        :param str trail_arn: Trail ARN to check
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True

        # ARN format: arn:aws:cloudtrail:region:account-id:trail/trail-name
        try:
            arn_parts = trail_arn.split(":")
            if len(arn_parts) >= 5:
                trail_account_id = arn_parts[4]
                return trail_account_id == self.account_id
        except (IndexError, AttributeError):
            logger.warning(f"Could not parse account ID from trail ARN: {trail_arn}")

        return False

    def _matches_tags(self, resource_tags: Dict[str, str]) -> bool:
        """
        Check if resource tags match the specified filter tags.

        :param dict resource_tags: Tags on the resource
        :return: True if all filter tags match
        :rtype: bool
        """
        if not self.tags:
            return True

        # All filter tags must match
        for key, value in self.tags.items():
            if resource_tags.get(key) != value:
                return False

        return True


class CloudTrailEventsCollector(BaseCollector):
    """Collector for AWS CloudTrail events."""

    def __init__(
        self,
        session: Any,
        region: str,
        max_results: int = 50,
        lookup_attributes: Optional[List[Dict[str, str]]] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
    ):
        """
        Initialize CloudTrail events collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param int max_results: Maximum number of events to return (default 50, max 50)
        :param List[Dict[str, str]] lookup_attributes: Optional lookup attributes to filter events
        :param start_time: Optional start time for event lookup
        :param end_time: Optional end time for event lookup
        """
        super().__init__(session, region)
        self.max_results = min(max_results, 50)  # AWS maximum is 50
        self.lookup_attributes = lookup_attributes or []
        self.start_time = start_time
        self.end_time = end_time

    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudTrail events.

        :return: Dictionary containing CloudTrail events
        :rtype: Dict[str, Any]
        """
        result = {"Events": [], "EventCount": 0}

        try:
            client = self._get_client("cloudtrail")
            events = self._lookup_events(client)
            result["Events"] = events
            result["EventCount"] = len(events)

            logger.info(f"Collected {len(events)} CloudTrail event(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "CloudTrail events")
        except Exception as e:
            logger.error(f"Unexpected error collecting CloudTrail events: {e}", exc_info=True)

        return result

    def _lookup_events(self, client: Any) -> List[Dict[str, Any]]:
        """
        Lookup CloudTrail events with pagination support.

        :param client: CloudTrail client
        :return: List of events
        :rtype: List[Dict[str, Any]]
        """
        events = []
        next_token = None

        try:
            while True:
                # Build request parameters
                params = {"MaxResults": self.max_results}

                if self.lookup_attributes:
                    params["LookupAttributes"] = self.lookup_attributes

                if self.start_time:
                    params["StartTime"] = self.start_time

                if self.end_time:
                    params["EndTime"] = self.end_time

                if next_token:
                    params["NextToken"] = next_token

                response = client.lookup_events(**params)
                events.extend(response.get("Events", []))

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to lookup CloudTrail events in {self.region}")
            else:
                logger.error(f"Error looking up CloudTrail events: {e}")

        return events
