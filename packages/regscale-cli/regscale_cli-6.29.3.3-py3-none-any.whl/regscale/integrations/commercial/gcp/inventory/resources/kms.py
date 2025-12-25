#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP KMS resource collectors.

This module provides collectors for GCP Cloud KMS resources including:
- Key Rings
- Crypto Keys
- Crypto Key Versions
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class KMSCollector(BaseCollector):
    """Collector for GCP Cloud KMS resources."""

    # GCP asset types for KMS resources
    supported_asset_types: List[str] = [
        "cloudkms.googleapis.com/KeyRing",
        "cloudkms.googleapis.com/CryptoKey",
        "cloudkms.googleapis.com/CryptoKeyVersion",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the KMS collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def _get_kms_client(self) -> Any:
        """Get a Cloud KMS client with optional credentials.

        :return: KeyManagementServiceClient instance
        :rtype: Any
        """
        from google.cloud import kms_v1

        if self.credentials_path:
            return kms_v1.KeyManagementServiceClient.from_service_account_json(self.credentials_path)
        return kms_v1.KeyManagementServiceClient()

    def _get_locations(self, project: str) -> List[str]:
        """Get available KMS locations for a project.

        :param str project: GCP project ID
        :return: List of location names
        :rtype: List[str]
        """
        locations = []
        try:
            from google.cloud import kms_v1

            client = self._get_kms_client()
            parent = f"projects/{project}"

            # List locations using the locations client
            request = kms_v1.ListLocationsRequest(name=parent)
            for location in client.list_locations(request=request):
                locations.append(location.name)

        except Exception as e:
            # If listing locations fails, use common locations
            logger.debug("Could not list KMS locations, using common locations: %s", str(e))
            common_locations = [
                "global",
                "us",
                "us-central1",
                "us-east1",
                "us-east4",
                "us-west1",
                "us-west2",
                "europe",
                "europe-west1",
                "europe-west2",
                "asia",
                "asia-east1",
                "asia-southeast1",
            ]
            locations = [f"projects/{project}/locations/{loc}" for loc in common_locations]

        return locations

    def get_key_rings(self) -> List[Dict[str, Any]]:
        """Get information about Cloud KMS key rings.

        :return: List of key ring information
        :rtype: List[Dict[str, Any]]
        """
        key_rings = []
        try:
            from google.cloud import kms_v1

            client = self._get_kms_client()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for KMS key rings collection")
                return key_rings

            locations = self._get_locations(project)

            for location in locations:
                try:
                    # Ensure location format is correct
                    if not location.startswith("projects/"):
                        location_parent = f"projects/{project}/locations/{location}"
                    else:
                        location_parent = location

                    request = kms_v1.ListKeyRingsRequest(parent=location_parent)

                    for key_ring in client.list_key_rings(request=request):
                        key_rings.append(self._parse_key_ring(key_ring))

                except Exception as loc_error:
                    # Skip locations where KMS is not enabled or accessible
                    logger.debug("Could not list key rings in location %s: %s", location, str(loc_error))
                    continue

        except Exception as e:
            self._handle_error(e, "KMS key rings")

        return key_rings

    def _parse_key_ring(self, key_ring: Any) -> Dict[str, Any]:
        """Parse a Cloud KMS key ring to a dictionary.

        :param key_ring: KeyRing object
        :return: Parsed key ring data
        :rtype: Dict[str, Any]
        """
        return {
            "name": key_ring.name,
            "create_time": key_ring.create_time.isoformat() if key_ring.create_time else None,
        }

    def get_crypto_keys(self) -> List[Dict[str, Any]]:
        """Get information about Cloud KMS crypto keys for all key rings.

        :return: List of crypto key information
        :rtype: List[Dict[str, Any]]
        """
        crypto_keys = []
        try:
            from google.cloud import kms_v1

            client = self._get_kms_client()

            # First get all key rings
            key_rings = self.get_key_rings()

            for key_ring in key_rings:
                try:
                    key_ring_name = key_ring.get("name")
                    if not key_ring_name:
                        continue

                    request = kms_v1.ListCryptoKeysRequest(parent=key_ring_name)

                    for crypto_key in client.list_crypto_keys(request=request):
                        # Check label filter if labels are present on the key
                        key_labels = dict(crypto_key.labels) if crypto_key.labels else {}
                        if not self._matches_labels(key_labels):
                            continue

                        crypto_keys.append(self._parse_crypto_key(crypto_key))

                except Exception as ring_error:
                    logger.debug("Could not list crypto keys in key ring %s: %s", key_ring.get("name"), str(ring_error))
                    continue

        except Exception as e:
            self._handle_error(e, "KMS crypto keys")

        return crypto_keys

    def _extract_enum_value(self, obj: Any, attr_name: str) -> Optional[str]:
        """Extract an enum value as string from an object attribute.

        :param obj: Object containing the attribute
        :param attr_name: Name of the attribute to extract
        :return: String representation of the enum value or None
        :rtype: Optional[str]
        """
        attr = getattr(obj, attr_name, None)
        if attr is None:
            return None
        return attr.name if hasattr(attr, "name") else str(attr)

    def _extract_primary_algorithm(self, crypto_key: Any) -> Optional[str]:
        """Extract the primary algorithm from a crypto key.

        :param crypto_key: CryptoKey object
        :return: String representation of the primary algorithm or None
        :rtype: Optional[str]
        """
        if not crypto_key.primary or not crypto_key.primary.algorithm:
            return None
        algorithm = crypto_key.primary.algorithm
        return algorithm.name if hasattr(algorithm, "name") else str(algorithm)

    def _extract_version_template(self, crypto_key: Any) -> Optional[Dict[str, Any]]:
        """Extract version template information from a crypto key.

        :param crypto_key: CryptoKey object
        :return: Dictionary with version template data or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not crypto_key.version_template:
            return None
        template = crypto_key.version_template
        algorithm = self._extract_enum_value(template, "algorithm") if template.algorithm else None
        protection_level = self._extract_enum_value(template, "protection_level") if template.protection_level else None
        return {"algorithm": algorithm, "protection_level": protection_level}

    def _parse_crypto_key(self, crypto_key: Any) -> Dict[str, Any]:
        """Parse a Cloud KMS crypto key to a dictionary.

        :param crypto_key: CryptoKey object
        :return: Parsed crypto key data
        :rtype: Dict[str, Any]
        """
        purpose = self._extract_enum_value(crypto_key, "purpose")
        primary_state = self._extract_enum_value(crypto_key.primary, "state") if crypto_key.primary else None
        rotation_period = str(crypto_key.rotation_period) if crypto_key.rotation_period else None
        next_rotation_time = crypto_key.next_rotation_time.isoformat() if crypto_key.next_rotation_time else None
        create_time = crypto_key.create_time.isoformat() if crypto_key.create_time else None
        destroy_duration = str(crypto_key.destroy_scheduled_duration) if crypto_key.destroy_scheduled_duration else None
        import_only = crypto_key.import_only if hasattr(crypto_key, "import_only") else False

        return {
            "name": crypto_key.name,
            "purpose": purpose,
            "primary_state": primary_state,
            "primary_algorithm": self._extract_primary_algorithm(crypto_key),
            "rotation_period": rotation_period,
            "next_rotation_time": next_rotation_time,
            "create_time": create_time,
            "labels": dict(crypto_key.labels) if crypto_key.labels else {},
            "version_template": self._extract_version_template(crypto_key),
            "destroy_scheduled_duration": destroy_duration,
            "import_only": import_only,
        }

    def get_crypto_key_versions(self, crypto_key_name: str) -> List[Dict[str, Any]]:
        """Get information about crypto key versions for a specific crypto key.

        :param str crypto_key_name: Full resource name of the crypto key
        :return: List of crypto key version information
        :rtype: List[Dict[str, Any]]
        """
        versions = []
        try:
            from google.cloud import kms_v1

            client = self._get_kms_client()
            request = kms_v1.ListCryptoKeyVersionsRequest(parent=crypto_key_name)

            for version in client.list_crypto_key_versions(request=request):
                versions.append(self._parse_crypto_key_version(version))

        except Exception as e:
            self._handle_error(e, "KMS crypto key versions")

        return versions

    def _extract_external_protection_options(self, version: Any) -> Optional[Dict[str, Any]]:
        """Extract external protection level options from a crypto key version.

        :param version: CryptoKeyVersion object
        :return: Dictionary with external protection options or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not version.external_protection_level_options:
            return None
        if not version.external_protection_level_options.external_key_uri:
            return None
        return {"external_key_uri": version.external_protection_level_options.external_key_uri}

    def _parse_crypto_key_version(self, version: Any) -> Dict[str, Any]:
        """Parse a crypto key version to a dictionary.

        :param version: CryptoKeyVersion object
        :return: Parsed crypto key version data
        :rtype: Dict[str, Any]
        """
        state = self._extract_enum_value(version, "state")
        algorithm = self._extract_enum_value(version, "algorithm")
        protection_level = self._extract_enum_value(version, "protection_level")

        return {
            "name": version.name,
            "state": state,
            "algorithm": algorithm,
            "protection_level": protection_level,
            "create_time": version.create_time.isoformat() if version.create_time else None,
            "generate_time": version.generate_time.isoformat() if version.generate_time else None,
            "destroy_time": version.destroy_time.isoformat() if version.destroy_time else None,
            "destroy_event_time": version.destroy_event_time.isoformat() if version.destroy_event_time else None,
            "import_time": version.import_time.isoformat() if version.import_time else None,
            "import_job": version.import_job if version.import_job else None,
            "external_protection_level_options": self._extract_external_protection_options(version),
        }

    def collect(self) -> Dict[str, Any]:
        """Collect KMS resources based on enabled_services configuration.

        :return: Dictionary containing enabled KMS resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Key Rings
        if self.enabled_services.get("kms_key_rings", True):
            result["KeyRings"] = self.get_key_rings()

        # Crypto Keys
        if self.enabled_services.get("kms_crypto_keys", True):
            result["CryptoKeys"] = self.get_crypto_keys()

        return result
