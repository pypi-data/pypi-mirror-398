#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCSF constants for AWS service mappings"""

# OCSF Version
OCSF_VERSION = "1.3.0"

# OCSF Class UIDs
# Reference: https://schema.ocsf.io/1.3.0/classes
CLASS_SECURITY_FINDING = 2001  # Vulnerability Finding
CLASS_COMPLIANCE_FINDING = 2003  # Compliance Finding
CLASS_DETECTION_FINDING = 2004  # Detection Finding
CLASS_CLOUD_API = 3005  # Cloud API Activity

# Activity IDs for Detection Finding (Class 2004)
ACTIVITY_CREATE = 1
ACTIVITY_UPDATE = 2
ACTIVITY_CLOSE = 3
ACTIVITY_OTHER = 99

# Finding Status IDs
STATUS_NEW = 1
STATUS_IN_PROGRESS = 2
STATUS_SUPPRESSED = 3
STATUS_RESOLVED = 4
STATUS_OTHER = 99

# Severity IDs
SEVERITY_UNKNOWN = 0
SEVERITY_INFORMATIONAL = 1
SEVERITY_LOW = 2
SEVERITY_MEDIUM = 3
SEVERITY_HIGH = 4
SEVERITY_CRITICAL = 5
SEVERITY_FATAL = 6

# Confidence IDs
CONFIDENCE_UNKNOWN = 0
CONFIDENCE_LOW = 1
CONFIDENCE_MEDIUM = 2
CONFIDENCE_HIGH = 3

# AWS Service to OCSF Class UID Mapping
SERVICE_CLASS_MAPPING = {
    "GuardDuty": CLASS_DETECTION_FINDING,
    "SecurityHub": CLASS_SECURITY_FINDING,  # Can also be CLASS_COMPLIANCE_FINDING
    "CloudTrail": CLASS_CLOUD_API,
    "Inspector": CLASS_SECURITY_FINDING,
}

# GuardDuty Severity to OCSF Severity Mapping
GUARDDUTY_SEVERITY_MAP = {
    # GuardDuty uses 0.0-8.9 scale
    # 7.0-8.9: High
    # 4.0-6.9: Medium
    # 0.1-3.9: Low
}


def map_guardduty_severity(severity: float) -> int:
    """
    Map GuardDuty numeric severity to OCSF severity ID

    :param float severity: GuardDuty severity (0.0-8.9)
    :return: OCSF severity ID
    :rtype: int
    """
    if severity >= 7.0:
        return SEVERITY_HIGH
    elif severity >= 4.0:
        return SEVERITY_MEDIUM
    elif severity > 0:
        return SEVERITY_LOW
    return SEVERITY_UNKNOWN


# Security Hub Severity to OCSF Severity Mapping
SECURITYHUB_SEVERITY_MAP = {
    "CRITICAL": SEVERITY_CRITICAL,
    "HIGH": SEVERITY_HIGH,
    "MEDIUM": SEVERITY_MEDIUM,
    "LOW": SEVERITY_LOW,
    "INFORMATIONAL": SEVERITY_INFORMATIONAL,
}


def map_securityhub_severity(severity_label: str) -> int:
    """
    Map Security Hub severity label to OCSF severity ID

    :param str severity_label: Security Hub severity label
    :return: OCSF severity ID
    :rtype: int
    """
    return SECURITYHUB_SEVERITY_MAP.get(severity_label.upper(), SEVERITY_UNKNOWN)


# Security Hub Workflow Status to OCSF Status Mapping
SECURITYHUB_STATUS_MAP = {
    "NEW": STATUS_NEW,
    "NOTIFIED": STATUS_IN_PROGRESS,
    "SUPPRESSED": STATUS_SUPPRESSED,
    "RESOLVED": STATUS_RESOLVED,
}


def map_securityhub_status(workflow_status: str) -> int:
    """
    Map Security Hub workflow status to OCSF status ID

    :param str workflow_status: Security Hub workflow status
    :return: OCSF status ID
    :rtype: int
    """
    return SECURITYHUB_STATUS_MAP.get(workflow_status.upper(), STATUS_OTHER)
