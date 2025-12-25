#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parsers module for Wiz integration - re-exports from main.py for clean imports."""

# Import all parser functions from the main parsers module
from regscale.integrations.commercial.wizv2.parsers.main import (
    collect_components_to_create,
    fetch_wiz_data,
    get_disk_storage,
    get_ip_address,
    get_latest_version,
    get_network_info,
    get_product_ids,
    get_software_name_from_cpe,
    handle_container_image_version,
    handle_provider,
    handle_software_version,
    pull_resource_info_from_props,
)

__all__ = [
    "collect_components_to_create",
    "fetch_wiz_data",
    "get_disk_storage",
    "get_ip_address",
    "get_latest_version",
    "get_network_info",
    "get_product_ids",
    "get_software_name_from_cpe",
    "handle_container_image_version",
    "handle_provider",
    "handle_software_version",
    "pull_resource_info_from_props",
]
