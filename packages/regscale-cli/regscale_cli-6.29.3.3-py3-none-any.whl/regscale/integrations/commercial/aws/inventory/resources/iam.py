"""AWS IAM resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class IAMCollector(BaseCollector):
    """Collector for AWS IAM resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize IAM collector.

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
        Collect AWS IAM resources.

        :return: Dictionary containing IAM resources
        :rtype: Dict[str, Any]
        """
        result = {
            "Users": [],
            "Roles": [],
            "Groups": [],
            "Policies": [],
            "AccessKeys": [],
            "MFADevices": [],
            "AccountSummary": {},
            "PasswordPolicy": {},
        }

        try:
            client = self._get_client("iam")

            # Get account summary
            result["AccountSummary"] = self._get_account_summary(client)

            # Get password policy
            result["PasswordPolicy"] = self._get_password_policy(client)

            # Get users
            users = self._list_users(client)
            result["Users"] = users

            # Get roles
            roles = self._list_roles(client)
            result["Roles"] = roles

            # Get groups
            groups = self._list_groups(client)
            result["Groups"] = groups

            # Get policies
            policies = self._list_policies(client)
            result["Policies"] = policies

            # Get access keys for users
            access_keys = []
            for user in users:
                user_name = user.get("UserName")
                if user_name:
                    keys = self._list_access_keys(client, user_name)
                    access_keys.extend(keys)
            result["AccessKeys"] = access_keys

            # Get MFA devices for users
            mfa_devices = []
            for user in users:
                user_name = user.get("UserName")
                if user_name:
                    devices = self._list_mfa_devices(client, user_name)
                    mfa_devices.extend(devices)
            result["MFADevices"] = mfa_devices

            logger.info(
                f"Collected {len(users)} IAM user(s), {len(roles)} role(s), "
                f"{len(groups)} group(s), {len(policies)} polic(ies) from {self.region}"
            )

        except ClientError as e:
            self._handle_error(e, "IAM resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting IAM resources: {e}", exc_info=True)

        return result

    def _get_account_summary(self, client: Any) -> Dict[str, Any]:
        """
        Get IAM account summary.

        :param client: IAM client
        :return: Account summary information
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_account_summary()
            summary = response.get("SummaryMap", {})
            summary["Region"] = self.region
            return summary
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                logger.warning(f"Access denied to get IAM account summary in {self.region}")
            else:
                logger.error(f"Error getting IAM account summary: {e}")
            return {}

    def _get_password_policy(self, client: Any) -> Dict[str, Any]:
        """
        Get IAM password policy.

        :param client: IAM client
        :return: Password policy information
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_account_password_policy()
            policy = response.get("PasswordPolicy", {})
            policy["Region"] = self.region
            return policy
        except ClientError as e:
            if e.response["Error"]["Code"] in ["NoSuchEntity", "AccessDenied"]:
                logger.debug(f"No password policy found or access denied in {self.region}")
            else:
                logger.error(f"Error getting IAM password policy: {e}")
            return {}

    def _list_users(self, client: Any) -> List[Dict[str, Any]]:
        """
        List IAM users with pagination.

        :param client: IAM client
        :return: List of users
        :rtype: List[Dict[str, Any]]
        """
        users = []
        try:
            paginator = client.get_paginator("list_users")

            for page in paginator.paginate():
                for user in page.get("Users", []):
                    processed_user = self._process_user(user)
                    if processed_user:
                        users.append(processed_user)

        except ClientError as e:
            self._handle_list_users_error(e)

        return users

    def _process_user(self, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and filter a single IAM user.

        :param dict user: Raw user data from AWS API
        :return: Processed user dictionary or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        if not self._should_include_user(user):
            return None

        return self._build_user_dict(user)

    def _should_include_user(self, user: Dict[str, Any]) -> bool:
        """
        Check if user should be included based on filters.

        :param dict user: Raw user data from AWS API
        :return: True if user passes all filters
        :rtype: bool
        """
        if self.account_id and not self._matches_account_id(user.get("Arn", "")):
            return False

        if self.tags:
            user_tags = self._convert_tags_to_dict(user.get("Tags", []))
            if not self._matches_tags(user_tags):
                logger.debug(f"Skipping user {user.get('UserName')} - does not match tag filters")
                return False

        return True

    def _build_user_dict(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build user dictionary with standardized fields.

        :param dict user: Raw user data from AWS API
        :return: Processed user dictionary
        :rtype: Dict[str, Any]
        """
        password_last_used = user.get("PasswordLastUsed")
        return {
            "Region": self.region,
            "UserName": user.get("UserName"),
            "UserId": user.get("UserId"),
            "Arn": user.get("Arn"),
            "CreateDate": str(user.get("CreateDate")),
            "PasswordLastUsed": str(password_last_used) if password_last_used else None,
            "Path": user.get("Path"),
            "PermissionsBoundary": user.get("PermissionsBoundary"),
            "Tags": user.get("Tags", []),
        }

    def _handle_list_users_error(self, e: ClientError) -> None:
        """
        Handle errors from listing IAM users.

        :param ClientError e: The client error to handle
        """
        if e.response["Error"]["Code"] == "AccessDenied":
            logger.warning(f"Access denied to list IAM users in {self.region}")
        else:
            logger.error(f"Error listing IAM users: {e}")

    def _list_roles(self, client: Any) -> List[Dict[str, Any]]:
        """
        List IAM roles with pagination.

        :param client: IAM client
        :return: List of roles
        :rtype: List[Dict[str, Any]]
        """
        roles = []
        try:
            paginator = client.get_paginator("list_roles")

            for page in paginator.paginate():
                for role in page.get("Roles", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(role.get("Arn", "")):
                        continue

                    # Filter by tags if specified
                    role_tags = self._convert_tags_to_dict(role.get("Tags", []))
                    if self.tags and not self._matches_tags(role_tags):
                        logger.debug(f"Skipping role {role.get('RoleName')} - does not match tag filters")
                        continue

                    role_dict = {
                        "Region": self.region,
                        "RoleName": role.get("RoleName"),
                        "RoleId": role.get("RoleId"),
                        "Arn": role.get("Arn"),
                        "CreateDate": str(role.get("CreateDate")),
                        "AssumeRolePolicyDocument": role.get("AssumeRolePolicyDocument"),
                        "Description": role.get("Description"),
                        "MaxSessionDuration": role.get("MaxSessionDuration"),
                        "Path": role.get("Path"),
                        "PermissionsBoundary": role.get("PermissionsBoundary"),
                        "Tags": role.get("Tags", []),
                    }
                    roles.append(role_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                logger.warning(f"Access denied to list IAM roles in {self.region}")
            else:
                logger.error(f"Error listing IAM roles: {e}")

        return roles

    def _list_groups(self, client: Any) -> List[Dict[str, Any]]:
        """
        List IAM groups with pagination.

        :param client: IAM client
        :return: List of groups
        :rtype: List[Dict[str, Any]]
        """
        groups = []
        try:
            paginator = client.get_paginator("list_groups")

            for page in paginator.paginate():
                for group in page.get("Groups", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(group.get("Arn", "")):
                        continue

                    group_dict = {
                        "Region": self.region,
                        "GroupName": group.get("GroupName"),
                        "GroupId": group.get("GroupId"),
                        "Arn": group.get("Arn"),
                        "CreateDate": str(group.get("CreateDate")),
                        "Path": group.get("Path"),
                    }
                    groups.append(group_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                logger.warning(f"Access denied to list IAM groups in {self.region}")
            else:
                logger.error(f"Error listing IAM groups: {e}")

        return groups

    def _list_policies(self, client: Any, scope: str = "Local") -> List[Dict[str, Any]]:
        """
        List IAM policies with pagination.

        :param client: IAM client
        :param str scope: Policy scope (Local or AWS)
        :return: List of policies
        :rtype: List[Dict[str, Any]]
        """
        policies = []
        try:
            paginator = client.get_paginator("list_policies")

            for page in paginator.paginate(Scope=scope):
                for policy in page.get("Policies", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(policy.get("Arn", "")):
                        continue

                    # Filter by tags if specified
                    policy_tags = self._convert_tags_to_dict(policy.get("Tags", []))
                    if self.tags and not self._matches_tags(policy_tags):
                        logger.debug(f"Skipping policy {policy.get('PolicyName')} - does not match tag filters")
                        continue

                    policy_dict = {
                        "Region": self.region,
                        "PolicyName": policy.get("PolicyName"),
                        "PolicyId": policy.get("PolicyId"),
                        "Arn": policy.get("Arn"),
                        "CreateDate": str(policy.get("CreateDate")),
                        "UpdateDate": str(policy.get("UpdateDate")),
                        "AttachmentCount": policy.get("AttachmentCount"),
                        "PermissionsBoundaryUsageCount": policy.get("PermissionsBoundaryUsageCount"),
                        "IsAttachable": policy.get("IsAttachable"),
                        "Description": policy.get("Description"),
                        "DefaultVersionId": policy.get("DefaultVersionId"),
                        "Path": policy.get("Path"),
                        "Tags": policy.get("Tags", []),
                    }
                    policies.append(policy_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                logger.warning(f"Access denied to list IAM policies in {self.region}")
            else:
                logger.error(f"Error listing IAM policies: {e}")

        return policies

    def _list_access_keys(self, client: Any, user_name: str) -> List[Dict[str, Any]]:
        """
        List access keys for a user.

        :param client: IAM client
        :param str user_name: User name
        :return: List of access keys
        :rtype: List[Dict[str, Any]]
        """
        access_keys = []
        try:
            response = client.list_access_keys(UserName=user_name)
            for key in response.get("AccessKeyMetadata", []):
                key_dict = {
                    "Region": self.region,
                    "UserName": user_name,
                    "AccessKeyId": key.get("AccessKeyId"),
                    "Status": key.get("Status"),
                    "CreateDate": str(key.get("CreateDate")),
                }
                access_keys.append(key_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                logger.debug(f"Error listing access keys for user {user_name}: {e}")

        return access_keys

    def _list_mfa_devices(self, client: Any, user_name: str) -> List[Dict[str, Any]]:
        """
        List MFA devices for a user.

        :param client: IAM client
        :param str user_name: User name
        :return: List of MFA devices
        :rtype: List[Dict[str, Any]]
        """
        mfa_devices = []
        try:
            response = client.list_mfa_devices(UserName=user_name)
            for device in response.get("MFADevices", []):
                device_dict = {
                    "Region": self.region,
                    "UserName": user_name,
                    "SerialNumber": device.get("SerialNumber"),
                    "EnableDate": str(device.get("EnableDate")),
                }
                mfa_devices.append(device_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDenied":
                logger.debug(f"Error listing MFA devices for user {user_name}: {e}")

        return mfa_devices

    def _matches_account_id(self, arn: str) -> bool:
        """
        Check if ARN matches the specified account ID.

        :param str arn: ARN to check
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True

        # ARN format: arn:aws:iam::account-id:resource-type/resource-name
        try:
            arn_parts = arn.split(":")
            if len(arn_parts) >= 5:
                resource_account_id = arn_parts[4]
                return resource_account_id == self.account_id
        except (IndexError, AttributeError):
            logger.warning(f"Could not parse account ID from ARN: {arn}")

        return False

    def _convert_tags_to_dict(self, tags_list: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Convert IAM tags list format to dictionary format.

        IAM returns tags as list of dicts: [{"Key": "k1", "Value": "v1"}]
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
