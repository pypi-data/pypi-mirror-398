#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Config Conformance Pack to Control Mappings."""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# Control ID constants
CONTROL_IA_2_1 = "IA-2(1)"

# NIST 800-53 R5 Conformance Pack Control Mappings
# Maps AWS Config rule names to NIST 800-53 R5 control IDs
NIST_80053_R5_MAPPINGS = {
    # Access Control (AC) Family
    "iam-password-policy": ["AC-2", "IA-5"],
    "iam-user-mfa-enabled": ["AC-2", CONTROL_IA_2_1],
    "iam-root-access-key-check": ["AC-2", "AC-6"],
    "iam-user-unused-credentials-check": ["AC-2"],
    "iam-user-group-membership-check": ["AC-2"],
    "iam-policy-no-statements-with-admin-access": ["AC-6"],
    "iam-policy-no-statements-with-full-access": ["AC-6"],
    "s3-bucket-public-read-prohibited": ["AC-3", "AC-4"],
    "s3-bucket-public-write-prohibited": ["AC-3", "AC-4"],
    "ec2-security-group-attached-to-eni": ["AC-4"],
    "restricted-ssh": ["AC-4", "AC-17"],
    "restricted-common-ports": ["AC-4"],
    # Audit and Accountability (AU) Family
    "cloudtrail-enabled": ["AU-2", "AU-3", "AU-6", "AU-12"],
    "cloud-trail-cloud-watch-logs-enabled": ["AU-6"],
    "cloudtrail-log-file-validation-enabled": ["AU-9"],
    "cloudtrail-encryption-enabled": ["AU-9"],
    "cloudtrail-s3-dataevents-enabled": ["AU-2"],
    "multi-region-cloudtrail-enabled": ["AU-2"],
    "s3-bucket-logging-enabled": ["AU-2"],
    "rds-logging-enabled": ["AU-2"],
    "elb-logging-enabled": ["AU-2"],
    "cloudwatch-alarm-action-check": ["AU-6"],
    # Configuration Management (CM) Family
    "ec2-instance-managed-by-systems-manager": ["CM-2", "CM-6"],
    "ec2-managedinstance-patch-compliance-status-check": ["CM-6", "SI-2"],  # Maps to both CM and SI families
    "approved-amis-by-tag": ["CM-2"],
    # Identification and Authentication (IA) Family
    "mfa-enabled-for-iam-console-access": [CONTROL_IA_2_1],
    "root-account-mfa-enabled": [CONTROL_IA_2_1],
    # System and Communications Protection (SC) Family
    "s3-bucket-ssl-requests-only": ["SC-8", "SC-13"],
    "alb-http-to-https-redirection-check": ["SC-8"],
    "elb-tls-https-listeners-only": ["SC-8"],
    "rds-snapshot-encrypted": ["SC-13"],
    "encrypted-volumes": ["SC-13"],
    "s3-bucket-server-side-encryption-enabled": ["SC-13"],
    "ec2-ebs-encryption-by-default": ["SC-13"],
    "rds-storage-encrypted": ["SC-13"],
    "dynamodb-table-encrypted-kms": ["SC-13"],
    # System and Information Integrity (SI) Family
    "guardduty-enabled-centralized": ["SI-4"],
    "securityhub-enabled": ["SI-4"],
    "access-keys-rotated": ["SI-4"],
    "vpc-flow-logs-enabled": ["SI-4"],
    # Risk Assessment (RA) Family
    "security-account-information-provided": ["RA-5"],
}


def extract_control_ids_from_rule_name(rule_name: str) -> List[str]:
    """
    Extract control IDs from AWS Config rule name using pattern matching.

    Supports patterns like:
    - "ac-2-iam-user-mfa-enabled"
    - "nist-800-53-r5-ac-2"
    - "iam-password-policy-ac-2-ia-5"

    :param str rule_name: Config rule name
    :return: List of extracted control IDs
    :rtype: List[str]
    """
    control_ids = []

    # Pattern for NIST control IDs: AC-2, SI-3(1), etc.
    pattern = r"\b([A-Z]{2}-\d+(?:\(\d+\))?)\b"

    matches = re.findall(pattern, rule_name.upper())
    control_ids.extend(matches)

    return list(set(control_ids))  # Remove duplicates


def extract_control_ids_from_tags(tags: Dict[str, str]) -> List[str]:
    """
    Extract control IDs from AWS Config rule tags.

    Expected tag format:
    - ControlID=AC-2
    - ControlID=AC-2,AU-3,SI-2
    - ControlIDs=AC-2,AU-3

    :param Dict[str, str] tags: Dictionary of tag key-value pairs
    :return: List of extracted control IDs
    :rtype: List[str]
    """
    control_ids = []

    # Check for ControlID or ControlIDs tags
    for tag_key in ["ControlID", "ControlIDs", "Control-ID", "Control-IDs"]:
        if tag_key in tags:
            tag_value = tags[tag_key]
            # Split by comma and clean up
            ids = [cid.strip().upper() for cid in tag_value.split(",") if cid.strip()]
            control_ids.extend(ids)

    return list(set(control_ids))  # Remove duplicates


def get_control_mappings_for_framework(framework: str) -> Dict[str, List[str]]:
    """
    Get control mappings for a specific framework.

    :param str framework: Framework name (e.g., "NIST800-53R5")
    :return: Dictionary mapping rule names to control IDs
    :rtype: Dict[str, List[str]]
    """
    framework_upper = framework.upper().replace("-", "").replace("_", "")

    if "NIST80053" in framework_upper or "NIST800" in framework_upper:
        return NIST_80053_R5_MAPPINGS

    # Add more framework mappings as needed
    # elif "PCI" in framework_upper:
    #     return PCI_DSS_MAPPINGS
    # elif "CIS" in framework_upper:
    #     return CIS_MAPPINGS

    logger.warning(f"No built-in control mappings available for framework: {framework}")
    return {}


def map_rule_to_controls(
    rule_name: str,
    rule_description: Optional[str] = None,
    rule_tags: Optional[Dict[str, str]] = None,
    framework: str = "NIST800-53R5",
) -> List[str]:
    """
    Map an AWS Config rule to control IDs using multiple strategies.

    Priority order:
    1. Framework-specific mappings (conformance pack)
    2. Rule tags (ControlID tag)
    3. Pattern matching in rule name
    4. Pattern matching in rule description

    :param str rule_name: Config rule name
    :param Optional[str] rule_description: Config rule description
    :param Optional[Dict[str, str]] rule_tags: Config rule tags
    :param str framework: Target framework
    :return: List of mapped control IDs
    :rtype: List[str]
    """
    control_ids = []

    # Strategy 1: Check framework-specific mappings
    framework_mappings = get_control_mappings_for_framework(framework)
    if rule_name in framework_mappings:
        control_ids.extend(framework_mappings[rule_name])
        logger.debug(f"Rule '{rule_name}' mapped to controls via framework mappings: {control_ids}")

    # Strategy 2: Check rule tags
    if rule_tags:
        tag_control_ids = extract_control_ids_from_tags(rule_tags)
        if tag_control_ids:
            control_ids.extend(tag_control_ids)
            logger.debug(f"Rule '{rule_name}' mapped to controls via tags: {tag_control_ids}")

    # Strategy 3: Pattern matching in rule name
    if not control_ids:
        name_control_ids = extract_control_ids_from_rule_name(rule_name)
        if name_control_ids:
            control_ids.extend(name_control_ids)
            logger.debug(f"Rule '{rule_name}' mapped to controls via name pattern: {name_control_ids}")

    # Strategy 4: Pattern matching in rule description
    if not control_ids and rule_description:
        desc_control_ids = extract_control_ids_from_rule_name(rule_description)
        if desc_control_ids:
            control_ids.extend(desc_control_ids)
            logger.debug(f"Rule '{rule_name}' mapped to controls via description pattern: {desc_control_ids}")

    # Remove duplicates and sort
    control_ids = sorted(set(control_ids))

    if not control_ids:
        logger.debug(f"Rule '{rule_name}' could not be mapped to any controls")

    return control_ids
