#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Inventory Collection Package.

This package provides collectors for GCP resources using Cloud Asset Inventory
and Security Command Center APIs.
"""

# Lazy imports to avoid circular dependencies during development
# These will be populated as modules are implemented
__all__ = ["BaseCollector", "GCPInventoryCollector", "collect_all_inventory"]


def __getattr__(name: str):
    """Lazy import for inventory classes."""
    if name == "BaseCollector":
        from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

        return BaseCollector
    if name == "GCPInventoryCollector":
        from regscale.integrations.commercial.gcp.inventory.collector import GCPInventoryCollector

        return GCPInventoryCollector
    if name == "collect_all_inventory":
        from regscale.integrations.commercial.gcp.inventory.collector import collect_all_inventory

        return collect_all_inventory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
