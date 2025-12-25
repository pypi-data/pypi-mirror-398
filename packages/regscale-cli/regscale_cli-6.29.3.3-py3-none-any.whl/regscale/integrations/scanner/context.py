#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scanner context for sharing state across handlers."""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set

from regscale.core.app.application import Application
from regscale.integrations.scanner.models.enums import ScannerIntegrationType
from regscale.integrations.variables import ScannerVariables
from regscale.utils.threading import ThreadSafeDict, ThreadSafeList

if TYPE_CHECKING:
    from rich.progress import Progress

    from regscale.integrations.commercial.stig_mapper_integration.mapping_engine import StigMappingEngine
    from regscale.integrations.due_date_handler import DueDateHandler
    from regscale.integrations.milestone_manager import MilestoneManager
    from regscale.integrations.scanner.utils import ManagedDefaultDict
    from regscale.models import OpenIssueDict, regscale_models

logger = logging.getLogger("regscale")


def _default_thread_safe_dict() -> ThreadSafeDict:
    """Factory function for creating ThreadSafeDict instances."""
    return ThreadSafeDict()


def _default_thread_safe_list() -> ThreadSafeList:
    """Factory function for creating ThreadSafeList instances."""
    return ThreadSafeList()


@dataclass
class ScannerContext:
    """
    Shared context passed to all scanner handlers.

    Contains configuration, caches, and shared state needed
    by asset, finding, issue, and vulnerability handlers.

    This dataclass centralizes the state that was previously scattered
    across the ScannerIntegration class, making it easier to:
    - Pass state between handlers
    - Test handlers in isolation
    - Understand what state is shared

    Attributes:
        plan_id: The ID of the security plan or component
        tenant_id: The ID of the tenant (defaults to 1)
        is_component: Whether this is a component integration vs security plan
        parent_module: The parent module string ("securityplans" or "components")
        title: Display title for the scanner integration
        scan_date: Date of the scan being processed
        asset_identifier_field: Field used to identify assets (e.g., "otherTrackingNumber")
        issue_identifier_field: Field used to identify issues (integration-specific)
        enable_cci_mapping: Whether to map CCIs to controls
        close_outdated_findings: Whether to close findings not in current scan
        suppress_asset_not_found_errors: Suppress "Asset not found" error messages
        import_all_findings: Import findings even without associated assets
        asset_batch_size: Batch size for asset bulk operations
        issue_batch_size: Batch size for issue bulk operations
        vulnerability_batch_size: Batch size for vulnerability bulk operations
    """

    # Required configuration
    plan_id: int
    tenant_id: int = 1

    # Application context
    app: Application = field(default_factory=Application)

    # Parent information
    parent_module: str = "securityplans"
    is_component: bool = False

    # Scanner metadata
    title: str = "Scanner Integration"
    scan_date: str = ""
    scanner_type: ScannerIntegrationType = ScannerIntegrationType.CONTROL_TEST

    # Identifier fields
    asset_identifier_field: str = "otherTrackingNumber"
    issue_identifier_field: str = ""

    # Feature flags
    enable_cci_mapping: bool = True
    close_outdated_findings: bool = True
    suppress_asset_not_found_errors: bool = False
    import_all_findings: bool = False
    enable_finding_date_update: bool = False
    options_map_assets_to_components: bool = False

    # Batch sizes (loaded from ScannerVariables in __post_init__)
    asset_batch_size: int = 500
    issue_batch_size: int = 500
    vulnerability_batch_size: int = 1000

    # Processing counts
    num_assets_to_process: Optional[int] = None
    num_findings_to_process: Optional[int] = None
    closed_count: int = 0

    # User/assessor information
    assessor_id: str = ""

    # Progress trackers (injected after initialization)
    asset_progress: Optional["Progress"] = None
    finding_progress: Optional["Progress"] = None

    # Component reference (when is_component=True)
    component: Optional["regscale_models.Component"] = None

    # Handlers (lazy initialized)
    due_date_handler: Optional["DueDateHandler"] = None
    milestone_manager: Optional["MilestoneManager"] = None
    stig_mapper: Optional["StigMappingEngine"] = None

    # Thread-safe collections for assets
    asset_map_by_identifier: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)
    alerted_assets: Set[str] = field(default_factory=set)

    # Thread-safe collections for components
    components: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    components_by_title: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)

    # Thread-safe collections for software/data/links
    software_to_create: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    software_to_update: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    data_to_create: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    data_to_update: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    link_to_create: ThreadSafeList = field(default_factory=_default_thread_safe_list)
    link_to_update: ThreadSafeList = field(default_factory=_default_thread_safe_list)

    # Issue tracking
    existing_issues_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)

    # Control implementation maps
    control_implementation_id_map: Dict[str, int] = field(default_factory=dict)
    control_map: Dict[int, str] = field(default_factory=dict)
    control_id_to_implementation_map: Dict[int, int] = field(default_factory=dict)

    # Existing issues by implementation map
    existing_issue_ids_by_implementation_map: Dict[int, List["OpenIssueDict"]] = field(
        default_factory=lambda: defaultdict(list)
    )

    # CCI mapping
    cci_to_control_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)
    _no_ccis: bool = field(default=False, repr=False)
    _cci_map_loaded: bool = field(default=False, repr=False)
    cci_to_control_map_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # Assessment map
    assessment_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)

    # Control tests map (uses ManagedDefaultDict)
    control_tests_map: Optional["ManagedDefaultDict"] = None

    # Control implementation map
    control_implementation_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)
    implementation_objective_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)
    implementation_option_map: ThreadSafeDict = field(default_factory=_default_thread_safe_dict)

    # Issue lookup cache for performance optimization
    _integration_finding_id_cache: Optional[ThreadSafeDict] = field(default=None, repr=False)
    _issue_cache_lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    # Cache effectiveness metrics
    _cache_hit_count: int = field(default=0, repr=False)
    _cache_miss_count: int = field(default=0, repr=False)
    _cache_fallback_count: int = field(default=0, repr=False)

    # Lock registry for thread safety
    _lock_registry: ThreadSafeDict = field(default_factory=_default_thread_safe_dict, repr=False)
    _global_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # KEV data cache
    _kev_data: ThreadSafeDict = field(default_factory=_default_thread_safe_dict, repr=False)

    # Results tracking
    _results: ThreadSafeDict = field(default_factory=_default_thread_safe_dict, repr=False)

    # Error tracking
    errors: List[str] = field(default_factory=list)

    # Scan history lock
    scan_history_lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    # Max POAM ID (value holder)
    _max_poam_id: Optional[int] = field(default=None, repr=False)

    # RegScale version
    regscale_version: str = ""

    # Status and severity mapping dictionaries
    finding_status_map: Dict[Any, Any] = field(default_factory=dict)
    checklist_status_map: Dict[Any, Any] = field(default_factory=dict)
    finding_severity_map: Dict[Any, Any] = field(default_factory=dict)
    issue_to_vulnerability_map: Dict[Any, Any] = field(default_factory=dict)
    asset_map: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize derived attributes after dataclass initialization."""
        # Set parent module based on component status
        if self.is_component:
            self.parent_module = "components"
        else:
            self.parent_module = "securityplans"

        # Load batch sizes from ScannerVariables configuration only if not already set
        # (allows custom batch sizes to be passed in __init__)
        if self.asset_batch_size == 500:  # Default value
            self.asset_batch_size = getattr(ScannerVariables, "assetBatchSize", 500)
        if self.issue_batch_size == 500:  # Default value
            self.issue_batch_size = getattr(ScannerVariables, "issueBatchSize", 500)
        if self.vulnerability_batch_size == 1000:  # Default value
            self.vulnerability_batch_size = getattr(ScannerVariables, "vulnerabilityBatchSize", 1000)

        logger.debug(
            "ScannerContext initialized: plan_id=%d, tenant_id=%d, is_component=%s, parent_module=%s",
            self.plan_id,
            self.tenant_id,
            self.is_component,
            self.parent_module,
        )

    def get_lock(self, key: str) -> threading.RLock:
        """
        Get or create a lock associated with a key.

        Thread-safe method to obtain a reentrant lock for a given key.
        Used to ensure thread safety when accessing shared resources.

        :param str key: The cache key to get a lock for
        :return: A reentrant lock for the given key
        :rtype: threading.RLock
        """
        lock = self._lock_registry.get(key)
        if lock is None:
            with self._global_lock:
                lock = self._lock_registry.get(key)
                if lock is None:
                    lock = threading.RLock()
                    self._lock_registry[key] = lock
        return lock

    def update_result_counts(self, key: str, results: Dict[str, List]) -> None:
        """
        Update the results dictionary with counts from bulk operations.

        :param str key: The key to update (e.g., "assets", "issues", "vulnerabilities")
        :param Dict[str, List] results: The results dict with "created" and "updated" lists
        """
        if key not in self._results:
            self._results[key] = {"created_count": 0, "updated_count": 0}
        self._results[key]["created_count"] += len(results.get("created", []))
        self._results[key]["updated_count"] += len(results.get("updated", []))

    def log_cache_effectiveness(self) -> None:
        """
        Log cache hit/miss statistics to measure cache effectiveness.

        This helps identify performance improvements from caching.
        """
        total_lookups = self._cache_hit_count + self._cache_miss_count
        if total_lookups == 0:
            return

        hit_rate = (self._cache_hit_count / total_lookups) * 100

        logger.info(
            "Issue lookup cache effectiveness: %d hits, %d misses (%.1f%% hit rate), %d fallback API calls",
            self._cache_hit_count,
            self._cache_miss_count,
            hit_rate,
            self._cache_fallback_count,
        )

    def clear_batch_collections(self) -> None:
        """
        Clear batch collections after each chunk to free memory.

        This method should be called after processing each chunk of findings
        to prevent memory accumulation during large imports.
        """
        self.software_to_create.clear()
        self.software_to_update.clear()
        self.data_to_create.clear()
        self.data_to_update.clear()
        self.link_to_create.clear()
        self.link_to_update.clear()
        logger.debug("Cleared batch collections to free memory")

    def clear_lock_registry(self) -> None:
        """
        Clear lock registry to free memory.

        This method should be called periodically during large imports
        to prevent unbounded lock accumulation.
        """
        with self._global_lock:
            self._lock_registry.clear()
        logger.debug("Cleared lock registry to free memory")

    @classmethod
    def from_scanner_integration(cls, scanner: Any) -> "ScannerContext":
        """
        Create a ScannerContext from an existing ScannerIntegration instance.

        This factory method allows migration from the existing ScannerIntegration
        class to the new context-based approach.

        :param Any scanner: The ScannerIntegration instance to extract context from
        :return: A new ScannerContext with values from the scanner
        :rtype: ScannerContext
        """
        context = cls(
            plan_id=scanner.plan_id,
            tenant_id=scanner.tenant_id,
            app=scanner.app,
            is_component=scanner.is_component,
            parent_module=scanner.parent_module,
            title=scanner.title,
            scan_date=scanner.scan_date,
            scanner_type=scanner.type,
            asset_identifier_field=scanner.asset_identifier_field,
            issue_identifier_field=scanner.issue_identifier_field,
            enable_cci_mapping=scanner.enable_cci_mapping,
            close_outdated_findings=scanner.close_outdated_findings,
            suppress_asset_not_found_errors=scanner.suppress_asset_not_found_errors,
            import_all_findings=getattr(scanner, "import_all_findings", False),
            enable_finding_date_update=scanner.enable_finding_date_update,
            options_map_assets_to_components=scanner.options_map_assets_to_components,
            asset_batch_size=scanner.asset_batch_size,
            issue_batch_size=scanner.issue_batch_size,
            vulnerability_batch_size=scanner.vulnerability_batch_size,
            num_assets_to_process=scanner.num_assets_to_process,
            num_findings_to_process=scanner.num_findings_to_process,
            closed_count=scanner.closed_count,
            assessor_id=scanner.assessor_id,
            asset_progress=scanner.asset_progress,
            finding_progress=scanner.finding_progress,
        )

        # Copy thread-safe collections
        context.asset_map_by_identifier = scanner.asset_map_by_identifier
        context.alerted_assets = scanner.alerted_assets
        context.components = scanner.components
        context.components_by_title = scanner.components_by_title
        context.software_to_create = scanner.software_to_create
        context.software_to_update = scanner.software_to_update
        context.data_to_create = scanner.data_to_create
        context.data_to_update = scanner.data_to_update
        context.link_to_create = scanner.link_to_create
        context.link_to_update = scanner.link_to_update
        context.existing_issues_map = scanner.existing_issues_map

        # Copy maps
        context.control_implementation_id_map = scanner.control_implementation_id_map
        context.control_map = scanner.control_map
        context.control_id_to_implementation_map = scanner.control_id_to_implementation_map
        context.existing_issue_ids_by_implementation_map = scanner.existing_issue_ids_by_implementation_map
        context.cci_to_control_map = scanner.cci_to_control_map
        context.assessment_map = scanner.assessment_map
        context.control_tests_map = scanner.control_tests_map
        context.control_implementation_map = scanner.control_implementation_map
        context.implementation_objective_map = scanner.implementation_objective_map
        context.implementation_option_map = scanner.implementation_option_map

        # Copy status maps
        context.finding_status_map = scanner.finding_status_map
        context.checklist_status_map = scanner.checklist_status_map
        context.finding_severity_map = scanner.finding_severity_map
        context.issue_to_vulnerability_map = scanner.issue_to_vulnerability_map
        context.asset_map = scanner.asset_map

        # Copy handlers
        context.due_date_handler = scanner.due_date_handler
        context.milestone_manager = scanner.milestone_manager
        context.stig_mapper = scanner.stig_mapper

        # Copy internal state
        context._kev_data = scanner._kev_data
        context._results = scanner._results
        context.errors = scanner.errors
        context.regscale_version = scanner.regscale_version
        context._max_poam_id = scanner._max_poam_id

        # Copy component reference if applicable
        if scanner.is_component:
            context.component = getattr(scanner, "component", None)

        return context
