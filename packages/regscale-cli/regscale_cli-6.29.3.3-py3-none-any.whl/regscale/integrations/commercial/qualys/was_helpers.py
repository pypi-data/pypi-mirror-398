"""
WAS (Web Application Scanning) helper functions for Qualys integration.

This module contains helper functions for processing WAS vulnerability data
and converting it to RegScale format.
"""

import logging
import traceback
from typing import Optional, Union

from dateutil.parser import ParserError, parse
from datetime import datetime, timezone
from urllib.parse import urlparse

from regscale.integrations.variables import ScannerVariables

logger = logging.getLogger("regscale")

# Import datetime format constant from parent module
QUALYS_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def fetch_was_vulnerabilities() -> list:
    """
    Fetch WAS (Web Application Scanning) vulnerabilities from Qualys WAS API.

    :return: List of web applications with vulnerabilities
    """
    try:
        from regscale.integrations.commercial.qualys.was import fetch_all_was_vulnerabilities

        was_vulnerabilities = fetch_all_was_vulnerabilities()
        logger.info("Received %s web applications with vulnerabilities from Qualys WAS", len(was_vulnerabilities))
        return was_vulnerabilities
    except Exception as e:
        logger.error("Failed to fetch WAS data: %s", e)
        logger.debug(traceback.format_exc())
        return []


def extract_was_assets(was_vulnerabilities: list) -> list[dict]:
    """
    Extract unique web applications from vulnerability data and convert to asset format.

    WAS structure from API:
    {
        "webappId": "uuid",
        "name": "Web Application 1",
        "url": "https://app.example.com",
        "lastScanned": "2025-11-10T...",
        "vulnerabilities": [...]
    }

    Convert to VMDR asset format:
    {
        "ASSET_ID": "webappId",
        "IP": "WebApp",
        "DNS": "app.example.com",  # Extracted from URL
        "OS": "Web Application",
        "TRACKING_METHOD": "WAS",
        "URL": "https://app.example.com"
    }

    :param was_vulnerabilities: List of web application vulnerability dictionaries from Qualys WAS API
    :return: List of asset dictionaries in VMDR format
    :rtype: list[dict]
    """
    was_assets = []
    seen_webapp_ids = set()

    logger.info("extract_was_assets: Processing %s webapps", len(was_vulnerabilities))
    for i, webapp_data in enumerate(was_vulnerabilities, 1):
        webapp_id = webapp_data.get("webappId", "")
        if not webapp_id:
            logger.warning("Skipping webapp %s/%s with missing webappId", i, len(was_vulnerabilities))
            continue
        if webapp_id in seen_webapp_ids:
            logger.warning("Duplicate webappId '%s' encountered, skipping (keeping first occurrence)", webapp_id)
            continue

        seen_webapp_ids.add(webapp_id)
        logger.debug("extract_was_assets: Processing webapp %s/%s (ID: %s)", i, len(was_vulnerabilities), webapp_id)

        webapp_name = webapp_data.get("name", "Unknown Web Application")
        webapp_url = webapp_data.get("url", "")
        last_scanned = webapp_data.get("lastScanned", "")

        # Extract domain from URL for DNS field
        try:
            parsed_url = urlparse(webapp_url)
            dns = parsed_url.netloc or webapp_url
        except Exception:
            dns = webapp_url

        asset = {
            "ASSET_ID": webapp_id,
            "IP": "WebApp",  # Placeholder - web apps don't have traditional IPs
            "DNS": dns,
            "OS": "Web Application",
            "TRACKING_METHOD": "WAS",
            "ID": webapp_id,
            "URL": webapp_url,
            "LAST_SCAN_DATETIME": last_scanned,
            "NAME": webapp_name,
            "DETECTION_LIST": {"DETECTION": []},
        }

        was_assets.append(asset)

    logger.info("Extracted %s unique WAS assets from vulnerability data", len(was_assets))
    return was_assets


def map_was_severity(severity_text: str) -> int:
    """
    Map WAS text severity to RegScale numeric severity (1-5).

    WAS uses: CRITICAL, HIGH, MEDIUM, LOW, INFO
    RegScale uses: 1 (Low) to 5 (Critical)

    :param severity_text: Text severity from WAS API
    :return: Numeric severity value (1-5)
    :rtype: int
    """
    severity_map = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1, "INFORMATIONAL": 1}

    if isinstance(severity_text, str):
        return severity_map.get(severity_text.upper(), 3)
    if isinstance(severity_text, int):
        # Already numeric, but warn since WAS should return strings
        logger.warning("WAS severity is already numeric (%s), expected string. Using as-is.", severity_text)
        return severity_text
    # Unexpected type
    logger.warning(
        "WAS severity has unexpected type %s (value: %s). Defaulting to MEDIUM (3).",
        type(severity_text).__name__,
        severity_text,
    )
    return 3  # Default to MEDIUM


def construct_was_plugin_id(vuln: dict, webapp_id: str, qid: str) -> tuple[str, str]:
    """
    Construct Qualys ID and Plugin ID for WAS vulnerabilities with mode-aware deduplication.

    Deduplication behavior depends on ScannerVariables.issueCreation mode:
    - Consolidated mode: Group by CVE/QID across all webapps (deduplicate CVEs)
    - Per-Asset mode: Create unique issue per webapp-vulnerability pair (no CVE deduplication)

    :param vuln: Vulnerability dictionary from Qualys WAS API
    :param webapp_id: Web application ID for deduplication
    :param qid: Qualys QID (vulnerability ID) as string
    :return: Tuple of (qualys_id, plugin_id) for issue tracking
    :rtype: tuple[str, str]
    """
    cve_ids = vuln.get("cveids", [])
    cve = cve_ids[0] if cve_ids else ""
    qid_str = qid  # Already a string

    # Mode-aware deduplication
    if ScannerVariables.issueCreation == "Consolidated":
        # Consolidated: Deduplicate by CVE/QID across all webapps
        if cve:
            qualys_id = cve.replace("-", "_")
            plugin_id = f"Qualys_WAS_{cve.replace('-', '_')}"
        else:
            qualys_id = f"QID_{qid_str}"
            plugin_id = f"Qualys_WAS_{qid_str}"
    else:
        # Per-Asset: Include webapp identifier
        webapp_short = webapp_id[:12] if len(webapp_id) > 12 else webapp_id
        webapp_safe = webapp_short.replace("-", "_")

        if cve:
            qualys_id = f"{cve.replace('-', '_')}_{webapp_safe}"
            plugin_id = f"Qualys_WAS_{cve.replace('-', '_')}_{webapp_safe}"
        else:
            qualys_id = f"QID_{qid_str}_{webapp_safe}"
            plugin_id = f"Qualys_WAS_{qid_str}_{webapp_safe}"

    return qualys_id, plugin_id


def build_was_diagnosis(vuln: dict) -> str:
    """
    Build diagnosis string from WAS vulnerability data.

    :param vuln: Vulnerability dictionary from Qualys WAS API
    :return: Diagnosis string with URL, parameters, and description
    """
    diagnosis_parts = []

    # Extract values once to avoid redundant lookups
    url = vuln.get("url")
    param = vuln.get("param")
    method = vuln.get("method")
    description = vuln.get("description")

    if url:
        diagnosis_parts.append(f"Found in URL: {url}")
    if param:
        diagnosis_parts.append(f"Affected parameter: {param}")
    if method:
        diagnosis_parts.append(f"HTTP Method: {method}")
    if description:
        diagnosis_parts.append(description)

    return ". ".join(diagnosis_parts) if diagnosis_parts else "No details available"


def build_was_consequence(vuln: dict) -> str:
    """
    Build consequence string from WAS vulnerability data with OWASP category.

    :param vuln: Vulnerability dictionary from Qualys WAS API
    :return: Consequence string with OWASP and impact information
    """
    consequence_parts = []

    # Extract values once to avoid redundant lookups
    owasp = vuln.get("owasp")
    impact = vuln.get("impact")
    consequence = vuln.get("consequence")

    if owasp:
        consequence_parts.append(f"OWASP: {owasp}")
    if impact:
        consequence_parts.append(impact)
    elif consequence:
        consequence_parts.append(consequence)

    return ". ".join(consequence_parts) if consequence_parts else "Web application vulnerability"


def format_was_datetime(discovered: str) -> str:
    """
    Format WAS datetime string to standard format without milliseconds using dateutil.

    :param discovered: Datetime string from WAS API (may include milliseconds)
    :return: Formatted datetime string in YYYY-MM-DDTHH:MM:SSZ format
    """
    if discovered:
        try:
            # Use dateutil to parse the datetime string (handles various formats)
            dt = parse(discovered)
            # Convert to UTC if timezone-aware, otherwise assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            # Format without microseconds
            return dt.strftime(QUALYS_DATETIME_FORMAT)
        except ParserError as e:
            logger.warning("Failed to parse WAS datetime '%s': %s. Using current time.", discovered, e)
            # Fall through to default

    # Default to current time if no discovered date or parsing failed
    return datetime.now(timezone.utc).strftime(QUALYS_DATETIME_FORMAT)


def process_was_vulnerability(vuln: dict, webapp_id: str) -> dict | None:
    """
    Process a single WAS vulnerability and convert to RegScale issue format.

    :param vuln: Vulnerability dictionary from Qualys WAS API
    :param webapp_id: Web application ID for deduplication
    :return: Issue entry dictionary or None if invalid
    """
    qid = str(vuln.get("qid", ""))
    if not qid:
        return None

    # Map severity
    severity = map_was_severity(vuln.get("severity", "MEDIUM"))

    # Extract CVE
    cve_ids = vuln.get("cveids", [])
    cve = cve_ids[0] if cve_ids else ""

    # Construct deduplication key
    qualys_id, plugin_id = construct_was_plugin_id(vuln, webapp_id, qid)
    logger.debug(
        "WAS Vuln: webapp=%s, qid=%s, cve=%s -> qualys_id=%s, plugin_id=%s",
        webapp_id[:12],
        qid,
        cve_ids[0] if cve_ids else "None",
        qualys_id,
        plugin_id,
    )

    # Build title
    title = vuln.get("title", "Unknown WAS Vulnerability")
    if cve and cve not in title:
        title = f"{title} ({cve})"

    # Build diagnosis and consequence using helper functions
    diagnosis = build_was_diagnosis(vuln)
    consequence = build_was_consequence(vuln)

    # Format datetime
    discovered = format_was_datetime(vuln.get("discovered", ""))

    return {
        "QID": qid,
        "QUALYS_ID": qualys_id,
        "PLUGIN_ID": plugin_id,
        "SEVERITY": severity,
        "TYPE": "Confirmed",  # WAS findings are confirmed
        "FIRST_FOUND_DATETIME": discovered,
        "LAST_FOUND_DATETIME": discovered,
        "ISSUE_DATA": {
            "TITLE": title,
            "CONSEQUENCE": consequence,
            "DIAGNOSIS": diagnosis,
            "SOLUTION": vuln.get("solution", "Refer to security best practices"),
            "CVE": cve,
            "CVSS_SCORE": vuln.get("cvssScore", 0.0),
            "OWASP": vuln.get("owasp", ""),
            "CATEGORY": vuln.get("category", ""),
        },
    }


def convert_was_vulns_to_issues(was_vulnerabilities: list) -> list[dict]:
    """
    Convert WAS vulnerability data to RegScale Issue format matching qualys_assets_and_issues structure.

    Input structure:
    [{
        "webappId": "uuid",
        "name": "Web App 1",
        "url": "https://app.example.com",
        "vulnerabilities": [{
            "qid": 45839,
            "title": "SQL Injection",
            "severity": "CRITICAL",
            "url": "/api/users",
            "param": "id",
            "cveids": ["CVE-2021-1234"],
            "cvssScore": 9.1,
            "owasp": "A03:2021",
            "description": "...",
            "solution": "..."
        }]
    }]

    Output structure (matching qualys_assets_and_issues):
    [{
        "ASSET_ID": "webapp-uuid",
        "DNS": "app.example.com",
        "IP": "WebApp",
        "OS": "Web Application",
        "ISSUES": {
            "CVE_2021_1234": {
                "QID": "45839",
                "SEVERITY": 5,
                "ISSUE_DATA": {
                    "TITLE": "SQL Injection (CVE-2021-1234)",
                    "CONSEQUENCE": "OWASP A03:2021",
                    "DIAGNOSIS": "Found in: /api/users?id=...",
                    "SOLUTION": "..."
                }
            }
        }
    }]

    :param was_vulnerabilities: List of web application vulnerability dictionaries from Qualys WAS API
    :return: List of dictionaries with asset_data and ISSUES matching qualys_assets_and_issues format
    :rtype: list[dict]
    """
    was_issues = []

    logger.info("convert_was_vulns_to_issues: Received %s webapps", len(was_vulnerabilities))
    for i, webapp_data in enumerate(was_vulnerabilities):
        webapp_id = webapp_data.get("webappId", "")
        vulnerabilities_count = len(webapp_data.get("vulnerabilities", []))
        logger.info(
            "Processing webapp %s/%s: webappId=%s, has %s vulns",
            i + 1,
            len(was_vulnerabilities),
            webapp_id,
            vulnerabilities_count,
        )
        if not webapp_id:
            logger.warning("Skipping webapp %s/%s: No webappId", i + 1, len(was_vulnerabilities))
            continue

        webapp_url = webapp_data.get("url", "")

        # Extract domain for DNS
        try:
            parsed = urlparse(webapp_url)
            dns = parsed.netloc or webapp_url
        except Exception:
            dns = webapp_url

        asset_data = {
            "ASSET_ID": webapp_id,
            "DNS": dns,
            "IP": "WebApp",
            "OS": "Web Application",
            "TRACKING_METHOD": "WAS",
            "URL": webapp_url,
        }

        # Process all vulnerabilities for this webapp
        issues = {}
        vulnerabilities = webapp_data.get("vulnerabilities", [])
        for vuln in vulnerabilities:
            issue_entry = process_was_vulnerability(vuln, webapp_id)
            if issue_entry:
                qualys_id = issue_entry["QUALYS_ID"]
                issues[qualys_id] = issue_entry

        if issues:
            was_issue_entry = {**asset_data, "ISSUES": issues}
            was_issues.append(was_issue_entry)

    logger.info(
        "Converted %s webapps with vulnerabilities to issue format (%s total issues)",
        len(was_issues),
        sum(len(w["ISSUES"]) for w in was_issues),
    )
    return was_issues
