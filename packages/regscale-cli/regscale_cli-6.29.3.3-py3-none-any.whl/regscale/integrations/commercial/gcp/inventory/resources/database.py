#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Database resource collectors.

This module provides collectors for GCP database resources including:
- Cloud SQL instances
- Cloud Spanner instances
- Cloud Bigtable instances
- Cloud Memorystore (Redis) instances
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class DatabaseCollector(BaseCollector):
    """Collector for GCP database resources."""

    # GCP asset types for database resources
    supported_asset_types: List[str] = [
        "sqladmin.googleapis.com/Instance",
        "spanner.googleapis.com/Instance",
        "spanner.googleapis.com/Database",
        "bigtableadmin.googleapis.com/Instance",
        "bigtableadmin.googleapis.com/Cluster",
        "redis.googleapis.com/Instance",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the database collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_cloud_sql_instances(self) -> List[Dict[str, Any]]:
        """Get information about Cloud SQL instances.

        :return: List of Cloud SQL instance information
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        try:
            from googleapiclient.discovery import build

            # Cloud SQL Admin API uses REST
            service = build("sqladmin", "v1")
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Cloud SQL instances collection")
                return instances

            # List Cloud SQL instances
            request = service.instances().list(project=project)
            response = request.execute()

            for instance in response.get("items", []):
                user_labels = instance.get("settings", {}).get("userLabels", {})
                if not self._matches_labels(user_labels):
                    continue

                instances.append(self._parse_cloud_sql_instance(instance))

        except Exception as e:
            self._handle_error(e, "Cloud SQL instances")

        return instances

    def _parse_cloud_sql_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a Cloud SQL instance to a dictionary.

        :param Dict[str, Any] instance: Cloud SQL instance data from API
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        settings = instance.get("settings", {})
        return {
            "name": instance.get("name"),
            "database_version": instance.get("databaseVersion"),
            "state": instance.get("state"),
            "region": instance.get("region"),
            "gce_zone": instance.get("gceZone"),
            "instance_type": instance.get("instanceType"),
            "project": instance.get("project"),
            "self_link": instance.get("selfLink"),
            "connection_name": instance.get("connectionName"),
            "create_time": instance.get("createTime"),
            "labels": settings.get("userLabels", {}),
            "settings": {
                "tier": settings.get("tier"),
                "activation_policy": settings.get("activationPolicy"),
                "availability_type": settings.get("availabilityType"),
                "data_disk_size_gb": settings.get("dataDiskSizeGb"),
                "data_disk_type": settings.get("dataDiskType"),
                "storage_auto_resize": settings.get("storageAutoResize"),
                "backup_enabled": settings.get("backupConfiguration", {}).get("enabled"),
                "ip_configuration": {
                    "ipv4_enabled": settings.get("ipConfiguration", {}).get("ipv4Enabled"),
                    "require_ssl": settings.get("ipConfiguration", {}).get("requireSsl"),
                    "private_network": settings.get("ipConfiguration", {}).get("privateNetwork"),
                },
            },
            "ip_addresses": [
                {"ip_address": ip.get("ipAddress"), "type": ip.get("type")} for ip in instance.get("ipAddresses", [])
            ],
            "replica_names": instance.get("replicaNames", []),
            "master_instance_name": instance.get("masterInstanceName"),
        }

    def get_spanner_instances(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Spanner instances.

        :return: List of Cloud Spanner instance information
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        try:
            from google.cloud import spanner_admin_instance_v1

            client = spanner_admin_instance_v1.InstanceAdminClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Cloud Spanner instances collection")
                return instances

            # List Spanner instances
            parent = f"projects/{project}"
            request = spanner_admin_instance_v1.ListInstancesRequest(parent=parent)

            for instance in client.list_instances(request=request):
                labels = dict(instance.labels) if instance.labels else {}
                if not self._matches_labels(labels):
                    continue

                instances.append(self._parse_spanner_instance(instance))

        except Exception as e:
            self._handle_error(e, "Cloud Spanner instances")

        return instances

    def _parse_spanner_instance(self, instance: Any) -> Dict[str, Any]:
        """Parse a Cloud Spanner instance to a dictionary.

        :param instance: Cloud Spanner instance object
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        return {
            "name": instance.name,
            "display_name": instance.display_name,
            "config": instance.config,
            "node_count": instance.node_count,
            "processing_units": instance.processing_units,
            "state": instance.state.name if hasattr(instance.state, "name") else str(instance.state),
            "labels": dict(instance.labels) if instance.labels else {},
            "endpoint_uris": list(instance.endpoint_uris) if instance.endpoint_uris else [],
            "create_time": instance.create_time.isoformat() if instance.create_time else None,
            "update_time": instance.update_time.isoformat() if instance.update_time else None,
        }

    def get_bigtable_instances(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Bigtable instances.

        :return: List of Cloud Bigtable instance information
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        try:
            from google.cloud import bigtable_admin_v2

            client = bigtable_admin_v2.BigtableInstanceAdminClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Cloud Bigtable instances collection")
                return instances

            # List Bigtable instances
            parent = f"projects/{project}"
            request = bigtable_admin_v2.ListInstancesRequest(parent=parent)
            response = client.list_instances(request=request)

            for instance in response.instances:
                labels = dict(instance.labels) if instance.labels else {}
                if not self._matches_labels(labels):
                    continue

                instances.append(self._parse_bigtable_instance(instance, client))

        except Exception as e:
            self._handle_error(e, "Cloud Bigtable instances")

        return instances

    def _parse_bigtable_instance(self, instance: Any, client: Any) -> Dict[str, Any]:
        """Parse a Cloud Bigtable instance to a dictionary.

        :param instance: Cloud Bigtable instance object
        :param client: Bigtable instance admin client
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        from google.cloud import bigtable_admin_v2

        # Get clusters for this instance
        clusters: List[Dict[str, Any]] = []
        try:
            cluster_request = bigtable_admin_v2.ListClustersRequest(parent=instance.name)
            cluster_response = client.list_clusters(request=cluster_request)
            for cluster in cluster_response.clusters:
                clusters.append(
                    {
                        "name": cluster.name,
                        "location": cluster.location,
                        "state": cluster.state.name if hasattr(cluster.state, "name") else str(cluster.state),
                        "serve_nodes": cluster.serve_nodes,
                        "default_storage_type": (
                            cluster.default_storage_type.name
                            if hasattr(cluster.default_storage_type, "name")
                            else str(cluster.default_storage_type)
                        ),
                    }
                )
        except Exception as cluster_error:
            logger.warning("Could not retrieve clusters for Bigtable instance %s: %s", instance.name, cluster_error)

        return {
            "name": instance.name,
            "display_name": instance.display_name,
            "state": instance.state.name if hasattr(instance.state, "name") else str(instance.state),
            "type": instance.type_.name if hasattr(instance.type_, "name") else str(instance.type_),
            "labels": dict(instance.labels) if instance.labels else {},
            "create_time": instance.create_time.isoformat() if instance.create_time else None,
            "clusters": clusters,
        }

    def get_redis_instances(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Memorystore (Redis) instances.

        :return: List of Redis instance information
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        try:
            from google.cloud import redis_v1

            client = redis_v1.CloudRedisClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Redis instances collection")
                return instances

            # List Redis instances for all locations
            parent = f"projects/{project}/locations/-"
            request = redis_v1.ListInstancesRequest(parent=parent)

            for instance in client.list_instances(request=request):
                labels = dict(instance.labels) if instance.labels else {}
                if not self._matches_labels(labels):
                    continue

                instances.append(self._parse_redis_instance(instance))

        except Exception as e:
            self._handle_error(e, "Redis instances")

        return instances

    def _parse_redis_instance(self, instance: Any) -> Dict[str, Any]:
        """Parse a Redis instance to a dictionary.

        :param instance: Redis instance object
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        return {
            "name": instance.name,
            "display_name": instance.display_name,
            "location_id": instance.location_id,
            "alternative_location_id": instance.alternative_location_id,
            "redis_version": instance.redis_version,
            "tier": instance.tier.name if hasattr(instance.tier, "name") else str(instance.tier),
            "memory_size_gb": instance.memory_size_gb,
            "state": instance.state.name if hasattr(instance.state, "name") else str(instance.state),
            "status_message": instance.status_message,
            "labels": dict(instance.labels) if instance.labels else {},
            "host": instance.host,
            "port": instance.port,
            "current_location_id": instance.current_location_id,
            "create_time": instance.create_time.isoformat() if instance.create_time else None,
            "authorized_network": instance.authorized_network,
            "connect_mode": (
                instance.connect_mode.name if hasattr(instance.connect_mode, "name") else str(instance.connect_mode)
            ),
            "auth_enabled": instance.auth_enabled,
            "transit_encryption_mode": (
                instance.transit_encryption_mode.name
                if hasattr(instance.transit_encryption_mode, "name")
                else str(instance.transit_encryption_mode)
            ),
            "replica_count": instance.replica_count,
            "read_replicas_mode": (
                instance.read_replicas_mode.name
                if hasattr(instance.read_replicas_mode, "name")
                else str(instance.read_replicas_mode)
            ),
        }

    def collect(self) -> Dict[str, Any]:
        """Collect database resources based on enabled_services configuration.

        :return: Dictionary containing enabled database resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Cloud SQL instances
        if self.enabled_services.get("cloud_sql", True):
            result["CloudSQLInstances"] = self.get_cloud_sql_instances()

        # Cloud Spanner instances
        if self.enabled_services.get("cloud_spanner", True):
            result["SpannerInstances"] = self.get_spanner_instances()

        # Cloud Bigtable instances
        if self.enabled_services.get("cloud_bigtable", True):
            result["BigtableInstances"] = self.get_bigtable_instances()

        # Cloud Memorystore (Redis) instances
        if self.enabled_services.get("cloud_memorystore", True):
            result["RedisInstances"] = self.get_redis_instances()

        return result
