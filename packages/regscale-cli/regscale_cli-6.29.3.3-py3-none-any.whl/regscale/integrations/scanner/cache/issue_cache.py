#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue cache for scanner integrations.

This module provides a centralized cache for issue lookups during scanner processing.
It consolidates issue-related caching functionality from ScannerIntegration.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from regscale.core.app.application import Application
from regscale.models.regscale_models.issue import Issue, IssueStatus, OpenIssueDict
from regscale.utils.threading import ThreadSafeDict

if TYPE_CHECKING:
    from regscale.integrations.scanner.models import IntegrationFinding

logger = logging.getLogger("regscale")


class IssueCache:
    """
    Cache for issue lookups during scanner processing.

    This class provides thread-safe caching and lookup functionality for issues,
    reducing API calls and improving performance during scanner integration operations.

    Attributes:
        plan_id: The ID of the security plan or component
        parent_module: The parent module string (e.g., "securityplans" or "components")
        is_component: Whether this cache is for a component integration
    """

    def __init__(
        self,
        plan_id: int,
        parent_module: str,
        is_component: bool = False,
        title: Optional[str] = None,
        issue_identifier_field: Optional[str] = None,
    ) -> None:
        """
        Initialize the IssueCache.

        :param int plan_id: The ID of the security plan or component
        :param str parent_module: The parent module string
        :param bool is_component: Whether this is a component integration
        :param Optional[str] title: The integration title for source report filtering
        :param Optional[str] issue_identifier_field: Integration-specific identifier field name
        """
        self.plan_id = plan_id
        self.parent_module = parent_module
        self.is_component = is_component
        self.title = title
        self.issue_identifier_field = issue_identifier_field
        self.app = Application()

        # Thread-safe cache for issues indexed by integrationFindingId
        self._integration_finding_id_cache: Optional[ThreadSafeDict[str, List[Issue]]] = None
        self._cache_lock = threading.RLock()

        # Cache for existing issues by control implementation ID
        self._existing_issues_map: ThreadSafeDict[int, List[Issue]] = ThreadSafeDict()

        # Open issues by control implementation ID (from GraphQL)
        self._open_issues_by_implementation: Dict[int, List[OpenIssueDict]] = {}

        # Cache effectiveness metrics
        self._cache_hit_count: int = 0
        self._cache_miss_count: int = 0
        self._cache_fallback_count: int = 0

    def warm_cache(self) -> None:
        """
        Pre-load issues for the plan into the cache.

        This method fetches all issues for the security plan/component and indexes
        them by integrationFindingId for O(1) lookups during processing.
        """
        self._populate_issue_lookup_cache()
        self._load_open_issues_by_implementation()

    def _populate_issue_lookup_cache(self) -> None:
        """
        Populate the issue lookup cache by fetching all issues for the plan and indexing by integrationFindingId.

        This eliminates N+1 API calls during findings processing by creating an in-memory index.
        Thread-safe for concurrent access.
        """
        with self._cache_lock:
            # Double-check locking pattern - check if cache already populated
            if self._integration_finding_id_cache is not None:
                return

            module_str = "component" if self.is_component else "security plan"
            logger.info("Building issue lookup index for %s %d...", module_str, self.plan_id)
            start_time = time.time()

            # Fetch all issues for the security plan
            all_issues = Issue.fetch_issues_by_ssp(app=self.app, ssp_id=self.plan_id)

            # Build index: integrationFindingId -> List[Issue]
            cache: ThreadSafeDict[str, List[Issue]] = ThreadSafeDict()
            indexed_count = 0

            for issue in all_issues:
                if issue.integrationFindingId:
                    finding_id = issue.integrationFindingId
                    if finding_id not in cache:
                        cache[finding_id] = []
                    cache[finding_id].append(issue)
                    indexed_count += 1

            self._integration_finding_id_cache = cache

            elapsed = time.time() - start_time
            logger.info(
                "Issue lookup index built: %d issues indexed from %d total issues (%d unique finding IDs) in %.2fs",
                indexed_count,
                len(all_issues),
                len(cache),
                elapsed,
            )

    def _load_open_issues_by_implementation(self) -> None:
        """
        Load open issues indexed by control implementation ID.

        Uses the GraphQL-based method from Issue model for efficient retrieval.
        """
        self._open_issues_by_implementation = Issue.get_open_issues_ids_by_implementation_id(
            plan_id=self.plan_id, is_component=self.is_component
        )

    def get_by_finding_id(self, integration_finding_id: str) -> Optional[Issue]:
        """
        Get an issue by its integration finding ID.

        :param str integration_finding_id: The integration finding ID
        :return: The issue if found, None otherwise
        :rtype: Optional[Issue]
        """
        issues_map = self._get_issues_map()
        return issues_map.get(integration_finding_id)

    def _get_issues_map(self) -> Dict[str, Issue]:
        """
        Get the issues map indexed by integration finding ID.

        This provides backward compatibility with the get_issues_map() method
        from ScannerIntegration while using the cached data.

        :return: Dictionary mapping integrationFindingId to Issue
        :rtype: Dict[str, Issue]
        """
        all_issues: List[Issue] = Issue.get_all_by_parent(
            parent_id=self.plan_id,
            parent_module=self.parent_module,
        )
        return {issue.integrationFindingId: issue for issue in all_issues if issue.integrationFindingId}

    def get_by_implementation_id(self, implementation_id: int) -> List[Issue]:
        """
        Get issues associated with a control implementation ID.

        :param int implementation_id: The control implementation ID
        :return: List of issues for the implementation
        :rtype: List[Issue]
        """
        return self._existing_issues_map.get(implementation_id) or []

    def get_open_issues_by_implementation(self) -> Dict[int, List[OpenIssueDict]]:
        """
        Get open issues indexed by control implementation ID.

        :return: Dictionary mapping implementation ID to list of open issue dicts
        :rtype: Dict[int, List[OpenIssueDict]]
        """
        if not self._open_issues_by_implementation:
            self._load_open_issues_by_implementation()
        return self._open_issues_by_implementation

    def add(self, issue: Issue) -> None:
        """
        Add an issue to the cache.

        :param Issue issue: The issue to add
        """
        if issue.integrationFindingId:
            # Ensure cache is initialized
            if self._integration_finding_id_cache is None:
                self._populate_issue_lookup_cache()

            with self._cache_lock:
                cache = self._integration_finding_id_cache
                if cache is not None:
                    finding_id = issue.integrationFindingId
                    if finding_id not in cache:
                        cache[finding_id] = []
                    # Only add if not already present
                    if not any(existing.id == issue.id for existing in cache[finding_id]):
                        cache[finding_id].append(issue)

    def find_existing_for_finding(
        self,
        finding: "IntegrationFinding",
        finding_id: str,
        issue_status: Optional[IssueStatus] = None,
    ) -> Optional[Issue]:
        """
        Find an existing issue for a finding.

        :param IntegrationFinding finding: The finding to match
        :param str finding_id: The integration finding ID (generated by ScannerIntegration)
        :param Optional[IssueStatus] issue_status: The expected status of the issue
        :return: The existing issue if found, None otherwise
        :rtype: Optional[Issue]
        """
        from regscale.integrations.variables import ScannerVariables

        # Per-asset creation mode doesn't reuse issues
        if ScannerVariables.issueCreation.lower() == "perasset":
            return None

        existing_issues = self._get_existing_issues_for_finding(finding_id, finding)

        if not existing_issues:
            return None

        if issue_status == IssueStatus.Open:
            return self._find_issue_for_open_status(existing_issues, finding_id)
        elif issue_status == IssueStatus.Closed:
            return self._find_issue_for_closed_status(existing_issues, finding, finding_id)

        # Return first match if no specific status requested
        return existing_issues[0]

    def _get_existing_issues_for_finding(self, finding_id: str, finding: "IntegrationFinding") -> List[Issue]:
        """
        Get existing issues for the finding using cached lookup (fast) or API fallback (slow).

        :param str finding_id: The integration finding ID
        :param IntegrationFinding finding: The finding data
        :return: List of existing issues
        :rtype: List[Issue]
        """
        # Populate cache on first use (lazy initialization)
        if self._integration_finding_id_cache is None:
            self._populate_issue_lookup_cache()

        # FAST PATH: Check cache first (O(1) lookup, no API call)
        cache = self._integration_finding_id_cache
        if cache is None:
            return []

        existing_issues: List[Issue] = cache.get(finding_id) or []

        # Track cache hit/miss
        if existing_issues:
            self._cache_hit_count += 1
        else:
            self._cache_miss_count += 1

        # FALLBACK PATH: Only if no issues found in cache AND external_id exists
        if not existing_issues and finding.external_id:
            logger.debug("Issue not found in cache for finding_id=%s, trying identifier fallback", finding_id)
            fallback_issues = self._find_issues_by_identifier_fallback(finding.external_id)
            if fallback_issues:
                existing_issues = fallback_issues
                self._cache_fallback_count += 1

                # Cache the fallback result to avoid future API lookups
                if cache is not None:
                    with self._cache_lock:
                        cache[finding_id] = existing_issues

        return existing_issues

    def _find_issues_by_identifier_fallback(self, external_id: str) -> List[Issue]:
        """
        Find issues by identifier fields (otherIdentifier or integration-specific field) as fallback.

        :param str external_id: The external ID to search for
        :return: List of matching issues
        :rtype: List[Issue]
        """
        fallback_issues: List[Issue] = []

        try:
            all_issues: List[Issue] = Issue.get_all_by_parent(
                parent_id=self.plan_id,
                parent_module=self.parent_module,
            )

            # Filter by source report to only check our integration's issues
            source_issues = [issue for issue in all_issues if issue.sourceReport == self.title] if self.title else []

            for issue in source_issues:
                if getattr(issue, "otherIdentifier", None) == external_id:
                    fallback_issues.append(issue)
                    logger.debug("Found issue %d by otherIdentifier fallback: %s", issue.id, external_id)

                elif (
                    self.issue_identifier_field
                    and hasattr(issue, self.issue_identifier_field)
                    and getattr(issue, self.issue_identifier_field) == external_id
                ):
                    fallback_issues.append(issue)
                    logger.debug(
                        "Found issue %d by %s fallback: %s", issue.id, self.issue_identifier_field, external_id
                    )

            if fallback_issues:
                logger.debug(
                    "Fallback deduplication found %d existing issue(s) for external_id: %s",
                    len(fallback_issues),
                    external_id,
                )

        except Exception as e:
            logger.warning("Error in fallback issue lookup for %s: %s", external_id, e)

        return fallback_issues

    def _find_issue_for_open_status(self, existing_issues: List[Issue], finding_id: str) -> Optional[Issue]:
        """
        Find appropriate issue when the finding status is Open.

        :param List[Issue] existing_issues: List of existing issues to search
        :param str finding_id: The finding ID for logging
        :return: The matching issue or None
        :rtype: Optional[Issue]
        """
        # Find an open issue to update first
        open_issue = next((issue for issue in existing_issues if issue.status != IssueStatus.Closed), None)
        if open_issue:
            return open_issue

        # If no open issue found, look for a closed issue to reopen
        closed_issue = next((issue for issue in existing_issues if issue.status == IssueStatus.Closed), None)
        if closed_issue:
            logger.debug("Reopening closed issue %d for finding %s", closed_issue.id, finding_id)
            return closed_issue

        return None

    def _find_issue_for_closed_status(
        self,
        existing_issues: List[Issue],
        finding: "IntegrationFinding",
        finding_id: str,
    ) -> Optional[Issue]:
        """
        Find appropriate issue when the finding status is Closed.

        :param List[Issue] existing_issues: List of existing issues to search
        :param IntegrationFinding finding: The finding data
        :param str finding_id: The finding ID for logging
        :return: The matching issue or None
        :rtype: Optional[Issue]
        """
        from regscale.core.utils.date import date_str

        # Find a closed issue with matching due date to consolidate with
        matching_closed_issue = next(
            (
                issue
                for issue in existing_issues
                if issue.status == IssueStatus.Closed and date_str(issue.dueDate) == date_str(finding.due_date)
            ),
            None,
        )
        if matching_closed_issue:
            return matching_closed_issue

        # If no matching closed issue, look for any existing issue to update
        any_existing_issue = next(iter(existing_issues), None) if existing_issues else None
        if any_existing_issue:
            logger.debug("Closing existing issue %d for finding %s", any_existing_issue.id, finding_id)
            return any_existing_issue

        return None

    def log_cache_effectiveness(self) -> None:
        """
        Log cache hit/miss statistics to measure cache effectiveness.

        This helps identify performance improvements from the cache implementation.
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

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        :return: Dictionary containing cache statistics
        :rtype: Dict[str, Any]
        """
        total_lookups = self._cache_hit_count + self._cache_miss_count
        hit_rate = (self._cache_hit_count / total_lookups * 100) if total_lookups > 0 else 0.0

        return {
            "hit_count": self._cache_hit_count,
            "miss_count": self._cache_miss_count,
            "fallback_count": self._cache_fallback_count,
            "total_lookups": total_lookups,
            "hit_rate": hit_rate,
            "cache_size": len(self._integration_finding_id_cache) if self._integration_finding_id_cache else 0,
        }

    def clear(self) -> None:
        """
        Clear all cached data.
        """
        with self._cache_lock:
            self._integration_finding_id_cache = None
            self._existing_issues_map = ThreadSafeDict()
            self._open_issues_by_implementation = {}
            self._cache_hit_count = 0
            self._cache_miss_count = 0
            self._cache_fallback_count = 0
