"""
Web Application Scanning (WAS) operations module for Qualys WAS API integration.
"""

import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from json import JSONDecodeError
from typing import Dict, List, Optional
from urllib.parse import urljoin

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

# Create logger for this module
logger = logging.getLogger("regscale")


def auth_was_api() -> tuple[str, dict]:
    """
    Authenticate WAS API using HTTP Basic Auth (same credentials as VMDR)

    :return: A tuple of the base URL and a dictionary of headers
    :rtype: tuple[str, dict]
    """
    from . import QUALYS_API, _get_config  # noqa: C0415

    config = _get_config()
    # Use qualysMockUrl if available (for testing), otherwise use qualysUrl
    qualys_url = config.get("qualysMockUrl") or config.get("qualysUrl")
    user = config.get("qualysUserName")
    password = config.get("qualysPassword")

    logger.debug("WAS Auth - Configuring authentication for %s", qualys_url)

    # NO URL transformation needed - WAS uses standard qualysguard URL
    headers = {"X-Requested-With": "RegScale CLI"}

    # HTTP Basic Auth handled by QUALYS_API session
    QUALYS_API.auth = (user, password)

    logger.debug("WAS API authentication configured")
    return qualys_url, headers


def _make_was_api_request(current_url: str, headers: dict, params: Optional[Dict] = None) -> dict:
    """
    Make API request to WAS endpoints

    :param str current_url: The URL for the API request
    :param dict headers: Headers to include in the request
    :param Dict params: Optional query parameters for pagination
    :return: Response data containing WAS data
    :rtype: dict
    """
    from . import QUALYS_API  # noqa: C0415

    # Make API request
    response = QUALYS_API.get(url=current_url, headers=headers, params=params)

    # Validate response
    if not response.ok:
        logger.error("WAS API request failed: %s - %s", response.status_code, response.text)
        return {"data": []}

    try:
        return response.json()
    except JSONDecodeError as e:
        logger.error("Failed to parse WAS JSON response: %s", e)
        return {"data": []}


def fetch_all_webapps(filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
    """
    Fetch all web applications with pagination

    :param Optional[Dict] filters: Filters to apply to the web applications
    :param int limit: Number of web applications to fetch per page
    :return: A list of web applications
    :rtype: List[Dict]
    """
    base_url, headers = auth_was_api()
    current_url = urljoin(base_url, "/qps/rest/3.0/search/was/webapp")

    # WAS API pagination (similar to standard REST)
    params = {"pageSize": limit}
    if filters:
        params.update(filters)

    all_webapps = []
    page = 0

    # Create progress bar for pagination
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=None,
    )

    with progress:
        task = progress.add_task("[green]Fetching WAS web applications...", total=None)

        while True:
            params["pageNo"] = page
            response_data = _make_was_api_request(current_url, headers, params)

            webapps = response_data.get("data", [])
            all_webapps.extend(webapps)

            # Update progress description with current status
            progress.update(
                task,
                description=f"[green]Fetching WAS web applications... (Page {page + 1}, Total: {len(all_webapps)})",
            )

            logger.debug("Fetched page %s: %s webapps (Total so far: %s)", page + 1, len(webapps), len(all_webapps))

            # Check if more pages exist
            if response_data.get("hasMore", False):
                page += 1
            else:
                break

        progress.update(task, total=len(all_webapps), completed=len(all_webapps))

    logger.info("Fetched %s web applications from WAS", len(all_webapps))
    return all_webapps


def fetch_latest_scan_for_webapp(webapp_id: str) -> Optional[Dict]:
    """
    Fetch the most recent completed scan for a web application

    :param str webapp_id: The UUID of the web application
    :return: The most recent scan or None if not found
    :rtype: Optional[Dict]
    """
    base_url, headers = auth_was_api()
    current_url = urljoin(base_url, "/qps/rest/3.0/search/was/wasscan")

    params = {"webAppId": webapp_id, "status": "Completed", "sort": "endTime:desc", "pageSize": 1}

    response_data = _make_was_api_request(current_url, headers, params)
    scans = response_data.get("data", [])

    if scans:
        return scans[0]  # Most recent scan
    return None


def fetch_scan_vulnerabilities(scan_id: str) -> List[Dict]:
    """
    Fetch all vulnerabilities for a specific scan

    :param str scan_id: The UUID of the scan
    :return: A list of vulnerabilities
    :rtype: List[Dict]
    """
    base_url, headers = auth_was_api()
    current_url = urljoin(base_url, f"/qps/rest/3.0/get/was/wasscan/{scan_id}")

    response_data = _make_was_api_request(current_url, headers)
    # Mock API returns vulnerabilities in 'vulnerabilityDetails' key
    # Production API may use 'vulnerabilities' key - support both
    return response_data.get("vulnerabilityDetails", response_data.get("vulnerabilities", []))


def fetch_all_was_vulnerabilities(filters: Optional[Dict] = None, max_workers: int = 10) -> List[Dict]:
    """
    Fetch all web applications and their vulnerabilities with threading

    :param Optional[Dict] filters: Filters to apply to the web applications
    :param int max_workers: Maximum number of worker threads for concurrent vulnerability fetching
    :return: A list of web applications with vulnerabilities
    :rtype: List[Dict]
    """
    webapps = fetch_all_webapps(filters)

    if not webapps:
        logger.info("No web applications found to fetch vulnerabilities for")
        return []

    # Create progress bar for fetching vulnerabilities
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TimeElapsedColumn(),
        console=None,
    )

    def fetch_webapp_vulns_with_progress(webapp):
        """Helper function to fetch vulnerabilities for a single webapp with progress tracking."""
        # Extract values once to avoid redundant lookups
        webapp_id = webapp.get("webappId")
        webapp_name = webapp.get("name", "Unknown")

        # Get latest completed scan
        latest_scan = fetch_latest_scan_for_webapp(webapp_id)
        if not latest_scan:
            logger.info("WAS: No completed scans found for webapp: %s (ID: %s)", webapp_name, webapp_id)
            return webapp, []

        # Extract scan details
        scan_id = latest_scan.get("scanId")
        scan_status = latest_scan.get("status")
        webapp["scanId"] = scan_id
        webapp["scanStatus"] = scan_status
        logger.info("WAS: Found scan %s for webapp %s", scan_id, webapp_name)

        # Fetch vulnerabilities from scan
        try:
            vulns = fetch_scan_vulnerabilities(scan_id)
            logger.info("WAS: Fetched %s vulnerabilities for webapp: %s (scan: %s)", len(vulns), webapp_name, scan_id)
            return webapp, vulns
        except Exception as e:
            logger.error("Error fetching vulns for webapp %s: %s", webapp_name, e)
            logger.debug(traceback.format_exc())
            return webapp, []

    with progress:
        task = progress.add_task(
            f"[yellow]Fetching vulnerabilities for {len(webapps)} web applications...", total=len(webapps)
        )

        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_webapp = {}
            for webapp in webapps:
                future = executor.submit(fetch_webapp_vulns_with_progress, webapp)
                future_to_webapp[future] = webapp

            # Process completed tasks and update progress
            for future in as_completed(future_to_webapp):
                webapp, vulns = future.result()
                webapp["vulnerabilities"] = vulns
                progress.update(task, advance=1)

    logger.info("Completed fetching vulnerabilities for %s webapps using %s workers", len(webapps), max_workers)
    return webapps
