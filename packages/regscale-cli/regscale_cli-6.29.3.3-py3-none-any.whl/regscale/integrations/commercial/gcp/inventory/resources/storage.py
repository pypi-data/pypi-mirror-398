#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Storage resource collectors.

This module provides collectors for GCP storage resources including:
- Cloud Storage buckets
- Filestore instances
- Filestore backups
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class StorageCollector(BaseCollector):
    """Collector for GCP storage resources."""

    # GCP asset types for storage resources
    supported_asset_types: List[str] = [
        "storage.googleapis.com/Bucket",
        "file.googleapis.com/Instance",
        "file.googleapis.com/Backup",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the storage collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_storage_buckets(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Storage buckets.

        :return: List of Cloud Storage bucket information
        :rtype: List[Dict[str, Any]]
        """
        buckets = []
        try:
            from google.cloud import storage

            client = storage.Client(project=self.project_id)
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Cloud Storage buckets collection")
                return buckets

            # List buckets for the project
            for bucket in client.list_buckets(project=project):
                bucket_labels = dict(bucket.labels) if bucket.labels else {}
                if not self._matches_labels(bucket_labels):
                    continue

                buckets.append(self._parse_bucket(bucket))

        except Exception as e:
            self._handle_error(e, "Cloud Storage buckets")

        return buckets

    def _parse_bucket(self, bucket: Any) -> Dict[str, Any]:
        """Parse a Cloud Storage bucket to a dictionary.

        :param bucket: Cloud Storage bucket object
        :return: Parsed bucket data
        :rtype: Dict[str, Any]
        """
        return {
            "name": bucket.name,
            "location": bucket.location,
            "storage_class": bucket.storage_class,
            "labels": dict(bucket.labels) if bucket.labels else {},
            "versioning": getattr(bucket, "versioning_enabled", False),
            "lifecycle": self._parse_lifecycle_rules(bucket),
            "iam_configuration": self._parse_iam_configuration(bucket),
            "time_created": self._format_timestamp(bucket, "time_created"),
            "updated": self._format_timestamp(bucket, "updated"),
            "default_event_based_hold": getattr(bucket, "default_event_based_hold", False),
            "retention_policy": self._parse_retention_policy(bucket),
        }

    def _parse_iam_configuration(self, bucket: Any) -> Dict[str, Any]:
        """Parse IAM configuration from a bucket.

        :param bucket: Cloud Storage bucket object
        :return: Parsed IAM configuration dictionary
        :rtype: Dict[str, Any]
        """
        if not hasattr(bucket, "iam_configuration") or not bucket.iam_configuration:
            return {}
        iam_config = bucket.iam_configuration
        if isinstance(iam_config, dict):
            return {
                "uniform_bucket_level_access_enabled": iam_config.get("uniformBucketLevelAccess", {}).get(
                    "enabled", False
                ),
                "public_access_prevention": iam_config.get("publicAccessPrevention"),
            }
        uniform_access = getattr(iam_config, "uniform_bucket_level_access", None)
        return {
            "uniform_bucket_level_access_enabled": getattr(uniform_access, "enabled", False),
            "public_access_prevention": getattr(iam_config, "public_access_prevention", None),
        }

    def _parse_lifecycle_rules(self, bucket: Any) -> List[Dict[str, Any]]:
        """Parse lifecycle rules from a bucket.

        :param bucket: Cloud Storage bucket object
        :return: List of parsed lifecycle rule dictionaries
        :rtype: List[Dict[str, Any]]
        """
        if not hasattr(bucket, "lifecycle_rules") or not bucket.lifecycle_rules:
            return []
        lifecycle_rules = []
        for rule in bucket.lifecycle_rules:
            if isinstance(rule, dict):
                lifecycle_rules.append(rule)
            else:
                lifecycle_rules.append(
                    {
                        "action": getattr(rule, "action", {}),
                        "condition": getattr(rule, "condition", {}),
                    }
                )
        return lifecycle_rules

    def _format_timestamp(self, obj: Any, attr_name: str) -> Optional[str]:
        """Format a timestamp attribute as ISO string.

        :param obj: Object containing the timestamp attribute
        :param attr_name: Name of the timestamp attribute
        :return: ISO formatted timestamp string or None
        :rtype: Optional[str]
        """
        if not hasattr(obj, attr_name):
            return None
        timestamp = getattr(obj, attr_name)
        if timestamp:
            return timestamp.isoformat()
        return None

    def _parse_retention_policy(self, bucket: Any) -> Optional[Dict[str, Any]]:
        """Parse retention policy from a bucket.

        :param bucket: Cloud Storage bucket object
        :return: Parsed retention policy dictionary or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(bucket, "retention_period") or not bucket.retention_period:
            return None
        return {
            "retention_period": bucket.retention_period,
            "effective_time": self._format_timestamp(bucket, "retention_policy_effective_time"),
            "is_locked": getattr(bucket, "retention_policy_locked", False),
        }

    def get_filestore_instances(self) -> List[Dict[str, Any]]:
        """Get information about Filestore instances.

        :return: List of Filestore instance information
        :rtype: List[Dict[str, Any]]
        """
        instances = []
        try:
            from google.cloud import filestore_v1

            client = filestore_v1.CloudFilestoreManagerClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Filestore instances collection")
                return instances

            # List instances for all locations
            parent = f"projects/{project}/locations/-"
            request = filestore_v1.ListInstancesRequest(parent=parent)

            for instance in client.list_instances(request=request):
                instance_labels = dict(instance.labels) if instance.labels else {}
                if not self._matches_labels(instance_labels):
                    continue

                instances.append(self._parse_filestore_instance(instance))

        except Exception as e:
            self._handle_error(e, "Filestore instances")

        return instances

    def _parse_filestore_instance(self, instance: Any) -> Dict[str, Any]:
        """Parse a Filestore instance to a dictionary.

        :param instance: Filestore instance object
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        return {
            "name": instance.name,
            "description": instance.description,
            "state": self._extract_enum_name(instance.state),
            "tier": self._extract_enum_name(instance.tier),
            "labels": dict(instance.labels) if instance.labels else {},
            "file_shares": self._parse_file_shares(instance),
            "networks": self._parse_filestore_networks(instance),
            "create_time": self._format_timestamp(instance, "create_time"),
            "status_message": getattr(instance, "status_message", None),
            "etag": getattr(instance, "etag", None),
            "satisfies_pzs": getattr(instance, "satisfies_pzs", None),
        }

    def _extract_enum_name(self, enum_value: Any) -> str:
        """Extract the name from an enum value.

        :param enum_value: Enum value object
        :return: String representation of the enum
        :rtype: str
        """
        if hasattr(enum_value, "name"):
            return enum_value.name
        return str(enum_value)

    def _parse_file_shares(self, instance: Any) -> List[Dict[str, Any]]:
        """Parse file shares from a Filestore instance.

        :param instance: Filestore instance object
        :return: List of parsed file share dictionaries
        :rtype: List[Dict[str, Any]]
        """
        if not hasattr(instance, "file_shares") or not instance.file_shares:
            return []
        return [
            {
                "name": share.name,
                "capacity_gb": share.capacity_gb,
                "source_backup": getattr(share, "source_backup", None),
            }
            for share in instance.file_shares
        ]

    def _parse_filestore_networks(self, instance: Any) -> List[Dict[str, Any]]:
        """Parse networks from a Filestore instance.

        :param instance: Filestore instance object
        :return: List of parsed network dictionaries
        :rtype: List[Dict[str, Any]]
        """
        if not hasattr(instance, "networks") or not instance.networks:
            return []
        return [
            {
                "network": network.network,
                "modes": list(network.modes or []),
                "reserved_ip_range": network.reserved_ip_range,
                "ip_addresses": list(network.ip_addresses or []),
            }
            for network in instance.networks
        ]

    def get_filestore_backups(self) -> List[Dict[str, Any]]:
        """Get information about Filestore backups.

        :return: List of Filestore backup information
        :rtype: List[Dict[str, Any]]
        """
        backups = []
        try:
            from google.cloud import filestore_v1

            client = filestore_v1.CloudFilestoreManagerClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Filestore backups collection")
                return backups

            # List backups for all locations
            parent = f"projects/{project}/locations/-"
            request = filestore_v1.ListBackupsRequest(parent=parent)

            for backup in client.list_backups(request=request):
                backup_labels = dict(backup.labels) if backup.labels else {}
                if not self._matches_labels(backup_labels):
                    continue

                backups.append(self._parse_filestore_backup(backup))

        except Exception as e:
            self._handle_error(e, "Filestore backups")

        return backups

    def _parse_filestore_backup(self, backup: Any) -> Dict[str, Any]:
        """Parse a Filestore backup to a dictionary.

        :param backup: Filestore backup object
        :return: Parsed backup data
        :rtype: Dict[str, Any]
        """
        source_tier = getattr(backup, "source_instance_tier", None)
        return {
            "name": backup.name,
            "description": backup.description,
            "state": self._extract_enum_name(backup.state),
            "labels": dict(backup.labels) if backup.labels else {},
            "create_time": self._format_timestamp(backup, "create_time"),
            "capacity_gb": getattr(backup, "capacity_gb", None),
            "storage_bytes": getattr(backup, "storage_bytes", None),
            "source_instance": getattr(backup, "source_instance", None),
            "source_file_share": getattr(backup, "source_file_share", None),
            "source_instance_tier": self._extract_enum_name(source_tier) if source_tier else None,
            "download_bytes": getattr(backup, "download_bytes", None),
            "satisfies_pzs": getattr(backup, "satisfies_pzs", None),
        }

    def collect(self) -> Dict[str, Any]:
        """Collect storage resources based on enabled_services configuration.

        :return: Dictionary containing enabled storage resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Cloud Storage buckets
        if self.enabled_services.get("cloud_storage", True):
            result["StorageBuckets"] = self.get_storage_buckets()

        # Filestore instances
        if self.enabled_services.get("filestore", True):
            result["FilestoreInstances"] = self.get_filestore_instances()

        # Filestore backups
        if self.enabled_services.get("filestore_backups", True):
            result["FilestoreBackups"] = self.get_filestore_backups()

        return result
