#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Abstract Compliance Integration Base Class

This module provides a base class for implementing compliance integrations
that follow common patterns across different compliance tools (Wiz, Tenable, Sicura).
"""
import logging
import re
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional, Any, Iterator

from regscale.core.app.utils.app_utils import get_current_datetime, regscale_string_to_datetime
from regscale.integrations.control_matcher import ControlMatcher
from regscale.integrations.scanner_integration import (
    ScannerIntegration,
    IntegrationAsset,
    IntegrationFinding,
)
from regscale.models import regscale_models
from regscale.models.regscale_models import (
    Catalog,
    SecurityControl,
    ControlImplementation,
    Assessment,
    ImplementationObjective,
    SecurityPlan,
    ComplianceSettings,
)

logger = logging.getLogger("regscale")

# Safer, linear-time regex for control-id parsing/normalization used across
# compliance integrations. Supports: 'AC-4', 'AC-4(2)', 'AC-4 (2)', 'AC-4-2', 'AC-4 2'
# Distinct branches ('(', '-' or whitespace) avoid ambiguous nested alternation
# and excessive backtracking that could be used for DoS.
SAFE_CONTROL_ID_RE = re.compile(  # NOSONAR
    r"^([A-Za-z]{2}-\d+)(?:\s*\(\s*(\d+)\s*\)|-\s*(\d+)|\s+(\d+))?$",  # NOSONAR
    re.IGNORECASE,  # NOSONAR
)


class ComplianceItem(ABC):
    """
    Abstract base class representing a compliance assessment item.

    This represents a single compliance check result for a specific
    resource against a specific control.
    """

    @property
    @abstractmethod
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        pass

    @property
    @abstractmethod
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        pass

    @property
    @abstractmethod
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        pass

    @property
    @abstractmethod
    def compliance_result(self) -> str:
        """Result of compliance check (PASS, FAIL, etc)."""
        pass

    @property
    @abstractmethod
    def severity(self) -> Optional[str]:
        """Severity level of the compliance violation (if failed)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the compliance check."""
        pass

    @property
    @abstractmethod
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CSF)."""
        pass


class ComplianceIntegration(ScannerIntegration, ABC):
    """
    Abstract base class for compliance integrations.

    This class provides common patterns for:
    - Processing compliance data
    - Creating assets from compliance items
    - Creating findings/issues for failed compliance
    - Mapping compliance items to controls
    - Creating assessments and updating control status
    """

    # String literal constants
    NOT_APPLICABLE_LABEL = "Not Applicable"
    NOT_APPLICABLE_LOWER = "not applicable"
    NOT_APPLICABLE_UNDERSCORE = "not_applicable"

    # Status mapping constants
    PASS_STATUSES = ["PASS", "PASSED", "Pass", "Passed", "pass", "passed", "COMPLIANT", "Compliant", "compliant"]
    FAIL_STATUSES = [
        "FAIL",
        "FAILED",
        "Fail",
        "Failed",
        "fail",
        "failed",
        "NONCOMPLIANT",
        "NonCompliant",
        "noncompliant",
    ]

    NOT_APPLICABLE_STATUSES = ["NOT_APPLICABLE", NOT_APPLICABLE_LABEL, "not_applicable", "NA", "N/A"]
    INCONCLUSIVE_STATUSES = [
        "INCONCLUSIVE",
        "Inconclusive",
        "inconclusive",
        "UNKNOWN",
        "Unknown",
        "unknown",
        "MANUAL",
        "Manual",
        "manual",
    ]

    def __init__(
        self,
        plan_id: int,
        catalog_id: Optional[int] = None,
        framework: str = "NIST800-53R5",
        create_issues: bool = True,
        update_control_status: bool = True,
        create_poams: bool = False,
        parent_module: str = "securityplans",
        **kwargs,
    ):
        """
        Initialize compliance integration.

        :param int plan_id: RegScale plan ID
        :param Optional[int] catalog_id: RegScale catalog ID
        :param str framework: Compliance framework
        :param bool create_issues: Whether to create issues for failed compliance
        :param bool update_control_status: Whether to update control implementation status
        :param bool create_poams: Whether to mark issues as POAMs
        """
        super().__init__(plan_id=plan_id, **kwargs)

        self.catalog_id = catalog_id
        self.framework = framework
        self.create_issues = create_issues
        self.update_control_status = update_control_status
        self.create_poams = create_poams

        # Compliance data storage
        self.all_compliance_items: List[ComplianceItem] = []
        self.failed_compliance_items: List[ComplianceItem] = []
        self.passing_controls: Dict[str, ComplianceItem] = {}
        self.failing_controls: Dict[str, ComplianceItem] = {}
        self.not_applicable_controls: Dict[str, ComplianceItem] = {}

        # Asset mapping for compliance to asset correlation
        self.asset_compliance_map: Dict[str, List[ComplianceItem]] = defaultdict(list)

        # Initialize caches for existing records to prevent duplicates
        self._existing_assets_cache: Dict[str, regscale_models.Asset] = {}
        self._existing_issues_cache: Dict[str, regscale_models.Issue] = {}
        self._existing_assessments_cache: Dict[str, regscale_models.Assessment] = {}
        self._cache_loaded = False

        # Mapping caches for linking issues to implementations and assessments
        # Key: canonical control id string (e.g., "AC-2(1)") -> ControlImplementation.id
        self._impl_id_by_control: Dict[str, int] = {}
        # Key: ControlImplementation.id -> Assessment created/updated today
        self._assessment_by_impl_today: Dict[int, regscale_models.Assessment] = {}
        # suppress asset not found errors in non-debug modes
        self.suppress_asset_not_found_errors = logger.level != logging.DEBUG
        # Set scan date
        self.scan_date = get_current_datetime()

        # Cache for compliance settings
        self._compliance_settings = None
        self._security_plan = None
        self._security_plan_loaded = False  # Track if we've attempted to load
        self._compliance_settings_loaded = False  # Track if we've attempted to load
        self._status_mapping_cache = {}  # Cache for status mappings to avoid repeated calculations

        # Initialize control matcher for robust control ID matching
        self._control_matcher = ControlMatcher()

        # Performance optimization: cache for control lookups
        # Key: control ID variation (e.g., 'ac-2(1)') -> (ControlImplementation, SecurityControl)
        self._control_lookup_cache: Dict[str, tuple[ControlImplementation, SecurityControl]] = {}

    def is_poam(self, finding: IntegrationFinding) -> bool:  # type: ignore[override]
        """
        Determines if an issue should be considered a POAM for compliance integrations.

        - If the integration was initialized with `create_poams=True` (e.g., via `--create-poams/-cp`),
          always return True so newly created and updated issues are POAMs.
        - Otherwise, defer to the generic scanner behavior.
        """
        try:
            if getattr(self, "create_poams", False):
                return True
            if finding.due_date >= get_current_datetime():
                return True
        except Exception:
            pass
        return super().is_poam(finding)

    def _load_existing_records_cache(self) -> None:
        """
        Load existing RegScale records into cache to prevent duplicates.
        This method populates caches for assets, issues, and assessments.

        :return: None
        :rtype: None
        """
        if self._cache_loaded:
            return

        logger.info("Loading existing RegScale records to prevent duplicates...")

        try:
            # Load existing assets for this plan
            self._load_existing_assets()

            # Load existing issues for this plan
            self._load_existing_issues()

            # Load existing assessments for control implementations
            self._load_existing_assessments()

            self._cache_loaded = True
            logger.info("Loaded existing records cache to prevent duplicates:")
            logger.info(f"   - Assets: {len(self._existing_assets_cache)}")
            logger.info(f"   - Issues: {len(self._existing_issues_cache)}")
            logger.info(f"   - Assessments: {len(self._existing_assessments_cache)}")

        except Exception as e:
            logger.error(f"Error loading existing records cache: {e}")
            # Continue without cache to avoid blocking the integration
            self._cache_loaded = True

    def _load_existing_assets(self) -> None:
        """
        Load existing assets into cache.

        :return: None
        :rtype: None
        """
        try:
            # Get all assets for this plan
            existing_assets = regscale_models.Asset.get_all_by_parent(
                parent_id=self.plan_id, parent_module=self.parent_module
            )

            for asset in existing_assets:
                # Cache by identifier and other_tracking_number for flexible lookup
                if hasattr(asset, "identifier") and asset.identifier:
                    self._existing_assets_cache[asset.identifier] = asset
                if hasattr(asset, "otherTrackingNumber") and asset.otherTrackingNumber:
                    self._existing_assets_cache[asset.otherTrackingNumber] = asset

        except Exception as e:
            logger.debug(f"Error loading existing assets: {e}")

    def _load_existing_issues(self) -> None:
        """
        Load existing issues into cache.

        Uses both plan-level and control-level queries to ensure all relevant issues are found.

        :return: None
        :rtype: None
        """
        try:
            all_issues = set()

            # Method 1: Get issues directly associated with the plan
            plan_issues = regscale_models.Issue.get_all_by_parent(
                parent_id=self.plan_id, parent_module=self.parent_module
            )
            all_issues.update(plan_issues)
            logger.debug(f"Found {len(plan_issues)} issues directly under plan {self.plan_id}")

            # Method 2: Get issues associated with control implementations (matches scanner integration logic)
            try:
                issues_by_impl = regscale_models.Issue.get_open_issues_ids_by_implementation_id(
                    plan_id=self.plan_id, is_component=getattr(self, "is_component", False)
                )
                impl_issues_count = 0
                for impl_id, issue_list in issues_by_impl.items():
                    for issue_dict in issue_list:
                        # issue_dict contains issue data, need to get the actual issue object
                        issue_id = issue_dict.get("id")
                        if issue_id:
                            try:
                                issue = regscale_models.Issue.get_object(object_id=issue_id)
                                if issue:
                                    all_issues.add(issue)
                                    impl_issues_count += 1
                            except Exception as e:
                                logger.debug(f"Could not load issue {issue_id}: {e}")

                logger.debug(f"Found {impl_issues_count} additional issues via control implementations")
            except Exception as e:
                logger.debug(f"Could not load issues by control implementation: {e}")

            logger.debug(f"Total unique issues found: {len(all_issues)} for plan {self.plan_id}")

            wiz_issues = 0
            for issue in all_issues:
                # Cache by external_id and other_identifier for flexible lookup
                if hasattr(issue, "otherIdentifier") and issue.otherIdentifier:
                    self._existing_issues_cache[issue.otherIdentifier] = issue
                    if "wiz-policy" in issue.otherIdentifier.lower():
                        wiz_issues += 1
                        logger.debug(f"Cached Wiz issue: {issue.id} -> other_identifier: {issue.otherIdentifier}")

            logger.debug(f"Cached {wiz_issues} Wiz policy issues out of {len(all_issues)} total issues")

        except Exception as e:
            logger.debug(f"Error loading existing issues: {e}")

    def _load_existing_assessments(self) -> None:
        """
        Load existing assessments into cache.

        :return: None
        :rtype: None
        """
        try:
            # Get control implementations for this plan to find their assessments
            implementations = ControlImplementation.get_all_by_parent(
                parent_id=self.plan_id, parent_module=self.parent_module
            )

            for implementation in implementations:
                try:
                    # Get assessments for this implementation
                    assessments = regscale_models.Assessment.get_all_by_parent(
                        parent_id=implementation.id, parent_module="controls"
                    )

                    for assessment in assessments:
                        # Create cache key: impl_id + day (YYYY-MM-DD)
                        if hasattr(assessment, "actualFinish") and assessment.actualFinish:
                            try:
                                # actualFinish may be a string; normalize to date-only key
                                if hasattr(assessment.actualFinish, "date"):
                                    day_key = assessment.actualFinish.date().isoformat()
                                else:
                                    day_key = regscale_string_to_datetime(assessment.actualFinish).date().isoformat()
                                cache_key = f"{implementation.id}_{day_key}"
                                self._existing_assessments_cache[cache_key] = assessment
                            except Exception:
                                continue

                except Exception as e:
                    logger.debug(f"Error loading assessments for implementation {implementation.id}: {e}")

        except Exception as e:
            logger.debug(f"Error loading existing assessments: {e}")

    def _find_existing_asset_cached(self, resource_id: str) -> Optional[regscale_models.Asset]:
        """
        Find existing asset by resource ID using cache.

        :param str resource_id: Resource identifier to search for
        :return: Existing asset or None if not found
        :rtype: Optional[regscale_models.Asset]
        """
        return self._existing_assets_cache.get(resource_id)

    def _find_existing_issue_cached(self, external_id: str) -> Optional[regscale_models.Issue]:
        """
        Find existing issue by external ID using cache.

        :param str external_id: External identifier to search for
        :return: Existing issue or None if not found
        :rtype: Optional[regscale_models.Issue]
        """
        return self._existing_issues_cache.get(external_id)

    def _find_existing_assessment_cached(
        self, implementation_id: int, scan_date
    ) -> Optional[regscale_models.Assessment]:
        """
        Find existing assessment by implementation ID and date using cache.

        :param int implementation_id: Control implementation ID
        :param scan_date: Scan date to check against existing assessments
        :return: Existing assessment or None if not found
        :rtype: Optional[regscale_models.Assessment]
        """
        # Normalize to date-only key
        try:
            if hasattr(scan_date, "date"):
                day_key = scan_date.date().isoformat()
            else:
                day_key = regscale_string_to_datetime(str(scan_date)).date().isoformat()
        except Exception:
            day_key = str(scan_date).split(" ")[0]
        cache_key = f"{implementation_id}_{day_key}"
        return self._existing_assessments_cache.get(cache_key)

    def check_for_existing_evidence(self, file_name_pattern: str) -> bool:
        """
        Check if an evidence file matching the pattern already exists in RegScale.

        This method fetches existing files for the plan and checks if any match
        the provided pattern, helping prevent duplicate evidence uploads.

        :param str file_name_pattern: Pattern to match against existing file names
        :return: True if a matching file exists, False otherwise
        :rtype: bool
        """
        try:
            # Import here to avoid circular dependency
            from regscale.models.regscale_models import File

            # Get all existing files for the plan
            existing_files = File.get_files_for_parent_from_regscale(
                parent_id=self.plan_id, parent_module=self.parent_module
            )

            # Check if any file matches the pattern
            for file_obj in existing_files:
                if hasattr(file_obj, "trustedDisplayName") and file_obj.trustedDisplayName:
                    # Check if the pattern is in the file name
                    if file_name_pattern in file_obj.trustedDisplayName:
                        logger.debug(
                            "Found existing evidence file matching pattern '%s': %s",
                            file_name_pattern,
                            file_obj.trustedDisplayName,
                        )
                        return True

            logger.debug("No existing evidence files found matching pattern '%s'", file_name_pattern)
            return False

        except Exception as e:
            logger.warning(
                "Unable to check for existing evidence files (pattern: '%s'): %s. Proceeding with upload.",
                file_name_pattern,
                e,
            )
            # Return False to allow upload to proceed if check fails
            return False

    @abstractmethod
    def fetch_compliance_data(self) -> List[Any]:
        """
        Fetch raw compliance data from the external system.

        :return: List of raw compliance data (will be converted to ComplianceItems)
        :rtype: List[Any]
        """
        pass

    @abstractmethod
    def create_compliance_item(self, raw_data: Any) -> ComplianceItem:
        """
        Create a ComplianceItem from raw compliance data.

        :param Any raw_data: Raw compliance data from external system
        :return: ComplianceItem instance
        :rtype: ComplianceItem
        """
        pass

    def process_compliance_data(self) -> None:
        """
        Process compliance data and categorize items.

        Separates passing and failing compliance items and builds
        control status mappings.

        :return: None
        :rtype: None
        """
        logger.info("Processing compliance data...")

        self._reset_compliance_state()
        allowed_controls = self._build_allowed_controls_set()
        raw_compliance_data = self.fetch_compliance_data()

        processing_stats = self._process_raw_compliance_items(raw_compliance_data, allowed_controls)
        self._log_processing_summary(raw_compliance_data, processing_stats)

        # Perform control-level categorization based on aggregated results
        self._categorize_controls_by_aggregation()
        self._log_final_results()

    def _reset_compliance_state(self) -> None:
        """Reset state to avoid double counting on repeated calls."""
        self.all_compliance_items = []
        self.failed_compliance_items = []
        self.passing_controls = {}
        self.failing_controls = {}
        self.not_applicable_controls = {}
        self.asset_compliance_map.clear()

    def _build_allowed_controls_set(self) -> set[str]:
        """Build allowed control IDs from plan/catalog controls to restrict scope."""
        allowed_controls_normalized: set[str] = set()
        try:
            controls = self._get_controls()
            logger.debug(f"Loaded {len(controls)} controls from plan/catalog")

            for ctl in controls:
                cid = (ctl.get("controlId") or "").strip()
                if not cid:
                    continue
                base, sub = self._normalize_control_id(cid)
                normalized = f"{base}({sub})" if sub else base
                allowed_controls_normalized.add(normalized)

            logger.debug(f"Built allowed_controls_normalized set with {len(allowed_controls_normalized)} entries")
            if allowed_controls_normalized:
                sample = sorted(allowed_controls_normalized)[:5]
                logger.debug(f"Sample allowed controls: {sample}")
        except Exception as e:
            logger.warning(f"Could not load controls from plan/catalog: {e}")
            allowed_controls_normalized = set()

        return allowed_controls_normalized

    def _process_raw_compliance_items(self, raw_compliance_data: list, allowed_controls: set) -> dict:
        """Process raw compliance items and return processing statistics.
        :param list raw_compliance_data: Raw compliance data from external system
        :param set allowed_controls: Allowed control IDs
        :return: Processed compliance items
        :rtype: dict
        """
        stats = {"skipped_no_control": 0, "skipped_no_resource": 0, "skipped_not_in_plan": 0, "processed_count": 0}

        for raw_item in raw_compliance_data:
            try:
                compliance_item = self.create_compliance_item(raw_item)
                if not self._process_single_compliance_item(compliance_item, allowed_controls, stats):
                    continue
            except Exception as e:
                logger.error(f"Error processing compliance item: {e}")
                continue

        return stats

    def _process_single_compliance_item(self, compliance_item: Any, allowed_controls: set, stats: dict) -> bool:
        """Process a single compliance item and update statistics. Returns True if processed successfully."""
        control_id = getattr(compliance_item, "control_id", "")
        resource_id = getattr(compliance_item, "resource_id", "")

        if not control_id:
            stats["skipped_no_control"] += 1
            return False
        if not resource_id:
            stats["skipped_no_resource"] += 1
            return False

        if not self._should_process_item(compliance_item, control_id, allowed_controls, stats):
            return False

        self._add_processed_item(compliance_item, stats)
        return True

    def _should_process_item(self, compliance_item: Any, control_id: str, allowed_controls: set, stats: dict) -> bool:
        """Determine if an item should be processed based on control filtering."""
        if not allowed_controls:
            return True

        base, sub = self._normalize_control_id(control_id)
        norm_item = f"{base}({sub})" if sub else base

        if norm_item in allowed_controls:
            return True

        # Allow PASS controls through even if they don't have existing implementations
        if compliance_item.compliance_result in self.PASS_STATUSES:
            return True

        stats["skipped_not_in_plan"] += 1
        if stats["skipped_not_in_plan"] <= 3:
            logger.debug(f"Skipping control {norm_item} - not in plan (result: {compliance_item.compliance_result})")
        return False

    def _add_processed_item(self, compliance_item: Any, stats: dict) -> None:
        """Add a processed item to collections and update statistics."""
        self.all_compliance_items.append(compliance_item)
        stats["processed_count"] += 1

        # Build asset mapping
        self.asset_compliance_map[compliance_item.resource_id].append(compliance_item)

        # Categorize by result
        if compliance_item.compliance_result in self.FAIL_STATUSES:
            self.failed_compliance_items.append(compliance_item)
            logger.debug(
                f"Added failing compliance item: control={compliance_item.control_id}, "
                f"result={compliance_item.compliance_result}, resource={compliance_item.resource_id}"
            )

    def _log_processing_summary(self, raw_compliance_data: list, stats: dict) -> None:
        """Log summary of compliance data processing."""
        logger.debug("Compliance item processing summary:")
        logger.debug(f"  - Total raw items: {len(raw_compliance_data)}")
        logger.debug(f"  - Skipped (no control_id): {stats['skipped_no_control']}")
        logger.debug(f"  - Skipped (no resource_id): {stats['skipped_no_resource']}")
        logger.debug(f"  - Skipped (not in plan): {stats['skipped_not_in_plan']}")
        logger.debug(f"  - Processed successfully: {stats['processed_count']}")

    def _log_final_results(self) -> None:
        """Log final processing results."""
        logger.debug(
            f"Processed {len(self.all_compliance_items)} compliance items: "
            f"{len(self.all_compliance_items) - len(self.failed_compliance_items)} passing, "
            f"{len(self.failed_compliance_items)} failing"
        )
        logger.debug(
            f"Control categorization: {len(self.passing_controls)} passing controls, "
            f"{len(self.failing_controls)} failing controls"
        )

    def _categorize_controls_by_aggregation(self) -> None:
        """
        Categorize controls as passing or failing based on aggregated results across all compliance items.

        This method uses project-scoped aggregation logic instead of the previous "any fail = control fails"
        approach. For project-scoped integrations (like Wiz), this provides more accurate control status.
        """

        # Group all compliance items by control ID
        control_items = self._group_items_by_control()

        # Analyze each control's results
        for control_key, items in control_items.items():
            self._categorize_single_control(control_key, items)

    def _group_items_by_control(self) -> dict:
        """Group compliance items by control ID."""
        from collections import defaultdict

        control_items = defaultdict(list)
        for item in self.all_compliance_items:
            control_key = item.control_id.lower()
            control_items[control_key].append(item)

        return control_items

    def _categorize_single_control(self, control_key: str, items: list) -> None:
        """Categorize a single control based on its compliance items."""
        from collections import Counter

        results = [item.compliance_result for item in items]
        result_counts = Counter(results)
        total_items = len(results)

        fail_count, pass_count, not_applicable_count = self._count_results(result_counts)

        if fail_count == 0 and pass_count > 0:
            self._mark_control_as_passing(control_key, items, pass_count, fail_count)
        elif fail_count > 0:
            self._handle_control_with_failures(control_key, items, fail_count, pass_count, total_items)
        elif not_applicable_count > 0 and pass_count == 0 and fail_count == 0:
            self._mark_control_as_not_applicable(control_key, items, not_applicable_count)
        else:
            logger.debug(f"Control {control_key} has unclear results: {dict(result_counts)}")

    def _count_results(self, result_counts: dict) -> tuple[int, int, int]:
        """Count pass, fail, and not applicable results from result counts."""
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]
        pass_statuses_lower = [status.lower() for status in self.PASS_STATUSES]
        not_applicable_statuses_lower = [status.lower() for status in self.NOT_APPLICABLE_STATUSES]

        fail_count = 0
        pass_count = 0
        not_applicable_count = 0

        for result, count in result_counts.items():
            if result is None:  # Skip None results (controls without evidence)
                continue
            result_lower = result.lower()
            if result_lower in fail_statuses_lower:
                fail_count += count
            elif result_lower in pass_statuses_lower:
                pass_count += count
            elif result_lower in not_applicable_statuses_lower:
                not_applicable_count += count

        return fail_count, pass_count, not_applicable_count

    def _count_pass_fail_results(self, result_counts: dict) -> tuple[int, int]:
        """Count pass and fail results from result counts (legacy method)."""
        fail_count, pass_count, _ = self._count_results(result_counts)
        return fail_count, pass_count

    def _mark_control_as_passing(self, control_key: str, items: list, pass_count: int, fail_count: int) -> None:
        """Mark a control as passing."""
        self.passing_controls[control_key] = items[0]  # Use first item as representative
        logger.debug(f"Control {control_key} marked as PASSING: {pass_count}P/{fail_count}F")

    def _mark_control_as_not_applicable(self, control_key: str, items: list, not_applicable_count: int) -> None:
        """Mark a control as not applicable."""
        self.not_applicable_controls[control_key] = items[0]  # Use first item as representative
        logger.debug(f"Control {control_key} marked as NOT_APPLICABLE: {not_applicable_count} items")

    def _handle_control_with_failures(
        self, control_key: str, items: list, fail_count: int, pass_count: int, total_items: int
    ) -> None:
        """Handle a control that has some failures."""
        fail_ratio = fail_count / total_items
        failure_threshold = getattr(self, "control_failure_threshold", 0.2)

        if fail_ratio > failure_threshold:
            self._mark_control_as_failing(control_key, items, pass_count, fail_count, fail_ratio, failure_threshold)
        else:
            self._mark_control_as_passing_with_warnings(
                control_key, items, pass_count, fail_count, fail_ratio, failure_threshold
            )

    def _mark_control_as_failing(
        self,
        control_key: str,
        items: list,
        pass_count: int,
        fail_count: int,
        fail_ratio: float,
        failure_threshold: float,
    ) -> None:
        """Mark a control as failing due to significant failures."""
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]
        failing_item = next(item for item in items if item.compliance_result.lower() in fail_statuses_lower)
        self.failing_controls[control_key] = failing_item
        logger.debug(
            f"Control {control_key} marked as FAILING: {pass_count}P/{fail_count}F "
            f"({fail_ratio:.1%} fail rate > {failure_threshold:.1%} threshold)"
        )

    def _mark_control_as_passing_with_warnings(
        self,
        control_key: str,
        items: list,
        pass_count: int,
        fail_count: int,
        fail_ratio: float,
        failure_threshold: float,
    ) -> None:
        """Mark a control as passing despite low failure rate."""
        self.passing_controls[control_key] = items[0]
        logger.debug(
            f"Control {control_key} marked as PASSING (low fail rate): {pass_count}P/{fail_count}F "
            f"({fail_ratio:.1%} fail rate < {failure_threshold:.1%} threshold)"
        )

    def create_asset_from_compliance_item(self, compliance_item: ComplianceItem) -> Optional[IntegrationAsset]:
        """
        Create an IntegrationAsset from a compliance item.

        :param ComplianceItem compliance_item: The compliance item
        :return: IntegrationAsset or None
        :rtype: Optional[IntegrationAsset]
        """
        try:
            # Check if asset already exists
            existing_asset = self._find_existing_asset_by_resource_id(compliance_item.resource_id)
            if existing_asset:
                return None

            asset_type = self._map_resource_type_to_asset_type(compliance_item)

            asset = IntegrationAsset(
                name=compliance_item.resource_name,
                identifier=compliance_item.resource_id,
                external_id=compliance_item.resource_id,
                other_tracking_number=compliance_item.resource_id,  # For deduplication
                asset_type=asset_type,
                asset_category=regscale_models.AssetCategory.Hardware,
                description=f"Asset from {self.title} compliance scan",
                parent_id=self.plan_id,
                parent_module=self.parent_module,
                status=regscale_models.AssetStatus.Active,
                date_last_updated=self.scan_date,
            )

            return asset

        except Exception as e:
            logger.error(f"Error creating asset from compliance item: {e}")
            return None

    def create_finding_from_compliance_item(self, compliance_item: ComplianceItem) -> Optional[IntegrationFinding]:
        """
        Create an IntegrationFinding from a failed compliance item.

        :param ComplianceItem compliance_item: The compliance item
        :return: IntegrationFinding or None
        :rtype: Optional[IntegrationFinding]
        """
        try:
            control_labels = [compliance_item.control_id] if compliance_item.control_id else []
            severity = self._map_severity(compliance_item.severity)

            # Extract ARNs if available (for AWS Audit Manager and other integrations)
            arns = None
            if hasattr(compliance_item, "resource_arns"):
                arns = compliance_item.resource_arns
                # Only use ARNs if they're non-empty
                if not arns:
                    arns = None

            finding = IntegrationFinding(
                control_labels=control_labels,
                title=f"Compliance Violation: {compliance_item.control_id}",
                category="Compliance",
                plugin_name=f"{self.title} Compliance Scanner",
                severity=severity,
                description=compliance_item.description,
                status=regscale_models.IssueStatus.Open,
                priority=self._map_severity_to_priority(severity),
                external_id=f"{self.title.lower()}-{compliance_item.control_id}-{compliance_item.resource_id}",
                first_seen=self.scan_date,
                last_seen=self.scan_date,
                scan_date=self.scan_date,
                asset_identifier=compliance_item.resource_id,
                issue_asset_identifier_value=arns,
                vulnerability_type="Compliance Violation",
                rule_id=compliance_item.control_id,
                baseline=compliance_item.framework,
                affected_controls=compliance_item.control_id,
            )

            # Ensure affected controls are set to the normalized control label (e.g., RA-5, AC-2(1))
            if compliance_item.control_id:
                base, sub = self._normalize_control_id(compliance_item.control_id)
                finding.affected_controls = f"{base}({sub})" if sub else base

            return finding

        except Exception as e:
            logger.error(f"Error creating finding from compliance item: {e}")
            return None

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """
        Fetch assets from compliance items, avoiding duplicates.

        :param args: Variable positional arguments
        :param kwargs: Variable keyword arguments
        :return: Iterator of integration assets
        :rtype: Iterator[IntegrationAsset]
        """
        logger.info("Fetching assets from compliance items...")

        # Load cache if not already loaded
        self._load_existing_records_cache()

        processed_resources = set()
        for compliance_item in self.all_compliance_items:
            if compliance_item.resource_id not in processed_resources:
                # Check if asset already exists in RegScale
                existing_asset = self._find_existing_asset_cached(compliance_item.resource_id)
                if existing_asset:
                    logger.debug(f"Asset already exists for resource {compliance_item.resource_id}, skipping creation")
                    processed_resources.add(compliance_item.resource_id)
                    continue

                asset = self.create_asset_from_compliance_item(compliance_item)
                if asset:
                    processed_resources.add(compliance_item.resource_id)
                    yield asset

    def fetch_findings(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetch findings from failed compliance items to create RegScale issues.

        :param args: Variable positional arguments
        :param kwargs: Variable keyword arguments
        :return: Iterator of integration findings (will be converted to RegScale Issue objects)
        :rtype: Iterator[IntegrationFinding]
        """
        logger.info(f"Preparing to create issues from {len(self.failed_compliance_items)} failed compliance items...")

        # Debug: Show sample of failed items
        if self.failed_compliance_items:
            sample_size = min(5, len(self.failed_compliance_items))
            sample = self.failed_compliance_items[:sample_size]
            logger.debug(f"Sample failed items (first {sample_size}):")
            for item in sample:
                logger.debug(
                    f"  - Control: {item.control_id}, Result: {item.compliance_result}, Resource: {item.resource_id}"
                )

        total = len(self.failed_compliance_items)
        # Backwards compatibility: check if finding_progress exists and has add_task method
        task_id = None
        if self.finding_progress is not None and hasattr(self.finding_progress, "add_task"):
            task_id = self.finding_progress.add_task(
                f"[#f68d1f]Creating issues from {total} failed compliance item(s)...",
                total=total or None,
            )

        findings_created = 0
        for compliance_item in self.failed_compliance_items:
            finding = self.create_finding_from_compliance_item(compliance_item)
            if finding:
                findings_created += 1
                # Backwards compatibility: check if finding_progress exists and has advance method
                if (
                    task_id is not None
                    and self.finding_progress is not None
                    and hasattr(self.finding_progress, "advance")
                ):
                    self.finding_progress.advance(task_id, 1)
                yield finding

        # Ensure task completes if total is known
        # Backwards compatibility: check if finding_progress exists and has update method
        if (
            total
            and task_id is not None
            and self.finding_progress is not None
            and hasattr(self.finding_progress, "update")
        ):
            self.finding_progress.update(task_id, completed=total)

        logger.info(f"Prepared {findings_created} issue records from {total} failed compliance items")

    def sync_compliance(self) -> None:
        """
        Main method to sync compliance data.

        This method orchestrates the entire compliance sync process:
        1. Process compliance data
        2. Create assets and findings
        3. Create/update control assessments
        4. Update control implementation status

        :return: None
        :rtype: None
        """
        logger.info(f"Starting {self.title} compliance sync...")

        try:
            scan_history = self.create_scan_history()
            self.process_compliance_data()

            self._sync_assets()
            self._sync_control_assessments()
            self._sync_issues()
            self._finalize_scan_history(scan_history)

            logger.info(f"Completed {self.title} compliance sync")

        except Exception as e:
            logger.error(f"Error during compliance sync: {e}")
            raise

    def _sync_assets(self) -> None:
        """
        Process and sync assets from compliance items.

        :return: None
        :rtype: None
        """
        assets = list(self.fetch_assets())
        if not assets:
            logger.debug("No assets generated from compliance items")
            return

        assets_processed = self.update_regscale_assets(iter(assets))
        self._log_asset_results(assets_processed)

        # Refresh the asset map after creating/updating assets to ensure
        # the map contains all assets for issue creation
        logger.debug("Refreshing asset map after asset sync...")
        self.asset_map_by_identifier.update(self.get_asset_map())

    def _log_asset_results(self, assets_processed: int) -> None:
        """
        Log asset processing results.

        :param int assets_processed: Number of assets processed
        :return: None
        :rtype: None
        """
        results = getattr(self, "_results", {}).get("assets", {})
        created = results.get("created_count", 0)
        updated = results.get("updated_count", 0)
        deleted = results.get("deleted_count", 0) if isinstance(results, dict) else 0

        if deleted > 0:
            logger.info(
                f"Assets processed: {assets_processed} (created: {created}, updated: {updated}, deleted: {deleted})"
            )
        elif created > 0 or updated > 0:
            logger.info(f"Assets processed: {assets_processed} (created: {created}, updated: {updated})")
        else:
            logger.debug(f"Assets processed: {assets_processed} (no changes made)")

    def _sync_control_assessments(self) -> None:
        """
        Process control assessments if enabled.

        :return: None
        :rtype: None
        """
        if self.update_control_status:
            self._process_control_assessments()

    def _sync_issues(self) -> None:
        """
        Process and sync issues from failed compliance items.

        :return: None
        :rtype: None
        """
        if not self.create_issues:
            return

        findings = list(self.fetch_findings())
        if not findings:
            logger.debug("No findings to process into issues")
            return

        # Ensure asset map is populated before processing issues
        # This handles cases where assets were created in previous runs
        if not self.asset_map_by_identifier:
            logger.debug("Loading asset map before issue processing...")
            self.asset_map_by_identifier.update(self.get_asset_map())

        findings_processed, findings_skipped = self._process_findings_to_issues(findings)

        # CRITICAL FIX: Flush bulk issue operations to database
        # This ensures all issues created/updated in bulk mode are persisted
        logger.debug(f"Calling bulk_save for {findings_processed} processed findings ({findings_skipped} skipped)...")
        issue_results = regscale_models.Issue.bulk_save()
        logger.debug(
            f"Bulk save completed - created: {issue_results.get('created_count', 0)}, updated: {issue_results.get('updated_count', 0)}"
        )

        # Update result counts with actual database operations
        if hasattr(self, "_results"):
            if "issues" not in self._results:
                self._results["issues"] = {}
            self._results["issues"].update(issue_results)

        # Use actual database results for logging
        issues_created = issue_results.get("created_count", 0)
        issues_updated = issue_results.get("updated_count", 0)
        self._log_issue_results_accurate(issues_created, issues_updated, findings_processed, findings_skipped)

    def _process_findings_to_issues(self, findings: List[IntegrationFinding]) -> tuple[int, int]:
        """
        Process findings into issues and return counts.

        :param findings: List of findings to process
        :return: Tuple of (issues_created, issues_skipped)
        """
        issues_created = 0
        issues_skipped = 0

        logger.debug(f"Processing {len(findings)} findings into issues...")
        for i, finding in enumerate(findings):
            try:
                logger.debug(
                    f"Processing finding {i + 1}/{len(findings)}: external_id='{finding.external_id}', asset_identifier='{finding.asset_identifier}"
                )
                if self._process_single_finding(finding):
                    issues_created += 1
                    logger.debug(f"  -> Finding {i + 1} processed successfully")
                else:
                    issues_skipped += 1
                    logger.debug(f"  -> Finding {i + 1} skipped")
            except Exception as e:
                logger.error(f"Error processing finding {i + 1}: {e}")
                issues_skipped += 1

        return issues_created, issues_skipped

    def _process_single_finding(self, finding: IntegrationFinding) -> bool:
        """
        Process a single finding into an issue.

        :param finding: Finding to process
        :return: True if issue was created/updated, False if skipped
        """
        logger.debug(
            f"  -> Processing finding: external_id='{finding.external_id}', asset_identifier='{finding.asset_identifier}'"
        )

        asset = self._get_or_create_asset_for_finding(finding)
        if not asset:
            logger.debug(f"  -> Asset not found/created for identifier '{finding.asset_identifier}', skipping finding")
            self._log_asset_not_found_error(finding)
            return False

        logger.debug(f"  -> Found/created asset {asset.id} for identifier '{finding.asset_identifier}'")
        issue_title = self.get_issue_title(finding)
        issue = self.create_or_update_issue_from_finding(title=issue_title, finding=finding)
        success = issue is not None
        if success and issue:
            logger.debug(f"  -> Successfully processed finding -> issue {issue.id}")
        else:
            logger.debug("  -> Failed to create/update issue for finding")
        return success

    def _get_or_create_asset_for_finding(self, finding: IntegrationFinding) -> Optional[regscale_models.Asset]:
        """
        Get existing asset or create one on-demand for the finding.

        :param IntegrationFinding finding: Finding needing an asset
        :return: Asset if found/created, None otherwise
        :rtype: Optional[regscale_models.Asset]
        """
        asset = self.get_asset_by_identifier(finding.asset_identifier)
        if not asset:
            asset = self._ensure_asset_for_finding(finding)
        return asset

    def _log_asset_not_found_error(self, finding: IntegrationFinding) -> None:
        """
        Log error when asset is not found for a finding.

        :param IntegrationFinding finding: Finding with missing asset
        :return: None
        :rtype: None
        """
        if not getattr(self, "suppress_asset_not_found_errors", False):
            logger.warning(
                f"Asset not found for identifier {finding.asset_identifier} — "
                "skipping issue creation for this finding"
            )

    def _log_issue_results(self, issues_created: int, issues_skipped: int) -> None:
        """
        Log issue processing results.
        DEPRECATED: Use _log_issue_results_accurate for accurate reporting.

        :param int issues_created: Number of issues created/updated
        :param int issues_skipped: Number of issues skipped
        :return: None
        :rtype: None
        """
        if issues_created > 0:
            logger.info(f"Issues processed: {issues_created} created/updated, {issues_skipped} skipped")
        elif issues_skipped > 0:
            logger.warning(f"Issues processed: 0 created, {issues_skipped} skipped (assets not found)")
        else:
            logger.debug("No issues processed")

    def _log_issue_results_accurate(
        self, issues_created: int, issues_updated: int, findings_processed: int, findings_skipped: int
    ) -> None:
        """
        Log accurate issue processing results based on actual database operations.

        :param int issues_created: Number of new issues created in database
        :param int issues_updated: Number of existing issues updated in database
        :param int findings_processed: Number of findings that were processed
        :param int findings_skipped: Number of findings that were skipped
        :return: None
        :rtype: None
        """
        total_db_operations = issues_created + issues_updated

        if total_db_operations > 0:
            logger.info(
                f"Processed {findings_processed} findings into issues: {issues_created} new issues created, {issues_updated} existing issues updated"
            )
            if findings_skipped > 0:
                logger.info(f"Skipped {findings_skipped} findings (assets not found)")
        elif findings_skipped > 0:
            logger.warning(
                f"Issues processed: 0 created/updated, {findings_skipped} findings skipped (assets not found)"
            )
        else:
            logger.debug(
                f"Processed {findings_processed} findings but no database changes were needed (all issues up-to-date)"
            )

    def _finalize_scan_history(self, scan_history: regscale_models.ScanHistory) -> None:
        """
        Finalize scan history with error handling.

        :param regscale_models.ScanHistory scan_history: Scan history to update
        :return: None
        :rtype: None
        """
        try:
            if getattr(self, "enable_scan_history", True):
                self._update_scan_history(scan_history)
        except Exception:
            self._update_scan_history(scan_history)

    def _ensure_asset_for_finding(self, finding: IntegrationFinding) -> Optional[regscale_models.Asset]:
        """
        Ensure an asset exists for the given finding.

        Attempts to locate the asset by identifier. If missing, it will try to
        build an IntegrationAsset from the first compliance item associated with
        the resource id and upsert it into RegScale, then return the created asset.

        :param IntegrationFinding finding: Finding referencing the asset identifier
        :return: The located or newly created Asset, or None if it cannot be created
        :rtype: Optional[regscale_models.Asset]
        """
        try:
            resource_id = getattr(finding, "asset_identifier", None)
            if not resource_id:
                return None

            # Re-check cache/DB
            asset = self.get_asset_by_identifier(resource_id)
            if asset:
                return asset

            # Use compliance items we already processed to construct an asset
            related_items = self.asset_compliance_map.get(resource_id, [])
            if not related_items:
                return None

            candidate_item = related_items[0]
            integration_asset = self.create_asset_from_compliance_item(candidate_item)
            if not integration_asset:
                return None

            # Persist the asset and refresh lookup
            _ = self.update_regscale_assets(iter([integration_asset]))
            return self.get_asset_by_identifier(resource_id)

        except Exception as ensure_exc:
            logger.debug(
                f"On-demand asset creation failed for {getattr(finding, 'asset_identifier', None)}: {ensure_exc}"
            )
            return None

    def _process_control_assessments(self) -> None:
        """
        Process control assessments based on compliance results.

        This follows the same pattern as the original Wiz compliance integration:
        1. Get control implementations
        2. For each implementation, get the security control using controlID
        3. Match the security control's controlId with the extracted control ID from compliance items

        :return: None
        :rtype: None
        """
        logger.info("Processing control assessments...")

        # Ensure existing records cache (including assessments) is loaded to prevent duplicates
        self._load_existing_records_cache()

        implementations = self._get_control_implementations()
        if not implementations:
            logger.warning("No control implementations found for assessment processing")
            return

        # Build control lookup cache for fast O(1) matching
        self._build_control_lookup_cache(implementations)

        all_control_ids = set(self.passing_controls.keys()) | set(self.failing_controls.keys())
        logger.info(f"Processing assessments for {len(all_control_ids)} controls with compliance data")
        logger.info(f"Control IDs with data: {sorted(list(all_control_ids))}")
        self._log_sample_controls(implementations)

        assessments_created = 0
        processed_impl_today: set[int] = set()
        for control_id in all_control_ids:
            created = self._process_single_control_assessment(
                control_id=control_id,
                implementations=implementations,
                processed_impl_today=processed_impl_today,
            )
            assessments_created += created

        if assessments_created > 0:
            logger.info(f"Successfully created {assessments_created} control assessments")
        passing_assessments = len([cid for cid in all_control_ids if cid not in self.failing_controls])
        failing_assessments = len([cid for cid in all_control_ids if cid in self.failing_controls])
        logger.info(f"Assessment breakdown: {passing_assessments} passing, {failing_assessments} failing")
        logger.debug(f"Control implementation mappings created: {len(self._impl_id_by_control)}")
        if self._impl_id_by_control:
            logger.debug(f"Sample mappings: {dict(list(self._impl_id_by_control.items())[:5])}")
        logger.debug(f"Today's assessments by implementation: {len(self._assessment_by_impl_today)}")
        if self._assessment_by_impl_today:
            logger.debug(f"Sample assessment mappings: {dict(list(self._assessment_by_impl_today.items())[:5])}")

    def _get_control_implementations(self) -> List[ControlImplementation]:
        """
        Get all control implementations for the current plan.

        :return: List of control implementations
        :rtype: List[ControlImplementation]
        """
        implementations: List[ControlImplementation] = ControlImplementation.get_all_by_parent(
            parent_module=self.parent_module, parent_id=self.plan_id
        )
        logger.info(f"Found {len(implementations)} control implementations")
        return implementations

    def _build_control_lookup_cache(self, implementations: List[ControlImplementation]) -> None:
        """
        Build a lookup cache mapping control ID variations to implementations and security controls.

        This dramatically improves performance by:
        1. Fetching all SecurityControl objects once (instead of once per match attempt)
        2. Pre-computing all control ID variations
        3. Creating a dictionary for O(1) lookup instead of O(n) iteration

        For 1011 implementations x 71 controls = 71,781 iterations in the old code.
        New code: 1011 fetches + 71 dictionary lookups = ~1082 operations (67x faster!)

        Also builds a reverse cache (_impl_to_control_id_cache) mapping implementation IDs
        to control IDs for better logging.

        :param List[ControlImplementation] implementations: List of control implementations to cache
        :return: None
        :rtype: None
        """
        if self._control_lookup_cache:
            return

        logger.debug("Building control lookup cache for %d implementations...", len(implementations))
        start_time = time.time()

        # Initialize reverse cache for implementation ID -> control ID lookup
        self._impl_to_control_id_cache: Dict[int, str] = {}

        for implementation in implementations:
            self._cache_single_implementation(implementation)

        elapsed = time.time() - start_time
        logger.info(
            "Built control lookup cache with %d control ID variations in %.2fs",
            len(self._control_lookup_cache),
            elapsed,
        )
        self._log_cached_frameworks_debug()

    def _cache_single_implementation(self, implementation: ControlImplementation) -> None:
        """
        Cache a single implementation's control ID variations.

        :param ControlImplementation implementation: The implementation to cache
        :return: None
        :rtype: None
        """
        try:
            security_control = SecurityControl.get_object(object_id=implementation.controlID)
            if not security_control or not security_control.controlId:
                return

            control_variations = self._control_matcher._get_control_id_variations(security_control.controlId)
            self._add_variations_to_cache(control_variations, implementation, security_control)

        except Exception as e:  # noqa: BLE001
            logger.error(
                "Error caching implementation %d with controlID %s: %s",
                implementation.id,
                implementation.controlID,
                e,
            )

    def _add_variations_to_cache(
        self,
        variations: List[str],
        implementation: ControlImplementation,
        security_control: SecurityControl,
    ) -> None:
        """
        Add control ID variations to the lookup cache.

        :param List[str] variations: Control ID variations to add
        :param ControlImplementation implementation: The implementation to cache
        :param SecurityControl security_control: The security control to cache
        :return: None
        :rtype: None
        """
        for variation in variations:
            if variation not in self._control_lookup_cache:
                self._control_lookup_cache[variation] = (implementation, security_control)

        # Also populate reverse cache for implementation ID -> control ID lookup
        if implementation.id and security_control.controlId:
            self._impl_to_control_id_cache[implementation.id] = security_control.controlId

    def _log_cached_frameworks_debug(self) -> None:
        """
        Log sample controls grouped by framework type for debugging.

        :return: None
        :rtype: None
        """
        if not logger.isEnabledFor(logging.DEBUG):
            return

        frameworks: Dict[str, List[str]] = {}
        for control_id in self._control_lookup_cache.keys():
            framework = self._control_matcher._detect_framework(control_id)
            framework_list = frameworks.setdefault(framework, [])
            if len(framework_list) < 5:
                framework_list.append(control_id)

        for framework, controls in frameworks.items():
            logger.debug("  %s controls (sample): %s", framework, controls)

    def _log_sample_controls(self, implementations: List[ControlImplementation]) -> None:
        """
        Log sample control IDs for debugging purposes.

        :param List[ControlImplementation] implementations: List of implementations to sample from
        :return: None
        :rtype: None
        """
        sample_regscale_controls: List[str] = []
        for impl in implementations[:10]:
            try:
                sec_control = SecurityControl.get_object(object_id=impl.controlID)
                if sec_control and sec_control.controlId:
                    sample_regscale_controls.append(f"{sec_control.controlId}")
                else:
                    sample_regscale_controls.append(f"NoControlId-impl:{impl.id}-controlID:{impl.controlID}")
            except Exception as e:  # noqa: BLE001
                sample_regscale_controls.append(f"ERROR-impl:{impl.id}-controlID:{impl.controlID}-error:{str(e)[:50]}")
                logger.error(
                    f"Error fetching SecurityControl for implementation {impl.id} with controlID {impl.controlID}: {e}"
                )
        logger.info(f"Sample RegScale control IDs available: {sample_regscale_controls}")

    def _process_single_control_assessment(
        self,
        *,
        control_id: str,
        implementations: List[ControlImplementation],
        processed_impl_today: set[int],
    ) -> int:
        """
        Process assessment for a single control.

        :param str control_id: Control identifier to process
        :param List[ControlImplementation] implementations: Available control implementations
        :param set[int] processed_impl_today: Set of implementation IDs already processed today
        :return: Number of assessments created (0 or 1)
        :rtype: int
        """
        try:
            logger.debug(f"Processing control assessment for '{control_id}'")
            impl, sec_control = self._find_matching_implementation(control_id, implementations)
            if not impl or not sec_control:
                self._log_no_match(control_id, implementations)
                return 0

            result = self._determine_overall_result(control_id)
            items = self._get_control_compliance_items(control_id)
            logger.debug(f"Control '{control_id}' assessment: {result} (based on {len(items)} policy assessments)")

            if impl.id in processed_impl_today and self._find_existing_assessment_cached(impl.id, self.scan_date):
                logger.debug(f"Skipping duplicate assessment for implementation {impl.id} (already processed today)")
                # IMPORTANT: Still update the control implementation status even when skipping assessment creation
                # This ensures status is updated on subsequent runs
                if self.update_control_status:
                    logger.debug(f"Updating control implementation status for {control_id} (existing assessment)")
                    self._update_implementation_status(impl, result)
            else:
                self._create_control_assessment(
                    implementation=impl,
                    catalog_control={"id": sec_control.id, "controlId": sec_control.controlId},
                    result=result,
                    control_id=control_id,
                    compliance_items=items,
                )
                processed_impl_today.add(impl.id)

            self._record_control_mapping(control_id, impl.id)
            return 1
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error processing control assessment for '{control_id}': {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return 0

    def _find_matching_implementation(
        self, control_id: str, implementations: List[ControlImplementation]
    ) -> tuple[Optional[ControlImplementation], Optional[SecurityControl]]:
        """
        Find matching implementation and security control for a control ID.

        Uses ControlMatcher for robust control ID matching with leading zero normalization.
        Performance optimized with pre-built lookup cache for O(1) matching.

        :param str control_id: Control identifier to match
        :param List[ControlImplementation] implementations: Available implementations (used for fallback only)
        :return: Tuple of matching implementation and security control, or (None, None)
        :rtype: tuple[Optional[ControlImplementation], Optional[SecurityControl]]
        """
        # Generate all variations of the search control ID for matching
        search_variations = self._control_matcher._get_control_id_variations(control_id)
        if not search_variations:
            logger.warning(f"Could not generate control ID variations for: {control_id}")
            return None, None

        # Log the variations being searched
        logger.debug(f"Searching for control '{control_id}' using variations: {search_variations}")

        # Try to find a match using the pre-built lookup cache (O(1) lookup)
        for variation in search_variations:
            if variation in self._control_lookup_cache:
                implementation, security_control = self._control_lookup_cache[variation]
                logger.debug(
                    f"MATCH FOUND: '{security_control.controlId}' == '{control_id}' (implementation: {implementation.id})"
                )
                return implementation, security_control

        # No match found in cache - log available controls for debugging
        logger.warning(f"NO MATCH for control '{control_id}' with variations {search_variations}")
        if logger.isEnabledFor(logging.DEBUG):
            # Only show sample of cache keys in debug mode to avoid spam
            cache_keys = list(self._control_lookup_cache.keys())[:10]
            logger.debug(f"Sample of available controls in cache: {cache_keys}")
            logger.debug(f"Total controls in cache: {len(self._control_lookup_cache)}")
        return None, None

    def _log_no_match(self, control_id: str, implementations: List[ControlImplementation]) -> None:
        """
        Log when no matching implementation is found for a control.

        :param str control_id: Control identifier that couldn't be matched
        :param List[ControlImplementation] implementations: Available implementations for context
        :return: None
        :rtype: None
        """
        logger.warning(f"No matching implementation found for control ID '{control_id}'")
        sample_impl_controls = []
        for impl in implementations[:5]:
            try:
                sec_control = SecurityControl.get_object(object_id=impl.controlID)
                if sec_control and sec_control.controlId:
                    sample_impl_controls.append(f"{sec_control.controlId} (impl:{impl.id})")
            except Exception:
                sample_impl_controls.append(f"Unknown (impl:{impl.id})")
        logger.debug(f"Sample implementation control IDs (first 5): {sample_impl_controls}")

    def _determine_overall_result(self, control_id: str) -> str:
        """
        Determine overall assessment result for a control.

        :param str control_id: Control identifier to check
        :return: Assessment result ('Pass', 'Fail', or 'Not Applicable')
        :rtype: str
        """
        is_failing = (
            control_id in self.failing_controls
            or control_id.lower() in self.failing_controls
            or control_id.upper() in self.failing_controls
        )
        if is_failing:
            return "Fail"

        is_not_applicable = (
            control_id in self.not_applicable_controls
            or control_id.lower() in self.not_applicable_controls
            or control_id.upper() in self.not_applicable_controls
        )
        if is_not_applicable:
            return self.NOT_APPLICABLE_LABEL

        return "Pass"

    def _get_control_compliance_items(self, control_id: str) -> List[ComplianceItem]:
        """
        Get all compliance items for a specific control.

        :param str control_id: Control identifier to filter by
        :return: List of compliance items for the control
        :rtype: List[ComplianceItem]
        """
        items: List[ComplianceItem] = []
        for item in self.all_compliance_items:
            if hasattr(item, "control_ids"):
                item_control_ids = getattr(item, "control_ids", [])
                if any(cid.lower() == control_id.lower() for cid in item_control_ids):
                    items.append(item)
            elif hasattr(item, "control_id") and item.control_id.lower() == control_id.lower():
                items.append(item)
        return items

    def _record_control_mapping(self, control_id: str, implementation_id: int) -> None:
        """
        Record mapping between normalized control ID and implementation ID.

        :param str control_id: Control identifier to map
        :param int implementation_id: Implementation ID to associate
        :return: None
        :rtype: None
        """
        try:
            base, sub = self._normalize_control_id(control_id)
            canonical = f"{base}({sub})" if sub else base
            self._impl_id_by_control[canonical] = implementation_id
            logger.debug(f"Mapped control '{canonical}' -> implementation ID {implementation_id}")
        except Exception:
            pass

    @staticmethod
    def _parse_control_id(control_id: str) -> tuple[str, Optional[str]]:
        """
        Parse a control id like 'AC-2(1)', 'AC-2 (1)', 'AC-2-1' into (base, sub).
        Normalizes leading zeros (e.g., AC-01 becomes AC-1).

        Returns (base, None) when no subcontrol.

        :param str control_id: Control identifier to parse
        :return: Tuple of (base_control, subcontrol) where subcontrol may be None
        :rtype: tuple[str, Optional[str]]
        """
        cid = control_id.strip()
        # Use precompiled safe regex to avoid catastrophic backtracking on crafted input
        m = SAFE_CONTROL_ID_RE.match(cid)
        if not m:
            return cid.upper(), None
        base = m.group(1).upper()
        # Normalize leading zeros in base control number (e.g., AC-01 -> AC-1)
        if "-" in base:
            prefix, number = base.split("-", 1)
            try:
                normalized_number = str(int(number))
                base = f"{prefix}-{normalized_number}"
            except ValueError:
                pass  # Keep original if conversion fails
        # Subcontrol may be captured in group 2, 3, or 4 depending on the branch matched
        sub = m.group(2) or m.group(3) or m.group(4)
        # Normalize leading zeros in subcontrol (e.g., 01 -> 1)
        if sub:
            try:
                sub = str(int(sub))
            except ValueError:
                pass  # Keep original if conversion fails
        return base, sub

    @classmethod
    def _control_ids_match(cls, a: str, b: str) -> bool:
        """
        Strict match of control ids. Exact match if equal.
        If subcontrols exist on either side, both must exist and be equal.

        :param str a: First control ID to compare
        :param str b: Second control ID to compare
        :return: True if control IDs match according to strict rules
        :rtype: bool
        """
        if not a or not b:
            return False
        if a.strip().lower() == b.strip().lower():
            return True
        base_a, sub_a = cls._parse_control_id(a)
        base_b, sub_b = cls._parse_control_id(b)
        if base_a != base_b:
            return False
        # If either has a subcontrol, require both and equality
        if sub_a or sub_b:
            return (sub_a is not None) and (sub_b is not None) and (sub_a == sub_b)
        # No subcontrols -> base equals
        return True

    @staticmethod
    def _normalize_control_id(control_id: str) -> tuple[str, Optional[str]]:
        """
        Normalize control id to a canonical tuple (BASE, SUB) for set membership.
        Normalizes leading zeros (e.g., AC-01 becomes AC-1).

        :param str control_id: Control identifier to normalize
        :return: Tuple of (base_control, subcontrol) in canonical form
        :rtype: tuple[str, Optional[str]]
        """
        cid = (control_id or "").strip()
        # Use precompiled safe regex to avoid catastrophic backtracking on crafted input
        m = SAFE_CONTROL_ID_RE.match(cid)
        if not m:
            return cid.upper(), None
        base = m.group(1).upper()
        # Normalize leading zeros in base control number (e.g., AC-01 -> AC-1)
        if "-" in base:
            prefix, number = base.split("-", 1)
            try:
                normalized_number = str(int(number))
                base = f"{prefix}-{normalized_number}"
            except ValueError:
                pass  # Keep original if conversion fails
        sub = m.group(2) or m.group(3) or m.group(4)
        # Normalize leading zeros in subcontrol (e.g., 01 -> 1)
        if sub:
            try:
                sub = str(int(sub))
            except ValueError:
                pass  # Keep original if conversion fails
        return base, sub

    def _create_control_assessment(
        self,
        implementation: ControlImplementation,
        catalog_control: Dict,
        result: str,
        control_id: str,
        compliance_items: List[ComplianceItem] = None,
    ) -> None:
        """
        Create or update an assessment for a control implementation.
        If an assessment for the same day exists, update it instead of creating a duplicate.

        :param ControlImplementation implementation: The control implementation to assess
        :param Dict catalog_control: The catalog control data dictionary
        :param str result: Assessment result ('Pass' or 'Fail')
        :param str control_id: Control identifier string
        :param List[ComplianceItem] compliance_items: Pre-aggregated compliance items for this control
        :return: None
        :rtype: None
        """
        try:
            # Use provided compliance items or get them for this control (backward compatibility)
            if compliance_items is None:
                compliance_items = []
                if (
                    control_id in self.failing_controls
                    or control_id.lower() in self.failing_controls
                    or control_id.upper() in self.failing_controls
                ):
                    compliance_items = [
                        item for item in self.failed_compliance_items if item.control_id.lower() == control_id.lower()
                    ]
                else:
                    compliance_items = [
                        item for item in self.all_compliance_items if item.control_id.lower() == control_id.lower()
                    ]

            # Create assessment report
            assessment_report = self._create_assessment_report(control_id, result, compliance_items)

            # Check for existing assessment on the same day using cache
            existing_assessment = self._find_existing_assessment_cached(implementation.id, self.scan_date)

            if existing_assessment:
                # Update existing assessment with new report
                existing_assessment.assessmentResult = result
                existing_assessment.assessmentReport = assessment_report
                existing_assessment.actualFinish = get_current_datetime()
                existing_assessment.dateLastUpdated = get_current_datetime()
                existing_assessment.save()
                logger.info(
                    "Updated existing assessment %d for control %s with new report",
                    existing_assessment.id,
                    control_id,
                )
                # Refresh cache for today
                try:
                    day_key = regscale_string_to_datetime(self.scan_date).date().isoformat()
                except Exception:
                    day_key = str(self.scan_date).split(" ")[0]
                self._existing_assessments_cache[f"{implementation.id}_{day_key}"] = existing_assessment
                # Track today's assessment by implementation id for linking to issues later
                try:
                    self._assessment_by_impl_today[implementation.id] = existing_assessment
                except Exception:
                    pass
            else:
                # Create new assessment
                # leadAssessorId will be set automatically from the token via the Assessment model's default_factory
                assessment = Assessment(
                    title=f"{self.title} compliance assessment for {control_id.upper()}",
                    assessmentType="Control Testing",
                    plannedStart=get_current_datetime(),
                    plannedFinish=get_current_datetime(),
                    actualFinish=get_current_datetime(),
                    assessmentResult=result,
                    assessmentReport=assessment_report,
                    status="Complete",
                    parentId=implementation.id,
                    parentModule="controls",
                    isPublic=True,
                ).create()
                logger.debug(f"Created new assessment {assessment.id} for control {control_id}")
                # Add to cache for today to prevent duplicate creation in subsequent processing
                try:
                    day_key = regscale_string_to_datetime(self.scan_date).date().isoformat()
                except Exception:
                    day_key = str(self.scan_date).split(" ")[0]
                self._existing_assessments_cache[f"{implementation.id}_{day_key}"] = assessment
                # Track today's assessment by implementation id for linking to issues later
                try:
                    self._assessment_by_impl_today[implementation.id] = assessment
                except Exception:
                    pass

            # Update implementation status if needed
            if self.update_control_status:
                self._update_implementation_status(implementation, result)

        except Exception as e:
            logger.error(f"Error creating control assessment: {e}")

    def _find_existing_assessment(self, implementation: ControlImplementation, scan_date) -> Optional:
        """
        Find existing assessment for the same implementation on the same day.
        DEPRECATED: Use _find_existing_assessment_cached instead.

        :param ControlImplementation implementation: The control implementation
        :param scan_date: The scan date to check
        :return: Existing assessment or None
        :rtype: Optional[regscale_models.Assessment]
        """
        logger.warning("_find_existing_assessment is deprecated, use _find_existing_assessment_cached")
        return self._find_existing_assessment_cached(implementation.id, scan_date)

    def _create_assessment_report(self, control_id: str, result: str, compliance_items: List[ComplianceItem]) -> str:
        """
        Create HTML assessment report.

        :param str control_id: Control identifier
        :param str result: Assessment result ('Pass' or 'Fail')
        :param List[ComplianceItem] compliance_items: Compliance items for this control
        :return: Formatted HTML report string
        :rtype: str
        """
        result_color = "#d32f2f" if result == "Fail" else "#2e7d32"

        html_parts = [
            f"""
            <div style="margin-bottom: 20px; padding: 15px; border: 2px solid {result_color};
                        border-radius: 5px; background-color: {'#ffebee' if result == 'Fail' else '#e8f5e8'};">
                <h3 style="margin: 0 0 10px 0; color: {result_color};">
                    {self.title} Compliance Assessment for Control {control_id.upper()}
                </h3>
                <p><strong>Overall Result:</strong>
                   <span style="color: {result_color}; font-weight: bold;">{result}</span></p>
                <p><strong>Assessment Date:</strong> {self.scan_date}</p>
                <p><strong>Framework:</strong> {self.framework}</p>
                <p><strong>Total Policy Assessments:</strong> {len(compliance_items)}</p>
            </div>
            """
        ]  # NOSONAR

        if compliance_items:
            # Group by result for more detailed summary
            compliant_count = len([item for item in compliance_items if item.compliance_result in self.PASS_STATUSES])
            noncompliant_count = len(
                [item for item in compliance_items if item.compliance_result in self.FAIL_STATUSES]
            )
            inconclusive_count = len(
                [item for item in compliance_items if item.compliance_result in self.INCONCLUSIVE_STATUSES]
            )
            not_applicable_count = len(
                [item for item in compliance_items if item.compliance_result in self.NOT_APPLICABLE_STATUSES]
            )

            # Calculate confidence score based on evidence quality
            total_evaluated = compliant_count + noncompliant_count + inconclusive_count
            confidence_score = 0
            if total_evaluated > 0:
                # Confidence is based on the ratio of conclusive evidence (compliant + noncompliant) to total
                conclusive_count = compliant_count + noncompliant_count
                confidence_score = round((conclusive_count / total_evaluated) * 100, 2)

            # Calculate compliance score
            compliance_score = 0
            if (compliant_count + noncompliant_count) > 0:
                compliance_score = round((compliant_count / (compliant_count + noncompliant_count)) * 100, 2)

            # Count unique resources across all policy assessments for this control
            unique_resources = set()
            unique_policies = set()

            for item in compliance_items:
                unique_resources.add(item.resource_id)
                # Get policy name for aggregation
                if hasattr(item, "description") and item.description:  # Check for non-empty description
                    unique_policies.add(
                        item.description[:50] + "..." if len(item.description) > 50 else item.description
                    )
                elif hasattr(item, "policy") and isinstance(item.policy, dict):
                    policy_name = item.policy.get("name", "Unknown Policy")
                    unique_policies.add(policy_name[:50] + "..." if len(policy_name) > 50 else policy_name)

            html_parts.append(
                f"""
            <div style="margin-top: 20px;">
                <h4>Aggregated Assessment Summary</h4>
                <p><strong>Control {control_id} Analysis:</strong>
                   status=<span style="color: {result_color}; font-weight: bold;">{result.upper()}</span>,
                   score={compliance_score:.2f},
                   confidence={confidence_score:.0f},
                   compliant={compliant_count},
                   noncompliant={noncompliant_count},
                   inconclusive={inconclusive_count}
                   {f', not_applicable={not_applicable_count}' if not_applicable_count > 0 else ''}
                </p>
                <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 10px 0;">
                <p><strong>Policy Assessments:</strong> {len(compliance_items)} total</p>
                <p><strong>Unique Policies Tested:</strong> {len(unique_policies)}</p>
                <p><strong>Unique Resources Assessed:</strong> {len(unique_resources)}</p>
                <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 10px 0;">
                <h5>Evidence Breakdown:</h5>
                <p style="margin-left: 20px;">
                    <span style="color: #2e7d32;">✓ Compliant:</span> {compliant_count}<br>
                    <span style="color: #d32f2f;">✗ Non-Compliant:</span> {noncompliant_count}<br>
                    <span style="color: #ff9800;">⚠ Inconclusive:</span> {inconclusive_count}
                    {f'<br><span style="color: #9e9e9e;">- Not Applicable:</span> {not_applicable_count}' if not_applicable_count > 0 else ''}
                </p>
                <hr style="border: 0; border-top: 1px solid #e0e0e0; margin: 10px 0;">
                <p><strong>Compliance Score:</strong> {compliance_score:.2f}%
                   <span style="font-size: 0.9em; color: #666;">(compliant / (compliant + noncompliant))</span></p>
                <p><strong>Confidence Level:</strong> {confidence_score:.0f}%
                   <span style="font-size: 0.9em; color: #666;">(conclusive evidence ratio)</span></p>
                <p><strong>Overall Control Result:</strong>
                   <span style="color: {result_color}; font-weight: bold;">{result}</span></p>
            </div>
             """
            )

            # Add detailed failure information
            if result == "Fail" and noncompliant_count > 0:
                failed_items = [item for item in compliance_items if item.compliance_result in self.FAIL_STATUSES]
                html_parts.append(self._create_failure_details_section(failed_items))

        return "\n".join(html_parts)

    def _create_failure_details_section(self, failed_items: List[ComplianceItem]) -> str:
        """
        Create detailed failure information section for failed compliance items.

        :param List[ComplianceItem] failed_items: List of failed compliance items
        :return: HTML section with detailed failure information
        :rtype: str
        """
        html_parts = [self._get_failure_section_header()]

        for idx, item in enumerate(failed_items, 1):
            html_parts.append(self._process_failed_item(idx, item))

        html_parts.append("</div>")
        return "\n".join(html_parts)

    def _get_failure_section_header(self) -> str:
        """Get the HTML header for failure details section."""
        return """
            <div style="margin-top: 20px; padding: 15px; background-color: #fff3e0;
                        border-left: 4px solid #ff9800; border-radius: 5px;">
                <h4 style="color: #e65100; margin-top: 0;">Failed Evidence Details</h4>
            """

    def _process_failed_item(self, idx: int, item: ComplianceItem) -> str:
        """
        Process a single failed item and return HTML.

        :param int idx: The index of the failed item
        :param ComplianceItem item: The failed compliance item
        :return: HTML for the failed item
        :rtype: str
        """
        if self._has_aws_evidence(item):
            return self._process_aws_item_with_evidence(idx, item)
        return self._process_non_aws_item(idx, item)

    def _has_aws_evidence(self, item: ComplianceItem) -> bool:
        """Check if item has AWS Audit Manager evidence."""
        return hasattr(item, "evidence_items") and item.evidence_items

    def _process_aws_item_with_evidence(self, idx: int, item: ComplianceItem) -> str:
        """Process AWS item with evidence details."""
        evidence_categories = self._categorize_evidence(item)

        if not evidence_categories["failed"]:
            return ""

        html_parts = []
        html_parts.append(self._create_failed_check_header(idx, item, evidence_categories))
        html_parts.append(self._create_failed_evidence_details(evidence_categories["failed"]))
        html_parts.append(self._add_remediation_guidance(item))
        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _categorize_evidence(self, item: ComplianceItem) -> Dict[str, List[Any]]:
        """
        Categorize evidence items by compliance status.

        :param ComplianceItem item: The compliance item with evidence
        :return: Dictionary with categorized evidence
        :rtype: Dict[str, List[Any]]
        """
        categories = {"failed": [], "compliant": [], "inconclusive": []}

        for evidence in item.evidence_items:
            compliance_check = self._get_evidence_compliance_check(item, evidence)

            if compliance_check == "FAILED":
                categories["failed"].append(evidence)
            elif compliance_check == "COMPLIANT":
                categories["compliant"].append(evidence)
            else:
                categories["inconclusive"].append(evidence)

        return categories

    def _get_evidence_compliance_check(self, item: ComplianceItem, evidence: Any) -> Optional[str]:
        """Get compliance check result for evidence."""
        if hasattr(item, "_get_evidence_compliance"):
            return item._get_evidence_compliance(evidence)
        return None

    def _create_failed_check_header(
        self, idx: int, item: ComplianceItem, evidence_categories: Dict[str, List[Any]]
    ) -> str:
        """Create HTML header for failed check."""
        return f"""
            <div style="margin-top: 15px; padding: 10px; background-color: #ffebee; border-radius: 3px;">
                <h5 style="color: #c62828; margin-top: 0;">
                    Failed Check #{idx}: {item.control_id}
                </h5>
                <p><strong>Resource:</strong> {getattr(item, 'resource_name', item.resource_id)}</p>
                <p><strong>Evidence Summary:</strong>
                   {len(evidence_categories["failed"])} failed, {len(evidence_categories["compliant"])} compliant,
                   {len(evidence_categories["inconclusive"])} inconclusive</p>
            """

    def _create_failed_evidence_details(self, failed_evidence: List[Any]) -> str:
        """Create HTML for failed evidence details."""
        html_parts = ['<div style="margin-top: 10px;"><strong>Failed Evidence:</strong><ul>']

        # Limit to 10 failed evidence items
        for evidence in failed_evidence[:10]:
            html_parts.append(self._format_single_evidence(evidence))

        html_parts.append("</ul></div>")
        return "\n".join(html_parts)

    def _format_single_evidence(self, evidence: Dict[str, Any]) -> str:
        """Format a single evidence item as HTML."""
        evidence_html = []
        evidence_source = evidence.get("dataSource", "Unknown source")
        evidence_id = evidence.get("id", "")[:50]

        evidence_html.append(f"<li><strong>Source:</strong> {evidence_source}")

        if evidence_id:
            evidence_html.append(f"<br><strong>Evidence ID:</strong> {evidence_id}")

        resources_info = self._get_resources_info(evidence)
        if resources_info:
            evidence_html.append(f'<br><strong>Resources:</strong><ul><li>{"</li><li>".join(resources_info)}</li></ul>')

        evidence_html.append("</li>")
        return "\n".join(evidence_html)

    def _get_resources_info(self, evidence: Dict[str, Any]) -> List[str]:
        """Extract resource information from evidence."""
        resources_info = []
        resources_included = evidence.get("resourcesIncluded", [])

        # Limit to 5 resources per evidence
        for resource in resources_included[:5]:
            resource_str = self._format_resource(resource)
            if resource_str:
                resources_info.append(resource_str)

        return resources_info

    def _format_resource(self, resource: Dict[str, Any]) -> Optional[str]:
        """Format a single resource as a string."""
        resource_type = resource.get("type", "Unknown")
        resource_value = resource.get("value", "")[:100]
        resource_check = resource.get("complianceCheck", "N/A")

        if resource_value:
            return f"{resource_type}: {resource_value} (Status: {resource_check})"
        return None

    def _add_remediation_guidance(self, item: ComplianceItem) -> str:
        """Add remediation guidance if available."""
        if not (hasattr(item, "action_plan_instructions") and item.action_plan_instructions):
            return ""

        instructions = item.action_plan_instructions[:500]
        truncated = "..." if len(item.action_plan_instructions) > 500 else ""

        return f"""
            <div style="margin-top: 10px; padding: 8px; background-color: #e3f2fd;
                        border-left: 3px solid #1976d2; border-radius: 3px;">
                <strong>Remediation Guidance:</strong><br>
                {instructions}{truncated}
            </div>
            """

    def _process_non_aws_item(self, idx: int, item: ComplianceItem) -> str:
        """Process non-AWS items or items without evidence."""
        description = self._get_item_description(item)

        return f"""
            <div style="margin-top: 15px; padding: 10px; background-color: #ffebee; border-radius: 3px;">
                <h5 style="color: #c62828; margin-top: 0;">Failed Check #{idx}: {item.control_id}</h5>
                <p><strong>Resource:</strong> {getattr(item, 'resource_name', item.resource_id)}</p>
                <p><strong>Description:</strong> {description}</p>
            </div>
            """

    def _get_item_description(self, item: ComplianceItem) -> str:
        """Get description from item without truncation to show full failure details."""
        if hasattr(item, "description"):
            return item.description
        return "N/A"

    def _get_security_plan(self) -> Optional[regscale_models.SecurityPlan]:
        """
        Get the security plan for this integration.

        :return: SecurityPlan instance or None
        :rtype: Optional[regscale_models.SecurityPlan]
        """
        if not self._security_plan_loaded:
            self._security_plan_loaded = True  # Mark as attempted to prevent repeated calls
            try:
                logger.info(f"[SECURITY PLAN] Retrieving security plan with ID: {self.plan_id}")
                self._security_plan = SecurityPlan.get_object(object_id=self.plan_id)
                if self._security_plan:
                    logger.info(
                        f"[SECURITY PLAN] Retrieved security plan: {getattr(self._security_plan, 'systemName', 'N/A')}"
                    )
                    logger.info(
                        f"[SECURITY PLAN] complianceSettingsId: {getattr(self._security_plan, 'complianceSettingsId', None)}"
                    )
                else:
                    logger.warning(f"[SECURITY PLAN] No security plan found with ID: {self.plan_id}")
            except Exception as e:
                logger.error(f"[SECURITY PLAN] Error getting security plan {self.plan_id}: {e}")
                # Don't set to None - keep as None but mark as loaded to prevent retry
        return self._security_plan

    def _get_compliance_settings(self) -> Optional[regscale_models.ComplianceSettings]:
        """
        Get compliance settings for the security plan.

        :return: ComplianceSettings instance or None
        :rtype: Optional[regscale_models.ComplianceSettings]
        """
        if not self._compliance_settings_loaded:
            self._compliance_settings_loaded = True  # Mark as attempted to prevent repeated calls
            try:
                security_plan = self._get_security_plan()
                logger.debug(f"[COMPLIANCE SETTINGS] Security plan retrieved: {security_plan is not None}")
                if security_plan:
                    logger.debug(
                        f"[COMPLIANCE SETTINGS] Security plan systemName: {getattr(security_plan, 'systemName', 'N/A')}"
                    )
                    logger.debug(f"[COMPLIANCE SETTINGS] Security plan ID: {getattr(security_plan, 'id', 'N/A')}")
                    logger.debug(
                        f"[COMPLIANCE SETTINGS] Has complianceSettingsId attribute: {hasattr(security_plan, 'complianceSettingsId')}"
                    )
                    logger.debug(
                        f"[COMPLIANCE SETTINGS] complianceSettingsId value: {getattr(security_plan, 'complianceSettingsId', 'None')}"
                    )

                if self._has_valid_compliance_settings_id(security_plan):
                    self._compliance_settings = self._fetch_compliance_settings(security_plan)
                else:
                    self._log_missing_compliance_settings_reason(security_plan)
            except Exception as e:
                logger.debug(f"Error getting compliance settings: {e}")
                import traceback

                logger.debug(f"Full traceback: {traceback.format_exc()}")
                # Don't set to None - keep as None but mark as loaded to prevent retry
        return self._compliance_settings

    def _has_valid_compliance_settings_id(self, security_plan) -> bool:
        """Check if security plan has valid compliance settings ID."""
        return security_plan and hasattr(security_plan, "complianceSettingsId") and security_plan.complianceSettingsId

    def _fetch_compliance_settings(self, security_plan) -> Optional[regscale_models.ComplianceSettings]:
        """Fetch and log compliance settings."""
        logger.debug(f"Retrieving compliance settings with ID: {security_plan.complianceSettingsId}")
        compliance_settings = ComplianceSettings.get_object(object_id=security_plan.complianceSettingsId)

        if compliance_settings:
            logger.debug(f"Using compliance settings: {compliance_settings.title}")
            logger.debug(
                f"Compliance settings has field groups: {bool(getattr(compliance_settings, 'complianceSettingsFieldGroups', None))}"
            )
        else:
            logger.debug(f"No compliance settings found for ID: {security_plan.complianceSettingsId}")

        return compliance_settings

    def _log_missing_compliance_settings_reason(self, security_plan) -> None:
        """Log specific reason why compliance settings are not available."""
        if not security_plan:
            logger.debug("Security plan not found")
        elif not hasattr(security_plan, "complianceSettingsId"):
            logger.debug("Security plan does not have complianceSettingsId attribute")
        elif not security_plan.complianceSettingsId:
            logger.debug("Security plan has no complianceSettingsId set")

    def _get_implementation_status_from_result(self, result: str, override: Optional[str] = None) -> str:
        """
        Get implementation status based on assessment result using enum-based mappings.
        Results are cached to avoid repeated calculations for the same input.

        :param str result: Assessment result ('Pass', 'Fail', 'Not Applicable', etc.)
        :param Optional[str] override: Optional override value to use instead of the mapping
        :return: Implementation status string
        :rtype: str
        """
        # Use override directly if provided
        if override:
            return override

        # Handle None or empty result
        if not result:
            logger.warning("Received None or empty result for status mapping, defaulting to 'Unknown'")
            return "Unknown"

        # Check cache first to avoid repeated calculations
        cache_key = result.lower().strip()
        if cache_key in self._status_mapping_cache:
            cached_status = self._status_mapping_cache[cache_key]
            logger.debug(f"[STATUS MAPPING] Using cached mapping for '{result}': '{cached_status}'")
            return cached_status

        logger.info(f"[STATUS MAPPING] Getting implementation status for result: {result}")

        # Try to use the compliance settings mapping function
        compliance_settings = self._get_compliance_settings()
        if compliance_settings:
            logger.info(f"[STATUS MAPPING] Using compliance settings '{compliance_settings.title}' for mapping")
            try:
                mapped_status = compliance_settings.get_implementation_status_for_result(result, None)
                logger.info(f"[STATUS MAPPING] Mapped '{result}' to '{mapped_status}' using compliance settings")
                # Cache the result
                self._status_mapping_cache[cache_key] = mapped_status
                return mapped_status
            except Exception as e:
                logger.warning(f"[STATUS MAPPING] Error using compliance settings mapping: {e}")

        # Fallback: Use the class method directly if no compliance settings instance
        framework = self._detect_compliance_framework()
        logger.info(f"[STATUS MAPPING] Using framework '{framework}' for fallback mapping")
        mapped_status = ComplianceSettings.get_status_mapping(framework, result, None)
        logger.info(f"[STATUS MAPPING] Mapped '{result}' to '{mapped_status}' using fallback")
        # Cache the result
        self._status_mapping_cache[cache_key] = mapped_status
        return mapped_status

    def _update_implementation_status(self, implementation: ControlImplementation, result: str) -> None:
        """
        Update control implementation status based on assessment result.
        Uses compliance settings from the security plan if available, otherwise falls back to defaults.

        :param ControlImplementation implementation: Control implementation to update
        :param str result: Assessment result ('Pass' or 'Fail')
        :return: None
        :rtype: None
        """
        try:
            # Get status from compliance settings or fallback to default
            new_status = self._get_implementation_status_from_result(result)

            # Update implementation status
            implementation.status = new_status
            implementation.dateLastAssessed = get_current_datetime()
            implementation.lastAssessmentResult = result

            # Ensure required fields are set if empty
            if not implementation.responsibility:
                implementation.responsibility = ControlImplementation.get_default_responsibility(
                    parent_id=implementation.parentId
                )
                logger.debug(
                    f"Setting default responsibility for implementation {implementation.id}: {implementation.responsibility}"
                )

            if not implementation.implementation:
                control_id = (
                    getattr(implementation.control, "controlId", "control") if implementation.control else "control"
                )
                implementation.implementation = f"Implementation details for {control_id} will be documented."
                logger.debug(f"Setting default implementation statement for implementation {implementation.id}")

            implementation.save()

            # Look up control ID from cache for better logging
            control_id_display = "unknown"
            if hasattr(self, "_impl_to_control_id_cache") and implementation.id in self._impl_to_control_id_cache:
                control_id_display = self._impl_to_control_id_cache[implementation.id]

            logger.info(
                "Updated control implementation %d status to '%s' (control: %s)",
                implementation.id,
                new_status,
                control_id_display,
            )

            # Update objectives if they exist
            objectives = ImplementationObjective.get_all_by_parent(
                parent_module=implementation.get_module_slug(),
                parent_id=implementation.id,
            )

            for objective in objectives:
                objective.status = new_status
                objective.save()
                logger.debug("Updated objective %d status to '%s'", objective.id, new_status)

        except Exception as e:
            logger.error(f"Error updating implementation status: {e}")

    def _get_controls(self) -> List[Dict]:
        """
        Get controls from catalog or plan.

        :return: List of control dictionaries from catalog or plan
        :rtype: List[Dict]
        """
        if self.catalog_id:
            catalog = Catalog.get_with_all_details(catalog_id=self.catalog_id)
            return catalog.get("controls", []) if catalog else []
        else:
            return SecurityControl.get_controls_by_parent_id_and_module(
                parent_module=self.parent_module, parent_id=self.plan_id, return_dicts=True
            )

    def _find_existing_asset_by_resource_id(self, resource_id: str) -> Optional[regscale_models.Asset]:
        """
        Find existing asset by resource ID.

        :param str resource_id: Resource identifier to search for
        :return: Existing asset or None if not found
        :rtype: Optional[regscale_models.Asset]
        """
        try:
            if hasattr(self, "asset_map_by_identifier") and self.asset_map_by_identifier:
                return self.asset_map_by_identifier.get(resource_id)

            # Query database
            existing_assets = regscale_models.Asset.get_all_by_parent(
                parent_id=self.plan_id,
                parent_module=self.parent_module,
            )

            for asset in existing_assets:
                if hasattr(asset, "otherTrackingNumber") and asset.otherTrackingNumber == resource_id:
                    return asset

            return None

        except Exception as e:
            logger.error(f"Error finding existing asset: {e}")
            return None

    def _map_resource_type_to_asset_type(self, compliance_item: ComplianceItem) -> str:
        """
        Map compliance item resource type to RegScale asset type.

        :param ComplianceItem compliance_item: Compliance item with resource type information
        :return: Asset type string suitable for RegScale
        :rtype: str
        """
        # Default implementation - can be overridden by subclasses
        return "Cloud Resource"

    def _map_severity(self, severity: Optional[str]) -> regscale_models.IssueSeverity:
        """
        Map compliance severity to RegScale severity.

        :param Optional[str] severity: Severity string from compliance source
        :return: Mapped RegScale severity enum value
        :rtype: regscale_models.IssueSeverity
        """
        if not severity:
            return regscale_models.IssueSeverity.Moderate

        severity_mapping = {
            "CRITICAL": regscale_models.IssueSeverity.Critical,
            "HIGH": regscale_models.IssueSeverity.High,
            "MEDIUM": regscale_models.IssueSeverity.Moderate,
            "LOW": regscale_models.IssueSeverity.Low,
        }

        return severity_mapping.get(severity.upper(), regscale_models.IssueSeverity.Moderate)

    def _map_severity_to_priority(self, severity: regscale_models.IssueSeverity) -> str:
        """
        Map severity to priority string.

        :param regscale_models.IssueSeverity severity: Issue severity enum value
        :return: Priority string for issues
        :rtype: str
        """
        priority_mapping = {
            regscale_models.IssueSeverity.Critical: "Critical",
            regscale_models.IssueSeverity.High: "High",
            regscale_models.IssueSeverity.Moderate: "Medium",
            regscale_models.IssueSeverity.Low: "Low",
        }

        return priority_mapping.get(severity, "Medium")

    def _update_scan_history(self, scan_history: regscale_models.ScanHistory) -> None:
        """
        Update scan history with results.

        :param regscale_models.ScanHistory scan_history: Scan history record to update
        :return: None
        :rtype: None
        """
        try:
            scan_history.dateLastUpdated = get_current_datetime()
            scan_history.save()
            logger.debug(f"Updated scan history {scan_history.id}")
        except Exception as e:
            logger.error(f"Error updating scan history: {e}")

    def create_scan_history(self) -> regscale_models.ScanHistory:
        """
        Create or reuse a ScanHistory for the same day and tool.

        If a scan history exists for this plan/module with the same
        scanning tool and scan date (day-level), update and reuse it
        instead of creating a duplicate.

        :return: Created or reused scan history record
        :rtype: regscale_models.ScanHistory
        """
        try:
            # Load existing scans for the plan/module
            existing_scans = regscale_models.ScanHistory.get_all_by_parent(
                parent_id=self.plan_id, parent_module=self.parent_module
            )

            # Normalize target date to date component only
            target_dt = self.scan_date
            target_date_only = target_dt.split("T")[0] if isinstance(target_dt, str) else str(target_dt)[:10]

            # Find an existing scan for today and this tool
            for scan in existing_scans:
                try:
                    if getattr(scan, "scanningTool", None) == self.title and getattr(scan, "scanDate", None):
                        scan_date = str(scan.scanDate)
                        scan_date_only = scan_date.split("T")[0]
                        if scan_date_only == target_date_only:
                            # Reuse this scan history; refresh last updated
                            scan.dateLastUpdated = get_current_datetime()
                            scan.save()
                            return scan
                except Exception:
                    # Skip any malformed scan records
                    continue

            # No existing same-day scan found, create new via base behavior
            return super().create_scan_history()
        except Exception:
            # Fallback: create new scan history
            return super().create_scan_history()

    def create_or_update_issue_from_finding(self, title: str, finding: IntegrationFinding) -> regscale_models.Issue:
        """
        Create or update an issue from a finding, using cache to prevent duplicates.

        Properly handles milestone creation for compliance integrations.

        :param str title: Issue title
        :param IntegrationFinding finding: The finding to create issue from
        :return: Created or updated issue
        :rtype: regscale_models.Issue
        """
        # Load cache if not already loaded
        self._load_existing_records_cache()

        # Check for existing issue by external_id first
        external_id = finding.external_id
        logger.debug(f"Looking for existing issue with external_id: '{external_id}'")
        existing_issue = self._find_existing_issue_cached(external_id)

        if existing_issue:
            logger.debug(
                f"Found existing issue {existing_issue.id} (other_identifier: '{existing_issue.otherIdentifier}') for lookup external_id '{external_id}', updating instead of creating"
            )

            # Store original status for milestone comparison
            original_status = existing_issue.status

            # Update existing issue with new finding data
            existing_issue.title = title
            existing_issue.description = finding.description
            existing_issue.severityLevel = finding.severity
            existing_issue.status = finding.status
            # Ensure affectedControls is updated from the finding's control id
            try:
                if getattr(finding, "control_labels", None):
                    existing_issue.affectedControls = ",".join(finding.control_labels)
                else:
                    # Fall back to normalized control id from rule_id/control_labels
                    ctl = None
                    if getattr(finding, "rule_id", None):
                        ctl = finding.rule_id
                    elif getattr(finding, "control_labels", None):
                        labels = list(finding.control_labels)
                        ctl = labels[0] if labels else None
                    if ctl:
                        base, sub = self._normalize_control_id(ctl)
                        existing_issue.affectedControls = f"{base}({sub})" if sub else base
            except Exception:
                pass
            existing_issue.dateLastUpdated = self.scan_date
            # Set organization ID based on Issue Owner or SSP Owner hierarchy
            existing_issue.orgId = self.determine_issue_organization_id(existing_issue.issueOwnerId)
            existing_issue.save()

            # Create milestone if status changed
            # Reconstruct original issue state for comparison
            original_issue = regscale_models.Issue()
            original_issue.status = original_status
            self._create_milestones_for_updated_issue(existing_issue, finding, original_issue)

            return existing_issue
        else:
            # No existing issue found, create new one using parent method
            logger.debug(f"No existing issue found for external_id {external_id}, creating new issue")
            return super().create_or_update_issue_from_finding(title, finding)

    def _create_milestones_for_updated_issue(
        self,
        issue: regscale_models.Issue,
        finding: IntegrationFinding,
        original_issue: regscale_models.Issue,
    ) -> None:
        """
        Create milestones for an updated issue in compliance integration.

        This method handles both status transition milestones and backfilling of missing
        creation milestones for existing issues.

        :param regscale_models.Issue issue: The updated issue
        :param IntegrationFinding finding: The finding data
        :param regscale_models.Issue original_issue: Original state for comparison
        """
        milestone_manager = self.get_milestone_manager()

        # First, ensure the issue has a creation milestone (backfill if missing)
        milestone_manager.ensure_creation_milestone_exists(issue=issue, finding=finding)

        # Then, handle status transition milestones
        milestone_manager.create_milestones_for_issue(
            issue=issue,
            finding=finding,
            existing_issue=original_issue,
        )
