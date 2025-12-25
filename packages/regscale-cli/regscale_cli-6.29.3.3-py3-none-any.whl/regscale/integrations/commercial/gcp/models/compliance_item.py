#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Security Command Center Compliance Item for RegScale CLI.

This module provides the GCPComplianceItem class for representing compliance assessment
results from GCP Security Command Center findings.
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.compliance_integration import ComplianceItem

logger = logging.getLogger("regscale")

# HTML tag constants for description formatting
HTML_STRONG_OPEN = "<strong>"
HTML_STRONG_CLOSE = "</strong>"
HTML_P_OPEN = "<p>"
HTML_P_CLOSE = "</p>"
HTML_UL_OPEN = "<ul>"
HTML_UL_CLOSE = "</ul>"
HTML_LI_OPEN = "<li>"
HTML_LI_CLOSE = "</li>"
HTML_H3_OPEN = "<h3>"
HTML_H3_CLOSE = "</h3>"
HTML_H4_OPEN = "<h4>"
HTML_H4_CLOSE = "</h4>"
HTML_BR = "<br>"


class GCPComplianceItem(ComplianceItem):
    """
    Compliance item from GCP Security Command Center finding.

    Represents a control assessment based on GCP SCC findings. Multiple findings
    can map to a single control, and the control passes only if ALL associated
    findings are resolved (state=ACTIVE means failing).

    GCP SCC Finding States:
    - ACTIVE: The finding is active (non-compliant)
    - INACTIVE: The finding has been resolved (compliant)

    GCP SCC Finding Severities:
    - CRITICAL: Most severe
    - HIGH: High severity
    - MEDIUM: Medium severity
    - LOW: Low severity
    - UNSPECIFIED: No severity specified
    """

    def __init__(
        self,
        control_id: str,
        control_name: str,
        framework: str,
        finding_evaluations: List[Dict[str, Any]],
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
    ):
        """
        Initialize from GCP SCC finding evaluations.

        :param str control_id: Control identifier (e.g., AC-2, SI-3)
        :param str control_name: Human-readable control name
        :param str framework: Compliance framework (e.g., NIST800-53R5, CIS)
        :param List[Dict[str, Any]] finding_evaluations: SCC finding evaluation results
        :param Optional[str] resource_id: Resource identifier (GCP project ID typically)
        :param Optional[str] resource_name: Resource name
        """
        self._control_id = control_id
        self._control_name = control_name
        self._framework = framework
        self.finding_evaluations = finding_evaluations
        self._resource_id = resource_id or ""
        self._resource_name = resource_name or ""

        # Cache for aggregated compliance result
        self._aggregated_compliance_result = None
        self._result_was_cached = False

    @property
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        return self._resource_id

    @property
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        return self._resource_name

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        return self._control_id

    def _aggregate_finding_compliance(self) -> Optional[str]:
        """
        Aggregate SCC finding results to determine overall control compliance.

        GCP SCC finding states:
        - "ACTIVE": Finding is active (resource is non-compliant)
        - "INACTIVE": Finding has been resolved (resource is compliant)

        Aggregation Logic (fail-first):
        1. If ANY finding shows "ACTIVE" → Control FAILS
        2. If ALL findings show "INACTIVE" → Control PASSES
        3. If no findings or inconclusive data → None (inconclusive)

        :return: "PASS", "FAIL", or None (if inconclusive/no data)
        :rtype: Optional[str]
        """
        if not self.finding_evaluations:
            logger.debug(f"Control {self.control_id}: No finding evaluations available")
            return None

        active_count = 0
        inactive_count = 0
        other_count = 0

        for evaluation in self.finding_evaluations:
            state = evaluation.get("state", "").upper()

            if state == "ACTIVE":
                active_count += 1
            elif state == "INACTIVE":
                inactive_count += 1
            else:
                other_count += 1

        total_evaluations = len(self.finding_evaluations)

        logger.debug(
            f"Control {self.control_id} finding summary: "
            f"{active_count} ACTIVE, {inactive_count} INACTIVE, "
            f"{other_count} OTHER out of {total_evaluations} total"
        )

        # If ANY finding is active (non-compliant), the control fails
        if active_count > 0:
            logger.info(f"Control {self.control_id} FAILS: {active_count} active finding(s) out of {total_evaluations}")
            return "FAIL"

        # If we have inactive findings and no active findings, control passes
        if inactive_count > 0:
            if other_count > 0:
                logger.info(
                    f"Control {self.control_id} PASSES: {inactive_count} inactive, "
                    f"{other_count} other state (no active findings)"
                )
            else:
                logger.info(f"Control {self.control_id} PASSES: All {inactive_count} findings inactive")
            return "PASS"

        # If no applicable compliance checks available, we cannot determine status
        logger.warning(
            f"Control {self.control_id}: No conclusive compliance checks in {total_evaluations} evaluation(s)"
        )
        return None

    @property
    def compliance_result(self) -> Optional[str]:
        """
        Result of compliance check (PASS, FAIL, etc).

        Aggregates SCC finding evaluations to determine control-level compliance.

        :return: "PASS", "FAIL", or None (if no conclusive data available)
        :rtype: Optional[str]
        """
        # Use cached result if available
        if self._result_was_cached:
            return self._aggregated_compliance_result

        # Aggregate finding compliance checks
        result = self._aggregate_finding_compliance()

        if result is None:
            logger.info(
                f"Control {self.control_id}: No conclusive data for compliance determination. "
                f"Control status will not be updated. Finding evaluations: {len(self.finding_evaluations)}"
            )

        # Cache the result (including None)
        self._aggregated_compliance_result = result
        self._result_was_cached = True
        return result

    @property
    def severity(self) -> Optional[str]:
        """Severity level of the compliance violation (if failed)."""
        if self.compliance_result != "FAIL":
            return None

        # Determine severity based on highest severity of active findings
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNSPECIFIED": 4}
        highest_severity = "LOW"

        for evaluation in self.finding_evaluations:
            if evaluation.get("state", "").upper() == "ACTIVE":
                finding_severity = evaluation.get("severity", "UNSPECIFIED").upper()
                if severity_order.get(finding_severity, 4) < severity_order.get(highest_severity, 4):
                    highest_severity = finding_severity

        # Map GCP severity to RegScale severity
        if highest_severity == "CRITICAL":
            return "CRITICAL"
        elif highest_severity == "HIGH":
            return "HIGH"
        elif highest_severity == "MEDIUM":
            return "MEDIUM"
        return "LOW"

    @property
    def description(self) -> str:
        """Description of the compliance check using HTML formatting."""
        desc_parts = [
            f"{HTML_H3_OPEN}GCP Security Command Center compliance assessment for control "
            f"{self.control_id}{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Control:{HTML_STRONG_CLOSE} {self._control_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self._framework}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Total Findings:{HTML_STRONG_CLOSE} {len(self.finding_evaluations)}",
            HTML_P_CLOSE,
        ]

        # Add compliance summary
        active_findings = [e for e in self.finding_evaluations if e.get("state", "").upper() == "ACTIVE"]
        inactive_findings = [e for e in self.finding_evaluations if e.get("state", "").upper() == "INACTIVE"]

        desc_parts.extend(
            [
                f"{HTML_H4_OPEN}Compliance Summary{HTML_H4_CLOSE}",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Active (Non-Compliant) Findings:{HTML_STRONG_CLOSE} "
                f"{len(active_findings)}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Inactive (Resolved) Findings:{HTML_STRONG_CLOSE} "
                f"{len(inactive_findings)}{HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
            ]
        )

        # Add active findings details
        if active_findings:
            desc_parts.append(f"{HTML_H4_OPEN}Active Findings{HTML_H4_CLOSE}")
            desc_parts.append(HTML_UL_OPEN)
            for finding in active_findings[:10]:  # Show up to 10 active findings
                category = finding.get("finding_category", "Unknown")
                severity = finding.get("severity", "UNSPECIFIED")
                resource = finding.get("resource_name", "Unknown resource")
                desc_parts.append(
                    f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{category}{HTML_STRONG_CLOSE} "
                    f"[{severity}]: {resource}{HTML_LI_CLOSE}"
                )
            if len(active_findings) > 10:
                desc_parts.append(
                    f"{HTML_LI_OPEN}... and {len(active_findings) - 10} more active finding(s){HTML_LI_CLOSE}"
                )
            desc_parts.append(HTML_UL_CLOSE)

        return "\n".join(desc_parts)

    @property
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CIS)."""
        return self._framework

    @classmethod
    def from_scc_finding(
        cls,
        finding: Dict[str, Any],
        framework: str,
        control_ids: List[str],
        project_id: Optional[str] = None,
    ) -> List["GCPComplianceItem"]:
        """
        Create GCPComplianceItem instances from a raw SCC finding.

        Factory method to create compliance items from GCP SCC finding data.
        A single finding can map to multiple controls, so this returns a list.

        :param Dict[str, Any] finding: Raw SCC finding data (parsed format)
        :param str framework: Compliance framework name
        :param List[str] control_ids: List of control IDs this finding maps to
        :param Optional[str] project_id: GCP project ID for resource identification
        :return: List of GCPComplianceItem instances (one per control)
        :rtype: List[GCPComplianceItem]
        """
        # Extract finding details
        finding_evaluation = {
            "finding_name": finding.get("name", ""),
            "finding_category": finding.get("category", ""),
            "source_type": cls._extract_source_type(finding.get("parent", "")),
            "state": finding.get("state", "ACTIVE"),
            "severity": finding.get("severity", "UNSPECIFIED"),
            "resource_name": finding.get("resource_name", ""),
            "external_uri": finding.get("external_uri", ""),
            "description": finding.get("description", ""),
            "recommendation": cls._extract_recommendation(finding),
            "event_time": finding.get("event_time", ""),
            "create_time": finding.get("create_time", ""),
        }

        # Extract project ID from resource name if not provided
        if not project_id:
            project_id = cls._extract_project_id(finding.get("resource_name", ""))

        resource_id = project_id or "unknown-project"
        resource_name = f"GCP Project {project_id}" if project_id else "Unknown Project"

        # Create one compliance item per control
        items = []
        for control_id in control_ids:
            item = cls(
                control_id=control_id,
                control_name=f"Control {control_id}",  # Will be enriched by RegScale lookup
                framework=framework,
                finding_evaluations=[finding_evaluation],
                resource_id=resource_id,
                resource_name=resource_name,
            )
            items.append(item)

        return items

    @staticmethod
    def _extract_source_type(parent_path: str) -> str:
        """
        Extract the source type from the finding's parent path.

        :param str parent_path: Finding parent path (e.g., 'organizations/123/sources/456')
        :return: Source type identifier
        :rtype: str
        """
        # The parent path typically contains the source ID
        # For now, return a generic identifier; can be enhanced with source name lookup
        if "sources/" in parent_path:
            source_id = parent_path.split("sources/")[-1]
            return f"source-{source_id}"
        return "UNKNOWN_SOURCE"

    @staticmethod
    def _extract_recommendation(finding: Dict[str, Any]) -> str:
        """
        Extract remediation recommendation from the finding.

        :param Dict[str, Any] finding: SCC finding data
        :return: Remediation recommendation
        :rtype: str
        """
        # Check source_properties for recommendation
        source_props = finding.get("source_properties", {})
        recommendation = source_props.get("Recommendation", source_props.get("recommendation", ""))

        if not recommendation:
            # Fall back to description if no recommendation found
            recommendation = finding.get("description", "No remediation guidance available")

        return recommendation

    @staticmethod
    def _extract_project_id(resource_name: str) -> Optional[str]:
        """
        Extract GCP project ID from resource name.

        GCP resource names typically follow patterns like:
        - //cloudresourcemanager.googleapis.com/projects/PROJECT_ID
        - projects/PROJECT_ID/...

        :param str resource_name: GCP resource name
        :return: Project ID or None
        :rtype: Optional[str]
        """
        if not resource_name:
            return None

        # Try pattern: projects/PROJECT_ID
        if "projects/" in resource_name:
            parts = resource_name.split("projects/")
            if len(parts) > 1:
                project_part = parts[1].split("/")[0]
                return project_part

        return None

    @classmethod
    def aggregate_findings_by_control(
        cls,
        findings: List[Dict[str, Any]],
        control_mapping: Dict[str, List[str]],
        framework: str,
        project_id: Optional[str] = None,
    ) -> List["GCPComplianceItem"]:
        """
        Aggregate multiple SCC findings by control ID.

        Groups findings that map to the same control and creates a single
        GCPComplianceItem per control with all relevant findings.

        Implements fail-first logic: if ANY finding for a control is ACTIVE,
        the control fails.

        :param List[Dict[str, Any]] findings: List of SCC findings (parsed format)
        :param Dict[str, List[str]] control_mapping: Map of finding category to control IDs
        :param str framework: Compliance framework name
        :param Optional[str] project_id: GCP project ID
        :return: List of aggregated GCPComplianceItem instances
        :rtype: List[GCPComplianceItem]
        """
        # Group findings by control ID
        control_findings: Dict[str, List[Dict[str, Any]]] = {}

        for finding in findings:
            category = finding.get("category", "")
            # Get control IDs for this finding category
            control_ids = control_mapping.get(category, [])

            for control_id in control_ids:
                if control_id not in control_findings:
                    control_findings[control_id] = []

                # Create finding evaluation dict
                finding_eval = {
                    "finding_name": finding.get("name", ""),
                    "finding_category": category,
                    "source_type": cls._extract_source_type(finding.get("parent", "")),
                    "state": finding.get("state", "ACTIVE"),
                    "severity": finding.get("severity", "UNSPECIFIED"),
                    "resource_name": finding.get("resource_name", ""),
                    "external_uri": finding.get("external_uri", ""),
                    "description": finding.get("description", ""),
                    "recommendation": cls._extract_recommendation(finding),
                    "event_time": finding.get("event_time", ""),
                    "create_time": finding.get("create_time", ""),
                }
                control_findings[control_id].append(finding_eval)

        # Extract project ID if not provided
        if not project_id and findings:
            project_id = cls._extract_project_id(findings[0].get("resource_name", ""))

        resource_id = project_id or "unknown-project"
        resource_name = f"GCP Project {project_id}" if project_id else "Unknown Project"

        # Create GCPComplianceItem for each control
        compliance_items = []
        for control_id, finding_evals in control_findings.items():
            item = cls(
                control_id=control_id,
                control_name=f"Control {control_id}",
                framework=framework,
                finding_evaluations=finding_evals,
                resource_id=resource_id,
                resource_name=resource_name,
            )
            compliance_items.append(item)

        logger.info(f"Aggregated {len(findings)} findings into {len(compliance_items)} control compliance items")

        return compliance_items
