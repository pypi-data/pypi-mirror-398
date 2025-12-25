"""Base classes for AWS resource collection."""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    import boto3

logger = logging.getLogger("regscale")


class BaseCollector:
    """Base class for AWS resource collectors with universal filtering support."""

    def __init__(
        self,
        session: "boto3.Session",
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the base collector with filtering support.

        :param boto3.Session session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional dictionary of tag key-value pairs to filter resources (AND logic)
        """
        self.session = session
        self.region = region
        self.account_id = account_id
        self.tags = tags or {}

    def _get_client(self, service_name: str) -> Any:
        """
        Get a boto3 client for the specified service.

        :param str service_name: Name of the AWS service
        :return: Boto3 client for the service
        :rtype: Any
        """
        return self.session.client(service_name, region_name=self.region)

    def _matches_account(self, resource_arn: str) -> bool:
        """
        Check if resource belongs to target account.

        :param str resource_arn: AWS Resource ARN
        :return: True if resource matches account filter or no filter specified
        :rtype: bool

        ARN format: arn:partition:service:region:account-id:resource
        """
        if not self.account_id:
            return True  # No filter, include all

        try:
            # ARN format: arn:aws:service:region:account-id:resource-id
            arn_parts = resource_arn.split(":")
            if len(arn_parts) >= 5:
                arn_account = arn_parts[4]
                match = arn_account == self.account_id
                if not match:
                    logger.debug(f"Filtering out resource {resource_arn} - account {arn_account} != {self.account_id}")
                return match
        except (IndexError, AttributeError) as e:
            logger.debug(f"Could not parse account from ARN {resource_arn}: {e}")
            return True  # Can't parse, include by default

        return True

    def _matches_tags(self, resource_tags: Any) -> bool:
        """
        Check if all filter tags match resource tags (AND logic).

        Supports multiple AWS tag formats:
        - Dict: {'Key': 'Value', ...}
        - List of dicts: [{'Key': 'k', 'Value': 'v'}, ...]
        - List of Tags: [{'key': 'k', 'value': 'v'}, ...] (lowercase)

        :param resource_tags: Resource tags in any AWS format
        :return: True if all filter tags match (or no filter), False otherwise
        :rtype: bool
        """
        if not self.tags:
            return True  # No filter, include all

        # Normalize tags to dict format
        normalized_tags = self._normalize_tags(resource_tags)

        # All filter tags must match (AND logic)
        for key, value in self.tags.items():
            if normalized_tags.get(key) != value:
                logger.debug(
                    f"Resource does not match tag filter: expected {key}={value}, got {normalized_tags.get(key)}"
                )
                return False

        return True

    def _normalize_tags(self, tags: Any) -> Dict[str, str]:
        """
        Normalize various AWS tag formats to simple dict.

        Handles:
        - Dict format: {'Key': 'Value'}
        - List format: [{'Key': 'k', 'Value': 'v'}] (uppercase)
        - List format: [{'key': 'k', 'value': 'v'}] (lowercase)
        - None or empty

        :param tags: Tags in any AWS format
        :return: Normalized dict of tags
        :rtype: Dict[str, str]
        """
        if not tags:
            return {}

        if isinstance(tags, dict):
            return tags

        if isinstance(tags, list):
            result = {}
            for tag in tags:
                if isinstance(tag, dict):
                    # Handle uppercase format (most common)
                    if "Key" in tag and "Value" in tag:
                        result[tag["Key"]] = tag["Value"]
                    # Handle lowercase format
                    elif "key" in tag and "value" in tag:
                        result[tag["key"]] = tag["value"]
            return result

        logger.warning(f"Unexpected tag format: {type(tags)}")
        return {}

    def _handle_error(self, error: Exception, resource_type: str) -> None:
        """
        Handle and log AWS API errors.

        :param Exception error: The error that occurred
        :param str resource_type: Type of resource being collected
        """
        if isinstance(error, ClientError):
            if error.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to {resource_type} in {self.region}")
            else:
                logger.error(f"Error collecting {resource_type} in {self.region}: {error}")
                logger.debug(error, exc_info=True)
        else:
            logger.error(f"Unexpected error collecting {resource_type} in {self.region}: {error}")
            logger.debug(error, exc_info=True)

    def collect(self) -> Dict[str, Any]:
        """
        Collect resources. Must be implemented by subclasses.

        :return: Dictionary containing resource information
        :rtype: Dict[str, Any]
        :raises NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement collect()")
