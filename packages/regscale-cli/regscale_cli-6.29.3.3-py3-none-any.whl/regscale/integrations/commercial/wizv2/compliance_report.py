#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiz Compliance Report Integration for RegScale CLI."""

import csv
import gzip
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from regscale.core.app.utils.app_utils import error_and_exit
from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.wizv2.file_cleanup import ReportFileCleanup
from regscale.integrations.commercial.wizv2.reports import WizReportManager
from regscale.integrations.commercial.wizv2.variables import WizVariables
from regscale.integrations.commercial.wizv2.core.auth import wiz_authenticate
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.integrations.control_matcher import ControlMatcher
from regscale.models import regscale_models
from regscale.models.regscale_models.control_implementation import ControlImplementation
from regscale.models.regscale_models.issue import IssueIdentification

logger = logging.getLogger("regscale")


class WizComplianceReportItem(ComplianceItem):
    """Compliance item parsed from Wiz CSV report."""

    def __init__(self, csv_row: Dict[str, str]):
        """
        Initialize from CSV row data.

        :param Dict[str, str] csv_row: Row data from CSV report
        """
        self.csv_data = csv_row
        self._resource_name = csv_row.get("Resource Name", "")  # Use _resource_name to avoid conflict with property
        self.cloud_provider = csv_row.get("Cloud Provider", "")
        self.cloud_provider_id = csv_row.get("Cloud Provider ID", "")
        self._resource_id = csv_row.get("Resource ID", "")  # Use _resource_id to avoid conflict with property
        self.resource_region = csv_row.get("Resource Region", "")
        self.subscription = csv_row.get("Subscription", "")
        self.subscription_name = csv_row.get("Subscription Name", "")
        self.policy_name = csv_row.get("Policy Name", "")
        self.policy_id = csv_row.get("Policy ID", "")
        self.result = csv_row.get("Result", "")
        self._severity = csv_row.get("Severity", "")  # Use _severity to avoid conflict with property
        self.compliance_check_name = csv_row.get("Compliance Check Name (Wiz Subcategory)", "")
        self._framework = csv_row.get("Framework", "")  # Use _framework to avoid conflict with property
        self.remediation_steps = csv_row.get("Remediation Steps", "")

    # ComplianceItem abstract property implementations
    @property
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        return self.cloud_provider_id or self._resource_id or self._resource_name or "Unknown"

    @property
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        return self.get_unique_resource_name()

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        return self.get_control_id()

    @property
    def compliance_result(self) -> str:
        """Result of compliance check (PASS, FAIL, etc)."""
        return self.result

    @property
    def severity(self) -> Optional[str]:
        """Severity level of the compliance violation (if failed)."""
        return self._severity if self._severity else None

    @property
    def description(self) -> str:
        """Description of the compliance check."""
        return self.get_finding_details()

    @property
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CSF)."""
        if not self._framework:
            return "NIST800-53R5"

        # Normalize Wiz framework names to RegScale format
        framework_mappings = {
            "NIST SP 800-53 Revision 5": "NIST800-53R5",
            "NIST SP 800-53 Rev 5": "NIST800-53R5",
            "NIST SP 800-53 R5": "NIST800-53R5",
            "NIST 800-53 Revision 5": "NIST800-53R5",
            "NIST 800-53 Rev 5": "NIST800-53R5",
            "NIST 800-53 R5": "NIST800-53R5",
        }

        return framework_mappings.get(self._framework, self._framework)

    def get_control_id(self) -> str:
        """Extract first control ID from compliance check name for compatibility."""
        control_ids = self.get_all_control_ids()
        return control_ids[0] if control_ids else ""

    def get_all_control_ids(self) -> list:
        """Extract all control IDs from compliance check name and normalize leading zeros."""
        if not self.compliance_check_name:
            return []

        control_id_pattern = r"([A-Za-z]{2}-\d+)(?:\s*\(\s*(\d+)\s*\))?"
        control_ids = []

        for part in self.compliance_check_name.split(", "):
            matches = re.findall(control_id_pattern, part.strip())
            for match in matches:
                base_control, enhancement = match
                normalized_control = self._normalize_base_control(base_control)
                formatted_control = self._format_control_id(normalized_control, enhancement)
                control_ids.append(formatted_control)

        return control_ids

    def _normalize_base_control(self, base_control: str) -> str:
        """Normalize leading zeros in base control number (e.g., AC-01 -> AC-1)."""
        if "-" in base_control:
            prefix, number = base_control.split("-", 1)
            try:
                normalized_number = str(int(number))
                return f"{prefix.upper()}-{normalized_number}"
            except ValueError:
                return base_control.upper()
        else:
            return base_control.upper()

    def _format_control_id(self, base_control: str, enhancement: str) -> str:
        """Format control ID with optional enhancement."""
        if enhancement:
            # Normalize enhancement number to remove leading zeros
            try:
                normalized_enhancement = str(int(enhancement))
            except ValueError:
                normalized_enhancement = enhancement
            return f"{base_control}({normalized_enhancement})"
        else:
            return base_control

    @property
    def affected_controls(self) -> str:
        """Get affected controls as comma-separated string for issues."""
        control_ids = self.get_all_control_ids()
        return ",".join(control_ids) if control_ids else self.control_id

    def get_status(self) -> str:
        """Get compliance status based on result."""
        return "Satisfied" if self.result.lower() == "pass" else "Other Than Satisfied"

    def get_implementation_status(self) -> str:
        """Get implementation status based on result."""
        return "Implemented" if self.result.lower() == "pass" else "In Remediation"

    def get_severity(self) -> str:
        """Map Wiz severity to RegScale severity."""
        severity_map = {"CRITICAL": "High", "HIGH": "High", "MEDIUM": "Moderate", "LOW": "Low", "INFORMATIONAL": "Low"}
        return severity_map.get(self._severity.upper(), "Low")

    def get_unique_resource_name(self) -> str:
        """Get a unique resource name by appending provider ID or resource ID."""
        base_name = self._resource_name
        if not base_name:
            base_name = "Unknown Resource"

        # Add region if available
        if self.resource_region:
            base_name = f"{base_name} ({self.resource_region})"

        # Add unique identifier (prefer resource_id over cloud_provider_id)
        unique_id = self._resource_id or self.cloud_provider_id
        if unique_id:
            # Extract just the last part of Azure resource IDs for brevity
            if "/" in unique_id:
                unique_suffix = unique_id.split("/")[-1]
            else:
                unique_suffix = unique_id

            # Only append if not already in the name
            if unique_suffix.lower() not in base_name.lower():
                base_name = f"{base_name} [{unique_suffix[:12]}]"  # Limit to 12 chars

        return base_name

    def get_unique_issue_identifier(self) -> str:
        """Get a unique identifier for deduplication of issues."""
        # Use resource_id + policy_id + control_id for uniqueness
        resource_key = self._resource_id or self.cloud_provider_id or self._resource_name
        policy_key = self.policy_id or self.policy_name
        control_key = self.get_control_id()
        return f"{resource_key}|{policy_key}|{control_key}"

    def get_title(self) -> str:
        """Get assessment title."""
        return f"{self.get_control_id()} - {self.policy_name}"

    def get_description(self) -> str:
        """Get assessment description."""
        return f"Wiz compliance assessment for {self.get_unique_resource_name()} - {self.policy_name}"

    def get_finding_details(self) -> str:
        """Get finding details for issues."""
        details = f"Resource: {self.get_unique_resource_name()}\n"
        details += f"Cloud Provider: {self.cloud_provider}\n"
        if self.subscription_name:
            details += f"Subscription: {self.subscription_name}\n"
        details += f"Result: {self.result}\n"
        details += f"Remediation: {self.remediation_steps}"
        return details

    def get_asset_identifier(self) -> str:
        """Get asset identifier using cloud provider ID for issues."""
        return self.cloud_provider_id or self._resource_id or self._resource_name or "Unknown"


class WizComplianceReportProcessor(ComplianceIntegration):
    """Process compliance reports from Wiz and create assessments in RegScale."""

    # Server-side batch deduplication requires a standard RegScale Asset field name
    # The Wiz ID is stored in otherTrackingNumber for deduplication purposes
    asset_identifier_field: str = "otherTrackingNumber"

    def __init__(
        self,
        plan_id: int,
        wiz_project_id: str,
        client_id: str,
        client_secret: str,
        regscale_module: str = "securityplans",
        create_poams: bool = False,
        report_file_path: Optional[str] = None,
        bypass_control_filtering: bool = False,
        max_report_age_days: int = 7,
        force_fresh_report: bool = False,
        reuse_existing_reports: bool = True,
        **kwargs,
    ):
        """
        Initialize the compliance report processor.

        :param int plan_id: RegScale plan/SSP ID
        :param str wiz_project_id: Wiz project ID
        :param str client_id: Wiz client ID
        :param str client_secret: Wiz client secret
        :param str regscale_module: RegScale module to use
        :param bool create_poams: Whether to create POAMs for failed assessments
        :param Optional[str] report_file_path: Path to existing report file to use instead of creating new one
        :param bool bypass_control_filtering: Skip control filtering for performance with large control sets
        :param int max_report_age_days: Maximum age in days for reusing existing reports (default: 7 days)
        :param bool force_fresh_report: Force creation of fresh report, ignoring existing reports
        :param bool reuse_existing_reports: Whether to reuse existing Wiz reports instead of creating new ones (default: True)
        """
        # Call parent constructor with ComplianceIntegration parameters
        super().__init__(
            plan_id=plan_id,
            framework="NIST800-53R5",
            create_poams=create_poams,
            parent_module=regscale_module,
            **kwargs,
        )

        # Wiz-specific attributes
        self.wiz_project_id = wiz_project_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.report_file_path = report_file_path
        self.bypass_control_filtering = bypass_control_filtering
        self.max_report_age_days = max_report_age_days
        self.force_fresh_report = force_fresh_report
        self.reuse_existing_reports = reuse_existing_reports
        self.title = "Wiz Compliance"  # Required by ScannerIntegration

        # Initialize Wiz authentication
        access_token = wiz_authenticate(client_id, client_secret)
        if not access_token:
            error_and_exit("Failed to authenticate with Wiz")

        self.report_manager = WizReportManager(WizVariables.wizUrl, access_token)

        # Initialize control matcher for robust control ID matching (inherited from parent but ensure it's set)
        if not hasattr(self, "_control_matcher"):
            self._control_matcher = ControlMatcher()

    def parse_csv_report(self, file_path: str) -> List[WizComplianceReportItem]:
        """
        Parse CSV compliance report.

        :param str file_path: Path to CSV report file
        :return: List of compliance items
        :rtype: List[WizComplianceReportItem]
        """
        items = []

        try:
            # Handle gzipped files
            if file_path.endswith(".gz"):
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        items.append(WizComplianceReportItem(row))
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        items.append(WizComplianceReportItem(row))

            logger.info(f"Parsed {len(items)} compliance items from report")
            return items

        except Exception as e:
            logger.error(f"Error parsing CSV report: {e}")
            return []

    # ComplianceIntegration abstract method implementations
    def fetch_compliance_data(self) -> List[Dict[str, str]]:
        """
        Fetch raw compliance data from CSV report.

        :return: List of raw compliance data (CSV rows as dictionaries)
        :rtype: List[Dict[str, str]]
        """
        # Use provided report file or get/create one
        if self.report_file_path and os.path.exists(self.report_file_path):
            report_file_path = self.report_file_path
        else:
            report_file_path = self._get_or_create_report()
            if not report_file_path or not os.path.exists(report_file_path):
                logger.error("Failed to get compliance report")
                return []

        # Read CSV file and return raw data
        raw_data = []
        try:
            with open(report_file_path, "r", encoding="utf-8") as file:
                csv_reader = csv.DictReader(file)
                raw_data = list(csv_reader)

            logger.info(f"Fetched {len(raw_data)} raw compliance records from CSV")
            return raw_data

        except Exception as e:
            logger.error(f"Error reading CSV report: {e}")
            return []

    def create_compliance_item(self, raw_data: Dict[str, str]) -> ComplianceItem:
        """
        Create a ComplianceItem from raw compliance data.

        :param Dict[str, str] raw_data: Raw compliance data from CSV row
        :return: ComplianceItem instance
        :rtype: ComplianceItem
        """
        return WizComplianceReportItem(raw_data)

    def _map_string_severity_to_enum(self, severity_str: str) -> regscale_models.IssueSeverity:
        """
        Convert string severity to regscale_models.IssueSeverity enum.

        :param str severity_str: String severity like "HIGH", "MEDIUM", etc.
        :return: IssueSeverity enum value
        :rtype: regscale_models.IssueSeverity
        """
        severity_mapping = {
            "CRITICAL": regscale_models.IssueSeverity.Critical,
            "HIGH": regscale_models.IssueSeverity.High,
            "MEDIUM": regscale_models.IssueSeverity.Moderate,
            "MODERATE": regscale_models.IssueSeverity.Moderate,
            "LOW": regscale_models.IssueSeverity.Low,
            "INFORMATIONAL": regscale_models.IssueSeverity.Low,
        }
        return severity_mapping.get(severity_str.upper(), regscale_models.IssueSeverity.Low)

    def process_compliance_data(self) -> None:
        """
        Override the parent method to implement bypass logic for large control sets.
        """
        if self.bypass_control_filtering:
            logger.info("Bypassing control filtering due to bypass_control_filtering=True")
            # Call parent method but bypass the allowed_controls_normalized logic
            self._process_compliance_data_without_filtering()
        else:
            # Use standard parent implementation
            super().process_compliance_data()

    def _process_compliance_data_without_filtering(self) -> None:
        """
        Process compliance data without control filtering for performance.
        """
        logger.info("Processing compliance data without control filtering...")

        self._reset_compliance_state()
        raw_compliance_data = self.fetch_compliance_data()
        self._process_raw_compliance_items(raw_compliance_data)
        self._log_processing_debug_info()
        self._categorize_controls_fail_first()
        self._log_processing_summary()
        self._log_categorization_debug_info()

    def _reset_compliance_state(self) -> None:
        """Reset state to avoid double counting on repeated calls."""
        self.all_compliance_items = []
        self.failed_compliance_items = []
        self.passing_controls = {}
        self.failing_controls = {}
        self.asset_compliance_map.clear()

    def _process_raw_compliance_items(self, raw_compliance_data: List[Any], allowed_controls: set = None) -> dict:
        """Convert raw compliance data to ComplianceItem objects.

        :param List[Any] raw_compliance_data: Raw compliance data from CSV row
        :param set allowed_controls: Allowed control IDs (unused in this override, provided for interface compatibility)
        :return: Processing statistics dictionary (empty dict for this implementation)
        :rtype: dict
        """
        for raw_item in raw_compliance_data:
            try:
                compliance_item = self.create_compliance_item(raw_item)

                if not self._is_valid_compliance_item_for_processing(compliance_item):
                    continue

                self._add_compliance_item_to_collections(compliance_item)

            except Exception as e:
                logger.error(f"Error processing compliance item: {e}")
                continue

        # Return empty stats dict for interface compatibility
        return {}

    def _is_valid_compliance_item_for_processing(self, compliance_item: Any) -> bool:
        """Check if compliance item has required control and resource IDs.

        :param Any compliance_item: Compliance item to check
        :return: True if compliance item has required control and resource IDs
        :rtype: bool
        """
        control_id = getattr(compliance_item, "control_id", "")
        resource_id = getattr(compliance_item, "resource_id", "")
        return bool(control_id and resource_id)

    def _add_compliance_item_to_collections(self, compliance_item: Any) -> None:
        """Add compliance item to appropriate collections and categorize.

        :param Any compliance_item: Compliance item to add to collections
        :return: None
        :rtype: None
        """
        self.all_compliance_items.append(compliance_item)
        self.asset_compliance_map[compliance_item.resource_id].append(compliance_item)

        # Categorize by result - normalize to handle case variations
        result_lower = compliance_item.compliance_result.lower()
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]

        if result_lower in fail_statuses_lower:
            self.failed_compliance_items.append(compliance_item)

    def _log_processing_debug_info(self) -> None:
        """
        Log debug information before categorization.

        Logs sample compliance item data and status configurations
        to help with debugging categorization issues.

        :return: None
        :rtype: None
        """
        logger.debug(f"About to categorize {len(self.all_compliance_items)} compliance items")
        if self.all_compliance_items:
            sample_item = self.all_compliance_items[0]
            logger.debug(
                f"DEBUG: Sample item control_id='{sample_item.control_id}', result='{sample_item.compliance_result}'"
            )
            logger.debug(f"FAIL_STATUSES = {self.FAIL_STATUSES}")
            logger.debug(f"PASS_STATUSES = {self.PASS_STATUSES}")

    def _log_processing_summary(self, raw_compliance_data: list = None, stats: dict = None) -> None:
        """
        Log summary of processed compliance items.

        Provides a summary count of total items, passing items, failing items,
        and control categorization results for monitoring processing progress.

        :param list raw_compliance_data: Raw compliance data (unused in this implementation, for interface compatibility)
        :param dict stats: Processing statistics (unused in this implementation, for interface compatibility)
        :return: None
        :rtype: None
        """
        passing_count = len(self.all_compliance_items) - len(self.failed_compliance_items)
        failing_count = len(self.failed_compliance_items)

        logger.info(
            f"Processed {len(self.all_compliance_items)} compliance items: "
            f"{passing_count} passing, {failing_count} failing"
        )
        logger.info(
            f"Control categorization: {len(self.passing_controls)} passing controls, "
            f"{len(self.failing_controls)} failing controls"
        )

    def _log_categorization_debug_info(self) -> None:
        """
        Log debug information about categorized controls.

        Outputs lists of passing and failing control IDs for debugging
        categorization logic and identifying potential issues.

        :return: None
        :rtype: None
        """
        if self.passing_controls:
            logger.debug(f"Passing control IDs: {list(self.passing_controls.keys())}")
        if self.failing_controls:
            logger.debug(f"Failing control IDs: {list(self.failing_controls.keys())}")
        if not self.passing_controls and not self.failing_controls:
            logger.error(
                "DEBUG: No controls were categorized! This indicates an issue in _categorize_controls_fail_first"
            )

    def _categorize_controls_fail_first(self) -> None:
        """
        Categorize controls using fail-first logic.

        If ANY compliance item for a control is failing, the entire control is marked as failing.
        A control is only marked as passing if ALL instances of that control are passing.
        """
        logger.info("Starting fail-first control categorization...")

        control_results = self._determine_control_results()
        self._populate_control_collections(control_results)
        self._populate_failed_compliance_items()
        self._log_categorization_completion()

    def _determine_control_results(self) -> Dict[str, str]:
        """
        Determine pass/fail status for each control based on compliance items.

        Analyzes all compliance items and applies fail-first logic to determine
        the overall status for each control. A control is marked as "fail" if
        ANY compliance item for that control is failing.

        :return: Dictionary mapping control IDs (lowercase) to "pass" or "fail"
        :rtype: Dict[str, str]
        """
        control_results = {}  # {control_id: "pass" or "fail"}

        for item in self.all_compliance_items:
            control_ids = self._get_control_ids_for_item(item)

            for control_id in control_ids:
                if not control_id:
                    continue

                control_id_lower = control_id.lower()

                if self._is_compliance_item_failing(item):
                    control_results[control_id_lower] = "fail"
                    logger.debug(f"Control {control_id} marked as FAILING due to failed item")
                elif control_id_lower not in control_results:
                    control_results[control_id_lower] = "pass"

        return control_results

    def _get_control_ids_for_item(self, item: Any) -> List[str]:
        """
        Get all control IDs for a compliance item.

        Extracts control IDs from compliance items that may reference
        multiple controls (e.g., multi-control compliance checks).

        :param Any item: Compliance item to extract control IDs from
        :return: List of control ID strings
        :rtype: List[str]
        """
        if hasattr(item, "get_all_control_ids"):
            return item.get_all_control_ids()
        else:
            return [item.control_id] if item.control_id else []

    def _is_compliance_item_failing(self, item: Any) -> bool:
        """
        Check if a compliance item is failing.

        Compares the compliance result against the list of failure statuses
        using case-insensitive matching.

        :param Any item: Compliance item to check
        :return: True if the item is failing, False otherwise
        :rtype: bool
        """
        result_lower = item.compliance_result.lower()
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]
        return result_lower in fail_statuses_lower

    def _populate_control_collections(self, control_results: Dict[str, str]) -> None:
        """
        Populate passing and failing control collections.

        Based on the control results dictionary, populates the passing_controls
        and failing_controls collections with the appropriate compliance items.

        :param Dict[str, str] control_results: Dictionary mapping control IDs to "pass" or "fail"
        :return: None
        :rtype: None
        """
        for control_id_lower, result in control_results.items():
            if result == "fail":
                self.failing_controls[control_id_lower] = self._get_items_for_control(control_id_lower)
            else:
                self.passing_controls[control_id_lower] = self._get_items_for_control(control_id_lower)

    def _get_items_for_control(self, control_id_lower: str) -> List[Any]:
        """
        Get all compliance items that belong to a specific control.

        Searches through all compliance items to find those that reference
        the specified control ID (case-insensitive matching).

        :param str control_id_lower: Control ID in lowercase format
        :return: List of compliance items for the control
        :rtype: List[Any]
        """
        items = []
        for item in self.all_compliance_items:
            item_control_ids = self._get_normalized_control_ids_for_item(item)
            if control_id_lower in item_control_ids:
                items.append(item)
        return items

    def _get_normalized_control_ids_for_item(self, item: Any) -> List[str]:
        """
        Get normalized (lowercase) control IDs for an item.

        Extracts all control IDs from a compliance item and normalizes
        them to lowercase for consistent comparison and matching.

        :param Any item: Compliance item to extract control IDs from
        :return: List of normalized control ID strings
        :rtype: List[str]
        """
        if hasattr(item, "get_all_control_ids"):
            return [cid.lower() for cid in item.get_all_control_ids()]
        else:
            return [item.control_id.lower()] if item.control_id else []

    def _populate_failed_compliance_items(self) -> None:
        """
        Populate and deduplicate the failed compliance items list.

        Collects all failing compliance items from the failing_controls
        collection and removes duplicates to create a clean list of
        failed items for issue processing.

        :return: None
        :rtype: None
        """
        self.failed_compliance_items.clear()

        for control_id, failing_items in self.failing_controls.items():
            self.failed_compliance_items.extend(failing_items)

        self.failed_compliance_items = self._remove_duplicate_items(self.failed_compliance_items)

    def _remove_duplicate_items(self, items: List[Any]) -> List[Any]:
        """
        Remove duplicate compliance items while preserving order.

        Uses resource_id and control_id to create unique keys for
        deduplication while maintaining the original order of items.

        :param List[Any] items: List of compliance items to deduplicate
        :return: List of unique compliance items
        :rtype: List[Any]
        """
        seen = set()
        unique_items = []

        for item in items:
            item_key = f"{getattr(item, 'resource_id', '')}-{getattr(item, 'control_id', '')}"
            if item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)

        return unique_items

    def _log_categorization_completion(self) -> None:
        """
        Log completion of control categorization.

        Provides final summary statistics about the categorization process,
        including counts of passing/failing controls and failed items.

        :return: None
        :rtype: None
        """
        logger.info(
            f"Fail-first categorization complete: {len(self.passing_controls)} passing, "
            f"{len(self.failing_controls)} failing controls"
        )
        logger.info(f"Populated failed_compliance_items list with {len(self.failed_compliance_items)} items")

    def process_compliance_sync(self) -> None:
        """
        New main method using ComplianceIntegration pattern.

        This replaces the old process_compliance_report method.
        """
        logger.info("Starting Wiz compliance sync using ComplianceIntegration pattern...")
        self.sync_compliance()

    def _get_or_create_report(self, max_age_hours: int = None) -> Optional[str]:
        """
        Get existing recent report or create a new one if needed.

        :param int max_age_hours: Maximum age in hours for reusing existing reports (deprecated, use max_report_age_days)
        :return: Path to report file
        :rtype: Optional[str]
        """
        # Handle force fresh report request
        if self.force_fresh_report:
            logger.info("Force fresh report requested, creating new compliance report...")
            return self._create_and_download_report(force_new=True)

        # Use instance variable max_report_age_days or legacy max_age_hours
        if max_age_hours is not None:
            # Legacy behavior for backward compatibility
            max_age_hours_to_use = max_age_hours
            logger.warning("Using deprecated max_age_hours parameter. Consider using max_report_age_days instead.")
        else:
            # Convert days to hours for the internal method
            max_age_hours_to_use = self.max_report_age_days * 24

        # Check for existing recent reports
        existing_report = self._find_recent_report(max_age_hours_to_use)
        if existing_report:
            logger.info(f"Using existing report: {existing_report}")
            return existing_report

        # No recent report found, create a new one
        logger.info(f"No recent report found within {self.max_report_age_days} days, creating new compliance report...")
        return self._create_and_download_report()

    def _find_recent_report(self, max_age_hours: int = 24) -> Optional[str]:
        """
        Find the most recent compliance report within the specified age limit.

        :param int max_age_hours: Maximum age in hours
        :return: Path to recent report file or None
        :rtype: Optional[str]
        """
        artifacts_dir = "artifacts/wiz"
        if not os.path.exists(artifacts_dir):
            return None

        report_prefix = f"compliance_report_{self.wiz_project_id}_"
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        # Find matching files
        matching_files = []
        for filename in os.listdir(artifacts_dir):
            if filename.startswith(report_prefix) and filename.endswith(".csv"):
                file_path = os.path.join(artifacts_dir, filename)
                try:
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mod_time > cutoff_time:
                        matching_files.append((file_path, mod_time))
                except (OSError, ValueError):
                    continue

        if not matching_files:
            return None

        # Return the most recent file
        most_recent = max(matching_files, key=lambda x: x[1])
        age_hours = (datetime.now() - most_recent[1]).total_seconds() / 3600
        logger.info(f"Found recent report (age: {age_hours:.1f}h): {most_recent[0]}")
        return most_recent[0]

    def _find_existing_compliance_report(self) -> Optional[str]:
        """
        Find existing compliance report for the current project.

        :return: Report ID if found, None otherwise
        :rtype: Optional[str]
        """
        try:
            # Filter for compliance reports (projectId not supported in ReportFilters, using name-based lookup)
            filter_by = {"type": ["COMPLIANCE_ASSESSMENTS"]}

            logger.debug(f"Searching for existing compliance reports with filter: {filter_by}")
            reports = self.report_manager.list_reports(filter_by=filter_by)

            if not reports:
                logger.info("No existing compliance reports found")
                return None

            # Look for report with project-specific name
            expected_name = f"Compliance Report - {self.wiz_project_id}"
            matching_reports = [report for report in reports if report.get("name", "").strip() == expected_name]

            if not matching_reports:
                logger.info(f"No existing compliance report found with name: {expected_name}")
                return None

            # Return the first matching report (most recent will be used)
            selected_report = matching_reports[0]
            report_id = selected_report.get("id")
            report_name = selected_report.get("name", "Unknown")

            logger.info(f"Found existing compliance report: '{report_name}' (ID: {report_id})")
            return report_id

        except Exception as e:
            logger.error(f"Error searching for existing compliance reports: {e}")
            return None

    def _create_and_download_report(self, force_new: bool = False) -> Optional[str]:
        """
        Find existing compliance report and rerun it, or create a new one if none exists.

        :param bool force_new: Force creation of new report, skip reuse logic
        :return: Path to downloaded report file
        :rtype: Optional[str]
        """
        if force_new or not self.reuse_existing_reports:
            logger.info("Creating new compliance report (reuse disabled or forced)")
            # Create new report
            report_id = self.report_manager.create_compliance_report(self.wiz_project_id)
            if not report_id:
                logger.error("Failed to create compliance report")
                return None

            # Wait for completion and get download URL
            download_url = self.report_manager.wait_for_report_completion(report_id)
        else:
            logger.info(f"Looking for existing compliance report for project: {self.wiz_project_id}")

            # Try to find existing compliance report for this project
            if existing_report_id := self._find_existing_compliance_report():
                logger.info(
                    f"Found existing compliance report {existing_report_id}, rerunning instead of creating new one"
                )
                # Rerun existing report
                download_url = self.report_manager.rerun_report(existing_report_id)
            else:
                logger.info("No existing compliance report found, creating new one")
                # Create new report
                report_id = self.report_manager.create_compliance_report(self.wiz_project_id)
                if not report_id:
                    logger.error("Failed to create compliance report")
                    return None

                # Wait for completion and get download URL
                download_url = self.report_manager.wait_for_report_completion(report_id)

        if not download_url:
            logger.error("Failed to get download URL for report")
            return None

        # Download report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"artifacts/wiz/compliance_report_{self.wiz_project_id}_{timestamp}.csv"

        # Ensure directory exists
        artifacts_dir = os.path.dirname(output_path)
        os.makedirs(artifacts_dir, exist_ok=True)

        if self.report_manager.download_report(download_url, output_path):
            # Clean up old report files
            ReportFileCleanup.cleanup_old_files(
                directory=artifacts_dir, file_prefix="compliance_report_", extensions=[".csv"], keep_count=5
            )
            return output_path
        else:
            logger.error("Failed to download report")
            return None

    def _update_passing_controls_to_implemented(self, passing_control_ids: list[str]) -> None:
        """
        Update passing controls to 'Implemented' status in RegScale.

        Uses ControlMatcher for robust control ID matching with leading zero normalization.

        :param list[str] passing_control_ids: List of control IDs that passed
        """
        if not passing_control_ids:
            return

        try:
            logger.debug(f"Looking for passing control IDs: {passing_control_ids}")

            # Prepare batch updates for passing controls
            implementations_to_update = []
            controls_not_found = []

            for control_id in passing_control_ids:
                # Use ControlMatcher to find implementation with robust control ID matching
                impl = self._control_matcher.find_control_implementation(
                    control_id=control_id, parent_id=self.plan_id, parent_module=self.parent_module
                )

                if impl:
                    logger.debug(f"Found matching implementation for '{control_id}': {impl.id}")

                    # Update status using compliance settings
                    new_status = self._get_implementation_status_from_result("Pass")
                    logger.debug(f"Setting control {control_id} status from 'Pass' result to: {new_status}")
                    impl.status = new_status
                    impl.dateLastAssessed = get_current_datetime()
                    impl.lastAssessmentResult = "Pass"
                    impl.bStatusImplemented = True

                    # Ensure required fields are set if empty
                    if not impl.responsibility:
                        impl.responsibility = ControlImplementation.get_default_responsibility(parent_id=impl.parentId)
                        logger.debug(f"Setting default responsibility for control {control_id}: {impl.responsibility}")

                    if not impl.implementation:
                        impl.implementation = f"Implementation details for {control_id} will be documented."
                        logger.debug(f"Setting default implementation statement for control {control_id}")

                    # Set audit fields if available
                    user_id = self.app.config.get("userId")
                    if user_id:
                        impl.lastUpdatedById = user_id
                        impl.dateLastUpdated = get_current_datetime()

                    implementations_to_update.append(impl.dict())
                    logger.info(f"Marking control {control_id} as {new_status}")
                else:
                    logger.debug(f"Control '{control_id}' not found in implementation map")
                    controls_not_found.append(control_id)

            # Log summary
            if controls_not_found:
                logger.info(f"Passing control IDs not found in plan: {', '.join(sorted(controls_not_found))}")

            logger.info(
                f"Control implementation status update summary: {len(implementations_to_update)} found, "
                f"{len(controls_not_found)} not in plan"
            )

            # Batch update all implementations
            if implementations_to_update:
                ControlImplementation.put_batch_implementation(self.app, implementations_to_update)
                logger.info(f"Successfully updated {len(implementations_to_update)} controls to Implemented status")
            else:
                logger.warning("No matching control implementations found to update")

        except Exception as e:
            logger.error(f"Error updating control implementation status: {e}")

    def _prepare_failing_control_update(self, control_id: str) -> Optional[dict]:
        """
        Prepare a single failing control for update.

        :param str control_id: Control ID to update
        :return: Dictionary representation of updated implementation, or None if not found
        :rtype: Optional[dict]
        """
        impl = self._control_matcher.find_control_implementation(
            control_id=control_id, parent_id=self.plan_id, parent_module=self.parent_module
        )

        if not impl:
            logger.debug(f"Control '{control_id}' not found in implementation map")
            return None

        logger.debug(f"Found matching implementation for '{control_id}': {impl.id}")

        new_status = self._get_implementation_status_from_result("Fail")
        logger.debug(f"Setting control {control_id} status from 'Fail' result to: {new_status}")

        impl.status = new_status
        impl.dateLastAssessed = get_current_datetime()
        impl.lastAssessmentResult = "Fail"
        impl.bStatusImplemented = False

        self._set_default_fields_if_empty(impl, control_id)
        self._set_audit_fields(impl)

        logger.info(f"Marking control {control_id} as {new_status}")
        return impl.dict()

    def _set_default_fields_if_empty(self, impl: ControlImplementation, control_id: str) -> None:
        """
        Set default values for required fields if they are empty.

        :param ControlImplementation impl: Implementation to update
        :param str control_id: Control ID for logging
        :return: None
        :rtype: None
        """
        if not impl.responsibility:
            impl.responsibility = ControlImplementation.get_default_responsibility(parent_id=impl.parentId)
            logger.debug(f"Setting default responsibility for control {control_id}: {impl.responsibility}")

        if not impl.implementation:
            impl.implementation = f"Implementation details for {control_id} will be documented."
            logger.debug(f"Setting default implementation statement for control {control_id}")

    def _set_audit_fields(self, impl: ControlImplementation) -> None:
        """
        Set audit fields on implementation if user ID is available.

        :param ControlImplementation impl: Implementation to update
        :return: None
        :rtype: None
        """
        user_id = self.app.config.get("userId")
        if user_id:
            impl.lastUpdatedById = user_id
            impl.dateLastUpdated = get_current_datetime()

    def _update_failing_controls_to_in_remediation(self, control_ids: List[str]) -> None:
        """
        Update control implementation status to In Remediation for failing controls.

        Uses ControlMatcher for robust control ID matching with leading zero normalization.

        :param List[str] control_ids: List of control IDs that are failing
        :return: None
        :rtype: None
        """
        if not control_ids:
            return

        try:
            logger.debug(f"Looking for failing control IDs: {control_ids}")

            implementations_to_update = []
            controls_not_found = []

            for control_id in control_ids:
                impl_dict = self._prepare_failing_control_update(control_id)
                if impl_dict:
                    implementations_to_update.append(impl_dict)
                else:
                    controls_not_found.append(control_id)

            self._log_update_summary(controls_not_found, implementations_to_update)
            self._batch_update_implementations(implementations_to_update)

        except Exception as e:
            logger.error(f"Error updating failing control implementation status: {e}")

    def _log_update_summary(self, controls_not_found: List[str], implementations_to_update: List[dict]) -> None:
        """
        Log summary of control update operation.

        :param List[str] controls_not_found: List of controls not found
        :param List[dict] implementations_to_update: List of implementations to update
        :return: None
        :rtype: None
        """
        if controls_not_found:
            logger.info(f"Control IDs not found in plan: {', '.join(sorted(controls_not_found))}")

        logger.info(
            f"Control implementation status update summary: {len(implementations_to_update)} found, "
            f"{len(controls_not_found)} not in plan"
        )

    def _batch_update_implementations(self, implementations_to_update: List[dict]) -> None:
        """
        Perform batch update of control implementations.

        :param List[dict] implementations_to_update: List of implementations to update
        :return: None
        :rtype: None
        """
        if implementations_to_update:
            ControlImplementation.put_batch_implementation(self.app, implementations_to_update)
            logger.debug(f"Updated {len(implementations_to_update)} Control Implementations, Successfully!")
            logger.info(f"Successfully updated {len(implementations_to_update)} controls to In Remediation status")
        else:
            logger.warning("No matching control implementations found to update for failing controls")

    def _process_control_assessments(self) -> None:
        """
        Override parent method to add control implementation status updates.
        """
        # Call parent method to create assessments
        super()._process_control_assessments()

        # Update control implementation status for both passing and failing controls if enabled
        if self.update_control_status:
            if self.passing_controls:
                passing_control_ids = list(self.passing_controls.keys())
                logger.info(f"Updating control implementation status for {len(passing_control_ids)} passing controls")
                self._update_passing_controls_to_implemented(passing_control_ids)

            if self.failing_controls:
                failing_control_ids = list(self.failing_controls.keys())
                logger.info(
                    f"Attempting to update control implementation status for {len(failing_control_ids)} failing controls"
                )
                self._update_failing_controls_to_in_remediation(failing_control_ids)

    def _categorize_controls_by_aggregation(self) -> None:
        """
        Override parent method to implement "fail-first" logic for Wiz compliance.

        In the Wiz compliance integration, we implement strict "fail-first" logic:
        - If ANY compliance item for a control is failing, the entire control is marked as failing
        - A control is only marked as passing if ALL instances of that control are passing
        - This applies to both single-control and multi-control compliance items
        """
        control_items = self._group_compliance_items_by_control()
        self._apply_fail_first_logic_to_controls(control_items)
        self._populate_failed_compliance_items_from_control_items(control_items)
        self._log_categorization_results()

    def _group_compliance_items_by_control(self) -> dict:
        """
        Group compliance items by control ID.

        Creates a dictionary mapping control IDs (lowercase) to lists of
        compliance items that reference those controls. Handles multi-control
        items that may reference multiple control IDs.

        :return: Dictionary mapping control IDs to lists of compliance items
        :rtype: dict
        """
        from collections import defaultdict

        control_items = defaultdict(list)

        for item in self.all_compliance_items:
            control_ids = self._extract_control_ids_from_item(item)
            self._add_item_to_control_groups(item, control_ids, control_items)

        logger.debug(
            f"Grouped {len(self.all_compliance_items)} compliance items into {len(control_items)} control groups"
        )
        return control_items

    def _extract_control_ids_from_item(self, item) -> list:
        """
        Extract all control IDs that an item affects.

        Checks if the item has a get_all_control_ids method for multi-control
        items, otherwise falls back to the single control_id attribute.

        :param item: Compliance item to extract control IDs from
        :type item: Any
        :return: List of control ID strings
        :rtype: list
        """
        if hasattr(item, "get_all_control_ids") and callable(item.get_all_control_ids):
            return item.get_all_control_ids()
        return [item.control_id] if item.control_id else []

    def _add_item_to_control_groups(self, item, control_ids: list, control_items: dict) -> None:
        """
        Add item to all control groups it affects.

        Adds the compliance item to the appropriate control groups based on
        all the control IDs it references. Uses lowercase control IDs as keys.

        :param item: Compliance item to add to groups
        :type item: Any
        :param list control_ids: List of control IDs the item affects
        :param dict control_items: Dictionary of control groups to update
        :return: None
        :rtype: None
        """
        for control_id in control_ids:
            if control_id:
                control_key = control_id.lower()
                control_items[control_key].append(item)

    def _apply_fail_first_logic_to_controls(self, control_items: dict) -> None:
        """
        Apply fail-first logic to categorize each control as passing or failing.

        For each control, determines its overall status based on all associated
        compliance items. Any failure in the items makes the control fail.

        :param dict control_items: Dictionary mapping control IDs to compliance items
        :return: None
        :rtype: None
        """
        for control_key, items in control_items.items():
            control_status = self._determine_control_status(items)
            self._categorize_control(control_key, control_status, len(items))

    def _determine_control_status(self, items: list) -> dict:
        """
        Determine the overall status of a control based on its items.

        Analyzes all compliance items for a control to determine if any are
        failing or passing. Returns status indicators and representative items.

        :param list items: List of compliance items for the control
        :return: Dictionary with status flags and representative items
        :rtype: dict
        """
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]
        pass_statuses_lower = [status.lower() for status in self.PASS_STATUSES]

        status = {"has_failure": False, "has_pass": False, "failing_item": None, "passing_item": None}

        for item in items:
            result_lower = item.compliance_result.lower()

            if result_lower in fail_statuses_lower:
                status["has_failure"] = True
                if not status["failing_item"]:
                    status["failing_item"] = item
            elif result_lower in pass_statuses_lower:
                status["has_pass"] = True
                if not status["passing_item"]:
                    status["passing_item"] = item

        return status

    def _categorize_control(self, control_key: str, status: dict, item_count: int) -> None:
        """
        Categorize a control as passing or failing based on its status.

        Uses the status information to place the control in the appropriate
        passing or failing collection and logs the categorization decision.

        :param str control_key: Control ID (lowercase)
        :param dict status: Status information from _determine_control_status
        :param int item_count: Number of items analyzed for the control
        :return: None
        :rtype: None
        """
        if status["has_failure"]:
            self.failing_controls[control_key] = status["failing_item"]
            logger.debug(f"Control {control_key} marked as FAILING: fail-first logic triggered")
        elif status["has_pass"]:
            self.passing_controls[control_key] = status["passing_item"]
            logger.debug(f"Control {control_key} marked as PASSING: all {item_count} items passed")
        else:
            logger.debug(f"Control {control_key} has unclear results - no pass or fail statuses found")

    def _populate_failed_compliance_items_from_control_items(self, control_items: dict) -> None:
        """
        Populate the list of failed compliance items from failing controls.

        Collects all failing compliance items from controls marked as failing,
        removes duplicates, and updates the failed_compliance_items list.

        :param dict control_items: Dictionary mapping control IDs to compliance items
        :return: None
        :rtype: None
        """
        self.failed_compliance_items.clear()
        failing_items = self._collect_failing_items_from_controls(control_items)
        self.failed_compliance_items = self._remove_duplicate_items(failing_items)
        logger.info(f"Populated failed_compliance_items list with {len(self.failed_compliance_items)} items")

    def _collect_failing_items_from_controls(self, control_items: dict) -> list:
        """
        Collect all failing items from controls marked as failing.

        Iterates through controls marked as failing and collects all their
        compliance items that have failing status results.

        :param dict control_items: Dictionary mapping control IDs to compliance items
        :return: List of failing compliance items
        :rtype: list
        """
        failing_items = []
        fail_statuses_lower = [status.lower() for status in self.FAIL_STATUSES]

        for control_key, items in control_items.items():
            if control_key in self.failing_controls:
                for item in items:
                    if item.compliance_result.lower() in fail_statuses_lower:
                        failing_items.append(item)

        return failing_items

    def _remove_duplicate_items(self, items: list) -> list:
        """
        Remove duplicate items while preserving order.

        Uses resource_id and control_id combinations to create unique keys
        for deduplication while maintaining the original item order.

        :param list items: List of compliance items to deduplicate
        :return: List of unique compliance items
        :rtype: list
        """
        seen = set()
        unique_items = []

        for item in items:
            item_key = f"{getattr(item, 'resource_id', '')}-{getattr(item, 'control_id', '')}"
            if item_key not in seen:
                seen.add(item_key)
                unique_items.append(item)

        return unique_items

    def _log_categorization_results(self) -> None:
        """
        Log the final results of control categorization.

        Provides summary statistics about the fail-first categorization
        process, including counts of passing and failing controls.

        :return: None
        :rtype: None
        """
        logger.info(
            f"Control categorization with fail-first logic: "
            f"{len(self.passing_controls)} passing controls, "
            f"{len(self.failing_controls)} failing controls"
        )

    def fetch_findings(self, *args, **kwargs):
        """
        Override to create one finding per control rather than per compliance item.

        This ensures that each failing control gets exactly one issue in RegScale,
        consolidating all failed compliance items for that control.
        """
        logger.info("Fetching findings from failed controls (one per control)...")

        processed_controls = set()
        findings_created = 0

        for compliance_item in self.failed_compliance_items:
            control_ids = self._get_control_ids_for_item(compliance_item)

            for control_id in control_ids:
                if not control_id or self._is_control_already_processed(control_id, processed_controls):
                    continue

                control_id_normalized = control_id.upper()
                processed_controls.add(control_id.lower())

                control_failed_items = self._get_failed_items_for_control(control_id_normalized)
                finding = self._create_consolidated_finding_for_control(
                    control_id=control_id_normalized, failed_items=control_failed_items
                )

                if finding:
                    findings_created += 1
                    yield finding

        self._log_findings_generation_summary(findings_created, len(processed_controls))

    def _is_control_already_processed(self, control_id: str, processed_controls: set) -> bool:
        """
        Check if control has already been processed to avoid duplicates.

        Uses case-insensitive comparison to determine if a control has
        already been processed for finding generation.

        :param str control_id: Control ID to check
        :param set processed_controls: Set of already processed control IDs
        :return: True if control has been processed, False otherwise
        :rtype: bool
        """
        return control_id.lower() in processed_controls

    def _get_failed_items_for_control(self, control_id_normalized: str) -> List[Any]:
        """
        Get all failed compliance items for a specific control.

        Searches through the failed compliance items to find all items
        that reference the specified control ID (case-insensitive).

        :param str control_id_normalized: Control ID in normalized format
        :return: List of failed compliance items for the control
        :rtype: List[Any]
        """
        control_failed_items = []

        for item in self.failed_compliance_items:
            item_control_ids = self._get_control_ids_for_item(item)

            if any(cid.upper() == control_id_normalized for cid in item_control_ids):
                control_failed_items.append(item)

        return control_failed_items

    def _log_findings_generation_summary(self, findings_created: int, controls_processed: int) -> None:
        """
        Log summary of findings generation.

        Provides statistics about the finding generation process,
        including number of findings created and controls processed.

        :param int findings_created: Number of findings successfully created
        :param int controls_processed: Number of controls processed
        :return: None
        :rtype: None
        """
        logger.info(
            f"Generated {findings_created} findings from {controls_processed} failing controls for issue processing"
        )

    def _create_consolidated_finding_for_control(self, control_id: str, failed_items: list) -> Optional[Any]:
        """
        Create a single consolidated finding for a control with all its failed compliance items.

        :param str control_id: The control identifier
        :param list failed_items: List of failed compliance items for this control
        :return: IntegrationFinding or None
        """
        try:
            from regscale.integrations.scanner_integration import IntegrationFinding

            if not failed_items:
                return None

            representative_item = failed_items[0]
            resource_info = self._collect_resource_information(failed_items)
            severity = self._determine_highest_severity(resource_info["severities"])
            description = self._build_consolidated_description(control_id, resource_info)

            severity_enum = self._map_string_severity_to_enum(severity)

            return self._create_integration_finding(
                control_id=control_id,
                severity_enum=severity_enum,
                description=description,
                representative_item=representative_item,
            )

        except Exception as e:
            logger.error(f"Error creating consolidated finding for control {control_id}: {e}")
            return None

    def _map_severity_to_priority(self, severity: Any) -> str:
        """
        Map severity enum to priority string.

        Converts RegScale severity enumeration values to corresponding
        priority strings used in issue creation.

        :param Any severity: Severity enum value
        :return: Priority string (High, Moderate, Low)
        :rtype: str
        """
        # Map severity to priority
        if hasattr(severity, "value"):
            severity_value = severity.value
        else:
            severity_value = str(severity)

        priority_map = {"Critical": "High", "High": "High", "Moderate": "Moderate", "Low": "Low"}

        return priority_map.get(severity_value, "Low")

    def _collect_resource_information(self, failed_items: list) -> Dict[str, Any]:
        """Collect resource information from failed compliance items.

        :param list failed_items: List of failed compliance items to process
        :return: Dictionary with resource information including affected_resources, severities, and descriptions
        :rtype: Dict[str, Any]
        """
        affected_resources = set()
        severities = []
        descriptions = []

        for item in failed_items:
            affected_resources.add(item.resource_name)
            if item.severity:
                severities.append(item.severity)
            descriptions.append(f"- {item.resource_name}: {item.description}")

        return {"affected_resources": affected_resources, "severities": severities, "descriptions": descriptions}

    def _determine_highest_severity(self, severities: List[str]) -> str:
        """Determine the highest severity from a list of severities.

        :param List[str] severities: List of severity strings to analyze
        :return: The highest severity found in the list
        :rtype: str
        """
        severity = "HIGH"  # Default
        if severities:
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
            for sev in severity_order:
                if sev in [s.upper() for s in severities]:
                    severity = sev
                    break
        return severity

    def _build_consolidated_description(self, control_id: str, resource_info: Dict[str, Any]) -> str:
        """Build consolidated description for the finding.

        :param str control_id: The control identifier
        :param Dict[str, Any] resource_info: Dictionary with resource information
        :return: Consolidated description string for the finding
        :rtype: str
        """
        affected_resources = resource_info["affected_resources"]
        descriptions = resource_info["descriptions"]

        description = f"Control {control_id} failed for {len(affected_resources)} resource(s):\n\n"
        description += "\n".join(descriptions[:10])  # Limit to first 10 for readability

        if len(descriptions) > 10:
            description += f"\n... and {len(descriptions) - 10} more resources"

        return description

    def _create_integration_finding(
        self, control_id: str, severity_enum: Any, description: str, representative_item: Any
    ) -> Any:
        """Create the IntegrationFinding object.

        :param str control_id: The control identifier
        :param Any severity_enum: Severity enumeration value
        :param str description: Description for the finding
        :param Any representative_item: Representative compliance item
        :return: IntegrationFinding object
        :rtype: Any
        """
        from regscale.integrations.scanner_integration import IntegrationFinding

        return IntegrationFinding(
            control_labels=[control_id],
            title=f"Compliance Violation: {control_id}",
            category="Compliance",
            plugin_name=f"{self.title} Compliance Scanner - {control_id}",
            severity=severity_enum,
            description=description,
            status="Open",
            priority=self._map_severity_to_priority(severity_enum),
            external_id=f"{self.title.lower().replace(' ', '-')}-control-{control_id}",
            first_seen=self.scan_date,
            last_seen=self.scan_date,
            scan_date=self.scan_date,
            asset_identifier=representative_item.resource_id,
            vulnerability_type="Compliance Violation",
            rule_id=control_id,
            baseline=representative_item.framework,
            affected_controls=control_id,
            identification=IssueIdentification.SecurityControlAssessment.value,
        )

    def _create_finding_from_compliance_item(self, compliance_item: ComplianceItem) -> Optional[Any]:
        """
        Override parent method to properly set affected_controls for multi-control items.

        :param ComplianceItem compliance_item: The compliance item
        :return: Finding object or None if creation fails
        :rtype: Optional[Any]
        """
        try:
            # Get severity mapping
            severity = compliance_item.severity or "Low"
            severity_enum = self._map_string_severity_to_enum(severity)

            # Create the finding using the parent class structure
            from regscale.integrations.scanner_integration import IntegrationFinding

            finding = IntegrationFinding(
                control_labels=[compliance_item.control_id],
                title=f"Compliance Violation: {compliance_item.control_id}",
                category="Compliance",
                plugin_name=f"{self.title} Compliance Scanner",
                severity=severity_enum,
                description=compliance_item.description,
                status="Open",  # Use string instead of enum to avoid import issues
                priority=self._map_severity_to_priority(severity_enum),
                external_id=f"{self.title.lower()}-{compliance_item.control_id}-{compliance_item.resource_id}",
                first_seen=self.scan_date,
                last_seen=self.scan_date,
                scan_date=self.scan_date,
                asset_identifier=compliance_item.resource_id,
                vulnerability_type="Compliance Violation",
                rule_id=compliance_item.control_id,
                baseline=compliance_item.framework,
                affected_controls=compliance_item.affected_controls,  # Use our property with all control IDs
                identification=IssueIdentification.SecurityControlAssessment.value,
            )

            return finding

        except Exception as e:
            logger.error(f"Error creating finding from compliance item: {e}")
            return None
