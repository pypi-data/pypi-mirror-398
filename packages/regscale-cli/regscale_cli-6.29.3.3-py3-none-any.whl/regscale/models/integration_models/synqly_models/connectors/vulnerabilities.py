"""Vulnerabilities Connector Model"""

from typing import Iterator, Optional, Union

from pydantic import ConfigDict

from regscale.integrations.scanner_integration import IntegrationAsset, IntegrationFinding, ScannerIntegration
from regscale.models.integration_models.synqly_models.synqly_model import SynqlyModel
from regscale.models.regscale_models import IssueSeverity


class VulnerabilitiesIntegration(ScannerIntegration):
    title = "Vulnerabilities Connector Integration"
    # Required fields from ScannerIntegration
    asset_identifier_field = "otherTrackingNumber"
    finding_severity_map = {
        # String severity values
        "Critical": IssueSeverity.Critical,
        "High": IssueSeverity.High,
        "Medium": IssueSeverity.Moderate,
        "Low": IssueSeverity.Low,
        # Integer severity values (OCSF severity_id scale: 0-5)
        5: IssueSeverity.Critical,  # Critical
        4: IssueSeverity.High,  # High
        3: IssueSeverity.Moderate,  # Medium
        2: IssueSeverity.Low,  # Low
        1: IssueSeverity.Low,  # Info/Low
        0: IssueSeverity.NotAssigned,  # Unknown
    }

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """
        Fetches assets from Synqly

        :yields: Iterator[IntegrationAsset]
        """
        integration_assets = kwargs.get("integration_assets")
        for asset in integration_assets:
            yield asset

    def fetch_findings(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetches findings from the Synqly

        :yields: Iterator[IntegrationFinding]
        """
        integration_findings = kwargs.get("integration_findings")
        for finding in integration_findings:
            yield finding


class Vulnerabilities(SynqlyModel):
    """Vulnerabilities Connector Model"""

    model_config = ConfigDict(populate_by_name=True, use_enum_values=True, arbitrary_types_allowed=True)

    integration_id: str = ""
    scanner_integration: Optional["VulnerabilitiesIntegration"] = None
    provider: str = ""
    can_fetch_assets: bool = False
    can_fetch_vulns: bool = False

    def __init__(self, integration: str, **kwargs):
        SynqlyModel.__init__(self, connector_type=self.__class__.__name__, integration=integration, **kwargs)
        self.integration_id = f"{self._connector_type.lower()}_{self.integration.lower()}"
        integration_company = self.integration.split("_")[0] if "_" in self.integration else self.integration  # noqa
        self.provider = integration_company
        self.can_fetch_assets = "query_assets" in self.capabilities
        self.can_fetch_vulns = "query_findings" in self.capabilities

    @staticmethod
    def _build_severity_filter(severity: Optional[Union[str, int]] = None) -> str:
        """
        Build severity filter string for Synqly queries

        :param Optional[Union[str, int]] severity: Minimum severity level, if None, defaults to 'low'
        :return: Comma-separated severity filter string
        :rtype: str
        """
        if severity is None:
            severity = "low"
        # Convert integer severity to string equivalent (OCSF severity_id scale: 0-5)
        if isinstance(severity, int):
            severity_int_map = {
                5: "critical",  # Fatal
                4: "high",  # Critical/High
                3: "medium",  # Medium
                2: "low",  # Low
                1: "info",  # Informational
                0: "info",  # Unknown
            }
            severity = severity_int_map.get(severity, "low")
        # Ensure severity is a string
        severity = str(severity)
        severity_map = {
            "critical": ["critical"],
            "high": ["high", "critical"],
            "medium": ["medium", "high", "critical"],
            "low": ["low", "medium", "high", "critical"],
            "info": ["info", "low", "medium", "high", "critical"],
        }
        # Check if severity starts with 'a' (for 'all')
        if severity and severity[0].lower() == "a":
            mapped_severities = list(severity_map.keys())
        else:
            mapped_severities = severity_map.get(severity.lower(), [severity])
        severity_filter = f"severity[in]{','.join(mapped_severities)}"
        return severity_filter

    def _translate_asset_filter(self, replace: str, replace_with: str, asset_filters: Optional[list[str]]) -> list[str]:
        """
        Translate asset filters to the correct format for the integration

        :param str replace: The string to replace
        :param str replace_with: The string to replace with
        :param list[str] asset_filters: The asset filters to translate
        :return: The translated asset filters
        :rtype: list[str]
        """
        translated_asset_filters = []
        for asset_filter in asset_filters:
            # Remove outer double quotes if present
            cleaned_filter = asset_filter
            if cleaned_filter.startswith('"') and cleaned_filter.endswith('"') and len(cleaned_filter) > 1:
                cleaned_filter = cleaned_filter[1:-1]
            if cleaned_filter.startswith("'") and cleaned_filter.endswith("'") and len(cleaned_filter) > 1:
                cleaned_filter = cleaned_filter[1:-1]

            if replace_with in cleaned_filter:
                possible_filter = cleaned_filter
            elif replace in cleaned_filter:
                possible_filter = cleaned_filter.replace(replace, replace_with)
                self.logger.debug(f"Translated filter: from {cleaned_filter} to {possible_filter}")
            else:
                continue
            valid_filter, _ = self.filter_parser.validate_filter(self.integration_id, possible_filter)
            if valid_filter:
                translated_asset_filters.append(possible_filter)
        return translated_asset_filters

    def _handle_scan_date_options(self, regscale_ssp_id: int, **kwargs) -> list[str]:
        """
        Handle scan date options for the integration sync process

        :param int regscale_ssp_id: The RegScale SSP ID
        :return: List of strings to filter vulnerabilities
        :rtype: list[str]
        """
        from regscale.integrations.commercial.tenablev2.utils import get_last_pull_epoch

        vuln_filter = [self._build_severity_filter(kwargs.get("minimum_severity_filter"))]

        if asset_filters := kwargs.get("filter", []):
            vuln_filter.extend(
                self._translate_asset_filter(replace="device.", replace_with="resources.", asset_filters=asset_filters)
            )

        if kwargs.get("all_scans"):
            vuln_filter.append("finding.last_seen_time[gte]915148800")  # Friday, January 1, 1999 12:00:00 AM UTC
        elif scan_date := kwargs.get("scan_date"):
            from regscale.core.utils.date import datetime_obj

            if scan_date := datetime_obj(scan_date):
                vuln_filter.append(f"finding.last_seen_time[gte]{int(scan_date.timestamp())}")
            else:
                vuln_filter.append(f"finding.last_seen_time[gte]{get_last_pull_epoch(regscale_ssp_id)}")
        else:
            vuln_filter.append(f"finding.last_seen_time[gte]{get_last_pull_epoch(regscale_ssp_id)}")
        return vuln_filter

    def _export_debug_data(self, data: list, data_type: str) -> None:
        """
        Export raw integration data to artifacts directory for debugging.

        :param list data: The raw data to export
        :param str data_type: Type of data (assets or findings)
        :rtype: None
        """
        import json
        import os
        from datetime import datetime as dt
        from pathlib import Path

        artifacts_dir = Path(os.getcwd()) / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        filename = artifacts_dir / f"{self.integration}_{data_type}_{timestamp}.json"

        # Convert data to JSON-serializable format
        serializable_data = []
        for item in data:
            if hasattr(item, "dict"):
                serializable_data.append(item.dict())
            elif hasattr(item, "__dict__"):
                serializable_data.append(str(item.__dict__))
            else:
                serializable_data.append(str(item))

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, default=str)

        self.logger.info(f"Exported {len(data)} {data_type} to {filename}")

    def integration_sync(self, regscale_ssp_id: int, **kwargs) -> None:
        """
        Runs the integration sync process

        :param int regscale_ssp_id: The RegScale SSP ID
        :rtype: None
        """
        vuln_filter = self._handle_scan_date_options(regscale_ssp_id=regscale_ssp_id, **kwargs)
        self.logger.debug(f"Vulnerability filter: {vuln_filter}")

        # Pop the filter from kwargs so it doesn't get passed to query_findings
        if asset_filter := kwargs.pop("filter", []):
            asset_filter = self._translate_asset_filter(
                replace="resources.", replace_with="device.", asset_filters=asset_filter
            )
            self.logger.debug(f"Asset filter: {asset_filter}")

        self.logger.info(f"Fetching asset data from {self.integration_name}...")
        assets = (
            self.fetch_integration_data(
                func=self.tenant.engine_client.vulnerabilities.query_assets,
                filter=asset_filter,  # Field-based filters only for assets
                **kwargs,
            )
            if self.can_fetch_assets
            else []
        )

        self.logger.info(f"Fetching vulnerability data from {self.integration_name}...")
        findings = (
            self.fetch_integration_data(
                func=self.tenant.engine_client.vulnerabilities.query_findings,
                filter=vuln_filter,  # Only severity/date filters for findings
                **kwargs,
            )
            if self.can_fetch_vulns
            else []
        )

        # Export raw data to artifacts directory for debugging
        if assets:
            self._export_debug_data(assets, "raw_assets")
        if findings:
            self._export_debug_data(findings, "raw_findings")

        self.scanner_integration = VulnerabilitiesIntegration(plan_id=regscale_ssp_id)
        self.logger.info(f"Mapping {self.provider} asset(s) data to RegScale asset(s)...")
        if assets:
            self.app.thread_manager.submit_tasks_from_list(
                func=self.mapper.to_regscale,
                items=assets,
                args=None,
                connector=self,
                regscale_ssp_id=regscale_ssp_id,
                **kwargs,
            )
            integration_assets = self.app.thread_manager.execute_and_verify(return_passed=True)
            self.logger.info(f"Mapped {len(integration_assets)} {self.provider} asset(s) to RegScale asset(s)...")
            self.scanner_integration.sync_assets(
                title=f"{self.integration_name} Vulnerabilities",
                plan_id=regscale_ssp_id,
                integration_assets=integration_assets,
                asset_count=len(integration_assets),
            )

        if findings:
            integration_findings = []
            self.logger.info(f"Mapping {self.provider} finding(s) data to RegScale finding(s)...")
            self.app.thread_manager.submit_tasks_from_list(
                func=self.mapper.to_regscale,
                items=findings,
                args=None,
                connector=self,
                regscale_ssp_id=regscale_ssp_id,
                **kwargs,
            )
            mapped_findings = self.app.thread_manager.execute_and_verify(return_passed=True)
            for finding in mapped_findings:
                if isinstance(finding, list):
                    integration_findings.extend(finding)
                else:
                    integration_findings.append(finding)
            self.logger.info(f"Mapped {len(integration_findings)} {self.provider} finding(s) to RegScale finding(s)...")
            self.scanner_integration.sync_findings(
                title=f"{self.integration_name} Vulnerabilities",
                plan_id=regscale_ssp_id,
                integration_findings=integration_findings,
                finding_count=len(integration_findings),
            )
        self.logger.info(f"[green]Sync from {self.integration_name} to RegScale completed.")

    def run_sync(self, *args, **kwargs) -> None:
        """
        Syncs RegScale issues with Vulnerability connector using Synqly

        :rtype: None
        """
        self.run_integration_sync(*args, **kwargs)
