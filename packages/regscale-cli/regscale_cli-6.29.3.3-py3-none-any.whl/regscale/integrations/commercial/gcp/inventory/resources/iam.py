#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP IAM resource collectors.

This module provides collectors for GCP IAM resources including:
- Service Accounts
- Service Account Keys
- Custom IAM Roles
- Project IAM Policies
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class IAMCollector(BaseCollector):
    """Collector for GCP IAM resources."""

    # GCP asset types for IAM resources
    supported_asset_types: List[str] = [
        "iam.googleapis.com/ServiceAccount",
        "iam.googleapis.com/ServiceAccountKey",
        "iam.googleapis.com/Role",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the IAM collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_service_accounts(self) -> List[Dict[str, Any]]:
        """Get information about IAM service accounts.

        :return: List of service account information
        :rtype: List[Dict[str, Any]]
        """
        service_accounts: List[Dict[str, Any]] = []
        try:
            from google.cloud import iam_admin_v1

            client = iam_admin_v1.IAMClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for service accounts collection")
                return service_accounts

            # List service accounts for the project
            request = iam_admin_v1.ListServiceAccountsRequest(
                name=f"projects/{project}",
            )

            for service_account in client.list_service_accounts(request=request):
                service_accounts.append(self._parse_service_account(service_account))

        except Exception as e:
            self._handle_error(e, "IAM service accounts")

        return service_accounts

    def _parse_service_account(self, service_account: Any) -> Dict[str, Any]:
        """Parse a service account to a dictionary.

        :param service_account: Service account object from IAM API
        :return: Parsed service account data
        :rtype: Dict[str, Any]
        """
        return {
            "name": service_account.name,
            "email": service_account.email,
            "display_name": service_account.display_name,
            "description": service_account.description,
            "disabled": service_account.disabled,
            "unique_id": service_account.unique_id,
            "oauth2_client_id": service_account.oauth2_client_id,
            "project_id": service_account.project_id,
        }

    def get_service_account_keys(self, service_account_email: str) -> List[Dict[str, Any]]:
        """Get keys for a specific service account.

        :param str service_account_email: Email of the service account
        :return: List of service account key information
        :rtype: List[Dict[str, Any]]
        """
        keys: List[Dict[str, Any]] = []
        try:
            from google.cloud import iam_admin_v1

            client = iam_admin_v1.IAMClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for service account keys collection")
                return keys

            # List keys for the service account
            request = iam_admin_v1.ListServiceAccountKeysRequest(
                name=f"projects/{project}/serviceAccounts/{service_account_email}",
            )

            response = client.list_service_account_keys(request=request)

            for key in response.keys:
                keys.append(self._parse_service_account_key(key))

        except Exception as e:
            self._handle_error(e, "IAM service account keys")

        return keys

    def _parse_service_account_key(self, key: Any) -> Dict[str, Any]:
        """Parse a service account key to a dictionary.

        :param key: Service account key object from IAM API
        :return: Parsed service account key data
        :rtype: Dict[str, Any]
        """
        key_algorithm = key.key_algorithm.name if hasattr(key.key_algorithm, "name") else str(key.key_algorithm)
        key_origin = key.key_origin.name if hasattr(key.key_origin, "name") else str(key.key_origin)
        key_type = key.key_type.name if hasattr(key.key_type, "name") else str(key.key_type)
        valid_after = key.valid_after_time.isoformat() if key.valid_after_time else None
        valid_before = key.valid_before_time.isoformat() if key.valid_before_time else None
        disabled = key.disabled if hasattr(key, "disabled") else False

        return {
            "name": key.name,
            "key_algorithm": key_algorithm,
            "key_origin": key_origin,
            "key_type": key_type,
            "valid_after_time": valid_after,
            "valid_before_time": valid_before,
            "disabled": disabled,
        }

    def get_iam_policies(self) -> Dict[str, Any]:
        """Get IAM policy for the project.

        :return: IAM policy information
        :rtype: Dict[str, Any]
        """
        policy_data: Dict[str, Any] = {}
        try:
            from google.cloud import resourcemanager_v3

            client = resourcemanager_v3.ProjectsClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for IAM policy collection")
                return policy_data

            # Get IAM policy for the project
            policy = client.get_iam_policy(resource=f"projects/{project}")

            bindings = []
            for binding in policy.bindings:
                bindings.append(
                    {
                        "role": binding.role,
                        "members": list(binding.members) if binding.members else [],
                        "condition": (
                            {
                                "title": binding.condition.title,
                                "description": binding.condition.description,
                                "expression": binding.condition.expression,
                            }
                            if binding.condition and binding.condition.expression
                            else None
                        ),
                    }
                )

            policy_data = {
                "version": policy.version,
                "bindings": bindings,
                "etag": policy.etag.decode("utf-8") if isinstance(policy.etag, bytes) else policy.etag,
            }

        except Exception as e:
            self._handle_error(e, "IAM policies")

        return policy_data

    def get_custom_roles(self) -> List[Dict[str, Any]]:
        """Get custom IAM roles for the project or organization.

        :return: List of custom role information
        :rtype: List[Dict[str, Any]]
        """
        roles: List[Dict[str, Any]] = []
        try:
            from google.cloud import iam_admin_v1

            client = iam_admin_v1.IAMClient()

            # Determine parent for custom roles (project or organization)
            scope_type = self._get_scope_type()
            scope_id = self._get_scope_id()

            if scope_type == "project":
                parent = f"projects/{scope_id}"
            elif scope_type == "organization":
                parent = f"organizations/{scope_id}"
            else:
                # For folders, we need a project_id to list roles
                if self.project_id:
                    parent = f"projects/{self.project_id}"
                else:
                    logger.warning("No project or organization ID available for custom roles collection")
                    return roles

            # List custom roles
            request = iam_admin_v1.ListRolesRequest(
                parent=parent,
                show_deleted=False,
            )

            for role in client.list_roles(request=request):
                roles.append(self._parse_custom_role(role))

        except Exception as e:
            self._handle_error(e, "IAM custom roles")

        return roles

    def _parse_custom_role(self, role: Any) -> Dict[str, Any]:
        """Parse a custom role to a dictionary.

        :param role: Role object from IAM API
        :return: Parsed role data
        :rtype: Dict[str, Any]
        """
        return {
            "name": role.name,
            "title": role.title,
            "description": role.description,
            "stage": role.stage.name if hasattr(role.stage, "name") else str(role.stage),
            "included_permissions": list(role.included_permissions) if role.included_permissions else [],
            "deleted": role.deleted,
            "etag": role.etag.decode("utf-8") if isinstance(role.etag, bytes) else role.etag,
        }

    def get_all_service_account_keys(self) -> List[Dict[str, Any]]:
        """Get keys for all service accounts in the project.

        :return: List of all service account keys with their parent account info
        :rtype: List[Dict[str, Any]]
        """
        all_keys = []

        # First get all service accounts
        service_accounts = self.get_service_accounts()

        for sa in service_accounts:
            email = sa.get("email")
            if email:
                keys = self.get_service_account_keys(email)
                for key in keys:
                    key["service_account_email"] = email
                    key["service_account_name"] = sa.get("display_name", "")
                    all_keys.append(key)

        return all_keys

    def collect(self) -> Dict[str, Any]:
        """Collect IAM resources based on enabled_services configuration.

        :return: Dictionary containing enabled IAM resource information
        :rtype: Dict[str, Any]
        """
        result: Dict[str, Any] = {}

        # Service Accounts
        if self.enabled_services.get("service_accounts", True):
            result["ServiceAccounts"] = self.get_service_accounts()

        # Service Account Keys
        if self.enabled_services.get("service_account_keys", True):
            result["ServiceAccountKeys"] = self.get_all_service_account_keys()

        # IAM Policies
        if self.enabled_services.get("iam_policies", True):
            result["IAMPolicies"] = self.get_iam_policies()

        # Custom Roles
        if self.enabled_services.get("custom_roles", True):
            result["CustomRoles"] = self.get_custom_roles()

        return result
