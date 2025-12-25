#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Security Hub optimized data puller with rate limiting and pagination."""

import logging
import sys
import time
from typing import Any, Dict, List, Optional

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

logger = logging.getLogger("regscale")


class SecurityHubPuller:
    """
    Optimized AWS Security Hub data puller with intelligent rate limiting and pagination.

    This class provides enhanced functionality for fetching Security Hub findings with:
    - Automatic pagination handling
    - Exponential backoff retry logic
    - Rate limiting compliance
    - Efficient batch processing
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        profile_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        max_retries: int = 5,
        initial_delay: float = 1.0,
    ):
        """
        Initialize SecurityHub puller.

        :param str region_name: AWS region name
        :param Optional[str] profile_name: AWS profile name
        :param Optional[str] aws_access_key_id: AWS access key ID
        :param Optional[str] aws_secret_access_key: AWS secret access key
        :param Optional[str] aws_session_token: AWS session token
        :param int max_retries: Maximum number of retries for failed requests
        :param float initial_delay: Initial delay in seconds for exponential backoff
        """
        self.region_name = region_name
        self.max_retries = max_retries
        self.initial_delay = initial_delay

        # Create boto3 session
        if profile_name:
            session = boto3.Session(profile_name=profile_name, region_name=region_name)
        elif aws_access_key_id and aws_secret_access_key:
            session = boto3.Session(
                region_name=region_name,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            session = boto3.Session(region_name=region_name)

        # Create Security Hub client
        self.client: BaseClient = session.client("securityhub")

    def get_all_findings_with_retries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all Security Hub findings with automatic pagination and retry logic.

        :param Optional[Dict[str, Any]] filters: Security Hub filters to apply
        :param int max_results: Maximum results per page (1-100)
        :return: List of all findings
        :rtype: List[Dict[str, Any]]
        """
        all_findings = []
        next_token = None
        page_count = 0

        # Default filters if none provided
        if filters is None:
            filters = {
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                # Include NEW and NOTIFIED (In Progress) workflow statuses
                # Exclude SUPPRESSED and RESOLVED
                "WorkflowStatus": [
                    {"Value": "NEW", "Comparison": "EQUALS"},
                    {"Value": "NOTIFIED", "Comparison": "EQUALS"},
                ],
            }

        logger.info("Starting Security Hub findings retrieval with pagination...")

        while True:
            page_count += 1
            try:
                # Build request parameters
                params = {
                    "Filters": filters,
                    "MaxResults": max_results,
                }

                if next_token:
                    params["NextToken"] = next_token

                # Fetch findings with retry logic
                response = self._get_findings_with_retry(params)

                # Extract findings from response
                findings = response.get("Findings", [])
                all_findings.extend(findings)

                logger.info(f"Retrieved page {page_count}: {len(findings)} findings (Total: {len(all_findings)})")

                # Check for next page
                next_token = response.get("NextToken")
                if not next_token:
                    break

                # Brief pause between pages to respect rate limits
                time.sleep(0.2)

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                error_message = e.response.get("Error", {}).get("Message", str(e))
                # Fail fast on authentication/authorization errors - these won't resolve with retries
                auth_errors = {
                    "ExpiredTokenException": "Your AWS session token has expired. Please refresh your credentials.",
                    "InvalidIdentityToken": "The provided identity token is invalid. Please check your credentials.",
                    "InvalidClientTokenId": "The AWS access key ID is invalid. Please verify your credentials.",
                    "AccessDeniedException": "Access denied. Please ensure your credentials have the required permissions.",
                    "UnauthorizedAccess": "Unauthorized access. Please check your AWS credentials and permissions.",
                    "InvalidAccessKeyId": "The AWS access key ID does not exist. Please verify your credentials.",
                    "SignatureDoesNotMatch": "The request signature does not match. Please check your secret access key.",
                    "IncompleteSignature": "The request signature is incomplete. Please check your credentials.",
                    "MissingAuthenticationToken": "Missing authentication token. Please provide valid AWS credentials.",
                }
                if error_code in auth_errors:
                    logger.error(f"AWS Authentication Error: {auth_errors[error_code]}")
                    logger.error(f"Details: {error_message}")
                    sys.exit(1)
                logger.error(f"Failed to retrieve findings on page {page_count}: {error_code} - {str(e)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page_count}: {str(e)}")
                break

        logger.info(f"Completed Security Hub retrieval: {len(all_findings)} total findings across {page_count} pages")

        return all_findings

    def _get_findings_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute get_findings with exponential backoff retry logic.

        :param Dict[str, Any] params: Parameters for get_findings call
        :return: API response
        :rtype: Dict[str, Any]
        :raises ClientError: If all retries are exhausted
        """
        delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                response = self.client.get_findings(**params)
                return response

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")

                # Handle throttling errors with exponential backoff
                if error_code in ["ThrottlingException", "TooManyRequestsException"]:
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {self.max_retries} attempts")
                        raise
                else:
                    # For non-throttling errors, raise immediately
                    logger.error(f"Security Hub API error: {error_code} - {str(e)}")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error calling Security Hub API: {str(e)}")
                raise

        # Should not reach here, but just in case
        raise RuntimeError(f"Failed to retrieve findings after {self.max_retries} attempts")

    def get_findings_by_severity(self, severity_labels: List[str], max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch findings filtered by severity levels.

        :param List[str] severity_labels: Severity labels to filter (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
        :param int max_results: Maximum results per page
        :return: List of findings matching severity criteria
        :rtype: List[Dict[str, Any]]
        """
        filters = {
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            "SeverityLabel": [{"Value": label, "Comparison": "EQUALS"} for label in severity_labels],
            # Include NEW and NOTIFIED workflow statuses, exclude SUPPRESSED and RESOLVED
            "WorkflowStatus": [
                {"Value": "NEW", "Comparison": "EQUALS"},
                {"Value": "NOTIFIED", "Comparison": "EQUALS"},
            ],
        }

        logger.info(f"Fetching findings with severity: {', '.join(severity_labels)}")
        return self.get_all_findings_with_retries(filters=filters, max_results=max_results)

    @staticmethod
    def get_severity_filters_from_minimum(minimum_severity: str) -> List[str]:
        """
        Get list of severity labels to filter based on minimum severity threshold.

        :param str minimum_severity: Minimum severity level (CRITICAL, HIGH, MEDIUM, LOW, INFORMATIONAL)
        :return: List of severity labels at or above the minimum threshold
        :rtype: List[str]
        """
        severity_hierarchy = ["INFORMATIONAL", "LOW", "MEDIUM", "MODERATE", "HIGH", "CRITICAL"]
        min_sev_upper = minimum_severity.upper()

        # Handle MODERATE as alias for MEDIUM
        if min_sev_upper == "MODERATE":
            min_sev_upper = "MEDIUM"

        # Find the index of the minimum severity
        if min_sev_upper not in severity_hierarchy:
            logger.warning(f"Unknown minimum severity '{minimum_severity}', defaulting to LOW")
            min_sev_upper = "LOW"

        min_index = severity_hierarchy.index(min_sev_upper)

        # Return all severities at or above the minimum (excluding MODERATE since it's an alias)
        return [sev for sev in severity_hierarchy[min_index:] if sev != "MODERATE"]

    def get_findings_by_compliance_status(
        self, compliance_statuses: List[str], max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch findings filtered by compliance status (for posture management findings).

        :param List[str] compliance_statuses: Compliance statuses (PASSED, FAILED, WARNING, NOT_AVAILABLE)
        :param int max_results: Maximum results per page
        :return: List of findings matching compliance criteria
        :rtype: List[Dict[str, Any]]
        """
        filters = {
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            "ComplianceStatus": [{"Value": status, "Comparison": "EQUALS"} for status in compliance_statuses],
            # Include NEW and NOTIFIED workflow statuses, exclude SUPPRESSED and RESOLVED
            "WorkflowStatus": [
                {"Value": "NEW", "Comparison": "EQUALS"},
                {"Value": "NOTIFIED", "Comparison": "EQUALS"},
            ],
        }

        logger.info(f"Fetching findings with compliance status: {', '.join(compliance_statuses)}")
        return self.get_all_findings_with_retries(filters=filters, max_results=max_results)

    def get_posture_management_findings(
        self, severity_labels: Optional[List[str]] = None, max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch posture management findings (compliance checks from security standards).
        These are findings that have a ComplianceStatus, indicating they come from
        enabled security standards like CIS, PCI-DSS, AWS Foundational Security Best Practices, etc.

        :param Optional[List[str]] severity_labels: Optional severity filter
        :param int max_results: Maximum results per page
        :return: List of posture management findings
        :rtype: List[Dict[str, Any]]
        """
        filters = {
            "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
            # Include NEW and NOTIFIED workflow statuses, exclude SUPPRESSED and RESOLVED
            "WorkflowStatus": [
                {"Value": "NEW", "Comparison": "EQUALS"},
                {"Value": "NOTIFIED", "Comparison": "EQUALS"},
            ],
            # Posture management findings have FAILED compliance status
            # (PASSED findings are not vulnerabilities)
            "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}],
        }

        # Add severity filter if provided
        if severity_labels:
            filters["SeverityLabel"] = [{"Value": label, "Comparison": "EQUALS"} for label in severity_labels]
            logger.info(f"Fetching posture management findings with severity: {', '.join(severity_labels)}")
        else:
            logger.info("Fetching all posture management findings (FAILED compliance checks)")

        return self.get_all_findings_with_retries(filters=filters, max_results=max_results)

    def get_findings_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Get count of findings matching filters without retrieving full data.

        :param Optional[Dict[str, Any]] filters: Security Hub filters
        :return: Count of matching findings
        :rtype: int
        """
        try:
            if filters is None:
                filters = {"RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]}

            # Use MaxResults=1 to minimize data transfer
            response = self.client.get_findings(Filters=filters, MaxResults=1)

            # The total count is typically not directly available, but we can
            # estimate from pagination. For exact count, we'd need to paginate fully.
            # This is a lightweight check to see if any findings exist.
            findings_count = len(response.get("Findings", []))

            if response.get("NextToken"):
                logger.info("More than 1 finding exists (exact count requires full pagination)")
                # For a rough estimate, we could paginate a few pages
                return findings_count  # Would need full pagination for exact count
            else:
                return findings_count

        except ClientError as e:
            logger.error(f"Failed to get findings count: {str(e)}")
            return 0
