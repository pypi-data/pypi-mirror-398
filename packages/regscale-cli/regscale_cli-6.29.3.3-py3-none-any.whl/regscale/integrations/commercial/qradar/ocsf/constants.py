#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OCSF constants for QRadar event mappings"""

# OCSF Version
OCSF_VERSION = "1.3.0"

# OCSF Class UIDs
# Reference: https://schema.ocsf.io/1.3.0/classes
CLASS_SECURITY_FINDING = 2001  # Vulnerability Finding
CLASS_DETECTION_FINDING = 2004  # Detection Finding (for security events)
CLASS_NETWORK_ACTIVITY = 4001  # Network Activity

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

# Severity IDs (OCSF Standard)
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

# QRadar Severity to OCSF Severity Mapping
# QRadar uses 0-10 scale
# Reference: https://www.ibm.com/docs/en/qradar-common?topic=overview-severity-levels
QRADAR_SEVERITY_MAP = {
    0: SEVERITY_INFORMATIONAL,  # Informational
    1: SEVERITY_INFORMATIONAL,  # Informational
    2: SEVERITY_LOW,  # Low
    3: SEVERITY_LOW,  # Low
    4: SEVERITY_LOW,  # Low
    5: SEVERITY_MEDIUM,  # Medium
    6: SEVERITY_MEDIUM,  # Medium
    7: SEVERITY_HIGH,  # High
    8: SEVERITY_HIGH,  # High
    9: SEVERITY_CRITICAL,  # Critical
    10: SEVERITY_CRITICAL,  # Critical
}


def map_qradar_severity(severity: int) -> int:
    """
    Map QRadar numeric severity (0-10) to OCSF severity ID.

    Args:
        severity: QRadar severity level (0-10)

    Returns:
        OCSF severity ID
    """
    return QRADAR_SEVERITY_MAP.get(severity, SEVERITY_UNKNOWN)


# QRadar Magnitude to OCSF Confidence Mapping
# Magnitude represents the relative importance of the event
def map_qradar_magnitude(magnitude: int) -> int:
    """
    Map QRadar magnitude to OCSF confidence ID.

    QRadar magnitude ranges from 0-10, representing event importance.

    Args:
        magnitude: QRadar magnitude value (0-10)

    Returns:
        OCSF confidence ID
    """
    if magnitude >= 7:
        return CONFIDENCE_HIGH
    if magnitude >= 4:
        return CONFIDENCE_MEDIUM
    if magnitude > 0:
        return CONFIDENCE_LOW
    return CONFIDENCE_UNKNOWN


# QRadar Event Category to OCSF Class UID Mapping
# This maps common QRadar event categories to appropriate OCSF classes
QRADAR_CATEGORY_CLASS_MAP = {
    "Authentication": CLASS_DETECTION_FINDING,
    "Access": CLASS_DETECTION_FINDING,
    "Exploit": CLASS_DETECTION_FINDING,
    "Malware": CLASS_DETECTION_FINDING,
    "Network": CLASS_NETWORK_ACTIVITY,
    "Policy": CLASS_DETECTION_FINDING,
    "Suspicious Activity": CLASS_DETECTION_FINDING,
    "System": CLASS_DETECTION_FINDING,
    "Unknown": CLASS_DETECTION_FINDING,  # Default to detection finding
}


def get_qradar_class_uid(category: str) -> int:
    """
    Get OCSF class UID based on QRadar event category.

    Args:
        category: QRadar event category name

    Returns:
        OCSF class UID
    """
    return QRADAR_CATEGORY_CLASS_MAP.get(category, CLASS_DETECTION_FINDING)
