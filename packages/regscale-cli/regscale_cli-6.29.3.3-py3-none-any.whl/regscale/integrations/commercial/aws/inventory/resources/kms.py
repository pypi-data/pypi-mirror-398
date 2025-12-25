"""AWS KMS resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class KMSCollector(BaseCollector):
    """Collector for AWS KMS resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize KMS collector.

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
        Collect AWS KMS resources.

        :return: Dictionary containing KMS key information
        :rtype: Dict[str, Any]
        """
        result = {"Keys": [], "Aliases": []}

        try:
            client = self._get_client("kms")

            # Get all keys
            keys = self._list_keys(client)
            result["Keys"] = keys

            # Get all aliases
            aliases = self._list_aliases(client)
            result["Aliases"] = aliases

            logger.info(f"Collected {len(keys)} KMS key(s), {len(aliases)} alias(es) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "KMS keys")
        except Exception as e:
            logger.error(f"Unexpected error collecting KMS resources: {e}", exc_info=True)

        return result

    def _list_keys(self, client: Any) -> List[Dict[str, Any]]:
        """
        List KMS keys with enhanced details.

        :param client: KMS client
        :return: List of key information
        :rtype: List[Dict[str, Any]]
        """
        keys = []
        try:
            paginator = client.get_paginator("list_keys")

            for page in paginator.paginate():
                for key in page.get("Keys", []):
                    key_id = key["KeyId"]
                    processed_key = self._process_key(client, key_id)
                    if processed_key:
                        keys.append(processed_key)

        except ClientError as e:
            self._handle_list_keys_error(e)

        return keys

    def _process_key(self, client: Any, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Process a single KMS key and return its details if it passes filters.

        :param client: KMS client
        :param str key_id: Key ID to process
        :return: Key information if it passes filters, None otherwise
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            key_info = self._describe_key(client, key_id)
            if not key_info:
                return None

            if not self._passes_account_filter(key_info):
                return None

            self._enrich_key_info(client, key_id, key_info)

            if not self._passes_tag_filter(client, key_id):
                return None

            return key_info

        except ClientError as e:
            self._handle_key_processing_error(e, key_id)
            return None

    def _passes_account_filter(self, key_info: Dict[str, Any]) -> bool:
        """
        Check if key passes account ID filter.

        :param dict key_info: Key information dictionary
        :return: True if key passes account filter
        :rtype: bool
        """
        if not self.account_id:
            return True
        return self._matches_account_id(key_info.get("Arn", ""))

    def _enrich_key_info(self, client: Any, key_id: str, key_info: Dict[str, Any]) -> None:
        """
        Enrich key information with additional details.

        :param client: KMS client
        :param str key_id: Key ID
        :param dict key_info: Key information dictionary to enrich
        """
        key_info["Region"] = self.region
        key_info["RotationEnabled"] = self._get_key_rotation_status(client, key_id)
        key_info["Policy"] = self._get_key_policy(client, key_id)

        grants = self._list_grants(client, key_id)
        key_info["GrantCount"] = len(grants)

        tags = self._list_resource_tags(client, key_id)
        key_info["Tags"] = tags

    def _passes_tag_filter(self, client: Any, key_id: str) -> bool:
        """
        Check if key passes tag filter.

        :param client: KMS client
        :param str key_id: Key ID
        :return: True if key passes tag filter
        :rtype: bool
        """
        if not self.tags:
            return True

        key_tags = self._get_key_tags(client, key_id)
        if not self._matches_tags(key_tags):
            logger.debug(f"Skipping key {key_id} - does not match tag filters")
            return False
        return True

    def _handle_list_keys_error(self, error: ClientError) -> None:
        """
        Handle errors from list_keys operation.

        :param error: Client error exception
        """
        if error.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(f"Access denied to list KMS keys in {self.region}")
        else:
            logger.error(f"Error listing KMS keys: {error}")

    def _handle_key_processing_error(self, error: ClientError, key_id: str) -> None:
        """
        Handle errors from processing individual keys.

        :param error: Client error exception
        :param str key_id: Key ID being processed
        """
        if error.response["Error"]["Code"] not in ["NotFoundException", "AccessDeniedException"]:
            logger.error(f"Error getting details for key {key_id}: {error}")

    def _describe_key(self, client: Any, key_id: str) -> Optional[Dict[str, Any]]:
        """
        Get key metadata.

        :param client: KMS client
        :param str key_id: Key ID
        :return: Key metadata
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = client.describe_key(KeyId=key_id)
            key_metadata = response["KeyMetadata"]

            return {
                "KeyId": key_metadata.get("KeyId"),
                "Arn": key_metadata.get("Arn"),
                "Description": key_metadata.get("Description"),
                "Enabled": key_metadata.get("Enabled"),
                "KeyState": key_metadata.get("KeyState"),
                "CreationDate": str(key_metadata.get("CreationDate")),
                "DeletionDate": str(key_metadata.get("DeletionDate")) if key_metadata.get("DeletionDate") else None,
                "Origin": key_metadata.get("Origin"),
                "KeyManager": key_metadata.get("KeyManager"),
                "KeySpec": key_metadata.get("KeySpec"),
                "KeyUsage": key_metadata.get("KeyUsage"),
                "MultiRegion": key_metadata.get("MultiRegion", False),
                "MultiRegionConfiguration": key_metadata.get("MultiRegionConfiguration"),
            }
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["NotFoundException", "AccessDeniedException"]:
                logger.error(f"Error describing key {key_id}: {e}")
            return None

    def _get_key_rotation_status(self, client: Any, key_id: str) -> bool:
        """
        Get key rotation status.

        :param client: KMS client
        :param str key_id: Key ID
        :return: Rotation enabled status
        :rtype: bool
        """
        try:
            response = client.get_key_rotation_status(KeyId=key_id)
            return response.get("KeyRotationEnabled", False)
        except ClientError as e:
            if e.response["Error"]["Code"] in [
                "NotFoundException",
                "AccessDeniedException",
                "UnsupportedOperationException",
            ]:
                return False
            logger.debug(f"Error getting rotation status for key {key_id}: {e}")
            return False

    def _get_key_policy(self, client: Any, key_id: str) -> Optional[str]:
        """
        Get key policy.

        :param client: KMS client
        :param str key_id: Key ID
        :return: Key policy as JSON string
        :rtype: Optional[str]
        """
        try:
            response = client.get_key_policy(KeyId=key_id, PolicyName="default")
            return response.get("Policy")
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["NotFoundException", "AccessDeniedException"]:
                logger.debug(f"Error getting policy for key {key_id}: {e}")
            return None

    def _list_grants(self, client: Any, key_id: str) -> List[Dict[str, Any]]:
        """
        List grants for a key.

        :param client: KMS client
        :param str key_id: Key ID
        :return: List of grants
        :rtype: List[Dict[str, Any]]
        """
        grants = []
        try:
            paginator = client.get_paginator("list_grants")

            for page in paginator.paginate(KeyId=key_id):
                grants.extend(page.get("Grants", []))

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["NotFoundException", "AccessDeniedException"]:
                logger.debug(f"Error listing grants for key {key_id}: {e}")

        return grants

    def _list_resource_tags(self, client: Any, key_id: str) -> List[Dict[str, str]]:
        """
        List tags for a key.

        :param client: KMS client
        :param str key_id: Key ID
        :return: List of tags
        :rtype: List[Dict[str, str]]
        """
        try:
            response = client.list_resource_tags(KeyId=key_id)
            return response.get("Tags", [])
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["NotFoundException", "AccessDeniedException"]:
                logger.debug(f"Error listing tags for key {key_id}: {e}")
            return []

    def _list_aliases(self, client: Any) -> List[Dict[str, Any]]:
        """
        List KMS aliases.

        :param client: KMS client
        :return: List of aliases
        :rtype: List[Dict[str, Any]]
        """
        aliases = []
        try:
            paginator = client.get_paginator("list_aliases")

            for page in paginator.paginate():
                for alias in page.get("Aliases", []):
                    processed_alias = self._process_alias(client, alias)
                    if processed_alias:
                        aliases.append(processed_alias)

        except ClientError as e:
            self._handle_list_aliases_error(e)

        return aliases

    def _process_alias(self, client: Any, alias: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single KMS alias and return its details if it passes filters.

        :param client: KMS client
        :param dict alias: Alias information from AWS API
        :return: Alias dictionary if it passes filters, None otherwise
        :rtype: Optional[Dict[str, Any]]
        """
        if not self._alias_passes_filters(client, alias):
            return None

        return {
            "Region": self.region,
            "AliasName": alias.get("AliasName"),
            "AliasArn": alias.get("AliasArn"),
            "TargetKeyId": alias.get("TargetKeyId"),
        }

    def _alias_passes_filters(self, client: Any, alias: Dict[str, Any]) -> bool:
        """
        Check if alias passes account filtering rules.

        :param client: KMS client
        :param dict alias: Alias information
        :return: True if alias passes filters
        :rtype: bool
        """
        if not self.account_id:
            return True

        if self._is_aws_managed_alias(alias):
            return False

        return self._alias_target_matches_account(client, alias)

    def _is_aws_managed_alias(self, alias: Dict[str, Any]) -> bool:
        """
        Check if alias is AWS-managed.

        :param dict alias: Alias information
        :return: True if alias is AWS-managed
        :rtype: bool
        """
        alias_name = alias.get("AliasName", "")
        return alias_name.startswith("alias/aws/")

    def _alias_target_matches_account(self, client: Any, alias: Dict[str, Any]) -> bool:
        """
        Check if alias target key matches the account filter.

        :param client: KMS client
        :param dict alias: Alias information
        :return: True if target key matches account or no target key exists
        :rtype: bool
        """
        target_key_id = alias.get("TargetKeyId")
        if not target_key_id:
            return True

        key_info = self._describe_key(client, target_key_id)
        if not key_info:
            return True

        return self._matches_account_id(key_info.get("Arn", ""))

    def _handle_list_aliases_error(self, error: ClientError) -> None:
        """
        Handle errors from list_aliases operation.

        :param error: Client error exception
        """
        if error.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(f"Access denied to list KMS aliases in {self.region}")
        else:
            logger.error(f"Error listing KMS aliases: {error}")

    def _matches_account_id(self, arn: str) -> bool:
        """
        Check if ARN matches the specified account ID.

        :param str arn: ARN to check
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True

        # ARN format: arn:aws:kms:region:account-id:key/key-id
        try:
            arn_parts = arn.split(":")
            if len(arn_parts) >= 5:
                key_account_id = arn_parts[4]
                return key_account_id == self.account_id
        except (IndexError, AttributeError):
            logger.warning(f"Could not parse account ID from KMS key ARN: {arn}")

        return False

    def _get_key_tags(self, client: Any, key_id: str) -> Dict[str, str]:
        """
        Get tags for a KMS key.

        :param client: KMS client
        :param str key_id: Key ID
        :return: Dictionary of tags (Key -> Value)
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_resource_tags(KeyId=key_id)
            tags_list = response.get("Tags", [])
            return {tag["TagKey"]: tag["TagValue"] for tag in tags_list}
        except ClientError as e:
            logger.debug(f"Error getting tags for key {key_id}: {e}")
            return {}

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
