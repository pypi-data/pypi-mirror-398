"""AWS S3 resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class S3Collector(BaseCollector):
    """Collector for AWS S3 resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize S3 collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        """
        super().__init__(session, region, account_id, tags)

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS S3 resources.

        :return: Dictionary containing S3 bucket information
        :rtype: Dict[str, Any]
        """
        result = {"Buckets": []}

        try:
            client = self._get_client("s3")

            # Get all buckets
            buckets = self._list_buckets(client)
            result["Buckets"] = buckets

            logger.info(f"Collected {len(buckets)} S3 bucket(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "S3 buckets")
        except Exception as e:
            logger.error(f"Unexpected error collecting S3 resources: {e}", exc_info=True)

        return result

    def _list_buckets(self, client: Any) -> List[Dict[str, Any]]:
        """
        List S3 buckets with enhanced details.

        :param client: S3 client
        :return: List of bucket information
        :rtype: List[Dict[str, Any]]
        """
        buckets = []
        try:
            response = client.list_buckets()

            for bucket in response.get("Buckets", []):
                bucket_name = bucket["Name"]
                bucket_dict = self._process_bucket(client, bucket, bucket_name)

                if bucket_dict:
                    buckets.append(bucket_dict)

        except ClientError as e:
            self._handle_list_buckets_error(e)

        return buckets

    def _process_bucket(self, client: Any, bucket: Dict[str, Any], bucket_name: str) -> Optional[Dict[str, Any]]:
        """
        Process a single bucket and return its details if it passes filters.

        :param client: S3 client
        :param dict bucket: Bucket information from list_buckets
        :param str bucket_name: Bucket name
        :return: Bucket details dictionary or None if bucket should be skipped
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            # Get bucket location
            location = self._get_bucket_location(client, bucket_name)

            # Only include buckets in the target region
            if location != self.region:
                return None

            # Build bucket details dictionary
            bucket_dict = self._build_bucket_details(client, bucket, bucket_name, location)

            # Apply tag filtering if configured
            if not self._should_include_bucket(bucket_dict):
                return None

            return bucket_dict

        except ClientError as e:
            self._handle_bucket_processing_error(e, bucket_name)
            return None

    def _build_bucket_details(
        self, client: Any, bucket: Dict[str, Any], bucket_name: str, location: str
    ) -> Dict[str, Any]:
        """
        Build complete details dictionary for a bucket.

        :param client: S3 client
        :param dict bucket: Bucket information from list_buckets
        :param str bucket_name: Bucket name
        :param str location: Bucket location/region
        :return: Complete bucket details dictionary
        :rtype: Dict[str, Any]
        """
        bucket_dict = {
            "Region": self.region,
            "Name": bucket_name,
            "CreationDate": str(bucket["CreationDate"]),
            "Location": location,
        }

        # Get encryption configuration
        encryption = self._get_bucket_encryption(client, bucket_name)
        bucket_dict["Encryption"] = encryption

        # Get versioning configuration
        versioning = self._get_bucket_versioning(client, bucket_name)
        bucket_dict["Versioning"] = versioning

        # Get public access block configuration
        public_access_block = self._get_public_access_block(client, bucket_name)
        bucket_dict["PublicAccessBlock"] = public_access_block

        # Get bucket policy status
        policy_status = self._get_bucket_policy_status(client, bucket_name)
        bucket_dict["PolicyStatus"] = policy_status

        # Get bucket ACL
        acl = self._get_bucket_acl(client, bucket_name)
        bucket_dict["ACL"] = acl

        # Get bucket tagging
        tags = self._get_bucket_tagging(client, bucket_name)
        bucket_dict["Tags"] = tags

        # Get bucket logging
        logging_config = self._get_bucket_logging(client, bucket_name)
        bucket_dict["Logging"] = logging_config

        return bucket_dict

    def _should_include_bucket(self, bucket_dict: Dict[str, Any]) -> bool:
        """
        Check if bucket should be included based on tag filters.

        :param dict bucket_dict: Bucket details dictionary
        :return: True if bucket should be included, False otherwise
        :rtype: bool
        """
        if not self.tags:
            return True

        tags = bucket_dict.get("Tags", [])
        bucket_tags_dict = self._convert_tags_to_dict(tags)

        if not self._matches_tags(bucket_tags_dict):
            bucket_name = bucket_dict.get("Name", "unknown")
            logger.debug("Skipping bucket %s - does not match tag filters", bucket_name)
            return False

        return True

    def _handle_list_buckets_error(self, error: ClientError) -> None:
        """
        Handle errors from list_buckets operation.

        :param ClientError error: The client error to handle
        """
        error_code = error.response["Error"]["Code"]
        if error_code == "AccessDenied":
            logger.warning("Access denied to list S3 buckets")
        else:
            logger.error("Error listing S3 buckets: %s", error)

    def _handle_bucket_processing_error(self, error: ClientError, bucket_name: str) -> None:
        """
        Handle errors during bucket detail processing.

        :param ClientError error: The client error to handle
        :param str bucket_name: Name of the bucket being processed
        """
        error_code = error.response["Error"]["Code"]
        if error_code not in ["NoSuchBucket", "AccessDenied"]:
            logger.error("Error getting details for bucket %s: %s", bucket_name, error)

    def _get_bucket_location(self, client: Any, bucket_name: str) -> str:
        """
        Get bucket location.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Bucket region
        :rtype: str
        """
        try:
            response = client.get_bucket_location(Bucket=bucket_name)
            location = response.get("LocationConstraint") or "us-east-1"
            return location
        except ClientError:
            return "unknown"

    def _get_bucket_encryption(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket encryption configuration.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Encryption configuration
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_bucket_encryption(Bucket=bucket_name)
            rules = response.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
            if rules:
                return {
                    "Enabled": True,
                    "Algorithm": rules[0].get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm"),
                    "KMSMasterKeyID": rules[0].get("ApplyServerSideEncryptionByDefault", {}).get("KMSMasterKeyID"),
                }
            return {"Enabled": False}
        except ClientError as e:
            if e.response["Error"]["Code"] == "ServerSideEncryptionConfigurationNotFoundError":
                return {"Enabled": False}
            logger.debug(f"Error getting encryption for bucket {bucket_name}: {e}")
            return {}

    def _get_bucket_versioning(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket versioning configuration.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Versioning configuration
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_bucket_versioning(Bucket=bucket_name)
            return {"Status": response.get("Status", "Disabled"), "MFADelete": response.get("MFADelete", "Disabled")}
        except ClientError as e:
            logger.debug(f"Error getting versioning for bucket {bucket_name}: {e}")
            return {}

    def _get_public_access_block(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get public access block configuration.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Public access block configuration
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_public_access_block(Bucket=bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            return {
                "BlockPublicAcls": config.get("BlockPublicAcls", False),
                "IgnorePublicAcls": config.get("IgnorePublicAcls", False),
                "BlockPublicPolicy": config.get("BlockPublicPolicy", False),
                "RestrictPublicBuckets": config.get("RestrictPublicBuckets", False),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchPublicAccessBlockConfiguration":
                return {
                    "BlockPublicAcls": False,
                    "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False,
                    "RestrictPublicBuckets": False,
                }
            logger.debug(f"Error getting public access block for bucket {bucket_name}: {e}")
            return {}

    def _get_bucket_policy_status(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket policy status.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Policy status
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_bucket_policy_status(Bucket=bucket_name)
            policy_status = response.get("PolicyStatus", {})
            return {"IsPublic": policy_status.get("IsPublic", False)}
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
                return {"IsPublic": False}
            logger.debug(f"Error getting policy status for bucket {bucket_name}: {e}")
            return {}

    def _get_bucket_acl(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket ACL.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: ACL information
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_bucket_acl(Bucket=bucket_name)
            return {"Owner": response.get("Owner", {}), "GrantCount": len(response.get("Grants", []))}
        except ClientError as e:
            logger.debug(f"Error getting ACL for bucket {bucket_name}: {e}")
            return {}

    def _get_bucket_tagging(self, client: Any, bucket_name: str) -> List[Dict[str, str]]:
        """
        Get bucket tags.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: List of tags
        :rtype: List[Dict[str, str]]
        """
        try:
            response = client.get_bucket_tagging(Bucket=bucket_name)
            return response.get("TagSet", [])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchTagSet":
                return []
            logger.debug(f"Error getting tags for bucket {bucket_name}: {e}")
            return []

    def _get_bucket_logging(self, client: Any, bucket_name: str) -> Dict[str, Any]:
        """
        Get bucket logging configuration.

        :param client: S3 client
        :param str bucket_name: Bucket name
        :return: Logging configuration
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_bucket_logging(Bucket=bucket_name)
            logging_enabled = response.get("LoggingEnabled", {})
            if logging_enabled:
                return {
                    "Enabled": True,
                    "TargetBucket": logging_enabled.get("TargetBucket"),
                    "TargetPrefix": logging_enabled.get("TargetPrefix"),
                }
            return {"Enabled": False}
        except ClientError as e:
            logger.debug(f"Error getting logging for bucket {bucket_name}: {e}")
            return {}

    def _convert_tags_to_dict(self, tags_list: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Convert S3 tags list format to dictionary format.

        S3 returns tags as list of dicts: [{"Key": "k1", "Value": "v1"}]
        Convert to dict format: {"k1": "v1"}

        :param list tags_list: List of tag dictionaries
        :return: Dictionary of tags (Key -> Value)
        :rtype: Dict[str, str]
        """
        return {tag.get("Key", ""): tag.get("Value", "") for tag in tags_list}

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
