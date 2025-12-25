#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Control Mappings Package.

This package contains control mappings for various compliance frameworks:
- NIST 800-53 Rev 5
- CIS GCP Benchmark
- FedRAMP
- PCI-DSS
- SOC2

Each mapping file defines the relationship between GCP Security Command Center
finding categories and compliance control IDs.
"""

import logging
from typing import Dict, List, Optional

from regscale.integrations.commercial.gcp.control_mappings.nist_800_53 import (
    NIST_800_53_R5_MAPPINGS,
    get_controls_for_category as nist_get_controls_for_category,
    get_categories_for_control as nist_get_categories_for_control,
    get_control_name,
    get_control_description,
    get_evidence_sources_for_control,
    get_all_control_ids,
    get_all_scc_categories,
    get_control_family,
    get_controls_by_family,
    get_mapping_summary,
)

logger = logging.getLogger("regscale")

# Supported frameworks for GCP Security Command Center control mappings
SUPPORTED_FRAMEWORKS = ["NIST800-53R5", "CIS_GCP", "FedRAMP", "PCI-DSS", "SOC2"]

# Framework mappings dictionary - populated lazily when framework resolvers are created
FRAMEWORK_MAPPINGS: Dict[str, dict] = {}


def _get_nist_800_53_r5_mappings() -> Dict[str, Dict]:
    """
    Get NIST 800-53 Rev 5 control mappings for GCP SCC categories.

    Returns control ID to category mappings for the NIST 800-53 R5 framework.
    This function transforms the comprehensive NIST_800_53_R5_MAPPINGS into
    the format expected by ControlFrameworkResolver (control_id -> category -> info).

    :return: Dictionary mapping control IDs to SCC category information
    :rtype: Dict[str, Dict]
    """
    # Transform NIST_800_53_R5_MAPPINGS to the format used by ControlFrameworkResolver
    # From: control_id -> {name, description, scc_categories, asset_types, evidence_sources}
    # To: control_id -> {category -> {severity, description}}
    result: Dict[str, Dict] = {}

    for control_id, mapping in NIST_800_53_R5_MAPPINGS.items():
        control_key = control_id.lower()
        result[control_key] = {}

        control_description = str(mapping.get("description", ""))
        categories = mapping.get("scc_categories", [])

        if isinstance(categories, list):
            for category in categories:
                result[control_key][str(category)] = {
                    "severity": "MEDIUM",  # Default severity, actual severity comes from SCC findings
                    "description": control_description,
                }

    # Also include mappings from the legacy control_tests for backward compatibility
    try:
        from regscale.integrations.commercial.gcp.control_tests import gcp_control_tests

        for legacy_control_id, legacy_categories in gcp_control_tests.items():
            legacy_control_key = legacy_control_id.lower()
            if legacy_control_key not in result:
                result[legacy_control_key] = {}

            for legacy_category, legacy_info in legacy_categories.items():
                if legacy_category not in result[legacy_control_key]:
                    result[legacy_control_key][legacy_category] = legacy_info
    except ImportError:
        logger.debug("Could not import gcp_control_tests for backward compatibility")

    return result


def _get_cis_gcp_mappings() -> Dict[str, Dict]:
    """
    Get CIS GCP Benchmark control mappings.

    CIS GCP mappings align with the CIS Google Cloud Platform Foundation Benchmark.

    :return: Dictionary mapping CIS control IDs to SCC category information
    :rtype: Dict[str, Dict]
    """
    # CIS GCP Benchmark mappings - these align with CIS GCP Foundation Benchmark v2.0
    return {
        "1.1": {
            "PUBLIC_BUCKET_ACL": {
                "severity": "HIGH",
                "description": "Ensure corporate login credentials are used instead of Gmail accounts",
            },
        },
        "1.4": {
            "SERVICE_ACCOUNT_KEY_NOT_ROTATED": {
                "severity": "MEDIUM",
                "description": "Ensure service account keys are rotated within 90 days",
            },
        },
        "1.5": {
            "USER_MANAGED_SERVICE_ACCOUNT_KEY": {
                "severity": "MEDIUM",
                "description": "Ensure user-managed service account keys are managed properly",
            },
        },
        "1.6": {
            "OVER_PRIVILEGED_SERVICE_ACCOUNT_USER": {
                "severity": "MEDIUM",
                "description": "Ensure service account has no admin privileges",
            },
        },
        "2.1": {
            "AUDIT_LOGGING_DISABLED": {
                "severity": "LOW",
                "description": "Ensure Cloud Audit Logging is configured properly",
            },
        },
        "3.1": {
            "DEFAULT_NETWORK": {
                "severity": "MEDIUM",
                "description": "Ensure default network does not exist in a project",
            },
        },
        "3.6": {
            "OPEN_SSH_PORT": {
                "severity": "HIGH",
                "description": "Ensure SSH access is restricted from the internet",
            },
        },
        "3.7": {
            "OPEN_RDP_PORT": {
                "severity": "HIGH",
                "description": "Ensure RDP access is restricted from the internet",
            },
        },
        "4.1": {
            "COMPUTE_PROJECT_WIDE_SSH_KEYS_ALLOWED": {
                "severity": "MEDIUM",
                "description": "Ensure oslogin is enabled for a project",
            },
        },
        "4.3": {
            "COMPUTE_SECURE_BOOT_DISABLED": {
                "severity": "MEDIUM",
                "description": "Ensure 'Enable connecting to serial ports' is not enabled",
            },
        },
        "4.4": {
            "IP_FORWARDING_ENABLED": {
                "severity": "MEDIUM",
                "description": "Ensure IP forwarding is not enabled on instances",
            },
        },
        "5.1": {
            "KMS_KEY_NOT_ROTATED": {
                "severity": "MEDIUM",
                "description": "Ensure Cloud KMS cryptokeys are rotated within 90 days",
            },
        },
        "5.2": {
            "KMS_ROLE_SEPARATION": {
                "severity": "MEDIUM",
                "description": "Ensure separation of duties for KMS-related roles",
            },
        },
        "6.1": {
            "PUBLIC_SQL_INSTANCE": {
                "severity": "HIGH",
                "description": "Ensure Cloud SQL database instance requires SSL",
            },
        },
        "6.2": {
            "SQL_NO_ROOT_PASSWORD": {
                "severity": "HIGH",
                "description": "Ensure Cloud SQL instance requires all incoming connections to use SSL",
            },
        },
        "6.3": {
            "SSL_NOT_ENFORCED": {
                "severity": "HIGH",
                "description": "Ensure Cloud SQL instances are not open to the world",
            },
        },
        "7.1": {
            "PUBLIC_BUCKET_ACL": {
                "severity": "HIGH",
                "description": "Ensure Cloud Storage bucket is not anonymously or publicly accessible",
            },
        },
    }


def _get_fedramp_mappings() -> Dict[str, Dict]:
    """
    Get FedRAMP control mappings.

    FedRAMP mappings align NIST 800-53 controls with FedRAMP baselines.

    :return: Dictionary mapping FedRAMP control IDs to SCC category information
    :rtype: Dict[str, Dict]
    """
    # FedRAMP uses NIST 800-53 controls with specific parameter values
    # For simplicity, we map to the same categories as NIST 800-53 R5
    return _get_nist_800_53_r5_mappings()


def _get_pci_dss_mappings() -> Dict[str, Dict]:
    """
    Get PCI-DSS control mappings.

    PCI-DSS mappings align with Payment Card Industry Data Security Standard.

    :return: Dictionary mapping PCI-DSS requirements to SCC category information
    :rtype: Dict[str, Dict]
    """
    return {
        "1.1": {
            "OPEN_FIREWALL": {
                "severity": "HIGH",
                "description": "Install and maintain a firewall configuration to protect cardholder data",
            },
            "DEFAULT_NETWORK": {
                "severity": "MEDIUM",
                "description": "Ensure firewall and router configurations restrict connections",
            },
        },
        "1.2": {
            "OPEN_RDP_PORT": {
                "severity": "HIGH",
                "description": "Build firewall and router configurations that restrict connections",
            },
            "OPEN_SSH_PORT": {
                "severity": "HIGH",
                "description": "Restrict inbound and outbound traffic to that which is necessary",
            },
        },
        "2.1": {
            "SQL_NO_ROOT_PASSWORD": {
                "severity": "HIGH",
                "description": "Always change vendor-supplied defaults",
            },
            "DEFAULT_SERVICE_ACCOUNT_USED": {
                "severity": "MEDIUM",
                "description": "Remove or disable unnecessary default accounts",
            },
        },
        "3.4": {
            "DISK_ENCRYPTION_DISABLED": {
                "severity": "HIGH",
                "description": "Render PAN unreadable using strong cryptography",
            },
        },
        "4.1": {
            "SSL_NOT_ENFORCED": {
                "severity": "HIGH",
                "description": "Use strong cryptography and security protocols",
            },
            "WEAK_SSL_POLICY": {
                "severity": "MEDIUM",
                "description": "Never send unprotected PANs over end-user messaging technologies",
            },
        },
        "6.5": {
            "PUBLIC_SQL_INSTANCE": {
                "severity": "HIGH",
                "description": "Address common coding vulnerabilities in development processes",
            },
        },
        "7.1": {
            "PUBLIC_BUCKET_ACL": {
                "severity": "HIGH",
                "description": "Limit access to system components to only those individuals whose job requires access",
            },
            "OVER_PRIVILEGED_ACCOUNT": {
                "severity": "MEDIUM",
                "description": "Restrict access to privileged user IDs to least privileges necessary",
            },
        },
        "8.1": {
            "MFA_NOT_ENFORCED": {
                "severity": "HIGH",
                "description": "Define and implement policies for identification and authentication management",
            },
        },
        "10.1": {
            "AUDIT_LOGGING_DISABLED": {
                "severity": "LOW",
                "description": "Implement audit trails to link all access to system components",
            },
            "FLOW_LOGS_DISABLED": {
                "severity": "LOW",
                "description": "Track and monitor all access to network resources",
            },
        },
    }


def _get_soc2_mappings() -> Dict[str, Dict]:
    """
    Get SOC2 Trust Services Criteria control mappings.

    SOC2 mappings align with AICPA Trust Services Criteria.

    :return: Dictionary mapping SOC2 criteria to SCC category information
    :rtype: Dict[str, Dict]
    """
    return {
        "CC5.1": {
            "OVER_PRIVILEGED_ACCOUNT": {
                "severity": "MEDIUM",
                "description": "Logical access security software and policies",
            },
            "PRIMITIVE_ROLES_USED": {
                "severity": "MEDIUM",
                "description": "Authorization and access control policies",
            },
        },
        "CC5.2": {
            "NON_ORG_IAM_MEMBER": {
                "severity": "HIGH",
                "description": "New user registration and authorization",
            },
        },
        "CC6.1": {
            "PUBLIC_BUCKET_ACL": {
                "severity": "HIGH",
                "description": "Logical and physical access controls",
            },
            "PUBLIC_DATASET": {
                "severity": "HIGH",
                "description": "Restriction of data access",
            },
        },
        "CC6.2": {
            "MFA_NOT_ENFORCED": {
                "severity": "HIGH",
                "description": "Multi-factor authentication",
            },
        },
        "CC6.3": {
            "KMS_ROLE_SEPARATION": {
                "severity": "MEDIUM",
                "description": "Role-based access and segregation of duties",
            },
            "SERVICE_ACCOUNT_ROLE_SEPARATION": {
                "severity": "MEDIUM",
                "description": "Segregation of duties for privileged access",
            },
        },
        "CC6.6": {
            "OPEN_SSH_PORT": {
                "severity": "HIGH",
                "description": "Boundary protection and network security",
            },
            "OPEN_RDP_PORT": {
                "severity": "HIGH",
                "description": "Network access restrictions",
            },
            "PUBLIC_IP_ADDRESS": {
                "severity": "HIGH",
                "description": "Network boundary protection",
            },
        },
        "CC6.7": {
            "SSL_NOT_ENFORCED": {
                "severity": "HIGH",
                "description": "Transmission encryption",
            },
            "WEAK_SSL_POLICY": {
                "severity": "MEDIUM",
                "description": "Encryption of data in transit",
            },
        },
        "CC6.8": {
            "DISK_ENCRYPTION_DISABLED": {
                "severity": "HIGH",
                "description": "Encryption of data at rest",
            },
            "KMS_KEY_NOT_ROTATED": {
                "severity": "MEDIUM",
                "description": "Cryptographic key management",
            },
        },
        "CC7.1": {
            "AUDIT_LOGGING_DISABLED": {
                "severity": "LOW",
                "description": "System monitoring and detection",
            },
            "FLOW_LOGS_DISABLED": {
                "severity": "LOW",
                "description": "Network monitoring",
            },
        },
        "CC7.2": {
            "FIREWALL_RULE_LOGGING_DISABLED": {
                "severity": "MEDIUM",
                "description": "Anomaly detection and monitoring",
            },
        },
        "A1.1": {
            "AUTO_BACKUP_DISABLED": {
                "severity": "MEDIUM",
                "description": "System availability and backup",
            },
        },
        "A1.2": {
            "LOCKED_RETENTION_POLICY_NOT_SET": {
                "severity": "LOW",
                "description": "Data retention policies",
            },
            "OBJECT_VERSIONING_DISABLED": {
                "severity": "LOW",
                "description": "Data recovery capabilities",
            },
        },
    }


def _load_framework_mappings(framework: str) -> Dict[str, Dict]:
    """
    Load mappings for a specific framework.

    :param str framework: Framework name (e.g., "NIST800-53R5", "CIS_GCP")
    :return: Dictionary of control mappings for the framework
    :rtype: Dict[str, Dict]
    """
    framework_upper = framework.upper().replace("-", "").replace("_", "")

    if "NIST80053" in framework_upper or "NIST800" in framework_upper:
        return _get_nist_800_53_r5_mappings()

    if "CIS" in framework_upper and "GCP" in framework_upper:
        return _get_cis_gcp_mappings()

    if "FEDRAMP" in framework_upper:
        return _get_fedramp_mappings()

    if "PCI" in framework_upper or "DSS" in framework_upper:
        return _get_pci_dss_mappings()

    if "SOC2" in framework_upper or "SOC 2" in framework_upper:
        return _get_soc2_mappings()

    logger.warning("Unsupported framework: %s. Using NIST 800-53 R5 mappings.", framework)
    return _get_nist_800_53_r5_mappings()


class ControlFrameworkResolver:
    """Resolves control mappings across multiple compliance frameworks.

    This class provides methods to look up controls for GCP Security Command Center
    finding categories and to reverse-lookup categories for given control IDs.

    Supported frameworks:
    - NIST800-53R5: NIST 800-53 Revision 5
    - CIS_GCP: CIS GCP Foundation Benchmark
    - FedRAMP: Federal Risk and Authorization Management Program
    - PCI-DSS: Payment Card Industry Data Security Standard
    - SOC2: Service Organization Control 2

    Example usage:
        resolver = ControlFrameworkResolver(framework="NIST800-53R5")
        controls = resolver.get_controls_for_category("PUBLIC_BUCKET_ACL")
        categories = resolver.get_categories_for_control("ac-2")
    """

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize the ControlFrameworkResolver.

        :param str framework: Compliance framework name (default: "NIST800-53R5")
        """
        self.framework = framework
        self._mappings: Dict[str, Dict] = {}
        self._category_to_controls: Dict[str, List[str]] = {}
        self._control_to_categories: Dict[str, List[str]] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load mappings for the selected framework and build reverse lookup indexes."""
        self._mappings = _load_framework_mappings(self.framework)

        # Build reverse lookup: category -> list of control IDs
        self._category_to_controls = {}
        # Build lookup: control_id (lowercase) -> list of categories
        self._control_to_categories = {}

        for control_id, categories in self._mappings.items():
            control_key = control_id.lower()
            if control_key not in self._control_to_categories:
                self._control_to_categories[control_key] = []

            for category in categories:
                # Add category to control's list
                if category not in self._control_to_categories[control_key]:
                    self._control_to_categories[control_key].append(category)

                # Add control to category's list
                if category not in self._category_to_controls:
                    self._category_to_controls[category] = []
                if control_key not in self._category_to_controls[category]:
                    self._category_to_controls[category].append(control_key)

        logger.debug(
            "Loaded %d control mappings for framework %s with %d unique categories",
            len(self._mappings),
            self.framework,
            len(self._category_to_controls),
        )

    def get_controls_for_category(self, category: str) -> List[str]:
        """
        Get all control IDs that map to a given SCC finding category.

        :param str category: SCC finding category (e.g., "PUBLIC_BUCKET_ACL")
        :return: List of control IDs (lowercase) that map to this category
        :rtype: List[str]
        """
        category_upper = category.upper()
        return self._category_to_controls.get(category_upper, [])

    def get_categories_for_control(self, control_id: str) -> List[str]:
        """
        Get all SCC categories that map to a given control ID.

        :param str control_id: Control ID (e.g., "AC-2", "ac-2")
        :return: List of SCC category names that map to this control
        :rtype: List[str]
        """
        control_key = control_id.lower()
        return self._control_to_categories.get(control_key, [])

    def get_control_info(self, control_id: str) -> Optional[Dict]:
        """
        Get full control mapping info for a control ID.

        Returns the complete mapping dictionary for a control ID, including
        all categories and their severity/description information.

        :param str control_id: Control ID (e.g., "AC-2", "ac-2")
        :return: Dictionary of category mappings for the control, or None if not found
        :rtype: Optional[Dict]
        """
        control_key = control_id.lower()

        # Look up the control in our mappings (trying both lowercase and original case)
        if control_key in self._mappings:
            return self._mappings[control_key]

        # Try to find it case-insensitively
        for mapping_control_id, mapping_info in self._mappings.items():
            if mapping_control_id.lower() == control_key:
                return mapping_info

        return None

    def get_evidence_sources(self, control_id: str) -> List[str]:
        """
        Get evidence sources for a control.

        Evidence sources are derived from the SCC categories that map to the control.
        Each category represents a type of finding that can provide evidence for
        control compliance.

        :param str control_id: Control ID (e.g., "AC-2")
        :return: List of evidence source names (SCC category names)
        :rtype: List[str]
        """
        return self.get_categories_for_control(control_id)

    def get_all_categories(self) -> List[str]:
        """
        Get all unique SCC categories across all control mappings.

        :return: Sorted list of all SCC category names
        :rtype: List[str]
        """
        return sorted(self._category_to_controls.keys())

    def get_all_controls(self) -> List[str]:
        """
        Get all control IDs in the current framework mappings.

        :return: Sorted list of all control IDs (lowercase)
        :rtype: List[str]
        """
        return sorted(self._control_to_categories.keys())

    def get_category_info(self, category: str, control_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get detailed information about an SCC category.

        :param str category: SCC category name (e.g., "PUBLIC_BUCKET_ACL")
        :param Optional[str] control_id: Optional control ID to get info specific to that mapping
        :return: Dictionary with severity and description, or None if not found
        :rtype: Optional[Dict]
        """
        category_upper = category.upper()

        if control_id:
            # Get info for specific control-category pair
            control_info = self.get_control_info(control_id)
            if control_info and category_upper in control_info:
                return control_info[category_upper]
        else:
            # Find the first control that has this category and return its info
            for ctrl_info in self._mappings.values():
                if category_upper in ctrl_info:
                    return ctrl_info[category_upper]

        return None

    def assess_category_compliance(self, category: str, finding_present: bool = True) -> Dict[str, str]:
        """
        Assess compliance status for all controls mapped to a category.

        :param str category: SCC category name
        :param bool finding_present: True if finding is present (indicates non-compliance)
        :return: Dictionary mapping control IDs to compliance status (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        controls = self.get_controls_for_category(category)
        status = "FAIL" if finding_present else "PASS"

        return dict.fromkeys(controls, status)

    @classmethod
    def get_supported_frameworks(cls) -> List[str]:
        """
        Return list of supported framework names.

        :return: List of supported framework identifiers
        :rtype: List[str]
        """
        return SUPPORTED_FRAMEWORKS.copy()


__all__ = [
    "ControlFrameworkResolver",
    "FRAMEWORK_MAPPINGS",
    "SUPPORTED_FRAMEWORKS",
    "NIST_800_53_R5_MAPPINGS",
    "nist_get_controls_for_category",
    "nist_get_categories_for_control",
    "get_control_name",
    "get_control_description",
    "get_evidence_sources_for_control",
    "get_all_control_ids",
    "get_all_scc_categories",
    "get_control_family",
    "get_controls_by_family",
    "get_mapping_summary",
]
