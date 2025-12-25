"""
Integration Asset dataclass for scanner integrations.

This module provides the IntegrationAsset dataclass which represents an asset
to be integrated into RegScale, including its metadata and associated components.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Dict, List, Optional

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.models import regscale_models

logger = logging.getLogger("regscale")


@dataclasses.dataclass
class IntegrationAsset:
    """
    Dataclass for integration assets.

    Represents an asset to be integrated, including its metadata and associated components.
    If a component does not exist, it will be created based on the names provided in ``component_names``.

    :param str name: The name of the asset.
    :param str identifier: A unique identifier for the asset.
    :param str asset_type: The type of the asset.
    :param str asset_category: The category of the asset.
    :param str component_type: The type of the component, defaults to ``ComponentType.Hardware``.
    :param Optional[int] parent_id: The ID of the parent asset, defaults to None.
    :param Optional[str] parent_module: The module of the parent asset, defaults to None.
    :param str status: The status of the asset, defaults to "Active (On Network)".
    :param str date_last_updated: The last update date of the asset, defaults to the current datetime.
    :param Optional[str] asset_owner_id: The ID of the asset owner, defaults to None.
    :param Optional[str] mac_address: The MAC address of the asset, defaults to None.
    :param Optional[str] fqdn: The Fully Qualified Domain Name of the asset, defaults to None.
    :param Optional[str] ip_address: The IP address of the asset, defaults to None.
    :param List[str] component_names: A list of strings that represent the names of the components associated with the
    asset, components will be created if they do not exist.
    """

    name: str
    identifier: str
    asset_type: str
    asset_category: str
    component_type: str = regscale_models.ComponentType.Hardware
    description: str = ""
    parent_id: Optional[int] = None
    parent_module: Optional[str] = None
    status: regscale_models.AssetStatus = regscale_models.AssetStatus.Active
    date_last_updated: str = dataclasses.field(default_factory=get_current_datetime)
    asset_owner_id: Optional[str] = None
    mac_address: Optional[str] = None
    fqdn: Optional[str] = None
    ip_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    component_names: List[str] = dataclasses.field(default_factory=list)
    is_virtual: bool = True

    # Additional fields from Wiz integration
    external_id: Optional[str] = None
    management_type: Optional[str] = None
    software_vendor: Optional[str] = None
    software_version: Optional[str] = None
    software_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    other_tracking_number: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag_number: Optional[str] = None
    is_public_facing: Optional[bool] = None
    azure_identifier: Optional[str] = None
    disk_storage: Optional[int] = None
    cpu: Optional[int] = None
    ram: Optional[int] = None
    operating_system: Optional[regscale_models.AssetOperatingSystem] = None
    os_version: Optional[str] = None
    end_of_life_date: Optional[str] = None
    vlan_id: Optional[str] = None
    uri: Optional[str] = None
    aws_identifier: Optional[str] = None
    google_identifier: Optional[str] = None
    other_cloud_identifier: Optional[str] = None
    patch_level: Optional[str] = None
    cpe: Optional[str] = None
    is_latest_scan: Optional[bool] = None
    is_authenticated_scan: Optional[bool] = None
    system_administrator_id: Optional[str] = None
    scanning_tool: Optional[str] = None

    source_data: Optional[Dict[str, Any]] = None
    url: Optional[str] = None
    software_function: Optional[str] = None
    baseline_configuration: Optional[str] = None
    ports_and_protocols: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    software_inventory: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        if self.ip_address in ["", "0.0.0.0"]:
            self.ip_address = None
