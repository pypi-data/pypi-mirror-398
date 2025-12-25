#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Axonius integration for RegScale CLI to sync assets"""

import json
import logging
import time
import warnings
from typing import Any, Dict, List, Set
from urllib.parse import urljoin

# Standard python imports
import click
import pandas as pd
import requests

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import save_to_json
from regscale.core.app.utils.file_utils import get_file_stream
from regscale.core.utils.date import date_str, datetime_str
from regscale.integrations.scanner_integration import (
    issue_due_date,
)
from regscale.integrations.variables import ScannerVariables
from regscale.models.regscale_models import (
    SecurityPlan,
    Catalog,
    ControlImplementation,
    SecurityControl,
    FormFieldValue,
)
from regscale.models.regscale_models.asset import Asset
from regscale.models.regscale_models.module import Module

warnings.filterwarnings("ignore")
logger = logging.getLogger("regscale")

FISMA_FIELD_NAME = "FISMA Id"  # Label of FISMA ID Custom Field with RegScale Instance
PATH_TO_FISMA_COMPLIANCE = [
    "adapters_data.gui.custom_fisma_DOT__DOT_id"
]  # Relative Path to FISMA ID Field within Axonius Compliance/Posture Dataset
PATH_TO_FISMA_VULNS = [
    "FISMA",
    0,
]  # Relative Path to FISMA ID Field within Axonius Vulnerabilities Dataset

# Constants for repeated literals
CONTENT_TYPE_JSON = "application/json"
BASIC_INFO_TAB = "Basic Info"
ERROR_MSG_DOMAIN_REQUIRED = "Domain configuration is required"
ERROR_MSG_TOKEN_REQUIRED = "Token configuration is required"
LOG_MSG_MAPPING_FISMA = "Mapping FISMA IDs to Systems"
FISMA_ID_COLUMN = "FISMA Id"  # DataFrame column name for FISMA ID


def _apply_ssl_verification_setting() -> bool:
    """
    Apply SSL verification setting from ScannerVariables.

    Returns:
        bool: SSL verification setting (True to verify, False to skip)
    """
    ssl_verify = getattr(ScannerVariables, "sslVerify", True)
    if not ssl_verify:
        logger.warning("SSL Verification has been disabled for Axonius integration.")
    return ssl_verify


def _parse_fisma_filter(fisma_filter: str) -> List[str]:
    """
    Parse comma-separated FISMA filter string into a list.

    :param str fisma_filter: Comma-separated list of FISMA IDs
    :return: List of trimmed FISMA IDs, or empty list if no filter
    :rtype: List[str]
    """
    if fisma_filter:
        return [fid.strip() for fid in fisma_filter.split(",")]
    return []


def _should_skip_fisma(fisma: str, ssp_id: int, include_list: List[str]) -> bool:
    """
    Determine if a FISMA ID should be skipped during processing.

    :param str fisma: FISMA ID to check
    :param int ssp_id: SSP ID (None if not found)
    :param List[str] include_list: List of FISMA IDs to include (empty means include all)
    :return: True if the FISMA should be skipped, False otherwise
    :rtype: bool
    """
    if ssp_id is None:
        logger.warning("Skipping FISMA %s: No SSP ID found", fisma)
        return True
    if include_list and fisma not in include_list:
        return True
    return False


def _process_findings_batches(
    findings: List[dict],
    domain: str,
    token: str,
    ssp_id: int,
    owner_id: str,
    batch_size: int = 2000,
) -> int:
    """
    Process findings in batches and send to RegScale API.

    :param List[dict] findings: List of finding dictionaries to process
    :param str domain: RegScale domain URL
    :param str token: Authorization token
    :param int ssp_id: Parent SSP ID
    :param str owner_id: Owner ID for issues
    :param int batch_size: Number of findings per batch (default 2000)
    :return: Total number of findings successfully processed
    :rtype: int
    """
    url = urljoin(domain, "/api/issues/batchCreateOrUpdate")
    headers = {"accept": CONTENT_TYPE_JSON, "Authorization": token}
    ssl_verify = _apply_ssl_verification_setting()

    finding_batches = [findings[i : i + batch_size] for i in range(0, len(findings), batch_size)]
    findings_processed = 0

    for batch_count, batch in enumerate(finding_batches, start=1):
        if batch_count % 2 == 0:
            logger.info("Issues Processed: %d", batch_count * batch_size)

        payload = {
            "issues": batch,
            "options": {
                "source": "Axonius_Posture",
                "uniqueKeyFields": ["pluginId"],
                "enableMopUp": True,
                "mopUpStatus": "Closed",
                "performValidation": True,
                "parentId": ssp_id,
                "parentModule": "securityplans",
                "batchSize": 1000,
                "poamCreation": False,
                "issueOwnerId": owner_id,
                "assetIdentifierFieldName": "name",
                "assetIdentifierPoamDisplay": "name",
            },
        }

        save_to_json("artifacts/sample_findings_payload.json", payload, False)
        response = requests.post(url, headers=headers, json=payload, verify=ssl_verify)

        try:
            findings_processed += response.json()["statistics"]["ValidCount"]
        except (KeyError, ValueError) as e:
            logger.error("Unable to parse API response for findings processing: %s", e)

    return findings_processed


def _process_vulnerabilities_batches(
    vulns: List[dict],
    domain: str,
    token: str,
    ssp_id: int,
    batch_size: int = 6000,
) -> int:
    """
    Process vulnerabilities in batches and send to RegScale API.

    :param List[dict] vulns: List of vulnerability dictionaries to process
    :param str domain: RegScale domain URL
    :param str token: Authorization token
    :param int ssp_id: Parent SSP ID
    :param int batch_size: Number of vulnerabilities per batch (default 5000)
    :return: Total number of vulnerabilities successfully processed
    :rtype: int
    """
    url = urljoin(domain, "/api/vulnerability/streamBatchCreateOrUpdate")
    headers = {
        "Authorization": token,
        "Content-Type": CONTENT_TYPE_JSON,
    }
    ssl_verify = _apply_ssl_verification_setting()

    vuln_batches = [vulns[i : i + batch_size] for i in range(0, len(vulns), batch_size)]
    vulns_processed = 0

    for batch_count, batch in enumerate(vuln_batches, start=1):
        if batch_count % 10 == 0:
            logger.info("Vulns Processed: %d", batch_count * batch_size)

        payload = {
            "vulnerabilities": batch,
            "options": {
                "source": "Axonius_Vulnerability",
                "uniqueKeyFields": ["cve", "parentId"],
                "enableMopUp": True,
                "mopUpStatus": "Closed",
                "batchSize": 1000,
                "enableAssetDiscovery": True,
                "suppressAssetNotFoundWarnings": True,
                "poamCreation": False,
                "assetIdentifierFieldName": "name",
                "assetIdentifierPoamDisplay": "name",
                "parentId": ssp_id,
                "parentModule": "securityplans",
            },
        }

        save_to_json("artifacts/sample_vulns_payload.json", payload, False)
        response = requests.post(url, headers=headers, json=payload, verify=ssl_verify)
        save_to_json("artifacts/vuln_response.json", response.json(), False)

        try:
            vulns_processed += response.json()["summary"]["totalProcessed"]
        except (KeyError, ValueError) as e:
            logger.error("Unable to parse API response for vulnerability processing: %s", e)

    return vulns_processed


def _verify_rbac_access(domain: str, token: str, ssp_id: int) -> None:
    """
    Verify and reset RBAC access control for a security plan.

    :param str domain: RegScale domain URL
    :param str token: Authorization token
    :param int ssp_id: Security Plan ID
    """
    logger.info("Verifying Access Control")
    url_rbac = urljoin(domain, f"/api/rbac/reset/16/{ssp_id}")
    headers = {
        "Authorization": token,
        "Content-Type": CONTENT_TYPE_JSON,
    }
    ssl_verify = _apply_ssl_verification_setting()

    response = requests.get(url_rbac, headers=headers, verify=ssl_verify)

    if response.status_code == 200:
        logger.info("Access Control Verified")


####################################################################################################
#
# SYNC ASSETS WITH AXONIUS (Leidos cleaned up Axonius Records)
# AXONIUS API Docs: https://developer.axonius.com/docs/overview
#
# Sample Data object:
#    {
#    "hostname": "AAAAAAAAA",  # IntegrationAsset name (will use ip address if no hostname)
#    "serial": "A1A1A1A1",  # IntegrationAsset serial serial_number (optional)
#    "axonid": "cf119e6efe685999de4ee50bc23e3a4a", # IntegrationAsset identifier
#    "ip": "1.1.1.1", # IntegrationAsset ip_address (optional)
#    "COMPLIANCE_TABLE": [
#        {
#            "CHECK":"", # IntegrationFinding plugin_name
#            "PLUGIN":"1368103", # IntegrationFinding plugin_id
#            "FISMA":"DHQ-11111-GSS-11111", # Field that maps to an SSP in RegScale
#            "ComplianceResult":"WARNING", # IntegrationFinding
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
#
####################################################################################################


# Create group to handle Axonius integration
@click.group()
def axonius():
    """Sync assets between Axonius and RegScale."""


@axonius.command(name="pull_data")
@click.option(
    "--s3_bucket",
    type=click.STRING,
    help="S3 bucket name for Axonius data storage",
    default="axonius-enterprise-core-repo",
    show_default=True,
)
@click.option(
    "--s3_prefix",
    type=click.STRING,
    help="S3 prefix/key for the vulnerability data file",
    default="DHS-MGMT-CDM-CSM-JSON-Export-Processed.json",
    show_default=True,
)
@click.option(
    "--local_path",
    type=click.STRING,
    help="Local path to save the downloaded file",
    default="artifacts/compliance.json",
    show_default=True,
)
def pull_data(s3_bucket: str, s3_prefix: str, local_path: str) -> None:
    """Pull Data From Axonius for Specified FISMA ID"""

    import regscale.core.app.utils.file_utils as s3Util
    from regscale.core.app.utils.app_utils import save_to_json

    # Axonius.pull_data(fisma_id=fisma_id)

    s3Util.download_from_s3(
        bucket=s3_bucket,
        prefix=s3_prefix,
        local_path=local_path,
        aws_profile="none",
    )

    with get_file_stream(local_path) as data_file:
        jsonstring = data_file.read()  # .replace("\\", "\\\\")
        json_file = json.loads(jsonstring)
        vulns_small = json_file[:10]

    save_to_json("artifacts/vulns_small.json", vulns_small, False)

    # Replace with read_file() from regscale.core.app.utils.file_utils.py


@axonius.command(name="pull_data_axonius")
@click.option(
    "--query_name",
    type=click.STRING,
    help="Name of saved query in axonius",
    default="RegScale Integration",
    show_default=True,
    required=True,
)
def pull_data_axonius(query_name: str) -> None:
    """Pull Data From Axonius for Specified FISMA ID"""

    start_time = time.time()

    app = Application()

    axonius_token = app.config.get("axoniusAccessToken")
    axonius_secret = app.config.get("axoniusSecretToken")
    axonius_url = app.config.get("axoniusUrl")
    url = urljoin(axonius_url, "/api/v2/assets/devices")

    payload = {
        "include_metadata": False,
        "include_details": False,
        "saved_query_name": query_name,
    }

    headers: dict = {"accept": CONTENT_TYPE_JSON, "api-key": axonius_token, "api-secret": axonius_secret}

    logger.info(f"Importing Assets from Axonius from Query: {query_name}")
    ssl_verify = _apply_ssl_verification_setting()
    response = requests.post(url, json=payload, headers=headers, verify=ssl_verify).json()

    file_name = "artifacts/axonius_data.json"

    # Write JSON data to the file using get_file_stream utility
    from regscale.core.app.utils.app_utils import save_to_json

    save_to_json(file_name, response, False)

    end_time = time.time()

    logger.info(f"Import Successful: Imported {len(response['assets'])} Assets")
    elapsed_time = end_time - start_time
    logger.info(f"Elapsed time: {elapsed_time:.2f} seconds")


@axonius.command(name="file_stats")
@click.option(
    "--filepath",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/compliance.json",
    show_default=True,
)
@click.option(
    "--filepath_vulns",
    "-f_vulns",
    type=click.STRING,
    help="Enter Axonius Vulnerabilities File Path",
    default="artifacts/vuln_skinny.json",
    show_default=True,
)
@click.option(
    "--component",
    type=click.STRING,
    help="Enter Component Name",
    default="HQ",
    show_default=True,
)
def file_stats(filepath: str, filepath_vulns: str, component: str):
    from regscale.core.app.utils.app_utils import save_to_json

    with get_file_stream(filepath) as data_file:
        jsonstring = data_file.read()
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object = pd.DataFrame(json_file)

    with get_file_stream(filepath_vulns) as data_file:
        jsonstring = data_file.read()
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_vulns = pd.DataFrame(json_file)

    axonius_vulns["fisma"] = axonius_vulns["FISMA"].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None
    )

    fisma_list_posture = list(set(axonius_object["fisma"]))

    asset_metrics = pd.DataFrame(columns=[FISMA_ID_COLUMN, "Posture Assets", "Vuln Assets", "Combined Assets"])

    for fisma in fisma_list_posture:
        assets_csm = list(axonius_object[axonius_object["fisma"] == fisma]["axonid"])
        posture_assets = len(list(set(assets_csm)))

        assets_vuln = list(axonius_vulns[axonius_vulns["fisma"] == fisma]["identifier"])
        vuln_assets = len(list(set(assets_vuln)))

        assets_total = len(list(set(assets_csm + assets_vuln)))

        logger.info(
            f"{fisma}: Posture Assets {posture_assets}, Vuln Assets {vuln_assets}, Combined Assets {assets_total}"
        )

        asset_metrics = pd.concat(
            [
                asset_metrics,
                pd.DataFrame(
                    [
                        {
                            FISMA_ID_COLUMN: fisma,
                            "Posture Assets": posture_assets,
                            "Vuln Assets": vuln_assets,
                            "Combined Assets": assets_total,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    save_to_json(f"artifacts/{component}_Asset_Metrics.json", asset_metrics.to_dict("records"), False)


def _process_asset_batches(
    assets: list[dict],
    domain: str,
    token: str,
    batch_size: int = 1000,
) -> tuple[int, int, int]:
    """
    Process asset batches and send to RegScale API.

    :param list[dict] assets: List of asset dictionaries to process
    :param str domain: RegScale domain URL
    :param str token: Authorization token
    :param int batch_size: Number of assets per batch (default 1000)
    :return: Tuple of (total_processed, created_count, updated_count)
    :rtype: tuple[int, int, int]
    """
    url = urljoin(domain, "/api/assets/batchCreateOrUpdate")
    headers = {"accept": CONTENT_TYPE_JSON, "Authorization": token}
    ssl_verify = _apply_ssl_verification_setting()

    asset_batches = [assets[i : i + batch_size] for i in range(0, len(assets), batch_size)]
    assets_created = 0
    assets_updated = 0
    assets_processed = 0

    for batch_count, batch in enumerate(asset_batches, start=1):
        if batch_count % 2 == 0:
            logger.info("Assets Processed: %d", batch_count * batch_size)

        payload = {
            "assets": batch,
            "options": {
                "source": "Axonius",
                "uniqueKeyFields": ["otherTrackingNumber"],
                "enableMopUp": False,
                "batchSize": 500,
                "mopUpStatus": "Off-Network",
            },
        }

        response = requests.post(url, headers=headers, json=payload, verify=ssl_verify)
        response_data = response.json()

        assets_processed += response_data["statistics"]["TotalAssets"]
        assets_created += response_data["statistics"]["CreatedCount"]
        assets_updated += response_data["statistics"]["UpdatedCount"]

    return assets_processed, assets_created, assets_updated


def _gather_assets_for_fisma(
    fisma: str,
    ssp_id: int,
    owner_id: str,
    axonius_object: pd.DataFrame,
    axonius_object_vuln: pd.DataFrame,
) -> tuple[list[dict], set[str]]:
    """
    Gather assets from both compliance and vulnerability datasets for a FISMA ID.

    :param str fisma: FISMA ID to gather assets for
    :param int ssp_id: Parent SSP ID
    :param str owner_id: Owner ID of desired Asset Owner
    :param pd.DataFrame axonius_object: Compliance dataset
    :param pd.DataFrame axonius_object_vuln: Vulnerability dataset
    :return: Tuple of (assets list, assets_checked set)
    :rtype: tuple[list[dict], set[str]]
    """
    assets: list[dict] = []
    assets_checked: set[str] = set()
    logger.info("Fetching Assets for %s", fisma)

    # Gather Assets in Compliance Dataset
    assets, assets_checked = add_assets_for_ingestion(
        axonius_object=axonius_object,
        fisma=fisma,
        assets=assets,
        assets_checked=assets_checked,
        owner_id=owner_id,
        ssp_id=ssp_id,
    )

    # Gather Assets in Vulnerabilities Dataset
    assets, assets_checked = add_assets_for_ingestion(
        axonius_object=axonius_object_vuln,
        fisma=fisma,
        owner_id=owner_id,
        ssp_id=ssp_id,
        assets=assets,
        assets_checked=assets_checked,
        asset_source="vulnerabilities",
    )

    return assets, assets_checked


@axonius.command(name="sync_assets")
@click.option(
    "--filepath",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/compliance.json",
    show_default=True,
)
@click.option(
    "--filepath_vuln",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/vuln_skinny.json",
    show_default=True,
)
@click.option(
    "--fisma_filter",
    type=click.STRING,
    help="Comma-separated list of FISMA IDs to include",
    default="",
    show_default=True,
)
def sync_assets(filepath: str, filepath_vuln: str, fisma_filter: str) -> None:
    """Sync Assets from Axonius into RegScale."""

    app = Application()

    domain = app.config.get("domain")
    if not domain:
        raise ValueError(ERROR_MSG_DOMAIN_REQUIRED)
    token = app.config.get("token")
    if not token:
        raise ValueError(ERROR_MSG_TOKEN_REQUIRED)
    owner_id = app.config.get("userId")
    Asset._x_api_version = "2"

    include_list = _parse_fisma_filter(fisma_filter)

    # Call the check_custom_fields to get the fieldFormValue
    custom_fields_basic_map = FormFieldValue.check_custom_fields([FISMA_FIELD_NAME], "securityplans", BASIC_INFO_TAB)
    logger.info(LOG_MSG_MAPPING_FISMA)
    # Call the following function to get the map of FISMA Ids to SSP Ids:
    ssp_map = retrieve_ssps_fisma_map(fisma_form_id=custom_fields_basic_map[FISMA_FIELD_NAME])

    logger.info("Reading input file...")
    with get_file_stream(filepath) as data_file:
        jsonstring = data_file.read()
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object = pd.DataFrame(json_file)

    with get_file_stream(filepath_vuln) as data_file:
        jsonstring = data_file.read()
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object_vuln = pd.DataFrame(json_file)

    # Get FISMA/SSP ID Data Map for Axonius Compliance Dataset
    system_ids_compliance = map_fisma_ids_to_system(axonius_object=axonius_object, ssp_map=ssp_map)

    # Get FISMA/SSP ID Data Map for Axonius Vuln Dataset
    system_ids_full = map_fisma_ids_to_system(
        axonius_object=axonius_object_vuln,
        ssp_map=ssp_map,
        system_ids=system_ids_compliance,
        path_to_fisma=PATH_TO_FISMA_VULNS,
    )

    logger.info("Found %d System(s) with Findings", len(system_ids_full))

    # Loop through FISMA IDs and import Assets
    for fisma, ssp_id in system_ids_full.items():
        if _should_skip_fisma(fisma, ssp_id, include_list):
            continue

        # Get List of Existing Assets in System
        existing_assets: List[Asset] = Asset.get_all_by_parent(parent_id=ssp_id, parent_module="securityplans")
        existing_asset_identifiers: Set[Any] = {
            existing_asset.otherTrackingNumber for existing_asset in existing_assets
        }

        assets, assets_checked = _gather_assets_for_fisma(
            fisma=fisma,
            ssp_id=ssp_id,
            owner_id=owner_id,
            axonius_object=axonius_object,
            axonius_object_vuln=axonius_object_vuln,
        )

        asset_mop_up(
            existing_assets=existing_assets,
            existing_asset_identifiers=existing_asset_identifiers,
            assets_checked=assets_checked,
        )

        logger.info("Creating/Updating %d Assets In RegScale", len(assets))

        assets_processed, assets_created, assets_updated = _process_asset_batches(
            assets=assets,
            domain=domain,
            token=token,
        )

        logger.info("Asset Ingestion Completed for %s", fisma)
        logger.info(
            "Assets Processed: %d, Assets Created: %d, Assets Updated: %d",
            assets_processed,
            assets_created,
            assets_updated,
        )


@axonius.command(name="sync_findings")
@click.option(
    "--fisma_filter",
    type=click.STRING,
    help="Comma-separated list of FISMA IDs to include",
    default="",
    show_default=True,
)
@click.option(
    "--filepath",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/compliance.json",
    show_default=True,
)
def sync_findings(filepath: str, fisma_filter: str) -> None:
    """Sync Compliance Findings from Axonius into RegScale."""
    from regscale.core.app.utils.app_utils import save_to_json

    from regscale.models.regscale_models import (
        IssueSeverity,
    )

    app = Application()

    domain = app.config.get("domain")
    if not domain:
        raise ValueError(ERROR_MSG_DOMAIN_REQUIRED)
    token = app.config.get("token")
    if not token:
        raise ValueError(ERROR_MSG_TOKEN_REQUIRED)
    owner_id = app.config.get("userId")

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

    include_list = _parse_fisma_filter(fisma_filter)

    # Call the check_custom_fields to get the fieldFormValue
    custom_fields_basic_map = FormFieldValue.check_custom_fields([FISMA_FIELD_NAME], "securityplans", BASIC_INFO_TAB)

    logger.info(LOG_MSG_MAPPING_FISMA)
    # # Call the following function to get the map of FISMA Ids to SSP Ids:
    ssp_map = retrieve_ssps_fisma_map(fisma_form_id=custom_fields_basic_map[FISMA_FIELD_NAME])

    with get_file_stream(filepath) as data_file:
        jsonstring = data_file.read()  # .replace("\\", "\\\\")
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object_comp = pd.DataFrame(json_file)

    # Get FISMA/SSP ID Data Map for Axonius Compliance Dataset
    system_ids = map_fisma_ids_to_system(axonius_object=axonius_object_comp, ssp_map=ssp_map)

    logger.info(f"Found {len(system_ids)} System(s) with Findings")

    findings_metrics = pd.DataFrame(columns=[FISMA_ID_COLUMN, "Posture Findings", "Findings Processed"])

    for fisma, ssp_id in system_ids.items():
        if _should_skip_fisma(fisma, ssp_id, include_list):
            continue

        logger.info(f"Syncing Findings for {fisma}")

        # Consolidate Compliance Finding by Asset
        axonius_object_fisma, asset_identifiers = consolidate_compliance_findings(
            axonius_object=axonius_object_comp, fisma=fisma
        )

        save_to_json("artifacts/asset_identifiers.json", asset_identifiers, False)

        findings = add_findings_for_ingestion(
            axonius_object=axonius_object_fisma,
            asset_identifiers=asset_identifiers,
            finding_severity_map=finding_severity_map,
            fisma=fisma,
            owner_id=owner_id,
            ssp_id=ssp_id,
        )

        logger.info(f"Sending {len(findings)} compliance issues to RegScale")
        save_to_json("artifacts/sample_findings.json", findings, False)

        findings_processed = _process_findings_batches(
            findings=findings,
            domain=domain,
            token=token,
            ssp_id=ssp_id,
            owner_id=owner_id,
        )

        logger.info(f"Findings Ingestion Completed for {fisma}")
        logger.info(f"Findings Successfully Processed: {findings_processed}")
        findings_metrics = pd.concat(
            [
                findings_metrics,
                pd.DataFrame(
                    [
                        {
                            FISMA_ID_COLUMN: fisma,
                            "Posture Findings": len(findings),
                            "Findings Processed": findings_processed,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    save_to_json("artifacts/ICE_Findings_Metrics.json", findings_metrics.to_dict("records"), False)


@axonius.command(name="sync_vulns")
@click.option(
    "--fisma_filter",
    type=click.STRING,
    help="Comma-separated list of FISMA IDs to include",
    default="",
    show_default=True,
)
@click.option(
    "--filepath",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/vuln_skinny.json",
    show_default=True,
)
def sync_vulns(filepath: str, fisma_filter: str) -> None:
    """Sync Assets from Axonius into RegScale."""
    from regscale.core.app.utils.app_utils import save_to_json

    app = Application()

    domain = app.config.get("domain")
    if not domain:
        raise ValueError(ERROR_MSG_DOMAIN_REQUIRED)
    token = app.config.get("token")
    if not token:
        raise ValueError(ERROR_MSG_TOKEN_REQUIRED)

    vuln_severity_map = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }

    include_list = _parse_fisma_filter(fisma_filter)

    # Call the check_custom_fields to get the fieldFormValue
    custom_fields_basic_map = FormFieldValue.check_custom_fields([FISMA_FIELD_NAME], "securityplans", BASIC_INFO_TAB)

    logger.info(LOG_MSG_MAPPING_FISMA)
    # Call the following function to get the map of FISMA Ids to SSP Ids:
    ssp_map = retrieve_ssps_fisma_map(fisma_form_id=custom_fields_basic_map[FISMA_FIELD_NAME])

    with get_file_stream(filepath) as data_file:
        jsonstring = data_file.read()
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object_vuln = pd.DataFrame(json_file)

    # Get FISMA/SSP ID Data Map for Axonius Vulnerability Dataset Dataset
    system_ids = map_fisma_ids_to_system(
        axonius_object=axonius_object_vuln, ssp_map=ssp_map, path_to_fisma=PATH_TO_FISMA_VULNS
    )

    logger.info(f"Found {len(system_ids)} System(s) with Findings")

    vuln_metrics = pd.DataFrame(columns=[FISMA_ID_COLUMN, "Vulnerabilities Exported", "Vulnerabilities Processed"])

    for fisma, ssp_id in system_ids.items():
        if _should_skip_fisma(fisma, ssp_id, include_list):
            continue

        logger.info(f"Syncing Vulns for {fisma}")

        axonius_object_fisma_vuln, asset_identifiers = consolidate_vulns(
            axonius_object=axonius_object_vuln, fisma=fisma
        )

        logger.info("Vulns Compiled")
        save_to_json("artifacts/vuln_asset_identifiers.json", asset_identifiers, False)

        vulns = add_vulns_for_ingestion(
            axonius_object=axonius_object_fisma_vuln,
            asset_identifiers=asset_identifiers,
            vuln_severity_map=vuln_severity_map,
            fisma=fisma,
            ssp_id=ssp_id,
        )

        logger.info(f"Sending {len(vulns)} vulnerabilties to RegScale")
        save_to_json("artifacts/sample_vulns.json", vulns, False)

        vulns_processed = _process_vulnerabilities_batches(
            vulns=vulns,
            domain=domain,
            token=token,
            ssp_id=ssp_id,
        )

        logger.info(f"Vulns Ingestion Completed for {fisma}")
        logger.info(f"Vulns Successfully Processed: {vulns_processed}")

        _verify_rbac_access(domain, token, ssp_id)
        vuln_metrics = pd.concat(
            [
                vuln_metrics,
                pd.DataFrame(
                    [
                        {
                            FISMA_ID_COLUMN: fisma,
                            "Vulnerabilities Exported": len(vulns),
                            "Vulnerabilities Processed": vulns_processed,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    save_to_json("artifacts/ICE_Vuln_Metrics.json", vuln_metrics.to_dict("records"), False)


@axonius.command(name="sync_compliance")
@click.option(
    "--filepath",
    "-f",
    type=click.STRING,
    help="Enter Axonius Findings File Path",
    default="artifacts/compliance.json",
    show_default=True,
)
@click.option(
    "--fisma_filter",
    type=click.STRING,
    help="Comma-separated list of FISMA IDs to include",
    default="",
    show_default=True,
)
def sync_compliance(filepath: str, fisma_filter: str) -> None:
    """Sync Compliance Objects from Axonius into RegScale. Creates Assessments and Marks Relevant Controls"""
    import regscale.models.integration_models.axonius_models.connectors.assets as Axonius

    include_list = _parse_fisma_filter(fisma_filter)

    # Call the check_custom_fields to get the fieldFormValue
    custom_fields_basic_map = FormFieldValue.check_custom_fields([FISMA_FIELD_NAME], "securityplans", BASIC_INFO_TAB)

    logger.info(LOG_MSG_MAPPING_FISMA)
    # # Call the following function to get the map of FISMA Ids to SSP Ids:
    ssp_map = retrieve_ssps_fisma_map(fisma_form_id=custom_fields_basic_map[FISMA_FIELD_NAME])

    with get_file_stream(filepath) as data_file:
        jsonstring = data_file.read().replace("\\", "\\\\")
        json_file = json.loads(jsonstring)

    # Set json data into Pandas DataFrame
    axonius_object = pd.DataFrame(json_file)

    # Get FISMA/SSP ID Data Map for Axonius Compliance Dataset
    system_ids = map_fisma_ids_to_system(axonius_object=axonius_object, ssp_map=ssp_map)

    logger.info(f"Found {len(system_ids)} System(s) with Findings")

    catatlog_framework_map = retrieve_name_by_catalog_map()

    for fisma, ssp_id in system_ids.items():
        if _should_skip_fisma(fisma, ssp_id, include_list):
            continue

        logger.info(f"Syncing Compliance for {fisma}")

        axonius_object_fisma = pd.DataFrame()
        for ind, asset in axonius_object.iterrows():
            if get_nested_value(asset, PATH_TO_FISMA_COMPLIANCE) == fisma:
                axonius_object_fisma = pd.concat([axonius_object_fisma, pd.DataFrame([asset])], ignore_index=True)

        try:
            catalog_id = get_catalog_by_ssp(ssp_id=ssp_id)
        except (KeyError, IndexError, AttributeError) as e:
            logger.error(f"Catalog not found for {fisma}: {e}")
            continue
        framework = catatlog_framework_map.get(catalog_id)
        if not framework:
            logger.error(f"Framework not found for catalog {catalog_id}")
            continue
        Axonius.sync_compliance_data(
            ssp_id=ssp_id, catalog_id=catalog_id, framework="800-53r5", axonius_object=axonius_object_fisma
        )


def retrieve_ssps_fisma_map(fisma_form_id: int) -> dict:
    """
    Retreives a list of the SSPs in RegScale
    Returns a map of SSP Fisma Ids: RegScale Id

    :param int fisma_form_id: The RegScale Form Id of FISMA Id
    :param int tab_id: The RegScale tab id
    :return: dictionary of FISMA ID: regscale_ssp_id
    :return_type: dict
    """
    tab = Module.get_tab_by_name(regscale_module_name="securityplans", regscale_tab_name=BASIC_INFO_TAB)

    fisma_map = {}
    ssps = SecurityPlan.get_ssp_list()
    form_values = []
    for ssp in ssps:
        form_values = FormFieldValue.get_field_values(
            record_id=ssp.get("id"), module_name=SecurityPlan.get_module_slug(), form_id=tab.id
        )

        for form in form_values:
            if form.formFieldId == fisma_form_id and form.data:
                fisma_map[form.data] = ssp.get("id")
        form_values = []
    return fisma_map


def get_catalog_by_ssp(ssp_id: int) -> int:
    """
    Return the catalog id for an SSP

    :param int ssp_id: The id of the Security Plan
    :return: catalog Id
    :return_type: int
    """

    controls = ControlImplementation.get_list_by_plan(plan_id=ssp_id)
    if controls:
        control_id = controls[000].controlID
        control = SecurityControl.get_object(object_id=control_id)
        catalog_id = control.catalogueId

    return catalog_id


def retrieve_name_by_catalog_map() -> dict:
    """
    Return a map of Catalog Ids to Frameworks

    :return: dictionary of Catalog Id: framework name
    :return_type: dict
    """
    catalogs = Catalog.get_list()

    # Need to expand this list
    # Title of RegScale catalog to Axonius list of frameworks
    framework_map = {
        "NIST 800-53 Revision 4: Security and Privacy Controls for Federal Information Systems and Organizations": "800-53",
        "NIST SP 800-53 Rev 5 Controls and SP 800-53A Rev 5 Assessment Procedures": "800-53r5",
    }

    catalog_map = {}

    for catalog in catalogs:
        framework = framework_map.get(catalog.title)
        if framework:
            catalog_map[catalog.id] = framework

    return catalog_map


def _map_single_fisma_to_system(fisma_id: str, ssp_map: dict):
    """
    Map a single FISMA ID to its corresponding system ID.

    :param str fisma_id: FISMA ID to map
    :param dict ssp_map: System-Level map of FISMA IDs to SSP IDs
    :return: System ID if found, None otherwise
    """
    if not fisma_id:
        return None

    try:
        return ssp_map.get(fisma_id)
    except (KeyError, IndexError) as e:
        logger.debug("Unable to map FISMA ID %s: %s", fisma_id, e)
        return None


def map_fisma_ids_to_system(
    axonius_object: pd.DataFrame, ssp_map: dict, system_ids: dict = None, path_to_fisma: list = None
) -> dict:
    """
    Return a map of FISMA IDs in the dataset to System IDs

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param dict ssp_map: System-Level map of FISMA IDs to SSP IDs
    :param dict system_ids: Existing system_id map (if pulling from multiple datasets), defaults to None
    :param list path_to_fisma: Path to FISMA ID in dataset object, entered as a list of keys

    :return: dictionary of FISMA Mapppings: system_ids
    :return_type: dict
    """
    system_ids = system_ids if system_ids is not None else {}
    path_to_fisma = path_to_fisma if path_to_fisma is not None else PATH_TO_FISMA_COMPLIANCE

    # Create FISMA ID:System ID map
    for ind, asset in axonius_object.iterrows():
        fisma_id = get_nested_value(asset, path_to_fisma)
        mapped_id = _map_single_fisma_to_system(fisma_id, ssp_map)

        if mapped_id is not None:
            system_ids[fisma_id] = mapped_id

    # Remove FISMA IDs that are not mapped to an SSP in RegScale
    return {k: v for k, v in system_ids.items() if v is not None}


def get_nested_value(data_dict: dict, path_keys: list):
    """
    Return a nested dict value given list of nestings

    :param dict data_dict: Full Input Dict
    :param list path_keys: Key Nesting, given as list

    :return: Value at Nested Location
    """
    current_level = data_dict
    for key in path_keys:
        try:
            current_level = current_level[key]
        except Exception:
            if isinstance(current_level, str):
                return current_level
            else:
                return ""

    return current_level


def _process_compliance_assets(
    axonius_object: pd.DataFrame,
    fisma: str,
    owner_id: str,
    ssp_id: int,
    assets: list[dict],
    assets_checked: set,
) -> tuple[list[dict], set]:
    """
    Process compliance assets from Axonius dataset.

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for
    :param str owner_id: Owner ID of desired Asset Owner
    :param int ssp_id: ID of Parent SSP
    :param list[dict] assets: List of assets being accumulated
    :param set assets_checked: Set of asset identifiers already processed
    :return: Tuple of (assets list, assets_checked set)
    :rtype: tuple[list[dict], set]
    """
    for ind, asset in axonius_object.iterrows():
        fisma_value = get_nested_value(asset, PATH_TO_FISMA_COMPLIANCE)
        if fisma_value != fisma:
            continue

        assets.append(
            {
                "name": asset["specific_data.data.name"][0],
                "otherTrackingNumber": asset["specific_data.data.hostname_preferred"][0],
                "assetOwnerId": owner_id,
                "ipAddress": asset.get("specific_data.data.network_interfaces.ips_v4", "")[0],
                "macAddress": asset.get("specific_data.data.network_interfaces.mac_preferred", "")[0],
                "operatingSystem": asset.get("operating_system", None),
                "notes": fisma_value,
                "status": "Active (On Network)",
                "assetCategory": "Hardware" if asset.get("labels", "") != "" else "Software",
                "assetType": "Other",
                "bLatestScan": True,
                "scanningTool": "Axonius",
                "source": "Axonius",
                "parentModule": "securityplans",
                "parentId": ssp_id,
            }
        )
        assets_checked.add(asset["axonid"])

    return assets, assets_checked


def _should_process_vulnerability_asset(asset: pd.Series, fisma: str, assets_checked: set) -> bool:
    """
    Check if a vulnerability asset should be processed.

    :param pd.Series asset: Asset row from DataFrame
    :param str fisma: FISMA ID to match
    :param set assets_checked: Set of already processed asset identifiers
    :return: True if asset should be processed, False otherwise
    :rtype: bool
    """
    fisma_value = get_nested_value(asset, PATH_TO_FISMA_VULNS)
    if fisma_value != fisma:
        return False

    if asset["identifier"] in assets_checked:
        return False

    if pd.isna(asset["dnsname"]):
        return False

    return True


def _process_vulnerability_assets(
    axonius_object: pd.DataFrame,
    fisma: str,
    owner_id: str,
    ssp_id: int,
    assets: list[dict],
    assets_checked: set,
) -> tuple[list[dict], set]:
    """
    Process vulnerability assets from Axonius dataset.

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for
    :param str owner_id: Owner ID of desired Asset Owner
    :param int ssp_id: ID of Parent SSP
    :param list[dict] assets: List of assets being accumulated
    :param set assets_checked: Set of asset identifiers already processed
    :return: Tuple of (assets list, assets_checked set)
    :rtype: tuple[list[dict], set]
    """
    for ind, asset in axonius_object.iterrows():
        try:
            if not _should_process_vulnerability_asset(asset, fisma, assets_checked):
                continue

            fisma_value = get_nested_value(asset, PATH_TO_FISMA_VULNS)
            assets.append(
                {
                    "name": asset["dnsname"],
                    "otherTrackingNumber": asset["identifier"],
                    "assetOwnerId": owner_id,
                    "notes": fisma_value,
                    "status": "Active (On Network)",
                    "assetCategory": "Hardware",
                    "assetType": "Other",
                    "bLatestScan": True,
                    "scanningTool": "Axonius",
                    "source": "Axonius",
                    "parentModule": "securityplans",
                    "parentId": ssp_id,
                }
            )
            assets_checked.add(asset["identifier"])
        except (KeyError, TypeError) as e:
            logger.debug("Unable to process vulnerability asset: %s", e)
            continue

    return assets, assets_checked


def add_assets_for_ingestion(
    axonius_object: pd.DataFrame,
    fisma: str,
    owner_id: str,
    ssp_id: int,
    assets: list[Asset] = None,
    assets_checked: set = None,
    asset_source: str = "compliance",
):
    """
    Compile List of Assets to be ingested from Axonius Dataset

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for
    :param str owner_id: Owner ID of desired Asset Owner
    :param str ssp_id: ID of Parent SSP
    :param list[Asset] assets: Seed list of Assets, defaults to None but can add list in the case of pulling from multiple datasets
    :param set assets_checked: Seed checked assets, defaults to None but can add list in the case of pulling from multiple datasets
    :param str asset_source: asset source to define asset mapping, currently limited to "compliance" or "vulnerabilities"

    :return: list of asset objects to be fed into ingestion
    """
    if assets is None:
        assets = []
    if assets_checked is None:
        assets_checked = set()

    if asset_source == "compliance":
        return _process_compliance_assets(axonius_object, fisma, owner_id, ssp_id, assets, assets_checked)
    elif asset_source == "vulnerabilities":
        return _process_vulnerability_assets(axonius_object, fisma, owner_id, ssp_id, assets, assets_checked)
    else:
        logger.error("Asset Source must be either 'compliance' or 'vulnerabilities'")
        return assets, assets_checked


def asset_mop_up(
    existing_assets: list[Asset],
    existing_asset_identifiers: set,
    assets_checked: set,
    mop_up_status: str = "Off-Network",
):
    """
    Mop Up assets that do not appear in current scan, set to defined "mop_up_status"

    :param list[Asset] existing_assets: List of assets that currently exist in SSP
    :param set existing_asset_identifiers: set of existing asset ids
    :param set assets_checked: set of asset ids in current scan
    :param str mop_up_status: Status to set deactivated asset to

    """
    inactive_assets = existing_asset_identifiers.difference(assets_checked)
    assets_to_deactivate = [
        asset
        for asset in existing_assets
        if asset.status != "Off-Network" and asset.otherTrackingNumber in inactive_assets
    ]

    logger.info(f"Deactivating {len(assets_to_deactivate)} Off-Network Assets")
    for asset in assets_to_deactivate:
        asset.status = mop_up_status
        asset.save()


def _is_failed_compliance_finding(finding: dict) -> bool:
    """
    Check if a finding represents a failed compliance check.

    :param dict finding: Compliance finding to evaluate
    :return: True if finding is failed and has required fields
    """
    return finding["ComplianceResult"] in ["FAILED", "FAIL"] and finding["800-53r5"] != ""


def _add_asset_to_identifier(asset_identifiers: Dict[str, List[str]], stig_key: str, hostname: str):
    """
    Add an asset hostname to the identifier map for a STIG check.

    :param Dict[str, List[str]] asset_identifiers: Map of STIG checks to hostnames
    :param str stig_key: STIG check identifier
    :param str hostname: Asset hostname to add
    """
    if stig_key in asset_identifiers:
        if hostname not in asset_identifiers[stig_key]:
            asset_identifiers[stig_key].append(hostname)
    else:
        asset_identifiers[stig_key] = [hostname]


def consolidate_compliance_findings(axonius_object: pd.DataFrame, fisma: str):
    """
    Filter and Consolidate Compliance Findings by Asset

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for

    :return: Filtered Findings Dataset for FISMA ID, consolidated asset_identifiers map for STIG Check
    """
    axonius_object_fisma = pd.DataFrame()
    for ind, asset in axonius_object.iterrows():
        if get_nested_value(asset, PATH_TO_FISMA_COMPLIANCE) == fisma:
            axonius_object_fisma = pd.concat([axonius_object_fisma, pd.DataFrame([asset])], ignore_index=True)

    asset_identifiers: Dict[str, List[str]] = {}
    for ind, asset in axonius_object_fisma.iterrows():
        for finding in asset.COMPLIANCE_TABLE:
            if not _is_failed_compliance_finding(finding):
                continue

            key_temp = finding["STIG"]
            if key_temp == "":
                continue

            _add_asset_to_identifier(asset_identifiers, key_temp, asset["hostname"])

    return axonius_object_fisma, asset_identifiers


def _is_valid_compliance_finding(finding: dict) -> bool:
    """
    Validate if a compliance finding should be processed for ingestion.

    :param dict finding: Finding data from Axonius
    :return: True if finding should be processed, False otherwise
    :rtype: bool
    """
    if finding["ComplianceResult"] not in ["FAILED", "FAIL"]:
        return False
    if finding["800-53r5"] == "":
        return False
    if finding["STIG"] == "":
        return False
    return True


def _calculate_compliance_due_date(finding: dict, finding_severity_map: dict):
    """
    Calculate due date and severity for a compliance finding.

    :param dict finding: Finding data from Axonius
    :param dict finding_severity_map: Map of finding severities
    :return: Tuple of (severity, created_date, due_date) or None if calculation fails
    :rtype: tuple or None
    """
    from regscale.models.regscale_models import IssueSeverity

    severity = finding_severity_map.get(finding["CAT"], IssueSeverity.NotAssigned)
    created_date = date_str(finding["FIRST-SEEN"])
    title = "Axonius"
    try:
        due_date = issue_due_date(severity, created_date, title=title)
        return severity, created_date, due_date
    except (ValueError, TypeError) as e:
        logger.warning("Unable to calculate due date for finding: %s", e)
        return None


def _create_compliance_finding_dict(
    finding: dict,
    asset_identifiers: dict,
    finding_control: str,
    severity: str,
    created_date: str,
    due_date: str,
    owner_id: str,
    ssp_id: int,
) -> dict:
    """
    Create a compliance finding dictionary for RegScale API ingestion.

    :param dict finding: Finding data from Axonius
    :param dict asset_identifiers: Dictionary of Asset Identifiers for each STIG Check
    :param str finding_control: Normalized control identifier
    :param str severity: Finding severity level
    :param str created_date: Date when finding was first detected
    :param str due_date: Due date for remediation
    :param str owner_id: Owner ID of desired Asset Owner
    :param int ssp_id: Parent SSP ID
    :return: Finding dictionary ready for API submission
    :rtype: dict
    """
    return {
        "title": f"Assessment Failure for Security Check: {finding['STIG']}",
        "assetIdentifier": "|".join(asset_identifiers[finding["STIG"]]),
        "severityLevel": severity,
        "identification": "Security Control Assessment",
        "sourceReport": "Axonius_Posture",
        "source": "Axonius_Posture",
        "status": "Open",
        "description": finding.get("COMPLIANCE-INFO", ""),
        "pluginId": finding["STIG"],
        "issueOwnerId": owner_id,
        "category": "Other",
        "securityChecks": finding["CHECK"],
        "affectedControls": finding_control,
        "dateFirstDetected": datetime_str(finding.get("created_date", "")),
        "recommendedActions": finding.get("COMPLIANCE-SOLUTION", ""),
        "dueDate": due_date,
        "parentId": ssp_id,
        "parentModule": "securityplans",
    }


def add_findings_for_ingestion(
    axonius_object: pd.DataFrame,
    asset_identifiers: dict[str, list],
    finding_severity_map: dict,
    fisma: str,
    owner_id: str,
    ssp_id: int,
):
    """
    Compile List of Findings to be ingested from Axonius Dataset

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for
    :param int ssp_id: Parent SSP ID
    :param str owner_id: Owner ID of desired Asset Owner
    :param dict asset_identifiers: Dictionary of Asset Identifiers for each STIG Check
    :param dict finding_severity_map: Map of finding severities

    :return: List of Compliance Findings objects to feed to API
    """
    from regscale.models.integration_models.axonius_models.connectors.assets import normalize_control

    findings = []
    checks_completed = set()

    logger.info("Fetching Findings for %s", fisma)
    logger.info("Consolidating Compliance Findings")

    for ind, asset in axonius_object.iterrows():
        for finding in asset.COMPLIANCE_TABLE:
            if not _is_valid_compliance_finding(finding):
                continue

            if finding["STIG"] in checks_completed:
                continue

            due_date_result = _calculate_compliance_due_date(finding, finding_severity_map)
            if due_date_result is None:
                continue

            severity, created_date, due_date = due_date_result
            finding_control = normalize_control(finding["800-53r5"])

            finding_dict = _create_compliance_finding_dict(
                finding=finding,
                asset_identifiers=asset_identifiers,
                finding_control=finding_control,
                severity=severity,
                created_date=created_date,
                due_date=due_date,
                owner_id=owner_id,
                ssp_id=ssp_id,
            )

            findings.append(finding_dict)
            checks_completed.add(finding["STIG"])

    return findings


def _is_valid_finding(finding: dict) -> bool:
    """
    Check if a finding is valid for processing.

    :param dict finding: The vulnerability finding to validate
    :return: True if finding is valid, False otherwise
    """
    return (
        finding["remediated"] in ["Open", "Reopened"]
        and finding["cve_severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        and finding["cve_id"] != ""
    )


def _add_asset_to_identifiers(asset_identifiers: Dict[str, List[str]], cve_id: str, dnsname: str) -> None:
    """
    Add asset dnsname to the asset_identifiers dictionary for a given CVE.

    :param dict asset_identifiers: Dictionary mapping CVE IDs to asset dnsnames
    :param str cve_id: The CVE ID key
    :param str dnsname: The asset dnsname to add
    """
    if cve_id in asset_identifiers:
        if dnsname not in asset_identifiers[cve_id]:
            asset_identifiers[cve_id].append(dnsname)
    else:
        asset_identifiers[cve_id] = [dnsname]


def consolidate_vulns(axonius_object: pd.DataFrame, fisma: str):
    """
    Filter and Consolidate Vulnerabilities by Asset

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for

    :return: Filtered Vulnerabilities Dataset for FISMA ID, consolidated asset_identifiers map for CVE
    """
    axonius_object_fisma_vuln = pd.DataFrame()
    for ind, asset in axonius_object.iterrows():
        try:
            if get_nested_value(asset, PATH_TO_FISMA_VULNS) == fisma:
                axonius_object_fisma_vuln = pd.concat(
                    [axonius_object_fisma_vuln, pd.DataFrame([asset])], ignore_index=True
                )
        except (KeyError, TypeError) as e:
            logger.debug(f"Unable to process vulnerability finding: {e}")
            continue

    logger.info("Vulns Filtered")
    asset_identifiers: Dict[str, List[str]] = {}
    for ind, asset in axonius_object_fisma_vuln.iterrows():
        if pd.isna(asset["dnsname"]):
            continue

        for finding in asset["specific_data.data.cdm_vulnerability_findings"]:
            try:
                if not _is_valid_finding(finding):
                    continue

                _add_asset_to_identifiers(asset_identifiers, finding["cve_id"], asset["dnsname"])
            except (KeyError, TypeError) as e:
                logger.debug(f"Unable to process vulnerability finding for asset identifier: {e}")
                continue

    return axonius_object_fisma_vuln, asset_identifiers


def _is_valid_vulnerability(finding: dict, checks_completed: set) -> bool:
    """
    Validate if a vulnerability finding should be processed.

    :param dict finding: Vulnerability finding data
    :param set checks_completed: Set of already processed CVE IDs
    :return: True if finding is valid for processing, False otherwise
    :rtype: bool
    """
    if finding["cve_id"] in checks_completed:
        return False
    if finding["remediated"] not in ["Open", "Reopened"]:
        return False
    if finding["cve_severity"] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        return False
    return True


def _create_vulnerability_dict(finding: dict, asset_identifiers: dict, vuln_severity_map: dict, ssp_id: int) -> dict:
    """
    Create vulnerability dictionary for API ingestion.

    :param dict finding: Vulnerability finding data
    :param dict asset_identifiers: Dictionary mapping CVE IDs to asset identifiers
    :param dict vuln_severity_map: Map of severity levels
    :param int ssp_id: Parent SSP ID
    :return: Vulnerability dictionary ready for API ingestion
    :rtype: dict
    """
    from regscale.models.regscale_models import IssueSeverity

    return {
        "title": finding["cve_id"],
        "assetIdentifier": asset_identifiers[finding["cve_id"]],
        "severity": vuln_severity_map.get(finding["cve_severity"].lower(), IssueSeverity.NotAssigned),
        "source": "Axonius_Vulnerability",
        "status": "Open",
        "description": finding.get("software_name", ""),
        "plugInName": finding["cve_id"],
        "cvsSv3BaseScore": finding.get("cvss_base_score", 10),
        "cve": finding["cve_id"],
        "affectedControls": "si-02",
        "firstSeen": datetime_str(finding.get("first_seen", "")),
        "parentId": ssp_id,
        "parentModule": "securityplans",
    }


def add_vulns_for_ingestion(
    axonius_object: list[dict], asset_identifiers: set, vuln_severity_map: dict, fisma: str, ssp_id: int
):
    """
    Compile List of Vulnerabilities to be ingested from Axonius Dataset

    :param pd.DataFrame axonius_object: Input Axonius Dataset
    :param str fisma: FISMA ID to gather assets for
    :param int ssp_id: Parent SSP ID
    :param dict asset_identifiers: Dictionary of Asset Identifiers for each CVE
    :param dict vuln_severity_map: Map of finding severities

    :return: List of Vulnerabilities objects to feed to API
    """
    vulns = []
    logger.info("Fetching Vulns for %s", fisma)
    checks_completed = set()

    for ind, asset in axonius_object.iterrows():
        for finding in asset["specific_data.data.cdm_vulnerability_findings"]:
            try:
                if not _is_valid_vulnerability(finding, checks_completed):
                    continue

                vuln_dict = _create_vulnerability_dict(finding, asset_identifiers, vuln_severity_map, ssp_id)
                vulns.append(vuln_dict)
                checks_completed.add(finding["cve_id"])

            except (KeyError, TypeError) as e:
                logger.debug("Unable to process vulnerability finding: %s", e)
                continue

    return vulns
