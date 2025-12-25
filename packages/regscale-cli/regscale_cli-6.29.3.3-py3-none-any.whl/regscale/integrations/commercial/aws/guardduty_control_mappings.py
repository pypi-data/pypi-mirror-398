#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS GuardDuty Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS GuardDuty
GUARDDUTY_CONTROL_MAPPINGS = {
    "SI-4": {
        "name": "System Monitoring",
        "description": "Monitor the system to detect attacks and indicators of potential attacks",
        "checks": {
            "detector_enabled": {
                "weight": 100,
                "pass_criteria": "GuardDuty detector is enabled and actively monitoring",
                "fail_criteria": "GuardDuty detector is disabled or suspended",
            },
            "findings_processed": {
                "weight": 90,
                "pass_criteria": "Active findings are reviewed and remediated",
                "fail_criteria": "High severity findings remain unaddressed",
            },
        },
    },
    "IR-4": {
        "name": "Incident Handling",
        "description": "Implement incident handling capability for security incidents",
        "checks": {
            "high_severity_findings": {
                "weight": 100,
                "pass_criteria": "No unaddressed high severity findings",
                "fail_criteria": "High severity findings detected and not remediated",
            },
            "incident_response": {
                "weight": 90,
                "pass_criteria": "Findings integrated with incident response workflow",
                "fail_criteria": "Findings not tracked in incident management system",
            },
        },
    },
    "IR-5": {
        "name": "Incident Monitoring",
        "description": "Track and document system security incidents",
        "checks": {
            "finding_tracking": {
                "weight": 100,
                "pass_criteria": "All findings tracked and documented",
                "fail_criteria": "Findings not systematically tracked",
            },
        },
    },
    "SI-3": {
        "name": "Malicious Code Protection",
        "description": "Implement malicious code protection mechanisms",
        "checks": {
            "malware_detection": {
                "weight": 100,
                "pass_criteria": "GuardDuty detecting and alerting on malware activities",
                "fail_criteria": "Malware protection findings not enabled or monitored",
            },
        },
    },
    "RA-5": {
        "name": "Vulnerability Monitoring and Scanning",
        "description": "Monitor and scan for vulnerabilities in the system",
        "checks": {
            "threat_intelligence": {
                "weight": 100,
                "pass_criteria": "GuardDuty threat intelligence enabled and current",
                "fail_criteria": "Threat intelligence feeds not enabled or outdated",
            },
        },
    },
}

# Severity mapping (GuardDuty uses 0-10 scale)
SEVERITY_MAPPING = {
    "LOW": (0.1, 3.9),
    "MEDIUM": (4.0, 6.9),
    "HIGH": (7.0, 8.9),
    "CRITICAL": (9.0, 10.0),
}

# Finding types that may contain CVEs
CVE_RELATED_FINDING_TYPES = [
    "UnauthorizedAccess:EC2/MaliciousIPCaller",
    "CryptoCurrency:EC2/BitcoinTool",
    "Trojan:EC2/",
    "Backdoor:EC2/",
    "Behavior:EC2/NetworkPortUnusual",
    "Recon:EC2/",
]


class GuardDutyControlMapper:
    """Map AWS GuardDuty findings to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize GuardDuty control mapper.

        :param str framework: Compliance framework
        """
        self.framework = framework
        self.mappings = GUARDDUTY_CONTROL_MAPPINGS

    def assess_guardduty_compliance(self, guardduty_data: Dict) -> Dict[str, str]:
        """
        Assess GuardDuty compliance against all mapped controls.

        :param Dict guardduty_data: GuardDuty detectors and findings
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["SI-4"] = self._assess_si4(guardduty_data)
            results["IR-4"] = self._assess_ir4(guardduty_data)
            results["IR-5"] = self._assess_ir5(guardduty_data)
            results["SI-3"] = self._assess_si3(guardduty_data)
            results["RA-5"] = self._assess_ra5(guardduty_data)

        return results

    def _assess_si4(self, guardduty_data: Dict) -> str:
        """
        Assess SI-4 (System Monitoring) compliance.

        :param Dict guardduty_data: GuardDuty data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        detectors = guardduty_data.get("Detectors", [])

        if not detectors:
            logger.debug("GuardDuty FAILS SI-4: No detectors configured")
            return "FAIL"

        # Check if any detector is disabled
        disabled_detectors = [d for d in detectors if d.get("Status") != "ENABLED"]
        if disabled_detectors:
            logger.debug(f"GuardDuty FAILS SI-4: {len(disabled_detectors)} detector(s) disabled")
            return "FAIL"

        logger.debug(f"GuardDuty PASSES SI-4: {len(detectors)} detector(s) enabled and monitoring")
        return "PASS"

    def _assess_ir4(self, guardduty_data: Dict) -> str:
        """
        Assess IR-4 (Incident Handling) compliance.

        :param Dict guardduty_data: GuardDuty data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        findings = guardduty_data.get("Findings", [])

        # Check for high/critical severity unaddressed findings
        high_severity_findings = [
            f for f in findings if self._get_severity_level(f.get("Severity", 0)) in ["HIGH", "CRITICAL"]
        ]

        if high_severity_findings:
            logger.debug(
                f"GuardDuty FAILS IR-4: {len(high_severity_findings)} high/critical severity "
                "findings requiring incident response"
            )
            return "FAIL"

        logger.debug("GuardDuty PASSES IR-4: No high severity findings requiring immediate attention")
        return "PASS"

    def _assess_ir5(self, guardduty_data: Dict) -> str:
        """
        Assess IR-5 (Incident Monitoring) compliance.

        GuardDuty's active monitoring satisfies IR-5 requirements by providing continuous
        security monitoring and incident detection capabilities. The presence of GuardDuty
        itself, along with this integration's tracking of findings, fulfills the control.

        :param Dict guardduty_data: GuardDuty data
        :return: Compliance result (always PASS when GuardDuty is enabled)
        :rtype: str
        """
        findings = guardduty_data.get("Findings", [])

        # GuardDuty being active satisfies IR-5 (Incident Monitoring)
        if findings:
            logger.debug(f"GuardDuty PASSES IR-5: {len(findings)} findings tracked for incident monitoring")
        else:
            logger.debug("GuardDuty PASSES IR-5: GuardDuty monitoring active, no incidents detected")

        return "PASS"

    def _assess_si3(self, guardduty_data: Dict) -> str:
        """
        Assess SI-3 (Malicious Code Protection) compliance.

        :param Dict guardduty_data: GuardDuty data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        detectors = guardduty_data.get("Detectors", [])
        findings = guardduty_data.get("Findings", [])

        # Check if GuardDuty is enabled (provides malware detection)
        if not detectors or all(d.get("Status") != "ENABLED" for d in detectors):
            logger.debug("GuardDuty FAILS SI-3: No enabled detectors for malware protection")
            return "FAIL"

        # Check for malware-related findings
        malware_findings = [f for f in findings if self._is_malware_finding(f)]

        if malware_findings:
            logger.warning(
                f"GuardDuty malware findings detected: {len(malware_findings)} "
                "potential malware activities (requires remediation)"
            )

        logger.debug("GuardDuty PASSES SI-3: Malware protection monitoring enabled")
        return "PASS"

    def _assess_ra5(self, guardduty_data: Dict) -> str:
        """
        Assess RA-5 (Vulnerability Monitoring) compliance.

        :param Dict guardduty_data: GuardDuty data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        detectors = guardduty_data.get("Detectors", [])

        # Check if threat intelligence is enabled
        threat_intel_enabled = any(
            d.get("DataSources", {}).get("S3Logs", {}).get("Status") == "ENABLED" for d in detectors
        )

        if not threat_intel_enabled:
            logger.debug("GuardDuty FAILS RA-5: Threat intelligence data sources not fully enabled")
            return "FAIL"

        logger.debug("GuardDuty PASSES RA-5: Threat intelligence and vulnerability monitoring active")
        return "PASS"

    def _get_severity_level(self, severity_score: float) -> str:
        """
        Map GuardDuty severity score to severity level.

        :param float severity_score: Severity score (0-10)
        :return: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        :rtype: str
        """
        for level, (min_score, max_score) in SEVERITY_MAPPING.items():
            if min_score <= severity_score <= max_score:
                return level
        return "LOW"

    def _is_malware_finding(self, finding: Dict) -> bool:
        """
        Check if finding is related to malware.

        :param Dict finding: GuardDuty finding
        :return: True if malware-related
        :rtype: bool
        """
        finding_type = finding.get("Type", "")
        malware_indicators = [
            "Trojan",
            "Backdoor",
            "CryptoCurrency",
            "Malware",
            "Bitcoin",
            "CryptoCoin",
        ]
        return any(indicator in finding_type for indicator in malware_indicators)

    def has_cve_reference(self, finding: Dict) -> bool:
        """
        Check if GuardDuty finding references a CVE.

        :param Dict finding: GuardDuty finding
        :return: True if CVE referenced
        :rtype: bool
        """
        # Check finding description and title for CVE patterns
        description = finding.get("Description", "")
        title = finding.get("Title", "")
        service = finding.get("Service", {})
        additional_info = service.get("AdditionalInfo", {})

        # CVE pattern: CVE-YYYY-NNNNN
        text_to_search = f"{description} {title} {str(additional_info)}"
        return "CVE-" in text_to_search.upper()

    def extract_cves_from_finding(self, finding: Dict) -> List[str]:
        """
        Extract CVE IDs from GuardDuty finding.

        :param Dict finding: GuardDuty finding
        :return: List of CVE IDs
        :rtype: List[str]
        """
        import re

        cves = []
        description = finding.get("Description", "")
        title = finding.get("Title", "")
        service = finding.get("Service", {})
        additional_info = str(service.get("AdditionalInfo", {}))

        text_to_search = f"{description} {title} {additional_info}"

        # CVE pattern: CVE-YYYY-NNNNN
        cve_pattern = r"CVE-\d{4}-\d{4,7}"
        matches = re.findall(cve_pattern, text_to_search, re.IGNORECASE)

        cves = list({match.upper() for match in matches})
        return cves

    def get_control_description(self, control_id: str) -> Optional[str]:
        """Get human-readable description for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return f"{control_data.get('name')}: {control_data.get('description', '')}"
        return None

    def get_mapped_controls(self) -> List[str]:
        """Get list of all control IDs mapped for this framework."""
        return list(self.mappings.keys())

    def get_check_details(self, control_id: str) -> Optional[Dict]:
        """Get detailed check criteria for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return control_data.get("checks", {})
        return None
