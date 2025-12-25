"""Wiz Issue Integration class"""

import logging
import re
from typing import List, Dict, Any, Iterator, Optional

from regscale import models as regscale_models
from regscale.core.app.utils.parser_utils import safe_datetime_str
from regscale.integrations.scanner_integration import IntegrationFinding
from regscale.models import Issue
from regscale.utils.dict_utils import get_value
from .core.constants import (
    get_wiz_issue_queries,
    WizVulnerabilityType,
)
from .scanner import WizVulnerabilityIntegration

logger = logging.getLogger(__name__)


class WizIssue(WizVulnerabilityIntegration):
    """
    Wiz Issue class
    """

    title = "Wiz-Issue"
    # Server-side batch deduplication requires a standard RegScale Asset field name
    # The Wiz ID is stored in otherTrackingNumber for deduplication purposes
    asset_identifier_field = "otherTrackingNumber"
    issue_identifier_field = "wizId"

    def get_query_types(self, project_id: str, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get the query types for issue scanning.

        :param str project_id: The project ID to get queries for
        :param Optional[Dict[str, Any]] filter_by: Optional filter criteria to override defaults
        :return: List of query types
        :rtype: List[Dict[str, Any]]
        """
        return get_wiz_issue_queries(project_id=project_id, filter_by=filter_by)

    def parse_findings(
        self, nodes: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> Iterator[IntegrationFinding]:
        """
        Parse the Wiz issues into IntegrationFinding objects.
        Groups issues by source rule and server to consolidate multiple database assets.
        :param nodes:
        :param vulnerability_type:
        :return:
        """
        logger.debug(f"ISSUE PROCESSING ANALYSIS: Received {len(nodes)} raw Wiz issues for processing")

        # Analyze and log raw issue statistics
        self._log_raw_issue_statistics(nodes)

        # Filter nodes by minimum severity configuration
        filtered_nodes = self._filter_nodes_by_severity(nodes)
        if not filtered_nodes:
            return

        # Group and process issues for consolidation
        grouped_issues = self._group_issues_for_consolidation(filtered_nodes)
        self._log_consolidation_analysis(grouped_issues)

        # Generate findings from grouped issues
        yield from self._generate_findings_from_groups(grouped_issues, vulnerability_type, len(nodes))

    def _log_raw_issue_statistics(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Count and log raw issue statistics by severity and status.

        :param List[Dict[str, Any]] nodes: List of raw Wiz issues
        """
        severity_counts: Dict[str, int] = {}
        status_counts: Dict[str, int] = {}

        for node in nodes:
            severity = node.get("severity", "Low")
            status = node.get("status", "OPEN")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1

        logger.debug(f"Raw issue breakdown by severity: {severity_counts}")
        logger.debug(f"Raw issue breakdown by status: {status_counts}")

    def _filter_nodes_by_severity(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter nodes based on minimum severity configuration.

        :param List[Dict[str, Any]] nodes: List of raw Wiz issues
        :return: Filtered list of issues that meet severity requirements
        :rtype: List[Dict[str, Any]]
        """
        filtered_nodes = []
        filtered_out_count = 0

        for node in nodes:
            wiz_severity = node.get("severity", "Low")
            wiz_id = node.get("id", "unknown")

            if self.should_process_finding_by_severity(wiz_severity):
                filtered_nodes.append(node)
            else:
                filtered_out_count += 1
                logger.debug(
                    f"FILTERED BY SEVERITY: Issue {wiz_id} with severity '{wiz_severity}' filtered due to minimumSeverity configuration"
                )

        logger.debug(f"After severity filtering: {len(filtered_nodes)} issues kept, {filtered_out_count} filtered out")

        if not filtered_nodes:
            logger.warning("All findings filtered out by severity configuration - check your minimumSeverity setting")

        return filtered_nodes

    def _log_consolidation_analysis(self, grouped_issues: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Log detailed consolidation analysis statistics.

        :param Dict[str, List[Dict[str, Any]]] grouped_issues: Issues grouped for consolidation
        """
        total_groups = len(grouped_issues)
        consolidated_groups = sum(1 for group in grouped_issues.values() if len(group) > 1)
        total_consolidated_issues = sum(len(group) for group in grouped_issues.values() if len(group) > 1)
        single_issue_groups = total_groups - consolidated_groups

        logger.debug("CONSOLIDATION ANALYSIS:")
        logger.debug(f"   • Total groups: {total_groups}")
        logger.debug(f"   • Groups with multiple issues (consolidated): {consolidated_groups}")
        logger.debug(f"   • Total issues being consolidated: {total_consolidated_issues}")
        logger.debug(f"   • Single-issue groups: {single_issue_groups}")
        logger.debug(f"   • Expected RegScale issues to create: {total_groups}")

    def _generate_findings_from_groups(
        self,
        grouped_issues: Dict[str, List[Dict[str, Any]]],
        vulnerability_type: WizVulnerabilityType,
        total_raw_issues: int,
    ) -> Iterator[IntegrationFinding]:
        """
        Generate IntegrationFindings from grouped issues, handling both consolidation and single issues.

        :param Dict[str, List[Dict[str, Any]]] grouped_issues: Issues grouped for processing
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :param int total_raw_issues: Total number of raw issues for logging
        :return: Generator of IntegrationFindings
        :rtype: Iterator[IntegrationFinding]
        """
        findings_generated = 0

        for group_key, group_issues in grouped_issues.items():
            if len(group_issues) > 1:
                finding = self._process_consolidated_group(group_key, group_issues, vulnerability_type)
            else:
                finding = self._process_single_issue_group(group_issues[0], vulnerability_type)

            if finding:
                findings_generated += 1
                yield finding

        logger.info(f"Generated {findings_generated} RegScale findings from {total_raw_issues} raw Wiz issues")

    def _process_consolidated_group(
        self, group_key: str, group_issues: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> Optional[IntegrationFinding]:
        """
        Process a group with multiple issues that need consolidation.

        :param str group_key: The consolidation group key
        :param List[Dict[str, Any]] group_issues: List of issues to consolidate
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :return: Consolidated finding or None if failed
        :rtype: Optional[IntegrationFinding]
        """
        issue_ids = [issue.get("id", "unknown") for issue in group_issues]
        logger.debug(f"CONSOLIDATING: Group '{group_key}' - merging {len(group_issues)} issues: {issue_ids}")

        finding = self._create_consolidated_finding(group_issues, vulnerability_type)
        if not finding:
            logger.warning(f"Failed to create consolidated finding for group '{group_key}'")

        return finding

    def _process_single_issue_group(
        self, issue: Dict[str, Any], vulnerability_type: WizVulnerabilityType
    ) -> Optional[IntegrationFinding]:
        """
        Process a single issue that doesn't require consolidation.

        :param Dict[str, Any] issue: The single issue to process
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :return: Single issue finding or None if failed
        :rtype: Optional[IntegrationFinding]
        """
        wiz_id = issue.get("id", "unknown")
        logger.debug(f"📝 SINGLE ISSUE: Processing issue {wiz_id} individually")

        finding = self.parse_finding(issue, vulnerability_type)
        if not finding:
            logger.warning(f"Failed to create finding for single issue {wiz_id}")

        return finding

    def _group_issues_for_consolidation(self, nodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group issues by source rule name (title) for consolidation.
        This consolidates all issues with the same rule/title regardless of the affected asset.

        :param List[Dict[str, Any]] nodes: List of Wiz issues
        :return: Dictionary mapping rule names to lists of issues
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        groups: Dict[str, List[Dict[str, Any]]] = {}

        for issue in nodes:
            # Group by source rule name only (which becomes the title)
            # This ensures all issues with identical titles are consolidated together
            source_rule = issue.get("sourceRule", {})
            rule_name = source_rule.get("name", "")

            # Use rule name as the grouping key
            # If no rule name, fall back to issue name to avoid empty keys
            group_key = rule_name or issue.get("name", "") or f"unknown-{issue.get('id', 'no-id')}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(issue)

            # Log the grouping for analysis
            logger.debug(f"Grouping issue {issue.get('id')} under key '{group_key}'")

        return groups

    def _determine_grouping_scope(self, provider_id: str, rule_name: str) -> str:
        """
        DEPRECATED: This method is no longer used as consolidation is now done by title only.
        Kept for backward compatibility but will be removed in future versions.

        :param str provider_id: The Azure provider ID
        :param str rule_name: The source rule name
        :return: The grouping scope (always returns provider_id)
        :rtype: str
        """
        # This method is deprecated - consolidation now happens by title only
        logger.debug("_determine_grouping_scope is deprecated and will be removed in a future version")
        return provider_id

    def _create_consolidated_finding(
        self, issues: List[Dict[str, Any]], vulnerability_type: WizVulnerabilityType
    ) -> IntegrationFinding:
        """
        Create a consolidated finding from multiple issues with the same rule.
        Implements priority rules for severity, status, due date, and asset consolidation.

        :param List[Dict[str, Any]] issues: List of issues to consolidate
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :return: Consolidated IntegrationFinding
        :rtype: IntegrationFinding
        """
        # Determine consolidation priorities
        highest_severity = self._determine_highest_severity(issues)
        most_urgent_status = self._determine_most_urgent_status(issues)
        earliest_created = self._find_earliest_creation_date(issues)
        base_issue = self._select_base_issue(issues, highest_severity)

        # Consolidate asset information
        primary_asset_id, consolidated_provider_ids = self._consolidate_all_assets(issues)

        # Log consolidation details
        self._log_consolidation_details(
            issues, base_issue, highest_severity, most_urgent_status, primary_asset_id, consolidated_provider_ids
        )

        # Create and return the consolidated finding
        return self._build_integration_finding(
            base_issue,
            vulnerability_type,
            highest_severity,
            most_urgent_status,
            earliest_created,
            primary_asset_id,
            consolidated_provider_ids,
        )

    def _determine_highest_severity(self, issues: List[Dict[str, Any]]) -> str:
        """
        Determine the highest priority severity from a list of issues.

        :param List[Dict[str, Any]] issues: List of issues to analyze
        :return: The highest severity level
        :rtype: str
        """
        severity_priority = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFORMATIONAL": 0}
        highest_severity = "LOW"
        highest_priority = 0

        for issue in issues:
            issue_severity = issue.get("severity", "LOW").upper()
            priority = severity_priority.get(issue_severity, 0)
            if priority > highest_priority:
                highest_priority = priority
                highest_severity = issue_severity

        return highest_severity

    def _determine_most_urgent_status(self, issues: List[Dict[str, Any]]) -> str:
        """
        Determine the most urgent status from a list of issues.
        Any open issue means the consolidated issue should be open.

        :param List[Dict[str, Any]] issues: List of issues to analyze
        :return: The most urgent status
        :rtype: str
        """
        for issue in issues:
            issue_status = issue.get("status", "OPEN").upper()
            if issue_status in ["OPEN", "IN_PROGRESS", "ACKNOWLEDGE"]:
                return "OPEN"
        return "RESOLVED"

    def _find_earliest_creation_date(self, issues: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find the earliest creation date from a list of issues.

        :param List[Dict[str, Any]] issues: List of issues to analyze
        :return: The earliest creation date or None
        :rtype: Optional[str]
        """
        earliest_created = None
        for issue in issues:
            created = safe_datetime_str(issue.get("createdAt"))
            if created and (not earliest_created or created < earliest_created):
                earliest_created = created
        return earliest_created

    def _select_base_issue(self, issues: List[Dict[str, Any]], highest_severity: str) -> Dict[str, Any]:
        """
        Select the base issue for consolidation based on highest severity.

        :param List[Dict[str, Any]] issues: List of issues to choose from
        :param str highest_severity: The highest severity level identified
        :return: The selected base issue
        :rtype: Dict[str, Any]
        """
        for issue in issues:
            if issue.get("severity", "LOW").upper() == highest_severity:
                return issue
        return issues[0]  # Fallback to first issue

    def _consolidate_all_assets(self, issues: List[Dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
        """
        Consolidate all asset identifiers and provider IDs from multiple issues.

        :param List[Dict[str, Any]] issues: List of issues to consolidate assets from
        :return: Tuple of (primary_asset_id, consolidated_provider_ids)
        :rtype: tuple[Optional[str], Optional[str]]
        """
        asset_ids: List[str] = []
        provider_ids: List[str] = []
        seen_asset_ids: set[str] = set()
        seen_provider_ids: set[str] = set()

        for issue in issues:
            self._collect_assets_from_issue(issue, asset_ids, provider_ids, seen_asset_ids, seen_provider_ids)

        primary_asset_id = asset_ids[0] if asset_ids else None
        consolidated_provider_ids = "\n".join(provider_ids) if provider_ids else None

        return primary_asset_id, consolidated_provider_ids

    def _collect_assets_from_issue(
        self,
        issue: Dict[str, Any],
        asset_ids: List[str],
        provider_ids: List[str],
        seen_asset_ids: set,
        seen_provider_ids: set,
    ) -> None:
        """
        Collect asset IDs and provider IDs from a single issue.

        :param Dict[str, Any] issue: The issue to extract assets from
        :param List[str] asset_ids: List to append asset IDs to
        :param List[str] provider_ids: List to append provider IDs to
        :param set seen_asset_ids: Set to track seen asset IDs
        :param set seen_provider_ids: Set to track seen provider IDs
        """
        self._collect_from_entity_snapshot(issue, asset_ids, provider_ids, seen_asset_ids, seen_provider_ids)
        self._collect_from_related_entities(issue, asset_ids, provider_ids, seen_asset_ids, seen_provider_ids)

    def _collect_from_entity_snapshot(
        self,
        issue: Dict[str, Any],
        asset_ids: List[str],
        provider_ids: List[str],
        seen_asset_ids: set,
        seen_provider_ids: set,
    ) -> None:
        """
        Collect asset IDs and provider IDs from entitySnapshot.

        :param Dict[str, Any] issue: The issue to extract assets from
        :param List[str] asset_ids: List to append asset IDs to
        :param List[str] provider_ids: List to append provider IDs to
        :param set seen_asset_ids: Set to track seen asset IDs
        :param set seen_provider_ids: Set to track seen provider IDs
        """
        entity_snapshot = issue.get("entitySnapshot", {})
        self._add_entity_ids(entity_snapshot, asset_ids, provider_ids, seen_asset_ids, seen_provider_ids)

    def _collect_from_related_entities(
        self,
        issue: Dict[str, Any],
        asset_ids: List[str],
        provider_ids: List[str],
        seen_asset_ids: set,
        seen_provider_ids: set,
    ) -> None:
        """
        Collect asset IDs and provider IDs from related entities.

        :param Dict[str, Any] issue: The issue to extract assets from
        :param List[str] asset_ids: List to append asset IDs to
        :param List[str] provider_ids: List to append provider IDs to
        :param set seen_asset_ids: Set to track seen asset IDs
        :param set seen_provider_ids: Set to track seen provider IDs
        """
        for entity in issue.get("relatedEntities", []):
            if entity and isinstance(entity, dict):
                self._add_entity_ids(entity, asset_ids, provider_ids, seen_asset_ids, seen_provider_ids)

    def _add_entity_ids(
        self,
        entity: Dict[str, Any],
        asset_ids: List[str],
        provider_ids: List[str],
        seen_asset_ids: set,
        seen_provider_ids: set,
    ) -> None:
        """
        Add entity ID and provider ID from a single entity if not already seen.

        :param Dict[str, Any] entity: The entity to extract IDs from
        :param List[str] asset_ids: List to append asset IDs to
        :param List[str] provider_ids: List to append provider IDs to
        :param set seen_asset_ids: Set to track seen asset IDs
        :param set seen_provider_ids: Set to track seen provider IDs
        """
        self._add_unique_id(entity.get("id"), asset_ids, seen_asset_ids)
        self._add_unique_id(entity.get("providerId"), provider_ids, seen_provider_ids)

    def _add_unique_id(self, id_value: Optional[str], id_list: List[str], seen_ids: set) -> None:
        """
        Add an ID to the list if it exists and hasn't been seen before.

        :param Optional[str] id_value: The ID value to add
        :param List[str] id_list: List to append the ID to
        :param set seen_ids: Set to track seen IDs
        """
        if id_value and id_value not in seen_ids:
            id_list.append(id_value)
            seen_ids.add(id_value)

    def _log_consolidation_details(
        self,
        issues: List[Dict[str, Any]],
        base_issue: Dict[str, Any],
        highest_severity: str,
        most_urgent_status: str,
        primary_asset_id: Optional[str],
        consolidated_provider_ids: Optional[str],
    ) -> None:
        """
        Log detailed information about the consolidation process.

        :param List[Dict[str, Any]] issues: List of issues being consolidated
        :param Dict[str, Any] base_issue: The base issue selected for consolidation
        :param str highest_severity: The highest severity determined
        :param str most_urgent_status: The most urgent status determined
        :param Optional[str] primary_asset_id: The primary asset ID
        :param Optional[str] consolidated_provider_ids: The consolidated provider IDs
        """
        rule_name = base_issue.get("sourceRule", {}).get("name", "Unknown")
        severity_count = len([i for i in issues if i.get("severity", "").upper() == highest_severity])
        asset_count = len(primary_asset_id.split("\n")) if primary_asset_id else 0
        provider_count = len(consolidated_provider_ids.split("\n")) if consolidated_provider_ids else 0

        logger.debug(f"CONSOLIDATION DETAILS for '{rule_name}':")
        logger.debug(f"   • Consolidating {len(issues)} issues into 1")
        logger.debug(f"   • Highest severity: {highest_severity} (from {severity_count} issues)")
        logger.debug(f"   • Most urgent status: {most_urgent_status}")
        logger.debug(f"   • Total unique assets: {asset_count}")
        logger.debug(f"   • Total unique provider IDs: {provider_count}")

    def _build_integration_finding(
        self,
        base_issue: Dict[str, Any],
        vulnerability_type: WizVulnerabilityType,
        highest_severity: str,
        most_urgent_status: str,
        earliest_created: Optional[str],
        primary_asset_id: Optional[str],
        consolidated_provider_ids: Optional[str],
    ) -> IntegrationFinding:
        """
        Build the final IntegrationFinding object from consolidated data.

        :param Dict[str, Any] base_issue: The base issue to use for field values
        :param WizVulnerabilityType vulnerability_type: The vulnerability type
        :param str highest_severity: The highest severity determined
        :param str most_urgent_status: The most urgent status determined
        :param Optional[str] earliest_created: The earliest creation date
        :param Optional[str] primary_asset_id: The primary asset identifier
        :param Optional[str] consolidated_provider_ids: The consolidated provider IDs
        :return: The built IntegrationFinding
        :rtype: IntegrationFinding
        """
        wiz_id = base_issue.get("id", "N/A")
        severity = self.get_issue_severity(highest_severity)
        status = self.map_status_to_issue_status(most_urgent_status)
        date_created = earliest_created or safe_datetime_str(base_issue.get("createdAt"))
        name = base_issue.get("name", "")

        # Handle source rule (Control) specific fields
        source_rule = base_issue.get("sourceRule", {})
        control_name = source_rule.get("name", "")
        control_labels = self._parse_security_subcategories(source_rule)
        description = (
            self._format_control_description(source_rule) if source_rule else base_issue.get("description", "")
        )

        # Handle CVE if present
        cve = (
            name
            if name and (name.startswith("CVE") or name.startswith("GHSA")) and not base_issue.get("cve")
            else base_issue.get("cve")
        )

        # Get plugin name and source rule ID
        plugin_name = self._get_plugin_name(base_issue)
        source_rule_id = self._get_source_rule_id(source_rule)
        security_check = f"Wiz {plugin_name}"

        return IntegrationFinding(
            control_labels=control_labels,
            category="Wiz Control" if source_rule else "Wiz Vulnerability",
            title=control_name or base_issue.get("name") or f"unknown - {wiz_id}",
            security_check=security_check,
            description=description,
            severity=severity,
            status=status,
            asset_identifier=primary_asset_id or f"wiz-issue-{wiz_id}",
            issue_asset_identifier_value=consolidated_provider_ids,
            external_id=wiz_id,
            first_seen=date_created,
            last_seen=safe_datetime_str(base_issue.get("lastDetectedAt")),
            remediation=source_rule.get("resolutionRecommendation")
            or f"Update to version {base_issue.get('fixedVersion')} or higher",
            cve=cve,
            plugin_name=plugin_name,
            source_rule_id=source_rule_id,
            vulnerability_type=vulnerability_type.value,
            date_created=date_created,
            due_date=Issue.get_due_date(severity, self.app.config, "wiz", date_created),
            recommendation_for_mitigation=source_rule.get("resolutionRecommendation")
            or base_issue.get("description", ""),
            poam_comments=None,
            basis_for_adjustment=None,
        )

    def _get_consolidated_asset_identifiers(self, wiz_issue: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """
        Get consolidated asset identifiers for an issue.
        For multiple assets, returns the primary asset ID and all provider IDs as newline-separated string.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Tuple of (primary_asset_id, consolidated_provider_ids)
        :rtype: tuple[str, Optional[str]]
        """
        assets = self._collect_all_assets(wiz_issue)

        if not assets:
            return None, None

        primary_asset_id = assets[0][0]
        consolidated_provider_ids = self._consolidate_provider_ids(assets)

        return primary_asset_id, consolidated_provider_ids

    def _collect_all_assets(self, wiz_issue: Dict[str, Any]) -> List[tuple[str, Optional[str]]]:
        """Collect all assets from entitySnapshot and relatedEntities."""
        assets = []

        # Check entitySnapshot first (primary asset)
        assets.extend(self._extract_entity_snapshot_assets(wiz_issue))

        # Check related entities (additional assets)
        assets.extend(self._extract_related_entity_assets(wiz_issue))

        # If no assets found yet, try the standard single-asset approach
        if not assets:
            asset_id, provider_id = self._get_asset_identifiers(wiz_issue)
            if asset_id:
                assets.append((asset_id, provider_id))

        return assets

    def _extract_entity_snapshot_assets(self, wiz_issue: Dict[str, Any]) -> List[tuple[str, Optional[str]]]:
        """Extract assets from entitySnapshot."""
        assets = []
        if entity_snapshot := wiz_issue.get("entitySnapshot"):
            if entity_id := entity_snapshot.get("id"):
                provider_id = self._get_provider_id_from_entity(entity_snapshot)
                assets.append((entity_id, provider_id))
        return assets

    def _extract_related_entity_assets(self, wiz_issue: Dict[str, Any]) -> List[tuple[str, Optional[str]]]:
        """Extract assets from relatedEntities."""
        assets = []
        entities = wiz_issue.get("relatedEntities", [])
        if entities and isinstance(entities, list):
            for entity in entities:
                if entity and isinstance(entity, dict) and (entity_id := entity.get("id")):
                    provider_id = self._get_provider_id_from_entity(entity)
                    assets.append((entity_id, provider_id))
        return assets

    def _consolidate_provider_ids(self, assets: List[tuple[str, Optional[str]]]) -> Optional[str]:
        """Consolidate provider IDs from assets into newline-separated string."""
        provider_ids = [provider_id for _, provider_id in assets if provider_id]
        return "\n".join(provider_ids) if provider_ids else None

    def _parse_security_subcategories(self, source_rule: Dict[str, Any]) -> List[str]:
        """
        Parse security subcategories from a source rule.

        :param Dict[str, Any] source_rule: The source rule containing security subcategories
        :return: List of formatted security subcategories
        :rtype: List[str]
        """
        if not source_rule or "securitySubCategories" not in source_rule:
            return []

        subcategories = []
        for subcat in source_rule.get("securitySubCategories", []):
            if control_id := self._extract_nist_control_id(subcat):
                subcategories.append(control_id)

        return subcategories

    def _extract_nist_control_id(self, subcat: Dict[str, Any]) -> Optional[str]:
        """
        Extract and format NIST control ID from a security subcategory.

        :param Dict[str, Any] subcat: The security subcategory data
        :return: Formatted control ID or None if invalid
        :rtype: Optional[str]
        """
        framework = subcat.get("category", {}).get("framework", {}).get("name", "")
        external_id = subcat.get("externalId", "")

        if not external_id or "NIST SP 800-53" not in framework:
            return None

        return self._format_control_id(external_id.strip())

    @staticmethod
    def _format_control_id(control_id: str) -> Optional[str]:
        """
        Format a control ID into RegScale format.

        :param str control_id: The raw control ID
        :return: Formatted control ID or None if invalid
        :rtype: Optional[str]
        """
        match = re.match(r"^([A-Z]{2})-(\d+)(?:\s*\((\d+)\))?$", control_id)
        if not match:
            return None

        family = match.group(1).lower()
        number = match.group(2)
        enhancement = match.group(3)

        return f"{family}-{number}" + (f".{enhancement}" if enhancement else "")

    @staticmethod
    def _get_asset_identifier(wiz_issue: Dict[str, Any]) -> str:
        """
        Get the asset identifier from a Wiz issue.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: The asset identifier
        :rtype: str
        """
        return (
            WizIssue._get_id_from_entity_snapshot(wiz_issue)
            or WizIssue._get_id_from_related_entities(wiz_issue)
            or WizIssue._get_id_from_asset_paths(wiz_issue)
            or WizIssue._get_id_from_source_rule(wiz_issue)
            or WizIssue._get_fallback_issue_id(wiz_issue)
        )

    @staticmethod
    def _get_id_from_entity_snapshot(wiz_issue: Dict[str, Any]) -> Optional[str]:
        """
        Get asset ID from entitySnapshot.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Asset ID if found, None otherwise
        :rtype: Optional[str]
        """
        if entity_snapshot := wiz_issue.get("entitySnapshot"):
            return entity_snapshot.get("id")
        return None

    @staticmethod
    def _get_id_from_related_entities(wiz_issue: Dict[str, Any]) -> Optional[str]:
        """
        Get asset ID from related entities.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Asset ID if found, None otherwise
        :rtype: Optional[str]
        """
        if "relatedEntities" not in wiz_issue:
            return None

        entities = wiz_issue.get("relatedEntities", [])
        if not (entities and isinstance(entities, list)):
            return None

        for entity in entities:
            if entity and isinstance(entity, dict):
                if entity_id := entity.get("id"):
                    return entity_id
        return None

    @staticmethod
    def _get_id_from_asset_paths(wiz_issue: Dict[str, Any]) -> Optional[str]:
        """
        Get asset ID from common asset ID paths.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Asset ID if found, None otherwise
        :rtype: Optional[str]
        """
        asset_paths = [
            "vulnerableAsset.id",
            "entity.id",
            "resource.id",
            "relatedEntity.id",
            "sourceEntity.id",
            "target.id",
        ]

        for path in asset_paths:
            if asset_id := get_value(wiz_issue, path):
                return asset_id
        return None

    @staticmethod
    def _get_id_from_source_rule(wiz_issue: Dict[str, Any]) -> Optional[str]:
        """
        Get asset ID from source rule as fallback.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Asset ID if found, None otherwise
        :rtype: Optional[str]
        """
        if source_rule := wiz_issue.get("sourceRule"):
            if rule_id := source_rule.get("id"):
                return f"wiz-rule-{rule_id}"
        return None

    @staticmethod
    def _get_fallback_issue_id(wiz_issue: Dict[str, Any]) -> str:
        """
        Get fallback asset ID using the issue ID.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Fallback asset ID
        :rtype: str
        """
        return f"wiz-issue-{wiz_issue.get('id', 'unknown')}"

    @staticmethod
    def _get_asset_identifiers(wiz_issue: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """
        Get both asset_identifier and issue_asset_identifier_value consistently.
        Ensures both values refer to the same asset entity.

        :param Dict[str, Any] wiz_issue: The Wiz issue
        :return: Tuple of (asset_identifier, issue_asset_identifier_value)
        :rtype: tuple[str, Optional[str]]
        """
        # Try each potential source in order
        asset_id, provider_id = WizIssue._try_entity_snapshot(wiz_issue)
        if asset_id:
            return asset_id, provider_id

        asset_id, provider_id = WizIssue._try_related_entities(wiz_issue)
        if asset_id:
            return asset_id, provider_id

        asset_id, provider_id = WizIssue._try_common_asset_paths(wiz_issue)
        if asset_id:
            return asset_id, provider_id

        return WizIssue._get_fallback_identifiers(wiz_issue)

    @staticmethod
    def _try_entity_snapshot(wiz_issue: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Try to get identifiers from entitySnapshot."""
        if entity_snapshot := wiz_issue.get("entitySnapshot"):
            if entity_id := entity_snapshot.get("id"):
                provider_id = WizIssue._get_provider_id_from_entity(entity_snapshot)
                return entity_id, provider_id
        return None, None

    @staticmethod
    def _try_related_entities(wiz_issue: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Try to get identifiers from relatedEntities."""
        if "relatedEntities" in wiz_issue:
            entities = wiz_issue.get("relatedEntities", [])
            if entities and isinstance(entities, list):
                for entity in entities:
                    if entity and isinstance(entity, dict) and (entity_id := entity.get("id")):
                        provider_id = WizIssue._get_provider_id_from_entity(entity)
                        return entity_id, provider_id
        return None, None

    @staticmethod
    def _try_common_asset_paths(wiz_issue: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Try to get identifiers from common asset paths."""
        asset_paths = ["vulnerableAsset", "entity", "resource", "relatedEntity", "sourceEntity", "target"]

        for path in asset_paths:
            if asset_obj := wiz_issue.get(path):
                if asset_id := asset_obj.get("id"):
                    provider_id = WizIssue._get_provider_id_from_entity(asset_obj)
                    return asset_id, provider_id
        return None, None

    @staticmethod
    def _get_fallback_identifiers(wiz_issue: Dict[str, Any]) -> tuple[str, None]:
        """Get fallback identifiers when no asset entity is found."""
        # Try source rule as fallback
        if source_rule := wiz_issue.get("sourceRule"):
            if rule_id := source_rule.get("id"):
                return f"wiz-rule-{rule_id}", None

        # Final fallback - use the issue ID
        issue_id = wiz_issue.get("id", "unknown")
        return f"wiz-issue-{issue_id}", None

    @staticmethod
    def _get_provider_id_from_entity(entity: Dict[str, Any]) -> Optional[str]:
        """Extract provider ID from an entity object."""
        return entity.get("providerId") or entity.get("providerUniqueId") or entity.get("name")

    @staticmethod
    def _format_control_description(control: Dict[str, Any]) -> str:
        """
        Format the control description with additional context.
        Handles different description field names for different source rule types.

        :param Dict[str, Any] control: The control data
        :return: Formatted description
        :rtype: str
        """
        formatted_desc = []

        # Try different description field names based on source rule type
        description = (
            control.get("controlDescription")
            or control.get("cloudEventRuleDescription")
            or control.get("cloudConfigurationRuleDescription")
            or control.get("description", "")
        )

        if description:
            formatted_desc.append("Description:")
            formatted_desc.append(description)

        # Try different recommendation field names
        recommendation = control.get("resolutionRecommendation") or control.get("remediationInstructions", "")

        if recommendation:
            if formatted_desc:
                formatted_desc.append("\n")
            formatted_desc.append("Resolution Recommendation:")
            formatted_desc.append(recommendation)

        return "\n".join(formatted_desc) if formatted_desc else "No description available"

    def _get_plugin_name(self, wiz_issue: Dict[str, Any]) -> str:
        """
        Generate a unique plugin name based on the Wiz issue type and source rule.

        :param Dict[str, Any] wiz_issue: The Wiz issue data
        :return: A unique plugin name
        :rtype: str
        """
        source_rule = wiz_issue.get("sourceRule", {})
        typename = source_rule.get("__typename", "")
        service_type = source_rule.get("serviceType", "")
        name = source_rule.get("name", "")

        if not typename:
            return "Wiz-Finding"

        if typename == "CloudConfigurationRule":
            return self._get_config_plugin_name(name, service_type)
        if typename == "Control":
            return self._get_control_plugin_name(source_rule, name)
        if typename == "CloudEventRule":
            return self._get_event_plugin_name(name, service_type)

        return "Wiz-Finding"

    @staticmethod
    def _get_config_plugin_name(name: str, service_type: str) -> str:
        """
        Generate plugin name for CloudConfigurationRule type.

        :param str name: Rule name
        :param str service_type: Service type
        :return: Plugin name
        :rtype: str
        """
        if not name:
            return f"Wiz-{service_type}-Config"

        # Safe regex pattern that looks for service name at start
        service_match = re.match(r"^([A-Za-z\s]{1,50}?)\s+(?:public|private|should|must|needs|to)", name)
        if not service_match:
            return f"Wiz-{service_type}-Config"

        service_name = service_match.group(1).strip()
        if service_name == "App Configuration":
            return f"Wiz-{service_type}-AppConfiguration"

        service_name = "".join(word.capitalize() for word in service_name.split())
        return f"Wiz-{service_type}-{service_name}"

    @staticmethod
    def _get_control_plugin_name(source_rule: Dict[str, Any], name: str) -> str:
        """
        Generate plugin name for Control type.

        :param Dict[str, Any] source_rule: Source rule data
        :param str name: Rule name
        :return: Plugin name
        :rtype: str
        """
        # Try to get NIST category first
        subcategories = source_rule.get("securitySubCategories", [])
        for subcat in subcategories:
            category = subcat.get("category", {})
            if category.get("framework", {}).get("name", "").lower() == "nist sp 800-53 revision 5":
                category_name = category.get("name", "")
                category_match = re.match(r"^([A-Z]+)\s", category_name)
                if category_match:
                    return f"Wiz-Control-{category_match.group(1)}"
                break

        # Fallback to control name prefix
        if name:
            prefix_match = re.match(
                r"^([A-Za-z\s]{1,50}?)\s+(?:exposed|misconfigured|vulnerable|security|access)", name
            )
            if prefix_match:
                prefix = "".join(word.capitalize() for word in prefix_match.group(1).strip().split())
                return f"Wiz-Control-{prefix}"

        return "Wiz-Security-Control"

    @staticmethod
    def _get_event_plugin_name(name: str, service_type: str) -> str:
        """
        Generate plugin name for CloudEventRule type.

        :param str name: Rule name
        :param str service_type: Service type
        :return: Plugin name
        :rtype: str
        """
        if not service_type:
            return "Wiz-Event"
        if not name:
            return f"Wiz-{service_type}-Event"
        event_match = re.match(r"^([A-Za-z]+(?: [A-Za-z]+)*)\s+(detection|event|alert|activity)", name)
        if not event_match:
            return f"Wiz-{service_type}-Event"

        event_type = event_match.group(1).strip()
        if event_type == "Suspicious" and event_match.group(2).strip().lower() == "activity":
            return f"Wiz-{service_type}-SuspiciousActivity"

        event_type = "".join(word.capitalize() for word in event_type.split())
        return f"Wiz-{service_type}-{event_type}"

    @staticmethod
    def _get_source_rule_id(source_rule: Dict[str, Any]) -> str:
        """
        Generate a source rule identifier that includes the type and ID.

        :param Dict[str, Any] source_rule: The source rule data
        :return: A formatted source rule identifier
        :rtype: str
        """
        typename = source_rule.get("__typename", "")
        rule_id = source_rule.get("id", "")
        service_type = source_rule.get("serviceType", "")

        if typename and rule_id:
            if service_type:
                return f"{typename}-{service_type}-{rule_id}"
            return f"{typename}-{rule_id}"
        return rule_id

    # noinspection PyMethodOverriding
    def parse_finding(self, wiz_issue: Dict[str, Any], vulnerability_type: WizVulnerabilityType) -> IntegrationFinding:
        """
        Parses a Wiz issue into an IntegrationFinding object.

        :param Dict[str, Any] wiz_issue: The Wiz issue to parse
        :param WizVulnerabilityType vulnerability_type: The type of vulnerability
        :return: The parsed IntegrationFinding
        :rtype: IntegrationFinding
        """
        wiz_id = wiz_issue.get("id", "N/A")
        severity = self.get_issue_severity(wiz_issue.get("severity", "Low"))

        # Get status with diagnostic logging
        wiz_status = wiz_issue.get("status", "OPEN")
        logger.debug(f"Processing Wiz issue {wiz_id}: raw status from node = '{wiz_status}'")
        status = self.map_status_to_issue_status(wiz_status)

        # Enhanced status mapping logging
        logger.debug(f"STATUS MAPPING: Wiz issue {wiz_id} - '{wiz_status}' -> {status}")

        # Check if we're creating a closed issue (which might not appear in your count)
        if status == regscale_models.IssueStatus.Closed:
            logger.debug(
                f"CLOSED ISSUE: Issue {wiz_id} will be created as CLOSED (status='{wiz_status}') - this won't appear in open issue counts"
            )

            # Add diagnostic logging for unexpected issue closure
            if wiz_status.upper() not in ["RESOLVED", "REJECTED"]:
                logger.warning(
                    f"Unexpected issue closure: Wiz issue status '{wiz_status}' mapped to Closed status "
                    f"for issue {wiz_id} - '{wiz_issue.get('sourceRule', {}).get('name', 'Unknown rule')}'. "
                    f"This may indicate a mapping configuration issue."
                )
        date_created = safe_datetime_str(wiz_issue.get("createdAt"))
        name: str = wiz_issue.get("name", "")

        # Handle source rule (Control) specific fields
        source_rule = wiz_issue.get("sourceRule", {})
        control_name = source_rule.get("name", "")

        # Get control labels from security subcategories
        control_labels = self._parse_security_subcategories(source_rule)

        # Get asset identifier and consolidated provider IDs
        asset_id, issue_asset_identifier_value = self._get_consolidated_asset_identifiers(wiz_issue)

        # Format description with control context
        description = self._format_control_description(source_rule) if source_rule else wiz_issue.get("description", "")

        # Handle CVE if present
        cve = (
            name
            if name and (name.startswith("CVE") or name.startswith("GHSA")) and not wiz_issue.get("cve")
            else wiz_issue.get("cve")
        )

        # Get plugin name and source rule ID
        plugin_name = self._get_plugin_name(wiz_issue)
        source_rule_id = self._get_source_rule_id(source_rule)

        # Get Security Check from plugin name
        security_check = f"Wiz {plugin_name}"

        return IntegrationFinding(
            control_labels=control_labels,
            category="Wiz Control" if source_rule else "Wiz Vulnerability",
            title=control_name or wiz_issue.get("name") or f"unknown - {wiz_id}",
            security_check=security_check,
            description=description,
            severity=severity,
            status=status,
            asset_identifier=asset_id,
            issue_asset_identifier_value=issue_asset_identifier_value,
            external_id=wiz_id,
            first_seen=date_created,
            last_seen=safe_datetime_str(wiz_issue.get("lastDetectedAt")),
            remediation=source_rule.get("resolutionRecommendation")
            or f"Update to version {wiz_issue.get('fixedVersion')} or higher",
            cve=cve,
            plugin_name=plugin_name,
            source_rule_id=source_rule_id,
            vulnerability_type=vulnerability_type.value,
            date_created=date_created,
            due_date=Issue.get_due_date(severity, self.app.config, "wiz", date_created),
            recommendation_for_mitigation=source_rule.get("resolutionRecommendation")
            or wiz_issue.get("description", ""),
            poam_comments=None,
            basis_for_adjustment=None,
        )
