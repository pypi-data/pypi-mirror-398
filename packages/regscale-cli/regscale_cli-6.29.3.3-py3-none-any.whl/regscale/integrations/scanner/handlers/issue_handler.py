#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue Handler for Scanner Integrations.

This module provides a handler class for issue-related operations during scanner processing.
It consolidates issue creation, update, and lookup functionality from ScannerIntegration.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.due_date_handler import DueDateHandler
from regscale.integrations.milestone_manager import MilestoneManager
from regscale.integrations.scanner.cache import IssueCache
from regscale.integrations.variables import ScannerVariables
from regscale.models import regscale_models
from regscale.models.regscale_models.batch_options import IssueBatchOptions
from regscale.utils.threading import ThreadSafeDict

if TYPE_CHECKING:
    from regscale.integrations.scanner.models import IntegrationFinding

logger = logging.getLogger("regscale")


class IssueHandler:
    """
    Handler for issue-related operations during scanner processing.

    This class provides centralized issue management including:
    - Building issues from findings for batch operations
    - Setting issue fields based on finding data
    - Batch issue operations with server-side deduplication
    - Building batch options for server-side create/update decisions

    Note: This handler does NOT perform client-side lookups for existing issues.
    The server handles deduplication via UniqueKeyFields in batch options.

    Attributes:
        plan_id: The ID of the security plan or component
        parent_module: The parent module string (e.g., "securityplans" or "components")
        issue_cache: IssueCache instance (retained for compatibility but not used for lookups)
        assessor_id: The ID of the assessor for issue ownership
        title: The integration title for source report
    """

    def __init__(
        self,
        plan_id: int,
        parent_module: str,
        issue_cache: IssueCache,
        assessor_id: str,
        title: str,
        is_component: bool = False,
        issue_identifier_field: Optional[str] = None,
        due_date_handler: Optional[DueDateHandler] = None,
        kev_data: Optional[ThreadSafeDict[str, Any]] = None,
        get_finding_identifier: Optional[Callable[["IntegrationFinding"], str]] = None,
        get_control_implementation_id_for_cci: Optional[Callable[[str], Optional[int]]] = None,
        determine_issue_organization_id: Optional[Callable[[str], Optional[int]]] = None,
    ) -> None:
        """
        Initialize the IssueHandler.

        :param int plan_id: The ID of the security plan or component
        :param str parent_module: The parent module string
        :param IssueCache issue_cache: IssueCache instance for lookups
        :param str assessor_id: The ID of the assessor for issue ownership
        :param str title: The integration title for source report
        :param bool is_component: Whether this is a component integration
        :param Optional[str] issue_identifier_field: Integration-specific identifier field name
        :param Optional[DueDateHandler] due_date_handler: Handler for due date calculations
        :param Optional[ThreadSafeDict[str, Any]] kev_data: CISA KEV data for vulnerability lookups
        :param Optional[Callable] get_finding_identifier: Callback to get finding identifier
        :param Optional[Callable] get_control_implementation_id_for_cci: Callback for CCI mapping
        :param Optional[Callable] determine_issue_organization_id: Callback for org ID determination
        """
        self.plan_id = plan_id
        self.parent_module = parent_module
        self.issue_cache = issue_cache
        # Use provided assessor_id or fallback to current user
        self.assessor_id = assessor_id or regscale_models.Issue.get_user_id() or ""
        if not self.assessor_id:
            logger.warning("No assessor_id available - issues may fail validation without issueOwnerId")
        self.title = title
        self.is_component = is_component
        self.issue_identifier_field = issue_identifier_field
        self.app = Application()

        # Due date handler - create default if not provided
        self.due_date_handler = due_date_handler or DueDateHandler(title, config=self.app.config)

        # KEV data for vulnerability lookups
        self._kev_data = kev_data or ThreadSafeDict()

        # Callback functions for integration-specific operations
        self._get_finding_identifier = get_finding_identifier
        self._get_control_implementation_id_for_cci = get_control_implementation_id_for_cci
        self._determine_issue_organization_id = determine_issue_organization_id

        # Milestone manager - lazy initialization
        self._milestone_manager: Optional[MilestoneManager] = None
        self._scan_date: str = ""

        # POAM tracking
        self._max_poam_id: Optional[int] = None

        # Lock registry for thread-safe operations
        self._lock_registry: ThreadSafeDict[str, threading.RLock] = ThreadSafeDict()
        self._global_lock = threading.Lock()

        # Deduplication tracking
        self._dedup_lock = threading.Lock()
        self._dedup_stats: Dict[str, int] = {"new": 0, "existing": 0}

    def set_scan_date(self, scan_date: str) -> None:
        """
        Set the scan date for milestone creation.

        :param str scan_date: The scan date string
        """
        self._scan_date = scan_date

    def get_milestone_manager(self) -> MilestoneManager:
        """
        Get or create the milestone manager.

        :return: The MilestoneManager instance
        :rtype: MilestoneManager
        """
        if self._milestone_manager is None:
            self._milestone_manager = MilestoneManager(
                integration_title=self.title,
                assessor_id=self.assessor_id,
                scan_date=self._scan_date or get_current_datetime(),
            )
        return self._milestone_manager

    def _get_lock(self, key: str) -> threading.RLock:
        """
        Get or create a lock for a specific key.

        :param str key: The key to get a lock for
        :return: The lock for the key
        :rtype: threading.RLock
        """
        with self._global_lock:
            if key not in self._lock_registry:
                self._lock_registry[key] = threading.RLock()
            return self._lock_registry[key]

    def create_or_update_issue(
        self,
        title: str,
        finding: "IntegrationFinding",
    ) -> regscale_models.Issue:
        """
        Build a RegScale issue from a finding for batch operations.

        Note: This method builds the issue but does NOT perform client-side lookups.
        The server handles create vs update decisions via UniqueKeyFields in batch options.

        :param str title: The title of the issue
        :param IntegrationFinding finding: The finding data
        :return: The built RegScale issue ready for batch submission
        :rtype: regscale_models.Issue
        """
        issue_status = finding.get_issue_status()
        finding_id = self._get_finding_id(finding)

        self._log_finding_processing_info(finding, finding_id, issue_status, title)

        # Build issue without client-side lookup - server handles deduplication
        return self._build_issue_from_finding(finding, issue_status, title)

    def _get_finding_id(self, finding: "IntegrationFinding") -> str:
        """
        Get the finding identifier using the callback or default method.

        :param IntegrationFinding finding: The finding data
        :return: The finding identifier
        :rtype: str
        """
        if self._get_finding_identifier:
            return self._get_finding_identifier(finding)
        # Default behavior - use external_id or generate from title/plugin
        return finding.external_id or f"{finding.plugin_id}:{finding.title}"

    def _log_finding_processing_info(
        self,
        finding: "IntegrationFinding",
        finding_id: str,
        issue_status: regscale_models.IssueStatus,
        title: str,
    ) -> None:
        """
        Log finding processing information for debugging.

        :param IntegrationFinding finding: The finding data
        :param str finding_id: The generated finding ID
        :param IssueStatus issue_status: The issue status
        :param str title: The issue title
        """
        title_preview = title[:50] if len(title) > 50 else title
        logger.debug(
            "PROCESSING FINDING: external_id=%s, finding_id=%s, status=%s, title='%s...'",
            finding.external_id,
            finding_id,
            issue_status,
            title_preview,
        )

        if issue_status == regscale_models.IssueStatus.Closed:
            logger.debug("CLOSED FINDING: This will create/update a CLOSED issue (status=%s)", issue_status)

    def find_existing_issue(
        self,
        finding: "IntegrationFinding",  # noqa: ARG002
    ) -> Optional[regscale_models.Issue]:
        """
        Deprecated: Client-side lookups are no longer performed.

        The server handles deduplication via UniqueKeyFields in batch options.
        This method is retained for backward compatibility but always returns None.

        :param IntegrationFinding finding: The finding data (unused)
        :return: Always returns None - server handles deduplication
        :rtype: Optional[regscale_models.Issue]
        """
        # Server handles deduplication via UniqueKeyFields - no client-side lookup needed
        return None

    def _build_issue_from_finding(
        self,
        finding: "IntegrationFinding",
        issue_status: regscale_models.IssueStatus,
        title: str,
    ) -> regscale_models.Issue:
        """
        Build a RegScale issue from finding data.

        Note: This method only builds the issue object. It does NOT save or create
        the issue. The server handles create vs update decisions via batch options.

        :param IntegrationFinding finding: The finding data
        :param IssueStatus issue_status: The status of the issue
        :param str title: The title of the issue
        :return: The built RegScale issue ready for batch submission
        :rtype: regscale_models.Issue
        """
        # Prepare issue data
        issue_title = self._get_issue_title(finding) or title
        description = finding.description or ""
        remediation_description = finding.recommendation_for_mitigation or finding.remediation or ""
        is_poam = self._is_poam(finding)

        # Create new issue object
        issue = regscale_models.Issue()

        # Get asset identifier (no consolidation needed - server handles deduplication)
        asset_identifier = finding.issue_asset_identifier_value or finding.asset_identifier

        # Set basic issue fields
        self._set_basic_issue_fields(issue, finding, issue_status, issue_title, asset_identifier)

        # Set due date
        self._set_issue_due_date(issue, finding)

        # Set additional issue fields
        self._set_additional_issue_fields(issue, finding, description, remediation_description)

        # Set control-related fields
        self._set_control_fields(issue, finding)

        # Set risk and operational fields
        self._set_risk_and_operational_fields(issue, finding, is_poam)

        # Update KEV data if CVE exists
        if finding.cve:
            issue = self._lookup_kev_and_update_issue(cve=finding.cve, issue=issue)

        # Set POAM identifier if applicable
        if is_poam and not finding.poam_id and ScannerVariables.incrementPoamIdentifier:
            issue.otherIdentifier = f"V-{self._get_next_poam_id():04d}"
        elif finding.poam_id:
            issue.otherIdentifier = finding.poam_id

        return issue

    def set_issue_fields(self, issue: regscale_models.Issue, finding: "IntegrationFinding") -> regscale_models.Issue:
        """
        Set all fields on an issue from a finding.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        :return: The updated issue
        :rtype: regscale_models.Issue
        """
        issue_status = finding.get_issue_status()
        issue_title = self._get_issue_title(finding)
        description = finding.description or ""
        remediation_description = finding.recommendation_for_mitigation or finding.remediation or ""
        is_poam = self._is_poam(finding)
        asset_identifier = self._get_consolidated_asset_identifier(finding, None)

        self._set_basic_issue_fields(issue, finding, issue_status, issue_title, asset_identifier)
        self._set_issue_due_date(issue, finding)
        self._set_additional_issue_fields(issue, finding, description, remediation_description)
        self._set_control_fields(issue, finding)
        self._set_risk_and_operational_fields(issue, finding, is_poam)

        if finding.cve:
            issue = self._lookup_kev_and_update_issue(cve=finding.cve, issue=issue)

        return issue

    def _set_basic_issue_fields(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
        issue_status: regscale_models.IssueStatus,
        issue_title: str,
        asset_identifier: str,
    ) -> None:
        """
        Set basic fields for the issue.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        :param IssueStatus issue_status: The issue status
        :param str issue_title: The issue title
        :param str asset_identifier: The asset identifier
        """
        issue.parentId = self.plan_id
        issue.parentModule = self.parent_module
        # Only set vulnerabilityId if it's a valid ID (> 0)
        # When bulk_create is used, vulnerability.id is 0 until bulk_save completes
        if finding.vulnerability_id and finding.vulnerability_id > 0:
            issue.vulnerabilityId = finding.vulnerability_id
        issue.title = issue_title
        issue.dateCreated = finding.date_created
        issue.status = issue_status
        issue.dateCompleted = (
            self._get_date_completed(finding, issue_status)
            if issue_status == regscale_models.IssueStatus.Closed
            else None
        )
        issue.severityLevel = finding.severity
        issue.issueOwnerId = self.assessor_id
        issue.securityPlanId = self.plan_id if not self.is_component else None
        issue.identification = finding.identification
        issue.dateFirstDetected = finding.first_seen
        issue.assetIdentifier = finding.issue_asset_identifier_value or asset_identifier

        # Set organization ID based on Issue Owner or SSP Owner hierarchy
        if self._determine_issue_organization_id:
            issue.orgId = self._determine_issue_organization_id(issue.issueOwnerId)

    def _set_issue_due_date(self, issue: regscale_models.Issue, finding: "IntegrationFinding") -> None:
        """
        Set the due date for the issue using DueDateHandler.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        """
        # Calculate or validate due date (past date validation controlled by noPastDueDates setting)
        if not finding.due_date:
            # No due date set, calculate new one
            try:
                base_created = finding.date_created or issue.dateCreated or get_current_datetime()
                finding.due_date = self.due_date_handler.calculate_due_date(
                    severity=finding.severity,
                    created_date=base_created,
                    cve=finding.cve,
                    title=finding.title or self.title,
                )
            except Exception as e:
                logger.warning("Error calculating due date with DueDateHandler: %s", e)
                # Final fallback to a Low severity default if anything goes wrong
                base_created = finding.date_created or issue.dateCreated or get_current_datetime()
                finding.due_date = self.due_date_handler.calculate_due_date(
                    severity=regscale_models.IssueSeverity.Low,
                    created_date=base_created,
                    cve=finding.cve,
                    title=finding.title or self.title,
                )
        else:
            # Due date already exists, but validate it's not in the past (if noPastDueDates is enabled)
            finding.due_date = self.due_date_handler._ensure_future_due_date(
                finding.due_date, self.due_date_handler.integration_timelines.get(finding.severity, 60)
            )

        issue.dueDate = finding.due_date

    def _set_additional_issue_fields(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
        description: str,
        remediation_description: str,
    ) -> None:
        """
        Set additional fields for the issue.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        :param str description: The issue description
        :param str remediation_description: The remediation description
        """
        issue.description = description
        issue.sourceReport = finding.source_report or self.title
        issue.recommendedActions = finding.recommendation_for_mitigation
        issue.securityChecks = finding.security_check or finding.external_id
        issue.remediationDescription = remediation_description
        issue.integrationFindingId = self._get_finding_id(finding)
        issue.poamComments = finding.poam_comments
        issue.cve = finding.cve
        issue.assessmentId = finding.assessment_id

        # Set issue identifier fields (e.g., wizId, otherIdentifier) before save/create
        self._set_issue_identifier_fields_internal(issue, finding)

    def _set_control_fields(self, issue: regscale_models.Issue, finding: "IntegrationFinding") -> None:
        """
        Set control-related fields for the issue.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        """
        control_id = None
        if finding.cci_ref and self._get_control_implementation_id_for_cci:
            control_id = self._get_control_implementation_id_for_cci(finding.cci_ref)
        # Note: controlId is deprecated, using controlImplementationIds instead
        cci_control_ids = [control_id] if control_id is not None else []

        # Ensure failed control labels (e.g., AC-4(21)) are present in affectedControls
        if finding.affected_controls:
            issue.affectedControls = finding.affected_controls
        elif finding.control_labels:
            issue.affectedControls = ", ".join(sorted({cl for cl in finding.control_labels if cl}))

        issue.controlImplementationIds = list(set(finding._control_implementation_ids + cci_control_ids))

    def _set_risk_and_operational_fields(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
        is_poam: bool,
    ) -> None:
        """
        Set risk and operational fields for the issue.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        :param bool is_poam: Whether this is a POAM issue
        """
        issue.isPoam = is_poam
        issue.basisForAdjustment = (
            finding.basis_for_adjustment if finding.basis_for_adjustment else f"{self.title} import"
        )
        issue.pluginId = finding.plugin_id
        issue.originalRiskRating = regscale_models.Issue.assign_risk_rating(finding.severity)
        issue.changes = (
            f"<p>Current: {finding.milestone_changes}</p><p>Planned: {finding.planned_milestone_changes}</p>"
        )
        issue.adjustedRiskRating = finding.adjusted_risk_rating
        issue.riskAdjustment = finding.risk_adjustment
        issue.operationalRequirement = finding.operational_requirements
        issue.deviationRationale = finding.deviation_rationale
        issue.dateLastUpdated = get_current_datetime()
        issue.affectedControls = finding.affected_controls

    def _set_issue_identifier_fields_internal(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
    ) -> None:
        """
        Set issue identifier fields (e.g., wizId) on the issue object without saving.

        :param regscale_models.Issue issue: The issue to update
        :param IntegrationFinding finding: The finding data
        """
        if not finding.external_id:
            logger.debug("finding.external_id is empty: %s", finding.external_id)
            return

        logger.debug("Setting issue identifier fields: external_id=%s", finding.external_id)

        # Set otherIdentifier field (the external ID field in Issue model)
        if not getattr(issue, "otherIdentifier", None):  # Only set if not already set
            issue.otherIdentifier = finding.external_id
            logger.debug("Set otherIdentifier = %s", finding.external_id)

        # Set the specific identifier field if configured (e.g., wizId for Wiz)
        if self.issue_identifier_field and hasattr(issue, self.issue_identifier_field):
            current_value = getattr(issue, self.issue_identifier_field)
            if not current_value:  # Only set if not already set
                setattr(issue, self.issue_identifier_field, finding.external_id)
                logger.debug("Set %s = %s", self.issue_identifier_field, finding.external_id)
            else:
                logger.debug("%s already set to: %s", self.issue_identifier_field, current_value)
        else:
            if self.issue_identifier_field:  # Only log warning if field is configured
                logger.warning(
                    "Cannot set issue_identifier_field: field='%s', hasattr=%s",
                    self.issue_identifier_field,
                    hasattr(issue, self.issue_identifier_field),
                )

    def _save_or_create_issue(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",  # noqa: ARG002
    ) -> regscale_models.Issue:
        """
        Deprecated: Use batch operations with server-side deduplication instead.

        This method is retained for backward compatibility but should not be used
        for new integrations. The server handles create vs update decisions via
        UniqueKeyFields in batch options.

        :param regscale_models.Issue issue: The issue to save
        :param IntegrationFinding finding: The finding data (unused)
        :return: The issue (unchanged)
        :rtype: regscale_models.Issue
        """
        logger.warning(
            "Deprecated: _save_or_create_issue called. Use batch operations with server-side deduplication instead."
        )
        # Return the issue unchanged - batch operations handle save/create
        return issue

    def _handle_property_and_milestone_creation(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
        existing_issue: Optional[regscale_models.Issue] = None,
    ) -> None:
        """
        Handle property creation and milestone creation for an issue.

        :param regscale_models.Issue issue: The issue to handle
        :param IntegrationFinding finding: The finding data
        :param Optional[regscale_models.Issue] existing_issue: Existing issue for milestone comparison
        """
        # Handle property creation
        self._create_issue_properties(issue, finding)

        # Handle milestone creation
        self._create_issue_milestones(issue, finding, existing_issue)

    def _create_issue_properties(self, issue: regscale_models.Issue, finding: "IntegrationFinding") -> None:
        """
        Create properties for an issue based on finding data.

        :param regscale_models.Issue issue: The issue to create properties for
        :param IntegrationFinding finding: The finding data
        """
        if poc := finding.point_of_contact:
            self._create_property_safe(issue, "POC", poc, "POC property")

        if finding.is_cwe and finding.plugin_id:
            self._create_property_safe(issue, "CWE", finding.plugin_id, "CWE property")

    def _create_property_safe(
        self,
        issue: regscale_models.Issue,
        key: str,
        value: str,
        property_type: str,
    ) -> None:
        """
        Safely create a property with error handling.

        Validates that the issue has a valid ID before attempting to create the property.
        When bulk_create=True is used for issue creation, issue.id is 0 until bulk_save() completes.
        In this case, property creation is skipped.

        :param regscale_models.Issue issue: The issue to create property for
        :param str key: The property key
        :param str value: The property value
        :param str property_type: Description for logging purposes
        """
        # Validate that the issue has a valid ID, skip if not
        # When bulk_create=True, issue.id is 0 until bulk_save() completes
        if not issue or not issue.id or issue.id == 0:
            logger.debug(
                "Skipping %s creation: issue ID is invalid or queued for bulk save (issue=%s, id=%s)",
                property_type,
                "None" if not issue else "present",
                issue.id if issue else "N/A",
            )
            return

        try:
            regscale_models.Property(
                key=key,
                value=value,
                parentId=issue.id,
                parentModule="issues",
            ).create_or_update()
            logger.debug("Added %s %s to issue %s", property_type, value, issue.id)
        except Exception as e:
            logger.warning("Failed to create %s for issue %s: %s", property_type, issue.id, str(e))

    def _create_issue_milestones(
        self,
        issue: regscale_models.Issue,
        finding: "IntegrationFinding",
        existing_issue: Optional[regscale_models.Issue],
    ) -> None:
        """
        Create milestones for an issue based on status transitions.

        Delegates to MilestoneManager for cleaner separation of concerns.
        Also ensures existing issues have creation milestones (backfills if missing).

        :param regscale_models.Issue issue: The issue to create milestones for
        :param IntegrationFinding finding: The finding data
        :param Optional[regscale_models.Issue] existing_issue: Existing issue for comparison
        """
        milestone_manager = self.get_milestone_manager()

        # For existing issues, ensure they have a creation milestone (backfill if missing)
        if existing_issue:
            milestone_manager.ensure_creation_milestone_exists(issue=issue, finding=finding)

        # Handle status transition milestones
        milestone_manager.create_milestones_for_issue(
            issue=issue,
            finding=finding,
            existing_issue=existing_issue,
        )

    def batch_create_issues(self, issues: List[regscale_models.Issue]) -> List[regscale_models.Issue]:
        """
        Batch create issues in RegScale.

        :param List[regscale_models.Issue] issues: List of issues to create
        :return: List of created issues
        :rtype: List[regscale_models.Issue]
        """
        if not issues:
            return []

        logger.info("Batch creating %d issue(s) in RegScale", len(issues))

        # Use the batch_create method from RegScaleModel
        return regscale_models.Issue.batch_create(issues)

    def _build_default_batch_options(self) -> IssueBatchOptions:
        """
        Build default batch options for server-side issue deduplication.

        The server uses these options to determine create vs update decisions
        based on UniqueKeyFields matching.

        :return: Default batch options for issue operations
        :rtype: IssueBatchOptions
        """
        return IssueBatchOptions(
            source=self.title,
            uniqueKeyFields=["integrationFindingId"],
            enableMopUp=True,
            mopUpStatus="Closed",
            parentId=self.plan_id,
            parentModule=self.parent_module,
        )

    def get_batch_options(self, **overrides: Any) -> IssueBatchOptions:
        """
        Get batch options with optional overrides.

        :param overrides: Key-value pairs to override default options
        :return: Batch options with overrides applied
        :rtype: IssueBatchOptions
        """
        options = self._build_default_batch_options()
        for key, value in overrides.items():
            if key in IssueBatchOptions.__annotations__:
                options[key] = value  # type: ignore[literal-required]
        return options

    def _get_issue_title(self, finding: "IntegrationFinding") -> str:
        """
        Get the issue title based on the POAM Title Type variable.

        :param IntegrationFinding finding: The finding data
        :return: The issue title
        :rtype: str
        """
        issue_title = finding.title or ""
        if ScannerVariables.poamTitleType.lower() == "pluginid" or not issue_title:
            issue_title = (
                f"{finding.plugin_id or finding.cve or finding.rule_id}: {finding.plugin_name or finding.description}"
            )
        return issue_title[:450]

    def _get_date_completed(
        self,
        finding: "IntegrationFinding",
        issue_status: regscale_models.IssueStatus,
    ) -> Optional[str]:
        """
        Get the date completed for a closed issue.

        :param IntegrationFinding finding: The finding data
        :param IssueStatus issue_status: The issue status
        :return: The date completed or None
        :rtype: Optional[str]
        """
        if issue_status == regscale_models.IssueStatus.Closed:
            return finding.last_seen or get_current_datetime()
        return None

    @staticmethod
    def _get_consolidated_asset_identifier(
        finding: "IntegrationFinding",
        existing_issue: Optional[regscale_models.Issue] = None,  # noqa: ARG004
    ) -> str:
        """
        Deprecated: Asset identifier consolidation is now handled server-side.

        This method is retained for backward compatibility but simply returns
        the finding's asset identifier. The server handles consolidation via
        batch operations.

        :param IntegrationFinding finding: The finding data
        :param Optional[regscale_models.Issue] existing_issue: Unused - retained for compatibility
        :return: The asset identifier from the finding
        :rtype: str
        """
        # Server handles asset identifier consolidation - just return the finding's value
        return finding.issue_asset_identifier_value or finding.asset_identifier

    def _get_other_identifier(self, finding: "IntegrationFinding", is_poam: bool) -> Optional[str]:
        """
        Get the other identifier for an issue.

        :param IntegrationFinding finding: The finding data
        :param bool is_poam: Whether this is a POAM issue
        :return: The other identifier if applicable
        :rtype: Optional[str]
        """
        # If existing POAM ID is greater than the cached max, update the cached max
        if finding.poam_id:
            if (poam_id := self._parse_poam_id(finding.poam_id)) and poam_id > (self._max_poam_id or 0):
                self._max_poam_id = poam_id
            return finding.poam_id

        # Only called if isPoam is True and creating a new issue
        if is_poam and ScannerVariables.incrementPoamIdentifier:
            return f"V-{self._get_next_poam_id():04d}"
        return None

    @staticmethod
    def _parse_poam_id(poam_id: str) -> Optional[int]:
        """
        Parse a POAM ID string to extract the numeric value.

        :param str poam_id: The POAM ID string (e.g., "V-0001")
        :return: The numeric POAM ID or None if parsing fails
        :rtype: Optional[int]
        """
        try:
            # Handle format like "V-0001" or just "0001"
            if "-" in poam_id:
                return int(poam_id.split("-")[1])
            return int(poam_id)
        except (ValueError, IndexError):
            return None

    def _get_next_poam_id(self) -> int:
        """
        Get the next POAM ID for issue creation.

        :return: The next POAM ID
        :rtype: int
        """
        if self._max_poam_id is None:
            self._max_poam_id = 0
        self._max_poam_id += 1
        return self._max_poam_id

    def _is_poam(self, finding: "IntegrationFinding") -> bool:
        """
        Determine if an issue should be considered a Plan of Action and Milestones (POAM).

        :param IntegrationFinding finding: The finding to check
        :return: True if the issue should be a POAM, False otherwise
        :rtype: bool
        """
        if (
            ScannerVariables.vulnerabilityCreation.lower() == "poamcreation"
            or ScannerVariables.complianceCreation.lower() == "poam"
        ):
            return True
        if finding.due_date < get_current_datetime():
            return True
        return False

    def _lookup_kev_and_update_issue(
        self,
        cve: str,
        issue: regscale_models.Issue,
    ) -> regscale_models.Issue:
        """
        Determine if the CVE is part of the published CISA KEV list.

        Note: Due date handling is managed by DueDateHandler. This method only sets kevList field.

        :param str cve: The CVE to lookup in CISA's KEV list
        :param regscale_models.Issue issue: The issue to update kevList field
        :return: The updated issue
        :rtype: regscale_models.Issue
        """
        issue.kevList = "No"

        if self._kev_data is not None:
            vulnerabilities: List[Dict[str, Any]] = (
                self._kev_data.get("vulnerabilities", []) if isinstance(self._kev_data, dict) else []
            )
            kev_data = next(
                (entry for entry in vulnerabilities if entry.get("cveID", "").lower() == cve.lower()),
                None,
            )
            if kev_data:
                issue.kevList = "Yes"

        return issue

    def _extra_data_to_properties(self, finding: "IntegrationFinding", issue_id: int) -> None:
        """
        Add extra data to properties for an issue in a separate thread.

        :param IntegrationFinding finding: The finding data
        :param int issue_id: The ID of the issue
        """

        def _create_property():
            """Create the property in a separate thread."""
            if not finding.extra_data:
                return
            try:
                regscale_models.Property(
                    key="source_file_path",
                    value=finding.extra_data.get("source_file_path"),
                    parentId=issue_id,
                    parentModule="issues",
                ).create()
            except Exception as exc:
                logger.error("Error creating property for issue %s: %s", issue_id, exc)

        # Start the property creation in a separate thread
        thread = threading.Thread(target=_create_property, daemon=True)
        thread.start()

    def get_dedup_stats(self) -> Dict[str, int]:
        """
        Get deduplication statistics.

        :return: Dictionary with 'new' and 'existing' counts
        :rtype: Dict[str, int]
        """
        with self._dedup_lock:
            return self._dedup_stats.copy()

    def reset_dedup_stats(self) -> None:
        """Reset deduplication statistics."""
        with self._dedup_lock:
            self._dedup_stats = {"new": 0, "existing": 0}
