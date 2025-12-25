#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Security Command Center Compliance Integration for RegScale CLI.

This module provides compliance posture management by mapping GCP Security Command Center
findings to RegScale controls and creating assessments.
"""

import gzip
import json
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, Iterator, List, Optional

from google.cloud import securitycenter_v1

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.gcp.auth import get_gcp_security_center_client
from regscale.integrations.commercial.gcp.control_mappings import ControlFrameworkResolver
from regscale.integrations.commercial.gcp.variables import GcpVariables
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.integrations.scanner_integration import IntegrationAsset, IntegrationFinding


@dataclass
class GCPEvidenceOptions:
    """Configuration options for GCP evidence collection."""

    collect: bool = False
    as_attachments: bool = True
    as_records: bool = False
    control_ids: Optional[List[str]] = None
    frequency: int = 30


@dataclass
class GCPScopeOptions:
    """Configuration options for GCP scan scope."""

    scope: Optional[str] = None
    project_id: Optional[str] = None
    organization_id: Optional[str] = None


logger = logging.getLogger("regscale")

# Constants for file paths and cache TTL
GCP_COMPLIANCE_CACHE_FILE = os.path.join("artifacts", "gcp", "compliance_assessments.json")
CACHE_TTL_SECONDS = 8 * 60 * 60  # 8 hours in seconds (matches GCP default cache TTL)

# HTML tag constants to avoid duplication
HTML_STRONG_OPEN = "<strong>"
HTML_STRONG_CLOSE = "</strong>"
HTML_P_OPEN = "<p>"
HTML_P_CLOSE = "</p>"
HTML_UL_OPEN = "<ul>"
HTML_UL_CLOSE = "</ul>"
HTML_LI_OPEN = "<li>"
HTML_LI_CLOSE = "</li>"
HTML_H2_OPEN = "<h2>"
HTML_H2_CLOSE = "</h2>"
HTML_H3_OPEN = "<h3>"
HTML_H3_CLOSE = "</h3>"
HTML_H4_OPEN = "<h4>"
HTML_H4_CLOSE = "</h4>"
HTML_BR = "<br>"


class GCPComplianceItem(ComplianceItem):
    """
    Compliance item from GCP Security Command Center finding evaluation.

    Represents a control assessment based on GCP SCC findings. Multiple findings
    can map to a single control, and the control passes only if NO findings exist
    for that control category.
    """

    def __init__(
        self,
        control_id: str,
        control_name: str,
        framework: str,
        scc_findings: List[Dict[str, Any]],
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
    ):
        """
        Initialize from GCP SCC findings.

        :param str control_id: Control identifier (e.g., AC-2, SI-3)
        :param str control_name: Human-readable control name
        :param str framework: Compliance framework
        :param List[Dict[str, Any]] scc_findings: SCC finding results for this control
        :param Optional[str] resource_id: Resource identifier (GCP project ID typically)
        :param Optional[str] resource_name: Resource name
        """
        self._control_id = control_id
        self._control_name = control_name
        self._framework = framework
        self.scc_findings = scc_findings
        self._resource_id = resource_id or ""
        self._resource_name = resource_name or ""

        # Cache for aggregated compliance result
        self._aggregated_compliance_result = None

    @property
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        return self._resource_id

    @property
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        return self._resource_name

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        return self._control_id

    def _aggregate_finding_compliance(self) -> Optional[str]:
        """
        Aggregate SCC findings to determine overall control compliance.

        GCP SCC Finding States:
        - "ACTIVE": Finding is currently active (non-compliant)
        - "INACTIVE": Finding has been remediated or is no longer applicable

        Aggregation Logic:
        1. If ANY finding shows "ACTIVE" state → Control FAILS
        2. If ALL findings show "INACTIVE" or no findings exist → Control PASSES
        3. If no conclusive data → None

        :return: "PASS", "FAIL", or None (if inconclusive/no data)
        :rtype: Optional[str]
        """
        if not self.scc_findings:
            logger.debug(f"Control {self.control_id}: No SCC findings available - PASS by default")
            return "PASS"

        active_count = 0
        inactive_count = 0
        total_findings = len(self.scc_findings)

        for finding in self.scc_findings:
            state = finding.get("state", "").upper()

            if state == "ACTIVE":
                active_count += 1
            elif state == "INACTIVE":
                inactive_count += 1

        logger.debug(
            f"Control {self.control_id} finding summary: "
            f"{active_count} ACTIVE, {inactive_count} INACTIVE "
            f"out of {total_findings} total"
        )

        # If ANY finding is active, the control fails
        if active_count > 0:
            logger.info(f"Control {self.control_id} FAILS: {active_count} active finding(s) out of {total_findings}")
            return "FAIL"

        # If we have findings but none are active, control passes
        if inactive_count > 0 or total_findings > 0:
            logger.info(f"Control {self.control_id} PASSES: No active findings (total findings: {total_findings})")
            return "PASS"

        # If no applicable data, we cannot determine status
        logger.warning(f"Control {self.control_id}: No conclusive data for {total_findings} finding(s)")
        return None

    @property
    def compliance_result(self) -> Optional[str]:
        """
        Result of compliance check (PASS, FAIL, etc).

        Aggregates SCC findings to determine control-level compliance.

        :return: "PASS", "FAIL", or None (if no conclusive data available)
        :rtype: Optional[str]
        """
        # Use cached result if available
        if self._aggregated_compliance_result is not None or hasattr(self, "_result_was_cached"):
            return self._aggregated_compliance_result

        # Aggregate finding compliance checks
        result = self._aggregate_finding_compliance()

        if result is None:
            logger.info(
                f"Control {self.control_id}: No conclusive data for compliance determination. "
                f"Control status will not be updated. Findings: {len(self.scc_findings)}"
            )

        # Cache the result (including None)
        self._aggregated_compliance_result = result
        self._result_was_cached = True
        return result

    @property
    def severity(self) -> Optional[str]:
        """Severity level of the compliance violation (if failed)."""
        if self.compliance_result != "FAIL":
            return None

        # Determine severity based on highest severity finding
        severity_map = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        max_severity = 0
        for finding in self.scc_findings:
            severity_str = finding.get("severity", "").upper()
            severity_val = severity_map.get(severity_str, 0)
            max_severity = max(max_severity, severity_val)

        # Map back to severity string
        for sev_str, sev_val in severity_map.items():
            if sev_val == max_severity:
                return sev_str

        return "MEDIUM"  # Default

    @property
    def description(self) -> str:
        """Description of the compliance check using HTML formatting."""
        desc_parts = [
            f"{HTML_H3_OPEN}GCP Security Command Center compliance assessment for control {self.control_id}{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Control:{HTML_STRONG_CLOSE} {self._control_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self._framework}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Total Findings:{HTML_STRONG_CLOSE} {len(self.scc_findings)}",
            HTML_P_CLOSE,
        ]

        # Add finding summary
        active_findings = [f for f in self.scc_findings if f.get("state") == "ACTIVE"]
        inactive_findings = [f for f in self.scc_findings if f.get("state") == "INACTIVE"]

        desc_parts.extend(
            [
                f"{HTML_H4_OPEN}Compliance Summary{HTML_H4_CLOSE}",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Active Findings:{HTML_STRONG_CLOSE} {len(active_findings)}"
                f"{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Inactive Findings:{HTML_STRONG_CLOSE} {len(inactive_findings)}"
                f"{HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
            ]
        )

        # Add active findings details with full information
        if active_findings:
            desc_parts.append(f"{HTML_H4_OPEN}Active Findings (Why This Control Failed){HTML_H4_CLOSE}")
            for idx, finding in enumerate(active_findings[:10], 1):  # Show up to 10 active findings
                category = finding.get("category", "Unknown")
                resource_name = finding.get("resource_name", "Unknown")
                severity = finding.get("severity", "Unknown")
                finding_description = finding.get("description", "")
                external_uri = finding.get("external_uri", "")

                desc_parts.append(
                    '<div style="margin: 10px 0; padding: 10px; background-color: #fff3e0; '
                    'border-left: 3px solid #ff9800;">'
                )
                desc_parts.append(f"{HTML_STRONG_OPEN}Finding #{idx}: {category}{HTML_STRONG_CLOSE}{HTML_BR}")
                desc_parts.append(f"{HTML_STRONG_OPEN}Severity:{HTML_STRONG_CLOSE} {severity}{HTML_BR}")
                desc_parts.append(f"{HTML_STRONG_OPEN}Resource:{HTML_STRONG_CLOSE} {resource_name}{HTML_BR}")
                if finding_description:
                    desc_parts.append(
                        f"{HTML_STRONG_OPEN}Description:{HTML_STRONG_CLOSE} {finding_description}{HTML_BR}"
                    )
                if external_uri:
                    desc_parts.append(
                        f'{HTML_STRONG_OPEN}More Info:{HTML_STRONG_CLOSE} <a href="{external_uri}">'
                        f"View in GCP Console</a>"
                    )
                desc_parts.append("</div>")

            if len(active_findings) > 10:
                desc_parts.append(
                    f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Note:{HTML_STRONG_CLOSE} "
                    f"{len(active_findings) - 10} additional active findings not shown.{HTML_P_CLOSE}"
                )

        return "\n".join(desc_parts)

    @property
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CIS_GCP)."""
        return self._framework


class GCPComplianceIntegration(ComplianceIntegration):
    """Process GCP Security Command Center compliance assessments and create compliance records in RegScale."""

    title = "GCP Security Command Center Compliance"
    asset_identifier_field = "otherTrackingNumber"  # Server-side batch deduplication requires standard field

    def __init__(
        self,
        plan_id: int,
        framework: str = "NIST800-53R5",
        create_issues: bool = True,
        update_control_status: bool = True,
        create_poams: bool = False,
        parent_module: str = "securityplans",
        evidence_options: Optional[GCPEvidenceOptions] = None,
        scope_options: Optional[GCPScopeOptions] = None,
        force_refresh: bool = False,
        **kwargs,
    ):
        """
        Initialize GCP Security Command Center compliance integration.

        :param int plan_id: RegScale plan ID
        :param str framework: Compliance framework (default: NIST800-53R5)
        :param bool create_issues: Whether to create issues for failed compliance
        :param bool update_control_status: Whether to update control implementation status
        :param bool create_poams: Whether to mark issues as POAMs
        :param str parent_module: RegScale parent module
        :param Optional[GCPEvidenceOptions] evidence_options: Evidence collection configuration
        :param Optional[GCPScopeOptions] scope_options: GCP scan scope configuration
        :param bool force_refresh: Force refresh of compliance data by bypassing cache
        :param kwargs: Additional parameters
        """
        super().__init__(
            plan_id=plan_id,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            parent_module=parent_module,
            **kwargs,
        )

        # Evidence collection parameters (use defaults if not provided)
        evidence_opts = evidence_options or GCPEvidenceOptions()
        self.collect_evidence = evidence_opts.collect
        self.evidence_as_attachments = evidence_opts.as_attachments
        self.evidence_as_records = evidence_opts.as_records
        self.evidence_control_ids = evidence_opts.control_ids
        self.evidence_frequency = evidence_opts.frequency

        # Cache control
        self.force_refresh = force_refresh

        # Initialize GCP clients and resolver
        self.scc_client = get_gcp_security_center_client()
        self.control_resolver = ControlFrameworkResolver(framework=framework)

        # Initialize scope from options or GcpVariables
        scope_opts = scope_options or GCPScopeOptions()
        self._initialize_scope(scope_opts)

        logger.info("Initialized GCP Compliance Integration for %s", self.resource_name)
        logger.info("Framework: %s", framework)
        logger.info("Parent resource: %s", self.parent_resource)

    def _initialize_scope(self, scope_opts: GCPScopeOptions) -> None:
        """
        Initialize scan scope from options or GcpVariables.

        :param GCPScopeOptions scope_opts: Scope configuration options
        :raises ValueError: If neither project nor organization ID is configured
        """
        # Get scan scope from options or fall back to GcpVariables
        self.scan_type = scope_opts.scope if scope_opts.scope else str(GcpVariables.gcpScanType)  # type: ignore

        # Resolve organization_id
        self.organization_id = self._resolve_organization_id(scope_opts.organization_id)

        # Resolve project_id
        self.project_id = self._resolve_project_id(scope_opts.project_id)

        # Determine parent resource for SCC API calls
        self._set_parent_resource()

    def _resolve_organization_id(self, org_id: Optional[str]) -> Optional[str]:
        """Resolve organization ID from parameter or GcpVariables."""
        if org_id:
            return org_id
        if hasattr(GcpVariables, "gcpOrganizationId"):
            return str(GcpVariables.gcpOrganizationId)  # type: ignore
        return None

    def _resolve_project_id(self, proj_id: Optional[str]) -> Optional[str]:
        """Resolve project ID from parameter or GcpVariables."""
        if proj_id:
            return proj_id
        if hasattr(GcpVariables, "gcpProjectId"):
            return str(GcpVariables.gcpProjectId)  # type: ignore
        return None

    def _set_parent_resource(self) -> None:
        """Set parent resource based on scan type and IDs."""
        if self.scan_type == "project" and self.project_id:
            self.parent_resource = f"projects/{self.project_id}/sources/-"
            self.resource_id = self.project_id
            self.resource_name = f"GCP Project {self.project_id}"
        elif self.organization_id:
            self.parent_resource = f"organizations/{self.organization_id}/sources/-"
            self.resource_id = self.organization_id
            self.resource_name = f"GCP Organization {self.organization_id}"
        else:
            raise ValueError("Either gcpProjectId or gcpOrganizationId must be configured in init.yaml")

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch raw compliance data from GCP Security Command Center.

        Returns control-level compliance data aggregated from SCC findings.

        :return: List of raw compliance data (control + SCC findings)
        :rtype: List[Dict[str, Any]]
        """
        # Check cache first unless force refresh
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        if self.force_refresh:
            logger.info("Force refresh requested, fetching fresh data from GCP SCC...")

        try:
            compliance_data = self._fetch_fresh_compliance_data()
            self._save_to_cache(compliance_data)
            return compliance_data
        except Exception as e:
            logger.error(f"Error fetching compliance data from GCP SCC: {e}")
            return []

    def _fetch_fresh_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh compliance data from GCP Security Command Center.

        :return: List of raw compliance data
        :rtype: List[Dict[str, Any]]
        """
        logger.info("Fetching compliance data from GCP Security Command Center...")

        # Fetch all SCC findings
        scc_findings = self._fetch_scc_findings()

        # Group findings by control
        findings_by_control = self._group_findings_by_control(scc_findings)

        # Build compliance data structure
        compliance_data = self._build_compliance_data(findings_by_control)

        logger.info(f"Fetched {len(compliance_data)} control compliance items from GCP SCC")
        return compliance_data

    def _fetch_scc_findings(self) -> List[securitycenter_v1.Finding]:
        """
        Fetch findings from GCP Security Command Center.

        :return: List of SCC findings
        :rtype: List[securitycenter_v1.Finding]
        """
        logger.info(f"Fetching SCC findings from {self.parent_resource}...")

        request = securitycenter_v1.ListFindingsRequest(
            parent=self.parent_resource,
            filter='state="ACTIVE"',  # Only fetch active findings
        )

        findings = []
        try:
            finding_result_iterator = self.scc_client.list_findings(request=request)

            for finding_result in finding_result_iterator:
                findings.append(finding_result.finding)

            logger.info(f"Fetched {len(findings)} active findings from SCC")
        except Exception as e:
            logger.error(f"Error fetching findings from SCC: {e}")
            raise

        return findings

    def _group_findings_by_control(
        self, scc_findings: List[securitycenter_v1.Finding]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group SCC findings by control ID using the ControlFrameworkResolver.

        :param List[securitycenter_v1.Finding] scc_findings: SCC findings to group
        :return: Dictionary mapping control IDs to lists of findings
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        findings_by_control: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for finding in scc_findings:
            # Get category from finding
            category = finding.category

            # Map category to control IDs using resolver
            control_ids = self.control_resolver.get_controls_for_category(category)

            if not control_ids:
                logger.debug(f"No control mappings found for category: {category}")
                continue

            # Create finding dict for storage
            finding_dict = {
                "name": finding.name,
                "category": category,
                "state": finding.state.name,
                "severity": finding.severity.name,
                "resource_name": finding.resource_name,
                "description": finding.description,
                "external_uri": finding.external_uri,
                "create_time": finding.create_time.isoformat() if finding.create_time else None,
            }

            # Add finding to each mapped control
            for control_id in control_ids:
                findings_by_control[control_id].append(finding_dict)

        logger.info(f"Mapped {len(scc_findings)} findings to {len(findings_by_control)} controls")
        return findings_by_control

    def _build_compliance_data(self, findings_by_control: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Build compliance data structure from findings grouped by control.

        :param Dict[str, List[Dict[str, Any]]] findings_by_control: Findings grouped by control ID
        :return: List of compliance data items
        :rtype: List[Dict[str, Any]]
        """
        compliance_data = []

        # Get all controls from the framework to include controls with no findings
        all_control_ids = self.control_resolver.get_all_controls()

        for control_id in all_control_ids:
            # Get findings for this control (may be empty list)
            control_findings = findings_by_control.get(control_id, [])

            compliance_item_dict = {
                "control_id": control_id,
                "control_name": f"Control {control_id}",  # Will be enriched by RegScale lookup
                "scc_findings": control_findings,
                "resource_id": self.resource_id,
                "resource_name": self.resource_name,
            }

            compliance_data.append(compliance_item_dict)

        return compliance_data

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        """
        Create a ComplianceItem from raw compliance data.

        :param Dict[str, Any] raw_data: Raw compliance data (control + SCC findings)
        :return: ComplianceItem instance
        :rtype: ComplianceItem
        """
        control_id = raw_data.get("control_id", "")
        control_name = raw_data.get("control_name", "")
        scc_findings = raw_data.get("scc_findings", [])
        resource_id = raw_data.get("resource_id")
        resource_name = raw_data.get("resource_name")

        return GCPComplianceItem(
            control_id=control_id,
            control_name=control_name,
            framework=self.framework,
            scc_findings=scc_findings,
            resource_id=resource_id,
            resource_name=resource_name,
        )

    def _is_cache_valid(self) -> bool:
        """Check if the cache file exists and is within the TTL."""
        if not os.path.exists(GCP_COMPLIANCE_CACHE_FILE):
            return False

        file_age = time.time() - os.path.getmtime(GCP_COMPLIANCE_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS

        if is_valid:
            hours_old = file_age / 3600
            logger.info(f"Using cached GCP compliance data (age: {hours_old:.1f} hours)")

        return is_valid

    def _load_cached_data(self) -> List[Dict[str, Any]]:
        """Load compliance data from cache file."""
        try:
            with open(GCP_COMPLIANCE_CACHE_FILE, encoding="utf-8") as file:
                cached_data = json.load(file)
                logger.info(f"Loaded {len(cached_data)} compliance items from cache")
                return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file: {e}. Fetching fresh data.")
            return []

    def _save_to_cache(self, compliance_data: List[Dict[str, Any]]) -> None:
        """Save compliance data to cache file."""
        try:
            os.makedirs(os.path.dirname(GCP_COMPLIANCE_CACHE_FILE), exist_ok=True)

            with open(GCP_COMPLIANCE_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(compliance_data, file, indent=2, default=str)

            logger.info(f"Cached {len(compliance_data)} compliance items")
        except IOError as e:
            logger.warning(f"Error writing to cache file: {e}")

    def sync_compliance(self) -> None:
        """
        Sync compliance data from GCP SCC to RegScale.

        Extends the base sync_compliance method to add evidence collection.

        :return: None
        :rtype: None
        """
        # Call the base class sync_compliance to handle control assessments
        super().sync_compliance()

        # If evidence collection is enabled, collect evidence after compliance sync
        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            try:
                # Collect evidence based on mode
                if self.evidence_as_records:
                    logger.info("Creating individual Evidence records per control...")
                    self._collect_evidence_as_records()
                else:
                    logger.info("Creating consolidated evidence file for SSP...")
                    self._collect_evidence_as_ssp_attachment()
            except Exception as e:
                logger.error(f"Error during evidence collection: {e}", exc_info=True)

    def _collect_evidence_as_ssp_attachment(self) -> None:
        """
        Collect evidence and attach as file to SecurityPlan, with mappings to controls.

        Creates an Evidence record, uploads the evidence file, and maps it to both
        the SSP and all controls that have compliance data.

        :return: None
        :rtype: None
        """
        from regscale.core.app.api import Api
        from regscale.models.regscale_models.evidence import Evidence
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
        from regscale.models.regscale_models.file import File

        logger.info("Collecting evidence as SSP-level attachment with control mappings...")

        # Collect all evidence data
        all_evidence = self._collect_all_evidence_data()

        if not all_evidence:
            logger.warning("No evidence data collected")
            return

        # Generate filename
        scan_date = get_current_datetime(dt_format="%Y-%m-%d")
        safe_framework = self.framework.replace(" ", "_").replace("/", "_")
        file_name = f"gcp_scc_compliance_{safe_framework}_{scan_date}.jsonl.gz"

        # Compress evidence data
        jsonl_content = "\n".join([json.dumps(item, default=str) for item in all_evidence])

        compressed_buffer = BytesIO()
        with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
            gz_file.write(jsonl_content)

        compressed_data = compressed_buffer.getvalue()
        compressed_size_mb = len(compressed_data) / (1024 * 1024)
        uncompressed_size_mb = len(jsonl_content.encode("utf-8")) / (1024 * 1024)
        compression_ratio = (1 - (len(compressed_data) / len(jsonl_content.encode("utf-8")))) * 100

        logger.info(
            "Compressed evidence: %.2f MB -> %.2f MB (%.1f%% reduction)",
            uncompressed_size_mb,
            compressed_size_mb,
            compression_ratio,
        )

        # Create Evidence record
        due_date = (datetime.now() + timedelta(days=self.evidence_frequency)).isoformat()
        evidence = Evidence(
            title=f"GCP SCC Compliance Evidence - {safe_framework} - {scan_date}",
            description=self._build_ssp_evidence_description(all_evidence),
            status="Collected",
            updateFrequency=self.evidence_frequency,
            dueDate=due_date,
        )

        created_evidence = evidence.create()
        if not created_evidence or not created_evidence.id:
            logger.error("Failed to create evidence record")
            return

        logger.info("Created evidence record %d: %s", created_evidence.id, created_evidence.title)

        # Upload file to Evidence record
        api = Api()
        success = File.upload_file_to_regscale(
            file_name=file_name,
            parent_id=created_evidence.id,
            parent_module="evidence",
            api=api,
            file_data=compressed_data,
            tags=f"gcp,scc,compliance,{safe_framework.lower()}",
        )

        if success:
            logger.info(
                "Successfully uploaded evidence file '%s' to Evidence record %d", file_name, created_evidence.id
            )
        else:
            logger.warning("Failed to upload evidence file to Evidence record %d", created_evidence.id)

        # Map evidence to SSP
        ssp_mapping = EvidenceMapping(
            evidenceID=created_evidence.id,
            mappedID=self.plan_id,
            mappingType="securityplans",
        )
        ssp_mapping.create()
        logger.info("Mapped evidence %d to SSP %d", created_evidence.id, self.plan_id)

        # Map evidence to each control that has compliance data
        self._map_evidence_to_controls(created_evidence.id)

    def _map_evidence_to_controls(self, evidence_id: int) -> None:
        """
        Map evidence to controls based on compliance data.

        Uses the control lookup cache to find control implementations for all
        controls that have compliance data and creates EvidenceMapping records.

        :param int evidence_id: ID of the Evidence record to map
        :return: None
        :rtype: None
        """
        # Get all control IDs that have compliance data
        all_control_ids = set(self.passing_controls.keys()) | set(self.failing_controls.keys())

        if not all_control_ids:
            logger.warning("No controls with compliance data to map evidence to")
            return

        # Ensure control lookup cache is built
        if not self._ensure_control_lookup_cache():
            return

        # Log what we're looking for vs what's available
        logger.info("Looking for %d control IDs: %s", len(all_control_ids), sorted(all_control_ids)[:20])
        logger.info("Sample cache keys: %s", sorted(self._control_lookup_cache.keys())[:20])

        # Create mappings for each control
        controls_mapped = self._create_control_mappings(evidence_id, all_control_ids)

        # Log results
        self._log_mapping_results(evidence_id, controls_mapped)

    def _ensure_control_lookup_cache(self) -> bool:
        """
        Ensure control lookup cache is built.

        :return: True if cache is available, False otherwise
        :rtype: bool
        """
        if hasattr(self, "_control_lookup_cache") and self._control_lookup_cache:
            return True

        logger.info("Building control lookup cache for evidence mapping...")
        implementations = self._get_control_implementations()
        if implementations:
            self._build_control_lookup_cache(implementations)
        else:
            logger.warning("No implementations found, cannot build control lookup cache")

        if not hasattr(self, "_control_lookup_cache") or not self._control_lookup_cache:
            logger.warning("Control lookup cache could not be built, skipping control mappings")
            return False
        return True

    def _create_control_mappings(self, evidence_id: int, control_ids: set) -> List[str]:
        """
        Create evidence mappings for each control.

        :param int evidence_id: Evidence record ID
        :param set control_ids: Set of control IDs to map
        :return: List of successfully mapped control IDs
        :rtype: List[str]
        """
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping

        controls_mapped = []
        for control_id in control_ids:
            match = self._find_control_in_cache(control_id)
            if not match:
                continue

            matched_impl, matched_control = match
            mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=matched_impl.id, mappingType="controls")
            try:
                mapping.create()
                controls_mapped.append(matched_control.controlId)
            except Exception as e:
                logger.debug("Failed to create evidence mapping for control %s: %s", control_id, e)

        return controls_mapped

    def _find_control_in_cache(self, control_id: str) -> Optional[tuple]:
        """
        Find control implementation in cache using ID variations.

        :param str control_id: Control ID to look up
        :return: Tuple of (implementation, security_control) or None
        :rtype: Optional[tuple]
        """
        control_variations = self._control_matcher._get_control_id_variations(control_id)
        for variation in control_variations:
            if variation in self._control_lookup_cache:
                return self._control_lookup_cache[variation]
        return None

    def _log_mapping_results(self, evidence_id: int, controls_mapped: List[str]) -> None:
        """Log evidence mapping results."""
        if controls_mapped:
            display = ", ".join(sorted(controls_mapped)[:10])
            suffix = "..." if len(controls_mapped) > 10 else ""
            logger.info("Mapped evidence %d to %d controls: %s%s", evidence_id, len(controls_mapped), display, suffix)
        else:
            logger.warning("No control mappings created for evidence %d", evidence_id)

    def _build_ssp_evidence_description(self, evidence_items: List[Dict[str, Any]]) -> str:
        """
        Build HTML description for SSP-level evidence record.

        :param List[Dict[str, Any]] evidence_items: All evidence items
        :return: HTML description
        :rtype: str
        """
        active_count = sum(1 for e in evidence_items if e.get("state") == "ACTIVE")
        inactive_count = sum(1 for e in evidence_items if e.get("state") == "INACTIVE")

        # Get unique control IDs
        all_control_ids = sorted(set(self.passing_controls.keys()) | set(self.failing_controls.keys()))

        desc_parts = [
            f"{HTML_H3_OPEN}GCP Security Command Center Compliance Evidence{HTML_H3_CLOSE}",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self.framework}{HTML_P_CLOSE}",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Scan Date:{HTML_STRONG_CLOSE} {get_current_datetime(dt_format='%Y-%m-%d')}"
            f"{HTML_P_CLOSE}",
            f"{HTML_H4_OPEN}Summary{HTML_H4_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Evidence Items:{HTML_STRONG_CLOSE} {len(evidence_items)}"
            f"{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Active Findings:{HTML_STRONG_CLOSE} {active_count}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Inactive Findings:{HTML_STRONG_CLOSE} {inactive_count}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Controls Assessed:{HTML_STRONG_CLOSE} {len(all_control_ids)}"
            f"{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Passing Controls:{HTML_STRONG_CLOSE} {len(self.passing_controls)}"
            f"{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Failing Controls:{HTML_STRONG_CLOSE} {len(self.failing_controls)}"
            f"{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

        # Add control list
        if all_control_ids:
            desc_parts.append(f"{HTML_H4_OPEN}Controls with Evidence{HTML_H4_CLOSE}")
            desc_parts.append(HTML_P_OPEN)
            desc_parts.append(", ".join(c.upper() for c in all_control_ids[:30]))
            if len(all_control_ids) > 30:
                desc_parts.append(f" ... and {len(all_control_ids) - 30} more")
            desc_parts.append(HTML_P_CLOSE)

        return "\n".join(desc_parts)

    def _collect_evidence_as_records(self) -> None:
        """
        Collect evidence and create individual Evidence records per control.

        :return: None
        :rtype: None
        """
        from regscale.core.app.api import Api
        from regscale.models.regscale_models.evidence import Evidence
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
        from regscale.models.regscale_models.file import File

        logger.info("Collecting evidence as individual records per control...")

        # Collect evidence grouped by control
        evidence_by_control = self._collect_evidence_by_control()

        if not evidence_by_control:
            logger.warning("No evidence data collected")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d")
        safe_framework = self.framework.replace(" ", "_").replace("/", "_")
        api = Api()
        evidence_records_created = 0

        for control_id, control_evidence in evidence_by_control.items():
            # Filter by evidence_control_ids if specified
            if self.evidence_control_ids and control_id not in self.evidence_control_ids:
                continue

            try:
                # Create Evidence record
                title = f"GCP SCC Evidence - {control_id} - {scan_date}"
                description = self._build_evidence_description(control_id, control_evidence)
                due_date = (datetime.now() + timedelta(days=self.evidence_frequency)).isoformat()

                evidence = Evidence(
                    title=title,
                    description=description,
                    status="Collected",
                    updateFrequency=self.evidence_frequency,
                    dueDate=due_date,
                )

                created_evidence = evidence.create()
                if not created_evidence or not created_evidence.id:
                    logger.error(f"Failed to create evidence record for control {control_id}")
                    continue

                logger.info(f"Created evidence record {created_evidence.id}: {title}")

                # Compress and upload evidence file
                file_name = f"gcp_scc_evidence_{control_id}_{scan_date}.jsonl.gz"
                jsonl_content = "\n".join([json.dumps(item, default=str) for item in control_evidence])

                compressed_buffer = BytesIO()
                with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                    gz_file.write(jsonl_content)

                compressed_data = compressed_buffer.getvalue()

                success = File.upload_file_to_regscale(
                    file_name=file_name,
                    parent_id=created_evidence.id,
                    parent_module="evidence",
                    api=api,
                    file_data=compressed_data,
                    tags=f"gcp,scc,{control_id.lower()},{safe_framework.lower()}",
                )

                if success:
                    logger.info(f"Uploaded evidence file for control {control_id}")

                # Map evidence to SSP
                mapping = EvidenceMapping(
                    evidenceID=created_evidence.id, mappedID=self.plan_id, mappingType="securityplans"
                )
                mapping.create()
                logger.info(f"Linked evidence {created_evidence.id} to SSP {self.plan_id}")

                evidence_records_created += 1

            except Exception as ex:
                logger.error(f"Failed to create evidence record for control {control_id}: {ex}", exc_info=True)

        logger.info(f"Created {evidence_records_created} evidence record(s)")

    def _collect_all_evidence_data(self) -> List[Dict[str, Any]]:
        """
        Collect all evidence data for SSP-level attachment.

        :return: List of evidence items
        :rtype: List[Dict[str, Any]]
        """
        all_evidence = []

        # Fetch all SCC findings (including inactive ones for complete evidence)
        logger.info("Collecting evidence from all SCC findings...")

        request = securitycenter_v1.ListFindingsRequest(parent=self.parent_resource)

        try:
            finding_result_iterator = self.scc_client.list_findings(request=request)

            for finding_result in finding_result_iterator:
                finding = finding_result.finding

                evidence_item = {
                    "name": finding.name,
                    "category": finding.category,
                    "state": finding.state.name,
                    "severity": finding.severity.name,
                    "resource_name": finding.resource_name,
                    "description": finding.description,
                    "external_uri": finding.external_uri,
                    "create_time": finding.create_time.isoformat() if finding.create_time else None,
                    "event_time": finding.event_time.isoformat() if finding.event_time else None,
                }
                all_evidence.append(evidence_item)

        except Exception as e:
            logger.error(f"Error collecting evidence from SCC: {e}")

        logger.info(f"Collected {len(all_evidence)} evidence items")
        return all_evidence

    def _collect_evidence_by_control(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect evidence data grouped by control ID.

        :return: Dictionary mapping control_id to list of evidence items
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        evidence_by_control: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("Collecting evidence grouped by control...")

        # Fetch all SCC findings
        request = securitycenter_v1.ListFindingsRequest(parent=self.parent_resource)

        try:
            finding_result_iterator = self.scc_client.list_findings(request=request)

            for finding_result in finding_result_iterator:
                finding = finding_result.finding
                category = finding.category

                # Map category to control IDs
                control_ids = self.control_resolver.get_controls_for_category(category)

                if not control_ids:
                    continue

                evidence_item = {
                    "name": finding.name,
                    "category": category,
                    "state": finding.state.name,
                    "severity": finding.severity.name,
                    "resource_name": finding.resource_name,
                    "description": finding.description,
                    "external_uri": finding.external_uri,
                    "create_time": finding.create_time.isoformat() if finding.create_time else None,
                    "event_time": finding.event_time.isoformat() if finding.event_time else None,
                }

                # Add to each control this finding maps to
                for control_id in control_ids:
                    evidence_by_control[control_id].append(evidence_item)

        except Exception as e:
            logger.error(f"Error collecting evidence by control: {e}")

        logger.info(f"Collected evidence for {len(evidence_by_control)} controls")
        return evidence_by_control

    def _build_evidence_description(self, control_id: str, control_evidence: List[Dict[str, Any]]) -> str:
        """
        Build HTML description for evidence record.

        :param str control_id: Control ID
        :param List[Dict[str, Any]] control_evidence: Evidence items for this control
        :return: HTML description
        :rtype: str
        """
        active_count = sum(1 for e in control_evidence if e.get("state") == "ACTIVE")
        inactive_count = sum(1 for e in control_evidence if e.get("state") == "INACTIVE")

        desc_parts = [
            f"{HTML_H3_OPEN}GCP Security Command Center Evidence for Control {control_id}{HTML_H3_CLOSE}",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self.framework}{HTML_P_CLOSE}",
            f"{HTML_H4_OPEN}Summary{HTML_H4_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Evidence Items:{HTML_STRONG_CLOSE} {len(control_evidence)}"
            f"{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Active Findings:{HTML_STRONG_CLOSE} {active_count}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Inactive Findings:{HTML_STRONG_CLOSE} {inactive_count}"
            f"{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

        return "\n".join(desc_parts)

    def fetch_assets(self, **kwargs) -> Iterator[IntegrationAsset]:
        """
        Fetch assets from compliance items.

        For GCP compliance integration, we delegate to the base class which creates
        assets from compliance items.

        :param kwargs: Additional keyword arguments
        :return: Iterator of integration assets
        :rtype: Iterator[IntegrationAsset]
        """
        return super().fetch_assets(**kwargs)

    def fetch_findings(self, **kwargs) -> List[IntegrationFinding]:
        """
        Fetch findings from compliance items.

        For GCP compliance integration, we delegate to the base class which creates
        findings from failed compliance items.

        :param kwargs: Additional keyword arguments
        :return: List of integration findings
        :rtype: List[IntegrationFinding]
        """
        return list(super().fetch_findings(**kwargs))
