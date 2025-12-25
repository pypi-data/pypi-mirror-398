#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Scanner Integration Class.

This module provides the BaseScannerIntegration orchestrator class that replaces
the monolithic ScannerIntegration with a clean handler-based architecture.

Following SOLID principles:
- Single Responsibility: This class ONLY orchestrates handlers
- Open/Closed: Extend via subclassing, closed for modification
- Liskov Substitution: Subclasses can replace this base
- Interface Segregation: Clean, minimal interface
- Dependency Injection: All handlers and caches are injected
"""
from __future__ import annotations

import logging
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from regscale.core.app.application import Application
from regscale.integrations.scanner.cache import AssetCache, ControlCache, IssueCache
from regscale.integrations.scanner.context import ScannerContext
from regscale.integrations.scanner.handlers import AssetHandler, IssueHandler, VulnerabilityHandler
from regscale.models import regscale_models
from regscale.models.regscale_models.batch_options import IssueBatchOptions, VulnerabilityBatchOptions
from regscale.models.regscale_models.regscale_model import RegScaleModel

if TYPE_CHECKING:
    from regscale.integrations.scanner.models import IntegrationAsset, IntegrationFinding

logger = logging.getLogger("regscale")


class BaseScannerIntegration(ABC):
    """
    Abstract base class for scanner integrations.

    This class orchestrates handlers and provides the integration contract.
    It follows SOLID principles and keeps complexity low (~300 lines max).

    The class provides:
    - Handler initialization and orchestration
    - Cache management
    - Batch processing with server-side deduplication
    - Thread-safe operations
    - Clean extension points via abstract methods

    Subclasses must implement:
    - fetch_findings(): Yield IntegrationFinding objects from the scanner
    - fetch_assets(): Yield IntegrationAsset objects from the scanner

    Example usage:
        class MyScanner(BaseScannerIntegration):
            def fetch_findings(self):
                # Yield findings from scanner API
                pass

            def fetch_assets(self):
                # Yield assets from scanner API
                pass

        scanner = MyScanner(plan_id=123)
        count = scanner.sync_findings()
    """

    # Configuration - subclasses can override
    title: str = "Scanner Integration"
    type: str = "CONTROL_TEST"
    create_vulnerabilities: bool = True  # Set to False for POAM-only imports (issues only)

    def __init__(
        self,
        plan_id: int,
        tenant_id: int = 1,
        is_component: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the scanner integration.

        :param int plan_id: The ID of the security plan or component
        :param int tenant_id: The ID of the tenant, defaults to 1
        :param bool is_component: Whether this is a component integration, defaults to False
        :param kwargs: Additional configuration options passed to context
        """
        self.plan_id = plan_id
        self.tenant_id = tenant_id
        self.app = Application()

        # Initialize context with configuration
        self.context = self._init_context(plan_id, tenant_id, is_component, **kwargs)

        # Initialize handlers (dependency injection)
        self._init_handlers()

        # Initialize caches (dependency injection)
        self._init_caches()

        logger.debug(
            "BaseScannerIntegration initialized: plan_id=%d, tenant_id=%d, is_component=%s",
            plan_id,
            tenant_id,
            is_component,
        )

    def _init_context(
        self,
        plan_id: int,
        tenant_id: int,
        is_component: bool,
        **kwargs: Any,
    ) -> ScannerContext:
        """
        Initialize the scanner context with configuration.

        :param int plan_id: The security plan ID
        :param int tenant_id: The tenant ID
        :param bool is_component: Whether this is a component
        :param kwargs: Additional context configuration
        :return: Initialized scanner context
        :rtype: ScannerContext
        """
        # Extract context-specific kwargs
        context_kwargs = {
            "plan_id": plan_id,
            "tenant_id": tenant_id,
            "is_component": is_component,
            "app": self.app,
            "title": kwargs.get("title", self.title),
        }

        # Add optional configuration
        optional_fields = [
            "asset_identifier_field",
            "issue_identifier_field",
            "enable_cci_mapping",
            "close_outdated_findings",
            "suppress_asset_not_found_errors",
            "import_all_findings",
            "enable_finding_date_update",
            "options_map_assets_to_components",
            "asset_batch_size",
            "issue_batch_size",
            "vulnerability_batch_size",
            "scan_date",
            "assessor_id",
        ]

        for field in optional_fields:
            if field in kwargs:
                context_kwargs[field] = kwargs[field]

        return ScannerContext(**context_kwargs)

    def _init_handlers(self) -> None:
        """
        Initialize all handlers with shared context.

        Handlers are injected with the context for dependency injection.
        This allows handlers to be easily mocked in tests.
        """
        # Asset handler
        self.asset_handler = AssetHandler(
            context=self.context,
            asset_cache=None,  # Will be set after cache init
        )

        # Vulnerability handler
        self.vulnerability_handler = VulnerabilityHandler(
            plan_id=self.context.plan_id,
            parent_module=self.context.parent_module,
            scanner_title=self.context.title,
            progress=None,  # Set later if needed
            batch_size=self.context.vulnerability_batch_size,
            suppress_asset_not_found_errors=self.context.suppress_asset_not_found_errors,
        )

        # Issue handler
        self.issue_handler = IssueHandler(
            plan_id=self.context.plan_id,
            parent_module=self.context.parent_module,
            issue_cache=None,  # Will be set after cache init
            assessor_id=self.context.assessor_id,
            title=self.context.title,
            is_component=self.context.is_component,
            issue_identifier_field=self.context.issue_identifier_field,
        )

    def _init_caches(self) -> None:
        """
        Initialize all caches for efficient lookups.

        Caches are thread-safe and provide O(1) lookups.
        """
        # Asset cache
        self.asset_cache = AssetCache(
            plan_id=self.context.plan_id,
            parent_module=self.context.parent_module,
            identifier_field=self.context.asset_identifier_field,
            is_component=self.context.is_component,
            options_map_assets_to_components=self.context.options_map_assets_to_components,
            suppress_not_found_errors=self.context.suppress_asset_not_found_errors,
            external_cache=self.context.asset_map_by_identifier,
        )

        # Issue cache
        self.issue_cache = IssueCache(
            plan_id=self.context.plan_id,
            parent_module=self.context.parent_module,
            is_component=self.context.is_component,
            title=self.context.title,
            issue_identifier_field=self.context.issue_identifier_field,
        )

        # Control cache
        self.control_cache = ControlCache(
            plan_id=self.context.plan_id,
            parent_module=self.context.parent_module,
            enable_cci_mapping=self.context.enable_cci_mapping,
        )

        # Wire caches to handlers
        self.asset_handler.asset_cache = self.asset_cache
        self.issue_handler.issue_cache = self.issue_cache

    @abstractmethod
    def fetch_findings(self, *args: Any, **kwargs: Any) -> Iterator["IntegrationFinding"]:
        """
        Fetch findings from the scanner source.

        Subclasses must implement this to yield findings from their source.

        :param args: Positional arguments for scanner-specific configuration
        :param kwargs: Keyword arguments for scanner-specific configuration
        :return: Iterator of IntegrationFinding objects
        :rtype: Iterator[IntegrationFinding]
        """
        pass

    @abstractmethod
    def fetch_assets(self, *args: Any, **kwargs: Any) -> Iterator["IntegrationAsset"]:
        """
        Fetch assets from the scanner source.

        Subclasses must implement this to yield assets from their source.

        :param args: Positional arguments for scanner-specific configuration
        :param kwargs: Keyword arguments for scanner-specific configuration
        :return: Iterator of IntegrationAsset objects
        :rtype: Iterator[IntegrationAsset]
        """
        pass

    # Entry points - delegate to handlers

    @classmethod
    def sync_findings(cls, plan_id: int, **kwargs: Any) -> int:
        """
        Sync findings from scanner to RegScale.

        This is the main entry point for finding synchronization.

        :param int plan_id: The security plan ID
        :param kwargs: Additional configuration options
        :return: Number of findings processed
        :rtype: int
        """
        instance = cls(plan_id=plan_id, **kwargs)
        return instance._execute_finding_sync(**kwargs)

    @classmethod
    def sync_assets(cls, plan_id: int, **kwargs: Any) -> int:
        """
        Sync assets from scanner to RegScale.

        This is the main entry point for asset synchronization.

        :param int plan_id: The security plan ID
        :param kwargs: Additional configuration options
        :return: Number of assets processed
        :rtype: int
        """
        instance = cls(plan_id=plan_id, **kwargs)
        return instance._execute_asset_sync(**kwargs)

    def _execute_finding_sync(self, **kwargs: Any) -> int:
        """
        Execute finding synchronization workflow.

        :param kwargs: Additional sync options
        :return: Number of findings processed
        :rtype: int
        """
        logger.info("Starting finding sync for plan_id=%d", self.plan_id)

        # Fetch findings from scanner
        findings = self.fetch_findings(**kwargs)

        # Process findings in batch
        results = self.process_findings_batch(
            findings,
            enable_mop_up=self.context.close_outdated_findings,
            create_vulnerabilities=self.create_vulnerabilities,
        )

        count = len(results.get("created", [])) + len(results.get("updated", []))
        logger.info("Finding sync completed: %d findings processed", count)

        return count

    def _execute_asset_sync(self, **kwargs: Any) -> int:
        """
        Execute asset synchronization workflow using batch processing.

        Converts IntegrationAssets to RegScale Asset models and uses
        batch_create_or_update for server-side deduplication (much faster
        than individual API calls).

        :param kwargs: Additional sync options
        :return: Number of assets processed
        :rtype: int
        """
        from regscale.models.regscale_models.batch_options import AssetBatchOptions

        logger.info("Starting asset sync for plan_id=%d", self.plan_id)

        # Fetch and convert assets to RegScale models
        regscale_assets: List[regscale_models.Asset] = []
        for asset in self.fetch_assets(**kwargs):
            try:
                regscale_asset = self.asset_handler.convert_to_regscale_asset(asset)
                if regscale_asset:
                    regscale_assets.append(regscale_asset)
            except Exception as exc:
                logger.error("Error converting asset %s: %s", asset.identifier, exc)

        if not regscale_assets:
            logger.info("No assets to sync")
            return 0

        logger.info("Sending %d assets to RegScale via batch API", len(regscale_assets))

        # Build batch options with proper unique key field
        # Use the scanner's asset_identifier_field (e.g., "otherTrackingNumber" for POAM)
        unique_key_field = self.context.asset_identifier_field
        batch_options = AssetBatchOptions(
            source=self.context.title,
            uniqueKeyFields=[unique_key_field],
            enableMopUp=False,
            mopUpStatus="",
        )
        logger.info(
            "Asset batch options: source=%s, uniqueKeyFields=%s, context.asset_identifier_field=%s",
            self.context.title,
            batch_options.get("uniqueKeyFields"),
            unique_key_field,
        )
        # Log first asset's key field value to verify it's populated
        if regscale_assets:
            first_asset = regscale_assets[0]
            key_value = getattr(first_asset, unique_key_field, "MISSING_ATTR")
            logger.info(
                "First asset %s=%s, name=%s",
                unique_key_field,
                key_value,
                first_asset.name,
            )

        # Use batch_create_or_update for server-side deduplication
        # This is much faster than individual create_or_update calls
        results = regscale_models.Asset.batch_create_or_update(
            items=regscale_assets,
            batch_size=1000,
            options=batch_options,
        )

        # Update asset cache with results
        for asset in results:
            if asset and asset.id:
                self.asset_cache.add_by_identifier(asset.name, asset)

        logger.info("Asset sync completed: %d assets processed", len(results))

        return len(results)

    # Orchestration methods

    def process_finding(self, finding: "IntegrationFinding") -> Optional[regscale_models.Issue]:
        """
        Process a single finding by orchestrating handlers.

        This method:
        1. Looks up the asset (if asset_identifier present)
        2. Creates vulnerability via VulnerabilityHandler
        3. Creates/updates issue via IssueHandler

        :param IntegrationFinding finding: The finding to process
        :return: The created/updated issue, or None on error
        :rtype: Optional[regscale_models.Issue]
        """
        try:
            # Look up asset if identifier present
            asset = None
            if finding.asset_identifier:
                asset = self.asset_cache.get_by_identifier(finding.asset_identifier)

            # Create vulnerability
            vulnerability = None
            if self.vulnerability_handler.has_required_vulnerability_fields(finding):
                try:
                    vulnerability = self.vulnerability_handler.create_vulnerability(
                        finding=finding,
                        asset=asset,
                    )
                    if vulnerability and vulnerability.id:
                        finding.vulnerability_id = vulnerability.id
                except Exception as exc:
                    logger.error("Error creating vulnerability for finding %s: %s", finding.external_id, exc)

            # Create/update issue
            issue = None
            try:
                issue = self.issue_handler.create_or_update_issue(
                    title=finding.title or "Unknown",
                    finding=finding,
                )
            except Exception as exc:
                logger.error("Error creating issue for finding %s: %s", finding.external_id, exc)

            return issue

        except Exception as exc:
            logger.error("Error processing finding: %s", exc)
            return None

    def _flush_chunk(
        self,
        vulnerabilities: List[regscale_models.Vulnerability],
        issues: List[regscale_models.Issue],
        vuln_options: VulnerabilityBatchOptions,
        issue_options: IssueBatchOptions,
    ) -> Dict[str, Any]:
        """
        Flush a chunk of vulnerabilities and issues to the server.

        :param List[regscale_models.Vulnerability] vulnerabilities: Vulnerabilities to submit
        :param List[regscale_models.Issue] issues: Issues to submit
        :param VulnerabilityBatchOptions vuln_options: Batch options for vulnerabilities
        :param IssueBatchOptions issue_options: Batch options for issues
        :return: Dictionary with "created" and "updated" lists
        :rtype: Dict[str, Any]
        """
        results: Dict[str, Any] = {"created": [], "updated": []}

        if vulnerabilities:
            vuln_results = self.vulnerability_handler.batch_create_vulnerabilities(
                vulnerabilities=vulnerabilities,
                options=vuln_options,
            )
            results["created"].extend(vuln_results)

        if issues:
            # Debug logging for batch issue creation
            sample_issue = issues[0]
            logger.info(
                "Sample issue #1: parentId=%s, parentModule=%s, integrationFindingId=%s, title=%s, status=%s",
                sample_issue.parentId,
                sample_issue.parentModule,
                sample_issue.integrationFindingId,
                (sample_issue.title or "")[:50],
                sample_issue.status,
            )
            # Show a few more samples to verify uniqueness
            if len(issues) > 1:
                logger.info(
                    "Sample issue #2: integrationFindingId=%s, title=%s",
                    issues[1].integrationFindingId,
                    (issues[1].title or "")[:50],
                )
            if len(issues) > 2:
                logger.info(
                    "Sample issue #3: integrationFindingId=%s, title=%s",
                    issues[2].integrationFindingId,
                    (issues[2].title or "")[:50],
                )
            logger.info("Issue batch options: %s", dict(issue_options))

            issue_results = regscale_models.Issue.batch_create_or_update(
                items=issues,
                batch_size=self.context.issue_batch_size,
                options=issue_options,
            )
            logger.info("Issue batch results: %d items returned", len(issue_results) if issue_results else 0)
            results["created"].extend(issue_results)

        return results

    def process_findings_batch(
        self,
        findings: Iterator["IntegrationFinding"],
        enable_mop_up: bool = True,
        enable_asset_discovery: bool = True,
        create_vulnerabilities: bool = True,
        **options: Any,
    ) -> Dict[str, Any]:
        """
        Process findings in chunks to minimize memory usage.

        This method processes findings in configurable chunks, flushing each chunk
        to the server before processing the next. This prevents memory accumulation
        when processing large datasets (e.g., 10k+ findings).

        :param Iterator[IntegrationFinding] findings: Iterator of findings to process
        :param bool enable_mop_up: Enable closing outdated findings, defaults to True
        :param bool enable_asset_discovery: Enable server-side asset discovery, defaults to True
        :param bool create_vulnerabilities: Create vulnerabilities for findings, defaults to True.
            Set to False for POAM imports which only need issues.
        :param options: Additional batch options
        :return: Dictionary with "created" and "updated" lists
        :rtype: Dict[str, Any]
        """
        from regscale.integrations.variables import ScannerVariables

        chunk_size = getattr(ScannerVariables, "findingChunkSize", 5000)
        all_results: Dict[str, Any] = {"created": [], "updated": []}
        chunk_count = 0

        # Build batch options once (reused per chunk)
        vuln_options = VulnerabilityBatchOptions(
            source=self.context.title,
            uniqueKeys=["plugInId", "parentId", "parentModule"],
            enableMopUp=enable_mop_up,
            mopUpStatus="Closed",
            enableAssetDiscovery=enable_asset_discovery,
            suppressAssetNotFoundWarnings=self.context.suppress_asset_not_found_errors,
            poamCreation=True,
            parentId=self.context.plan_id,
            parentModule=self.context.parent_module,
        )

        # Get issue owner ID - fallback to current user if not set
        issue_owner_id = self.context.assessor_id or RegScaleModel.get_user_id() or ""
        if not issue_owner_id:
            logger.warning("No issue owner ID available - issues may fail to create")

        issue_options = IssueBatchOptions(
            source=self.context.title,
            uniqueKeyFields=["integrationFindingId"],
            enableMopUp=enable_mop_up,
            mopUpStatus="Closed",
            performValidation=True,
            poamCreation=True,
            parentId=self.context.plan_id,
            parentModule=self.context.parent_module,
            issueOwnerId=issue_owner_id,
            assetIdentifierFieldName=self.context.asset_identifier_field,
        )

        # Initialize chunk lists
        chunk_vulns: List[regscale_models.Vulnerability] = []
        chunk_issues: List[regscale_models.Issue] = []

        for finding in findings:
            self._add_finding_to_chunks(finding, chunk_vulns, chunk_issues, create_vulnerabilities)

            # Flush chunk when size reached
            if self._should_flush_chunk(chunk_vulns, chunk_issues, chunk_size, create_vulnerabilities):
                chunk_count += 1
                self._flush_and_accumulate(
                    chunk_vulns,
                    chunk_issues,
                    vuln_options,
                    issue_options,
                    all_results,
                    chunk_count,
                    create_vulnerabilities,
                )

        # Flush remaining items
        if chunk_vulns or chunk_issues:
            chunk_count += 1
            self._flush_and_accumulate(
                chunk_vulns,
                chunk_issues,
                vuln_options,
                issue_options,
                all_results,
                chunk_count,
                create_vulnerabilities,
                is_final=True,
            )

        logger.info("Processed %d chunks total", chunk_count)
        return all_results

    def _add_finding_to_chunks(
        self,
        finding: "IntegrationFinding",
        chunk_vulns: List[regscale_models.Vulnerability],
        chunk_issues: List[regscale_models.Issue],
        create_vulnerabilities: bool,
    ) -> None:
        """Add a finding to the appropriate chunk lists."""
        if create_vulnerabilities and self.vulnerability_handler.has_required_vulnerability_fields(finding):
            vuln = self.vulnerability_handler.convert_finding_to_vulnerability(finding)
            if vuln:
                chunk_vulns.append(vuln)

        issue = self.issue_handler.create_or_update_issue(title=finding.title or "Unknown", finding=finding)
        if issue:
            chunk_issues.append(issue)

    def _should_flush_chunk(
        self,
        chunk_vulns: List[regscale_models.Vulnerability],
        chunk_issues: List[regscale_models.Issue],
        chunk_size: int,
        create_vulnerabilities: bool,
    ) -> bool:
        """Determine if chunks should be flushed based on size."""
        if len(chunk_issues) >= chunk_size:
            return True
        return create_vulnerabilities and len(chunk_vulns) >= chunk_size

    def _flush_and_accumulate(
        self,
        chunk_vulns: List[regscale_models.Vulnerability],
        chunk_issues: List[regscale_models.Issue],
        vuln_options: VulnerabilityBatchOptions,
        issue_options: IssueBatchOptions,
        all_results: Dict[str, Any],
        chunk_count: int,
        create_vulnerabilities: bool,
        is_final: bool = False,
    ) -> None:
        """Flush chunk to server and accumulate results."""
        prefix = "Flushing final chunk" if is_final else "Flushing chunk"
        if create_vulnerabilities:
            logger.info(
                "%s %d with %d vulnerabilities and %d issues", prefix, chunk_count, len(chunk_vulns), len(chunk_issues)
            )
        else:
            logger.info("%s %d with %d issues", prefix, chunk_count, len(chunk_issues))

        results = self._flush_chunk(chunk_vulns, chunk_issues, vuln_options, issue_options)
        all_results["created"].extend(results.get("created", []))
        chunk_vulns.clear()
        chunk_issues.clear()
        self.context.clear_batch_collections()

    def close_outdated_findings(
        self,
        current_findings: Dict[str, set],
    ) -> int:
        """
        Close findings not present in the current scan.

        This method orchestrates handlers to close outdated vulnerabilities
        and issues based on what was seen in the current scan.

        :param Dict[str, set] current_findings: Map of plugin_id to asset identifiers
        :return: Number of findings closed
        :rtype: int
        """
        closed_count = 0

        try:
            # Close outdated vulnerabilities
            # Note: VulnerabilityHandler would need a close_outdated method
            # For now, rely on server-side mop-up via batch options

            # Close outdated issues
            # Note: IssueHandler would need a close_outdated method
            # For now, rely on server-side mop-up via batch options

            logger.info("Closed %d outdated findings", closed_count)

        except Exception as exc:
            logger.error("Error closing outdated findings: %s", exc)

        return closed_count


# Backward compatibility layer
class ScannerIntegration(BaseScannerIntegration):
    """
    Backward-compatible alias for BaseScannerIntegration.

    **DEPRECATED**: Use BaseScannerIntegration directly.

    This class maintains backward compatibility with existing scanner
    integrations that inherit from ScannerIntegration. It will be
    removed in a future release.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize with deprecation warning.

        :param args: Positional arguments passed to BaseScannerIntegration
        :param kwargs: Keyword arguments passed to BaseScannerIntegration
        """
        warnings.warn(
            "ScannerIntegration is deprecated, use BaseScannerIntegration instead. "
            "This alias will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
