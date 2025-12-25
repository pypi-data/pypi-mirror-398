#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RegScale AWS Integrations"""
import re
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from dateutil import parser

from regscale.core.app.utils.app_utils import create_logger

logger = create_logger()

# Error message constants
ERROR_MSG_FETCHING_AWS_RESOURCES = "Unexpected error when fetching resources from AWS: %s"


def check_finding_severity(finding: dict, comment: Optional[str] = None) -> str:
    """Check the severity of the finding

    This function extracts severity from AWS Security Hub findings by checking:
    1. finding["Severity"]["Label"] (primary source for all findings including Inspector CVEs)
    2. finding["FindingProviderFields"]["Severity"]["Label"] (alternative source)
    3. Comment text parsing as fallback (for legacy compatibility)

    :param dict finding: AWS Security Hub finding
    :param Optional[str] comment: Comment from AWS Security Hub finding (optional, for fallback)
    :return: Severity of the finding (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL, or empty string)
    :rtype: str
    """
    result = ""

    # Primary: Check Severity.Label (available in all findings, including Inspector CVEs)
    if "Severity" in finding and "Label" in finding["Severity"]:
        result = finding["Severity"]["Label"]
        logger.debug(f"Found severity from Severity.Label: {result}")
        return result

    # Secondary: Check FindingProviderFields.Severity.Label (alternative source)
    if "FindingProviderFields" in finding:
        provider_severity = finding.get("FindingProviderFields", {}).get("Severity", {}).get("Label", "")
        if provider_severity:
            result = provider_severity
            logger.debug(f"Found severity from FindingProviderFields.Severity.Label: {result}")
            return result

    # Fallback: Parse from comment text (for legacy compatibility)
    if comment:
        match = re.search(r"(?<=Finding Severity: ).*", comment)
        if match:
            severity = match.group()
            result = severity
            logger.debug(f"Found severity from comment parsing: {result}")
            return result

    if not result:
        logger.warning(f"No severity found for finding {finding.get('Id', 'unknown')}")

    return result


def get_due_date(earliest_date_performed: datetime, days: int) -> datetime:
    """Returns the due date for an issue

    :param datetime earliest_date_performed: Earliest date performed
    :param int days: Days to add to the earliest date performed
    :return: Due date
    :rtype: datetime
    """
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        due_date = datetime.strptime(earliest_date_performed, fmt) + timedelta(days=days)
    except ValueError:
        # Try to determine the date format from a string
        due_date = parser.parse(earliest_date_performed) + timedelta(days)
    return due_date


def determine_status_and_results(finding: Any) -> Tuple[str, str]:
    """
    Determine Status and Results

    :param Any finding: AWS Finding
    :return: Status and Results
    :rtype: Tuple[str, str]
    """
    status = "Pass"
    results = ""
    if "Compliance" in finding.keys():
        status = "Fail" if finding["Compliance"]["Status"] == "FAILED" else "Pass"
        results = ", ".join(finding.get("Compliance", {}).get("RelatedRequirements", [])) or "N/A"
    if "FindingProviderFields" in finding.keys():
        status = (
            "Fail"
            if finding.get("FindingProviderFields", {}).get("Severity", {}).get("Label", "")
            in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            else "Pass"
        )
    if "PatchSummary" in finding.keys() and not results:
        results = (
            f"{finding.get('PatchSummary', {}).get('MissingCount', 0)} Missing Patch(s) of "
            "{finding.get('PatchSummary', {}).get('InstalledCount', 0)}"
        )
    # Ensure results is always a string, not None
    if not results:
        results = "N/A"
    return status, results


def get_comments(finding: dict) -> str:
    """
    Get Comments

    :param dict finding: AWS Finding
    :return: Comments
    :rtype: str
    """
    try:
        return (
            finding["Remediation"]["Recommendation"]["Text"]
            + "<br></br>"
            + finding["Remediation"]["Recommendation"]["Url"]
            + "<br></br>"
            + f"""Finding Severity: {finding["FindingProviderFields"]["Severity"]["Label"]}"""
        )
    except KeyError:
        return "No remediation recommendation available"


def fetch_aws_findings(
    aws_client: BaseClient, minimum_severity: Optional[str] = None, posture_management_only: bool = False
) -> list:
    """Fetch AWS Findings with optimized rate limiting and pagination

    :param BaseClient aws_client: AWS Security Hub Client
    :param Optional[str] minimum_severity: Minimum severity to filter (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
    :param bool posture_management_only: If True, only fetch posture management findings (compliance checks)
    :return: AWS Findings
    :rtype: list
    """
    findings = []
    try:
        # Use optimized SecurityHubPuller for better performance
        from regscale.integrations.commercial.aws.security_hub import SecurityHubPuller

        # Extract region from the client
        region = aws_client.meta.region_name

        # Create SecurityHubPuller with same region as the client
        puller = SecurityHubPuller(region_name=region)

        # Use existing client instead of creating new one to maintain credentials
        puller.client = aws_client

        # Fetch all findings with optimized pagination and rate limiting
        logger.info("Using optimized SecurityHubPuller for findings retrieval...")

        # Determine severity labels if minimum_severity is provided
        severity_labels = None
        if minimum_severity:
            severity_labels = SecurityHubPuller.get_severity_filters_from_minimum(minimum_severity)
            logger.info(f"Applying minimum severity filter '{minimum_severity}': {severity_labels}")

        # Fetch findings based on type requested
        if posture_management_only:
            logger.info("Fetching posture management findings only (security standards compliance checks)")
            findings = puller.get_posture_management_findings(severity_labels=severity_labels)
        elif severity_labels:
            findings = puller.get_findings_by_severity(severity_labels=severity_labels)
        else:
            findings = puller.get_all_findings_with_retries()

        logger.info(f"Successfully fetched {len(findings)} findings with rate limiting")

    except ImportError:
        # Fallback to original method if SecurityHubPuller not available
        logger.warning("SecurityHubPuller not available, falling back to basic client")
        findings = fallback_fetch_aws_findings(aws_client)
    except ClientError as cex:
        logger.error("Unexpected error: %s", cex)
    except Exception as e:
        logger.error("Error using SecurityHubPuller, falling back to basic client: %s", e)
        findings = fallback_fetch_aws_findings(aws_client)

    return findings


def fallback_fetch_aws_findings(aws_client: BaseClient) -> list:
    """Fallback method to fetch AWS Findings without pagination

    :param BaseClient aws_client: AWS Security Hub Client
    :return: AWS Findings
    :rtype: list
    """
    findings = []
    try:
        response = aws_client.get_findings()
        findings = response.get("Findings", [])
    except ClientError as cex:
        create_logger().error(ERROR_MSG_FETCHING_AWS_RESOURCES, cex)
    return findings


def fetch_aws_findings_v2(aws_client: BaseClient) -> list:
    """Fetch AWS Findings

    :param BaseClient aws_client: AWS Security Hub Client
    :return: AWS Findings
    :rtype: list
    """
    findings = []
    try:
        response = aws_client.get_findings_v2()
        findings = response.get("Findings", [])
    except ClientError as cex:
        create_logger().error(ERROR_MSG_FETCHING_AWS_RESOURCES, cex)
    return findings


def fetch_aws_resources(aws_client: BaseClient) -> list:
    """Fetch AWS Resources

    :param BaseClient aws_client: AWS Security Hub Client
    :return: AWS Resources
    :rtype: list
    """
    resources = []
    try:
        response = aws_client.get_resources_v2()
        resources = response.get("Resources", [])
        logger.info(f"Fetched {len(resources)} resources from Security Hub")
    except ClientError as cex:
        create_logger().error(ERROR_MSG_FETCHING_AWS_RESOURCES, cex)
    return resources
