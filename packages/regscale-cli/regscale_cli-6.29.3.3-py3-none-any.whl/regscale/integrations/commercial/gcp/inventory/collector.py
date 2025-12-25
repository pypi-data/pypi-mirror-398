#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Inventory Collector coordinator class.

This module provides the GCPInventoryCollector class that coordinates all
individual resource collectors (compute, storage, networking, etc.) for
GCP resource inventory collection.
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("regscale")

# Log message constant for exception details
_EXCEPTION_DETAILS_LOG_MSG = "Exception details:"


class GCPInventoryCollector:
    """Coordinates all GCP resource collectors for inventory collection.

    This class follows the pattern established by the AWS inventory collector,
    providing a unified interface to collect GCP resources from multiple services.

    Attributes:
        parent: GCP parent resource path (e.g., 'projects/my-proj', 'organizations/123').
        credentials_path: Optional path to service account JSON key file.
        project_id: Optional project ID for filtering resources.
        labels: Dictionary of label key-value pairs for filtering resources.
        enabled_collectors: Dictionary of collector names to boolean flags.
        cache_ttl: Time-to-live for cached results in seconds.
    """

    # Default enabled services configuration
    DEFAULT_ENABLED_SERVICES = {
        "compute": {
            "enabled": True,
            "services": {
                "compute_engine": True,
                "gke": True,
                "cloud_run": True,
                "cloud_functions": True,
                "app_engine": True,
            },
        },
        "storage": {
            "enabled": True,
            "services": {
                "cloud_storage": True,
                "filestore": True,
                "persistent_disk": True,
            },
        },
        "networking": {
            "enabled": True,
            "services": {
                "vpc": True,
                "subnets": True,
                "firewall_rules": True,
                "load_balancers": True,
                "cloud_nat": True,
                "vpn": True,
                "dns": True,
            },
        },
        "security": {
            "enabled": True,
            "services": {
                "scc_findings": True,
                "security_health_analytics": True,
            },
        },
        "iam": {
            "enabled": True,
            "services": {
                "iam_policies": True,
                "service_accounts": True,
                "roles": True,
            },
        },
        "databases": {
            "enabled": True,
            "services": {
                "cloud_sql": True,
                "spanner": True,
                "bigtable": True,
                "firestore": True,
                "memorystore": True,
            },
        },
        "kms": {
            "enabled": True,
            "services": {
                "key_rings": True,
                "crypto_keys": True,
            },
        },
        "logging": {
            "enabled": True,
            "services": {
                "log_sinks": True,
                "log_metrics": True,
                "audit_logs": True,
            },
        },
    }

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_collectors: Optional[Dict[str, bool]] = None,
        cache_ttl: int = 300,
    ) -> None:
        """Initialize the GCP inventory collector.

        :param str parent: GCP parent resource path (e.g., 'projects/my-proj',
                          'organizations/123456', 'folders/987654')
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering resources
        :param Optional[Dict[str, str]] labels: Dictionary of label key-value pairs
                                                for filtering resources
        :param Optional[Dict[str, bool]] enabled_collectors: Dictionary of collector
                                                              names to boolean flags
        :param int cache_ttl: Time-to-live for cached results in seconds (default: 300)
        """
        self.parent = parent
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.labels = labels or {}
        self.cache_ttl = cache_ttl
        self.enabled_services = self._get_enabled_services(enabled_collectors)

        # Cache for collected results
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}

        # Lazy-loaded collector instances
        self._compute: Optional[Any] = None
        self._storage: Optional[Any] = None
        self._networking: Optional[Any] = None
        self._security: Optional[Any] = None
        self._iam: Optional[Any] = None
        self._databases: Optional[Any] = None
        self._kms: Optional[Any] = None
        self._logging: Optional[Any] = None

    def _get_enabled_services(self, enabled_collectors: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get enabled services configuration with support for nested structure.

        Supports both simple (category: bool) and nested (category: {enabled: bool, services: {...}}) formats.

        :param Optional[Dict[str, Any]] enabled_collectors: Optional dictionary of collector names
                                                            to boolean flags or nested config
        :return: Dictionary of service configurations
        :rtype: Dict[str, Any]
        """
        default_services = self.DEFAULT_ENABLED_SERVICES.copy()

        # If no config provided, return defaults
        if enabled_collectors is None:
            return default_services

        # Process configuration - support both simple and nested formats
        merged_config = {}
        for category, default_value in default_services.items():
            if category not in enabled_collectors:
                # Category not specified, use default
                merged_config[category] = default_value
            elif isinstance(enabled_collectors[category], bool):
                # Simple format: compute: true/false
                # Convert to nested format with all services matching the category setting
                merged_config[category] = {
                    "enabled": enabled_collectors[category],
                    "services": {
                        service: enabled_collectors[category] for service in default_value.get("services", {}).keys()
                    },
                }
            elif isinstance(enabled_collectors[category], dict):
                # Nested format: compute: {enabled: true, services: {...}}
                category_config = enabled_collectors[category]
                enabled_flag = category_config.get("enabled", True)
                provided_services = category_config.get("services", {})

                # Merge provided services with defaults
                merged_services = default_value.get("services", {}).copy()
                merged_services.update(provided_services)

                merged_config[category] = {"enabled": enabled_flag, "services": merged_services}
            else:
                # Invalid format, use default
                logger.warning("Invalid configuration format for category '%s', using defaults", category)
                merged_config[category] = default_value

        # Log disabled categories and services
        disabled_categories = [name for name, config in merged_config.items() if not config.get("enabled", True)]
        if disabled_categories:
            logger.info("GCP inventory collection disabled for categories: %s", ", ".join(disabled_categories))

        for category, config in merged_config.items():
            if config.get("enabled", True):
                disabled_services = [service for service, enabled in config.get("services", {}).items() if not enabled]
                if disabled_services:
                    logger.info(
                        "GCP inventory collection disabled for %s services: %s", category, ", ".join(disabled_services)
                    )

        return merged_config

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid based on TTL.

        :param str cache_key: Key for the cached data
        :return: True if cache is valid, False otherwise
        :rtype: bool
        """
        if cache_key not in self._cache:
            return False
        if cache_key not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[cache_key]) < self.cache_ttl

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if valid.

        :param str cache_key: Key for the cached data
        :return: Cached data if valid, None otherwise
        :rtype: Optional[Dict[str, Any]]
        """
        if self._is_cache_valid(cache_key):
            logger.debug("Using cached data for %s", cache_key)
            return self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store data in cache with timestamp.

        :param str cache_key: Key for the cached data
        :param Dict[str, Any] data: Data to cache
        """
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.debug("GCP inventory cache cleared")

    @property
    def compute(self) -> Optional[Any]:
        """Get the compute collector (lazy-loaded).

        :return: ComputeCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._compute is None and self.enabled_services.get("compute", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.compute import ComputeCollector

            compute_config = self.enabled_services.get("compute", {"enabled": True, "services": {}})
            self._compute = ComputeCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=compute_config.get("services", {}),
            )
        return self._compute

    @property
    def storage(self) -> Optional[Any]:
        """Get the storage collector (lazy-loaded).

        :return: StorageCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._storage is None and self.enabled_services.get("storage", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.storage import StorageCollector

            storage_config = self.enabled_services.get("storage", {"enabled": True, "services": {}})
            self._storage = StorageCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=storage_config.get("services", {}),
            )
        return self._storage

    @property
    def networking(self) -> Optional[Any]:
        """Get the networking collector (lazy-loaded).

        :return: NetworkingCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._networking is None and self.enabled_services.get("networking", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.networking import NetworkingCollector

            networking_config = self.enabled_services.get("networking", {"enabled": True, "services": {}})
            self._networking = NetworkingCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=networking_config.get("services", {}),
            )
        return self._networking

    @property
    def security(self) -> Optional[Any]:
        """Get the security collector (lazy-loaded).

        :return: SecurityCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._security is None and self.enabled_services.get("security", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.security import SecurityCollector

            security_config = self.enabled_services.get("security", {"enabled": True, "services": {}})
            self._security = SecurityCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=security_config.get("services", {}),
            )
        return self._security

    @property
    def iam(self) -> Optional[Any]:
        """Get the IAM collector (lazy-loaded).

        :return: IAMCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._iam is None and self.enabled_services.get("iam", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.iam import IAMCollector

            iam_config = self.enabled_services.get("iam", {"enabled": True, "services": {}})
            self._iam = IAMCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=iam_config.get("services", {}),
            )
        return self._iam

    @property
    def databases(self) -> Optional[Any]:
        """Get the databases collector (lazy-loaded).

        :return: DatabaseCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._databases is None and self.enabled_services.get("databases", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.database import DatabaseCollector

            databases_config = self.enabled_services.get("databases", {"enabled": True, "services": {}})
            self._databases = DatabaseCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=databases_config.get("services", {}),
            )
        return self._databases

    @property
    def kms(self) -> Optional[Any]:
        """Get the KMS collector (lazy-loaded).

        :return: KMSCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._kms is None and self.enabled_services.get("kms", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.kms import KMSCollector

            kms_config = self.enabled_services.get("kms", {"enabled": True, "services": {}})
            self._kms = KMSCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=kms_config.get("services", {}),
            )
        return self._kms

    @property
    def logging_collector(self) -> Optional[Any]:
        """Get the logging collector (lazy-loaded).

        Named logging_collector to avoid conflict with logging module.

        :return: LoggingCollector instance if enabled, None otherwise
        :rtype: Optional[Any]
        """
        if self._logging is None and self.enabled_services.get("logging", {}).get("enabled", True):
            from regscale.integrations.commercial.gcp.inventory.resources.logging import LoggingCollector

            logging_config = self.enabled_services.get("logging", {"enabled": True, "services": {}})
            self._logging = LoggingCollector(
                parent=self.parent,
                credentials_path=self.credentials_path,
                project_id=self.project_id,
                labels=self.labels,
                enabled_services=logging_config.get("services", {}),
            )
        return self._logging

    def collect_all(self) -> Dict[str, Any]:
        """Collect all GCP resources from enabled collectors.

        Results are cached based on cache_ttl setting.

        :return: Dictionary containing all GCP resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "all"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        inventory: Dict[str, Any] = {}
        collectors = [
            ("compute", self.compute),
            ("storage", self.storage),
            ("networking", self.networking),
            ("security", self.security),
            ("iam", self.iam),
            ("databases", self.databases),
            ("kms", self.kms),
            ("logging", self.logging_collector),
        ]

        # Filter out None collectors (disabled services)
        active_collectors = [(name, c) for name, c in collectors if c is not None]

        logger.info("Collecting GCP inventory from %d enabled collector(s)", len(active_collectors))

        for name, collector in active_collectors:
            try:
                logger.debug("Collecting resources from %s collector", name)
                resources = collector.collect()
                inventory.update(resources)
            except Exception as e:
                logger.error("Error collecting resource(s) from %s collector: %s", name, str(e))
                logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)

        self._set_cache(cache_key, inventory)
        return inventory

    def collect_compute(self) -> Dict[str, Any]:
        """Run only the compute collector.

        :return: Dictionary containing compute resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "compute"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.compute is None:
            logger.warning("Compute collector is disabled")
            return {}

        try:
            result = self.compute.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting compute resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_storage(self) -> Dict[str, Any]:
        """Run only the storage collector.

        :return: Dictionary containing storage resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "storage"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.storage is None:
            logger.warning("Storage collector is disabled")
            return {}

        try:
            result = self.storage.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting storage resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_networking(self) -> Dict[str, Any]:
        """Run only the networking collector.

        :return: Dictionary containing networking resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "networking"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.networking is None:
            logger.warning("Networking collector is disabled")
            return {}

        try:
            result = self.networking.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting networking resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_security(self) -> Dict[str, Any]:
        """Run only the security collector.

        :return: Dictionary containing security resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "security"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.security is None:
            logger.warning("Security collector is disabled")
            return {}

        try:
            result = self.security.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting security resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_iam(self) -> Dict[str, Any]:
        """Run only the IAM collector.

        :return: Dictionary containing IAM resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "iam"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.iam is None:
            logger.warning("IAM collector is disabled")
            return {}

        try:
            result = self.iam.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting IAM resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_databases(self) -> Dict[str, Any]:
        """Run only the database collector.

        :return: Dictionary containing database resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "databases"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.databases is None:
            logger.warning("Database collector is disabled")
            return {}

        try:
            result = self.databases.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting database resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_kms(self) -> Dict[str, Any]:
        """Run only the KMS collector.

        :return: Dictionary containing KMS resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "kms"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.kms is None:
            logger.warning("KMS collector is disabled")
            return {}

        try:
            result = self.kms.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting KMS resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def collect_logging(self) -> Dict[str, Any]:
        """Run only the logging collector.

        :return: Dictionary containing logging resource information
        :rtype: Dict[str, Any]
        """
        cache_key = "logging"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        if self.logging_collector is None:
            logger.warning("Logging collector is disabled")
            return {}

        try:
            result = self.logging_collector.collect()
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error("Error collecting logging resources: %s", str(e))
            logger.debug(_EXCEPTION_DETAILS_LOG_MSG, exc_info=True)
            return {}

    def get_all_asset_types(self) -> List[str]:
        """Return combined list of all supported GCP asset types from all collectors.

        :return: List of all supported GCP asset types
        :rtype: List[str]
        """
        all_types: List[str] = []

        # Import collectors to get their supported asset types
        collectors_to_check = [
            ("compute", "regscale.integrations.commercial.gcp.inventory.resources.compute", "ComputeCollector"),
            ("storage", "regscale.integrations.commercial.gcp.inventory.resources.storage", "StorageCollector"),
            (
                "networking",
                "regscale.integrations.commercial.gcp.inventory.resources.networking",
                "NetworkingCollector",
            ),
            ("security", "regscale.integrations.commercial.gcp.inventory.resources.security", "SecurityCollector"),
            ("iam", "regscale.integrations.commercial.gcp.inventory.resources.iam", "IAMCollector"),
            ("databases", "regscale.integrations.commercial.gcp.inventory.resources.database", "DatabaseCollector"),
            ("kms", "regscale.integrations.commercial.gcp.inventory.resources.kms", "KMSCollector"),
            ("logging", "regscale.integrations.commercial.gcp.inventory.resources.logging", "LoggingCollector"),
        ]

        for category, module_path, class_name in collectors_to_check:
            if not self.enabled_services.get(category, {}).get("enabled", True):
                continue

            try:
                import importlib

                module = importlib.import_module(module_path)
                collector_class = getattr(module, class_name)
                if hasattr(collector_class, "supported_asset_types"):
                    all_types.extend(collector_class.supported_asset_types)
            except (ImportError, AttributeError) as e:
                logger.debug("Could not load asset types from %s: %s", class_name, str(e))

        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for asset_type in all_types:
            if asset_type not in seen:
                seen.add(asset_type)
                unique_types.append(asset_type)

        return unique_types


def collect_all_inventory(
    parent: str,
    credentials_path: Optional[str] = None,
    project_id: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
    enabled_collectors: Optional[Dict[str, bool]] = None,
    cache_ttl: int = 300,
) -> Dict[str, Any]:
    """Collect inventory of all GCP resources.

    Convenience function that creates a GCPInventoryCollector and runs collect_all().

    :param str parent: GCP parent resource path
    :param Optional[str] credentials_path: Path to service account JSON key file
    :param Optional[str] project_id: GCP project ID for filtering resources
    :param Optional[Dict[str, str]] labels: Dictionary of label key-value pairs for filtering
    :param Optional[Dict[str, bool]] enabled_collectors: Dictionary of collector names to boolean flags
    :param int cache_ttl: Time-to-live for cached results in seconds
    :return: Dictionary containing all GCP resource information
    :rtype: Dict[str, Any]
    """
    collector = GCPInventoryCollector(
        parent=parent,
        credentials_path=credentials_path,
        project_id=project_id,
        labels=labels,
        enabled_collectors=enabled_collectors,
        cache_ttl=cache_ttl,
    )
    return collector.collect_all()
