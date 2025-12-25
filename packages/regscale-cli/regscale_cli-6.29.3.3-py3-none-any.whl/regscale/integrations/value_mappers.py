#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value mapping utilities for scanner integrations.

This module provides robust mapping functions to normalize incoming severity and status values
from various scanners to RegScale's standardized enum values.
"""

import logging
import re
from typing import Optional, Union

from regscale.models import regscale_models

logger = logging.getLogger(__name__)


def normalize_severity_to_vulnerability(
    severity: Union[str, regscale_models.IssueSeverity, regscale_models.VulnerabilitySeverity, None],
    default: regscale_models.VulnerabilitySeverity = regscale_models.VulnerabilitySeverity.Low,
    source: Optional[str] = None,
) -> regscale_models.VulnerabilitySeverity:
    """
    Normalize severity value to VulnerabilitySeverity enum.

    Handles multiple input formats:
    - String values: "CRITICAL", "Critical", "critical", "HIGH", "High", "high", etc.
    - Numeric values: "0", "1", "2", "3", "4" or 0, 1, 2, 3, 4
    - RegScale IssueSeverity enums
    - RegScale VulnerabilitySeverity enums
    - Full severity strings: "0 - Critical - Critical Deficiency", "I - High - Significant Deficiency"

    :param Union[str, regscale_models.IssueSeverity, regscale_models.VulnerabilitySeverity, None] severity:
        The severity value to normalize
    :param regscale_models.VulnerabilitySeverity default: Default value if normalization fails
    :param Optional[str] source: Source system name for better logging
    :return: Normalized VulnerabilitySeverity enum value
    :rtype: regscale_models.VulnerabilitySeverity
    """
    if severity is None:
        logger.warning(f"[{source or 'Unknown'}] Received None severity value, using default: {default}")
        return default

    # If already the correct enum type, return it
    if isinstance(severity, regscale_models.VulnerabilitySeverity):
        return severity

    # If it's an IssueSeverity, map it to VulnerabilitySeverity
    if isinstance(severity, regscale_models.IssueSeverity):
        return _issue_severity_to_vulnerability_severity(severity)

    # Convert to string and normalize
    severity_str = str(severity).strip()

    # Try direct mapping first (handles exact matches including enum values)
    direct_match = _direct_severity_match(severity_str)
    if direct_match:
        logger.debug(f"[{source or 'Unknown'}] Mapped '{severity}' -> {direct_match} (direct match)")
        return direct_match

    # Try fuzzy matching with various patterns
    fuzzy_match = _fuzzy_severity_match(severity_str)
    if fuzzy_match:
        logger.debug(f"[{source or 'Unknown'}] Mapped '{severity}' -> {fuzzy_match} (fuzzy match)")
        return fuzzy_match

    # Log warning for unmapped value
    logger.warning(
        f"[{source or 'Unknown'}] Unable to map severity value '{severity}' "
        f"(type: {type(severity).__name__}), using default: {default}"
    )
    return default


def normalize_status_to_issue_status(
    status: Union[str, regscale_models.IssueStatus, regscale_models.VulnerabilityStatus, None],
    default: regscale_models.IssueStatus = regscale_models.IssueStatus.Open,
    source: Optional[str] = None,
) -> regscale_models.IssueStatus:
    """
    Normalize status value to IssueStatus enum.

    Handles multiple input formats:
    - String values: "OPEN", "Open", "open", "CLOSED", "Closed", "closed"
    - VulnerabilityStatus enums: VulnerabilityStatus.Open -> IssueStatus.Open
    - IssueStatus enums: returns as-is
    - Other status values: "Draft", "Pending Screening", etc.

    :param Union[str, regscale_models.IssueStatus, regscale_models.VulnerabilityStatus, None] status:
        The status value to normalize
    :param regscale_models.IssueStatus default: Default value if normalization fails
    :param Optional[str] source: Source system name for better logging
    :return: Normalized IssueStatus enum value
    :rtype: regscale_models.IssueStatus
    """
    if status is None:
        logger.warning(f"[{source or 'Unknown'}] Received None status value, using default: {default}")
        return default

    # If already the correct enum type, return it
    if isinstance(status, regscale_models.IssueStatus):
        return status

    # If it's a VulnerabilityStatus, map it to IssueStatus
    if isinstance(status, regscale_models.VulnerabilityStatus):
        return _vulnerability_status_to_issue_status(status)

    # Convert to string and normalize
    status_str = str(status).strip()

    # Try direct mapping
    direct_match = _direct_status_match(status_str)
    if direct_match:
        logger.debug(f"[{source or 'Unknown'}] Mapped '{status}' -> {direct_match} (direct match)")
        return direct_match

    # Try case-insensitive matching
    status_lower = status_str.lower()

    # Common status mappings
    status_map = {
        "open": regscale_models.IssueStatus.Open,
        "closed": regscale_models.IssueStatus.Closed,
        "draft": regscale_models.IssueStatus.Draft,
        "pending screening": regscale_models.IssueStatus.PendingScreening,
        "pending verification": regscale_models.IssueStatus.PendingVerification,
        "cancelled": regscale_models.IssueStatus.Cancelled,
        "canceled": regscale_models.IssueStatus.Cancelled,  # Handle alternate spelling
        "pending decommission": regscale_models.IssueStatus.PendingDecommission,
        "delayed": regscale_models.IssueStatus.Delayed,
        "pending approval": regscale_models.IssueStatus.PendingApproval,
    }

    if status_lower in status_map:
        mapped_status = status_map[status_lower]
        logger.debug(f"[{source or 'Unknown'}] Mapped '{status}' -> {mapped_status}")
        return mapped_status

    # Log warning for unmapped value
    logger.warning(
        f"[{source or 'Unknown'}] Unable to map status value '{status}' "
        f"(type: {type(status).__name__}), using default: {default}"
    )
    return default


def _issue_severity_to_vulnerability_severity(
    severity: regscale_models.IssueSeverity,
) -> regscale_models.VulnerabilitySeverity:
    """
    Map IssueSeverity to VulnerabilitySeverity.

    :param regscale_models.IssueSeverity severity: The IssueSeverity to map
    :return: Corresponding VulnerabilitySeverity
    :rtype: regscale_models.VulnerabilitySeverity
    """
    mapping = {
        regscale_models.IssueSeverity.Critical: regscale_models.VulnerabilitySeverity.Critical,
        regscale_models.IssueSeverity.High: regscale_models.VulnerabilitySeverity.High,
        regscale_models.IssueSeverity.Moderate: regscale_models.VulnerabilitySeverity.Medium,
        regscale_models.IssueSeverity.Low: regscale_models.VulnerabilitySeverity.Low,
        regscale_models.IssueSeverity.NotAssigned: regscale_models.VulnerabilitySeverity.Low,
    }
    return mapping.get(severity, regscale_models.VulnerabilitySeverity.Low)


def _vulnerability_status_to_issue_status(
    status: regscale_models.VulnerabilityStatus,
) -> regscale_models.IssueStatus:
    """
    Map VulnerabilityStatus to IssueStatus.

    :param regscale_models.VulnerabilityStatus status: The VulnerabilityStatus to map
    :return: Corresponding IssueStatus
    :rtype: regscale_models.IssueStatus
    """
    mapping = {
        regscale_models.VulnerabilityStatus.Open: regscale_models.IssueStatus.Open,
        regscale_models.VulnerabilityStatus.Closed: regscale_models.IssueStatus.Closed,
    }
    return mapping.get(status, regscale_models.IssueStatus.Open)


def _direct_severity_match(severity_str: str) -> Optional[regscale_models.VulnerabilitySeverity]:
    """
    Try direct string matching for severity values.

    :param str severity_str: The severity string to match
    :return: Matched VulnerabilitySeverity or None
    :rtype: Optional[regscale_models.VulnerabilitySeverity]
    """
    # Exact matches (case-insensitive)
    severity_lower = severity_str.lower()

    direct_map = {
        "critical": regscale_models.VulnerabilitySeverity.Critical,
        "high": regscale_models.VulnerabilitySeverity.High,
        "medium": regscale_models.VulnerabilitySeverity.Medium,
        "moderate": regscale_models.VulnerabilitySeverity.Medium,
        "low": regscale_models.VulnerabilitySeverity.Low,
        "informational": regscale_models.VulnerabilitySeverity.Informational,
        "info": regscale_models.VulnerabilitySeverity.Informational,
        "negligible": regscale_models.VulnerabilitySeverity.Informational,
        "none": regscale_models.VulnerabilitySeverity.Informational,
    }

    return direct_map.get(severity_lower)


def _fuzzy_severity_match(severity_str: str) -> Optional[regscale_models.VulnerabilitySeverity]:
    """
    Try fuzzy matching for severity values using patterns.

    Handles formats like:
    - "0 - Critical - Critical Deficiency"
    - "I - High - Significant Deficiency"
    - "IV - Not Assigned"
    - Numeric values: "0", "1", "2", "3", "4"

    :param str severity_str: The severity string to match
    :return: Matched VulnerabilitySeverity or None
    :rtype: Optional[regscale_models.VulnerabilitySeverity]
    """
    severity_lower = severity_str.lower()

    # Check for numeric severity (0=Critical, 1=High, 2=Medium, 3=Low, 4=Informational)
    if severity_str.isdigit():
        numeric_map = {
            "0": regscale_models.VulnerabilitySeverity.Critical,
            "1": regscale_models.VulnerabilitySeverity.High,
            "2": regscale_models.VulnerabilitySeverity.Medium,
            "3": regscale_models.VulnerabilitySeverity.Low,
            "4": regscale_models.VulnerabilitySeverity.Informational,
        }
        return numeric_map.get(severity_str)

    # Check for patterns in the string
    # NOTE: Order matters! Check more specific patterns first (III before II before I)
    if "critical" in severity_lower or "0 -" in severity_lower:
        return regscale_models.VulnerabilitySeverity.Critical

    if (
        "iii -" in severity_lower
        or "3 -" in severity_lower
        or ("low" in severity_lower and "ii -" not in severity_lower and "i -" not in severity_lower)
    ):
        return regscale_models.VulnerabilitySeverity.Low

    if (
        "moderate" in severity_lower
        or "medium" in severity_lower
        or "ii -" in severity_lower
        or "2 -" in severity_lower
    ):
        return regscale_models.VulnerabilitySeverity.Medium

    if "high" in severity_lower or "i -" in severity_lower or "1 -" in severity_lower:
        return regscale_models.VulnerabilitySeverity.High

    if "low" in severity_lower:
        return regscale_models.VulnerabilitySeverity.Low

    if (
        "info" in severity_lower
        or "informational" in severity_lower
        or "iv -" in severity_lower
        or "4 -" in severity_lower
        or "not assigned" in severity_lower
        or "negligible" in severity_lower
    ):
        return regscale_models.VulnerabilitySeverity.Informational

    return None


def _direct_status_match(status_str: str) -> Optional[regscale_models.IssueStatus]:
    """
    Try direct string matching for status values (case-insensitive).

    :param str status_str: The status string to match
    :return: Matched IssueStatus or None
    :rtype: Optional[regscale_models.IssueStatus]
    """
    # Try to match against all IssueStatus enum values
    for status_enum in regscale_models.IssueStatus:
        if status_str.lower() == status_enum.value.lower():
            return status_enum

    return None
