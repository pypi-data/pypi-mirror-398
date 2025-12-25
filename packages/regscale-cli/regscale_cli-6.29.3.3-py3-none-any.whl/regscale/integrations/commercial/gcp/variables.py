#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Variables and Configuration Constants.

This module defines configuration variables and constants for the GCP
Security Command Center integration.
"""

from typing import List

from regscale.core.app.utils.variables import RsVariableType, RsVariablesMeta

# Valid scan scope types
GCP_VALID_SCAN_TYPES: List[str] = ["organization", "folder", "project"]

# Supported compliance frameworks
GCP_SUPPORTED_FRAMEWORKS: List[str] = [
    "NIST800-53R5",
    "CIS_GCP",
    "FedRAMP",
    "PCI-DSS",
    "SOC2",
]

# Default finding sources from Security Command Center
GCP_DEFAULT_FINDING_SOURCES: List[str] = [
    "SECURITY_HEALTH_ANALYTICS",
    "EVENT_THREAT_DETECTION",
    "CONTAINER_THREAT_DETECTION",
    "WEB_SECURITY_SCANNER",
]

# Valid evidence collection modes
GCP_VALID_EVIDENCE_MODES: List[str] = ["attachments", "records"]

# Default configuration values
GCP_DEFAULT_CACHE_TTL_HOURS: int = 8
GCP_DEFAULT_COMPLIANCE_FRAMEWORK: str = "NIST800-53R5"
GCP_DEFAULT_EVIDENCE_MODE: str = "attachments"
GCP_DEFAULT_SEVERITY_FILTER: str = "CRITICAL,HIGH,MEDIUM"


class GcpVariables(metaclass=RsVariablesMeta):
    """GCP Variables class to define class-level attributes with type annotations and examples.

    This class uses RsVariablesMeta to automatically create properties that read
    from the application's init.yaml configuration file.

    Attributes:
        gcpCredentials: Path to the GCP service account JSON key file.
        gcpCredentialsJsonBase64: Base64-encoded GCP service account credentials (recommended).
        gcpCredentialsJson: GCP service account credentials as raw JSON string content.
        gcpScanType: Scope type for scanning (organization, folder, or project).
        gcpOrganizationId: GCP Organization ID for organization-level scanning.
        gcpFolderId: GCP Folder ID for folder-level scanning.
        gcpProjectId: GCP Project ID for project-level scanning.
        gcpCacheTTLHours: Cache time-to-live in hours for inventory data.
        gcpComplianceFramework: Compliance framework for control mapping.
        gcpSeverityFilter: Comma-separated severity levels to include.
        gcpFindingSources: JSON list of SCC finding sources to include.
        gcpEvidenceMode: Evidence collection mode (attachments or records).
    """

    # Authentication - File path (legacy)
    gcpCredentials: RsVariableType(str, "path/to/service-account.json")  # type: ignore # noqa: F722,F821

    # Authentication - Base64-encoded JSON content (RECOMMENDED for init.yaml)
    # Generate with: cat service-account.json | base64
    gcpCredentialsJsonBase64: RsVariableType(str, "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsIC4uLn0=", required=False)  # type: ignore # noqa: F722,F821

    # Authentication - Raw JSON content (alternative, but may have YAML escaping issues)
    gcpCredentialsJson: RsVariableType(str, '{"type": "service_account", ...}', required=False)  # type: ignore # noqa: F722,F821

    # Scope Configuration
    gcpScanType: RsVariableType(str, "organization", required=False)  # type: ignore # noqa: F722,F821
    gcpOrganizationId: RsVariableType(str, "000000000000", required=False)  # type: ignore # noqa: F722,F821
    gcpFolderId: RsVariableType(str, "000000000000", required=False)  # type: ignore # noqa: F722,F821
    gcpProjectId: RsVariableType(str, "my-project-id", required=False)  # type: ignore # noqa: F722,F821

    # API Configuration
    gcpCacheTTLHours: RsVariableType(int, "8", default=GCP_DEFAULT_CACHE_TTL_HOURS, required=False)  # type: ignore # noqa: F722,F821

    # Compliance Configuration
    gcpComplianceFramework: RsVariableType(str, "NIST800-53R5", default=GCP_DEFAULT_COMPLIANCE_FRAMEWORK, required=False)  # type: ignore # noqa: F722,F821
    gcpSeverityFilter: RsVariableType(str, "CRITICAL,HIGH,MEDIUM", default=GCP_DEFAULT_SEVERITY_FILTER, required=False)  # type: ignore # noqa: F722,F821
    gcpFindingSources: RsVariableType(list, '["SECURITY_HEALTH_ANALYTICS", "EVENT_THREAT_DETECTION"]', default=GCP_DEFAULT_FINDING_SOURCES, required=False)  # type: ignore # noqa: F722,F821

    # Evidence Configuration
    gcpEvidenceMode: RsVariableType(str, "attachments", default=GCP_DEFAULT_EVIDENCE_MODE, required=False)  # type: ignore # noqa: F722,F821
