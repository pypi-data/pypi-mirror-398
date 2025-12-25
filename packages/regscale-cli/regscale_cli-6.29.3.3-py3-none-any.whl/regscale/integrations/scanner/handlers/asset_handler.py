#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Asset handler for scanner integrations.

This module provides the AssetHandler class which handles all asset-related
operations extracted from scanner_integration.py. The handler manages:
- Processing integration assets
- Creating/updating assets in RegScale
- Converting IntegrationAsset to RegScale Asset
- Asset lookup by identifier via AssetCache

The handler accepts a ScannerContext for shared state and an AssetCache
for efficient asset lookups.
"""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.durosuite.process_devices import scan_durosuite_devices
from regscale.integrations.commercial.durosuite.variables import DuroSuiteVariables
from regscale.integrations.scanner.cache import AssetCache
from regscale.integrations.scanner.models import IntegrationAsset
from regscale.integrations.scanner.utils import _retry_with_backoff
from regscale.models import DateTimeEncoder, regscale_models
from regscale.models.regscale_models.batch_options import AssetBatchOptions

if TYPE_CHECKING:
    from rich.progress import TaskID

    from regscale.integrations.scanner.context import ScannerContext

logger = logging.getLogger("regscale")


# Valid asset types supported by RegScale
VALID_ASSET_TYPES = [
    "Physical Server",
    "Virtual Machine (VM)",
    "Appliance",
    "Network Router",
    "Network Switch",
    "Firewall",
    "Desktop",
    "Laptop",
    "Tablet",
    "Phone",
    "Other",
]


class AssetHandler:
    """
    Handler for asset-related operations in scanner integrations.

    This class encapsulates asset processing logic that was previously in
    ScannerIntegration, enabling better separation of concerns and easier testing.

    The handler uses:
    - ScannerContext for shared configuration and state
    - AssetCache for efficient asset lookups by identifier

    Example usage:
        context = ScannerContext(plan_id=123)
        cache = AssetCache(plan_id=123, parent_module="securityplans")
        handler = AssetHandler(context, cache)

        for asset in integration_assets:
            handler.process_asset(asset, progress_task_id)
    """

    def __init__(self, context: "ScannerContext", asset_cache: AssetCache) -> None:
        """
        Initialize the asset handler.

        :param ScannerContext context: The scanner context containing shared state
        :param AssetCache asset_cache: The asset cache for lookups
        """
        self.context = context
        self.asset_cache = asset_cache

    def process_asset(
        self,
        asset: IntegrationAsset,
        loading_assets: Optional["TaskID"] = None,
    ) -> None:
        """
        Safely process a single asset in a concurrent environment.

        This method ensures thread safety by utilizing the context's lock registry.
        It assigns default values to the asset if necessary, maps the asset to
        components if specified, and updates the progress of asset loading.
        (Thread Safe)

        :param IntegrationAsset asset: The integration asset to be processed.
        :param Optional[TaskID] loading_assets: The identifier for the task tracking progress.
        :rtype: None
        """
        # Assign default values to the asset if they are not already set
        asset = self._set_asset_defaults(asset)

        # If mapping assets to components is enabled and the asset has associated component names,
        # attempt to update or create each asset under its respective component
        if any(asset.component_names):
            for component_name in asset.component_names:
                self.update_or_create_asset(asset, component_name)
        else:
            # If no component mapping is required, add the asset directly without a component
            self.update_or_create_asset(asset, None)

        # Update progress if tracking
        if loading_assets is not None and self.context.asset_progress:
            if self.context.num_assets_to_process and self.context.asset_progress.tasks[loading_assets].total != float(
                self.context.num_assets_to_process
            ):
                self.context.asset_progress.update(
                    loading_assets,
                    total=self.context.num_assets_to_process,
                    description=(
                        f"[#f8b737]Creating and updating {self.context.num_assets_to_process} "
                        f"assets from {self.context.title}."
                    ),
                )
            self.context.asset_progress.advance(loading_assets, 1)

    def update_or_create_asset(
        self,
        asset: IntegrationAsset,
        component_name: Optional[str] = None,
    ) -> None:
        """
        Update or create an asset in RegScale.

        This method either updates an existing asset or creates a new one within a
        thread-safe manner. It handles the asset's association with a component,
        creating the component if it does not exist.
        (Thread Safe)

        :param IntegrationAsset asset: The asset to be updated or created.
        :param Optional[str] component_name: The name of the component to associate with.
                                            If None, asset is added without component association.
        """
        if not asset.identifier:
            logger.warning("Asset has no identifier, skipping")
            return

        # Get or create component if needed
        component = self._get_or_create_component_for_asset(asset, component_name)

        # Create or update the asset
        created, existing_or_new_asset = self.create_new_asset(asset, component=None)

        # Handle component mapping and DuroSuite processing
        self._handle_component_mapping_and_durosuite(existing_or_new_asset, component, asset, created)

    def create_new_asset(
        self, asset: IntegrationAsset, component: Optional[regscale_models.Component]
    ) -> Tuple[bool, Optional[regscale_models.Asset]]:
        """
        Create a new asset in the system based on the provided integration asset details.

        Associates the asset with a component or directly with the security plan.

        :param IntegrationAsset asset: The integration asset from which the new asset will be created.
        :param Optional[regscale_models.Component] component: The component to link the asset to, or None.
        :return: Tuple of (was_created, newly created asset instance).
        :rtype: Tuple[bool, Optional[regscale_models.Asset]]
        """
        if not self._validate_asset_requirements(asset):
            return False, None

        asset_type = self._validate_and_map_asset_type(asset.asset_type)
        other_tracking_number = self._prepare_tracking_number(asset)
        field_data = self._prepare_truncated_asset_fields(asset, other_tracking_number)

        new_asset = self._create_regscale_asset_model(asset, component, asset_type, field_data)

        status, new_asset = new_asset.create_or_update_with_status(bulk_update=True)
        created = status == "created"

        # Update cache with the new/updated asset
        self.asset_cache.add_by_identifier(asset.identifier, new_asset)
        logger.debug("Created new asset with identifier %s", asset.identifier)

        self._handle_software_and_stig_processing(new_asset, asset, created)
        return created, new_asset

    def convert_to_regscale_asset(self, asset: IntegrationAsset) -> regscale_models.Asset:
        """
        Convert an IntegrationAsset to a RegScale Asset model.

        This method performs the conversion without creating/updating in RegScale.
        Useful for bulk operations where assets are batched before saving.

        :param IntegrationAsset asset: The integration asset to convert.
        :return: The converted RegScale Asset model.
        :rtype: regscale_models.Asset
        """
        asset = self._set_asset_defaults(asset)
        asset_type = self._validate_and_map_asset_type(asset.asset_type)
        other_tracking_number = self._prepare_tracking_number(asset)
        field_data = self._prepare_truncated_asset_fields(asset, other_tracking_number)

        return self._create_regscale_asset_model(asset, None, asset_type, field_data)

    def get_asset_by_identifier(self, identifier: str) -> Optional[regscale_models.Asset]:
        """
        Find an asset by its identifier.

        Delegates to the AssetCache for efficient lookup with fallback support.

        :param str identifier: The identifier of the asset to find.
        :return: The asset if found, None otherwise.
        :rtype: Optional[regscale_models.Asset]
        """
        return self.asset_cache.get_by_identifier(identifier)

    def _set_asset_defaults(self, asset: IntegrationAsset) -> IntegrationAsset:
        """
        Set default values for the asset.
        (Thread Safe)

        :param IntegrationAsset asset: The integration asset
        :return: The asset with defaults applied
        :rtype: IntegrationAsset
        """
        if not asset.asset_owner_id:
            asset.asset_owner_id = self._get_assessor_id()
        if not asset.status:
            asset.status = regscale_models.AssetStatus.Active
        return asset

    def _get_assessor_id(self) -> str:
        """
        Get the ID of the assessor from context or from RegScale.

        :return: The assessor ID
        :rtype: str
        """
        if self.context.assessor_id:
            return self.context.assessor_id
        return regscale_models.Issue.get_user_id() or "Unknown"

    def _get_or_create_component_for_asset(
        self, asset: IntegrationAsset, component_name: Optional[str]
    ) -> Optional[regscale_models.Component]:
        """
        Get or create a component for the asset if component_name is provided.

        :param IntegrationAsset asset: The asset being processed
        :param Optional[str] component_name: Name of the component to associate with
        :return: The component object or None
        :rtype: Optional[regscale_models.Component]
        """
        if not component_name:
            return self.context.component if self.context.is_component else None

        component = self.context.component if self.context.is_component else None
        component = component or self.context.components_by_title.get(component_name)

        if not component:
            component = self._create_new_component(asset, component_name)

        self._handle_component_mapping(component)
        self.context.components_by_title[component_name] = component
        return component

    def _get_compliance_settings_id(self) -> Optional[int]:
        """
        Get the compliance settings ID from the security plan.

        :return: The compliance settings ID if available
        :rtype: Optional[int]
        """
        try:
            security_plan = regscale_models.SecurityPlan.get_object(object_id=self.context.plan_id)
            if security_plan and hasattr(security_plan, "complianceSettingsId"):
                return security_plan.complianceSettingsId
        except Exception as e:
            logger.debug("Failed to get compliance settings ID from security plan %d: %s", self.context.plan_id, e)
        return None

    def _create_new_component(self, asset: IntegrationAsset, component_name: str) -> regscale_models.Component:
        """
        Create a new component for the asset.

        :param IntegrationAsset asset: The asset being processed
        :param str component_name: Name of the component to create
        :return: The newly created component
        :rtype: regscale_models.Component
        """
        logger.debug("No existing component found with name %s, proceeding to create it...", component_name)
        component = regscale_models.Component(
            title=component_name,
            componentType=asset.component_type,
            securityPlansId=self.context.plan_id,
            description=component_name,
            componentOwnerId=self._get_assessor_id(),
            complianceSettingsId=self._get_compliance_settings_id(),
        ).get_or_create()

        if component is None:
            raise ValueError("Failed to create component with name %s" % component_name)

        self.context.components.append(component)
        return component

    def _handle_component_mapping(self, component: regscale_models.Component) -> None:
        """
        Handle component mapping creation if needed.

        :param regscale_models.Component component: The component to create mapping for
        """
        if not (component.securityPlansId and not self.context.is_component):
            return

        component_mapping = regscale_models.ComponentMapping(
            componentId=component.id,
            securityPlanId=self.context.plan_id,
        )
        mapping_result = component_mapping.get_or_create()

        if mapping_result is None:
            logger.debug(
                "Failed to create or find ComponentMapping for componentId=%d, securityPlanId=%d",
                component.id,
                self.context.plan_id,
            )
        else:
            mapping_id = getattr(mapping_result, "id", "unknown")
            logger.debug("Successfully handled ComponentMapping for componentId=%d, ID=%s", component.id, mapping_id)

    def _handle_component_mapping_and_durosuite(
        self,
        existing_or_new_asset: Optional[regscale_models.Asset],
        component: Optional[regscale_models.Component],
        asset: IntegrationAsset,
        created: bool,
    ) -> None:
        """
        Handle component mapping and DuroSuite scanning after asset creation.

        :param Optional[regscale_models.Asset] existing_or_new_asset: The asset that was created/updated
        :param Optional[regscale_models.Component] component: The associated component, if any
        :param IntegrationAsset asset: The original integration asset
        :param bool created: Whether the asset was newly created
        """
        if existing_or_new_asset and component:
            asset_mapping = regscale_models.AssetMapping(
                assetId=existing_or_new_asset.id,
                componentId=component.id,
            )
            try:
                _retry_with_backoff(
                    operation=asset_mapping.get_or_create_with_status,
                    operation_name="AssetMapping(assetId=%d, componentId=%d)"
                    % (existing_or_new_asset.id, component.id),
                )
            except Exception as e:
                logger.warning(
                    "Failed to create AssetMapping for asset %d to component %d after retries: %s",
                    existing_or_new_asset.id,
                    component.id,
                    e,
                )

        if created and DuroSuiteVariables.duroSuiteEnabled:
            scan_durosuite_devices(asset=asset, plan_id=self.context.plan_id, progress=self.context.asset_progress)

    def _truncate_field(self, value: Optional[str], max_length: int = 450, field_name: str = "") -> Optional[str]:
        """
        Truncate a field to the maximum allowed length to prevent database errors.

        :param Optional[str] value: The value to truncate
        :param int max_length: Maximum allowed length, defaults to 450
        :param str field_name: Name of the field being truncated (for logging)
        :return: Truncated value or None
        :rtype: Optional[str]
        """
        if not value:
            return value

        if len(value) > max_length:
            truncated = value[:max_length]
            logger.warning(
                "Truncated %s field from %d to %d characters for value: %s...",
                field_name or "field",
                len(value),
                max_length,
                truncated[:100],
            )
            return truncated
        return value

    def _validate_asset_requirements(self, asset: IntegrationAsset) -> bool:
        """
        Validate that the asset has required fields for creation.

        :param IntegrationAsset asset: The asset to validate
        :return: True if valid, False otherwise
        :rtype: bool
        """
        if not asset.name:
            logger.warning(
                "Asset name is required for asset creation. Skipping asset creation of asset_type: %s", asset.asset_type
            )
            return False
        return True

    def _validate_and_map_asset_type(self, asset_type: str) -> str:
        """
        Validate and map asset type to valid RegScale values.

        :param str asset_type: The asset type to validate
        :return: The validated asset type
        :rtype: str
        """
        if asset_type not in VALID_ASSET_TYPES:
            logger.debug("Asset type '%s' not in valid types, mapping to 'Other'", asset_type)
            return "Other"
        return asset_type

    def _prepare_tracking_number(self, asset: IntegrationAsset) -> str:
        """
        Prepare and validate the tracking number for asset deduplication.

        :param IntegrationAsset asset: The asset to prepare tracking number for
        :return: The tracking number
        :rtype: str
        """
        other_tracking_number = asset.other_tracking_number or asset.identifier
        if not other_tracking_number:
            logger.warning("No tracking number available for asset %s, using name as fallback", asset.name)
            other_tracking_number = asset.name
        return other_tracking_number

    def _prepare_truncated_asset_fields(self, asset: IntegrationAsset, other_tracking_number: str) -> Dict[str, Any]:
        """
        Prepare and truncate asset fields to prevent database errors.

        :param IntegrationAsset asset: The asset to prepare fields for
        :param str other_tracking_number: The prepared tracking number
        :return: Dictionary of truncated field values
        :rtype: Dict[str, Any]
        """
        max_field_length = 450
        name = self._process_asset_name(asset, max_field_length)

        return {
            "name": name,
            "azure_identifier": self._truncate_field(asset.azure_identifier, max_field_length, "azureIdentifier"),
            "aws_identifier": self._truncate_field(asset.aws_identifier, max_field_length, "awsIdentifier"),
            "google_identifier": self._truncate_field(asset.google_identifier, max_field_length, "googleIdentifier"),
            "other_cloud_identifier": self._truncate_field(
                asset.other_cloud_identifier, max_field_length, "otherCloudIdentifier"
            ),
            "software_name": self._truncate_field(asset.software_name, max_field_length, "softwareName"),
            "other_tracking_number": self._truncate_field(
                other_tracking_number, max_field_length, "otherTrackingNumber"
            ),
        }

    def _process_asset_name(self, asset: IntegrationAsset, max_field_length: int) -> str:
        """
        Process and truncate asset name, handling special cases like Azure resource paths.

        :param IntegrationAsset asset: The asset to process name for
        :param int max_field_length: Maximum field length
        :return: The processed name
        :rtype: str
        """
        name = self._truncate_field(asset.name, max_field_length, "name")

        # For very long Azure resource paths, extract meaningful parts
        if asset.name and len(asset.name) > max_field_length and "/" in asset.name:
            name = self._shorten_azure_resource_path(asset.name, max_field_length)

        return name or "Unknown Asset"

    def _shorten_azure_resource_path(self, full_name: str, max_field_length: int) -> str:
        """
        Shorten long Azure resource paths to meaningful parts.

        :param str full_name: The full Azure resource path
        :param int max_field_length: Maximum field length
        :return: The shortened name
        :rtype: str
        """
        parts = full_name.split("/")
        if len(parts) >= 4:
            # Extract key components from Azure resource path
            resource_group = next(
                (p for i, p in enumerate(parts) if i > 0 and parts[i - 1].lower() == "resourcegroups"), ""
            )
            resource_type = parts[-2] if len(parts) > 1 else ""
            resource_name = parts[-1]

            # Build a shortened but meaningful name
            if resource_group:
                name = "../%s/.../%s/%s" % (resource_group, resource_type, resource_name)
            else:
                name = ".../%s/%s" % (resource_type, resource_name)

            # Ensure it fits within limits
            if len(name) > max_field_length:
                name = name[-(max_field_length):]

            logger.info(
                "Shortened long Azure resource path from %d to %d characters: %s", len(full_name), len(name), name
            )
            return name

        return self._truncate_field(full_name, max_field_length, "name") or full_name[:max_field_length]

    @staticmethod
    def _empty_to_none(value: Optional[str]) -> Optional[str]:
        """
        Convert empty strings to None for API compatibility.

        The API server cannot process empty strings for optional fields,
        so we convert them to None which will be excluded from the payload.

        :param Optional[str] value: The string value to check
        :return: None if the string is empty, otherwise the original value
        :rtype: Optional[str]
        """
        return value if value else None

    def _create_regscale_asset_model(
        self, asset: IntegrationAsset, component: Optional[regscale_models.Component], asset_type: str, field_data: dict
    ) -> regscale_models.Asset:
        """
        Create the RegScale Asset model with all required fields.

        :param IntegrationAsset asset: The integration asset
        :param Optional[regscale_models.Component] component: The component to link to
        :param str asset_type: The validated asset type
        :param dict field_data: The prepared/truncated field data
        :return: The created Asset model
        :rtype: regscale_models.Asset
        """
        new_asset = regscale_models.Asset(
            name=field_data["name"],
            description=self._empty_to_none(asset.description),
            bVirtual=asset.is_virtual,
            otherTrackingNumber=field_data["other_tracking_number"],
            assetOwnerId=asset.asset_owner_id or regscale_models.Asset.get_user_id() or "Unknown",
            parentId=component.id if component else self.context.plan_id,
            parentModule=self.context.parent_module,
            assetType=asset_type,
            dateLastUpdated=asset.date_last_updated or get_current_datetime(),
            status=asset.status,
            assetCategory=asset.asset_category,
            managementType=self._empty_to_none(asset.management_type),
            notes=self._empty_to_none(asset.notes),
            model=self._empty_to_none(asset.model),
            manufacturer=self._empty_to_none(asset.manufacturer),
            serialNumber=self._empty_to_none(asset.serial_number),
            assetTagNumber=self._empty_to_none(asset.asset_tag_number),
            bPublicFacing=asset.is_public_facing,
            azureIdentifier=self._empty_to_none(field_data["azure_identifier"]),
            location=self._empty_to_none(asset.location),
            ipAddress=self._empty_to_none(asset.ip_address),
            iPv6Address=self._empty_to_none(asset.ipv6_address),
            fqdn=self._empty_to_none(asset.fqdn),
            macAddress=self._empty_to_none(asset.mac_address),
            diskStorage=asset.disk_storage,
            cpu=asset.cpu,
            ram=asset.ram or 0,
            operatingSystem=self._empty_to_none(asset.operating_system),
            osVersion=self._empty_to_none(asset.os_version),
            endOfLifeDate=self._empty_to_none(asset.end_of_life_date),
            vlanId=self._empty_to_none(asset.vlan_id),
            uri=self._empty_to_none(asset.uri),
            awsIdentifier=self._empty_to_none(field_data["aws_identifier"]),
            googleIdentifier=self._empty_to_none(field_data["google_identifier"]),
            otherCloudIdentifier=self._empty_to_none(field_data["other_cloud_identifier"]),
            patchLevel=self._empty_to_none(asset.patch_level),
            cpe=self._empty_to_none(asset.cpe),
            softwareVersion=self._empty_to_none(asset.software_version),
            softwareName=self._empty_to_none(field_data["software_name"]),
            softwareVendor=self._empty_to_none(asset.software_vendor),
            bLatestScan=asset.is_latest_scan,
            bAuthenticatedScan=asset.is_authenticated_scan,
            systemAdministratorId=self._empty_to_none(asset.system_administrator_id),
            scanningTool=self._empty_to_none(asset.scanning_tool),
            softwareFunction=self._empty_to_none(asset.software_function),
            baselineConfiguration=self._empty_to_none(asset.baseline_configuration),
        )

        if self.context.asset_identifier_field:
            setattr(new_asset, self.context.asset_identifier_field, asset.identifier)

        return new_asset

    def _handle_software_and_stig_processing(
        self, new_asset: regscale_models.Asset, asset: IntegrationAsset, created: bool
    ) -> None:
        """
        Handle post-asset creation tasks like software inventory and STIG mapping.

        :param regscale_models.Asset new_asset: The newly created/updated asset
        :param IntegrationAsset asset: The original integration asset
        :param bool created: Whether the asset was newly created
        """
        self.handle_software_inventory(new_asset, asset.software_inventory, created)
        self.create_asset_data_and_link(new_asset, asset)
        self.create_or_update_ports_protocol(new_asset, asset)
        if self.context.stig_mapper:
            self.context.stig_mapper.map_associated_stigs_to_asset(asset=new_asset, ssp_id=self.context.plan_id)

    def handle_software_inventory(
        self, new_asset: regscale_models.Asset, software_inventory: List[Dict[str, Any]], created: bool
    ) -> None:
        """
        Handle the software inventory for the asset.

        :param regscale_models.Asset new_asset: The newly created asset
        :param List[Dict[str, Any]] software_inventory: List of software inventory items
        :param bool created: Flag indicating if the asset was newly created
        :rtype: None
        """
        if not software_inventory:
            return

        existing_software: List[regscale_models.SoftwareInventory] = (
            []
            if created
            else regscale_models.SoftwareInventory.get_all_by_parent(
                parent_id=new_asset.id,
                parent_module=None,
            )
        )
        existing_software_dict = {(s.name, s.version): s for s in existing_software}
        software_in_scan = set()

        for software in software_inventory:
            software_name = software.get("name")
            if not software_name:
                logger.error("Software name is required for software inventory")
                continue

            software_version = software.get("version")
            software_in_scan.add((software_name, software_version))

            if (software_name, software_version) not in existing_software_dict:
                self.context.software_to_create.append(
                    regscale_models.SoftwareInventory(
                        name=software_name,
                        parentHardwareAssetId=new_asset.id,
                        version=software_version,
                    )
                )

    def create_asset_data_and_link(self, asset: regscale_models.Asset, integration_asset: IntegrationAsset) -> None:
        """
        Create Data and Link objects for the given asset.

        :param regscale_models.Asset asset: The asset to create Data and Link for
        :param IntegrationAsset integration_asset: The integration asset containing source data and URL
        :rtype: None
        """
        if integration_asset.source_data:
            regscale_models.Data(
                parentId=asset.id,
                parentModule=asset.get_module_string(),
                dataSource=self.context.title,
                dataType=regscale_models.DataDataType.JSON.value,
                rawData=json.dumps(integration_asset.source_data, indent=2, cls=DateTimeEncoder),
                lastUpdatedById=integration_asset.asset_owner_id or "Unknown",
                createdById=integration_asset.asset_owner_id or "Unknown",
            ).create_or_update(bulk_create=True, bulk_update=True)

        if integration_asset.url:
            link = regscale_models.Link(
                parentID=asset.id,
                parentModule=asset.get_module_string(),
                url=integration_asset.url,
                title="Asset Provider URL",
            )
            if link.find_by_unique():
                self.context.link_to_update.append(link)
            else:
                self.context.link_to_create.append(link)

    @staticmethod
    def create_or_update_ports_protocol(asset: regscale_models.Asset, integration_asset: IntegrationAsset) -> None:
        """
        Create or update PortsProtocol objects for the given asset.

        :param regscale_models.Asset asset: The asset to create or update PortsProtocol for
        :param IntegrationAsset integration_asset: The integration asset containing ports/protocols info
        :rtype: None
        """
        if integration_asset.ports_and_protocols:
            for port_protocol in integration_asset.ports_and_protocols:
                if not port_protocol.get("start_port") or not port_protocol.get("end_port"):
                    logger.error("Invalid port protocol data: %s", port_protocol)
                    continue
                ports_protocol = regscale_models.PortsProtocol(
                    parentId=asset.id,
                    parentModule=asset.get_module_string(),
                    startPort=port_protocol.get("start_port", 0),
                    endPort=port_protocol.get("end_port", 0),
                    service=port_protocol.get("service", asset.name),
                    protocol=port_protocol.get("protocol"),
                    purpose=port_protocol.get("purpose", "Grant access to %s" % asset.name),
                    usedBy=asset.name,
                )
                try:
                    _retry_with_backoff(
                        operation=ports_protocol.create_or_update,
                        operation_name="PortsProtocol(parentId=%d, port=%s)"
                        % (asset.id, port_protocol.get("start_port")),
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to create PortsProtocol for asset %d port %s after retries: %s",
                        asset.id,
                        port_protocol.get("start_port"),
                        e,
                    )

    def _build_default_batch_options(self) -> AssetBatchOptions:
        """
        Build default batch options for asset processing.

        Creates an AssetBatchOptions dictionary with settings appropriate for
        scanner integration asset processing. Uses otherTrackingNumber as the
        primary unique key field since that is the primary identifier used for
        asset deduplication.

        :return: Default batch options for asset operations
        :rtype: AssetBatchOptions
        """
        return {
            "source": self.context.title,
            "uniqueKeyFields": ["otherTrackingNumber"],
            "enableMopUp": True,
            "mopUpStatus": "Inactive",
        }
