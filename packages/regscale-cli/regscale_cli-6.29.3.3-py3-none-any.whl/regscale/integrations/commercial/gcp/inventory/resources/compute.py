#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Compute resource collectors.

This module provides collectors for GCP compute resources including:
- Compute Engine instances
- GKE clusters
- Cloud Run services
- Cloud Functions
- App Engine services
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class ComputeCollector(BaseCollector):
    """Collector for GCP compute resources."""

    # GCP asset types for compute resources
    supported_asset_types: List[str] = [
        "compute.googleapis.com/Instance",
        "compute.googleapis.com/Disk",
        "compute.googleapis.com/Image",
        "compute.googleapis.com/InstanceGroup",
        "compute.googleapis.com/InstanceTemplate",
        "container.googleapis.com/Cluster",
        "container.googleapis.com/NodePool",
        "run.googleapis.com/Service",
        "run.googleapis.com/Revision",
        "cloudfunctions.googleapis.com/Function",
        "cloudfunctions.googleapis.com/CloudFunction",
        "appengine.googleapis.com/Service",
        "appengine.googleapis.com/Version",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the compute collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_compute_instances(self) -> List[Dict[str, Any]]:
        """Get information about Compute Engine instances.

        :return: List of Compute Engine instance information
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.InstancesClient()
            project = self._get_project_id()

            if not project:
                logger.warning("No project ID available for Compute Engine instances collection")
                return instances

            aggregated_list = client.aggregated_list(project=project)
            instances = self._collect_instances_from_zones(aggregated_list)

        except Exception as e:
            self._handle_error(e, "Compute Engine instances")

        return instances

    def _get_project_id(self) -> Optional[str]:
        """Get the project ID from scope or instance attribute.

        :return: Project ID if available
        :rtype: Optional[str]
        """
        if self._get_scope_type() == "project":
            return self._get_scope_id()
        return self.project_id

    def _collect_instances_from_zones(self, aggregated_list: Any) -> List[Dict[str, Any]]:
        """Collect instances from all zones in an aggregated list response.

        :param aggregated_list: Aggregated list response from Compute Engine API
        :return: List of parsed instance data
        :rtype: List[Dict[str, Any]]
        """
        instances: List[Dict[str, Any]] = []
        for zone, response in aggregated_list:
            if not response.instances:
                continue
            for instance in response.instances:
                labels = dict(instance.labels) if instance.labels else {}
                if self._matches_labels(labels):
                    instances.append(self._parse_compute_instance(instance))
        return instances

    def _parse_compute_instance(self, instance: Any) -> Dict[str, Any]:
        """Parse a Compute Engine instance to a dictionary.

        :param instance: Compute Engine instance object
        :return: Parsed instance data
        :rtype: Dict[str, Any]
        """
        return {
            "name": instance.name,
            "id": str(instance.id) if instance.id else None,
            "machine_type": instance.machine_type,
            "status": instance.status,
            "zone": instance.zone,
            "labels": dict(instance.labels) if instance.labels else {},
            "creation_timestamp": instance.creation_timestamp,
            "network_interfaces": [
                {
                    "network": ni.network,
                    "subnetwork": ni.subnetwork,
                    "network_ip": ni.network_ip,
                }
                for ni in (instance.network_interfaces or [])
            ],
            "disks": [
                {
                    "source": disk.source,
                    "boot": disk.boot,
                    "mode": disk.mode,
                }
                for disk in (instance.disks or [])
            ],
            "service_accounts": [
                {"email": sa.email, "scopes": list(sa.scopes) if sa.scopes else []}
                for sa in (instance.service_accounts or [])
            ],
            "tags": list(instance.tags.items) if instance.tags and instance.tags.items else [],
        }

    def get_gke_clusters(self) -> List[Dict[str, Any]]:
        """Get information about GKE clusters.

        :return: List of GKE cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters: List[Dict[str, Any]] = []
        try:
            from google.cloud import container_v1

            client = container_v1.ClusterManagerClient()
            project = self._get_project_id()

            if not project:
                logger.warning("No project ID available for GKE clusters collection")
                return clusters

            parent = f"projects/{project}/locations/-"
            response = client.list_clusters(parent=parent)

            for cluster in response.clusters:
                labels = dict(cluster.resource_labels) if cluster.resource_labels else {}
                if self._matches_labels(labels):
                    clusters.append(self._parse_gke_cluster(cluster))

        except Exception as e:
            self._handle_error(e, "GKE clusters")

        return clusters

    def _parse_gke_cluster(self, cluster: Any) -> Dict[str, Any]:
        """Parse a GKE cluster to a dictionary.

        :param cluster: GKE cluster object
        :return: Parsed cluster data
        :rtype: Dict[str, Any]
        """
        return {
            "name": cluster.name,
            "location": cluster.location,
            "status": self._get_enum_name(cluster.status),
            "current_node_count": cluster.current_node_count,
            "current_master_version": cluster.current_master_version,
            "resource_labels": dict(cluster.resource_labels) if cluster.resource_labels else {},
            "network": cluster.network,
            "subnetwork": cluster.subnetwork,
            "endpoint": cluster.endpoint,
            "cluster_ipv4_cidr": cluster.cluster_ipv4_cidr,
            "node_pools": self._parse_node_pools(cluster.node_pools),
        }

    def _parse_node_pools(self, node_pools: Any) -> List[Dict[str, Any]]:
        """Parse node pools from a GKE cluster.

        :param node_pools: List of node pool objects
        :return: List of parsed node pool data
        :rtype: List[Dict[str, Any]]
        """
        if not node_pools:
            return []
        result: List[Dict[str, Any]] = []
        for np in node_pools:
            machine_type = np.config.machine_type if np.config else None
            result.append(
                {
                    "name": np.name,
                    "initial_node_count": np.initial_node_count,
                    "machine_type": machine_type,
                }
            )
        return result

    def get_cloud_run_services(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Run services.

        :return: List of Cloud Run service information
        :rtype: List[Dict[str, Any]]
        """
        services: List[Dict[str, Any]] = []
        try:
            from google.cloud import run_v2

            client = run_v2.ServicesClient()
            project = self._get_project_id()

            if not project:
                logger.warning("No project ID available for Cloud Run services collection")
                return services

            parent = f"projects/{project}/locations/-"
            request = run_v2.ListServicesRequest(parent=parent)

            for service in client.list_services(request=request):
                labels = dict(service.labels) if service.labels else {}
                if self._matches_labels(labels):
                    services.append(self._parse_cloud_run_service(service, labels))

        except Exception as e:
            self._handle_error(e, "Cloud Run services")

        return services

    def _parse_cloud_run_service(self, service: Any, labels: Dict[str, str]) -> Dict[str, Any]:
        """Parse a Cloud Run service to a dictionary.

        :param service: Cloud Run service object
        :param labels: Pre-extracted labels dictionary
        :return: Parsed service data
        :rtype: Dict[str, Any]
        """
        return {
            "name": service.name,
            "uid": service.uid,
            "uri": service.uri,
            "labels": labels,
            "create_time": service.create_time.isoformat() if service.create_time else None,
            "update_time": service.update_time.isoformat() if service.update_time else None,
            "ingress": self._get_enum_name(service.ingress),
            "launch_stage": self._get_enum_name(service.launch_stage),
        }

    def _get_enum_name(self, enum_value: Any) -> str:
        """Get the name of an enum value, or its string representation.

        :param enum_value: Enum value to get name from
        :return: Name string or string representation
        :rtype: str
        """
        if hasattr(enum_value, "name"):
            return enum_value.name
        return str(enum_value)

    def get_cloud_functions(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Functions.

        :return: List of Cloud Functions information
        :rtype: List[Dict[str, Any]]
        """
        functions: List[Dict[str, Any]] = []
        try:
            from google.cloud import functions_v2

            client = functions_v2.FunctionServiceClient()
            project = self._get_project_id()

            if not project:
                logger.warning("No project ID available for Cloud Functions collection")
                return functions

            parent = f"projects/{project}/locations/-"
            request = functions_v2.ListFunctionsRequest(parent=parent)

            for function in client.list_functions(request=request):
                labels = dict(function.labels) if function.labels else {}
                if self._matches_labels(labels):
                    functions.append(self._parse_cloud_function(function, labels))

        except Exception as e:
            self._handle_error(e, "Cloud Functions")

        return functions

    def _parse_cloud_function(self, function: Any, labels: Dict[str, str]) -> Dict[str, Any]:
        """Parse a Cloud Function to a dictionary.

        :param function: Cloud Function object
        :param labels: Pre-extracted labels dictionary
        :return: Parsed function data
        :rtype: Dict[str, Any]
        """
        return {
            "name": function.name,
            "state": self._get_enum_name(function.state),
            "labels": labels,
            "description": function.description,
            "environment": self._get_enum_name(function.environment),
            "update_time": function.update_time.isoformat() if function.update_time else None,
            "build_config": self._parse_build_config(function.build_config),
        }

    def _parse_build_config(self, build_config: Any) -> Dict[str, Any]:
        """Parse build configuration from a Cloud Function.

        :param build_config: Build configuration object
        :return: Parsed build config data
        :rtype: Dict[str, Any]
        """
        if not build_config:
            return {}
        return {
            "runtime": build_config.runtime,
            "entry_point": build_config.entry_point,
        }

    def get_app_engine_services(self) -> List[Dict[str, Any]]:
        """Get information about App Engine services.

        :return: List of App Engine service information
        :rtype: List[Dict[str, Any]]
        """
        services: List[Dict[str, Any]] = []
        try:
            from googleapiclient.discovery import build

            service = build("appengine", "v1")
            project = self._get_project_id()

            if not project:
                logger.warning("No project ID available for App Engine services collection")
                return services

            request = service.apps().services().list(appsId=project)
            response = request.execute()

            for svc in response.get("services", []):
                services.append(
                    {
                        "name": svc.get("name"),
                        "id": svc.get("id"),
                        "split": svc.get("split"),
                    }
                )

        except Exception as e:
            self._handle_error(e, "App Engine services")

        return services

    def collect(self) -> Dict[str, Any]:
        """Collect compute resources based on enabled_services configuration.

        :return: Dictionary containing enabled compute resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Compute Engine instances
        if self.enabled_services.get("compute_engine", True):
            result["ComputeInstances"] = self.get_compute_instances()

        # GKE Clusters
        if self.enabled_services.get("gke", True):
            result["GKEClusters"] = self.get_gke_clusters()

        # Cloud Run Services
        if self.enabled_services.get("cloud_run", True):
            result["CloudRunServices"] = self.get_cloud_run_services()

        # Cloud Functions
        if self.enabled_services.get("cloud_functions", True):
            result["CloudFunctions"] = self.get_cloud_functions()

        # App Engine Services
        if self.enabled_services.get("app_engine", True):
            result["AppEngineServices"] = self.get_app_engine_services()

        return result
