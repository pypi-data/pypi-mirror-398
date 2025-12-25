"""Assets Connector Model"""

import re
from typing import Dict, List
import logging

from regscale.integrations.scanner_integration import (
    ScannerIntegration,
    ScannerIntegrationType,
)
from regscale.models.regscale_models import (
    IssueSeverity,
    ChecklistStatus,
)
from regscale.core.app.application import Application

# Sample Data object:
#    {
#    "hostname": "AAAAAAAAA",  # IntegrationAsset name
#    "serial": "A1A1A1A1",  # IntegrationAsset serial serial_number
#    "axonid": "cf119e6efe685999de4ee50bc23e3a4a", # IntegrationAsset identifier
#    "fisma": "DHQ-11111-GSS-11111", # IntegrationAsset notes
#    "ip": "1.1.1.1", # IntegrationAsset ip_address
#    "COMPLIANCE_TABLE": [
#        {
#            "CHECK":"", # IntegrationFinding plugin_name
#            "PLUGIN":"1368103", # IntegrationFinding plugin_id
#            "FISMA":"DHQ-11111-GSS-11111", # Field that maps to an SSP in RegScale
#            "ComplianceResult":"WARNING", # IntegrationFinding status
#            "CCI":"#CCI-000366", # IntegrationFinding cci_ref
#            "800-53r5":"#CM-6b.",    -| - # IntegrationFinding control_labels / affected_controls
#            "CSF":"#PR.IP-1",        _|
#            "VULID":"#V-253258", # IntegrationFinding external_id
#            "CAT":"#II", # IntegrationFinding severity
#            "STIG":"#WN11-00-000025", # IntegrationFinding vulnerability_number
#            "FIRST-SEEN":"2025-06-19T07:02:32+00:00", # vulnerability first_seen
#            "LAST-SEEN":"2025-08-12T07:02:25+00:00", # vulnerability last_seen
#            "COMPLIANCE-AUDIT-FILE":"DISA_STIG_Microsoft_Windows_11_v2r3.audit", # IntegrationFinding plugin_name
#            "COMPLIANCE-INFO":"An approved tool for continuous network scanning must be installed and...", # IntegrationFinding description
#            "COMPLIANCE-SOLUTION":"Install DOD-approved ESS software and ensure it is operating continuously."  # IntegrationFinding recommendation_for_mitigation
#        },
#        ]
#    }


class AxoniusIntegration(ScannerIntegration):
    from regscale.integrations.variables import ScannerVariables

    title = "Axonius"
    # Required fields from ScannerIntegration
    asset_identifier_field = "otherTrackingNumber"
    finding_severity_map = {
        "#I": IssueSeverity.Critical,
        "#II": IssueSeverity.High,
        "#III": IssueSeverity.Moderate,
        "#IV": IssueSeverity.Low,
        "I": IssueSeverity.Critical,
        "II": IssueSeverity.High,
        "III": IssueSeverity.Moderate,
        "IV": IssueSeverity.Low,
    }
    vuln_severity_map = {
        "CRITICAL": IssueSeverity.Critical,
        "HIGH": IssueSeverity.High,
        "MEDIUM": IssueSeverity.Moderate,
        "LOW": IssueSeverity.Low,
    }
    type = (
        ScannerIntegrationType.CHECKLIST
        if ScannerVariables.complianceCreation.lower() == "assessment"
        else ScannerIntegrationType.CONTROL_TEST
    )
    checklist_status_map = {
        "PASSED": ChecklistStatus.PASS,
        "WARNING": ChecklistStatus.FAIL,
        "FAIL": ChecklistStatus.FAIL,
    }
    app = Application()


def _is_valid_finding(finding: Dict) -> bool:
    """
    Check if a finding is valid for processing.

    :param Dict finding: The finding to validate
    :return: True if valid, False otherwise
    :rtype: bool
    """
    compliance_result = finding.get("ComplianceResult", "")
    control = finding.get("800-53r5", "")
    plugin = finding.get("PLUGIN", "")
    return compliance_result in ["PASSED", "FAILED"] and control != "" and plugin != ""


def _format_finding_as_asset_check(asset: Dict, finding: Dict, clean_control: str) -> Dict:
    """
    Format a finding into an asset check dictionary.

    :param Dict asset: The asset data
    :param Dict finding: The finding data
    :param str clean_control: The normalized control label
    :return: Formatted finding dictionary
    :rtype: Dict
    """
    compliance_result = finding.get("ComplianceResult", "FAILED")
    return {
        "asset_uuid": asset.get("axonid", ""),
        "first_seen": finding.get("FIRST-SEEN", ""),
        "last_seen": finding.get("LAST-SEEN", ""),
        "audit_file": finding.get("COMPLIANCE-AUDIT-FILE", ""),
        "check_id": finding.get("CCI", "").replace("#", ""),
        "check_name": "none",
        "status": "PASSED" if compliance_result == "PASSED" else "FAILED",
        "reference": [
            {
                "framework": "800-53r5",
                "control": clean_control,
            }
        ],
        "see_also": "NA",
        "plugin_id": finding.get("PLUGIN", ""),
        "state": "ACTIVE",
        "description": finding.get("COMPLIANCE-INFO", ""),
        "solution": finding.get("COMPLIANCE-SOLUTION", ""),
    }


def _process_failed_control(
    asset_check, ref, failed_temp: List, failing_controls: Dict, add_control_to_status_dict
) -> None:
    """
    Process a failed control and update tracking dictionaries.

    :param asset_check: The asset check object
    :param ref: The reference object
    :param List failed_temp: Temporary list of failed controls
    :param Dict failing_controls: Dictionary of failing controls
    :param add_control_to_status_dict: Function to add control to status dictionary
    :rtype: None
    """
    if asset_check.status == "FAILED" and ref.control not in failed_temp:
        failed_temp.append(ref.control)
        add_control_to_status_dict(
            control_id=ref.control,
            status=asset_check.status,
            dict_obj=failing_controls,
            desired_status="FAILED",
        )


def _ensure_framework_exists(framework_controls: Dict, framework: str) -> None:
    """
    Ensure a framework exists in the framework_controls dictionary.

    :param Dict framework_controls: Dictionary of framework controls
    :param str framework: The framework name
    :rtype: None
    """
    if framework not in framework_controls:
        framework_controls[framework] = []


def _process_control_status(
    ref,
    framework_controls: Dict,
    asset_check,
    passing_controls: Dict,
    failing_controls: Dict,
    asset_checks: Dict,
    add_control_to_status_dict,
) -> Dict:
    """
    Process control status and update tracking dictionaries.

    :param ref: The reference object
    :param Dict framework_controls: Dictionary of framework controls
    :param asset_check: The asset check object
    :param Dict passing_controls: Dictionary of passing controls
    :param Dict failing_controls: Dictionary of failing controls
    :param Dict asset_checks: Dictionary of asset checks
    :param add_control_to_status_dict: Function to add control to status dictionary
    :return: Updated passing_controls dictionary
    :rtype: Dict
    """
    if ref.control not in framework_controls[ref.framework]:
        framework_controls[ref.framework].append(ref.control)
        formatted_control_id = ref.control

        add_control_to_status_dict(
            control_id=formatted_control_id,
            status=asset_check.status,
            dict_obj=failing_controls,
            desired_status="FAILED",
        )
        add_control_to_status_dict(
            control_id=formatted_control_id,
            status=asset_check.status,
            dict_obj=passing_controls,
            desired_status="PASSED",
        )

        passing_controls = remove_passing_controls_if_failed(
            passing_controls=passing_controls, failing_controls=failing_controls
        )

        if formatted_control_id not in asset_checks:
            asset_checks[formatted_control_id] = [asset_check]
        else:
            asset_checks[formatted_control_id].append(asset_check)

    return passing_controls


def _process_asset_check_references(
    asset_check,
    failed_temp: List,
    framework_controls: Dict,
    failing_controls: Dict,
    passing_controls: Dict,
    asset_checks: Dict,
    add_control_to_status_dict,
) -> Dict:
    """
    Process all references in an asset check.

    :param asset_check: The asset check object
    :param List failed_temp: Temporary list of failed controls
    :param Dict framework_controls: Dictionary of framework controls
    :param Dict failing_controls: Dictionary of failing controls
    :param Dict passing_controls: Dictionary of passing controls
    :param Dict asset_checks: Dictionary of asset checks
    :param add_control_to_status_dict: Function to add control to status dictionary
    :return: Updated passing_controls dictionary
    :rtype: Dict
    """
    for ref in asset_check.reference:
        _process_failed_control(asset_check, ref, failed_temp, failing_controls, add_control_to_status_dict)
        _ensure_framework_exists(framework_controls, ref.framework)
        passing_controls = _process_control_status(
            ref,
            framework_controls,
            asset_check,
            passing_controls,
            failing_controls,
            asset_checks,
            add_control_to_status_dict,
        )

    return passing_controls


def _process_finding(
    asset: Dict,
    finding: Dict,
    failed_temp: List,
    framework_controls: Dict,
    failing_controls: Dict,
    passing_controls: Dict,
    asset_checks: Dict,
    asset_check_class,
    add_control_to_status_dict,
    logger,
) -> Dict:
    """
    Process a single finding from an asset.

    :param Dict asset: The asset data
    :param Dict finding: The finding data
    :param List failed_temp: Temporary list of failed controls
    :param Dict framework_controls: Dictionary of framework controls
    :param Dict failing_controls: Dictionary of failing controls
    :param Dict passing_controls: Dictionary of passing controls
    :param Dict asset_checks: Dictionary of asset checks
    :param asset_check_class: AssetCheck class
    :param add_control_to_status_dict: Function to add control to status dictionary
    :param logger: Logger instance
    :return: Updated passing_controls dictionary
    :rtype: Dict
    """
    if not _is_valid_finding(finding):
        return passing_controls

    clean_control = normalize_control(finding.get("800-53r5", ""))
    formatted_finding = _format_finding_as_asset_check(asset, finding, clean_control)
    asset_check = asset_check_class(**formatted_finding)

    if not asset_check.reference:
        logger.warning(f"Asset check {asset_check.check_name} has no references, skipping.")
        return passing_controls

    passing_controls = _process_asset_check_references(
        asset_check,
        failed_temp,
        framework_controls,
        failing_controls,
        passing_controls,
        asset_checks,
        add_control_to_status_dict,
    )

    return passing_controls


def sync_compliance_data(ssp_id: int, catalog_id: int, framework: str, axonius_object: Dict) -> None:
    """
    Sync the compliance data from Axonius to create control implementations for controls in frameworks.

    :param int ssp_id: The ID number from RegScale of the System Security Plan
    :param int catalog_id: The ID number from RegScale Catalog that the System Security Plan's controls belong to
    :param str framework: The framework to use. from Tenable.io frameworks MUST be the same RegScale Catalog of controls
    :param Dict axonius_object: The Axonius data object containing assets and compliance findings
    :rtype: None
    """
    from regscale.integrations.commercial.tenablev2.sync_compliance import (
        AssetCheck,
        add_control_to_status_dict,
        process_compliance_data,
    )

    logger = logging.getLogger("regscale")

    framework_controls: Dict[str, List[str]] = {}
    asset_checks: Dict[str, List[AssetCheck]] = {}
    passing_controls: Dict = {}
    failing_controls: Dict = {}
    failed_temp: List[str] = []

    for ind, asset in axonius_object.iterrows():  # type: ignore[attr-defined]
        for finding in asset.COMPLIANCE_TABLE:
            passing_controls = _process_finding(
                asset,
                finding,
                failed_temp,
                framework_controls,
                failing_controls,
                passing_controls,
                asset_checks,
                AssetCheck,
                add_control_to_status_dict,
                logger,
            )

    dict_of_frameworks_and_asset_checks = {
        key: {"controls": framework_controls, "asset_checks": asset_checks} for key in framework_controls.keys()
    }

    logger.info(f"Found {len(dict_of_frameworks_and_asset_checks)} findings to process")
    framework_data = dict_of_frameworks_and_asset_checks.get(framework, {})
    if framework_data:
        process_compliance_data(
            framework_data=framework_data,
            catalog_id=catalog_id,
            ssp_id=ssp_id,
            framework=framework,
            passing_controls=passing_controls,
            failing_controls=failing_controls,
        )
    else:
        logger.warning(f"No framework data found for framework: {framework}")


def normalize_control(control: str) -> str:
    """
    Takes a string like:
    AA-99, AA-99(99, #AA-99(99), AA-99a., #AA-99
    returns a string like:
    aa-99, aa-99(99)

    :param str control: messy control label
    :return: clean control label
    :return_typ: str
    """

    match = re.search(r"[A-Z]{2}-\d+\d?(?:\(\d+\d?)?", control)
    if not match:
        return control

    finding_control = match[0].lower()

    missing1 = re.search(r"\(", finding_control)
    missing2 = re.search(r"\)", finding_control)
    if missing1 and not missing2:
        finding_control = f"{finding_control})"

    return finding_control


def remove_passing_controls_if_failed(passing_controls: Dict, failing_controls: Dict) -> Dict:
    """
    Remove controls from passing_controls if they appear in failing_controls.

    :param Dict passing_controls: Dictionary of controls with passing status
    :param Dict failing_controls: Dictionary of controls with failing status
    :return: Updated passing_controls dictionary
    :rtype: Dict
    """
    to_remove = []
    for k in passing_controls.keys():
        if k in failing_controls.keys():
            to_remove.append(k)

    for k in to_remove:
        del passing_controls[k]

    return passing_controls
