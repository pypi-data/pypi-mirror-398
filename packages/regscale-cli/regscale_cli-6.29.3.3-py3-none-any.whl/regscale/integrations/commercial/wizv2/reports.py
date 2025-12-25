#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiz Report Management for RegScale CLI."""

import logging
import time
from typing import Dict, Any, Optional

import requests

from regscale.integrations.commercial.wizv2.core.constants import (
    CREATE_REPORT_QUERY,
    REPORTS_QUERY,
    DOWNLOAD_QUERY,
    RERUN_REPORT_QUERY,
    get_compliance_report_variables,
    CHECK_INTERVAL_FOR_DOWNLOAD_REPORT,
    MAX_RETRIES,
)

logger = logging.getLogger("regscale")


class WizReportManager:
    """Manages Wiz report operations including creation, monitoring, and download."""

    def __init__(self, api_url: str, access_token: str):
        """
        Initialize the report manager.

        :param str api_url: The Wiz GraphQL API URL
        :param str access_token: The authentication token
        """
        self.api_url = api_url
        self.access_token = access_token
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}

    def create_compliance_report(self, project_id: str, run_starts_at: Optional[str] = None) -> Optional[str]:
        """
        Create a compliance report for the specified project.

        :param str project_id: The Wiz project ID
        :param Optional[str] run_starts_at: ISO timestamp for when the report should start
        :return: Report ID if successful, None otherwise
        :rtype: Optional[str]
        """
        variables = get_compliance_report_variables(project_id, run_starts_at)

        payload = {"query": CREATE_REPORT_QUERY, "variables": variables}

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            report_data = data.get("data", {}).get("createReport", {}).get("report", {})
            report_id = report_data.get("id")

            if report_id:
                logger.info(f"Successfully created compliance report with ID: {report_id}")
                return report_id
            else:
                logger.error("No report ID returned from create report mutation")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating compliance report: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing create report response: {e}")
            return None

    def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """
        Get the status and details of a report.

        :param str report_id: The report ID
        :return: Report status information
        :rtype: Dict[str, Any]
        """
        variables = {"reportId": report_id}

        payload = {"query": DOWNLOAD_QUERY, "variables": variables}

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return {}

            report_data = data.get("data", {}).get("report", {})
            last_run = report_data.get("lastRun", {})

            return {
                "status": last_run.get("status", "UNKNOWN"),
                "url": last_run.get("url", ""),
                "report_data": report_data,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting report status: {e}")
            return {}
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing report status response: {e}")
            return {}

    def wait_for_report_completion(self, report_id: str) -> Optional[str]:
        """
        Wait for a report to complete and return the download URL.

        :param str report_id: The report ID
        :return: Download URL if successful, None otherwise
        :rtype: Optional[str]
        """
        logger.info(f"Waiting for report {report_id} to complete...")

        for attempt in range(MAX_RETRIES):
            status_info = self.get_report_status(report_id)
            status = status_info.get("status", "UNKNOWN")

            logger.info(f"Report status (attempt {attempt + 1}/{MAX_RETRIES}): {status}")

            if status in ["SUCCESS", "COMPLETED"]:
                download_url = status_info.get("url", "")
                if download_url:
                    logger.info(f"Report completed successfully. Download URL: {download_url}")
                    return download_url
                else:
                    logger.warning("Report completed but no download URL available")
                    return None

            elif status in ["FAILED", "CANCELLED", "TIMEOUT"]:
                logger.error(f"Report failed with status: {status}")
                return None

            elif status in ["PENDING", "RUNNING", "IN_PROGRESS", "UNKNOWN"]:
                logger.info(
                    f"Report is still {status.lower()}, waiting {CHECK_INTERVAL_FOR_DOWNLOAD_REPORT} seconds..."
                )
                time.sleep(CHECK_INTERVAL_FOR_DOWNLOAD_REPORT)
            else:
                logger.warning(f"Unknown report status: {status}")
                time.sleep(CHECK_INTERVAL_FOR_DOWNLOAD_REPORT)

        logger.error(f"Report did not complete after {MAX_RETRIES} attempts")
        return None

    def download_report(self, download_url: str, output_path: str) -> bool:
        """
        Download a report from the given URL.

        :param str download_url: The download URL
        :param str output_path: Path where the report should be saved
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            logger.info(f"Downloading report to: {output_path}")

            response = requests.get(download_url, timeout=300)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Report downloaded successfully to: {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading report: {e}")
            return False
        except IOError as e:
            logger.error(f"Error saving report to file: {e}")
            return False

    def rerun_report(self, report_id: str) -> Optional[str]:
        """
        Rerun an existing report.

        :param str report_id: The report ID
        :return: Download URL if successful, None otherwise
        :rtype: Optional[str]
        """
        variables = {"reportId": report_id}

        payload = {"query": RERUN_REPORT_QUERY, "variables": variables}

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None

            logger.info(f"Successfully triggered rerun for report {report_id}")
            return self.wait_for_report_completion(report_id)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error rerunning report: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing rerun report response: {e}")
            return None

    def list_reports(self, filter_by: Optional[Dict[str, Any]] = None) -> list:
        """
        List available reports.

        :param Optional[Dict[str, Any]] filter_by: Optional filter criteria
        :return: List of reports
        :rtype: list
        """
        variables = {"first": 50, "filterBy": filter_by or {}}

        payload = {"query": REPORTS_QUERY, "variables": variables}

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []

            reports = data.get("data", {}).get("reports", {}).get("nodes", [])
            return reports

        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing reports: {e}")
            return []
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing list reports response: {e}")
            return []
