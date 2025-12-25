"""AWS Inspector v2 resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class InspectorCollector(BaseCollector):
    """Collector for AWS Inspector v2 resources."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        collect_findings: bool = True,
    ):
        """
        Initialize Inspector collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param Dict[str, str] tags: Optional tags to filter resources (all must match)
        :param bool collect_findings: Whether to collect Inspector findings. Default True.
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.collect_findings = collect_findings

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS Inspector v2 resources.

        :return: Dictionary containing Inspector findings and coverage information
        :rtype: Dict[str, Any]
        """
        result = {
            "Findings": [],
            "Coverage": [],
            "AccountStatus": {},
            "Members": [],
            "CoverageStatistics": {},
        }

        try:
            client = self._get_client("inspector2")

            # Get account status
            account_status = self._get_account_status(client)
            result["AccountStatus"] = account_status

            # Get coverage information
            coverage = self._list_coverage(client)
            result["Coverage"] = coverage

            # Get coverage statistics
            coverage_stats = self._list_coverage_statistics(client)
            result["CoverageStatistics"] = coverage_stats

            # Get findings only if requested
            if self.collect_findings:
                findings = self._list_findings(client)
                result["Findings"] = findings
            else:
                findings = []
                logger.debug("Skipping Inspector findings collection (collect_findings=False)")

            # Get member accounts
            members = self._list_members(client)
            result["Members"] = members

            if self.collect_findings:
                logger.info(
                    f"Collected {len(findings)} Inspector finding(s), "
                    f"{len(coverage)} covered resource(s) from {self.region}"
                )
            else:
                logger.info(f"Collected {len(coverage)} covered resource(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "AWS Inspector resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting AWS Inspector resources: {e}", exc_info=True)

        return result

    def _get_account_status(self, client: Any) -> Dict[str, Any]:
        """
        Get account status for Inspector.

        :param client: Inspector client
        :return: Account status information
        :rtype: Dict[str, Any]
        """
        try:
            if self.account_id:
                response = client.batch_get_account_status(accountIds=[self.account_id])
            else:
                # If no account ID specified, get current account status
                response = client.batch_get_account_status()

            accounts = response.get("accounts", [])
            if accounts:
                status = accounts[0]
                status["Region"] = self.region
                return status

            return {}
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to get Inspector account status in {self.region}")
            else:
                logger.error(f"Error getting Inspector account status: {e}")
            return {}

    def _list_coverage(self, client: Any, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List resources covered by Inspector with tag filtering.

        :param client: Inspector client
        :param int max_results: Maximum number of results to retrieve
        :return: List of covered resources
        :rtype: List[Dict[str, Any]]
        """
        coverage = []
        next_token = None

        try:
            while True:
                params = self._build_coverage_params(max_results, next_token)
                response = client.list_coverage(**params)
                covered_resources = response.get("coveredResources", [])

                processed_resources = self._process_coverage_resources(covered_resources)
                coverage.extend(processed_resources)

                next_token = response.get("nextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_client_error(e, "list Inspector coverage")

        return coverage

    def _build_coverage_params(self, max_results: int, next_token: Optional[str]) -> Dict[str, Any]:
        """
        Build parameters for list_coverage API call.

        :param int max_results: Maximum number of results to retrieve
        :param next_token: Pagination token
        :return: API parameters dictionary
        :rtype: Dict[str, Any]
        """
        params = {"maxResults": max_results}

        if next_token:
            params["nextToken"] = next_token

        if self.account_id:
            params["filterCriteria"] = {"accountId": [{"comparison": "EQUALS", "value": self.account_id}]}

        return params

    def _process_coverage_resources(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and filter coverage resources by tags.

        :param resources: List of coverage resources
        :return: Filtered list of resources
        :rtype: List[Dict[str, Any]]
        """
        processed = []

        for resource in resources:
            resource["Region"] = self.region

            if self._should_include_coverage_resource(resource):
                processed.append(resource)

        return processed

    def _should_include_coverage_resource(self, resource: Dict[str, Any]) -> bool:
        """
        Check if coverage resource should be included based on tag filter.

        :param resource: Coverage resource to check
        :return: True if resource should be included
        :rtype: bool
        """
        if not self.tags:
            return True

        resource_metadata = resource.get("resourceMetadata", {})
        resource_tags = resource_metadata.get("tags", {})

        if self._matches_tags(resource_tags):
            return True

        logger.debug(
            "Filtering out Inspector coverage resource %s - tags do not match filter",
            resource.get("resourceId", "unknown"),
        )
        return False

    def _list_coverage_statistics(self, client: Any) -> Dict[str, Any]:
        """
        Get coverage statistics.

        :param client: Inspector client
        :return: Coverage statistics
        :rtype: Dict[str, Any]
        """
        try:
            params = {}

            if self.account_id:
                params["filterCriteria"] = {"accountId": [{"comparison": "EQUALS", "value": self.account_id}]}

            response = client.list_coverage_statistics(**params)
            counts_by_group = response.get("countsByGroup", [])

            stats = {"Region": self.region, "CountsByGroup": counts_by_group}

            return stats
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.debug(f"Access denied to list Inspector coverage statistics in {self.region}")
            else:
                logger.error(f"Error listing Inspector coverage statistics: {e}")
            return {}

    def _list_findings(self, client: Any, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List Inspector findings with pagination support and tag filtering.

        :param client: Inspector client
        :param int max_results: Maximum number of results per page
        :return: List of findings
        :rtype: List[Dict[str, Any]]
        """
        findings = []
        next_token = None

        try:
            while True:
                params = self._build_findings_params(max_results, next_token)
                response = client.list_findings(**params)
                finding_list = response.get("findings", [])

                processed_findings = self._process_findings(finding_list)
                findings.extend(processed_findings)

                next_token = response.get("nextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_client_error(e, "list Inspector findings")

        return findings

    def _build_findings_params(self, max_results: int, next_token: Optional[str]) -> Dict[str, Any]:
        """
        Build parameters for list_findings API call.

        :param int max_results: Maximum number of results per page
        :param next_token: Pagination token
        :return: API parameters dictionary
        :rtype: Dict[str, Any]
        """
        params = {"maxResults": max_results}

        if next_token:
            params["nextToken"] = next_token

        if self.account_id:
            params["filterCriteria"] = {"awsAccountId": [{"comparison": "EQUALS", "value": self.account_id}]}

        return params

    def _process_findings(self, finding_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and filter findings by tags.

        :param finding_list: List of findings to process
        :return: Filtered list of findings
        :rtype: List[Dict[str, Any]]
        """
        processed = []

        for finding in finding_list:
            finding["Region"] = self.region

            if self._should_include_finding(finding):
                processed.append(finding)

        return processed

    def _should_include_finding(self, finding: Dict[str, Any]) -> bool:
        """
        Check if finding should be included based on tag filter.

        :param finding: Finding to check
        :return: True if finding should be included
        :rtype: bool
        """
        if not self.tags:
            return True

        if self._finding_matches_tag_filter(finding):
            return True

        logger.debug(
            "Filtering out Inspector finding %s - tags do not match filter", finding.get("findingArn", "unknown")
        )
        return False

    def _finding_matches_tag_filter(self, finding: Dict[str, Any]) -> bool:
        """
        Check if any resource in the finding matches the tag filter.

        :param finding: Finding to check
        :return: True if any resource matches the tag filter
        :rtype: bool
        """
        resources = finding.get("resources", [])

        for resource in resources:
            resource_tags = resource.get("tags", {})
            if self._matches_tags(resource_tags):
                return True

        return False

    def _list_members(self, client: Any) -> List[Dict[str, Any]]:
        """
        List member accounts for Inspector organization.

        :param client: Inspector client
        :return: List of member accounts
        :rtype: List[Dict[str, Any]]
        """
        members = []
        next_token = None

        try:
            while True:
                params = {}

                if next_token:
                    params["nextToken"] = next_token

                response = client.list_members(**params)
                member_list = response.get("members", [])

                for member in member_list:
                    # Filter by account ID if specified
                    if self.account_id and member.get("accountId") != self.account_id:
                        continue

                    member["Region"] = self.region

                members.extend(member_list)

                next_token = response.get("nextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.debug(f"Access denied to list Inspector members in {self.region}")
            else:
                logger.error(f"Error listing Inspector members: {e}")

        return members

    def _convert_tags_to_dict(self, tags: Any) -> Dict[str, str]:
        """
        Convert tags from various formats to a dictionary.

        :param tags: Tags in list format [{"key": "k", "value": "v"}] or dict format
        :return: Dictionary of tag key-value pairs
        :rtype: Dict[str, str]
        """
        if not tags:
            return {}

        if isinstance(tags, dict):
            return tags

        if isinstance(tags, list):
            return self._convert_tag_list_to_dict(tags)

        return {}

    def _convert_tag_list_to_dict(self, tags: List[Any]) -> Dict[str, str]:
        """
        Convert a list of tag dictionaries to a single dictionary.

        :param tags: List of tag dictionaries
        :return: Dictionary of tag key-value pairs
        :rtype: Dict[str, str]
        """
        tag_dict = {}

        for tag in tags:
            if isinstance(tag, dict):
                key_value = self._extract_tag_key_value(tag)
                if key_value:
                    tag_dict[key_value[0]] = key_value[1]

        return tag_dict

    def _extract_tag_key_value(self, tag: Dict[str, Any]) -> Optional[tuple]:
        """
        Extract key and value from a tag dictionary.

        Handles both lowercase and uppercase formats:
        - {"key": "k", "value": "v"}
        - {"Key": "k", "Value": "v"}

        :param tag: Tag dictionary
        :return: Tuple of (key, value) or None if key not found
        :rtype: Optional[tuple]
        """
        key = tag.get("key") or tag.get("Key")
        if key is None:
            return None

        value = tag.get("value") or tag.get("Value")
        return (key, value if value is not None else "")

    def _handle_client_error(self, error: ClientError, operation: str) -> None:
        """
        Handle ClientError exceptions consistently.

        :param error: The ClientError exception
        :param str operation: Description of the operation that failed
        """
        error_code = error.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            logger.warning("Access denied to %s in %s", operation, self.region)
        else:
            logger.error("Error %s: %s", operation, error)

    def _matches_tags(self, resource_tags: Any) -> bool:
        """
        Check if resource tags match all filter tags.

        :param resource_tags: Tags from the resource (can be dict or list)
        :return: True if all filter tags match, False otherwise
        :rtype: bool
        """
        if not self.tags:
            # No tag filter, so all resources match
            return True

        resource_tag_dict = self._convert_tags_to_dict(resource_tags)

        # All filter tags must match
        for filter_key, filter_value in self.tags.items():
            if filter_key not in resource_tag_dict:
                return False
            if resource_tag_dict[filter_key] != filter_value:
                return False

        return True
