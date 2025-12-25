#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NIST 800-53 Rev 5 Control Mappings for GCP Security Command Center.

This module provides mappings between NIST 800-53 Rev 5 controls and GCP Security
Command Center (SCC) finding categories and asset types. These mappings enable
automated compliance assessment by correlating GCP security findings with their
corresponding NIST controls.

The mappings cover the following control families:
- AC (Access Control): AC-2, AC-3, AC-4, AC-5, AC-6, AC-17
- AU (Audit and Accountability): AU-2, AU-3, AU-6, AU-9, AU-12
- CA (Assessment, Authorization, and Monitoring): CA-7
- CM (Configuration Management): CM-2, CM-6, CM-7, CM-8
- CP (Contingency Planning): CP-9
- IA (Identification and Authentication): IA-2, IA-4, IA-5
- SC (System and Communications Protection): SC-7, SC-8, SC-12, SC-13, SC-28
- SI (System and Information Integrity): SI-2, SI-3, SI-4
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("regscale")

# Type alias for the mapping structure
ControlMapping = Dict[str, Union[str, List[str]]]

# GCP Asset Type Constants
ASSET_TYPE_SERVICE_ACCOUNT = "iam.googleapis.com/ServiceAccount"
ASSET_TYPE_SERVICE_ACCOUNT_KEY = "iam.googleapis.com/ServiceAccountKey"
ASSET_TYPE_PROJECT = "cloudresourcemanager.googleapis.com/Project"
ASSET_TYPE_BUCKET = "storage.googleapis.com/Bucket"
ASSET_TYPE_SQL_INSTANCE = "sqladmin.googleapis.com/Instance"
ASSET_TYPE_SUBNETWORK = "compute.googleapis.com/Subnetwork"
ASSET_TYPE_NETWORK = "compute.googleapis.com/Network"
ASSET_TYPE_FIREWALL = "compute.googleapis.com/Firewall"
ASSET_TYPE_CRYPTO_KEY = "cloudkms.googleapis.com/CryptoKey"
ASSET_TYPE_INSTANCE = "compute.googleapis.com/Instance"
ASSET_TYPE_CLUSTER = "container.googleapis.com/Cluster"
ASSET_TYPE_LOG_SINK = "logging.googleapis.com/LogSink"
ASSET_TYPE_DISK = "compute.googleapis.com/Disk"

# NIST 800-53 Rev 5 Control Mappings for GCP Security Command Center
NIST_800_53_R5_MAPPINGS: Dict[str, ControlMapping] = {
    # Access Control (AC) Family
    "AC-2": {
        "name": "Account Management",
        "description": "Manage system accounts including creation, enabling, modification, and removal",
        "scc_categories": [
            "ADMIN_SERVICE_ACCOUNT",
            "USER_MANAGED_SERVICE_ACCOUNT_KEY",
            "SERVICE_ACCOUNT_KEY_NOT_ROTATED",
            "DEFAULT_SERVICE_ACCOUNT_USED",
            "OVER_PRIVILEGED_SERVICE_ACCOUNT_USER",
            "MFA_NOT_ENFORCED",
        ],
        "asset_types": [
            ASSET_TYPE_SERVICE_ACCOUNT,
            ASSET_TYPE_SERVICE_ACCOUNT_KEY,
            ASSET_TYPE_PROJECT,
        ],
        "evidence_sources": ["iam", "logging", "cloudresourcemanager"],
    },
    "AC-3": {
        "name": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access to information and system resources",
        "scc_categories": [
            "PUBLIC_BUCKET_ACL",
            "BUCKET_POLICY_ONLY_DISABLED",
            "NON_ORG_IAM_MEMBER",
            "SQL_NO_ROOT_PASSWORD",
            "PUBLIC_DATASET",
            "ALLOYDB_PUBLIC_IP",
            "CLOUD_SQL_PUBLIC_IP",
        ],
        "asset_types": [
            ASSET_TYPE_BUCKET,
            ASSET_TYPE_SQL_INSTANCE,
            "bigquery.googleapis.com/Dataset",
            "iam.googleapis.com/Role",
        ],
        "evidence_sources": ["storage", "iam", "sqladmin", "bigquery"],
    },
    "AC-4": {
        "name": "Information Flow Enforcement",
        "description": "Enforce approved authorizations for controlling the flow of information within the system",
        "scc_categories": [
            "VPC_FLOW_LOGS_DISABLED",
            "FLOW_LOGS_DISABLED",
            "FIREWALL_RULE_LOGGING_DISABLED",
            "PRIVATE_GOOGLE_ACCESS_DISABLED",
            "LEGACY_NETWORK",
        ],
        "asset_types": [
            ASSET_TYPE_SUBNETWORK,
            ASSET_TYPE_NETWORK,
            ASSET_TYPE_FIREWALL,
        ],
        "evidence_sources": ["compute", "logging", "networkservices"],
    },
    "AC-5": {
        "name": "Separation of Duties",
        "description": "Separate duties of individuals to prevent malicious activity",
        "scc_categories": [
            "KMS_ROLE_SEPARATION",
            "SERVICE_ACCOUNT_ROLE_SEPARATION",
            "PRIMITIVE_ROLES_USED",
            "KMS_PROJECT_HAS_OWNER",
        ],
        "asset_types": [
            ASSET_TYPE_CRYPTO_KEY,
            ASSET_TYPE_SERVICE_ACCOUNT,
            ASSET_TYPE_PROJECT,
        ],
        "evidence_sources": ["iam", "cloudkms"],
    },
    "AC-6": {
        "name": "Least Privilege",
        "description": "Employ the principle of least privilege",
        "scc_categories": [
            "FULL_API_ACCESS",
            "OVER_PRIVILEGED_SERVICE_ACCOUNT_USER",
            "PRIMITIVE_ROLES_USED",
            "OVER_PRIVILEGED_ACCOUNT",
            "KMS_PROJECT_HAS_OWNER",
            "ADMIN_SERVICE_ACCOUNT",
            "OVER_PRIVILEGED_SCOPES",
        ],
        "asset_types": [
            ASSET_TYPE_SERVICE_ACCOUNT,
            "iam.googleapis.com/Role",
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_CLUSTER,
        ],
        "evidence_sources": ["iam", "compute", "container"],
    },
    "AC-17": {
        "name": "Remote Access",
        "description": "Establish and document usage restrictions and implementation guidance for remote access methods",
        "scc_categories": [
            "OPEN_SSH_PORT",
            "OPEN_RDP_PORT",
            "PUBLIC_IP_ADDRESS",
            "OPEN_TELNET_PORT",
            "COMPUTE_SECURE_BOOT",
            "OS_LOGIN_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_FIREWALL,
        ],
        "evidence_sources": ["compute", "oslogin"],
    },
    # Audit and Accountability (AU) Family
    "AU-2": {
        "name": "Event Logging",
        "description": "Identify events that the system should be capable of logging",
        "scc_categories": [
            "AUDIT_LOGGING_DISABLED",
            "AUDIT_CONFIG_NOT_MONITORED",
            "BUCKET_LOGGING_DISABLED",
            "CLOUD_AUDIT_LOGGING_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_LOG_SINK,
            ASSET_TYPE_PROJECT,
            ASSET_TYPE_BUCKET,
        ],
        "evidence_sources": ["logging", "cloudresourcemanager"],
    },
    "AU-3": {
        "name": "Content of Audit Records",
        "description": "Ensure audit records contain required information",
        "scc_categories": [
            "AUDIT_LOGGING_DISABLED",
            "LOG_NOT_EXPORTED",
            "BUCKET_LOGGING_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_LOG_SINK,
            "logging.googleapis.com/LogBucket",
            "pubsub.googleapis.com/Topic",
        ],
        "evidence_sources": ["logging", "pubsub"],
    },
    "AU-6": {
        "name": "Audit Record Review, Analysis, and Reporting",
        "description": "Review and analyze system audit records for indications of inappropriate or unusual activity",
        "scc_categories": [
            "AUDIT_CONFIG_NOT_MONITORED",
            "FLOW_LOGS_DISABLED",
            "DNS_LOGGING_DISABLED",
            "LOG_NOT_EXPORTED",
        ],
        "asset_types": [
            ASSET_TYPE_LOG_SINK,
            ASSET_TYPE_SUBNETWORK,
            "dns.googleapis.com/ManagedZone",
        ],
        "evidence_sources": ["logging", "monitoring", "securitycenter"],
    },
    "AU-9": {
        "name": "Protection of Audit Information",
        "description": "Protect audit information and audit logging tools from unauthorized access and modification",
        "scc_categories": [
            "PUBLIC_LOG_BUCKET",
            "LOCKED_RETENTION_POLICY_NOT_SET",
            "OBJECT_VERSIONING_DISABLED",
            "BUCKET_IAM_NOT_MONITORED",
        ],
        "asset_types": [
            ASSET_TYPE_BUCKET,
            "logging.googleapis.com/LogBucket",
        ],
        "evidence_sources": ["storage", "logging"],
    },
    "AU-12": {
        "name": "Audit Record Generation",
        "description": "Generate audit records for defined auditable events",
        "scc_categories": [
            "AUDIT_LOGGING_DISABLED",
            "FIREWALL_RULE_LOGGING_DISABLED",
            "FLOW_LOGS_DISABLED",
            "LOAD_BALANCER_LOGGING_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_LOG_SINK,
            ASSET_TYPE_FIREWALL,
            ASSET_TYPE_SUBNETWORK,
            "compute.googleapis.com/BackendService",
        ],
        "evidence_sources": ["logging", "compute"],
    },
    # Assessment, Authorization, and Monitoring (CA) Family
    "CA-7": {
        "name": "Continuous Monitoring",
        "description": "Develop a continuous monitoring strategy and program",
        "scc_categories": [
            "FLOW_LOGS_DISABLED",
            "FIREWALL_RULE_LOGGING_DISABLED",
            "AUDIT_LOGGING_DISABLED",
            "WEB_UI_ENABLED",
            "MONITORING_ACCOUNT_NOT_CONFIGURED",
        ],
        "asset_types": [
            ASSET_TYPE_LOG_SINK,
            "monitoring.googleapis.com/AlertPolicy",
            "securitycenter.googleapis.com/Source",
        ],
        "evidence_sources": ["logging", "monitoring", "securitycenter"],
    },
    # Configuration Management (CM) Family
    "CM-2": {
        "name": "Baseline Configuration",
        "description": "Develop, document, and maintain baseline configurations for the system",
        "scc_categories": [
            "DEFAULT_SERVICE_ACCOUNT_USED",
            "LEGACY_NETWORK",
            "INSTANCE_TEMPLATE_NOT_FOUND",
            "OUTDATED_LIBRARY",
        ],
        "asset_types": [
            ASSET_TYPE_INSTANCE,
            "compute.googleapis.com/InstanceTemplate",
            ASSET_TYPE_NETWORK,
            ASSET_TYPE_CLUSTER,
        ],
        "evidence_sources": ["compute", "container"],
    },
    "CM-6": {
        "name": "Configuration Settings",
        "description": "Establish and document configuration settings for system components",
        "scc_categories": [
            "SQL_NO_ROOT_PASSWORD",
            "SQL_WEAK_ROOT_PASSWORD",
            "COMPUTE_SECURE_BOOT",
            "IP_FORWARDING_ENABLED",
            "SERIAL_PORT_ENABLED",
            "COS_NOT_USED",
            "LEGACY_AUTHORIZATION_ENABLED",
            "INTEGRITY_MONITORING_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_SQL_INSTANCE,
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_CLUSTER,
        ],
        "evidence_sources": ["sqladmin", "compute", "container"],
    },
    "CM-7": {
        "name": "Least Functionality",
        "description": "Configure the system to provide only essential capabilities",
        "scc_categories": [
            "FULL_API_ACCESS",
            "WEB_UI_ENABLED",
            "SERIAL_PORT_ENABLED",
            "IP_FORWARDING_ENABLED",
            "LEGACY_AUTHORIZATION_ENABLED",
            "LEGACY_METADATA_ENABLED",
        ],
        "asset_types": [
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_CLUSTER,
        ],
        "evidence_sources": ["compute", "container"],
    },
    "CM-8": {
        "name": "System Component Inventory",
        "description": "Develop and document an inventory of system components",
        "scc_categories": [
            "ASSET_INVENTORY_DISABLED",
            "RESOURCE_NOT_FOUND",
        ],
        "asset_types": [
            "cloudasset.googleapis.com/Asset",
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_DISK,
        ],
        "evidence_sources": ["cloudasset", "compute"],
    },
    # Contingency Planning (CP) Family
    "CP-9": {
        "name": "System Backup",
        "description": "Conduct backups of system-level information and user-level information",
        "scc_categories": [
            "AUTO_BACKUP_DISABLED",
            "BUCKET_VERSIONING_DISABLED",
            "OBJECT_VERSIONING_DISABLED",
            "SNAPSHOT_NOT_FOUND",
        ],
        "asset_types": [
            ASSET_TYPE_SQL_INSTANCE,
            ASSET_TYPE_BUCKET,
            "compute.googleapis.com/Snapshot",
            ASSET_TYPE_DISK,
        ],
        "evidence_sources": ["sqladmin", "storage", "compute"],
    },
    # Identification and Authentication (IA) Family
    "IA-2": {
        "name": "Identification and Authentication (Organizational Users)",
        "description": "Uniquely identify and authenticate organizational users",
        "scc_categories": [
            "MFA_NOT_ENFORCED",
            "NON_ORG_IAM_MEMBER",
            "OS_LOGIN_DISABLED",
            "TWO_STEP_VERIFICATION_NOT_ENFORCED",
        ],
        "asset_types": [
            ASSET_TYPE_SERVICE_ACCOUNT,
            "cloudresourcemanager.googleapis.com/Organization",
            ASSET_TYPE_INSTANCE,
        ],
        "evidence_sources": ["iam", "admin", "oslogin"],
    },
    "IA-4": {
        "name": "Identifier Management",
        "description": "Manage system identifiers by receiving authorization to assign identifiers",
        "scc_categories": [
            "ADMIN_SERVICE_ACCOUNT",
            "DEFAULT_SERVICE_ACCOUNT_USED",
            "USER_MANAGED_SERVICE_ACCOUNT_KEY",
        ],
        "asset_types": [
            ASSET_TYPE_SERVICE_ACCOUNT,
            ASSET_TYPE_SERVICE_ACCOUNT_KEY,
        ],
        "evidence_sources": ["iam"],
    },
    "IA-5": {
        "name": "Authenticator Management",
        "description": "Manage system authenticators",
        "scc_categories": [
            "SERVICE_ACCOUNT_KEY_NOT_ROTATED",
            "SQL_NO_ROOT_PASSWORD",
            "SQL_WEAK_ROOT_PASSWORD",
            "USER_MANAGED_SERVICE_ACCOUNT_KEY",
            "API_KEY_NOT_ROTATED",
            "API_KEY_NOT_RESTRICTED",
        ],
        "asset_types": [
            ASSET_TYPE_SERVICE_ACCOUNT_KEY,
            ASSET_TYPE_SQL_INSTANCE,
            "apikeys.googleapis.com/Key",
        ],
        "evidence_sources": ["iam", "sqladmin", "apikeys"],
    },
    # System and Communications Protection (SC) Family
    "SC-7": {
        "name": "Boundary Protection",
        "description": "Monitor and control communications at external boundaries and key internal boundaries",
        "scc_categories": [
            "OPEN_CASSANDRA_PORT",
            "OPEN_CISCOSECURE_WEBSM_PORT",
            "OPEN_DIRECTORY_SERVICES_PORT",
            "OPEN_DNS_PORT",
            "OPEN_ELASTICSEARCH_PORT",
            "OPEN_FTP_PORT",
            "OPEN_HTTP_PORT",
            "OPEN_LDAP_PORT",
            "OPEN_MEMCACHED_PORT",
            "OPEN_MONGODB_PORT",
            "OPEN_MYSQL_PORT",
            "OPEN_NETBIOS_PORT",
            "OPEN_ORACLEDB_PORT",
            "OPEN_POP3_PORT",
            "OPEN_POSTGRESQL_PORT",
            "OPEN_RDP_PORT",
            "OPEN_REDIS_PORT",
            "OPEN_SMTP_PORT",
            "OPEN_SSH_PORT",
            "OPEN_TELNET_PORT",
            "NETWORK_POLICY_DISABLED",
            "PUBLIC_IP_ADDRESS",
            "PUBLIC_SQL_INSTANCE",
            "FIREWALL_RULE_LOGGING_DISABLED",
            "OVER_PRIVILEGED_ACCOUNT",
            "MASTER_AUTHORIZED_NETWORKS_DISABLED",
            "PRIVATE_CLUSTER_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_FIREWALL,
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_NETWORK,
            ASSET_TYPE_SQL_INSTANCE,
            ASSET_TYPE_CLUSTER,
        ],
        "evidence_sources": ["compute", "sqladmin", "container", "networkservices"],
    },
    "SC-8": {
        "name": "Transmission Confidentiality and Integrity",
        "description": "Protect the confidentiality and integrity of transmitted information",
        "scc_categories": [
            "SSL_NOT_ENFORCED",
            "WEAK_SSL_POLICY",
            "REDIS_AUTH_DISABLED",
            "COMPUTE_SECURE_BOOT",
            "HTTPS_NOT_ENFORCED",
            "LOAD_BALANCER_SSL_POLICY",
        ],
        "asset_types": [
            ASSET_TYPE_SQL_INSTANCE,
            "compute.googleapis.com/SslPolicy",
            "compute.googleapis.com/TargetHttpsProxy",
            "redis.googleapis.com/Instance",
        ],
        "evidence_sources": ["sqladmin", "compute", "redis"],
    },
    "SC-12": {
        "name": "Cryptographic Key Establishment and Management",
        "description": "Establish and manage cryptographic keys",
        "scc_categories": [
            "KMS_PROJECT_HAS_OWNER",
            "KMS_KEY_NOT_ROTATED",
            "KMS_ROLE_SEPARATION",
            "KMS_PUBLIC_KEY",
            "CMEK_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_CRYPTO_KEY,
            "cloudkms.googleapis.com/KeyRing",
            "cloudkms.googleapis.com/CryptoKeyVersion",
        ],
        "evidence_sources": ["cloudkms"],
    },
    "SC-13": {
        "name": "Cryptographic Protection",
        "description": "Implement cryptographic mechanisms to prevent unauthorized disclosure and modification",
        "scc_categories": [
            "WEAK_SSL_POLICY",
            "CMEK_DISABLED",
            "SQL_CMEK_DISABLED",
            "BUCKET_CMEK_DISABLED",
            "DISK_CSEK_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_SQL_INSTANCE,
            ASSET_TYPE_BUCKET,
            ASSET_TYPE_DISK,
            ASSET_TYPE_CRYPTO_KEY,
        ],
        "evidence_sources": ["sqladmin", "storage", "compute", "cloudkms"],
    },
    "SC-28": {
        "name": "Protection of Information at Rest",
        "description": "Protect the confidentiality and integrity of information at rest",
        "scc_categories": [
            "DISK_CSEK_DISABLED",
            "CMEK_DISABLED",
            "SQL_CMEK_DISABLED",
            "BUCKET_CMEK_DISABLED",
            "DEFAULT_ENCRYPTION_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_DISK,
            ASSET_TYPE_SQL_INSTANCE,
            ASSET_TYPE_BUCKET,
        ],
        "evidence_sources": ["compute", "sqladmin", "storage", "cloudkms"],
    },
    # System and Information Integrity (SI) Family
    "SI-2": {
        "name": "Flaw Remediation",
        "description": "Identify, report, and correct system flaws",
        "scc_categories": [
            "OUTDATED_LIBRARY",
            "OUTDATED_DEPENDENCIES",
            "VULNERABILITY_FOUND",
            "WEB_VULNERABILITY_FOUND",
            "CONTAINER_VULNERABILITY",
            "AUTO_UPGRADE_DISABLED",
            "NODE_AUTO_UPGRADE_DISABLED",
        ],
        "asset_types": [
            "cloudbuild.googleapis.com/Build",
            "containeranalysis.googleapis.com/Occurrence",
            ASSET_TYPE_CLUSTER,
            "artifactregistry.googleapis.com/Repository",
        ],
        "evidence_sources": ["containeranalysis", "container", "artifactregistry"],
    },
    "SI-3": {
        "name": "Malicious Code Protection",
        "description": "Implement malicious code protection mechanisms",
        "scc_categories": [
            "MALWARE_DETECTED",
            "SUSPICIOUS_ACTIVITY_DETECTED",
            "BINARY_AUTHORIZATION_DISABLED",
            "ANTIMALWARE_NOT_ENABLED",
        ],
        "asset_types": [
            ASSET_TYPE_INSTANCE,
            ASSET_TYPE_CLUSTER,
            "binaryauthorization.googleapis.com/Policy",
        ],
        "evidence_sources": ["securitycenter", "container", "binaryauthorization"],
    },
    "SI-4": {
        "name": "System Monitoring",
        "description": "Monitor the system to detect attacks and indicators of potential attacks",
        "scc_categories": [
            "FIREWALL_RULE_LOGGING_DISABLED",
            "FLOW_LOGS_DISABLED",
            "AUDIT_LOGGING_DISABLED",
            "DNS_LOGGING_DISABLED",
            "VPC_FLOW_LOGS_DISABLED",
            "CLOUD_ARMOR_LOGGING_DISABLED",
            "THREAT_DETECTION_DISABLED",
        ],
        "asset_types": [
            ASSET_TYPE_FIREWALL,
            ASSET_TYPE_SUBNETWORK,
            ASSET_TYPE_LOG_SINK,
            "dns.googleapis.com/ManagedZone",
            "securitycenter.googleapis.com/Source",
        ],
        "evidence_sources": ["compute", "logging", "dns", "securitycenter"],
    },
}

# Build reverse lookup indices for efficient category-to-control lookups
_CATEGORY_TO_CONTROLS: Dict[str, List[str]] = {}
_ASSET_TYPE_TO_CONTROLS: Dict[str, List[str]] = {}


def _add_to_index(index: Dict[str, List[str]], key: str, control_id: str) -> None:
    """Add a control ID to an index under the given key.

    :param Dict[str, List[str]] index: The index dictionary to update
    :param str key: The key to add the control under
    :param str control_id: The control ID to add
    """
    key_str = str(key)
    if key_str not in index:
        index[key_str] = []
    if control_id not in index[key_str]:
        index[key_str].append(control_id)


def _build_category_index(control_id: str, mapping: Dict[str, Any]) -> None:
    """Build category to control index entries for a single control.

    :param str control_id: The control ID
    :param Dict[str, Any] mapping: The control mapping data
    """
    scc_categories = mapping.get("scc_categories", [])
    if isinstance(scc_categories, list):
        for category in scc_categories:
            _add_to_index(_CATEGORY_TO_CONTROLS, category, control_id)


def _build_asset_type_index(control_id: str, mapping: Dict[str, Any]) -> None:
    """Build asset type to control index entries for a single control.

    :param str control_id: The control ID
    :param Dict[str, Any] mapping: The control mapping data
    """
    asset_types = mapping.get("asset_types", [])
    if isinstance(asset_types, list):
        for asset_type in asset_types:
            _add_to_index(_ASSET_TYPE_TO_CONTROLS, asset_type, control_id)


def _build_indices() -> None:
    """Build reverse lookup indices from the mappings."""
    for control_id, mapping in NIST_800_53_R5_MAPPINGS.items():
        _build_category_index(control_id, mapping)
        _build_asset_type_index(control_id, mapping)


# Initialize indices on module load
_build_indices()


def get_controls_for_category(category: str) -> List[str]:
    """Get all control IDs that map to a given SCC category.

    :param str category: The GCP SCC finding category (e.g., "PUBLIC_BUCKET_ACL")
    :return: List of NIST 800-53 control IDs that map to the category
    :rtype: List[str]

    Example:
        >>> get_controls_for_category("PUBLIC_BUCKET_ACL")
        ['AC-3']
        >>> get_controls_for_category("MFA_NOT_ENFORCED")
        ['AC-2', 'IA-2']
    """
    return _CATEGORY_TO_CONTROLS.get(category, [])


def get_categories_for_control(control_id: str) -> List[str]:
    """Get all SCC categories that map to a given control.

    :param str control_id: The NIST 800-53 control ID (e.g., "AC-2")
    :return: List of GCP SCC finding categories that map to the control
    :rtype: List[str]

    Example:
        >>> get_categories_for_control("AC-2")
        ['ADMIN_SERVICE_ACCOUNT', 'USER_MANAGED_SERVICE_ACCOUNT_KEY', ...]
    """
    mapping = NIST_800_53_R5_MAPPINGS.get(control_id.upper())
    if mapping:
        scc_categories = mapping.get("scc_categories", [])
        if isinstance(scc_categories, list):
            return [str(cat) for cat in scc_categories]
    return []


def get_controls_for_asset_type(asset_type: str) -> List[str]:
    """Get all control IDs that map to a given GCP asset type.

    :param str asset_type: The GCP asset type (e.g., "iam.googleapis.com/ServiceAccount")
    :return: List of NIST 800-53 control IDs that map to the asset type
    :rtype: List[str]

    Example:
        >>> get_controls_for_asset_type("storage.googleapis.com/Bucket")
        ['AC-3', 'AU-9', 'CP-9', 'SC-13', 'SC-28']
    """
    return _ASSET_TYPE_TO_CONTROLS.get(asset_type, [])


def get_control_name(control_id: str) -> Optional[str]:
    """Get the human-readable name for a control.

    :param str control_id: The NIST 800-53 control ID (e.g., "AC-2")
    :return: The control name or None if not found
    :rtype: Optional[str]

    Example:
        >>> get_control_name("AC-2")
        'Account Management'
    """
    mapping = NIST_800_53_R5_MAPPINGS.get(control_id.upper())
    if mapping:
        return str(mapping.get("name"))
    return None


def get_control_description(control_id: str) -> Optional[str]:
    """Get the description for a control.

    :param str control_id: The NIST 800-53 control ID (e.g., "AC-2")
    :return: The control description or None if not found
    :rtype: Optional[str]

    Example:
        >>> get_control_description("AC-2")
        'Manage system accounts including creation, enabling, modification, and removal'
    """
    mapping = NIST_800_53_R5_MAPPINGS.get(control_id.upper())
    if mapping:
        return str(mapping.get("description"))
    return None


def get_evidence_sources_for_control(control_id: str) -> List[str]:
    """Get the GCP evidence sources for a control.

    :param str control_id: The NIST 800-53 control ID (e.g., "AC-2")
    :return: List of GCP API services that provide evidence for the control
    :rtype: List[str]

    Example:
        >>> get_evidence_sources_for_control("AC-2")
        ['iam', 'logging', 'cloudresourcemanager']
    """
    mapping = NIST_800_53_R5_MAPPINGS.get(control_id.upper())
    if mapping:
        evidence_sources = mapping.get("evidence_sources", [])
        if isinstance(evidence_sources, list):
            return [str(source) for source in evidence_sources]
    return []


def get_all_control_ids() -> List[str]:
    """Get all mapped NIST 800-53 control IDs.

    :return: List of all control IDs in the mappings
    :rtype: List[str]
    """
    return list(NIST_800_53_R5_MAPPINGS.keys())


def get_all_scc_categories() -> List[str]:
    """Get all mapped GCP SCC finding categories.

    :return: List of all SCC categories in the mappings
    :rtype: List[str]
    """
    return list(_CATEGORY_TO_CONTROLS.keys())


def get_control_family(control_id: str) -> Optional[str]:
    """Get the control family for a control ID.

    :param str control_id: The NIST 800-53 control ID (e.g., "AC-2")
    :return: The control family (e.g., "AC") or None if not found
    :rtype: Optional[str]

    Example:
        >>> get_control_family("AC-2")
        'AC'
        >>> get_control_family("SI-4")
        'SI'
    """
    if control_id.upper() in NIST_800_53_R5_MAPPINGS:
        parts = control_id.split("-")
        if parts:
            return parts[0].upper()
    return None


def get_controls_by_family(family: str) -> List[str]:
    """Get all control IDs for a given control family.

    :param str family: The control family (e.g., "AC", "AU", "SC")
    :return: List of control IDs in the family
    :rtype: List[str]

    Example:
        >>> get_controls_by_family("AC")
        ['AC-2', 'AC-3', 'AC-4', 'AC-5', 'AC-6', 'AC-17']
    """
    family_upper = family.upper()
    return [control_id for control_id in NIST_800_53_R5_MAPPINGS.keys() if control_id.startswith(family_upper + "-")]


def get_mapping_summary() -> Dict[str, int]:
    """Get a summary of the mappings.

    :return: Dictionary with counts of controls, categories, and asset types
    :rtype: Dict[str, int]
    """
    all_categories: set[str] = set()
    all_asset_types: set[str] = set()

    for mapping in NIST_800_53_R5_MAPPINGS.values():
        scc_categories = mapping.get("scc_categories", [])
        if isinstance(scc_categories, list):
            all_categories.update(str(cat) for cat in scc_categories)
        asset_types = mapping.get("asset_types", [])
        if isinstance(asset_types, list):
            all_asset_types.update(str(at) for at in asset_types)

    return {
        "total_controls": len(NIST_800_53_R5_MAPPINGS),
        "total_scc_categories": len(all_categories),
        "total_asset_types": len(all_asset_types),
        "control_families": len({get_control_family(c) for c in NIST_800_53_R5_MAPPINGS.keys()}),
    }
