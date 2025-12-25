"""
Total Cloud helper functions for Qualys integration.

This module provides helper functions for fetching, validating, and processing
Total Cloud data from Qualys APIs, including VM detection data and container
security data.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from regscale.integrations.commercial.qualys.datetime_utils import parse_qualys_datetime
from regscale.integrations.commercial.qualys.qualys_error_handler import QualysErrorHandler
from regscale.integrations.variables import ScannerVariables

logger = logging.getLogger("regscale")

# Headers for Qualys API requests
HEADERS = {"Content-Type": "application/json", "X-Requested-With": "RegScale CLI"}

# Constants for asset source identification
SOURCE_TOTAL_CLOUD_VM = "Total Cloud VM"
SOURCE_TOTAL_CLOUD_CONTAINER = "Total Cloud Container"


def _get_qualys_api() -> Tuple[str, Any]:
    """
    Get the Qualys API client and base URL.

    :return: Tuple of (qualys_url, qualys_api_session)
    :rtype: Tuple[str, Any]
    """
    from regscale.integrations.commercial.qualys import _get_qualys_api as get_api

    return get_api()


def _get_config() -> Dict[str, Any]:
    """
    Get the Qualys configuration.

    :return: Configuration dictionary
    :rtype: Dict[str, Any]
    """
    from regscale.integrations.commercial.qualys import _get_config as get_config

    return get_config()


def _prepare_qualys_params(include_tags: Optional[str], exclude_tags: Optional[str]) -> Dict[str, str]:
    """
    Prepare parameters for Qualys API request.

    :param Optional[str] include_tags: Tags to include in the filter
    :param Optional[str] exclude_tags: Tags to exclude in the filter
    :return: Dictionary of parameters for the API request
    :rtype: Dict[str, str]
    """
    params = {
        "action": "list",
        "show_asset_id": "1",
        "show_tags": "1",
    }
    if exclude_tags or include_tags:
        params["use_tags"] = "1"
        params["tag_set_by"] = "name"
        if exclude_tags:
            params["tag_set_exclude"] = exclude_tags
        if include_tags:
            params["tag_set_include"] = include_tags

    return params


def fetch_total_cloud_data(
    tc_include_tags: Optional[str] = None, tc_exclude_tags: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch Total Cloud VM detection data from Qualys VMDR API.

    This function fetches host detection data from the Qualys VM Detection API,
    which provides comprehensive vulnerability data for VMs in the Total Cloud context.

    :param Optional[str] tc_include_tags: Tags to include for filtering (comma-separated)
    :param Optional[str] tc_exclude_tags: Tags to exclude from filtering (comma-separated)
    :return: Parsed XML data as dictionary, or None if request failed
    :rtype: Optional[Dict[str, Any]]
    """
    try:
        qualys_url, qualys_api = _get_qualys_api()
        params = _prepare_qualys_params(tc_include_tags, tc_exclude_tags)

        logger.info("Fetching Total Cloud VM detection data from Qualys...")

        response = qualys_api.get(
            url=urljoin(qualys_url, "/api/2.0/fo/asset/host/vm/detection/"),
            headers=HEADERS,
            params=params,
            verify=getattr(ScannerVariables, "sslVerify", True),
        )

        # Validate response
        is_valid, error_message, parsed_data = QualysErrorHandler.validate_response(response)

        if not is_valid:
            logger.error("Qualys Total Cloud API request failed: %s", error_message)
            if parsed_data:
                error_details = QualysErrorHandler.extract_error_details(parsed_data)
                QualysErrorHandler.log_error_details(error_details)
            return None

        logger.info("Total Cloud VM detection data fetched successfully")
        return parsed_data

    except Exception as e:
        logger.error("Error fetching Total Cloud data: %s", e)
        logger.debug(traceback.format_exc())
        return None


def fetch_total_cloud_containers(
    tc_include_tags: Optional[str] = None, tc_exclude_tags: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch Total Cloud container data from Qualys Container Security API.

    This function fetches all containers and their vulnerabilities from the
    Qualys Container Security API using the existing container module.

    :param Optional[str] tc_include_tags: Tags to include for filtering (comma-separated)
    :param Optional[str] tc_exclude_tags: Tags to exclude from filtering (comma-separated)
    :return: List of container dictionaries with vulnerabilities
    :rtype: List[Dict[str, Any]]
    """
    from regscale.integrations.commercial.qualys.containers import fetch_all_vulnerabilities

    try:
        logger.info("Fetching Total Cloud container data from Qualys...")

        # Prepare filters for container API if tags provided
        filters = {}
        if tc_include_tags:
            filters["tagName"] = tc_include_tags
        if tc_exclude_tags:
            filters["excludeTagName"] = tc_exclude_tags

        # Fetch containers with vulnerabilities
        containers = fetch_all_vulnerabilities(filters=filters if filters else None)

        if containers:
            logger.info("Fetched %s containers from Total Cloud", len(containers))
        else:
            logger.warning("No containers found in Total Cloud")

        return containers or []

    except Exception as e:
        logger.error("Error fetching Total Cloud containers: %s", e)
        logger.debug(traceback.format_exc())
        return []


def validate_total_cloud_data(tc_xml_data: Optional[Dict[str, Any]], tc_containers: List[Dict[str, Any]]) -> bool:
    """
    Validate that Total Cloud data is usable for asset and vulnerability processing.

    Validation checks:
    1. XML data contains expected structure (HOST_LIST_VM_DETECTION_OUTPUT)
    2. At least one host or container is present

    :param Optional[Dict[str, Any]] tc_xml_data: Total Cloud XML data dictionary
    :param List[Dict[str, Any]] tc_containers: List of container data dictionaries
    :return: True if data is valid and usable, False otherwise
    :rtype: bool
    """
    # Check if we have any data at all
    if not tc_xml_data and not tc_containers:
        logger.warning("No Total Cloud data available (both VM and container data empty)")
        return False

    # Validate XML data structure if present
    if tc_xml_data:
        if not isinstance(tc_xml_data, dict):
            logger.warning("Total Cloud XML data is not a dictionary")
            return False

        # Check for Qualys errors
        error_details = QualysErrorHandler.extract_error_details(tc_xml_data)
        if error_details.get("has_error"):
            logger.error("Total Cloud XML data contains error response")
            QualysErrorHandler.log_error_details(error_details)
            return False

        # Check for expected structure
        if "HOST_LIST_VM_DETECTION_OUTPUT" not in tc_xml_data:
            logger.warning("Total Cloud XML data missing HOST_LIST_VM_DETECTION_OUTPUT")
            return False

        # Check if hosts exist
        hosts = _extract_hosts_from_xml_data(tc_xml_data)
        if hosts:
            logger.info("Total Cloud VM data validated: %s hosts found", len(hosts))
            return True

    # If we have containers, that's also valid
    if tc_containers:
        logger.info("Total Cloud container data validated: %s containers found", len(tc_containers))
        return True

    logger.warning("Total Cloud data validation failed: no valid hosts or containers found")
    return False


def _extract_hosts_from_xml_data(tc_xml_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract host data from Total Cloud XML data structure.

    :param Dict[str, Any] tc_xml_data: Total Cloud XML data dictionary
    :return: List of host dictionaries
    :rtype: List[Dict[str, Any]]
    """
    try:
        hosts = (
            tc_xml_data.get("HOST_LIST_VM_DETECTION_OUTPUT", {})
            .get("RESPONSE", {})
            .get("HOST_LIST", {})
            .get("HOST", [])
        )

        # Normalize to list
        if isinstance(hosts, dict):
            return [hosts]
        if isinstance(hosts, list):
            return hosts
        return []
    except (AttributeError, TypeError):
        return []


def extract_total_cloud_assets(
    tc_xml_data: Optional[Dict[str, Any]], tc_containers: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract assets from Total Cloud VM and container data.

    This function combines VM hosts from XML data and containers into a unified
    asset list suitable for RegScale asset creation.

    :param Optional[Dict[str, Any]] tc_xml_data: Total Cloud XML data dictionary
    :param List[Dict[str, Any]] tc_containers: List of container data dictionaries
    :return: List of asset dictionaries
    :rtype: List[Dict[str, Any]]
    """
    assets = []

    # Extract VM assets from XML data
    if tc_xml_data:
        vm_assets = _extract_vm_assets_from_tc(tc_xml_data)
        logger.info("Extracted %s VM assets from Total Cloud", len(vm_assets))
        assets.extend(vm_assets)

    # Extract container assets
    if tc_containers:
        container_assets = _extract_container_assets_from_tc(tc_containers)
        logger.info("Extracted %s container assets from Total Cloud", len(container_assets))
        assets.extend(container_assets)

    return assets


def _extract_vm_assets_from_tc(tc_xml_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract VM asset data from Total Cloud XML data.

    :param Dict[str, Any] tc_xml_data: Total Cloud XML data dictionary
    :return: List of VM asset dictionaries
    :rtype: List[Dict[str, Any]]
    """
    assets = []
    hosts = _extract_hosts_from_xml_data(tc_xml_data)

    for host in hosts:
        try:
            # Extract host information
            host_id = host.get("ID", "")
            ip = host.get("IP", "")
            dns = host.get("DNS", "")
            os_info = host.get("OS", "")
            last_scan = host.get("LAST_SCAN_DATETIME", "")
            network_id = host.get("NETWORK_ID", "")

            # Get FQDN from DNS_DATA if available
            dns_data = host.get("DNS_DATA", {})
            fqdn = dns_data.get("FQDN", "") if isinstance(dns_data, dict) else ""

            # Determine asset name
            name = dns or ip or f"QualysAsset-{host_id}"

            # Create asset dictionary matching expected format
            asset = {
                "ID": host_id,
                "IP": ip,
                "DNS": dns,
                "OS": os_info,
                "LAST_SCAN_DATETIME": parse_qualys_datetime(last_scan) if last_scan else "",
                "NETWORK_ID": network_id,
                "FQDN": fqdn,
                "name": name,
                "asset_type": "Server",
                "source": SOURCE_TOTAL_CLOUD_VM,
                # Include original detection data for vulnerability processing
                "DETECTION_LIST": host.get("DETECTION_LIST", {}),
            }
            assets.append(asset)

        except Exception as e:
            logger.error("Error extracting VM asset: %s", e)
            logger.debug(traceback.format_exc())
            continue

    return assets


def _extract_container_assets_from_tc(tc_containers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract container assets from Total Cloud container data.

    :param List[Dict[str, Any]] tc_containers: List of container data dictionaries
    :return: List of container asset dictionaries
    :rtype: List[Dict[str, Any]]
    """
    assets = []

    for container in tc_containers:
        try:
            # Extract container information
            container_id = container.get("containerId", "")
            name = container.get("name", f"Container-{container_id[:12] if container_id else 'unknown'}")
            image_id = container.get("imageId", "")
            state = container.get("state", "unknown")
            sha = container.get("sha", "")
            state_changed = container.get("stateChanged", "")

            # Create asset dictionary matching expected format
            asset = {
                "ID": container_id,
                "IP": "",
                "DNS": "",
                "OS": "Container",
                "LAST_SCAN_DATETIME": parse_qualys_datetime(str(state_changed)) if state_changed else "",
                "NETWORK_ID": "",
                "FQDN": "",
                "name": name,
                "asset_type": "Container",
                "source": SOURCE_TOTAL_CLOUD_CONTAINER,
                "container_state": state,
                "image_id": image_id,
                "sha": sha,
                # Include vulnerabilities for issue creation
                "vulnerabilities": container.get("vulnerabilities", []),
            }
            assets.append(asset)

        except Exception as e:
            logger.error("Error extracting container asset: %s", e)
            logger.debug(traceback.format_exc())
            continue

    return assets


def deduplicate_service_data(
    qualys_assets: List[Dict[str, Any]],
    was_assets: Optional[List[Dict[str, Any]]] = None,
    additional_assets: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Deduplicate assets from multiple sources (VMDR, Total Cloud, WAS, containers).

    Assets are deduplicated by their ID field. When duplicates are found,
    the first occurrence is kept.

    :param List[Dict[str, Any]] qualys_assets: Primary list of Qualys assets
    :param Optional[List[Dict[str, Any]]] was_assets: Optional WAS assets to include
    :param Optional[List[Dict[str, Any]]] additional_assets: Optional additional assets
    :return: Deduplicated list of assets
    :rtype: List[Dict[str, Any]]
    """
    seen_ids = set()
    deduplicated = []

    # Combine all asset lists
    all_assets = list(qualys_assets)
    if was_assets:
        all_assets.extend(was_assets)
    if additional_assets:
        all_assets.extend(additional_assets)

    for asset in all_assets:
        # Get asset identifier
        asset_id = asset.get("ID") or asset.get("id") or asset.get("containerId")

        if not asset_id:
            # Include assets without ID (shouldn't happen but handle gracefully)
            deduplicated.append(asset)
            continue

        if asset_id not in seen_ids:
            seen_ids.add(asset_id)
            deduplicated.append(asset)
        else:
            logger.debug("Skipping duplicate asset with ID: %s", asset_id)

    logger.info(
        "Deduplicated %s assets to %s unique assets",
        len(all_assets),
        len(deduplicated),
    )
    return deduplicated


def convert_total_cloud_to_issues(deduplicated_assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert Total Cloud detections from assets to issue format for RegScale.

    This function processes the detection data embedded in assets and converts
    them to a format suitable for creating RegScale issues.

    :param List[Dict[str, Any]] deduplicated_assets: List of deduplicated asset dictionaries
    :return: List of issue dictionaries
    :rtype: List[Dict[str, Any]]
    """
    issues = []

    for asset in deduplicated_assets:
        try:
            asset_id = asset.get("ID", "")
            asset_name = asset.get("name", asset_id)

            # Process VM detections
            if "DETECTION_LIST" in asset and asset.get("source") == SOURCE_TOTAL_CLOUD_VM:
                vm_issues = _convert_vm_detections_to_issues(asset, asset_id, asset_name)
                issues.extend(vm_issues)

            # Process container vulnerabilities
            if "vulnerabilities" in asset and asset.get("source") == SOURCE_TOTAL_CLOUD_CONTAINER:
                container_issues = _convert_container_vulns_to_issues(asset, asset_id, asset_name)
                issues.extend(container_issues)

        except Exception as e:
            logger.error("Error converting asset to issues: %s", e)
            logger.debug(traceback.format_exc())
            continue

    logger.info("Converted %s Total Cloud issues from %s assets", len(issues), len(deduplicated_assets))
    return issues


def _convert_vm_detections_to_issues(asset: Dict[str, Any], asset_id: str, asset_name: str) -> List[Dict[str, Any]]:
    """
    Convert VM detection data to issue format.

    :param Dict[str, Any] asset: Asset dictionary containing DETECTION_LIST
    :param str asset_id: Asset identifier
    :param str asset_name: Asset name
    :return: List of issue dictionaries
    :rtype: List[Dict[str, Any]]
    """
    issues = []
    detection_list = asset.get("DETECTION_LIST", {})
    detections = detection_list.get("DETECTION", [])

    # Normalize to list
    if isinstance(detections, dict):
        detections = [detections]

    for detection in detections:
        try:
            qid = detection.get("QID", "Unknown")
            severity = detection.get("SEVERITY", "0")
            status = detection.get("STATUS", "New")
            first_found = detection.get("FIRST_FOUND_DATETIME", "")
            last_found = detection.get("LAST_FOUND_DATETIME", "")
            results = detection.get("RESULTS", "")
            unique_id = detection.get("UNIQUE_VULN_ID", f"QID-{qid}-{asset_id}")

            # Extract CVE if available
            cve_id = _extract_cve_from_detection(detection)

            # Get issue details
            issue_data = detection.get("ISSUE_DATA", {})
            title = f"Qualys Vulnerability QID-{qid}"
            description = "No description available"
            solution = "No remediation information available"

            if isinstance(issue_data, dict):
                title = issue_data.get("TITLE", title)
                description = issue_data.get("DIAGNOSIS", description)
                solution = issue_data.get("SOLUTION", solution)

            # Create issue dictionary
            issue = {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "qid": qid,
                "title": title,
                "description": description,
                "severity": _map_severity(severity),
                "status": status,
                "first_found": parse_qualys_datetime(first_found) if first_found else "",
                "last_found": parse_qualys_datetime(last_found) if last_found else "",
                "results": results,
                "solution": solution,
                "unique_id": unique_id,
                "cve_id": cve_id,
                "source": SOURCE_TOTAL_CLOUD_VM,
            }
            issues.append(issue)

        except Exception as e:
            logger.error("Error converting VM detection to issue: %s", e)
            logger.debug(traceback.format_exc())
            continue

    return issues


def _convert_container_vulns_to_issues(asset: Dict[str, Any], asset_id: str, asset_name: str) -> List[Dict[str, Any]]:
    """
    Convert container vulnerability data to issue format.

    :param Dict[str, Any] asset: Asset dictionary containing vulnerabilities
    :param str asset_id: Asset identifier (container ID)
    :param str asset_name: Asset name
    :return: List of issue dictionaries
    :rtype: List[Dict[str, Any]]
    """
    issues = []
    vulnerabilities = asset.get("vulnerabilities", [])

    for vuln in vulnerabilities:
        try:
            vuln_id = vuln.get("id", "")
            qid = vuln.get("qid", "")
            title = vuln.get("title", f"Container Vulnerability {vuln_id}")
            severity = vuln.get("severity", 0)
            status = vuln.get("status", "New")
            first_found = vuln.get("firstFound", "")
            last_found = vuln.get("lastFound", "")
            result = vuln.get("result", "")

            # Extract CVE from cveids list
            cve_ids = vuln.get("cveids", [])
            cve_id = cve_ids[0] if cve_ids else ""

            # Create issue dictionary
            issue = {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "qid": qid,
                "title": title,
                "description": result or "No description available",
                "severity": _map_container_severity(severity),
                "status": status,
                "first_found": parse_qualys_datetime(str(first_found)) if first_found else "",
                "last_found": parse_qualys_datetime(str(last_found)) if last_found else "",
                "results": result,
                "solution": "No remediation information available",
                "unique_id": vuln_id or f"CONTAINER-{qid}-{asset_id}",
                "cve_id": cve_id,
                "source": SOURCE_TOTAL_CLOUD_CONTAINER,
            }
            issues.append(issue)

        except Exception as e:
            logger.error("Error converting container vulnerability to issue: %s", e)
            logger.debug(traceback.format_exc())
            continue

    return issues


def _extract_cve_from_detection(detection: Dict[str, Any]) -> str:
    """
    Extract CVE ID from a detection dictionary.

    :param Dict[str, Any] detection: Detection dictionary
    :return: CVE ID string or empty string
    :rtype: str
    """
    try:
        cve_list = detection.get("CVE_ID_LIST", {})
        if not cve_list or not isinstance(cve_list, dict):
            return ""

        cve_data = cve_list.get("CVE_ID", [])

        if isinstance(cve_data, list) and cve_data:
            return str(cve_data[0])
        if isinstance(cve_data, str):
            return cve_data

        return ""
    except Exception:
        return ""


def _map_severity(severity: str) -> str:
    """
    Map Qualys VM severity level to RegScale severity.

    Qualys VMDR uses 0-5 severity scale:
    0 = Not Assigned
    1 = Minimal
    2 = Low
    3 = Medium
    4 = High
    5 = Critical

    :param str severity: Qualys severity level (0-5)
    :return: RegScale severity string
    :rtype: str
    """
    severity_map = {
        "0": "Low",
        "1": "Low",
        "2": "Low",
        "3": "Moderate",
        "4": "High",
        "5": "Critical",
    }
    return severity_map.get(str(severity), "Low")


def _map_container_severity(severity: int) -> str:
    """
    Map Qualys Container Security severity level to RegScale severity.

    Qualys Container Security uses 1-5 severity scale (inverted):
    1 = Critical
    2 = High
    3 = Medium
    4 = Low
    5 = Minimal/Not Assigned

    :param int severity: Qualys container severity level (1-5)
    :return: RegScale severity string
    :rtype: str
    """
    severity_map = {
        1: "Critical",
        2: "High",
        3: "Moderate",
        4: "Low",
        5: "Low",
    }
    return severity_map.get(int(severity) if severity else 5, "Low")
