#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Audit Manager Compliance Integration for RegScale CLI."""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from regscale.core.app.utils.app_utils import create_progress_object, get_current_datetime
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.models import regscale_models

# Import ControlComplianceAnalyzer for enhanced evidence analysis
from regscale.integrations.commercial.aws.control_compliance_analyzer import ControlComplianceAnalyzer

logger = logging.getLogger("regscale")

# Constants for file paths and cache TTL
AUDIT_MANAGER_CACHE_FILE = os.path.join("artifacts", "aws", "audit_manager_assessments.json")
CACHE_TTL_SECONDS = 4 * 60 * 60  # 4 hours in seconds

# AWS Audit Manager IAM permission constants
IAM_PERMISSION_LIST_ASSESSMENTS = "auditmanager:ListAssessments"
IAM_PERMISSION_GET_ASSESSMENT = "auditmanager:GetAssessment"
IAM_PERMISSION_GET_EVIDENCE_FOLDERS = "auditmanager:GetEvidenceFoldersByAssessmentControl"

# HTML tag constants to avoid duplication
HTML_STRONG_OPEN = "<strong>"
HTML_STRONG_CLOSE = "</strong>"
HTML_P_OPEN = "<p>"
HTML_P_CLOSE = "</p>"
HTML_UL_OPEN = "<ul>"
HTML_UL_CLOSE = "</ul>"
HTML_LI_OPEN = "<li>"
HTML_LI_CLOSE = "</li>"
HTML_H4_OPEN = "<h4>"
HTML_H4_CLOSE = "</h4>"
HTML_BR = "<br>"


class AWSAuditManagerComplianceItem(ComplianceItem):
    """
    Compliance item from AWS Audit Manager assessment.

    IMPORTANT: Evidence-Based Compliance Determination
    ---------------------------------------------------
    This integration uses evidence items to determine control compliance status:

    1. Control 'status' field (REVIEWED/UNDER_REVIEW/INACTIVE) is workflow tracking only
    2. Actual compliance is determined by aggregating evidence items' complianceCheck fields
    3. Evidence complianceCheck values (normalized internally):
       Success values (→ "COMPLIANT"):
         - "COMPLIANT" (AWS Config)
         - "PASS" (AWS Security Hub)
       Failure values (→ "FAILED"):
         - "NON_COMPLIANT" / "Non-compliant" (AWS Config)
         - "FAILED" / "FAIL" / "Fail" (AWS Security Hub)
       Other:
         - "NOT_APPLICABLE": Evidence not applicable to this control
         - None/missing: No compliance check available

    Aggregation Logic:
    - ANY evidence with failure values (FAILED, FAIL, NON_COMPLIANT, etc.) → Control FAILS
    - ALL evidence with success values (COMPLIANT, PASS) → Control PASSES
    - NOT_APPLICABLE evidence is tracked separately and doesn't affect compliance
    - No evidence or only inconclusive/not applicable evidence → Returns None (control not updated)

    The None return value signals the integration framework to skip updating the control
    status, preventing false positive/negative results when evidence is unavailable.
    """

    def __init__(
        self,
        assessment_data: Dict[str, Any],
        control_data: Dict[str, Any],
        evidence_items: Optional[List[Dict]] = None,
        use_enhanced_analyzer: bool = False,
    ):
        """
        Initialize from AWS Audit Manager assessment and control data.

        :param Dict[str, Any] assessment_data: Assessment metadata
        :param Dict[str, Any] control_data: Control assessment result
        :param Optional[List[Dict]] evidence_items: Evidence items with complianceCheck fields.
                                                      REQUIRED for accurate compliance determination.
                                                      Without evidence, control status will not be updated.
        :param bool use_enhanced_analyzer: Use enhanced ControlComplianceAnalyzer for evidence analysis
        """
        self.assessment_data = assessment_data
        self.control_data = control_data
        self.evidence_items = evidence_items or []
        self.use_enhanced_analyzer = use_enhanced_analyzer

        # Extract assessment metadata
        self.assessment_name = assessment_data.get("name", "")
        self.assessment_id = assessment_data.get("arn", "")
        self.framework_name = assessment_data.get("framework", {}).get("metadata", {}).get("name", "")
        self.framework_type = assessment_data.get("framework", {}).get("type", "")
        self.compliance_type = assessment_data.get("complianceType", "")
        self.aws_account = assessment_data.get("awsAccount", {})

        # Extract control metadata
        # AWS Audit Manager embeds the control ID in the 'name' field
        # Format: "AC-2 - Control Name" or "AC-2(1) - Control Name with Enhancement"
        control_name = control_data.get("name", "")
        self._control_name = control_name

        # Extract control ID from name field (before the hyphen)
        # Example: "AC-2  -  Access Control" -> "AC-2"
        self._control_id = self._extract_control_id_from_name(control_name)

        self.control_status = control_data.get("status", "UNDER_REVIEW")
        self.control_response = control_data.get("response", "")
        self.control_comments = control_data.get("comments", [])

        # Log extracted control ID for debugging
        logger.debug(f"Extracted control ID: '{self._control_id}' from name: '{control_name}'")

        # Extract evidence counts
        self.evidence_count = control_data.get("evidenceCount", 0)
        self.assessment_report_evidence_count = control_data.get("assessmentReportEvidenceCount", 0)

        # Initialize enhanced analyzer attributes
        self.compliance_score = None
        self.confidence_level = None
        self.compliance_details = None

        # Extract remediation and testing guidance
        self.action_plan_title = control_data.get("actionPlanTitle", "")
        self.action_plan_instructions = control_data.get("actionPlanInstructions", "")
        self.testing_information = control_data.get("testingInformation", "")

        # Resource information (from evidence sources)
        self._resource_id = None
        self._resource_name = None
        self._severity = "MEDIUM"

        # Cache for aggregated compliance result
        self._aggregated_compliance_result = None

    @property
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        if self._resource_id:
            return self._resource_id
        return self.aws_account.get("id", "")

    @property
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        if self._resource_name:
            return self._resource_name
        account_name = self.aws_account.get("name", "")
        account_id = self.aws_account.get("id", "")
        if account_name:
            return f"{account_name} ({account_id})"
        return account_id

    @property
    def resource_arns(self) -> str:
        """
        Extract all failing resource ARNs from evidence, newline-separated.

        Returns newline-separated ARNs for use in issue.assetIdentifier field.
        This provides full resource identification instead of just account ID.
        All FAILED evidence from AWS Security Hub and AWS Config includes resource ARNs.

        :return: Newline-separated ARNs of failing resources
        :rtype: str
        """
        failing_resources = self._extract_failing_resources(self.evidence_items)
        if failing_resources:
            # Extract unique ARNs, filtering out any "Unknown ARN" fallback values
            arns = [res["arn"] for res in failing_resources if res.get("arn") and res["arn"] != "Unknown ARN"]
            if arns:
                return "\n".join(arns)
        # Return empty string if no ARNs found (should never happen for FAILED evidence)
        return ""

    def _try_extract_with_pattern(self, control_name: str, pattern: str) -> Optional[str]:
        """
        Try to extract control ID using a specific regex pattern.

        :param str control_name: Full control name from AWS
        :param str pattern: Regex pattern to match
        :return: Extracted control ID or None
        :rtype: Optional[str]
        """
        import re

        match = re.match(pattern, control_name)
        return match.group(1).strip() if match else None

    def _extract_control_id_from_name(self, control_name: str) -> str:
        """
        Extract control ID from AWS Audit Manager control name.

        Supports multiple control ID formats:
        - NIST (colon): "AC-2: Access Control (NIST-SP-800-53-r5)", "AC-2(1): Enhancement (NIST-SP-800-53-r5)"
        - NIST (hyphen): "AC-2  -  Access Control", "AC-2(1)  -   Access Control Enhancement"
        - SOC 2: "CC1.1 COSO Principle 1...", "PI1.5 The entity implements..."
        - CIS: "1.1 Ensure...", "1.1.1 Ensure..."
        - ISO: "A.5.1 Policies for...", "A.5.1.1 Policies..."

        :param str control_name: Full control name from AWS
        :return: Extracted control ID
        :rtype: str
        """
        if not control_name:
            return ""

        # Define patterns in order of specificity
        patterns = [
            r"^([A-Z]{2,3}-\d+(?:\(\d+\))?):\s*",  # NIST with colon
            r"^([A-Z]{2,3}-\d+(?:\(\d+\))?)\s*-\s*",  # NIST with hyphen
            r"^([A-Z]{1,3}\d+\.\d+)\s+",  # SOC 2
            r"^(\d+(?:\.\d+){1,3})\s+",  # CIS
            r"^([A-Z]\.\d+(?:\.\d+){1,2})\s+",  # ISO
            r"^([A-Z]+\d+(?:\.\d+)*)\s+",  # Generic alphanumeric with dots
        ]

        for pattern in patterns:
            result = self._try_extract_with_pattern(control_name, pattern)
            if result:
                return result

        logger.warning(f"Could not extract control ID from name: '{control_name}'")
        return ""

    def _parse_remediation_from_attributes(self, attributes: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse remediation information from evidence attributes.

        Security Hub evidence includes remediation info in attributes.findingRemediation
        as a JSON string: {"recommendation": {"text": "...", "url": "..."}}

        :param Dict[str, Any] attributes: Evidence attributes dictionary
        :return: Dictionary with 'url' and 'text' keys, or empty dict if not available
        :rtype: Dict[str, str]
        """
        import json

        remediation_str = attributes.get("findingRemediation")
        if not remediation_str:
            return {}

        try:
            # Parse the JSON string
            remediation_data = json.loads(remediation_str)
            recommendation = remediation_data.get("recommendation", {})

            return {"url": recommendation.get("url", ""), "text": recommendation.get("text", "")}
        except (json.JSONDecodeError, AttributeError, TypeError) as ex:
            logger.debug(f"Failed to parse remediation from attributes: {ex}")
            return {}

    def _parse_severity_from_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse severity information from evidence attributes.

        Security Hub evidence includes severity in attributes.findingSeverity
        as a JSON string: {"label": "CRITICAL", "normalized": 90, "original": "CRITICAL"}

        :param Dict[str, Any] attributes: Evidence attributes dictionary
        :return: Dictionary with 'label', 'normalized', and 'original' keys, or empty dict
        :rtype: Dict[str, Any]
        """
        import json

        severity_str = attributes.get("findingSeverity")
        if not severity_str:
            return {}

        try:
            # Parse the JSON string
            severity_data = json.loads(severity_str)
            return {
                "label": severity_data.get("label", ""),
                "normalized": severity_data.get("normalized", 0),
                "original": severity_data.get("original", ""),
            }
        except (json.JSONDecodeError, AttributeError, TypeError) as ex:
            logger.debug(f"Failed to parse severity from attributes: {ex}")
            return {}

    def _extract_control_name_from_attributes(self, attributes: Dict[str, Any], data_source: str) -> str:
        """
        Extract control or rule name from evidence attributes.

        For Security Hub: extract and clean findingTitle
        For Config: extract configRuleName or managedRuleIdentifier

        :param Dict[str, Any] attributes: Evidence attributes dictionary
        :param str data_source: Evidence data source (e.g., "AWS Security Hub", "AWS Config")
        :return: Control/rule name, or empty string if not available
        :rtype: str
        """
        import json

        if "Security Hub" in data_source:
            # Extract Security Hub control title
            title_str = attributes.get("findingTitle", "")
            if title_str:
                # Remove surrounding quotes if present
                try:
                    # Try to parse as JSON string first (may be quoted)
                    title = json.loads(title_str) if title_str.startswith('"') else title_str
                    return title.strip()
                except (json.JSONDecodeError, AttributeError):
                    return title_str.strip().strip('"')

        elif "Config" in data_source:
            # Extract Config rule name
            rule_name = attributes.get("configRuleName", "")
            if rule_name:
                # Remove surrounding quotes if present
                rule_name = rule_name.strip().strip('"')
                return rule_name

            # Fall back to managed rule identifier
            managed_id = attributes.get("managedRuleIdentifier", "")
            if managed_id:
                managed_id = managed_id.strip().strip('"')
                return managed_id

        return ""

    def _extract_failing_resources(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract all failing resources from evidence items.

        Returns list of resources with FAILED or NON_COMPLIANT status,
        including their ARN, source (control/rule name), and severity.

        :param List[Dict[str, Any]] evidence_items: List of evidence items
        :return: List of failing resource dictionaries
        :rtype: List[Dict[str, str]]
        """
        failing_resources = []

        for evidence in evidence_items:
            # Get compliance check result
            compliance = self._get_evidence_compliance(evidence)
            if compliance != "FAILED":
                continue

            # Extract data source and attributes
            data_source = evidence.get("dataSource", "Unknown")
            attributes = evidence.get("attributes", {})

            # Get control/rule name
            control_name = self._extract_control_name_from_attributes(attributes, data_source)

            # Get severity
            severity_info = self._parse_severity_from_attributes(attributes)
            severity_label = severity_info.get("label", "MEDIUM") if severity_info else "MEDIUM"

            # Extract failing resources from resourcesIncluded
            resources_included = evidence.get("resourcesIncluded", [])
            for resource in resources_included:
                resource_check = resource.get("complianceCheck")
                # Check if this specific resource failed
                if resource_check in ("FAILED", "FAIL", "NON_COMPLIANT", "Non-compliant"):
                    arn = resource.get("arn", "Unknown ARN")
                    failing_resources.append(
                        {"arn": arn, "source": f"{data_source}: {control_name}", "severity": severity_label}
                    )

        return failing_resources

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        # The control ID is already in the correct format from the name field
        # Just return it directly
        return self._control_id if self._control_id else ""

    def _extract_resource_compliance(self, resources_included: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract compliance status from resourcesIncluded list.

        :param List[Dict[str, Any]] resources_included: List of resources
        :return: "COMPLIANT", "FAILED", "NOT_APPLICABLE", or None
        :rtype: Optional[str]
        """
        if not resources_included:
            return None

        resource_checks = [r.get("complianceCheck") for r in resources_included]

        # Check for any failure values (case-insensitive)
        failure_values = {"FAILED", "FAIL", "Fail", "NON_COMPLIANT", "Non-compliant"}
        if any(check in failure_values for check in resource_checks):
            return "FAILED"

        # Check for any success values (case-insensitive)
        if any(check in {"COMPLIANT", "PASS", "Pass"} for check in resource_checks):
            return "COMPLIANT"

        if any(check == "NOT_APPLICABLE" for check in resource_checks):
            return "NOT_APPLICABLE"

        return None

    def _normalize_compliance_value(self, compliance_check: str, evidence: Dict[str, Any]) -> Optional[str]:
        """
        Normalize compliance check value to standard format.

        :param str compliance_check: Raw compliance check value
        :param Dict[str, Any] evidence: Evidence item for logging context
        :return: Normalized compliance value or None
        :rtype: Optional[str]
        """
        if not isinstance(compliance_check, str):
            logger.warning(
                f"Control {self.control_id}: Invalid complianceCheck type {type(compliance_check).__name__}: "
                f"{compliance_check}. Treating as inconclusive."
            )
            return None

        compliance_upper = compliance_check.upper().replace("-", "_").replace(" ", "_")

        # Normalize failure values
        if compliance_upper in {"FAILED", "FAIL", "NON_COMPLIANT"}:
            if compliance_check != "FAILED":
                logger.debug(
                    f"Control {self.control_id}: Normalized '{compliance_check}' to FAILED "
                    f"(source: {evidence.get('dataSource', 'unknown')})"
                )
            return "FAILED"

        # Normalize success values
        if compliance_upper == "PASS":
            logger.debug(
                f"Control {self.control_id}: Normalized PASS to COMPLIANT "
                f"(source: {evidence.get('dataSource', 'unknown')})"
            )
            return "COMPLIANT"

        return compliance_check

    def _get_evidence_compliance(self, evidence: Dict[str, Any]) -> Optional[str]:
        """
        Extract compliance check result from a single evidence item.

        Checks both root-level and resource-level complianceCheck fields.

        AWS Audit Manager uses different values depending on the source:
        Success values (normalized to "COMPLIANT"):
        - "COMPLIANT" - from AWS Config
        - "PASS" - from AWS Security Hub

        Failure values (normalized to "FAILED"):
        - "NON_COMPLIANT" / "Non-compliant" - from AWS Config
        - "FAILED" / "FAIL" / "Fail" - from AWS Security Hub

        :param Dict[str, Any] evidence: Evidence item
        :return: "COMPLIANT", "FAILED", "NOT_APPLICABLE", or None
        :rtype: Optional[str]
        """
        # Check root-level complianceCheck first
        compliance_check = evidence.get("complianceCheck")

        # If no root-level check, look in resourcesIncluded
        if compliance_check is None:
            resources_included = evidence.get("resourcesIncluded", [])
            compliance_check = self._extract_resource_compliance(resources_included)

        # Normalize all variations to standard values
        if compliance_check:
            compliance_check = self._normalize_compliance_value(compliance_check, evidence)

        return compliance_check

    def _log_inconclusive_status(self, not_applicable_count: int, inconclusive_count: int, total_evidence: int) -> None:
        """Log inconclusive status with appropriate message."""
        if not_applicable_count > 0 and inconclusive_count == 0:
            logger.info(
                f"Control {self.control_id}: All {not_applicable_count} evidence item(s) marked as NOT_APPLICABLE. "
                "Control status will not be updated."
            )
        elif not_applicable_count > 0:
            logger.info(
                f"Control {self.control_id}: {not_applicable_count} NOT_APPLICABLE, "
                f"{inconclusive_count} inconclusive evidence item(s). Control status will not be updated."
            )
        else:
            logger.debug(
                f"Control {self.control_id}: Evidence collected ({total_evidence} item(s)) but no valid compliance checks found. "
                "Control status will not be updated. This may occur when evidence lacks complianceCheck fields."
            )

    def _count_evidence_by_status(self) -> tuple:
        """
        Count evidence items by compliance status.

        :return: Tuple of (compliant_count, failed_count, inconclusive_count, not_applicable_count)
        :rtype: tuple
        """
        compliant_count = 0
        failed_count = 0
        inconclusive_count = 0
        not_applicable_count = 0

        for evidence in self.evidence_items:
            compliance_check = self._get_evidence_compliance(evidence)

            if compliance_check == "FAILED":
                failed_count += 1
            elif compliance_check == "COMPLIANT":
                compliant_count += 1
            elif compliance_check == "NOT_APPLICABLE":
                not_applicable_count += 1
            else:
                inconclusive_count += 1

        return compliant_count, failed_count, inconclusive_count, not_applicable_count

    def _determine_compliance_status(self, counts: tuple) -> Optional[str]:
        """
        Determine compliance status based on evidence counts.

        :param tuple counts: Tuple of (compliant, failed, inconclusive, not_applicable) counts
        :return: "PASS", "FAIL", "NOT_APPLICABLE", or None
        :rtype: Optional[str]
        """
        compliant_count, failed_count, inconclusive_count, not_applicable_count = counts
        total_evidence = len(self.evidence_items)

        logger.debug(
            f"Control {self.control_id} evidence summary: "
            f"{failed_count} FAILED, {compliant_count} COMPLIANT, "
            f"{not_applicable_count} NOT_APPLICABLE, {inconclusive_count} inconclusive out of {total_evidence} total"
        )

        # If ANY evidence failed, the control fails
        if failed_count > 0:
            logger.info(
                f"Control {self.control_id} FAILS: {failed_count} failed evidence item(s) out of {total_evidence}"
            )
            return "FAIL"

        # If we have compliant evidence and no failures, control passes
        if compliant_count > 0:
            if inconclusive_count > 0 or not_applicable_count > 0:
                logger.info(
                    f"Control {self.control_id} PASSES: {compliant_count} compliant, "
                    f"{not_applicable_count} not applicable, {inconclusive_count} inconclusive (no failures)"
                )
            else:
                logger.info(f"Control {self.control_id} PASSES: All {compliant_count} evidence items compliant")
            return "PASS"

        # If all evidence is not applicable, return NOT_APPLICABLE status
        if not_applicable_count > 0 and inconclusive_count == 0:
            logger.info(
                f"Control {self.control_id}: All {not_applicable_count} evidence item(s) marked NOT_APPLICABLE. "
                "Control will be marked as Not Applicable."
            )
            return "NOT_APPLICABLE"

        # If all evidence is inconclusive or mix of not applicable and inconclusive
        self._log_inconclusive_status(not_applicable_count, inconclusive_count, total_evidence)
        return None

    def _aggregate_evidence_compliance(self) -> Optional[str]:
        """
        Aggregate evidence complianceCheck fields to determine overall control compliance.

        AWS Audit Manager evidence items contain a complianceCheck field with values that vary by source.
        All values are normalized before aggregation:

        Success values (normalized to "COMPLIANT"):
        - "COMPLIANT" (AWS Config)
        - "PASS" (AWS Security Hub)

        Failure values (normalized to "FAILED"):
        - "NON_COMPLIANT" / "Non-compliant" (AWS Config)
        - "FAILED" / "FAIL" / "Fail" (AWS Security Hub)

        Other values:
        - "NOT_APPLICABLE": Evidence is not applicable to this control
        - null/None: No compliance check available for this evidence

        Evidence can have compliance checks in TWO locations:
        1. Root level: evidence["complianceCheck"]
        2. Resource level: evidence["resourcesIncluded"][*]["complianceCheck"]

        This method checks BOTH locations to ensure accurate compliance determination.

        Aggregation Logic (after normalization):
        1. If ANY evidence shows "FAILED" (any failure value) → Control FAILS
        2. If ALL evidence shows "COMPLIANT" (any success value) → Control PASSES
        3. NOT_APPLICABLE evidence is tracked separately and doesn't affect compliance
        4. If NO compliance checks available (all null/NOT_APPLICABLE) → INCONCLUSIVE
        5. If mixed (some COMPLIANT, some null, no FAILED) → PASS with warning

        :return: "PASS", "FAIL", or None (if inconclusive/no evidence)
        :rtype: Optional[str]
        """
        if not self.evidence_items:
            logger.debug(f"Control {self.control_id}: No evidence items available for aggregation")
            return None

        # Use enhanced analyzer if enabled
        if self.use_enhanced_analyzer:
            logger.debug(f"Control {self.control_id}: Using enhanced ControlComplianceAnalyzer")
            return self._aggregate_evidence_with_analyzer()

        # Count evidence by status
        counts = self._count_evidence_by_status()

        # Determine compliance based on counts
        return self._determine_compliance_status(counts)

    def _aggregate_evidence_with_analyzer(self) -> Optional[str]:
        """
        Use enhanced ControlComplianceAnalyzer to determine control compliance.

        This method leverages the ControlComplianceAnalyzer for more sophisticated
        evidence analysis, providing compliance scores and confidence levels.

        :return: "PASS", "FAIL", "NOT_APPLICABLE", or None
        :rtype: Optional[str]
        """
        analyzer = ControlComplianceAnalyzer(control_id=self.control_id)

        # Add each evidence item to the analyzer
        for evidence in self.evidence_items:
            analyzer.add_evidence_insight(evidence)

        # Get the compliance determination
        status, details = analyzer.determine_control_status()

        # Store enhanced analysis results
        self.compliance_score = analyzer.get_compliance_score()
        self.confidence_level = analyzer.get_confidence_level()
        self.compliance_details = details

        # Get comprehensive analysis
        analysis = analyzer.get_compliance_analysis()

        # Log detailed analysis
        logger.info(
            f"Control {self.control_id} analysis: "
            f"status={status}, score={self.compliance_score:.2f}, "
            f"confidence={self.confidence_level * 100:.0f}, "
            f"compliant={analysis.compliant_evidence_count}, "
            f"noncompliant={analysis.noncompliant_evidence_count}, "
            f"inconclusive={analysis.inconclusive_evidence_count}"
        )

        # Note: The ComplianceIntegration base class will automatically map this status
        # to the appropriate value based on the security plan's compliance settings.
        # For example:
        # - DoD/RMF: PASS → "Implemented", FAIL → "Planned"
        # - FedRAMP: PASS → "Fully Implemented", FAIL → "In Remediation"
        logger.debug(
            f"Control {self.control_id}: Result '{status}' will be mapped to compliance-specific status "
            "by ComplianceIntegration._get_implementation_status_from_result()"
        )

        # Map analyzer status to expected return values
        if status == "PASS":
            return "PASS"
        elif status == "FAIL":
            return "FAIL"
        elif status == "NOT_APPLICABLE":
            return "NOT_APPLICABLE"
        elif status == "INCONCLUSIVE":
            logger.debug(
                f"Control {self.control_id}: Inconclusive evidence. Details: {details.get('reason', 'Unknown')}"
            )
            return None
        else:  # NO_DATA
            logger.debug(f"Control {self.control_id}: No evidence data available for assessment")
            return None

    @property
    def compliance_result(self) -> Optional[str]:
        """
        Result of compliance check (PASS, FAIL, etc).

        IMPORTANT: AWS Audit Manager control 'status' (REVIEWED/UNDER_REVIEW/INACTIVE) is a
        WORKFLOW STATUS, not a compliance result. The actual compliance determination requires
        analyzing the individual evidence items' 'complianceCheck' fields.

        This property aggregates evidence to determine actual compliance:
        1. Collects all evidence items' complianceCheck fields (COMPLIANT/FAILED)
        2. Determines overall control compliance (if ANY evidence FAILED -> control FAILS)
        3. Returns PASS if all evidence is compliant, FAIL if any failures

        If no evidence is available, returns None. The control status should NOT be updated
        when evidence is unavailable - this signals the integration to skip the control.

        :return: "PASS", "FAIL", or None (if no evidence available)
        :rtype: Optional[str]
        """
        # Use cached result if available (including None)
        if self._aggregated_compliance_result is not None or hasattr(self, "_result_was_cached"):
            return self._aggregated_compliance_result

        # Aggregate evidence compliance checks
        result = self._aggregate_evidence_compliance()

        if result is None:
            # No evidence or no compliance checks available
            # Return None to signal that control should not be updated
            if len(self.evidence_items) > 0:
                logger.debug(
                    f"Control {self.control_id}: Evidence items collected ({len(self.evidence_items)}) but cannot determine "
                    f"compliance status (no valid complianceCheck values found). Control status will not be updated."
                )
            else:
                logger.debug(
                    f"Control {self.control_id}: No evidence items available for compliance determination. "
                    f"Control status will not be updated. Metadata evidence count: {self.evidence_count}"
                )

        # Cache the result (including None)
        self._aggregated_compliance_result = result
        self._result_was_cached = True
        return result

    @property
    def severity(self) -> Optional[str]:
        """
        Severity level of the compliance violation (if failed).

        Returns the highest severity from failing evidence items, or None if control passed.
        """
        if self.compliance_result != "FAIL":
            return None

        # Use highest_severity from evidence if available
        return self.highest_severity

    @property
    def remediation_urls(self) -> List[str]:
        """
        List of unique remediation URLs from failing evidence.

        Extracts remediation URLs from Security Hub findings in evidence attributes.
        """
        urls = set()
        for evidence in self.evidence_items:
            # Only process failing evidence
            if self._get_evidence_compliance(evidence) != "FAILED":
                continue

            attributes = evidence.get("attributes", {})
            remediation_info = self._parse_remediation_from_attributes(attributes)
            if remediation_info.get("url"):
                urls.add(remediation_info["url"])

        return sorted(urls)

    @property
    def remediation_info(self) -> List[Dict[str, str]]:
        """
        List of remediation information from failing evidence.

        Returns list of dicts with 'url' and 'text' keys.
        """
        remediation_list = []
        seen_urls = set()

        for evidence in self.evidence_items:
            # Only process failing evidence
            if self._get_evidence_compliance(evidence) != "FAILED":
                continue

            attributes = evidence.get("attributes", {})
            remediation_info = self._parse_remediation_from_attributes(attributes)

            # Only add if we have a URL and haven't seen it before
            url = remediation_info.get("url")
            if url and url not in seen_urls:
                remediation_list.append(remediation_info)
                seen_urls.add(url)

        return remediation_list

    @property
    def failing_resources(self) -> List[Dict[str, str]]:
        """
        List of resources that failed compliance checks.

        Returns list of dicts with 'arn', 'source', and 'severity' keys.
        """
        return self._extract_failing_resources(self.evidence_items)

    @property
    def underlying_checks(self) -> List[str]:
        """
        List of underlying Security Hub controls and Config rules that were evaluated.

        Returns list of control/rule names from failing evidence.
        """
        checks = set()

        for evidence in self.evidence_items:
            # Only process failing evidence
            if self._get_evidence_compliance(evidence) != "FAILED":
                continue

            data_source = evidence.get("dataSource", "")
            attributes = evidence.get("attributes", {})
            control_name = self._extract_control_name_from_attributes(attributes, data_source)

            if control_name:
                checks.add(f"{data_source}: {control_name}")

        return sorted(checks)

    @property
    def highest_severity(self) -> str:
        """
        Highest severity level from failing evidence items.

        Returns CRITICAL, HIGH, MEDIUM, LOW, or INFORMATIONAL.
        Defaults to MEDIUM if no severity information available.
        """
        severity_rankings = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFORMATIONAL": 1}

        highest = "MEDIUM"  # Default
        highest_rank = severity_rankings.get(highest, 0)

        for evidence in self.evidence_items:
            # Only process failing evidence
            if self._get_evidence_compliance(evidence) != "FAILED":
                continue

            attributes = evidence.get("attributes", {})
            severity_info = self._parse_severity_from_attributes(attributes)
            severity_label = severity_info.get("label", "").upper()

            if severity_label in severity_rankings:
                rank = severity_rankings[severity_label]
                if rank > highest_rank:
                    highest = severity_label
                    highest_rank = rank

        return highest

    @property
    def severity_score(self) -> int:
        """
        Highest normalized severity score (0-100) from failing evidence items.

        Returns 0-100 where CRITICAL=90, HIGH=70, MEDIUM=40, LOW=30, INFORMATIONAL=10.
        """
        highest_score = 0

        for evidence in self.evidence_items:
            # Only process failing evidence
            if self._get_evidence_compliance(evidence) != "FAILED":
                continue

            attributes = evidence.get("attributes", {})
            severity_info = self._parse_severity_from_attributes(attributes)
            normalized = severity_info.get("normalized", 0)

            if normalized > highest_score:
                highest_score = normalized

        return highest_score

    def _add_compliance_assessment_section(self, desc_parts: list) -> None:
        """Add compliance assessment section to description."""
        compliance_result = self.compliance_result
        compliant_count = sum(1 for e in self.evidence_items if self._get_evidence_compliance(e) == "COMPLIANT")
        failed_count = sum(1 for e in self.evidence_items if self._get_evidence_compliance(e) == "FAILED")

        desc_parts.append(f"{HTML_H4_OPEN}Compliance Assessment{HTML_H4_CLOSE}")
        desc_parts.append(HTML_P_OPEN)

        if compliance_result == "FAIL":
            desc_parts.append(
                f"<span style='color: red;'>{HTML_STRONG_OPEN}Result: FAILED{HTML_STRONG_CLOSE}</span>{HTML_BR}"
            )
            desc_parts.append(
                f"This control has {HTML_STRONG_OPEN}{failed_count} failed evidence item(s){HTML_STRONG_CLOSE} "
                f"out of {len(self.evidence_items)} total.{HTML_BR}"
            )
            if compliant_count > 0:
                desc_parts.append(f"{compliant_count} evidence item(s) are compliant. ")
        elif compliance_result == "PASS":
            desc_parts.append(
                f"<span style='color: green;'>{HTML_STRONG_OPEN}Result: PASSED{HTML_STRONG_CLOSE}</span>{HTML_BR}"
            )
            desc_parts.append(f"All {compliant_count} evidence item(s) with compliance checks are compliant.")
        else:
            desc_parts.append(f"{HTML_STRONG_OPEN}Result: INCONCLUSIVE{HTML_STRONG_CLOSE}{HTML_BR}")
            desc_parts.append("Evidence collected but compliance status could not be determined.")

        desc_parts.append(HTML_P_CLOSE)

    def _add_remediation_section(self, desc_parts: list) -> None:
        """Add remediation section to description."""
        if not (self.action_plan_title or self.action_plan_instructions):
            return

        desc_parts.append(f"{HTML_H4_OPEN}Remediation{HTML_H4_CLOSE}")
        if self.action_plan_title:
            desc_parts.append(
                f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Action Plan:{HTML_STRONG_CLOSE} {self.action_plan_title}"
                f"{HTML_P_CLOSE}"
            )
        if self.action_plan_instructions:
            desc_parts.append(
                f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Remediation Steps:{HTML_STRONG_CLOSE}{HTML_BR}"
                f"{self.action_plan_instructions}{HTML_P_CLOSE}"
            )

    def _add_comments_section(self, desc_parts: list) -> None:
        """Add assessor comments section to description."""
        if not self.control_comments:
            return

        desc_parts.append(f"{HTML_H4_OPEN}Assessor Comments{HTML_H4_CLOSE}")
        desc_parts.append(HTML_UL_OPEN)
        for comment in self.control_comments[:5]:  # Show up to 5 comments
            author = comment.get("authorName", "Unknown")
            posted_date = comment.get("postedDate", "")
            comment_body = comment.get("commentBody", "")
            desc_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{author}{HTML_STRONG_CLOSE} ({posted_date}): {comment_body} {HTML_LI_CLOSE}"
            )
        desc_parts.append(HTML_UL_CLOSE)

    def _add_failed_resources_section(self, desc_parts: list) -> None:
        """Add failed resources section with ARNs, sources, and severity."""
        failing_resources = self.failing_resources
        if not failing_resources:
            return

        desc_parts.append(f"{HTML_H4_OPEN}Failed Resources{HTML_H4_CLOSE}")
        desc_parts.append(f"{HTML_P_OPEN}The following resources failed compliance checks:{HTML_P_CLOSE}")

        # Create HTML table
        desc_parts.append('<table style="border-collapse: collapse; width: 100%;">')
        desc_parts.append(
            '<tr style="background-color: #f2f2f2;">'
            '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Resource ARN</th>'
            '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Source</th>'
            '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Severity</th>'
            "</tr>"
        )

        for resource in failing_resources:
            arn = resource.get("arn", "Unknown")
            source = resource.get("source", "Unknown")
            severity = resource.get("severity", "MEDIUM")

            # Color-code severity
            severity_colors = {
                "CRITICAL": "#d32f2f",
                "HIGH": "#f57c00",
                "MEDIUM": "#fbc02d",
                "LOW": "#7cb342",
                "INFORMATIONAL": "#1976d2",
            }
            severity_color = severity_colors.get(severity, "#757575")

            desc_parts.append(
                f'<tr><td style="border: 1px solid #ddd; padding: 8px;">{arn}</td>'
                f'<td style="border: 1px solid #ddd; padding: 8px;">{source}</td>'
                f'<td style="border: 1px solid #ddd; padding: 8px; color: {severity_color}; font-weight: bold;">{severity}</td></tr>'
            )

        desc_parts.append("</table>")

    def _transform_remediation_url(self, url: str) -> str:
        """
        Transform AWS documentation URLs from console format to proper user guide format.

        AWS Audit Manager provides remediation URLs in this format:
            https://docs.aws.amazon.com/console/securityhub/Config.1/remediation

        But these should be transformed to the actual documentation:
            https://docs.aws.amazon.com/securityhub/latest/userguide/awsconfig-controls.html#awsconfig-1

        :param str url: Original URL from AWS Audit Manager
        :return: Transformed URL to actual AWS documentation
        :rtype: str
        """
        import re

        if not url:
            return url

        # Pattern: https://docs.aws.amazon.com/console/securityhub/<ControlID>/remediation
        console_pattern = r"https://docs\.aws\.amazon\.com/console/securityhub/([^/]+)/remediation"
        match = re.match(console_pattern, url)

        if match:
            control_id = match.group(1)  # e.g., "Config.1" or "EC2.1"

            # Parse control prefix and number
            # Examples: "Config.1" -> ("Config", "1"), "EC2.15" -> ("EC2", "15")
            control_match = re.match(r"([A-Za-z0-9]+)\.(\d+)", control_id)

            if control_match:
                prefix = control_match.group(1).lower()  # "config" or "ec2"
                number = control_match.group(2)  # "1" or "15"

                # Map service prefixes to documentation pages
                # Security Hub organizes controls by AWS service
                service_doc_map = {
                    "config": "awsconfig",
                    "ec2": "ec2",
                    "iam": "iam",
                    "s3": "s3",
                    "rds": "rds",
                    "lambda": "lambda",
                    "cloudtrail": "cloudtrail",
                    "guardduty": "guardduty",
                    "securityhub": "securityhub",
                    "kms": "kms",
                    "elb": "elb",
                    "elbv2": "elbv2",
                    "cloudwatch": "cloudwatch",
                    "sns": "sns",
                    "sqs": "sqs",
                    "autoscaling": "autoscaling",
                    "codebuild": "codebuild",
                    "dms": "dms",
                    "dynamodb": "dynamodb",
                    "ecs": "ecs",
                    "efs": "efs",
                    "elasticache": "elasticache",
                    "elasticsearch": "elasticsearch",
                    "emr": "emr",
                    "redshift": "redshift",
                    "sagemaker": "sagemaker",
                    "secretsmanager": "secretsmanager",
                    "ssm": "ssm",
                    "waf": "waf",
                }

                doc_prefix = service_doc_map.get(prefix, prefix)

                # Construct the proper documentation URL
                transformed_url = (
                    f"https://docs.aws.amazon.com/securityhub/latest/userguide/"
                    f"{doc_prefix}-controls.html#{doc_prefix}-{number}"
                )

                logger.debug(f"Transformed remediation URL: {url} -> {transformed_url}")
                return transformed_url

        # If pattern doesn't match or control ID can't be parsed, return original URL
        logger.debug(f"Could not transform remediation URL (returning original): {url}")
        return url

    def _add_remediation_resources_section(self, desc_parts: list) -> None:
        """Add remediation resources section with links."""
        remediation_info = self.remediation_info
        if not remediation_info:
            return

        desc_parts.append(f"{HTML_H4_OPEN}Remediation Resources{HTML_H4_CLOSE}")
        desc_parts.append(HTML_UL_OPEN)

        for remediation in remediation_info:
            url = remediation.get("url", "")
            text = remediation.get("text", "See remediation guidance")

            if url:
                # Transform console URLs to proper documentation URLs
                transformed_url = self._transform_remediation_url(url)
                desc_parts.append(
                    f'{HTML_LI_OPEN}<a href="{transformed_url}" target="_blank">{text}</a>{HTML_LI_CLOSE}'
                )

        desc_parts.append(HTML_UL_CLOSE)

    def _add_underlying_checks_section(self, desc_parts: list) -> None:
        """Add underlying Security Hub controls and Config rules section."""
        underlying_checks = self.underlying_checks
        if not underlying_checks:
            return

        desc_parts.append(f"{HTML_H4_OPEN}Underlying Security Checks{HTML_H4_CLOSE}")
        desc_parts.append(f"{HTML_P_OPEN}The following AWS checks contributed to this assessment:{HTML_P_CLOSE}")
        desc_parts.append(HTML_UL_OPEN)

        for check in underlying_checks:
            desc_parts.append(f"{HTML_LI_OPEN}{check}{HTML_LI_CLOSE}")

        desc_parts.append(HTML_UL_CLOSE)

    @property
    def description(self) -> str:
        """Description of the compliance check using HTML formatting."""
        desc_parts = [
            f"<h3>AWS Audit Manager assessment for control {self.control_id}</h3>",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Control:{HTML_STRONG_CLOSE} {self._control_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self.framework_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Assessment:{HTML_STRONG_CLOSE} {self.assessment_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Evidence Count:{HTML_STRONG_CLOSE} {self.evidence_count}",
            HTML_P_CLOSE,
        ]

        if self.control_response:
            desc_parts.extend(
                [HTML_P_OPEN, f"{HTML_STRONG_OPEN}Response:{HTML_STRONG_CLOSE} {self.control_response}", HTML_P_CLOSE]
            )

        # Add compliance result analysis if evidence is available
        if self.evidence_items:
            self._add_compliance_assessment_section(desc_parts)

        # Add failed resources section (only if control failed)
        if self.compliance_result == "FAIL":
            self._add_failed_resources_section(desc_parts)
            self._add_underlying_checks_section(desc_parts)
            self._add_remediation_resources_section(desc_parts)

        # Add remediation guidance if available
        self._add_remediation_section(desc_parts)

        # Add testing information if available
        if self.testing_information:
            desc_parts.extend(
                [
                    f"{HTML_H4_OPEN}Testing Guidance{HTML_H4_CLOSE}",
                    f"{HTML_P_OPEN}{self.testing_information}{HTML_P_CLOSE}",
                ]
            )

        # Add comments from assessors
        self._add_comments_section(desc_parts)

        return "\n".join(desc_parts)

    @property
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CSF)."""
        framework_mappings = {
            "NIST SP 800-53 Revision 5": "NIST800-53R5",
            "NIST SP 800-53 Rev 5": "NIST800-53R5",
            "NIST 800-53 R5": "NIST800-53R5",
            "NIST 800-53 Revision 5": "NIST800-53R5",
            "SOC2": "SOC2",
            "PCI DSS": "PCI DSS",
            "HIPAA": "HIPAA",
            "GDPR": "GDPR",
        }
        if not self.framework_name:
            return "NIST800-53R5"
        for key, value in framework_mappings.items():
            if key.lower() in self.framework_name.lower():
                return value
        # Return framework name directly for custom frameworks
        # Check framework_type first (STANDARD vs CUSTOM)
        if self.framework_type == "CUSTOM":
            return self.framework_name
        # For unknown standard frameworks, return the name as-is
        return self.framework_name

    def _format_control_parts(self, prefix: str, base_num: str, enhancement: Optional[str] = None) -> str:
        """
        Format control ID parts into standard RegScale format.

        :param str prefix: Control prefix (e.g., AC, SI)
        :param str base_num: Base number (e.g., 2, 3)
        :param Optional[str] enhancement: Enhancement number (e.g., 1, 4)
        :return: Formatted control ID
        :rtype: str
        """
        # Remove leading zeros
        base = str(int(base_num))
        if enhancement:
            enh = str(int(enhancement))
            return f"{prefix}-{base}({enh})"
        return f"{prefix}-{base}"

    def _try_parse_dot_notation(self, control_id: str) -> Optional[str]:
        """
        Try to parse dot notation format: AC.2.1 or AC.2.

        :param str control_id: Control ID to parse
        :return: Normalized control ID or None
        :rtype: Optional[str]
        """
        import re

        dot_pattern = r"^([A-Z]{2,3})\.(\d+)(?:\.(\d+))?$"
        match = re.match(dot_pattern, control_id)
        if match:
            return self._format_control_parts(match.group(1), match.group(2), match.group(3))
        return None

    def _try_parse_standard_format(self, control_id: str) -> Optional[str]:
        """
        Try to parse standard format: AC-2(1), AC-2 (1), AC-2-1, AC-2.1.

        :param str control_id: Control ID to parse
        :return: Normalized control ID or None
        :rtype: Optional[str]
        """
        import re

        pattern = r"^([A-Z]{2,3})-(\d+)(?:[\s\-\.](\d+)|\s?\((\d+)\))?$"
        match = re.match(pattern, control_id)
        if match:
            enhancement = match.group(3) or match.group(4)
            return self._format_control_parts(match.group(1), match.group(2), enhancement)
        return None

    def _try_parse_hyphen_split(self, control_id: str) -> Optional[str]:
        """
        Try to parse by splitting on hyphens.

        :param str control_id: Control ID to parse
        :return: Normalized control ID or None
        :rtype: Optional[str]
        """
        if "-" not in control_id:
            return None

        parts = control_id.split("-")
        if len(parts) < 2:
            return None

        try:
            enhancement = parts[2] if len(parts) > 2 else None
            return self._format_control_parts(parts[0], parts[1], enhancement)
        except (ValueError, IndexError):
            return None

    def _normalize_control_id(self, control_id: str) -> str:
        """
        Normalize control ID to remove leading zeros and standardize format to match RegScale.

        Handles various AWS Audit Manager formats:
        - AC-2, AC-02
        - AC-2(1), AC-02(04)
        - AC-2 (1), AC-02 (04)
        - AC-2-1, AC-02-04
        - AC-2.1, AC-02.04, AC.2.1 (dot notation)

        Returns format: AC-2 or AC-2(1) to match RegScale control IDs

        :param str control_id: Raw control ID
        :return: Normalized control ID in RegScale format
        :rtype: str
        """
        if not control_id:
            return ""

        control_id = control_id.strip().upper()

        # Try parsing strategies in order
        result = self._try_parse_dot_notation(control_id)
        if result:
            return result

        result = self._try_parse_standard_format(control_id)
        if result:
            return result

        result = self._try_parse_hyphen_split(control_id)
        if result:
            return result

        logger.warning(f"Could not parse control ID format: '{control_id}'")
        return control_id


@dataclass
class EvidenceCollectionConfig:
    """Configuration for evidence collection from AWS Audit Manager."""

    collect_evidence: bool = False
    evidence_control_ids: Optional[List[str]] = None
    evidence_frequency: int = 30
    max_evidence_per_control: Optional[int] = (
        None  # BUGFIX: Changed from 100 to None (unlimited) to collect all evidence
    )


class AWSAuditManagerCompliance(ComplianceIntegration):
    """Process AWS Audit Manager assessments and create compliance records in RegScale."""

    def __init__(
        self,
        plan_id: int,
        region: str = "us-east-1",
        framework: str = "NIST800-53R5",
        assessment_id: Optional[str] = None,
        create_issues: bool = True,
        update_control_status: bool = True,
        create_poams: bool = False,
        parent_module: str = "securityplans",
        evidence_config: Optional[EvidenceCollectionConfig] = None,
        force_refresh: bool = False,
        use_assessment_evidence_folders: bool = True,
        use_enhanced_analyzer: bool = False,
        **kwargs,
    ):
        """
        Initialize AWS Audit Manager compliance integration.

        :param int plan_id: RegScale plan ID
        :param str region: AWS region
        :param str framework: Compliance framework
        :param Optional[str] assessment_id: Specific assessment ID to sync
        :param bool create_issues: Whether to create issues for failed compliance
        :param bool update_control_status: Whether to update control implementation status
        :param bool create_poams: Whether to mark issues as POAMs
        :param str parent_module: RegScale parent module
        :param Optional[EvidenceCollectionConfig] evidence_config: Evidence collection configuration
        :param bool force_refresh: Force refresh of compliance data by bypassing cache
        :param bool use_enhanced_analyzer: Use enhanced ControlComplianceAnalyzer for evidence analysis
        :param bool use_assessment_evidence_folders: Use GetEvidenceFoldersByAssessment API for faster
                                                       evidence collection (default: False, uses per-control API)
        :param kwargs: Additional parameters including AWS credentials (profile, aws_access_key_id,
                       aws_secret_access_key, aws_session_token)
        """
        super().__init__(
            plan_id=plan_id,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            parent_module=parent_module,
            **kwargs,
        )

        self.region = region
        self.assessment_id = assessment_id
        self.title = "AWS Audit Manager"
        self.custom_framework_name = kwargs.get("custom_framework_name")
        self.use_enhanced_analyzer = use_enhanced_analyzer

        # Evidence collection parameters - support both evidence_config object and individual kwargs
        if evidence_config:
            # Use provided evidence_config object
            self.evidence_config = evidence_config
            self.collect_evidence = evidence_config.collect_evidence
            self.evidence_control_ids = evidence_config.evidence_control_ids
            self.evidence_frequency = evidence_config.evidence_frequency
            self.max_evidence_per_control = (
                evidence_config.max_evidence_per_control
            )  # BUGFIX: Removed limit to collect all evidence
        else:
            # Build evidence_config from kwargs (for CLI compatibility)
            collect_evidence = kwargs.get("collect_evidence", False)
            evidence_control_ids = kwargs.get("evidence_control_ids")
            evidence_frequency = kwargs.get("evidence_frequency", 30)
            max_evidence_per_control = kwargs.get(
                "max_evidence_per_control", None
            )  # BUGFIX: Changed default from 100 to None (unlimited)

            self.evidence_config = EvidenceCollectionConfig(
                collect_evidence=collect_evidence,
                evidence_control_ids=evidence_control_ids,
                evidence_frequency=evidence_frequency,
                max_evidence_per_control=max_evidence_per_control,
            )
            self.collect_evidence = collect_evidence
            self.evidence_control_ids = evidence_control_ids
            self.evidence_frequency = evidence_frequency
            self.max_evidence_per_control = max_evidence_per_control  # BUGFIX: Removed limit to collect all evidence

        # Cache control
        self.force_refresh = force_refresh

        # Evidence collection method
        self.use_assessment_evidence_folders = use_assessment_evidence_folders

        # Pre-collected evidence storage (populated before sync when using assessment folders)
        # Maps control_id (lowercase) -> List[evidence_items]
        self._evidence_by_control: Dict[str, List[Dict[str, Any]]] = {}

        # Extract AWS credentials from kwargs
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        # INFO-level logging for credential resolution
        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS Audit Manager client with explicit credentials")
            self.session = boto3.Session(
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS Audit Manager client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=region)

        try:
            self.client = self.session.client("auditmanager")
            logger.info("Successfully created AWS Audit Manager client")
        except Exception as e:
            logger.error(f"Failed to create AWS Audit Manager client: {e}")
            raise

    def get_finding_identifier(self, finding) -> str:
        """
        Override parent method to ensure unique issue per control per resource.

        For AWS compliance, we want one issue per failed control per AWS resource.
        The external_id already includes resource_id, so we use it directly to ensure uniqueness.

        :param finding: IntegrationFinding object
        :return: Unique identifier for the finding
        :rtype: str
        """
        # Use the full external_id which includes control_id and resource_id
        # Format: "aws audit manager-{control_id}-{resource_id}"
        prefix = f"{self.plan_id}:{self.hash_string(finding.external_id)}"
        return prefix[:450]

    def _is_cache_valid(self) -> bool:
        """
        Check if the cache file exists and is within the TTL.

        :return: True if cache is valid, False otherwise
        :rtype: bool
        """
        if not os.path.exists(AUDIT_MANAGER_CACHE_FILE):
            logger.debug("Cache file does not exist")
            return False

        file_age = time.time() - os.path.getmtime(AUDIT_MANAGER_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS

        if is_valid:
            hours_old = file_age / 3600
            logger.info(f"Using cached Audit Manager data (age: {hours_old:.1f} hours)")
        else:
            hours_old = file_age / 3600
            logger.debug(f"Cache expired (age: {hours_old:.1f} hours, TTL: {CACHE_TTL_SECONDS / 3600} hours)")

        return is_valid

    def _load_cached_data(self) -> List[Dict[str, Any]]:
        """
        Load compliance data from cache file.

        :return: List of raw compliance data from cache
        :rtype: List[Dict[str, Any]]
        """
        try:
            with open(AUDIT_MANAGER_CACHE_FILE, encoding="utf-8") as file:
                cached_data = json.load(file)
                logger.info(f"Loaded {len(cached_data)} compliance items from cache")
                return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file: {e}. Fetching fresh data.")
            return []

    def _save_to_cache(self, compliance_data: List[Dict[str, Any]]) -> None:
        """
        Save compliance data to cache file.

        :param List[Dict[str, Any]] compliance_data: Data to cache
        :return: None
        :rtype: None
        """
        try:
            # Ensure the artifacts directory exists
            os.makedirs(os.path.dirname(AUDIT_MANAGER_CACHE_FILE), exist_ok=True)

            with open(AUDIT_MANAGER_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(compliance_data, file, indent=2, default=str)

            logger.info(f"Cached {len(compliance_data)} compliance items to {AUDIT_MANAGER_CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Error writing to cache file: {e}")

    def _collect_evidence_for_control(
        self, assessment_id: str, control_set_id: str, control: Dict[str, Any], assessment: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Collect evidence for a single control if enabled.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param Dict[str, Any] control: Control data
        :param Dict[str, Any] assessment: Assessment data
        :return: List of evidence items or None if not collected
        :rtype: Optional[List[Dict[str, Any]]]
        """
        control_id_raw = control.get("id")
        control_evidence_count = control.get("evidenceCount", 0)

        # Create a temporary compliance item to get normalized control ID
        temp_item = AWSAuditManagerComplianceItem(assessment, control)
        control_id_normalized = temp_item.control_id

        # Check if we should collect evidence for this control
        if not self._should_collect_control_evidence(control_id_normalized):
            logger.debug(
                f"Skipping evidence collection for control {control_id_normalized} "
                f"(evidenceCount: {control_evidence_count})"
            )
            return None

        # Log INFO level for controls with evidence to show progress
        if control_evidence_count > 0:
            logger.info(
                f"Collecting evidence for control {control_id_normalized} "
                f"({control_evidence_count} evidence items available)..."
            )
        else:
            logger.debug(
                f"Fetching evidence inline for control {control_id_normalized} (evidenceCount: {control_evidence_count})"
            )

        # Fetch evidence for this control
        evidence_items = self._get_control_evidence(
            assessment_id=assessment_id, control_set_id=control_set_id, control_id=control_id_raw
        )

        if evidence_items:
            logger.info(
                f"Successfully collected {len(evidence_items)} evidence items for control {control_id_normalized}"
            )
        else:
            logger.debug(f"No evidence items retrieved for control {control_id_normalized}")

        return evidence_items

    def _process_assessment_controls(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a single assessment and extract all control data.

        If collect_evidence is True, fetches evidence inline for each control to enable
        compliance determination based on evidence analysis.

        :param Dict[str, Any] assessment: Assessment data
        :return: List of control data for this assessment (with optional evidence_items)
        :rtype: List[Dict[str, Any]]
        """
        compliance_data = []
        control_sets = assessment.get("framework", {}).get("controlSets", [])
        logger.debug(f"Found {len(control_sets)} control sets in assessment")

        # Extract assessment ID for evidence collection
        assessment_id = assessment.get("arn", "").split("/")[-1]

        # Calculate total controls for progress tracking
        total_controls = sum(len(cs.get("controls", [])) for cs in control_sets)
        logger.info(f"Processing {total_controls} controls across {len(control_sets)} control sets...")

        # Create progress bar for control processing
        progress = create_progress_object()
        with progress:
            task = progress.add_task(
                f"Processing controls for assessment '{assessment.get('name', 'Unknown')}'", total=total_controls
            )

            for control_set in control_sets:
                control_set_id = control_set.get("id")
                controls = control_set.get("controls", [])
                logger.debug(f"Found {len(controls)} controls in control set")

                for control in controls:
                    control_data = {"assessment": assessment, "control": control}

                    # If evidence collection is enabled, fetch evidence inline for compliance determination
                    if self.collect_evidence:
                        evidence_items = self._collect_evidence_for_control(
                            assessment_id, control_set_id, control, assessment
                        )
                        if evidence_items:
                            control_data["evidence_items"] = evidence_items

                    compliance_data.append(control_data)
                    progress.update(task, advance=1)

        logger.info(f"Finished processing {len(compliance_data)} controls for assessment")
        return compliance_data

    def _should_process_assessment(self, assessment: Dict[str, Any]) -> bool:
        """
        Check if assessment should be processed based on framework match.

        For custom frameworks (--framework Custom), matches against the assessment name
        using the custom_framework_name parameter.

        :param Dict[str, Any] assessment: Assessment data
        :return: True if assessment should be processed
        :rtype: bool
        """
        if not assessment:
            return False

        assessment_name = assessment.get("name", "Unknown")

        # Special handling for custom frameworks - match by framework name
        if self.framework.upper() == "CUSTOM":
            if not self.custom_framework_name:
                logger.warning(
                    f"Skipping assessment '{assessment_name}' - framework is set to 'CUSTOM' "
                    "but no custom_framework_name provided. Use --custom-framework-name to specify."
                )
                return False

            # Check the framework metadata for custom framework name
            framework = assessment.get("framework", {})
            framework_metadata = framework.get("metadata", {})
            framework_name = framework_metadata.get("name", "")

            # Debug logging to understand the structure
            logger.debug(f"Assessment '{assessment_name}' framework metadata: {framework_metadata}")

            # Normalize both names for comparison
            custom_normalized = self.custom_framework_name.lower().replace(" ", "").replace("-", "").replace("_", "")
            framework_normalized = framework_name.lower().replace(" ", "").replace("-", "").replace("_", "")

            # Match against the framework name (not assessment name)
            if (
                custom_normalized == framework_normalized
                or custom_normalized in framework_normalized
                or framework_normalized in custom_normalized
            ):
                logger.info(
                    f"Processing assessment '{assessment_name}' - uses custom framework '{framework_name}' matching '{self.custom_framework_name}'"
                )
                return True

            logger.info(
                f"Skipping assessment '{assessment_name}' - framework '{framework_name}' does not match custom framework name '{self.custom_framework_name}'"
            )
            return False

        # For standard frameworks, match by framework type
        assessment_framework = self._get_assessment_framework(assessment)
        if not self._matches_framework(assessment_framework):
            logger.info(
                f"Skipping assessment '{assessment_name}' - framework '{assessment_framework}' "
                f"does not match target framework '{self.framework}'"
            )
            return False

        return True

    def _fetch_fresh_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh compliance data from AWS Audit Manager.

        :return: List of raw compliance data
        :rtype: List[Dict[str, Any]]
        """
        logger.info("Fetching compliance data from AWS Audit Manager...")
        compliance_data = []

        assessments = (
            [self._get_assessment_details(self.assessment_id)] if self.assessment_id else self._list_all_assessments()
        )

        for assessment in assessments:
            if not self._should_process_assessment(assessment):
                continue

            assessment_id = assessment.get("arn", "")
            logger.info(f"Processing assessment: {assessment.get('name', assessment_id)}")
            compliance_data.extend(self._process_assessment_controls(assessment))

        logger.info(f"Fetched {len(compliance_data)} compliance items from AWS Audit Manager")
        return compliance_data

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch raw compliance data from AWS Audit Manager.

        Uses cached data if available and not expired (4-hour TTL), unless force_refresh is True.
        Filters assessments to only include those matching the specified framework.

        :return: List of raw compliance data (assessment + control combinations)
        :rtype: List[Dict[str, Any]]
        """
        # Check if we should use cached data
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return self._filter_by_framework(cached_data)

        # Force refresh requested or no valid cache, fetch fresh data from AWS
        if self.force_refresh:
            logger.info("Force refresh requested, bypassing cache and fetching fresh data from AWS Audit Manager...")

        try:
            compliance_data = self._fetch_fresh_compliance_data()
            self._save_to_cache(compliance_data)
            return compliance_data
        except ClientError as e:
            logger.error(f"Error fetching compliance data from AWS Audit Manager: {e}")
            return []

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        """
        Create a ComplianceItem from raw compliance data.

        If evidence was pre-collected (via _collect_evidence_before_sync), it will be retrieved
        from _evidence_by_control storage and included in the compliance item for proper
        pass/fail determination.

        :param Dict[str, Any] raw_data: Raw compliance data (assessment + control + optional evidence)
        :return: ComplianceItem instance
        :rtype: ComplianceItem
        """
        assessment = raw_data.get("assessment", {})
        control = raw_data.get("control", {})
        evidence_items = raw_data.get("evidence_items", [])

        # If no evidence in raw_data, check if we have pre-collected evidence
        if not evidence_items and self._evidence_by_control:
            # Extract control ID from control
            temp_item = AWSAuditManagerComplianceItem(
                assessment, control, [], use_enhanced_analyzer=self.use_enhanced_analyzer
            )
            control_id = temp_item.control_id.lower()

            # Look up pre-collected evidence
            evidence_items = self._evidence_by_control.get(control_id, [])
            if evidence_items:
                logger.debug(f"Using pre-collected evidence for control {control_id}: {len(evidence_items)} items")

        return AWSAuditManagerComplianceItem(
            assessment, control, evidence_items, use_enhanced_analyzer=self.use_enhanced_analyzer
        )

    def _list_all_assessments(self) -> List[Dict[str, Any]]:
        """
        List all active assessments.

        :return: List of assessment details
        :rtype: List[Dict[str, Any]]
        """
        assessments = []
        try:
            response = self.client.list_assessments()
            assessment_metadata_list = response.get("assessmentMetadata", [])

            for metadata in assessment_metadata_list:
                status = metadata.get("status", "")
                if status in ["ACTIVE", "COMPLETED"]:
                    assessment_id = metadata.get("id", "")
                    assessment = self._get_assessment_details(assessment_id)
                    if assessment:
                        assessments.append(assessment)

        except ClientError as e:
            logger.error(f"Error listing assessments: {e}")

        return assessments

    def _get_assessment_details(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full assessment details including controls and evidence.

        :param str assessment_id: Assessment ID
        :return: Assessment details or None
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = self.client.get_assessment(assessmentId=assessment_id)
            assessment = response.get("assessment", {})

            metadata = assessment.get("metadata", {})
            assessment_data = {
                "arn": assessment.get("arn", ""),
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "complianceType": metadata.get("complianceType", ""),
                "status": metadata.get("status", ""),
                "awsAccount": assessment.get("awsAccount", {}),
                "framework": assessment.get("framework", {}),
            }

            return assessment_data

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.error(f"Error getting assessment details for {assessment_id}: {e}")
            return None

    def _get_assessment_framework(self, assessment: Dict[str, Any]) -> str:
        """
        Extract framework name from assessment data.

        :param Dict[str, Any] assessment: Assessment data
        :return: Framework name
        :rtype: str
        """
        # For custom frameworks, we need to handle the case where the assessment
        # was created from a custom framework. In this case, we should match
        # based on the assessment name if the framework is CUSTOM
        if self.framework.upper() == "CUSTOM" and self.custom_framework_name:
            # Return the assessment name for custom framework matching
            # This allows matching against the assessment name pattern
            return assessment.get("name", "")

        framework_name = assessment.get("framework", {}).get("metadata", {}).get("name", "")
        compliance_type = assessment.get("complianceType", "")

        # Prefer compliance type if available, otherwise use framework name
        return compliance_type or framework_name

    def _normalize_framework_string(self, framework_string: str) -> str:
        """
        Normalize a framework string by removing spaces, hyphens, and underscores.

        :param str framework_string: The string to normalize
        :return: Normalized string
        :rtype: str
        """
        return framework_string.lower().replace(" ", "").replace("-", "").replace("_", "")

    def _check_custom_framework_match(self, assessment_framework: str) -> bool:
        """
        Check if an assessment framework matches a custom framework.

        :param str assessment_framework: Framework name from AWS assessment
        :return: True if framework matches custom target
        :rtype: bool
        """
        if not self.custom_framework_name:
            logger.warning(
                "Framework is set to 'CUSTOM' but no custom_framework_name provided. "
                "Use --custom-framework-name to specify the custom framework name."
            )
            return False

        custom_normalized = self._normalize_framework_string(self.custom_framework_name)
        actual_normalized = self._normalize_framework_string(assessment_framework)

        # Allow flexible matching for custom frameworks
        matches = (
            custom_normalized == actual_normalized
            or custom_normalized in actual_normalized
            or actual_normalized in custom_normalized
            or "customframework" in actual_normalized
        )

        if matches:
            logger.debug(f"Custom framework match: '{assessment_framework}' matches '{self.custom_framework_name}'")

        return matches

    def _check_framework_aliases(self, target: str, actual: str) -> bool:
        """
        Check if target and actual frameworks match using known aliases.

        :param str target: Normalized target framework
        :param str actual: Normalized actual framework
        :return: True if frameworks match via aliases
        :rtype: bool
        """
        framework_aliases = {
            "nist80053r5": ["nist", "nistsp80053", "nist80053", "80053"],
            "soc2": ["soc", "soc2typeii", "soc2type2"],
            "pcidss": ["pci", "pcidss3.2.1", "pcidss3.2"],
            "hipaa": ["hipaa", "hipaasecurityrule"],
            "gdpr": ["gdpr", "generaldataprotectionregulation"],
        }

        for key, aliases in framework_aliases.items():
            if target.startswith(key) or any(target.startswith(alias) for alias in aliases):
                if any(alias in actual for alias in aliases):
                    return True
        return False

    def _matches_framework(self, assessment_framework: str) -> bool:
        """
        Check if an assessment framework matches the target framework.

        Handles various naming conventions:
        - NIST 800-53: "NIST SP 800-53 Revision 5", "NIST800-53R5", "NIST 800-53 R5"
        - SOC 2: "SOC2", "SOC 2", "SOC 2 Type II"
        - PCI DSS: "PCI DSS", "PCI DSS 3.2.1"
        - HIPAA: "HIPAA", "HIPAA Security Rule"
        - GDPR: "GDPR", "General Data Protection Regulation"
        - CUSTOM: Matches against custom_framework_name parameter or assessment name patterns

        :param str assessment_framework: Framework name from AWS assessment (or assessment name for custom frameworks)
        :return: True if framework matches target
        :rtype: bool
        """
        if not assessment_framework:
            return False

        # Special handling for custom frameworks
        if self.framework.upper() == "CUSTOM":
            return self._check_custom_framework_match(assessment_framework)

        # Normalize both for comparison
        target = self._normalize_framework_string(self.framework)
        actual = self._normalize_framework_string(assessment_framework)

        # Direct match
        if target in actual or actual in target:
            return True

        # Check framework aliases
        return self._check_framework_aliases(target, actual)

    def _filter_by_framework(self, compliance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter compliance data to only include items from matching framework.

        :param List[Dict[str, Any]] compliance_data: Raw compliance data
        :return: Filtered compliance data matching the target framework
        :rtype: List[Dict[str, Any]]
        """
        filtered_data = []
        frameworks_seen = set()

        for item in compliance_data:
            assessment = item.get("assessment", {})
            assessment_framework = self._get_assessment_framework(assessment)
            frameworks_seen.add(assessment_framework)

            if self._matches_framework(assessment_framework):
                filtered_data.append(item)

        if filtered_data != compliance_data:
            logger.info(
                f"Filtered compliance data by framework: {len(compliance_data)} total items, "
                f"{len(filtered_data)} matching '{self.framework}'"
            )
            logger.debug(f"Frameworks found in cached data: {sorted(frameworks_seen)}")

        return filtered_data

    def _map_resource_type_to_asset_type(self, compliance_item: ComplianceItem) -> str:
        """
        Map AWS resource type to RegScale asset type.

        :param ComplianceItem compliance_item: Compliance item with resource information
        :return: Asset type string
        :rtype: str
        """
        return "AWS Account"

    def _map_severity(self, severity: Optional[str]) -> regscale_models.IssueSeverity:
        """
        Map AWS severity to RegScale severity.

        :param Optional[str] severity: Severity string from AWS
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

    def _should_collect_control_evidence(self, control_id_normalized: str) -> bool:
        """
        Check if evidence should be collected for a control.

        Note: AWS Audit Manager's evidenceCount field in control metadata is not always accurate.
        We attempt to fetch evidence for all controls (or filtered controls if specified) and
        let the API determine if evidence exists.

        :param str control_id_normalized: Normalized control ID
        :return: True if evidence should be collected
        :rtype: bool
        """
        # Filter by control IDs if specified
        if self.evidence_control_ids:
            if control_id_normalized not in self.evidence_control_ids:
                logger.debug(f"Skipping evidence collection for control {control_id_normalized} (not in filter list)")
                return False

        # Don't skip based on evidenceCount - AWS Audit Manager metadata may be inaccurate
        # The API call will return empty list if no evidence exists
        return True

    def _process_control_evidence(
        self,
        assessment_id: str,
        control_set_id: str,
        control: Dict[str, Any],
        assessment: Dict[str, Any],
        all_evidence_items: List[Dict[str, Any]],
        control_summary: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Process evidence collection for a single control.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param Dict[str, Any] control: Control data
        :param Dict[str, Any] assessment: Assessment data
        :param List[Dict[str, Any]] all_evidence_items: List to append evidence to
        :param Dict[str, Dict[str, Any]] control_summary: Summary dict to update
        :return: None
        :rtype: None
        """
        control_id_raw = control.get("id")
        control_name = control.get("name", "")
        control_evidence_count = control.get("evidenceCount", 0)

        # Extract and normalize control ID (e.g., AU-2, AC-3)
        compliance_item = AWSAuditManagerComplianceItem(assessment, control)
        control_id_normalized = compliance_item.control_id

        # Check if we should collect evidence for this control
        if not self._should_collect_control_evidence(control_id_normalized):
            return

        logger.debug(
            f"Collecting evidence for control: {control_id_normalized} (evidenceCount: {control_evidence_count})"
        )

        # Collect evidence for this control
        evidence_items = self._get_control_evidence(
            assessment_id=assessment_id, control_set_id=control_set_id, control_id=control_id_raw
        )

        if evidence_items:
            # Tag each evidence item with control information for traceability
            for item in evidence_items:
                item["_control_id"] = control_id_normalized
                item["_control_name"] = control_name

            all_evidence_items.extend(evidence_items)
            control_summary[control_id_normalized] = {
                "control_name": control_name,
                "evidence_count": len(evidence_items),
            }
            logger.debug(f"Collected {len(evidence_items)} evidence items for control {control_id_normalized}")

    def _collect_assessment_control_evidence(self, assessment: Dict[str, Any]) -> tuple:
        """
        Collect evidence for all controls in an assessment.

        :param Dict[str, Any] assessment: Assessment data
        :return: Tuple of (all_evidence_items, control_summary, controls_processed)
        :rtype: tuple
        """
        assessment_id = assessment.get("arn", "").split("/")[-1]
        all_evidence_items = []
        control_summary = {}
        controls_processed = 0

        # Get control sets from assessment framework
        control_sets = assessment.get("framework", {}).get("controlSets", [])

        for control_set in control_sets:
            control_set_id = control_set.get("id")
            controls = control_set.get("controls", [])

            for control in controls:
                self._process_control_evidence(
                    assessment_id=assessment_id,
                    control_set_id=control_set_id,
                    control=control,
                    assessment=assessment,
                    all_evidence_items=all_evidence_items,
                    control_summary=control_summary,
                )
                controls_processed += 1

        return all_evidence_items, control_summary, controls_processed

    def _get_all_evidence_folders_for_assessment(self, assessment_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get ALL evidence folders for an assessment using GetEvidenceFoldersByAssessment API.

        This is faster than iterating through controls individually because it retrieves
        all evidence folders in a single paginated operation. Evidence folders are grouped
        by control ID for easier processing.

        :param str assessment_id: Assessment ID
        :return: Dict mapping control_id -> list of evidence folders
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        evidence_folders_by_control = {}
        next_token = None

        logger.info(f"Fetching all evidence folders for assessment {assessment_id} using assessment-level API")

        try:
            while True:
                params = {"assessmentId": assessment_id, "maxResults": 1000}
                if next_token:
                    params["nextToken"] = next_token

                logger.debug(f"Calling get_evidence_folders_by_assessment (maxResults={params['maxResults']})")
                response = self.client.get_evidence_folders_by_assessment(**params)
                evidence_folders = response.get("evidenceFolders", [])

                # Group by control ID
                for folder in evidence_folders:
                    control_id = folder.get("controlId")
                    if control_id:
                        if control_id not in evidence_folders_by_control:
                            evidence_folders_by_control[control_id] = []
                        evidence_folders_by_control[control_id].append(folder)

                logger.debug(f"Retrieved {len(evidence_folders)} evidence folder(s) in this page")

                next_token = response.get("nextToken")
                if not next_token:
                    break

            total_folders = sum(len(folders) for folders in evidence_folders_by_control.values())
            logger.info(
                f"Found {total_folders} evidence folder(s) across {len(evidence_folders_by_control)} control(s)"
            )
            return evidence_folders_by_control

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"].get("Message", "")
            logger.error(
                f"Error fetching evidence folders by assessment {assessment_id}: {error_code} - {error_message}"
            )
            return {}

    def _collect_evidence_assessment_level(self, assessment: Dict[str, Any], assessment_id: str) -> tuple:
        """
        Collect evidence using assessment-level API (faster method).

        Uses GetEvidenceFoldersByAssessment to retrieve all evidence folders at once,
        then processes each control's evidence. This is much faster than iterating
        through controls individually.

        :param Dict[str, Any] assessment: Assessment data
        :param str assessment_id: Assessment ID
        :return: Tuple of (all_evidence_items, control_summary)
        :rtype: tuple
        """
        # Get ALL evidence folders at once
        evidence_folders_by_control = self._get_all_evidence_folders_for_assessment(assessment_id)

        if not evidence_folders_by_control:
            logger.warning(f"No evidence folders found for assessment {assessment_id}")
            return [], {}

        all_evidence_items = []
        control_summary = {}

        # Create progress bar for evidence collection
        from rich.progress import (
            Progress,
            SpinnerColumn,
            TextColumn,
            BarColumn,
            TaskProgressColumn,
            TimeRemainingColumn,
        )

        total_controls = len(evidence_folders_by_control)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(
                f"[cyan]Collecting evidence from {total_controls} control(s)...", total=total_controls
            )

            # Process each control that has evidence folders
            for control_id_raw, folders in evidence_folders_by_control.items():
                # Get control info from first folder
                control_set_id = folders[0].get("controlSetId")
                control_name = folders[0].get("controlName", control_id_raw)

                # Normalize control ID by creating a temporary compliance item
                # We need to build control data from the folder metadata
                control_data = {"id": control_id_raw, "name": control_name}
                temp_item = AWSAuditManagerComplianceItem(assessment, control_data)
                control_id_normalized = temp_item.control_id

                # Filter by evidence_control_ids if specified
                if self.evidence_control_ids and control_id_normalized not in self.evidence_control_ids:
                    logger.debug(f"Skipping control {control_id_normalized} (not in filter list)")
                    progress.advance(task)
                    continue

                logger.debug(
                    f"Collecting evidence for control {control_id_normalized} ({len(folders)} evidence folder(s))"
                )

                # Collect evidence from these folders
                evidence_items = self._process_evidence_folders(
                    assessment_id, control_set_id, control_id_raw, folders, control_name=control_id_normalized
                )

                if evidence_items:
                    # Tag each evidence item with control information
                    for item in evidence_items:
                        item["_control_id"] = control_id_normalized
                        item["_control_name"] = control_name

                    all_evidence_items.extend(evidence_items)
                    control_summary[control_id_normalized] = {
                        "control_name": control_name,
                        "evidence_count": len(evidence_items),
                    }
                    logger.debug(f"Collected {len(evidence_items)} evidence items for control {control_id_normalized}")

                progress.advance(task)

        return all_evidence_items, control_summary

    def _process_cached_evidence(self) -> tuple:
        """
        Process pre-collected cached evidence.

        :return: Tuple of (all_evidence_items, control_summary, controls_processed)
        :rtype: tuple
        """
        all_evidence_items = []
        control_summary = {}

        # Aggregate all evidence items from the cache
        for control_id, evidence_items in self._evidence_by_control.items():
            all_evidence_items.extend(evidence_items)

            # Extract control name from the first evidence item if available
            control_name = "Unknown Control"
            if evidence_items and len(evidence_items) > 0:
                first_item = evidence_items[0]
                if isinstance(first_item, dict):
                    control_name = first_item.get("_control_name", first_item.get("controlName", control_id))

            # Create control summary in the expected format
            control_summary[control_id] = {
                "control_name": control_name,
                "evidence_count": len(evidence_items),
            }

        controls_processed = len(control_summary)
        logger.info(f"Reusing cached evidence: {len(all_evidence_items)} items from {controls_processed} controls")

        return all_evidence_items, control_summary, controls_processed

    def collect_assessment_evidence(self, assessments: List[Dict[str, Any]]) -> None:
        """
        Collect evidence artifacts from AWS Audit Manager assessments.

        Collects evidence from yesterday's evidence folders (UTC timezone) to provide
        daily compliance evidence snapshots. If no evidence exists for yesterday for a
        control, that control is skipped.

        Supports two collection methods:
        1. Assessment-level: GetEvidenceFoldersByAssessment (faster, single API call)
        2. Control-level: GetEvidenceFoldersByAssessmentControl (current, per-control iteration)

        Aggregates all evidence across all controls in each assessment and creates
        a single consolidated JSONL file per assessment stored in the artifacts directory.
        Creates one RegScale Evidence record per assessment with the consolidated file attached.

        :param List[Dict[str, Any]] assessments: List of assessment data
        :return: None
        :rtype: None
        """
        if not self.collect_evidence:
            logger.debug("Evidence collection disabled, skipping")
            return

        collection_method = "assessment-level" if self.use_assessment_evidence_folders else "control-level"

        # Check if evidence was already collected during pre-sync
        if self._evidence_by_control:
            logger.info(f"Using pre-collected evidence from {len(self._evidence_by_control)} controls")
        else:
            logger.info(f"Starting evidence collection from AWS Audit Manager using {collection_method} API...")

        evidence_records_created = 0

        for assessment in assessments:
            assessment_name = assessment.get("name", "Unknown Assessment")
            assessment_id = assessment.get("arn", "").split("/")[-1]

            logger.info(f"Processing evidence for assessment: {assessment_name}")

            # Check if evidence was already collected during pre-sync
            if self._evidence_by_control:
                # Reuse pre-collected evidence instead of fetching again from AWS
                all_evidence_items, control_summary, controls_processed = self._process_cached_evidence()
            elif self.use_assessment_evidence_folders:
                # NEW: Fast method - get all evidence folders at once
                all_evidence_items, control_summary = self._collect_evidence_assessment_level(assessment, assessment_id)
                controls_processed = len(control_summary)
            else:
                # EXISTING: Per-control iteration method (backward compatible)
                all_evidence_items, control_summary, controls_processed = self._collect_assessment_control_evidence(
                    assessment
                )

            # Create consolidated evidence record if we collected any evidence
            if all_evidence_items:
                evidence_record = self._create_consolidated_evidence_record(
                    assessment=assessment,
                    assessment_name=assessment_name,
                    all_evidence_items=all_evidence_items,
                    control_summary=control_summary,
                    controls_processed=controls_processed,
                )

                if evidence_record:
                    evidence_records_created += 1
            else:
                logger.info(f"No evidence collected for assessment: {assessment_name}")

        logger.info(f"Evidence collection complete: {evidence_records_created} consolidated evidence record(s) created")

    def _get_evidence_folders(self, assessment_id: str, control_set_id: str, control_id: str) -> List[Dict[str, Any]]:
        """
        Get all evidence folders for a specific control.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str control_id: Control ID (AWS internal ID)
        :return: List of evidence folders
        :rtype: List[Dict[str, Any]]
        """
        logger.debug(
            f"Getting evidence folders for control: assessmentId={assessment_id}, "
            f"controlSetId={control_set_id}, controlId={control_id}"
        )

        try:
            folders_response = self.client.get_evidence_folders_by_assessment_control(
                assessmentId=assessment_id, controlSetId=control_set_id, controlId=control_id
            )

            evidence_folders = folders_response.get("evidenceFolders", [])
            logger.debug(f"Found {len(evidence_folders)} evidence folder(s) for control {control_id}")

            return evidence_folders

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"].get("Message", "")
            logger.error(f"Error fetching evidence folders for control {control_id}: {error_code} - {error_message}")
            raise

    def _parse_evidence_timestamp(self, time_str: Any) -> Optional[datetime]:
        """
        Parse evidence timestamp from various formats.

        :param Any time_str: Timestamp string or datetime object
        :return: Parsed datetime object or None if unparseable
        :rtype: Optional[datetime]
        """
        if not time_str:
            return None

        try:
            if isinstance(time_str, datetime):
                # If it's already a datetime object, ensure it's naive UTC
                if time_str.tzinfo:
                    # Convert to UTC and make naive
                    return time_str.astimezone(timezone.utc).replace(tzinfo=None)
                return time_str

            if not isinstance(time_str, str):
                return None

            # Handle ISO format with T separator
            if "T" in time_str:
                # Parse ISO format and convert to naive UTC
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                # If timezone-aware, convert to UTC and make naive
                if dt.tzinfo:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt

            # Handle format with space separator
            parts = time_str.split("-")
            if len(parts) > 3:  # Has timezone offset
                # Remove timezone suffix and parse as naive datetime
                time_without_tz = time_str.rsplit("-", 1)[0] if "+" not in time_str else time_str.rsplit("+", 1)[0]
                date_format = "%Y-%m-%d %H:%M:%S.%f" if "." in time_without_tz else "%Y-%m-%d %H:%M:%S"
                # Parse as naive datetime (already in UTC after removing timezone)
                return datetime.strptime(time_without_tz.strip(), date_format)

            # Simple date format
            date_format = "%Y-%m-%d %H:%M:%S.%f" if "." in time_str else "%Y-%m-%d %H:%M:%S"
            return datetime.strptime(time_str, date_format)

        except (ValueError, TypeError) as e:
            logger.debug(f"Error parsing timestamp '{time_str}': {e}")
            return None

    def _filter_evidence_by_date(
        self, evidence_items: List[Dict[str, Any]], yesterday_start: datetime, yesterday_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Filter evidence items to only include those from yesterday's date range.

        :param List[Dict[str, Any]] evidence_items: Evidence items to filter
        :param datetime yesterday_start: Start of yesterday's date range
        :param datetime yesterday_end: End of yesterday's date range
        :return: Filtered evidence items
        :rtype: List[Dict[str, Any]]
        """
        filtered_evidence = []

        for item in evidence_items:
            time_str = item.get("time")
            evidence_time = self._parse_evidence_timestamp(time_str)

            if not evidence_time:
                logger.debug(f"Skipping evidence item without parseable timestamp: {item.get('id', 'unknown')}")
                continue

            if yesterday_start <= evidence_time < yesterday_end:
                filtered_evidence.append(item)
            else:
                logger.debug(
                    f"Excluding evidence item {item.get('id', 'unknown')} with timestamp {time_str} "
                    f"(outside yesterday's range)"
                )

        return filtered_evidence

    def _collect_evidence_from_folder(
        self,
        assessment_id: str,
        control_set_id: str,
        evidence_folder_id: str,
        evidence_items: List[Dict[str, Any]],
    ) -> None:
        """
        Collect evidence from a single evidence folder with pagination.

        Filters evidence items to only include those from yesterday's date to prevent
        including evidence from the current day.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str evidence_folder_id: Evidence folder ID
        :param List[Dict[str, Any]] evidence_items: List to append evidence to
        :return: None
        :rtype: None
        """
        next_token = None
        max_results = 50  # API maximum per request

        # Calculate yesterday's date range in UTC
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        yesterday_start = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_end = yesterday_start + timedelta(days=1)

        logger.debug(
            f"Filtering evidence items for date range: {yesterday_start.isoformat()} to {yesterday_end.isoformat()} UTC"
        )

        while True:  # BUGFIX: Removed limit to collect all evidence
            # Build request parameters
            # Calculate maxResults: if no limit, use max_results; otherwise respect the limit
            if self.max_evidence_per_control is None:
                request_max_results = max_results
            else:
                request_max_results = min(max_results, self.max_evidence_per_control - len(evidence_items))

            params = {
                "assessmentId": assessment_id,
                "controlSetId": control_set_id,
                "evidenceFolderId": evidence_folder_id,
                "maxResults": request_max_results,
            }

            if next_token:
                params["nextToken"] = next_token

            logger.debug(
                f"Calling get_evidence_by_evidence_folder: "
                f"evidenceFolderId={evidence_folder_id}, maxResults={params['maxResults']}"
            )

            # Make API call
            response = self.client.get_evidence_by_evidence_folder(**params)

            # Get evidence items from the folder
            # Note: We don't filter by date here since the folder is already from the correct date
            page_evidence = response.get("evidence", [])

            # Add all evidence items from the folder (folder date filtering already applied)
            evidence_items.extend(page_evidence)

            logger.debug(
                f"Retrieved {len(page_evidence)} evidence item(s) from folder {evidence_folder_id} "
                f"(total so far: {len(evidence_items)})"
            )

            # Check if we've reached the limit (if one is set)
            if self.max_evidence_per_control is not None and len(evidence_items) >= self.max_evidence_per_control:
                logger.debug(f"Reached max evidence limit ({self.max_evidence_per_control}), stopping pagination")
                break

            # Check for more pages
            next_token = response.get("nextToken")
            if not next_token or not page_evidence:
                break

    def _process_evidence_folders(
        self,
        assessment_id: str,
        control_set_id: str,
        control_id: str,
        evidence_folders: List[Dict[str, Any]],
        control_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process yesterday's evidence folders for a control and collect evidence items.

        This method filters evidence folders to only process folders from yesterday (UTC timezone)
        to avoid collecting duplicate or stale evidence. If no evidence folders exist for yesterday,
        an info message is logged and an empty list is returned.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str control_id: Control ID (AWS internal ID)
        :param List[Dict[str, Any]] evidence_folders: List of evidence folders to filter
        :param Optional[str] control_name: Human-readable control name (e.g., AC-1, AU-2)
        :return: List of evidence items from yesterday's folders
        :rtype: List[Dict[str, Any]]
        """
        evidence_items = []
        display_control = control_name if control_name else control_id

        # Calculate yesterday's date in UTC (AWS Audit Manager uses UTC timestamps)
        yesterday = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.debug(f"Filtering evidence folders for date: {yesterday} (UTC) for control {display_control}")

        # Helper function to match folder date with yesterday's date
        def matches_yesterday(folder: Dict[str, Any]) -> bool:
            folder_date = folder.get("date")
            if not folder_date:
                return False

            # AWS returns datetime objects - convert to date string for comparison
            if isinstance(folder_date, datetime):
                folder_date_str = folder_date.strftime("%Y-%m-%d")
            else:
                # Handle string dates (defensive programming)
                folder_date_str = str(folder_date)

            return folder_date_str.startswith(yesterday)

        # Filter folders to only yesterday's date
        yesterdays_folders = [f for f in evidence_folders if matches_yesterday(f)]

        logger.info(
            f"Found {len(yesterdays_folders)} evidence folder(s) for {yesterday} "
            f"out of {len(evidence_folders)} total folder(s) for control {display_control}"
        )

        if not yesterdays_folders:
            logger.info(f"No evidence folders found for yesterday ({yesterday}) for control {display_control}")
            return evidence_items

        # Process yesterday's folders
        for folder in yesterdays_folders:
            # Check if we've reached the limit (if one is set)
            if self.max_evidence_per_control is not None and len(evidence_items) >= self.max_evidence_per_control:
                logger.debug(
                    f"Reached max evidence limit ({self.max_evidence_per_control}), "
                    f"stopping evidence collection for control {display_control}"
                )
                break

            evidence_folder_id = folder.get("id")
            folder_date = folder.get("date")
            folder_evidence_count = folder.get("evidenceResourcesIncludedCount", 0)

            logger.info(
                f"Processing evidence folder {evidence_folder_id} for control {display_control} "
                f"(date: {folder_date}, evidence count: {folder_evidence_count})"
            )

            self._collect_evidence_from_folder(assessment_id, control_set_id, evidence_folder_id, evidence_items)

        return evidence_items

    def _get_control_evidence(self, assessment_id: str, control_set_id: str, control_id: str) -> List[Dict[str, Any]]:
        """
        Get evidence items for a specific control from AWS Audit Manager.

        AWS Audit Manager organizes evidence in daily evidence folders within each control.
        This method retrieves all evidence folders for the control, filters for yesterday's
        folders (UTC timezone), then collects evidence from those folders up to
        max_evidence_per_control items.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str control_id: Control ID (AWS internal ID)
        :return: List of evidence items from yesterday's evidence folders
        :rtype: List[Dict[str, Any]]
        """
        evidence_items = []

        try:
            # Step 1: Get all evidence folders for this control
            evidence_folders = self._get_evidence_folders(assessment_id, control_set_id, control_id)

            if not evidence_folders:
                logger.debug(f"No evidence folders found for control {control_id}")
                return evidence_items

            # Step 2: Filter for yesterday's folders and collect evidence
            evidence_items = self._process_evidence_folders(assessment_id, control_set_id, control_id, evidence_folders)

            logger.debug(
                f"Retrieved {len(evidence_items)} evidence item(s) for control {control_id} "
                f"from {len(evidence_folders)} evidence folder(s)"
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"].get("Message", "")
            if error_code in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.warning(f"Cannot access evidence for control {control_id}: {error_code} - {error_message}")
            else:
                logger.error(f"Error retrieving evidence for control {control_id}: {error_code} - {error_message}")

        return evidence_items

    def _create_consolidated_evidence_record(
        self,
        assessment: Dict[str, Any],
        assessment_name: str,
        all_evidence_items: List[Dict[str, Any]],
        control_summary: Dict[str, Dict[str, Any]],
        controls_processed: int,
    ) -> Optional[Any]:
        """
        Create a RegScale Evidence record with consolidated evidence from all controls.

        Saves a consolidated JSONL file to the artifacts directory and attaches it to
        a single Evidence record per assessment.

        :param Dict[str, Any] assessment: Full assessment data from AWS Audit Manager
        :param str assessment_name: Assessment name
        :param List[Dict[str, Any]] all_evidence_items: All evidence items across controls
        :param Dict[str, Dict[str, Any]] control_summary: Summary of evidence per control
        :param int controls_processed: Number of controls processed
        :return: Created Evidence record or None
        :rtype: Optional[Any]
        """
        from datetime import datetime, timedelta

        from regscale.models.regscale_models.evidence import Evidence

        # Build evidence title and description
        scan_timestamp = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")
        title = f"AWS Audit Manager Evidence - {assessment_name} - {scan_timestamp}"

        # Analyze evidence and build description
        description, safe_assessment_name, file_name = self._build_evidence_description(
            assessment=assessment,
            assessment_name=assessment_name,
            all_evidence_items=all_evidence_items,
            control_summary=control_summary,
            controls_processed=controls_processed,
            scan_date=scan_timestamp,
        )

        # Calculate due date
        due_date = (datetime.now() + timedelta(days=self.evidence_frequency)).isoformat()

        try:
            # Create Evidence record
            evidence = Evidence(
                title=title,
                description=description,
                status="Collected",
                updateFrequency=self.evidence_frequency,
                dueDate=due_date,
            )

            created_evidence = evidence.create()
            if not created_evidence or not created_evidence.id:
                logger.error("Failed to create evidence record")
                return None

            logger.info(f"Created evidence record {created_evidence.id}: {title}")

            # Save and upload consolidated evidence file
            self._upload_consolidated_evidence(
                created_evidence_id=created_evidence.id,
                safe_assessment_name=safe_assessment_name,
                scan_date=scan_timestamp,
                file_name=file_name,
                all_evidence_items=all_evidence_items,
            )

            # Link evidence to SSP
            ssp_linked = self._link_evidence_to_ssp(created_evidence.id)

            # Link evidence to control implementations
            controls_linked = self._link_evidence_to_control_implementations(created_evidence.id, control_summary)

            # Log summary of evidence mapping per policy
            if ssp_linked:
                logger.info(
                    f"Successfully mapped 1 evidence to {controls_linked} controls "
                    f"(Evidence ID: {created_evidence.id}, SSP ID: {self.plan_id})"
                )
            else:
                logger.warning(
                    f"Evidence record (ID: {created_evidence.id}) created but could not be linked to SSP. "
                    f"Linked to {controls_linked} control(s)"
                )

            return created_evidence

        except Exception as ex:
            logger.error(
                f"Failed to create consolidated evidence for assessment {assessment_name}: {ex}", exc_info=True
            )
            return None

    def _get_compliance_check_from_resources(self, resources_included: List[Dict[str, Any]]) -> Optional[str]:
        """
        Determine compliance check status from resource-level checks.

        :param List[Dict[str, Any]] resources_included: List of resources with complianceCheck fields
        :return: Aggregated compliance check status or None
        :rtype: Optional[str]
        """
        if not resources_included:
            return None

        resource_checks = [r.get("complianceCheck") for r in resources_included]
        if "FAILED" in resource_checks:
            return "FAILED"
        if any(check == "COMPLIANT" for check in resource_checks):
            return "COMPLIANT"
        if any(check == "NOT_APPLICABLE" for check in resource_checks):
            return "NOT_APPLICABLE"
        return None

    def _track_failed_control(
        self, control_id: Optional[str], failed_controls: set, failed_by_control: Dict[str, int]
    ) -> None:
        """
        Track a failed control for reporting.

        :param Optional[str] control_id: Control ID to track
        :param set failed_controls: Set of failed control IDs
        :param Dict[str, int] failed_by_control: Dictionary tracking failure count per control
        :return: None
        :rtype: None
        """
        if control_id:
            failed_controls.add(control_id)
            failed_by_control[control_id] = failed_by_control.get(control_id, 0) + 1

    def _count_compliance_status(
        self,
        compliance_check: Optional[str],
        evidence: Dict[str, Any],
        compliant_count: int,
        failed_count: int,
        not_applicable_count: int,
        inconclusive_count: int,
        failed_controls: set,
        failed_by_control: Dict[str, int],
    ) -> tuple:
        """
        Count compliance status and update tracking collections.

        :param Optional[str] compliance_check: Compliance check status
        :param Dict[str, Any] evidence: Evidence item with control_id
        :param int compliant_count: Current compliant count
        :param int failed_count: Current failed count
        :param int not_applicable_count: Current not applicable count
        :param int inconclusive_count: Current inconclusive count
        :param set failed_controls: Set of failed control IDs
        :param Dict[str, int] failed_by_control: Dictionary tracking failure count per control
        :return: Tuple of updated counts
        :rtype: tuple
        """
        if compliance_check == "FAILED":
            failed_count += 1
            control_id = evidence.get("_control_id")
            self._track_failed_control(control_id, failed_controls, failed_by_control)
        elif compliance_check == "COMPLIANT":
            compliant_count += 1
        elif compliance_check == "NOT_APPLICABLE":
            not_applicable_count += 1
        else:
            inconclusive_count += 1

        return compliant_count, failed_count, not_applicable_count, inconclusive_count

    def _analyze_compliance_results(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze compliance results from evidence items to determine pass/fail statistics.

        Checks both root-level and resource-level complianceCheck fields (same logic
        as _aggregate_evidence_compliance).

        :param List[Dict[str, Any]] evidence_items: Evidence items to analyze
        :return: Dictionary with compliance statistics
        :rtype: Dict[str, Any]
        """
        compliant_count = 0
        failed_count = 0
        inconclusive_count = 0
        not_applicable_count = 0
        failed_controls = set()
        failed_by_control = {}

        for evidence in evidence_items:
            # Check root-level complianceCheck first
            compliance_check = evidence.get("complianceCheck")

            # If no root-level check, look in resourcesIncluded
            if compliance_check is None:
                resources_included = evidence.get("resourcesIncluded", [])
                compliance_check = self._get_compliance_check_from_resources(resources_included)

            # Count compliance results
            compliant_count, failed_count, not_applicable_count, inconclusive_count = self._count_compliance_status(
                compliance_check,
                evidence,
                compliant_count,
                failed_count,
                not_applicable_count,
                inconclusive_count,
                failed_controls,
                failed_by_control,
            )

        total_with_checks = compliant_count + failed_count

        return {
            "compliant_count": compliant_count,
            "failed_count": failed_count,
            "inconclusive_count": inconclusive_count,
            "not_applicable_count": not_applicable_count,
            "total_with_checks": total_with_checks,
            "failed_controls": failed_controls,
            "failed_by_control": failed_by_control,
        }

    def _extract_assessment_metadata(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract assessment metadata for description building.

        :param Dict[str, Any] assessment: Assessment data
        :return: Dictionary with extracted metadata
        :rtype: Dict[str, Any]
        """
        assessment_arn = assessment.get("arn", "N/A")
        assessment_id = assessment_arn.split("/")[-1] if assessment_arn != "N/A" else "N/A"
        assessment_status = assessment.get("status", "Unknown")

        framework = assessment.get("framework", {})
        framework_name = framework.get("metadata", {}).get("name", "N/A")
        framework_type = framework.get("type", "N/A")

        aws_account = assessment.get("awsAccount", {})
        account_id = aws_account.get("id", "N/A")
        account_name = aws_account.get("name", "N/A")
        account_display = f"{account_name} ({account_id})" if account_name != "N/A" else account_id

        metadata = assessment.get("metadata", {})
        assessment_description = metadata.get("description", "")
        creation_time = metadata.get("creationTime")
        last_updated = metadata.get("lastUpdated")

        return {
            "assessment_id": assessment_id,
            "assessment_status": assessment_status,
            "framework_name": framework_name,
            "framework_type": framework_type,
            "account_display": account_display,
            "assessment_description": assessment_description,
            "creation_time": creation_time,
            "last_updated": last_updated,
        }

    def _add_timestamp_to_description(self, description_parts: list, label: str, timestamp: Any) -> None:
        """
        Add formatted timestamp to description if valid.

        :param list description_parts: List to append timestamp HTML to
        :param str label: Label for the timestamp (e.g., 'Created', 'Last Updated')
        :param Any timestamp: Timestamp value (int, float, or datetime)
        :return: None
        :rtype: None
        """
        from datetime import datetime

        if not timestamp:
            return

        try:
            if isinstance(timestamp, (int, float)):
                dt_obj = datetime.fromtimestamp(timestamp)
            else:
                dt_obj = timestamp
            description_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{label}:{HTML_STRONG_CLOSE} "
                f"{dt_obj.strftime('%Y-%m-%d %H:%M:%S')}{HTML_LI_CLOSE}"
            )
        except Exception:
            pass

    def _add_assessment_details_section(
        self, description_parts: list, assessment_name: str, metadata: Dict[str, Any]
    ) -> None:
        """
        Add assessment details section to description.

        :param list description_parts: List to append HTML sections to
        :param str assessment_name: Assessment name
        :param Dict[str, Any] metadata: Extracted metadata dictionary
        :return: None
        :rtype: None
        """
        description_parts.extend(
            [
                "<h1>AWS Audit Manager Evidence</h1>",
                f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Assessment:{HTML_STRONG_CLOSE} {assessment_name}{HTML_P_CLOSE}",
            ]
        )

        if metadata["assessment_description"]:
            description_parts.append(f"{HTML_P_OPEN}{metadata['assessment_description']}{HTML_P_CLOSE}")

        description_parts.extend(
            [
                "<h2>Assessment Details</h2>",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Assessment ID:{HTML_STRONG_CLOSE} "
                f"<code>{metadata['assessment_id']}</code>{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Status:{HTML_STRONG_CLOSE} "
                f"{metadata['assessment_status']}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}AWS Account:{HTML_STRONG_CLOSE} "
                f"{metadata['account_display']}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} "
                f"{metadata['framework_name']} ({metadata['framework_type']}){HTML_LI_CLOSE}",
            ]
        )

        self._add_timestamp_to_description(description_parts, "Created", metadata["creation_time"])
        self._add_timestamp_to_description(description_parts, "Last Updated", metadata["last_updated"])
        description_parts.append(HTML_UL_CLOSE)

    def _add_compliance_results_section(
        self,
        description_parts: list,
        compliance_stats: Dict[str, Any],
        control_summary: Dict[str, Dict[str, Any]],
        total_evidence_count: int,
    ) -> None:
        """
        Add compliance results section to description.

        :param list description_parts: List to append HTML sections to
        :param Dict[str, Any] compliance_stats: Compliance statistics
        :param Dict[str, Dict[str, Any]] control_summary: Control summary
        :param int total_evidence_count: Total evidence count
        :return: None
        :rtype: None
        """
        description_parts.extend(
            [
                "<h2>Compliance Results</h2>",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Evidence with Compliance Checks:{HTML_STRONG_CLOSE} "
                f"{compliance_stats['total_with_checks']:,} of {total_evidence_count:,}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Compliant:{HTML_STRONG_CLOSE} "
                f"{compliance_stats['compliant_count']:,}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Failed:{HTML_STRONG_CLOSE} "
                f"<span style='color: red;'>{compliance_stats['failed_count']:,}</span>{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Not Applicable:{HTML_STRONG_CLOSE} "
                f"{compliance_stats['not_applicable_count']:,}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Inconclusive:{HTML_STRONG_CLOSE} "
                f"{compliance_stats['inconclusive_count']:,}{HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
            ]
        )

        if compliance_stats["failed_controls"]:
            description_parts.extend(
                [
                    "<h3>Failed Controls</h3>",
                    f"{HTML_P_OPEN}<span style='color: red;'>{HTML_STRONG_OPEN}The following controls have "
                    f"failed compliance checks:{HTML_STRONG_CLOSE}</span>{HTML_P_CLOSE}",
                    HTML_UL_OPEN,
                ]
            )
            for control_id in sorted(compliance_stats["failed_controls"]):
                control_name = control_summary.get(control_id, {}).get("control_name", control_id)
                failed_evidence_count = compliance_stats["failed_by_control"].get(control_id, 0)
                description_parts.append(
                    f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} {control_name} "
                    f"({failed_evidence_count} failed evidence item(s)){HTML_LI_CLOSE}"
                )
            description_parts.append(HTML_UL_CLOSE)

    def _add_evidence_summary_sections(
        self,
        description_parts: list,
        total_evidence_count: int,
        control_summary: Dict[str, Dict[str, Any]],
        controls_processed: int,
        analysis: Dict[str, Any],
    ) -> None:
        """
        Add evidence summary and related sections to description.

        :param list description_parts: List to append HTML sections to
        :param int total_evidence_count: Total evidence count
        :param Dict[str, Dict[str, Any]] control_summary: Control summary
        :param int controls_processed: Number of controls processed
        :param Dict[str, Any] analysis: Evidence analysis results
        :return: None
        :rtype: None
        """
        description_parts.extend(
            [
                "<h2>Evidence Summary</h2>",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Evidence Items:{HTML_STRONG_CLOSE} "
                f"{total_evidence_count:,}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Controls with Evidence:{HTML_STRONG_CLOSE} "
                f"{len(control_summary)}{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Controls Processed:{HTML_STRONG_CLOSE} "
                f"{controls_processed}{HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
                "<h2>Controls Summary</h2>",
                HTML_UL_OPEN,
            ]
        )

        for control_id in sorted(control_summary.keys()):
            control_info = control_summary[control_id]
            description_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
                f"{control_info['evidence_count']:,} items - <em>{control_info['control_name']}</em>{HTML_LI_CLOSE}"
            )

        description_parts.append(HTML_UL_CLOSE)
        description_parts.append("<h2>Data Sources</h2>")
        description_parts.append(HTML_UL_OPEN)
        for source in sorted(analysis["data_sources"]):
            description_parts.append(f"{HTML_LI_OPEN}{source}{HTML_LI_CLOSE}")
        description_parts.append(HTML_UL_CLOSE)

        if analysis["event_names"]:
            description_parts.append("<h2>Event Types (Sample)</h2>")
            description_parts.append(HTML_UL_OPEN)
            for event_name in sorted(list(analysis["event_names"])[:10]):
                description_parts.append(f"{HTML_LI_OPEN}<code>{event_name}</code>{HTML_LI_CLOSE}")
            description_parts.append(HTML_UL_CLOSE)

        if analysis["date_range_start"] and analysis["date_range_end"]:
            description_parts.extend(
                [
                    "<h2>Evidence Date Range</h2>",
                    HTML_UL_OPEN,
                    f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}From:{HTML_STRONG_CLOSE} "
                    f"{analysis['date_range_start'].strftime('%Y-%m-%d %H:%M:%S')}{HTML_LI_CLOSE}",
                    f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}To:{HTML_STRONG_CLOSE} "
                    f"{analysis['date_range_end'].strftime('%Y-%m-%d %H:%M:%S')}{HTML_LI_CLOSE}",
                    HTML_UL_CLOSE,
                ]
            )

    def _build_evidence_description(
        self,
        assessment: Dict[str, Any],
        assessment_name: str,
        all_evidence_items: List[Dict[str, Any]],
        control_summary: Dict[str, Dict[str, Any]],
        controls_processed: int,
        scan_date: str,
    ) -> tuple:
        """
        Build evidence description with analysis of evidence items using HTML formatting.

        :param Dict[str, Any] assessment: Full assessment data from AWS Audit Manager
        :param str assessment_name: Assessment name
        :param List[Dict[str, Any]] all_evidence_items: All evidence items
        :param Dict[str, Dict[str, Any]] control_summary: Control summary
        :param int controls_processed: Number of controls processed
        :param str scan_date: Scan date
        :return: Tuple of (description, safe_assessment_name, file_name)
        :rtype: tuple
        """
        # Extract assessment metadata
        metadata = self._extract_assessment_metadata(assessment)

        # Analyze evidence items
        total_evidence_count = len(all_evidence_items)
        analysis = self._analyze_evidence_items(all_evidence_items)
        compliance_stats = self._analyze_compliance_results(all_evidence_items)

        # Build description parts
        description_parts = []

        self._add_assessment_details_section(description_parts, assessment_name, metadata)
        self._add_compliance_results_section(description_parts, compliance_stats, control_summary, total_evidence_count)
        self._add_evidence_summary_sections(
            description_parts, total_evidence_count, control_summary, controls_processed, analysis
        )

        # Generate safe filename from assessment name
        safe_assessment_name = assessment_name.replace(" ", "_").replace("/", "_")[:50]
        file_name = f"audit_manager_evidence_{safe_assessment_name}_{scan_date}.jsonl.gz"

        description_parts.extend(
            [
                "<h2>Attached Files</h2>",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{file_name}{HTML_STRONG_CLOSE} (gzipped JSONL format){HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
            ]
        )

        return "\n".join(description_parts), safe_assessment_name, file_name

    def _convert_evidence_timestamp(self, evidence_time: Any) -> Optional[Any]:
        """
        Convert evidence timestamp to datetime if needed.

        :param Any evidence_time: Evidence time value (datetime, int, float, or other)
        :return: Datetime object or None if invalid
        :rtype: Optional[Any]
        """
        from datetime import datetime

        # Handle both datetime objects and timestamp integers
        if isinstance(evidence_time, (int, float)):
            return datetime.fromtimestamp(evidence_time / 1000)
        if isinstance(evidence_time, datetime):
            return evidence_time
        return None

    def _update_date_range(self, evidence_time: Any, date_range_start: Any, date_range_end: Any) -> tuple:
        """
        Update date range with new evidence timestamp.

        :param Any evidence_time: Datetime object
        :param Any date_range_start: Current start datetime or None
        :param Any date_range_end: Current end datetime or None
        :return: Tuple of (updated_start, updated_end)
        :rtype: tuple
        """
        updated_start = date_range_start
        updated_end = date_range_end

        if not date_range_start or evidence_time < date_range_start:
            updated_start = evidence_time
        if not date_range_end or evidence_time > date_range_end:
            updated_end = evidence_time

        return updated_start, updated_end

    def _process_evidence_item(
        self, item: Dict[str, Any], data_sources: set, event_names: set, date_range_start: Any, date_range_end: Any
    ) -> tuple:
        """
        Process a single evidence item to extract analysis data.

        :param Dict[str, Any] item: Evidence item
        :param set data_sources: Set to update with data sources
        :param set event_names: Set to update with event names
        :param Any date_range_start: Current start datetime
        :param Any date_range_end: Current end datetime
        :return: Tuple of (date_range_start, date_range_end)
        :rtype: tuple
        """
        # Extract data source
        if "dataSource" in item:
            data_sources.add(item["dataSource"])

        # Extract event name
        if "eventName" in item:
            event_names.add(item["eventName"])

        # Extract and process timestamp
        if "time" in item:
            evidence_time = self._convert_evidence_timestamp(item["time"])
            if evidence_time:
                date_range_start, date_range_end = self._update_date_range(
                    evidence_time, date_range_start, date_range_end
                )

        return date_range_start, date_range_end

    def _analyze_evidence_items(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze evidence items to extract data sources, event names, and date ranges.

        :param List[Dict[str, Any]] evidence_items: Evidence items to analyze
        :return: Dictionary with analysis results
        :rtype: Dict[str, Any]
        """
        data_sources = set()
        event_names = set()
        date_range_start = None
        date_range_end = None

        for item in evidence_items:
            date_range_start, date_range_end = self._process_evidence_item(
                item, data_sources, event_names, date_range_start, date_range_end
            )

        return {
            "data_sources": data_sources,
            "event_names": event_names,
            "date_range_start": date_range_start,
            "date_range_end": date_range_end,
        }

    def _compress_evidence_data(self, evidence_items: List[Dict[str, Any]]) -> tuple:
        """
        Compress evidence data to gzipped JSONL format.

        :param List[Dict[str, Any]] evidence_items: Evidence items to compress
        :return: Tuple of (compressed_data, uncompressed_size_mb, compressed_size_mb, compression_ratio)
        :rtype: tuple
        """
        import gzip
        from io import BytesIO

        jsonl_content = "\n".join([json.dumps(item, default=str) for item in evidence_items])

        # Compress the JSONL content in memory
        compressed_buffer = BytesIO()
        with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
            gz_file.write(jsonl_content)

        compressed_data = compressed_buffer.getvalue()
        compressed_size_mb = len(compressed_data) / (1024 * 1024)
        uncompressed_size_mb = len(jsonl_content.encode("utf-8")) / (1024 * 1024)
        compression_ratio = (1 - (len(compressed_data) / len(jsonl_content.encode("utf-8")))) * 100

        return compressed_data, uncompressed_size_mb, compressed_size_mb, compression_ratio

    def _upload_consolidated_evidence(
        self,
        created_evidence_id: int,
        safe_assessment_name: str,
        scan_date: str,
        file_name: str,
        all_evidence_items: List[Dict[str, Any]],
    ) -> None:
        """
        Save and upload consolidated evidence file as gzipped JSONL.

        :param int created_evidence_id: Evidence record ID
        :param str safe_assessment_name: Safe assessment name for filename
        :param str scan_date: Scan date
        :param str file_name: File name for upload (will be modified to add .gz)
        :param List[Dict[str, Any]] all_evidence_items: All evidence items
        """
        from regscale.core.app.api import Api
        from regscale.models.regscale_models.file import File

        # Save consolidated JSONL file to artifacts directory (already gzipped)
        artifacts_file_path = self._save_consolidated_evidence_file(
            assessment_name=safe_assessment_name, scan_date=scan_date, evidence_items=all_evidence_items
        )

        if artifacts_file_path:
            logger.info(f"Saved consolidated evidence to: {artifacts_file_path}")

        # Compress evidence data for upload to RegScale
        compressed_data, uncompressed_size_mb, compressed_size_mb, compression_ratio = self._compress_evidence_data(
            all_evidence_items
        )

        logger.info(
            "Compressed evidence: %.2f MB -> %.2f MB (%.1f%% reduction)",
            uncompressed_size_mb,
            compressed_size_mb,
            compression_ratio,
        )

        # Upload with .gz extension
        api = Api()
        gzipped_file_name = file_name if file_name.endswith(".gz") else f"{file_name}.gz"

        success = File.upload_file_to_regscale(
            file_name=gzipped_file_name,
            parent_id=created_evidence_id,
            parent_module="evidence",
            api=api,
            file_data=compressed_data,
            tags=f"aws,audit-manager,{safe_assessment_name.lower()}",
        )

        if success:
            logger.info(f"Uploaded compressed evidence file for evidence {created_evidence_id}")
        else:
            logger.warning(f"Failed to upload compressed evidence file for evidence {created_evidence_id}")

    def _save_consolidated_evidence_file(
        self, assessment_name: str, scan_date: str, evidence_items: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Save consolidated evidence items to gzipped JSONL file in artifacts directory.

        :param str assessment_name: Safe assessment name for filename
        :param str scan_date: Scan date string
        :param List[Dict[str, Any]] evidence_items: All evidence items
        :return: File path if successful, None otherwise
        :rtype: Optional[str]
        """
        import gzip

        try:
            # Ensure artifacts directory exists
            artifacts_dir = os.path.join("artifacts", "aws", "audit_manager_evidence")
            os.makedirs(artifacts_dir, exist_ok=True)

            # Create file path with .gz extension
            file_name = f"audit_manager_evidence_{assessment_name}_{scan_date}.jsonl.gz"
            file_path = os.path.join(artifacts_dir, file_name)

            # Write compressed JSONL file
            with gzip.open(file_path, "wt", encoding="utf-8", compresslevel=9) as f:
                for item in evidence_items:
                    f.write(json.dumps(item, default=str) + "\n")

            # Get file size for logging
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"Saved {len(evidence_items)} evidence items to {file_path} ({file_size_mb:.2f} MB compressed)")
            return file_path

        except IOError as ex:
            logger.error(f"Failed to save consolidated evidence file: {ex}")
            return None

    def _link_evidence_to_ssp(self, evidence_id: int) -> bool:
        """
        Link evidence to Security Plan.

        :param int evidence_id: Evidence record ID
        :return: True if successfully linked, False otherwise
        :rtype: bool
        """
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping

        mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=self.plan_id, mappingType="securityplans")

        try:
            created_mapping = mapping.create()
            if created_mapping and created_mapping.id:
                logger.info(f"Linked evidence {evidence_id} to SSP {self.plan_id}")
                return True
            else:
                logger.warning(f"Failed to link evidence to SSP: mapping.create() returned {created_mapping}")
                return False
        except Exception as ex:
            logger.warning(f"Failed to link evidence to SSP: {ex}")
            return False

    def _link_evidence_to_control_implementations(
        self, evidence_id: int, control_summary: Dict[str, Dict[str, Any]]
    ) -> int:
        """
        Link evidence to control implementations in the security plan.

        For each control in the control_summary, looks up the corresponding control implementation
        in the security plan and creates an evidence mapping to link the evidence to that
        implementation. This ensures evidence is properly associated with both the security plan
        and the specific control implementations.

        Note: Uses mappingType="controls" to properly link evidence to control implementations,
        matching the RegScale evidence mapping model expectations.

        :param int evidence_id: Evidence record ID
        :param Dict[str, Dict[str, Any]] control_summary: Summary of controls with evidence
        :return: Number of controls successfully linked
        :rtype: int
        """
        if not control_summary:
            logger.debug("No control summary provided, skipping control implementation evidence mapping")
            return 0

        implementations = self._prepare_control_implementations()
        linked_count, failed_control_ids = self._link_controls_to_evidence(
            evidence_id, control_summary, implementations
        )
        self._log_linking_results(evidence_id, linked_count, failed_control_ids, len(control_summary))
        return linked_count

    def _prepare_control_implementations(self):
        """
        Get and cache control implementations for the security plan.

        :return: List of control implementations
        :rtype: list
        """
        implementations = self._get_control_implementations()
        if implementations:
            self._build_control_lookup_cache(implementations)
            logger.debug(f"Found {len(implementations)} control implementations in SSP {self.plan_id}")
        else:
            logger.warning(
                f"No control implementations found in SSP {self.plan_id} - evidence will not be linked to controls"
            )
        return implementations

    def _link_controls_to_evidence(
        self, evidence_id: int, control_summary: Dict[str, Dict[str, Any]], implementations
    ) -> tuple:
        """
        Link all controls in summary to evidence.

        :param int evidence_id: Evidence record ID
        :param Dict[str, Dict[str, Any]] control_summary: Summary of controls
        :param implementations: List of control implementations
        :return: Tuple of (linked_count, failed_control_ids)
        :rtype: tuple
        """
        logger.info(
            f"Linking evidence {evidence_id} to {len(control_summary)} control implementation(s) in SSP {self.plan_id}..."
        )
        control_ids_sample = list(control_summary.keys())[:5]
        logger.debug(f"Sample control IDs to be linked: {control_ids_sample}")

        linked_count = 0
        failed_control_ids = []

        for control_id in control_summary.keys():
            success = self._link_single_control_to_evidence(evidence_id, control_id, implementations)
            if success:
                linked_count += 1
            else:
                failed_control_ids.append(control_id)

        return linked_count, failed_control_ids

    def _link_single_control_to_evidence(self, evidence_id: int, control_id: str, implementations) -> bool:
        """
        Link a single control to evidence.

        :param int evidence_id: Evidence record ID
        :param str control_id: Control ID to link
        :param implementations: List of control implementations
        :return: True if successfully linked, False otherwise
        :rtype: bool
        """
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping

        try:
            control_impl, _ = self._find_matching_implementation(control_id, implementations)

            if not control_impl or not control_impl.id:
                logger.info(
                    f"Control implementation not found in SSP for control {control_id}, skipping evidence mapping"
                )
                return False

            mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=control_impl.id, mappingType="controls")
            created_mapping = mapping.create()

            if created_mapping and created_mapping.id:
                logger.info(
                    f"Successfully linked evidence {evidence_id} to control implementation {control_impl.id} "
                    f"(control {control_id}, mapping ID: {created_mapping.id})"
                )
                return True

            logger.warning(
                f"Failed to create evidence mapping for control {control_id}: "
                f"mapping.create() returned {created_mapping}"
            )
            return False

        except Exception as ex:
            logger.warning(f"Failed to link evidence to control implementation {control_id}: {ex}")
            return False

    def _log_linking_results(
        self, evidence_id: int, linked_count: int, failed_control_ids: list, total_controls: int
    ) -> None:
        """
        Log the results of evidence linking.

        :param int evidence_id: Evidence record ID
        :param int linked_count: Number of controls successfully linked
        :param list failed_control_ids: List of failed control IDs
        :param int total_controls: Total number of controls attempted
        :rtype: None
        """
        failed_count = len(failed_control_ids)

        if linked_count > 0:
            logger.info(
                f"Successfully linked evidence {evidence_id} to {linked_count} of {total_controls} "
                f"control implementation(s) in SSP {self.plan_id}"
            )
            if failed_count > 0:
                self._log_failed_controls(failed_control_ids)
        elif failed_count > 0:
            logger.warning(
                f"Failed to link evidence {evidence_id} to any control implementations. "
                f"{failed_count} control(s) not found in SSP {self.plan_id}: {', '.join(failed_control_ids[:10])}"
                f"{f' (and {len(failed_control_ids) - 10} more)' if len(failed_control_ids) > 10 else ''}"
            )

    def _log_failed_controls(self, failed_control_ids: list) -> None:
        """
        Log failed control IDs.

        :param list failed_control_ids: List of failed control IDs
        :rtype: None
        """
        failed_count = len(failed_control_ids)
        failed_sample = ", ".join(failed_control_ids[:10])
        remaining_msg = f" (and {failed_count - 10} more)" if failed_count > 10 else ""
        logger.warning(
            f"{failed_count} control(s) could not be linked (not found in SSP): {failed_sample}{remaining_msg}"
        )

    def _handle_permission_error(self, permission_name: str, error: ClientError) -> bool:
        """
        Handle permission test error and log appropriately.

        :param str permission_name: Permission being tested
        :param ClientError error: AWS ClientError exception
        :return: False (permission denied/failed)
        :rtype: bool
        """
        if error.response["Error"]["Code"] in ["AccessDeniedException", "UnauthorizedException"]:
            logger.error(f"✗ {permission_name} - DENIED: {error.response['Error']['Message']}")
        else:
            logger.warning(f"? {permission_name} - Error: {error}")
        return False

    def _test_list_assessments_permission(self, permissions: Dict[str, bool]) -> None:
        """
        Test auditmanager:ListAssessments permission.

        :param Dict[str, bool] permissions: Dictionary to update with test result
        :return: None
        :rtype: None
        """
        try:
            self.client.list_assessments(maxResults=1)
            permissions[IAM_PERMISSION_LIST_ASSESSMENTS] = True
            logger.info(f"✓ {IAM_PERMISSION_LIST_ASSESSMENTS} - OK")
        except ClientError as e:
            permissions[IAM_PERMISSION_LIST_ASSESSMENTS] = self._handle_permission_error(
                IAM_PERMISSION_LIST_ASSESSMENTS, e
            )

    def _test_get_assessment_permission(self, permissions: Dict[str, bool]) -> None:
        """
        Test auditmanager:GetAssessment permission.

        :param Dict[str, bool] permissions: Dictionary to update with test result
        :return: None
        :rtype: None
        """
        if not self.assessment_id:
            logger.info(f"⊘ {IAM_PERMISSION_GET_ASSESSMENT} - Skipped (no assessment_id provided)")
            return

        try:
            self.client.get_assessment(assessmentId=self.assessment_id)
            permissions[IAM_PERMISSION_GET_ASSESSMENT] = True
            logger.info(f"✓ {IAM_PERMISSION_GET_ASSESSMENT} - OK")
        except ClientError as e:
            permissions[IAM_PERMISSION_GET_ASSESSMENT] = self._handle_permission_error(IAM_PERMISSION_GET_ASSESSMENT, e)

    def _get_first_control_from_assessment(self) -> Optional[tuple]:
        """
        Get first control from assessment for permission testing.

        :return: Tuple of (control_set_id, control_id) or None
        :rtype: Optional[tuple]
        """
        try:
            response = self.client.get_assessment(assessmentId=self.assessment_id)
            assessment = response.get("assessment", {})
            control_sets = assessment.get("framework", {}).get("controlSets", [])

            if control_sets and control_sets[0].get("controls"):
                control_set_id = control_sets[0].get("id")
                control_id = control_sets[0].get("controls", [])[0].get("id")
                return control_set_id, control_id
        except ClientError as e:
            logger.warning(f"Could not retrieve assessment for permission testing: {e}")
        return None

    def _test_evidence_folders_permission(
        self, permissions: Dict[str, bool], control_set_id: str, control_id: str
    ) -> None:
        """
        Test auditmanager:GetEvidenceFoldersByAssessmentControl permission.

        :param Dict[str, bool] permissions: Dictionary to update with test result
        :param str control_set_id: Control set ID for testing
        :param str control_id: Control ID for testing
        :return: None
        :rtype: None
        """
        try:
            self.client.get_evidence_folders_by_assessment_control(
                assessmentId=self.assessment_id, controlSetId=control_set_id, controlId=control_id
            )
            permissions[IAM_PERMISSION_GET_EVIDENCE_FOLDERS] = True
            logger.info(f"✓ {IAM_PERMISSION_GET_EVIDENCE_FOLDERS} - OK")
        except ClientError as e:
            permissions[IAM_PERMISSION_GET_EVIDENCE_FOLDERS] = self._handle_permission_error(
                IAM_PERMISSION_GET_EVIDENCE_FOLDERS, e
            )

    def _test_evidence_permissions(self, permissions: Dict[str, bool]) -> None:
        """
        Test evidence-related permissions (requires assessment with controls).

        :param Dict[str, bool] permissions: Dictionary to update with test results
        :return: None
        :rtype: None
        """
        if not self.assessment_id:
            logger.info(f"⊘ {IAM_PERMISSION_GET_EVIDENCE_FOLDERS} - Skipped (no assessment_id provided)")
            logger.info("⊘ auditmanager:GetEvidenceByEvidenceFolder - Skipped (no assessment_id provided)")
            return

        control_info = self._get_first_control_from_assessment()
        if control_info:
            control_set_id, control_id = control_info
            self._test_evidence_folders_permission(permissions, control_set_id, control_id)
            logger.info("⊘ auditmanager:GetEvidenceByEvidenceFolder - Cannot test (requires evidence folder ID)")
        else:
            logger.info(f"⊘ {IAM_PERMISSION_GET_EVIDENCE_FOLDERS} - Skipped (no controls in assessment)")
            logger.info("⊘ auditmanager:GetEvidenceByEvidenceFolder - Skipped (no controls in assessment)")

    def _log_permission_test_summary(self, permissions: Dict[str, bool]) -> None:
        """
        Log summary of permission test results.

        :param Dict[str, bool] permissions: Dictionary of permission test results
        :return: None
        :rtype: None
        """
        passed = sum(1 for v in permissions.values() if v)
        total = len(permissions)
        logger.info(f"\nPermission Test Summary: {passed}/{total} permissions verified")

        if passed < total:
            logger.warning(
                "\nSome permissions are missing. Evidence collection may fail. "
                "Please ensure your IAM role/user has the required AWS Audit Manager permissions."
            )
        else:
            logger.info("\nAll tested permissions are OK!")

    def test_iam_permissions(self) -> Dict[str, bool]:
        """
        Test IAM permissions required for AWS Audit Manager evidence collection.

        Tests the following permissions:
        - auditmanager:ListAssessments
        - auditmanager:GetAssessment
        - auditmanager:GetEvidenceFoldersByAssessmentControl
        - auditmanager:GetEvidenceByEvidenceFolder

        :return: Dictionary mapping permission names to test results (True=success, False=denied)
        :rtype: Dict[str, bool]
        """
        logger.info("Testing IAM permissions for AWS Audit Manager...")
        permissions = {}

        self._test_list_assessments_permission(permissions)
        self._test_get_assessment_permission(permissions)
        self._test_evidence_permissions(permissions)

        self._log_permission_test_summary(permissions)

        return permissions

    def _fetch_assessments_for_evidence(self) -> List[Dict[str, Any]]:
        """
        Fetch assessments for evidence collection.

        :return: List of assessments
        :rtype: List[Dict[str, Any]]
        """
        if self.assessment_id:
            assessments = [self._get_assessment_details(self.assessment_id)]
            logger.debug(f"Using specific assessment ID: {self.assessment_id}")
        else:
            assessments = self._list_all_assessments()
            logger.debug(f"Listed {len(assessments)} total assessments")
        return assessments

    def _log_assessment_details(self, assessments: List[Dict[str, Any]]) -> None:
        """
        Log assessment details before filtering.

        :param List[Dict[str, Any]] assessments: List of assessments to log
        :return: None
        :rtype: None
        """
        for assessment in assessments:
            if not assessment:
                continue
            framework_info = self._get_assessment_framework(assessment)
            logger.debug(
                f"Assessment '{assessment.get('name', 'Unknown')}' - "
                f"Framework info: '{framework_info}', "
                f"ComplianceType: '{assessment.get('complianceType', '')}'"
            )

    def _filter_assessments_by_framework(self, assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter assessments by framework.

        IMPORTANT: When assessment_id is explicitly provided, skip framework filtering
        since the user has already specified exactly which assessment to use.

        :param List[Dict[str, Any]] assessments: Assessments to filter
        :return: Filtered assessments
        :rtype: List[Dict[str, Any]]
        """
        # If assessment_id is provided, skip framework filtering
        if self.assessment_id:
            logger.info(f"Using specific assessment ID '{self.assessment_id}' - bypassing framework filter")
            return assessments

        filtered_assessments = []
        for assessment in assessments:
            if not assessment:
                continue

            framework_info = self._get_assessment_framework(assessment)
            if self._matches_framework(framework_info):
                filtered_assessments.append(assessment)
                logger.debug(f"✓ Assessment '{assessment.get('name')}' passed framework filter")
            else:
                logger.debug(
                    f"✗ Assessment '{assessment.get('name')}' filtered out - "
                    f"framework '{framework_info}' does not match '{self.framework}' "
                    f"(custom name: '{self.custom_framework_name or 'N/A'}')"
                )
        return filtered_assessments

    def _process_evidence_collection(self, assessments: List[Dict[str, Any]]) -> None:
        """
        Process evidence collection for filtered assessments.

        :param List[Dict[str, Any]] assessments: Filtered assessments
        :return: None
        :rtype: None
        """
        if assessments:
            # Log assessment details for debugging
            if self.assessment_id:
                assessment = assessments[0]
                logger.info(
                    f"Processing specific assessment: "
                    f"Name: '{assessment.get('name', 'N/A')}', "
                    f"Framework: '{assessment.get('framework', {}).get('metadata', {}).get('name', 'N/A')}', "
                    f"Compliance Type: '{assessment.get('complianceType', 'N/A')}'"
                )
            else:
                logger.info(f"Found {len(assessments)} assessment(s) matching framework filter for evidence collection")

            self.collect_assessment_evidence(assessments)
        else:
            # More detailed error message when assessment_id is provided
            if self.assessment_id:
                logger.error(
                    f"Failed to find assessment with ID '{self.assessment_id}'. "
                    f"Please verify the assessment ID exists and you have permission to access it."
                )
            else:
                logger.warning(
                    f"No assessments found for evidence collection. "
                    f"Framework: '{self.framework}', Custom name: '{self.custom_framework_name or 'N/A'}'"
                )

    def _collect_evidence_before_sync(self, assessments: List[Dict[str, Any]]) -> None:
        """
        Collect evidence before compliance sync to enable evidence-based compliance determination.

        This method collects evidence and stores it by control ID so that when compliance items
        are created, they have evidence available for proper pass/fail status determination.

        :param List[Dict[str, Any]] assessments: Filtered assessments to collect evidence for
        :return: None
        :rtype: None
        """
        logger.info("Pre-collecting evidence for compliance items...")

        for assessment in assessments:
            assessment_id = assessment.get("arn", "").split("/")[-1]
            assessment_name = assessment.get("name", assessment_id)

            logger.info(f"Pre-collecting evidence for assessment: {assessment_name}")

            # Use assessment-level evidence collection (fast method)
            all_evidence_items, control_summary = self._collect_evidence_assessment_level(assessment, assessment_id)

            # Store evidence by control ID for use during compliance item creation
            for control_id, control_data in control_summary.items():
                # Normalize control ID to lowercase for consistent lookup
                control_id_lower = control_id.lower()

                # Get evidence items for this control
                evidence_for_control = [
                    item for item in all_evidence_items if item.get("_control_id", "").lower() == control_id_lower
                ]

                # Store in the evidence map
                if evidence_for_control:
                    self._evidence_by_control[control_id_lower] = evidence_for_control
                    logger.debug(
                        f"Stored {len(evidence_for_control)} evidence items for control {control_id} "
                        f"({control_data.get('passed', 0)}P/{control_data.get('failed', 0)}F)"
                    )

        logger.info(
            f"Pre-collected evidence for {len(self._evidence_by_control)} controls "
            f"({sum(len(items) for items in self._evidence_by_control.values())} total evidence items)"
        )

    def sync_compliance(self) -> None:
        """
        Sync compliance data from AWS Audit Manager to RegScale.

        Extends the base sync_compliance method to add evidence collection.

        CRITICAL: When using assessment-evidence-folders, evidence must be collected BEFORE
        compliance sync so that compliance items have proper pass/fail status for issue creation.

        :return: None
        :rtype: None
        """
        # If evidence collection is enabled with assessment folders, collect evidence FIRST
        # so compliance items have proper pass/fail status from the start
        if self.collect_evidence and self.use_assessment_evidence_folders:
            logger.info("Collecting evidence before compliance sync to enable proper pass/fail determination...")
            try:
                # Fetch assessments
                assessments = self._fetch_assessments_for_evidence()

                # Log assessment details
                self._log_assessment_details(assessments)

                # Filter by framework
                filtered_assessments = self._filter_assessments_by_framework(assessments)

                # Collect evidence and store by control ID for later use
                self._collect_evidence_before_sync(filtered_assessments)

            except Exception as e:
                logger.error(f"Error during pre-sync evidence collection: {e}", exc_info=True)
                # Continue with sync even if evidence collection fails

        # Call the base class sync_compliance to handle control assessments and issue creation
        # Compliance items will now have evidence available for proper pass/fail determination
        super().sync_compliance()

        # After sync, create Evidence records and link to controls if evidence collection is enabled
        if self.collect_evidence:
            logger.info("Evidence collection enabled, creating Evidence records and linking to controls...")
            try:
                # Fetch assessments
                assessments = self._fetch_assessments_for_evidence()

                # Log assessment details
                self._log_assessment_details(assessments)

                # Filter by framework
                filtered_assessments = self._filter_assessments_by_framework(assessments)

                # Process evidence collection (old inline method)
                self._process_evidence_collection(filtered_assessments)

            except Exception as e:
                logger.error(f"Error during evidence collection: {e}", exc_info=True)

    def create_finding_from_compliance_item(self, compliance_item):
        """
        Override to set identification field for AWS Audit Manager findings.

        AWS Audit Manager findings represent assessment/audit results rather than
        vulnerability assessments, so we use "Assessment/Audit (Internal)" as the
        identification type.

        :param ComplianceItem compliance_item: The compliance item to create a finding from
        :return: IntegrationFinding with proper identification set
        """
        # Call parent implementation to create the base finding
        finding = super().create_finding_from_compliance_item(compliance_item)

        if finding:
            # Set the identification to Assessment/Audit (Internal) instead of default Vulnerability Assessment
            finding.identification = "Assessment/Audit (Internal)"

        return finding
