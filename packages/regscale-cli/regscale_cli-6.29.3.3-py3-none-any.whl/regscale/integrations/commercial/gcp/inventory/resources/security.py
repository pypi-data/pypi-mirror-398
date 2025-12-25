#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Security Command Center resource collectors.

This module provides collectors for GCP Security Command Center resources including:
- Security Command Center findings
- Security Command Center sources
- Security Health Analytics findings
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class SecurityCollector(BaseCollector):
    """Collector for GCP Security Command Center resources."""

    # GCP asset types for security resources
    supported_asset_types: List[str] = [
        "securitycenter.googleapis.com/Finding",
        "securitycenter.googleapis.com/Source",
    ]

    # Severity levels for filtering (in order of severity)
    SEVERITY_LEVELS: List[str] = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNSPECIFIED"]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
        severity_filter: Optional[List[str]] = None,
    ) -> None:
        """Initialize the security collector.

        :param str parent: GCP parent resource path (organization ID required for SCC)
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        :param Optional[List[str]] severity_filter: List of severity levels to include
                                                    (e.g., ["CRITICAL", "HIGH"])
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}
        self.severity_filter = severity_filter or self.SEVERITY_LEVELS

    def _get_scc_client(self) -> Any:
        """Get Security Command Center client with credentials.

        :return: Security Command Center client
        :rtype: Any
        """
        from google.cloud import securitycenter

        if self.credentials_path:
            return securitycenter.SecurityCenterClient.from_service_account_file(self.credentials_path)
        return securitycenter.SecurityCenterClient()

    def _get_organization_name(self) -> Optional[str]:
        """Get the organization name for SCC API calls.

        SCC requires organization-level access for most operations.

        :return: Organization name in format 'organizations/ORG_ID' or None
        :rtype: Optional[str]
        """
        if self.parent.startswith("organizations/"):
            return self.parent
        logger.warning(
            "Security Command Center requires organization-level access. Parent '%s' is not an organization.",
            self.parent,
        )
        return None

    def _build_severity_filter(self) -> str:
        """Build the severity filter string for SCC API.

        :return: Filter string for severity filtering
        :rtype: str
        """
        if not self.severity_filter or set(self.severity_filter) == set(self.SEVERITY_LEVELS):
            return ""

        severity_conditions = [f'severity = "{sev}"' for sev in self.severity_filter]
        return " OR ".join(severity_conditions)

    def get_scc_findings(self) -> List[Dict[str, Any]]:
        """Get Security Command Center findings.

        :return: List of SCC finding information
        :rtype: List[Dict[str, Any]]
        """
        findings = []
        try:
            from google.cloud import securitycenter

            client = self._get_scc_client()
            org_name = self._get_organization_name()

            if not org_name:
                return findings

            # Build request with optional severity filter
            request = securitycenter.ListFindingsRequest(parent=f"{org_name}/sources/-")

            # Apply severity filter if specified
            severity_filter = self._build_severity_filter()
            if severity_filter:
                request.filter = severity_filter
                logger.debug("Applying severity filter: %s", severity_filter)

            # List all findings
            for finding_result in client.list_findings(request=request):
                finding = finding_result.finding
                parsed = self._parse_finding(finding)

                # Apply project filter if specified
                if self.project_id and not self._matches_project(parsed.get("resource_name", "")):
                    continue

                findings.append(parsed)

            logger.info("Collected %d SCC findings", len(findings))

        except Exception as e:
            self._handle_error(e, "Security Command Center findings")

        return findings

    def get_scc_sources(self) -> List[Dict[str, Any]]:
        """Get Security Command Center sources.

        :return: List of SCC source information
        :rtype: List[Dict[str, Any]]
        """
        sources = []
        try:
            from google.cloud import securitycenter

            client = self._get_scc_client()
            org_name = self._get_organization_name()

            if not org_name:
                return sources

            # List all sources
            request = securitycenter.ListSourcesRequest(parent=org_name)

            for source in client.list_sources(request=request):
                sources.append(self._parse_source(source))

            logger.info("Collected %d SCC sources", len(sources))

        except Exception as e:
            self._handle_error(e, "Security Command Center sources")

        return sources

    def get_security_health_analytics_findings(self) -> List[Dict[str, Any]]:
        """Get Security Health Analytics (SHA) findings specifically.

        SHA is a built-in source that detects misconfigurations and vulnerabilities.

        :return: List of SHA finding information
        :rtype: List[Dict[str, Any]]
        """
        findings = []
        try:
            from google.cloud import securitycenter

            client = self._get_scc_client()
            org_name = self._get_organization_name()

            if not org_name:
                return findings

            # Find the Security Health Analytics source
            sha_source_name = None
            list_sources_request = securitycenter.ListSourcesRequest(parent=org_name)

            for source in client.list_sources(request=list_sources_request):
                if (
                    "security-health-analytics" in source.display_name.lower()
                    or "securityhealthanalytics" in (source.canonical_name or "").lower()
                ):
                    sha_source_name = source.name
                    break

            if not sha_source_name:
                logger.warning("Security Health Analytics source not found in organization %s", org_name)
                return findings

            # Build request for SHA findings
            request = securitycenter.ListFindingsRequest(parent=sha_source_name)

            # Apply severity filter if specified
            severity_filter = self._build_severity_filter()
            if severity_filter:
                request.filter = severity_filter

            # List SHA findings
            for finding_result in client.list_findings(request=request):
                finding = finding_result.finding
                parsed = self._parse_finding(finding)

                # Apply project filter if specified
                if self.project_id and not self._matches_project(parsed.get("resource_name", "")):
                    continue

                findings.append(parsed)

            logger.info("Collected %d Security Health Analytics findings", len(findings))

        except Exception as e:
            self._handle_error(e, "Security Health Analytics findings")

        return findings

    def _parse_finding(self, finding: Any) -> Dict[str, Any]:
        """Parse a Security Command Center finding to a dictionary.

        :param finding: SCC finding object
        :return: Parsed finding data
        :rtype: Dict[str, Any]
        """
        return {
            "name": finding.name,
            "parent": finding.parent,
            "resource_name": finding.resource_name,
            "category": finding.category,
            "severity": self._extract_enum_value(finding, "severity"),
            "state": self._extract_enum_value(finding, "state"),
            "mute": self._extract_enum_value(finding, "mute"),
            "finding_class": self._extract_enum_value(finding, "finding_class"),
            "description": getattr(finding, "description", None),
            "event_time": finding.event_time.isoformat() if finding.event_time else None,
            "create_time": finding.create_time.isoformat() if finding.create_time else None,
            "external_uri": getattr(finding, "external_uri", None),
            "source_properties": dict(finding.source_properties) if finding.source_properties else {},
            "canonical_name": getattr(finding, "canonical_name", None),
            "vulnerability": self._parse_vulnerability(finding) if hasattr(finding, "vulnerability") else None,
            "compliances": self._parse_compliances(finding) if hasattr(finding, "compliances") else [],
        }

    def _extract_enum_value(self, obj: Any, attr_name: str, default: str = "UNSPECIFIED") -> str:
        """Extract an enum value as a string from an object attribute.

        :param obj: Object containing the attribute
        :param attr_name: Name of the attribute to extract
        :param default: Default value if attribute doesn't exist
        :return: String representation of the enum value
        :rtype: str
        """
        if not hasattr(obj, attr_name):
            return default
        attr_value = getattr(obj, attr_name)
        if hasattr(attr_value, "name"):
            return attr_value.name
        return str(attr_value)

    def _parse_source(self, source: Any) -> Dict[str, Any]:
        """Parse a Security Command Center source to a dictionary.

        :param source: SCC source object
        :return: Parsed source data
        :rtype: Dict[str, Any]
        """
        return {
            "name": source.name,
            "display_name": source.display_name,
            "description": getattr(source, "description", None),
            "canonical_name": getattr(source, "canonical_name", None),
        }

    def _parse_vulnerability(self, finding: Any) -> Optional[Dict[str, Any]]:
        """Parse vulnerability information from a finding.

        :param finding: SCC finding object
        :return: Parsed vulnerability data or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(finding, "vulnerability") or not finding.vulnerability:
            return None

        vuln = finding.vulnerability
        return {
            "cve": self._parse_cve(vuln) if hasattr(vuln, "cve") else None,
        }

    def _parse_cve(self, vuln: Any) -> Optional[Dict[str, Any]]:
        """Parse CVE information from vulnerability.

        :param vuln: Vulnerability object
        :return: Parsed CVE data or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(vuln, "cve") or not vuln.cve:
            return None

        cve = vuln.cve
        return {
            "id": getattr(cve, "id", None),
            "cvss_v3": self._parse_cvss_v3(cve),
            "references": self._parse_cve_references(cve),
        }

    def _parse_cvss_v3(self, cve: Any) -> Optional[Dict[str, Any]]:
        """Parse CVSS v3 information from CVE.

        :param cve: CVE object
        :return: Parsed CVSS v3 data or None
        :rtype: Optional[Dict[str, Any]]
        """
        if not hasattr(cve, "cvssv3") or not cve.cvssv3:
            return None
        attack_vector = None
        if hasattr(cve.cvssv3, "attack_vector") and hasattr(cve.cvssv3.attack_vector, "name"):
            attack_vector = cve.cvssv3.attack_vector.name
        return {
            "base_score": getattr(cve.cvssv3, "base_score", None),
            "attack_vector": attack_vector,
        }

    def _parse_cve_references(self, cve: Any) -> List[Dict[str, str]]:
        """Parse references from CVE.

        :param cve: CVE object
        :return: List of parsed reference data
        :rtype: List[Dict[str, str]]
        """
        if not hasattr(cve, "references"):
            return []
        return [{"source": ref.source, "uri": ref.uri} for ref in (cve.references or [])]

    def _parse_compliances(self, finding: Any) -> List[Dict[str, Any]]:
        """Parse compliance information from a finding.

        :param finding: SCC finding object
        :return: List of parsed compliance data
        :rtype: List[Dict[str, Any]]
        """
        if not hasattr(finding, "compliances") or not finding.compliances:
            return []

        compliances = []
        for compliance in finding.compliances:
            compliances.append(
                {
                    "standard": getattr(compliance, "standard", None),
                    "version": getattr(compliance, "version", None),
                    "ids": list(compliance.ids) if hasattr(compliance, "ids") and compliance.ids else [],
                }
            )
        return compliances

    def collect(self) -> Dict[str, Any]:
        """Collect security resources based on enabled_services configuration.

        :return: Dictionary containing enabled security resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # SCC Findings
        if self.enabled_services.get("scc_findings", True):
            result["SCCFindings"] = self.get_scc_findings()

        # SCC Sources
        if self.enabled_services.get("scc_sources", True):
            result["SCCSources"] = self.get_scc_sources()

        # Security Health Analytics Findings
        if self.enabled_services.get("security_health_analytics", True):
            result["SecurityHealthAnalyticsFindings"] = self.get_security_health_analytics_findings()

        return result
