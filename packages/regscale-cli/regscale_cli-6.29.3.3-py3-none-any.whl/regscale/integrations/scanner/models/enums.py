"""
Enumerations for scanner integrations.

This module provides enumerations used across scanner integrations for
categorizing integration types and finding statuses.
"""

import enum

from regscale.models import regscale_models


class ScannerIntegrationType(str, enum.Enum):
    """
    Enumeration for scanner integration types.
    """

    CHECKLIST = "checklist"
    CONTROL_TEST = "control_test"
    VULNERABILITY = "vulnerability"


class FindingStatus(str, enum.Enum):
    """
    Enumeration for finding statuses.

    Maps finding statuses to their corresponding IssueStatus values.
    """

    OPEN = regscale_models.IssueStatus.Open
    CLOSED = regscale_models.IssueStatus.Closed
    FAIL = regscale_models.IssueStatus.Open
    PASS = regscale_models.IssueStatus.Closed
    NOT_APPLICABLE = regscale_models.IssueStatus.Closed
    NOT_REVIEWED = regscale_models.IssueStatus.Open
