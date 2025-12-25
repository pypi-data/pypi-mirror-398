"""AWS CloudWatch Logs resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class CloudWatchLogsCollector(BaseCollector):
    """Collector for AWS CloudWatch Logs resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize CloudWatch Logs collector.

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
        Collect CloudWatch Logs resources.

        :return: Dictionary containing CloudWatch log groups and their configurations
        :rtype: Dict[str, Any]
        """
        result = {"LogGroups": [], "LogGroupMetrics": {}, "RetentionPolicies": {}}

        try:
            client = self._get_client("logs")

            # List all log groups
            log_groups = self._list_log_groups(client)

            # Get detailed information for each log group
            for log_group in log_groups:
                log_group_name = log_group.get("logGroupName", "")
                log_group_arn = log_group.get("arn", "")

                # Filter by account ID if specified
                if self.account_id and log_group_arn and not self._matches_account_id(log_group_arn):
                    logger.debug(f"Skipping log group {log_group_name} - does not match account ID {self.account_id}")
                    continue

                # Get tags for filtering
                log_group_tags = self._get_log_group_tags(client, log_group_name)

                # Filter by tags if specified
                if self.tags and not self._matches_tags(log_group_tags):
                    logger.debug(f"Skipping log group {log_group_name} - does not match tag filters")
                    continue

                log_group["Tags"] = log_group_tags

                # Get metric filters for this log group
                metric_filters = self._get_metric_filters(client, log_group_name)
                log_group["MetricFilters"] = metric_filters

                # Get subscription filters
                subscription_filters = self._get_subscription_filters(client, log_group_name)
                log_group["SubscriptionFilters"] = subscription_filters

                # Get retention policy
                retention_days = log_group.get("retentionInDays")
                if retention_days:
                    result["RetentionPolicies"][log_group_name] = retention_days

                # Add region information
                log_group["Region"] = self.region

                # Get storage bytes
                stored_bytes = log_group.get("storedBytes", 0)
                result["LogGroupMetrics"][log_group_name] = {
                    "StoredBytes": stored_bytes,
                    "MetricFilterCount": len(metric_filters),
                    "SubscriptionFilterCount": len(subscription_filters),
                }

                result["LogGroups"].append(log_group)

            logger.info(f"Collected {len(result['LogGroups'])} CloudWatch log group(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "CloudWatch Logs log groups")
        except Exception as e:
            logger.error(f"Unexpected error collecting CloudWatch Logs: {e}", exc_info=True)

        return result

    def _list_log_groups(self, client: Any) -> List[Dict[str, Any]]:
        """
        List all CloudWatch log groups with pagination.

        :param client: CloudWatch Logs client
        :return: List of log groups
        :rtype: List[Dict[str, Any]]
        """
        try:
            log_groups = []
            paginator = client.get_paginator("describe_log_groups")

            for page in paginator.paginate():
                log_groups.extend(page.get("logGroups", []))

            logger.debug(f"Found {len(log_groups)} log groups in {self.region}")
            return log_groups

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list CloudWatch log groups in {self.region}")
                return []
            raise

    def _get_log_group_tags(self, client: Any, log_group_name: str) -> Dict[str, str]:
        """
        Get tags for a log group.

        :param client: CloudWatch Logs client
        :param str log_group_name: Log group name
        :return: Dictionary of tags
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags_for_resource(resourceArn=self._build_log_group_arn(log_group_name))
            return response.get("tags", {})
        except ClientError as e:
            if e.response["Error"]["Code"] in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.debug(f"Cannot get tags for log group {log_group_name}: {e}")
                return {}
            logger.error(f"Error getting tags for log group {log_group_name}: {e}")
            return {}

    def _build_log_group_arn(self, log_group_name: str) -> str:
        """
        Build ARN for a log group.

        :param str log_group_name: Log group name
        :return: Log group ARN
        :rtype: str
        """
        account_id = self.account_id or self.session.client("sts").get_caller_identity()["Account"]
        return f"arn:aws:logs:{self.region}:{account_id}:log-group:{log_group_name}"

    def _get_metric_filters(self, client: Any, log_group_name: str) -> List[Dict[str, Any]]:
        """
        Get metric filters for a log group.

        :param client: CloudWatch Logs client
        :param str log_group_name: Log group name
        :return: List of metric filters
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.describe_metric_filters(logGroupName=log_group_name)
            return response.get("metricFilters", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.debug(f"Cannot get metric filters for log group {log_group_name}: {e}")
                return []
            logger.error(f"Error getting metric filters for log group {log_group_name}: {e}")
            return []

    def _get_subscription_filters(self, client: Any, log_group_name: str) -> List[Dict[str, Any]]:
        """
        Get subscription filters for a log group.

        :param client: CloudWatch Logs client
        :param str log_group_name: Log group name
        :return: List of subscription filters
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.describe_subscription_filters(logGroupName=log_group_name)
            return response.get("subscriptionFilters", [])
        except ClientError as e:
            if e.response["Error"]["Code"] in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.debug(f"Cannot get subscription filters for log group {log_group_name}: {e}")
                return []
            logger.error(f"Error getting subscription filters for log group {log_group_name}: {e}")
            return []
