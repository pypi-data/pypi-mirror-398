"""
Module to import and convert SARIF files to OCSF format using an API converter, and creating Vulnerability,
VulnerabilityMapping, and ScanHistory objects in RegScale.
"""

import datetime
import json
import os
from logging import getLogger
from typing import Any, Dict, Optional, Union

import requests
from pathlib import Path
from requests.exceptions import RequestException
from rich.progress import Progress
from synqly.engine.resources.ocsf.resources.v_1_3_0.resources.vulnerabilityfinding import Vulnerability as OcsfVuln
from synqly.engine.resources.ocsf.resources.v_1_5_0.resources.applicationsecurityposturefinding import (
    ApplicationSecurityPostureFinding,
)

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import (
    create_progress_object,
    check_file_path,
    check_license,
    error_and_exit,
    save_data_to,
    get_current_datetime,
)
from regscale.integrations.value_mappers import normalize_severity_to_vulnerability
from regscale.models import (
    Asset,
    IssueStatus,
    ScanHistory,
    SecurityPlan,
    Vulnerability,
    VulnerabilityMapping,
    VulnerabilitySeverity,
)
from regscale.validation.record import validate_regscale_object

logger = getLogger("regscale")


class SarifImporter:
    """
    Class to handle importing and converting SARIF files to OCSF format using an API converter. It then creates
    Vulnerability, VulnerabilityMapping, ScanHistory objects in RegScale.

    :param Path file_path: Path to the SARIF file or directory of files
    :param int asset_id: The RegScale Asset ID to import the findings to
    :param Union[datetime.datetime, str, None] scan_date: The scan date of the file (defaults to current date if None)
    :rtype: None
    """

    def __init__(self, file_path: Path, asset_id: int, scan_date: Union[datetime.datetime, str, None] = None) -> None:
        self.file_path: Path = file_path
        self.app: Application = check_license()
        if not scan_date:
            scan_date = get_current_datetime()
        if isinstance(scan_date, datetime.datetime):
            scan_date = scan_date.strftime("%Y-%m-%d")
        self.scan_date: str = scan_date
        self.token: Optional[str] = os.getenv("synqlyAccessToken") or self.app.config.get("synqlyAccessToken")
        if not self.token:
            error_and_exit("synqlyAccessToken environment variable or init.yaml value is required")
        if not validate_regscale_object(asset_id, Asset.get_module_string()):
            error_and_exit(f"Asset ID {asset_id} does not exist in RegScale.")
        self.asset: Asset = Asset.get_object(asset_id)
        self.parent_id = asset_id
        self.parent_module = Asset.get_module_slug()
        self.scan_history: Optional[ScanHistory] = None
        self.progress: Progress = create_progress_object()
        self.process_sarif_files()

    @staticmethod
    def load_sarif_file(file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a SARIF file from disk

        :param Path file_path: Path to the SARIF file
        :return: Parsed SARIF data as dictionary
        :rtype: Dict[str, Any]
        :raises: SystemExit if file cannot be loaded or parsed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:  # type: ignore
                sarif_data = json.load(file)

            # Basic validation that it's a SARIF file
            if not isinstance(sarif_data, dict) or "$schema" not in sarif_data:
                logger.warning("File may not be a valid SARIF file (missing $schema)")
            elif "sarif" not in sarif_data.get("$schema", "").lower():
                logger.warning("File may not be a valid SARIF file (schema doesn't contain 'sarif')")

            logger.debug("Successfully loaded SARIF file with %d runs", len(sarif_data.get("runs", [])))
            return sarif_data

        except FileNotFoundError:
            error_and_exit(f"SARIF file not found: {file_path}")
        except json.JSONDecodeError as e:
            error_and_exit(f"Failed to parse SARIF file as JSON: {e}")
        except Exception as e:
            error_and_exit(f"Failed to load SARIF file: {e}")

    def convert_sarif_to_ocsf(self, sarif_data: Dict[str, Any]) -> Optional[Any]:
        """
        Convert SARIF data to OCSF format using Synqly API

        :param Dict[str, Any] sarif_data: The SARIF data to convert
        :raises: SystemExit if API call fails
        :return: Converted data from Synqly API
        :rtype: Optional[Any]
        """
        api_url = "https://api.synqly.com/v1/mappings/apply"

        headers = {"content-type": "application/json", "authorization": f"Bearer {self.token}"}

        payload = {"mappings": ["synqly-default.sarif:1.5.0.0"], "data": sarif_data}

        try:
            logger.debug("Making API request to convert the data: %s", api_url)
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)  # 60 second timeout

            if response.status_code != 200:
                logger.error("API request failed with status %d: %s", response.status_code, response.text)

            converted_data = response.json()
            logger.debug("Successfully converted SARIF data using API.")
            logger.debug("Response status: %d, Content length: %d bytes", response.status_code, len(response.content))

            # get the results from the nested dictionary
            if mapping := converted_data.get("result", {}).get("mapping", {}):
                return mapping
            logger.error("Failed to convert SARIF data using API.")

        except RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_and_exit(f"API error ({e.response.status_code}): {error_detail}")
                except json.JSONDecodeError:
                    error_and_exit(f"API error ({e.response.status_code}): {e.response.text}")
            else:
                error_and_exit(f"Failed to connect to API: {e}")
        except json.JSONDecodeError:
            error_and_exit("Failed to parse API response as JSON")
        except Exception as e:
            error_and_exit(f"Unexpected error during SARIF conversion: {e}")

    def _process_single_sarif_file(
        self,
        sarif_file: Path,
        output_directory: Path,
    ) -> Dict[str, Any]:
        """
        Process a single SARIF file and return result information

        :param Path sarif_file: Path to the SARIF file to process
        :param Path output_directory: Output directory for converted files
        :return: Processing result information
        :rtype: Dict[str, Any]
        """
        try:
            sarif_data = self.load_sarif_file(sarif_file)
            logger.debug(f"Converting {sarif_file} data to OCSF data via API...")

            if "runs" in sarif_data and isinstance(sarif_data["runs"], list) and len(sarif_data["runs"]) > 0:
                # Process each run separately and collect results
                converted_data = [self.convert_sarif_to_ocsf(run) for run in sarif_data["runs"]]
            else:
                # Process the entire SARIF data as a single unit
                converted_data = self.convert_sarif_to_ocsf(sarif_data)

            # Save converted data
            output_file = output_directory / f"{sarif_file.stem}-converted.json"
            logger.debug("Saving converted data to: %s", output_file)

            save_data_to(
                file=output_file,
                data=converted_data,  # Only log save details in single file mode
            )

            created_count, updated_count = self._map_sarif_to_integration_findings(converted_data)

            return {
                "file": sarif_file.absolute(),
                "output": output_file.absolute(),
                "status": "success",
                "error": None,
                "created": created_count,
                "updated": updated_count,
            }

        except Exception as e:
            return {"file": sarif_file.absolute(), "output": None, "status": "failed", "error": str(e)}

    def process_sarif_files(
        self,
    ) -> None:
        """
        Unified function to process SARIF files (single or multiple) and convert them using an API converter

        :rtype: None
        """
        if self.file_path.is_file():
            sarif_files = [self.file_path]
        else:
            sarif_files = list(self.file_path.glob("*.sarif"))

        # Ensure output directory exists
        output_directory = self.file_path.parent / "converted"
        check_file_path(output_directory)

        # Initialize processing statistics
        successful_conversions = 0
        failed_conversions = 0
        processed_files = []

        if total_files := len(sarif_files):
            self.create_scan_history()
        else:
            error_and_exit(f"No SARIF files found in directory: {self.file_path}")
        if batch_mode := total_files > 1:
            logger.info("Found %d SARIF files to convert", total_files)

        # Process each SARIF file
        for idx, sarif_file in enumerate(sarif_files, 1):
            # Log progress for batch mode
            if batch_mode:
                logger.info("Processing file %d/%d: %s", idx, total_files, sarif_file.name)
            else:
                logger.info("Loading SARIF file: %s", sarif_file)

            # Process single file
            result = self._process_single_sarif_file(sarif_file, output_directory)
            processed_files.append(result)

            successful_conversions, failed_conversions = self._log_result_summary(
                result=result,
                successful_conversions=successful_conversions,
                failed_conversions=failed_conversions,
                batch_mode=batch_mode,
            )

        self.scan_history.save()
        if batch_mode:
            logger.info(
                "Batch conversion completed: %d successful, %d failed", successful_conversions, failed_conversions
            )
            logger.info("Converted files saved to: %s", output_directory.absolute())
        else:
            if successful_conversions == 1:
                logger.info(
                    "Conversion completed successfully. Converted file saved to: %s", output_directory.absolute()
                )
            else:
                error_and_exit("SARIF file conversion failed.")

    def create_scan_history(self) -> None:
        """
        Create a ScanHistory record for the SARIF import

        :rtype: None
        """
        if self.asset.parentModule == SecurityPlan.get_module_string():
            parent_id = self.asset.parentId
            parent_module: str = SecurityPlan.get_module_string()
        else:
            parent_id = self.asset.id
            parent_module = self.asset.parentModule
        self.scan_history = ScanHistory(
            parentId=parent_id,
            parentModule=parent_module,
            scanningTool="Sarif Scanner",
            scanDate=self.scan_date,
            tenantsId=Asset.get_tenant_id(),
            vLow=0,
            vMedium=0,
            vHigh=0,
            vCritical=0,
        ).create()

    @staticmethod
    def _log_result_summary(
        result: Dict[str, Any],
        successful_conversions: int,
        failed_conversions: int,
        batch_mode: bool,
    ) -> tuple[int, int]:
        """
        Log the result of a single SARIF file conversion and update statistics

        :param Dict[str, Any] result: The result of the conversion
        :param int successful_conversions: The number of successful conversions
        :param int failed_conversions: The number of failed conversions
        :param bool batch_mode: Whether running in batch mode (multiple files)
        :return: Updated counts of successful and failed conversions
        :rtype: tuple[int, int]
        """
        if result["status"] == "success":
            successful_conversions += 1
            logger.debug("Successfully converted: %s -> %s", result["file"], result["output"])
            logger.info(
                "Successfully converted: %s -> %s, %s created vulnerabilities and %s updated vulnerabilities",
                result["file"],
                result["output"],
                result["created"],
                result["updated"],
            )
        else:
            failed_conversions += 1
            if batch_mode:
                logger.error("Failed to convert %s: %s", result["file"], result["error"])
            else:
                error_and_exit(f"Failed to convert SARIF file: {result['error']}")
        return successful_conversions, failed_conversions

    def _map_sarif_to_integration_findings(
        self,
        converted_data: list[dict[str, Any]],
    ) -> tuple[int, int]:
        """
        Map converted SARIF data to a list of IntegrationFinding objects

        :param Any converted_data: The converted SARIF data from the API
        :return: Number of created and updated vulnerabilities
        :rtype: tuple[int, int]
        """
        create_vuln_count = 0
        updated_vuln_count = 0
        # Convert the nested dictionary to a list of ApplicationSecurityPostureFinding objects for easier parsing
        with self.progress as progress:
            task = progress.add_task("Mapping Sarif data to RegScale vulnerabilities...", total=len(converted_data))
            vulneribility_task = progress.add_task("Creating vulnerabilities and mappings...", total=0)
            for result in converted_data:
                name = self._parse_name(result)
                findings = ApplicationSecurityPostureFinding(**result).vulnerabilities
                progress.update(vulneribility_task, total=len(findings))
                for finding in findings:
                    created, vuln = Vulnerability(
                        title=finding.title,
                        severity=normalize_severity_to_vulnerability(finding.severity, source="SARIF"),
                        description=self._build_description(finding),
                        status=IssueStatus.Open,
                        firstSeen=self.scan_date,
                        lastSeen=self.scan_date,
                        plugInName=name,
                        plugInId=self._parse_plugin_id(finding),
                        parentId=self.parent_id,
                        parentModule=self.parent_module,
                    ).create_or_update_with_status()
                    self.update_scan_history_count(vuln.severity)
                    if created:
                        create_vuln_count += 1
                    else:
                        updated_vuln_count += 1
                    # Map vulnerability to asset
                    VulnerabilityMapping(
                        assetId=self.asset.id,
                        vulnerabilityId=vuln.id,
                        scanId=self.scan_history.id,
                        securityPlanId=self.asset.parentId if self.asset.parentModule == "securityplans" else None,
                        status=vuln.status,
                        firstSeen=vuln.firstSeen,
                        lastSeen=vuln.lastSeen,
                        dateCreated=self.scan_date,
                    ).create_or_update()
                    progress.update(vulneribility_task, advance=1)
                progress.update(task, advance=1)
        return create_vuln_count, updated_vuln_count

    @staticmethod
    def _parse_name(result: Dict[str, Any]) -> str:
        """
        Parse the name and version from the result metadata

        :param Dict[str, Any] result: The result to parse the name and version from
        :return: The name and version string
        :rtype: str
        """
        if metadata := result["metadata"]:
            name = metadata.get("product", {}).get("name", "Static Scanner")
            version = metadata.get("version")
        else:
            name = "Static Scanner"
            version = None
        name = f"{name} {version}" if version else name
        return name

    @staticmethod
    def _parse_plugin_id(finding: OcsfVuln) -> str:
        """
        Parse the plugin ID from the finding

        :param ocsf_vuln finding: The finding to parse the plugin ID from
        :return: The plugin ID string
        :rtype: str
        """
        if cwe := finding.cwe:
            return cwe.uid
        elif cve := finding.cve:
            return cve.uid
        return finding.title

    def update_scan_history_count(self, severity: str) -> None:
        """
        Update the scan history count for a given severity

        :param str severity: The severity of the vulnerability
        :rtype: None
        """
        # Use the same mapper to ensure consistency
        normalized_severity = normalize_severity_to_vulnerability(severity, source="SARIF")

        if normalized_severity == VulnerabilitySeverity.Low:
            self.scan_history.vLow += 1
        elif normalized_severity == VulnerabilitySeverity.Medium:
            self.scan_history.vMedium += 1
        elif normalized_severity == VulnerabilitySeverity.High:
            self.scan_history.vHigh += 1
        elif normalized_severity == VulnerabilitySeverity.Critical:
            self.scan_history.vCritical += 1
        else:
            self.scan_history.vInfo += 1

    @staticmethod
    def _build_description(finding: OcsfVuln) -> str:
        """
        Build a detailed description for a vulnerability finding

        :param ocsf_vuln finding: The finding to build the description for
        :return: Detailed description string
        :rtype: str
        """
        description_parts = [f"{finding.desc}\n"]
        for affected_code in getattr(finding, "affected_code", []):
            for key, value in affected_code.dict().items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        description_parts.append(f"file {sub_key}: {sub_value}\n")
                description_parts.append(f"{key}: {value}\n")
        return "".join(description_parts)
