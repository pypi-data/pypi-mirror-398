#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tenable Vulnerability Control Mappings for RegScale Compliance Integration.

This module provides mappings between Tenable vulnerability findings and NIST 800-53 controls.
It uses vulnerability severity, plugin families, and CVE patterns to determine which controls
are being tested and their implementation status.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# Plugin Family Constants
PLUGIN_FAMILY_DEFAULT_UNIX_ACCOUNTS = "Default Unix Accounts"
PLUGIN_FAMILY_DEFAULT_WINDOWS_ACCOUNTS = "Default Windows Accounts"
PLUGIN_FAMILY_SERVICE_DETECTION = "Service detection"
PLUGIN_FAMILY_MISC = "Misc."
PLUGIN_FAMILY_WEB_SERVERS = "Web Servers"

# NIST 800-53 R5 Control Mappings for Tenable Vulnerability Findings
# Mappings based on vulnerability types and their relationship to security controls
TENABLE_CONTROL_MAPPINGS = {
    # Configuration Management Controls
    "CM-6": {
        "name": "Configuration Settings",
        "description": "Establish and document configuration settings for systems",
        "plugin_families": [
            "Policy Compliance",
            "Settings",
            PLUGIN_FAMILY_DEFAULT_UNIX_ACCOUNTS,
            PLUGIN_FAMILY_DEFAULT_WINDOWS_ACCOUNTS,
        ],
        "severity_threshold": "medium",
        "keywords": ["configuration", "baseline", "hardening", "cis benchmark"],
    },
    "CM-7": {
        "name": "Least Functionality",
        "description": "Configure systems to provide only essential capabilities",
        "plugin_families": [PLUGIN_FAMILY_SERVICE_DETECTION, "Port scanners", "General"],
        "severity_threshold": "low",
        "keywords": ["unnecessary service", "unused", "disabled", "default"],
    },
    # Access Control
    "AC-2": {
        "name": "Account Management",
        "description": "Manage system accounts including creation, modification, and removal",
        "plugin_families": [PLUGIN_FAMILY_DEFAULT_UNIX_ACCOUNTS, PLUGIN_FAMILY_DEFAULT_WINDOWS_ACCOUNTS, "Windows"],
        "severity_threshold": "high",
        "keywords": ["default account", "guest account", "shared account", "credential"],
    },
    "AC-3": {
        "name": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access",
        "plugin_families": ["Windows", "Settings"],
        "severity_threshold": "high",
        "keywords": ["permission", "authorization", "privilege", "access control"],
    },
    "AC-17": {
        "name": "Remote Access",
        "description": "Establish usage restrictions and implementation guidance for remote access",
        "plugin_families": [PLUGIN_FAMILY_SERVICE_DETECTION, "RPC", PLUGIN_FAMILY_MISC],
        "severity_threshold": "medium",
        "keywords": ["remote", "ssh", "rdp", "telnet", "vnc"],
    },
    # Identification and Authentication
    "IA-2": {
        "name": "Identification and Authentication",
        "description": "Uniquely identify and authenticate organizational users",
        "plugin_families": [PLUGIN_FAMILY_DEFAULT_UNIX_ACCOUNTS, PLUGIN_FAMILY_DEFAULT_WINDOWS_ACCOUNTS],
        "severity_threshold": "critical",
        "keywords": ["authentication", "password", "credential", "login"],
    },
    "IA-5": {
        "name": "Authenticator Management",
        "description": "Manage system authenticators",
        "plugin_families": ["Windows", "Settings"],
        "severity_threshold": "high",
        "keywords": ["password policy", "password complexity", "password age", "authentication"],
    },
    # System and Communications Protection
    "SC-7": {
        "name": "Boundary Protection",
        "description": "Monitor and control communications at external boundaries",
        "plugin_families": ["Firewalls", "Port scanners", PLUGIN_FAMILY_SERVICE_DETECTION],
        "severity_threshold": "high",
        "keywords": ["firewall", "port", "boundary", "perimeter"],
    },
    "SC-8": {
        "name": "Transmission Confidentiality and Integrity",
        "description": "Protect the confidentiality and integrity of transmitted information",
        "plugin_families": [PLUGIN_FAMILY_WEB_SERVERS, PLUGIN_FAMILY_MISC, "General"],
        "severity_threshold": "medium",
        "keywords": ["encryption", "tls", "ssl", "https", "cipher"],
    },
    "SC-12": {
        "name": "Cryptographic Key Establishment and Management",
        "description": "Establish and manage cryptographic keys",
        "plugin_families": [PLUGIN_FAMILY_WEB_SERVERS, PLUGIN_FAMILY_MISC],
        "severity_threshold": "medium",
        "keywords": ["certificate", "key", "cryptographic", "pki"],
    },
    "SC-13": {
        "name": "Cryptographic Protection",
        "description": "Implement FIPS-validated cryptography",
        "plugin_families": [PLUGIN_FAMILY_WEB_SERVERS, PLUGIN_FAMILY_MISC, "General"],
        "severity_threshold": "high",
        "keywords": ["weak cipher", "insecure protocol", "deprecated", "tls 1.0", "tls 1.1", "ssl"],
    },
    # System and Information Integrity
    "SI-2": {
        "name": "Flaw Remediation",
        "description": "Identify, report, and correct system flaws",
        "plugin_families": ["Windows", PLUGIN_FAMILY_WEB_SERVERS, "Databases", "General"],
        "severity_threshold": "high",
        "keywords": ["vulnerability", "patch", "update", "cve"],
    },
    "SI-3": {
        "name": "Malicious Code Protection",
        "description": "Implement malicious code protection mechanisms",
        "plugin_families": ["Windows"],
        "severity_threshold": "high",
        "keywords": ["antivirus", "malware", "backdoor"],
    },
    "SI-4": {
        "name": "System Monitoring",
        "description": "Monitor the system to detect attacks and indicators of potential attacks",
        "plugin_families": [PLUGIN_FAMILY_SERVICE_DETECTION, PLUGIN_FAMILY_MISC],
        "severity_threshold": "medium",
        "keywords": ["monitoring", "logging", "intrusion detection"],
    },
    # Risk Assessment
    "RA-5": {
        "name": "Vulnerability Monitoring and Scanning",
        "description": "Monitor and scan for vulnerabilities in the system",
        "plugin_families": ["General"],
        "severity_threshold": "info",
        "keywords": ["scan", "assessment", "vulnerability"],
    },
}

# Severity level mappings to implementation status
SEVERITY_TO_STATUS = {
    "critical": "Not Implemented",  # Critical vulns indicate control not working
    "high": "Partially Implemented",  # High vulns indicate partial implementation
    "medium": "Largely Implemented",  # Medium vulns indicate mostly working
    "low": "Implemented",  # Low vulns indicate control is working but could be better
    "info": "Implemented",  # Info findings don't affect implementation status
}


class TenableControlMapper:
    """Map Tenable vulnerability findings to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize Tenable control mapper.

        :param str framework: Compliance framework (default: NIST800-53R5)
        """
        self.framework = framework
        self.mappings = TENABLE_CONTROL_MAPPINGS

    def map_vulnerability_to_controls(self, vulnerability: Dict) -> List[str]:
        """
        Map a vulnerability finding to applicable controls.

        :param Dict vulnerability: Vulnerability data with plugin info
        :return: List of control IDs that apply to this vulnerability
        :rtype: List[str]
        """
        matched_controls = []

        plugin_family = vulnerability.get("pluginFamily", "")
        plugin_name = vulnerability.get("pluginName", "").lower()
        description = vulnerability.get("description", "").lower()

        for control_id, control_data in self.mappings.items():
            # Check plugin family match
            if plugin_family in control_data.get("plugin_families", []):
                matched_controls.append(control_id)
                continue

            # Check keyword match in plugin name or description
            keywords = control_data.get("keywords", [])
            for keyword in keywords:
                if keyword in plugin_name or keyword in description:
                    matched_controls.append(control_id)
                    break

        return list(set(matched_controls))  # Remove duplicates

    def get_implementation_status_from_severity(self, severity: str) -> str:
        """
        Get implementation status based on vulnerability severity.

        :param str severity: Vulnerability severity (Critical, High, Medium, Low, Info)
        :return: Implementation status
        :rtype: str
        """
        severity_lower = severity.lower()
        return SEVERITY_TO_STATUS.get(severity_lower, "Unknown")

    def assess_control_from_vulnerabilities(self, control_id: str, vulnerabilities: List[Dict]) -> Dict[str, any]:
        """
        Assess a control's implementation status based on related vulnerabilities.

        :param str control_id: Control identifier
        :param List[Dict] vulnerabilities: List of vulnerabilities related to this control
        :return: Assessment result with status and details
        :rtype: Dict[str, any]
        """
        if not vulnerabilities:
            return {
                "control_id": control_id,
                "status": "Unknown",
                "vulnerability_count": 0,
                "highest_severity": "None",
                "result": "Unknown",
            }

        # Count vulnerabilities by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info").lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Determine highest severity
        highest_severity = "info"
        for sev in ["critical", "high", "medium", "low"]:
            if severity_counts[sev] > 0:
                highest_severity = sev
                break

        # Determine implementation status based on highest severity
        status = self.get_implementation_status_from_severity(highest_severity)

        # Determine Pass/Fail result
        # Controls with Critical or High vulnerabilities are considered "Fail"
        result = "Fail" if highest_severity in ["critical", "high"] else "Pass"

        return {
            "control_id": control_id,
            "status": status,
            "vulnerability_count": len(vulnerabilities),
            "highest_severity": highest_severity,
            "severity_breakdown": severity_counts,
            "result": result,
        }

    def get_mapped_controls(self) -> List[str]:
        """
        Get list of all control IDs mapped for this framework.

        :return: List of control IDs
        :rtype: List[str]
        """
        return list(self.mappings.keys())

    def get_control_info(self, control_id: str) -> Optional[Dict]:
        """
        Get information about a specific control mapping.

        :param str control_id: Control identifier
        :return: Control mapping information or None
        :rtype: Optional[Dict]
        """
        return self.mappings.get(control_id)
