#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Compliance Analyzer for AWS Audit Manager

This module provides enhanced control pass/fail determination based on evidence insights
from AWS Audit Manager. It implements the logic for determining control compliance status
based on compliant, non-compliant, and inconclusive evidence counts.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("regscale")

# Constants
AWS_AUDIT_MANAGER_INSIGHTS_SOURCE = "AWS Audit Manager Insights"


class ComplianceStatus(Enum):
    """Enumeration of possible compliance statuses."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NO_DATA = "NO_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceType(Enum):
    """Types of evidence compliance checks."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class EvidenceInsight:
    """Represents a single piece of evidence with its compliance status."""

    evidence_id: str
    source: str
    compliance_check: str
    resource_arn: Optional[str] = None
    timestamp: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ComplianceAnalysis:
    """Results of control compliance analysis."""

    control_id: str
    compliance_status: ComplianceStatus
    compliant_evidence_count: int
    noncompliant_evidence_count: int
    inconclusive_evidence_count: int
    not_applicable_count: int
    total_evidence_count: int
    compliance_score: float
    confidence_level: float
    reasoning: str
    evidence_sources: List[str]
    details: Dict[str, Any] = field(default_factory=dict)


class ControlComplianceAnalyzer:
    """
    Analyzes control compliance based on evidence insights from AWS Audit Manager.

    This class implements the control pass/fail determination logic based on the
    AWS Audit Manager documentation:
    - FAIL: noncompliantEvidenceCount > 0 (any non-compliance fails the control)
    - PASS: compliantEvidenceCount > 0 AND noncompliantEvidenceCount = 0
            (inconclusive evidence is allowed and doesn't prevent passing)
    - INCONCLUSIVE: Only inconclusiveEvidenceCount > 0 (no compliant/non-compliant evidence)
    - NOT_APPLICABLE: Only notApplicableCount > 0
    - NO DATA: All counts = 0

    Note: Inconclusive evidence does not prevent a control from passing as long as there
    is at least one piece of compliant evidence and no non-compliant evidence.
    """

    # Evidence source confidence mapping
    EVIDENCE_CONFIDENCE_MAP = {
        "AWS Security Hub": 0.95,
        "AWS Config": 0.95,
        "AWS CloudTrail": 0.75,
        "AWS Audit Manager": 0.85,
        "Manual": 0.60,
        "Unknown": 0.50,
    }

    def __init__(self, control_id: str):
        """
        Initialize the analyzer for a specific control.

        :param str control_id: The control identifier (e.g., "AC-2", "CC1.1")
        """
        self.control_id = control_id
        self.evidence_insights: List[EvidenceInsight] = []
        self._compliant_count = 0
        self._noncompliant_count = 0
        self._inconclusive_count = 0
        self._not_applicable_count = 0

    def add_evidence_insight(self, evidence_data: Dict[str, Any]) -> None:
        """
        Add evidence from AWS Audit Manager to the analysis.

        :param Dict[str, Any] evidence_data: Evidence data from AWS Audit Manager
        """
        # Normalize the compliance check value
        compliance_check = self._normalize_compliance_check(evidence_data.get("complianceCheck", ""))

        # Create evidence insight
        insight = EvidenceInsight(
            evidence_id=evidence_data.get("id", ""),
            source=evidence_data.get("dataSource", "AWS Audit Manager"),
            compliance_check=compliance_check,
            resource_arn=evidence_data.get("resourceArn"),
            timestamp=evidence_data.get("time"),
            attributes=evidence_data.get("attributes", {}),
            confidence=self._get_evidence_confidence(evidence_data.get("dataSource", "Unknown")),
        )

        self.evidence_insights.append(insight)

        # Update counts
        self._update_evidence_counts(compliance_check)

    def add_evidence_from_insights_api(self, insights_data: Dict[str, Any]) -> None:
        """
        Add evidence from AWS Audit Manager Control Insights API.

        :param Dict[str, Any] insights_data: Control insights data from API
        """
        # Extract evidence counts from insights API response
        evidence_insights = insights_data.get("evidenceInsights", {})

        compliant_count = evidence_insights.get("compliantEvidenceCount", 0)
        noncompliant_count = evidence_insights.get("noncompliantEvidenceCount", 0)
        inconclusive_count = evidence_insights.get("inconclusiveEvidenceCount", 0)

        # Create synthetic evidence insights for counted evidence
        for _ in range(compliant_count):
            self._compliant_count += 1
            self.evidence_insights.append(
                EvidenceInsight(
                    evidence_id=f"insights-compliant-{self._compliant_count}",
                    source=AWS_AUDIT_MANAGER_INSIGHTS_SOURCE,
                    compliance_check="COMPLIANT",
                    confidence=0.9,
                )
            )

        for _ in range(noncompliant_count):
            self._noncompliant_count += 1
            self.evidence_insights.append(
                EvidenceInsight(
                    evidence_id=f"insights-noncompliant-{self._noncompliant_count}",
                    source=AWS_AUDIT_MANAGER_INSIGHTS_SOURCE,
                    compliance_check="NON_COMPLIANT",
                    confidence=0.9,
                )
            )

        for _ in range(inconclusive_count):
            self._inconclusive_count += 1
            self.evidence_insights.append(
                EvidenceInsight(
                    evidence_id=f"insights-inconclusive-{self._inconclusive_count}",
                    source=AWS_AUDIT_MANAGER_INSIGHTS_SOURCE,
                    compliance_check="INCONCLUSIVE",
                    confidence=0.7,
                )
            )

    def determine_control_status(self) -> Tuple[str, Dict[str, Any]]:
        """
        Determine control pass/fail based on evidence counts.

        This implements the AWS Audit Manager logic:
        - FAIL: noncompliantEvidenceCount > 0 (any non-compliance = fail)
        - PASS: compliantEvidenceCount > 0 AND noncompliantEvidenceCount = 0
                (inconclusive evidence is allowed and doesn't prevent passing)
        - INCONCLUSIVE: Only inconclusiveEvidenceCount > 0 (no compliant or non-compliant)
        - NOT_APPLICABLE: Only notApplicableCount > 0
        - NO DATA: All counts = 0

        :return: Tuple of (status, details)
        :rtype: Tuple[str, Dict[str, Any]]
        """
        # Check for failures first (any non-compliant evidence = FAIL)
        if self._noncompliant_count > 0:
            return ComplianceStatus.FAIL.value, {
                "reason": "Evidence indicates non-compliance",
                "noncompliant_count": self._noncompliant_count,
                "compliant_count": self._compliant_count,
                "inconclusive_count": self._inconclusive_count,
                "not_applicable_count": self._not_applicable_count,
            }

        # Check for pass (compliant evidence with no non-compliant, inconclusive evidence allowed)
        if self._compliant_count > 0 and self._noncompliant_count == 0:
            # Determine the appropriate reason message
            if self._inconclusive_count > 0:
                reason = "Compliant evidence found with no non-compliance (some evidence inconclusive)"
            else:
                reason = "All evidence indicates compliance"

            return ComplianceStatus.PASS.value, {
                "reason": reason,
                "compliant_count": self._compliant_count,
                "inconclusive_count": self._inconclusive_count,
                "not_applicable_count": self._not_applicable_count,
            }

        # Check for inconclusive (only inconclusive evidence)
        if self._inconclusive_count > 0 and self._compliant_count == 0 and self._noncompliant_count == 0:
            return ComplianceStatus.INCONCLUSIVE.value, {
                "reason": "Only inconclusive evidence available",
                "inconclusive_count": self._inconclusive_count,
                "not_applicable_count": self._not_applicable_count,
            }

        # Check for not applicable (only not applicable evidence)
        if (
            self._not_applicable_count > 0
            and self._compliant_count == 0
            and self._noncompliant_count == 0
            and self._inconclusive_count == 0
        ):
            return ComplianceStatus.NOT_APPLICABLE.value, {
                "reason": "Evidence is not applicable to this control",
                "not_applicable_count": self._not_applicable_count,
            }

        # No data available
        return ComplianceStatus.NO_DATA.value, {
            "reason": "No evidence available for assessment",
            "total_evidence_checked": len(self.evidence_insights),
        }

    def get_compliance_analysis(self) -> ComplianceAnalysis:
        """
        Get comprehensive compliance analysis for the control.

        :return: Detailed compliance analysis
        :rtype: ComplianceAnalysis
        """
        status_str, details = self.determine_control_status()
        status = ComplianceStatus(status_str)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score()

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level()

        # Get unique evidence sources
        evidence_sources = list({insight.source for insight in self.evidence_insights})

        return ComplianceAnalysis(
            control_id=self.control_id,
            compliance_status=status,
            compliant_evidence_count=self._compliant_count,
            noncompliant_evidence_count=self._noncompliant_count,
            inconclusive_evidence_count=self._inconclusive_count,
            not_applicable_count=self._not_applicable_count,
            total_evidence_count=len(self.evidence_insights),
            compliance_score=compliance_score,
            confidence_level=confidence_level,
            reasoning=details.get("reason", ""),
            evidence_sources=evidence_sources,
            details=details,
        )

    def get_compliance_score(self) -> float:
        """
        Calculate compliance score (0-1) based on evidence.

        :return: Compliance score between 0 and 1
        :rtype: float
        """
        return self._calculate_compliance_score()

    def get_confidence_level(self) -> float:
        """
        Calculate confidence level based on evidence sources and quantity.

        :return: Confidence level between 0 and 1
        :rtype: float
        """
        return self._calculate_confidence_level()

    def get_compliance_setting_note(self) -> str:
        """
        Get a note about how the status will be mapped based on compliance settings.

        This is informational - the actual mapping is done by ComplianceIntegration
        based on the security plan's compliance settings.

        :return: Informational note about status mapping
        :rtype: str
        """
        status_str, details = self.determine_control_status()

        if status_str == "PASS":
            note = (
                "PASS status will be mapped to compliance-specific value: "
                "DoD/RMF → 'Implemented', FedRAMP → 'Fully Implemented', "
                "Default → 'Fully Implemented'"
            )
            # Add clarification if there's inconclusive evidence
            if details.get("inconclusive_count", 0) > 0:
                note += " (includes inconclusive evidence that doesn't affect passing)"
            return note
        elif status_str == "FAIL":
            return (
                "FAIL status will be mapped to compliance-specific value: "
                "DoD/RMF → 'Not Implemented' or 'Planned', FedRAMP → 'In Remediation' or 'Partially Implemented', "
                "Default → 'In Remediation'"
            )
        elif status_str == "NOT_APPLICABLE":
            return "NOT_APPLICABLE status will be mapped to 'Not Applicable' across all compliance settings"
        else:
            return "Status cannot be determined - control implementation will not be updated"

    def _normalize_compliance_check(self, compliance_check: str) -> str:
        """
        Normalize compliance check values from various AWS services.

        :param str compliance_check: Raw compliance check value
        :return: Normalized compliance status
        :rtype: str
        """
        if not compliance_check:
            return "INCONCLUSIVE"

        check_upper = compliance_check.upper()

        # Map success values
        if check_upper in ["COMPLIANT", "PASS", "PASSED", "SUCCESS"]:
            return "COMPLIANT"

        # Map failure values
        if check_upper in ["NON_COMPLIANT", "NON-COMPLIANT", "FAIL", "FAILED", "FAILURE"]:
            return "NON_COMPLIANT"

        # Map not applicable
        if check_upper in ["NOT_APPLICABLE", "NOT-APPLICABLE", "N/A", "NA"]:
            return "NOT_APPLICABLE"

        # Default to inconclusive
        return "INCONCLUSIVE"

    def _update_evidence_counts(self, compliance_check: str) -> None:
        """
        Update evidence counts based on compliance check value.

        :param str compliance_check: Normalized compliance check value
        """
        if compliance_check == "COMPLIANT":
            self._compliant_count += 1
        elif compliance_check == "NON_COMPLIANT":
            self._noncompliant_count += 1
        elif compliance_check == "NOT_APPLICABLE":
            self._not_applicable_count += 1
        else:
            self._inconclusive_count += 1

    def _get_evidence_confidence(self, source: str) -> float:
        """
        Get confidence level for an evidence source.

        :param str source: Evidence source name
        :return: Confidence level between 0 and 1
        :rtype: float
        """
        return self.EVIDENCE_CONFIDENCE_MAP.get(source, 0.5)

    def _calculate_compliance_score(self) -> float:
        """
        Calculate compliance score based on evidence.

        Score calculation:
        - 1.0: All evidence is compliant
        - 0.0: Any evidence is non-compliant
        - 0.5: Only inconclusive evidence
        - Weighted average based on evidence counts

        :return: Compliance score between 0 and 1
        :rtype: float
        """
        total_evidence = self._compliant_count + self._noncompliant_count + self._inconclusive_count

        if total_evidence == 0:
            return 0.0

        # If any non-compliant evidence, score is 0
        if self._noncompliant_count > 0:
            return 0.0

        # If all compliant, score is 1
        if self._compliant_count > 0 and self._inconclusive_count == 0:
            return 1.0

        # Mixed compliant and inconclusive
        if self._compliant_count > 0:
            return self._compliant_count / total_evidence

        # Only inconclusive
        return 0.5

    def _calculate_confidence_level(self) -> float:
        """
        Calculate confidence level based on evidence sources and quantity.

        :return: Confidence level between 0 and 1
        :rtype: float
        """
        if not self.evidence_insights:
            return 0.0

        # Calculate weighted average confidence
        total_confidence = sum(insight.confidence for insight in self.evidence_insights)
        avg_confidence = total_confidence / len(self.evidence_insights)

        # Adjust for evidence quantity (more evidence = higher confidence)
        quantity_factor = min(1.0, len(self.evidence_insights) / 10.0)

        # Combine average confidence with quantity factor
        return (avg_confidence * 0.7) + (quantity_factor * 0.3)
