"""
Module for Tenable CIS Benchmark checklist integration.

This module provides integration classes for importing CIS (Center for Internet Security)
benchmark compliance data from Tenable Security Center and Tenable.io into RegScale
as checklist items.
"""

import logging
from typing import Any, Generator, Iterator, List, Optional, Tuple

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.tenablev2.authenticate import gen_tio, gen_tsc
from regscale.integrations.commercial.tenablev2.cis_parsers import (
    parse_cis_compliance_result,
    parse_tenable_sc_cis_result,
)
from regscale.integrations.commercial.tenablev2.utils import get_filtered_severities
from regscale.integrations.scanner_integration import (
    IntegrationAsset,
    IntegrationFinding,
    ScannerIntegration,
    ScannerIntegrationType,
)
from regscale.models import regscale_models

logger = logging.getLogger("regscale")

# Constants
_PROGRESS_LOG_INTERVAL = 100  # Log progress every N findings


class TenableIOCISChecklistIntegration(ScannerIntegration):
    """
    Tenable.io CIS Benchmark Checklist Integration.

    This integration class fetches CIS benchmark compliance data from Tenable.io
    using the compliance export API and maps it to RegScale checklist items.

    Attributes:
        title: Integration title displayed in RegScale
        type: Integration type (CHECKLIST for compliance data)
        asset_identifier_field: Field name used for asset identification
    """

    title = "Tenable.io CIS Benchmarks"
    type = ScannerIntegrationType.CHECKLIST
    asset_identifier_field = "tenableId"

    # Map CIS compliance status to RegScale checklist status
    checklist_status_map = {
        "PASSED": regscale_models.ChecklistStatus.PASS,
        "FAILED": regscale_models.ChecklistStatus.FAIL,
        "WARNING": regscale_models.ChecklistStatus.NOT_REVIEWED,
        "ERROR": regscale_models.ChecklistStatus.FAIL,
        "NOT_APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
    }

    # Map severity levels for CIS findings
    finding_severity_map = {
        "critical": regscale_models.IssueSeverity.Critical,
        "high": regscale_models.IssueSeverity.High,
        "medium": regscale_models.IssueSeverity.Moderate,
        "low": regscale_models.IssueSeverity.Low,
    }

    def __init__(
        self,
        plan_id: int,
        tenant_id: int = 1,
        tags: Optional[List[Tuple[str, str]]] = None,
        audit_file_filter: Optional[str] = None,
        cis_level: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Tenable.io CIS Benchmark integration.

        :param int plan_id: The RegScale security plan ID
        :param int tenant_id: The RegScale tenant ID, defaults to 1
        :param Optional[List[Tuple[str, str]]] tags: Asset tags to filter by (e.g., [('environment', 'prod')])
        :param Optional[str] audit_file_filter: Filter for specific audit files (e.g., "CIS_AlmaLinux*")
        :param Optional[str] cis_level: Filter by CIS level ("1" or "2")
        :param Any kwargs: Additional keyword arguments
        """
        super().__init__(plan_id, tenant_id, **kwargs)
        self.client = None
        self.tags = tags or []
        self.audit_file_filter = audit_file_filter or "CIS_*"
        self.cis_level = cis_level
        self.scan_date = kwargs.get("scan_date", get_current_datetime())

    def authenticate(self) -> None:
        """Authenticate to Tenable.io."""
        self.client = gen_tio()

    def fetch_assets(self, **kwargs: Any) -> Iterator[IntegrationAsset]:
        """
        Fetch assets from Tenable.io.

        For CIS benchmark integration, assets are typically pre-existing in RegScale
        and linked via asset identifiers in the compliance findings.

        :param Any kwargs: Additional keyword arguments
        :yields: IntegrationAsset objects
        :return: Iterator of IntegrationAsset objects
        :rtype: Iterator[IntegrationAsset]
        """
        # CIS benchmark findings reference existing assets
        # Assets should be synced separately using the standard Tenable asset integration
        integration_assets = kwargs.get("integration_assets", [])
        yield from integration_assets

    def fetch_findings(self, **kwargs: Any) -> Generator[IntegrationFinding, None, None]:
        """
        Fetch CIS benchmark compliance findings from Tenable.io.

        Uses the Tenable.io compliance export API to retrieve CIS benchmark
        compliance check results and converts them to IntegrationFinding objects.

        :param Any kwargs: Additional keyword arguments
        :yields: IntegrationFinding objects
        :return: Generator of IntegrationFinding objects
        :rtype: Generator[IntegrationFinding, None, None]
        """
        logger.info("Fetching CIS benchmark compliance findings from Tenable.io...")

        self.authenticate()

        if not self.client:
            raise ValueError("Tenable.io client not authenticated")

        # Build filter criteria
        filters = {
            "audit_file_name": self.audit_file_filter,
            "compliance_results": ["FAILED", "WARNING"],  # Focus on non-passing checks
        }

        # Add tag filtering if specified
        if self.tags:
            filters["tags"] = self.tags

        # Fetch compliance export
        try:
            compliance_iterator = self.client.exports.compliance(**filters)

            findings_count = 0
            for compliance_finding in compliance_iterator:
                # Filter by CIS level if specified
                if self.cis_level:
                    audit_file = compliance_finding.get("audit_file", "")
                    if f"_L{self.cis_level}." not in audit_file:
                        continue

                # Convert compliance finding to IntegrationFinding
                if finding := self._parse_compliance_finding(compliance_finding):
                    findings_count += 1
                    if findings_count % _PROGRESS_LOG_INTERVAL == 0:
                        logger.info(f"Processed {findings_count} CIS compliance findings")
                    yield finding

            self.num_findings_to_process = findings_count
            logger.info(f"Total CIS compliance findings processed: {findings_count}")

        except Exception as e:
            logger.error(f"Error fetching CIS compliance findings: {str(e)}", exc_info=True)
            raise

    def _parse_compliance_finding(self, compliance_data: dict) -> Optional[IntegrationFinding]:
        """
        Parse a Tenable.io compliance finding into an IntegrationFinding.

        :param dict compliance_data: The compliance data from Tenable.io export
        :return: IntegrationFinding object or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        try:
            # Extract asset identifier
            asset_data = compliance_data.get("asset", {})
            asset_uuid = asset_data.get("uuid", "")
            asset_id = asset_data.get("id", "")
            asset_identifier = asset_uuid or asset_id

            if not asset_identifier:
                logger.warning("Compliance finding missing asset identifier, skipping")
                return None

            # Create base finding object
            finding = IntegrationFinding(
                asset_identifier=asset_identifier,
                control_labels=[],
                category="CIS Benchmark",
                plugin_name="",  # Will be set by parser
                title="",  # Will be set by parser
                description="",  # Will be set by parser
                severity=regscale_models.IssueSeverity.NotAssigned,  # Will be set by parser
                status=regscale_models.IssueStatus.Open,  # Will be set by parser
                first_seen=self.scan_date,
                last_seen=self.scan_date,
            )

            # Parse using CIS parser
            finding = parse_cis_compliance_result(compliance_data, finding)

            # Filter by severity if configured
            if finding.severity not in get_filtered_severities():
                return None

            return finding

        except Exception as e:
            logger.error(f"Error parsing CIS compliance finding: {str(e)}", exc_info=True)
            return None


class TenableSCCISChecklistIntegration(ScannerIntegration):
    """
    Tenable Security Center CIS Benchmark Checklist Integration.

    This integration class fetches CIS benchmark compliance data from Tenable Security Center
    using the analysis API and maps it to RegScale checklist items.

    Attributes:
        title: Integration title displayed in RegScale
        type: Integration type (CHECKLIST for compliance data)
        asset_identifier_field: Field name used for asset identification
    """

    title = "Tenable SC CIS Benchmarks"
    type = ScannerIntegrationType.CHECKLIST
    asset_identifier_field = "tenableId"

    # Map CIS compliance status to RegScale checklist status
    checklist_status_map = {
        "PASSED": regscale_models.ChecklistStatus.PASS,
        "FAILED": regscale_models.ChecklistStatus.FAIL,
        "WARNING": regscale_models.ChecklistStatus.NOT_REVIEWED,
        "ERROR": regscale_models.ChecklistStatus.FAIL,
        "NOT_APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
    }

    # Map severity levels (Tenable SC uses severity for compliance status)
    finding_severity_map = {
        "Info": regscale_models.IssueSeverity.NotAssigned,  # Passed checks
        "Low": regscale_models.IssueSeverity.Low,
        "Medium": regscale_models.IssueSeverity.Moderate,  # Manual/Warning checks
        "High": regscale_models.IssueSeverity.High,  # Failed checks
        "Critical": regscale_models.IssueSeverity.Critical,
    }

    # CIS benchmark plugin IDs
    CIS_PLUGIN_IDS = [
        "21156",  # Windows Compliance Checks
        "19506",  # Unix Compliance Checks
        "33814",  # Unix Compliance Checks (JSON)
        "21745",  # Policy compliance settings
    ]

    # CIS-related plugin families
    CIS_PLUGIN_FAMILIES = [
        "Policy Compliance",
        "Windows : SCAP",
        "SCAP Windows Compliance",
        "UNIX Compliance Checks",
    ]

    def __init__(
        self,
        plan_id: int,
        tenant_id: int = 1,
        query_id: Optional[int] = None,
        scan_date: Optional[str] = None,
        batch_size: int = 1000,
        cis_level: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the Tenable SC CIS Benchmark integration.

        :param int plan_id: The RegScale security plan ID
        :param int tenant_id: The RegScale tenant ID, defaults to 1
        :param Optional[int] query_id: The Tenable SC query ID containing CIS compliance data
        :param Optional[str] scan_date: The scan date for CIS assessment
        :param int batch_size: Batch size for processing, defaults to 1000
        :param Optional[str] cis_level: Filter by CIS level ("1" or "2")
        :param Any kwargs: Additional keyword arguments
        """
        super().__init__(plan_id, tenant_id, **kwargs)
        self.client = None
        self.query_id = query_id
        self.scan_date = scan_date or get_current_datetime()
        self.batch_size = batch_size
        self.cis_level = cis_level

    def authenticate(self) -> None:
        """Authenticate to Tenable Security Center."""
        self.client = gen_tsc()

    def fetch_assets(self, **kwargs: Any) -> Iterator[IntegrationAsset]:
        """
        Fetch assets from Tenable SC.

        For CIS benchmark integration, assets are typically pre-existing in RegScale
        and linked via asset identifiers in the compliance findings.

        :param Any kwargs: Additional keyword arguments
        :yields: IntegrationAsset objects
        :return: Iterator of IntegrationAsset objects
        :rtype: Iterator[IntegrationAsset]
        """
        # CIS benchmark findings reference existing assets
        integration_assets = kwargs.get("integration_assets", [])
        yield from integration_assets

    def _should_skip_finding(self, vuln: dict) -> bool:
        """
        Check if a finding should be skipped based on severity.

        :param dict vuln: The vulnerability data from Tenable SC
        :return: True if the finding should be skipped, False otherwise
        :rtype: bool
        """
        severity_name = vuln.get("severity", {}).get("name", "").lower()
        return severity_name in ["info"]  # Skip passed checks (Info severity)

    def _matches_cis_level_filter(self, finding: IntegrationFinding) -> bool:
        """
        Check if a finding matches the CIS level filter.

        :param IntegrationFinding finding: The finding to check
        :return: True if the finding matches the filter or no filter is set, False otherwise
        :rtype: bool
        """
        if not self.cis_level:
            return True
        return f"Level {self.cis_level}" in finding.baseline

    def _log_progress(self, findings_count: int) -> None:
        """
        Log progress at regular intervals.

        :param int findings_count: Current count of findings processed
        """
        if findings_count % _PROGRESS_LOG_INTERVAL == 0:
            logger.info(f"Processed {findings_count} CIS compliance findings")

    def fetch_findings(self, **kwargs: Any) -> Generator[IntegrationFinding, None, None]:
        """
        Fetch CIS benchmark compliance findings from Tenable SC.

        Uses the Tenable SC analysis API to retrieve CIS benchmark compliance
        check results and converts them to IntegrationFinding objects.

        :param Any kwargs: Additional keyword arguments
        :yields: IntegrationFinding objects
        :return: Generator of IntegrationFinding objects
        :rtype: Generator[IntegrationFinding, None, None]
        """
        logger.info("Fetching CIS benchmark compliance findings from Tenable SC...")

        self.authenticate()

        if not self.client:
            raise ValueError("Tenable SC client not authenticated")

        if not self.query_id:
            raise ValueError("query_id is required for Tenable SC CIS integration")

        # Query CIS compliance findings
        try:
            # Use analysis API with filters for CIS benchmarks
            results = self.client.analysis.vulns(
                ("benchmarkName", "=", "CIS"),  # Filter for CIS benchmarks
                ("pluginID", "=", ",".join(self.CIS_PLUGIN_IDS)),  # CIS plugin IDs
                tool="vulndetails",
                query_id=self.query_id,
            )

            findings_count = 0
            for vuln in results:
                # Skip passed checks (Info severity)
                if self._should_skip_finding(vuln):
                    continue

                # Parse the finding
                finding = self._parse_sc_finding(vuln)

                # Filter by CIS level and yield if valid
                if finding and self._matches_cis_level_filter(finding):
                    findings_count += 1
                    self._log_progress(findings_count)
                    yield finding

            self.num_findings_to_process = findings_count
            logger.info(f"Total CIS compliance findings processed: {findings_count}")

        except Exception as e:
            logger.error(f"Error fetching CIS compliance findings from Tenable SC: {str(e)}", exc_info=True)
            raise

    def _parse_sc_finding(self, vuln: dict) -> Optional[IntegrationFinding]:
        """
        Parse a Tenable SC vulnerability/compliance finding into an IntegrationFinding.

        :param dict vuln: The vulnerability data from Tenable SC analysis API
        :return: IntegrationFinding object or None if parsing fails
        :rtype: Optional[IntegrationFinding]
        """
        try:
            # Extract asset identifier
            asset_identifier = vuln.get("dnsName") or vuln.get("ip", "")

            if not asset_identifier:
                logger.warning("SC finding missing asset identifier, skipping")
                return None

            # Extract plugin information
            plugin_id = vuln.get("pluginID", "")
            plugin_output = vuln.get("pluginText", "")

            # Create base finding object
            finding = IntegrationFinding(
                asset_identifier=asset_identifier,
                control_labels=[],
                category="CIS Benchmark",
                plugin_name="",  # Will be set by parser
                title="",  # Will be set by parser
                description="",  # Will be set by parser
                severity=regscale_models.IssueSeverity.NotAssigned,  # Will be set by parser
                status=regscale_models.IssueStatus.Open,  # Will be set by parser
                plugin_id=plugin_id,
                first_seen=self.scan_date,
                last_seen=self.scan_date,
            )

            # Parse using Tenable SC CIS parser
            finding = parse_tenable_sc_cis_result(plugin_output, finding)

            # Filter by severity if configured
            if finding.severity not in get_filtered_severities():
                return None

            return finding

        except Exception as e:
            logger.error(f"Error parsing Tenable SC CIS finding: {str(e)}", exc_info=True)
            return None
