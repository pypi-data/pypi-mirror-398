"""
Scanner integration package.

This package provides a modular, SOLID-compliant architecture for scanner integrations.

Package Structure:
- base.py: BaseScannerIntegration orchestrator class
- cache/: Caching classes (AssetCache, ControlCache, IssueCache)
- context.py: ScannerContext for shared state
- handlers/: Handler classes (AssetHandler, VulnerabilityHandler, IssueHandler)
- models/: Data models (IntegrationAsset, IntegrationFinding, enums)
- utils/: Utility functions (field_utils, managed_dict)
"""

from regscale.integrations.scanner.base import BaseScannerIntegration, ScannerIntegration
from regscale.integrations.scanner.cache import AssetCache, ControlCache, IssueCache
from regscale.integrations.scanner.context import ScannerContext
from regscale.integrations.scanner.handlers import AssetHandler, IssueHandler, VulnerabilityHandler
from regscale.integrations.scanner.models import (
    FindingStatus,
    IntegrationAsset,
    IntegrationFinding,
    ScannerIntegrationType,
)
from regscale.integrations.scanner.utils import get_thread_workers_max, hash_string, issue_due_date

__all__ = [
    # Base classes
    "BaseScannerIntegration",
    "ScannerIntegration",  # Deprecated alias
    # Cache classes
    "AssetCache",
    "ControlCache",
    "IssueCache",
    # Context
    "ScannerContext",
    # Handler classes
    "AssetHandler",
    "IssueHandler",
    "VulnerabilityHandler",
    # Models
    "FindingStatus",
    "IntegrationAsset",
    "IntegrationFinding",
    "ScannerIntegrationType",
    # Utils
    "get_thread_workers_max",
    "hash_string",
    "issue_due_date",
]
