#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tenable Control Compliance Module.

This module provides functionality to update control implementation status based on
Tenable vulnerability findings, similar to the AWS compliance integration.
"""

import logging
from typing import Dict, List, Optional

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.tenablev2.tenable_control_mappings import TenableControlMapper
from regscale.integrations.control_matcher import ControlMatcher
from regscale.models.regscale_models import ControlImplementation, ImplementationObjective, SecurityPlan

logger = logging.getLogger("regscale")


class TenableControlCompliance:
    """Handle control compliance updates based on Tenable vulnerability findings."""

    def __init__(self, plan_id: int, framework: str = None):
        """
        Initialize Tenable Control Compliance handler.

        :param int plan_id: Security plan ID
        :param str framework: Compliance framework (optional, will be detected from plan)
        """
        self.plan_id = plan_id
        self.framework = framework
        self.security_plan = None
        self.control_matcher = ControlMatcher()
        self.control_implementations = {}  # Dict of control_id -> ControlImplementation
        self._load_security_plan()
        self._load_control_implementations()

        # Initialize mapper after loading plan
        if not self.framework and self.security_plan:
            # Try to detect framework from plan's catalog
            self.framework = self._detect_framework()

        self.mapper = TenableControlMapper(framework=self.framework or "NIST800-53R5")

    def _load_security_plan(self) -> None:
        """Load the security plan and cache it."""
        try:
            self.security_plan = SecurityPlan.get(self.plan_id)
            plan_name = getattr(self.security_plan, "title", getattr(self.security_plan, "name", "Unknown"))
            logger.info(f"Loaded security plan {self.plan_id}: {plan_name}")
        except Exception as e:
            logger.error(f"Failed to load security plan {self.plan_id}: {e}")

    def _load_control_implementations(self) -> None:
        """Load control implementations from the security plan using ControlMatcher."""
        try:
            # Use ControlMatcher to properly load control implementations with their control IDs
            self.control_implementations = self.control_matcher.get_security_plan_controls(self.plan_id)
            logger.info(f"Loaded {len(self.control_implementations)} control implementations from plan {self.plan_id}")
        except Exception as e:
            logger.error(f"Failed to load control implementations: {e}")
            self.control_implementations = {}

    def _detect_framework(self) -> Optional[str]:
        """
        Detect the framework from the security plan's control implementations.

        :return: Framework identifier or None
        :rtype: Optional[str]
        """
        if not self.control_implementations:
            return None

        # Check first 10 control IDs from the dict keys
        sample_control_ids = list(self.control_implementations.keys())[:10]

        for control_id in sample_control_ids:
            if control_id:
                # NIST 800-53 pattern (e.g., AC-2, SI-4, CM-6)
                if "-" in control_id and len(control_id.split("-")[0]) <= 3:
                    return "NIST800-53R5"

                # CMMC pattern (e.g., AC.1.001)
                if "." in control_id and not control_id.startswith("A."):
                    return "CMMC"

        return None

    def map_vulnerabilities_to_controls(self, vulnerabilities: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Map vulnerabilities to controls.

        :param List[Dict] vulnerabilities: List of vulnerability findings
        :return: Dictionary mapping control IDs to their vulnerabilities
        :rtype: Dict[str, List[Dict]]
        """
        control_vulns_map = {}

        for vuln in vulnerabilities:
            control_ids = self.mapper.map_vulnerability_to_controls(vuln)

            for control_id in control_ids:
                if control_id not in control_vulns_map:
                    control_vulns_map[control_id] = []
                control_vulns_map[control_id].append(vuln)

        logger.info(f"Mapped {len(vulnerabilities)} vulnerabilities to {len(control_vulns_map)} controls")

        return control_vulns_map

    def _update_implementation_fields(self, implementation, assessment, control_id):
        """Update control implementation fields with assessment data."""
        implementation.status = assessment["status"]
        implementation.dateLastAssessed = get_current_datetime()
        implementation.lastAssessmentResult = assessment["result"]

        # Add assessment notes
        vuln_summary = f"Tenable Assessment: {assessment['vulnerability_count']} vulnerabilities found. "
        vuln_summary += f"Highest severity: {assessment['highest_severity'].upper()}. "
        vuln_summary += f"Result: {assessment['result']}."

        if hasattr(implementation, "notes"):
            if implementation.notes:
                implementation.notes += f"\n\n{vuln_summary}"
            else:
                implementation.notes = vuln_summary

        # Ensure required fields are set
        if not implementation.responsibility:
            implementation.responsibility = ControlImplementation.get_default_responsibility(
                parent_id=implementation.parentId
            )

        if not implementation.implementation:
            implementation.implementation = f"Implementation details for {control_id} will be documented."

    def _update_control_objectives(self, implementation, assessment, control_id):
        """Update implementation objectives with assessment status."""
        try:
            objectives = ImplementationObjective.get_all_by_parent(
                parent_module=implementation.get_module_slug(),
                parent_id=implementation.id,
            )

            for objective in objectives:
                objective.status = assessment["status"]
                objective.save()

            if objectives:
                logger.debug(f"Updated {len(objectives)} objectives for control {control_id}")

        except Exception as e:
            logger.warning(f"Failed to update objectives for control {control_id}: {e}")

    def update_control_implementations(
        self, vulnerabilities: List[Dict], update_controls: bool = True
    ) -> Dict[str, any]:
        """
        Update control implementations based on vulnerability findings.

        :param List[Dict] vulnerabilities: List of vulnerability findings
        :param bool update_controls: Whether to actually update controls (default: True)
        :return: Summary of updates performed
        :rtype: Dict[str, any]
        """
        if not update_controls:
            logger.info("Control update is disabled, skipping control implementation updates")
            return {"updated": 0, "skipped": 0, "message": "Control updates disabled"}

        if not self.security_plan or not self.control_implementations:
            logger.warning("No security plan or control implementations loaded")
            return {"updated": 0, "skipped": 0, "message": "No security plan or control implementations"}

        # Map vulnerabilities to controls
        control_vulns_map = self.map_vulnerabilities_to_controls(vulnerabilities)
        logger.info(f"Working with {len(self.control_implementations)} control implementations")

        # Log sample IDs for debugging
        sample_control_ids = list(self.control_implementations.keys())[:5]
        mapped_control_ids = list(control_vulns_map.keys())[:5]
        logger.info(f"Sample plan control IDs: {sample_control_ids}")
        logger.info(f"Sample mapped control IDs: {mapped_control_ids}")
        logger.info(f"Filtering {len(control_vulns_map)} mapped controls to match plan controls")

        updated_count = 0
        skipped_count = 0

        # Update each control based on its vulnerabilities
        for control_id, vulns in control_vulns_map.items():
            implementation = self.control_matcher.find_control_implementation(control_id, self.plan_id, "securityplans")

            if not implementation:
                logger.debug(f"Control {control_id} not found in plan, skipping")
                skipped_count += 1
                continue

            assessment = self.mapper.assess_control_from_vulnerabilities(control_id, vulns)

            try:
                self._update_implementation_fields(implementation, assessment, control_id)
                implementation.save()
                updated_count += 1

                logger.info(
                    f"Updated control {control_id}: {assessment['status']} "
                    f"({assessment['vulnerability_count']} vulns, {assessment['result']})"
                )

                self._update_control_objectives(implementation, assessment, control_id)

            except Exception as e:
                logger.error(f"Failed to update control {control_id}: {e}")
                skipped_count += 1

        logger.info(f"Control update complete: {updated_count} updated, {skipped_count} skipped")

        return {
            "updated": updated_count,
            "skipped": skipped_count,
            "total_vulnerabilities": len(vulnerabilities),
            "mapped_controls": len(control_vulns_map),
            "message": f"Successfully updated {updated_count} control implementations",
        }

    def get_control_status_summary(self, vulnerabilities: List[Dict]) -> Dict[str, any]:
        """
        Get a summary of control statuses without updating them.

        :param List[Dict] vulnerabilities: List of vulnerability findings
        :return: Summary of control statuses
        :rtype: Dict[str, any]
        """
        control_vulns_map = self.map_vulnerabilities_to_controls(vulnerabilities)

        summary = {"controls": {}, "totals": {"critical": 0, "high": 0, "medium": 0, "low": 0}}

        for control_id, vulns in control_vulns_map.items():
            assessment = self.mapper.assess_control_from_vulnerabilities(control_id, vulns)
            summary["controls"][control_id] = assessment

            # Update totals
            for severity, count in assessment["severity_breakdown"].items():
                if severity in summary["totals"]:
                    summary["totals"][severity] += count

        return summary
