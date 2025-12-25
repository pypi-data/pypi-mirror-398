#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS to OCSF mapper for normalizing AWS security findings"""

import logging
from datetime import datetime
from typing import Optional

from regscale.integrations.commercial.aws.ocsf import constants

logger = logging.getLogger("regscale")

# Constants
AWS_VENDOR_NAME = "Amazon Web Services"


class AWSOCSFMapper:
    """Maps AWS security findings to OCSF (Open Cybersecurity Schema Framework) format"""

    def __init__(self):
        """Initialize OCSF mapper"""
        self.ocsf_version = constants.OCSF_VERSION

    def guardduty_to_ocsf(self, finding: dict) -> dict:
        """
        Map AWS GuardDuty finding to OCSF Detection Finding (Class 2004)

        :param dict finding: GuardDuty finding in native AWS format
        :return: OCSF-formatted detection finding
        :rtype: dict
        """
        severity_score = finding.get("Severity", 0)
        severity_id = constants.map_guardduty_severity(severity_score)

        # Extract resource information
        resource = finding.get("Resource", {})
        resource_type = resource.get("ResourceType", "Unknown")

        # Build OCSF finding
        ocsf_finding = {
            "metadata": {
                "version": self.ocsf_version,
                "product": {
                    "name": "AWS GuardDuty",
                    "vendor_name": AWS_VENDOR_NAME,
                },
                "logged_time": self._parse_aws_timestamp(finding.get("UpdatedAt")),
            },
            "class_uid": constants.CLASS_DETECTION_FINDING,
            "class_name": "Detection Finding",
            "category_uid": 2,  # Findings
            "category_name": "Findings",
            "activity_id": self._map_guardduty_activity(finding),
            "activity_name": self._get_activity_name(self._map_guardduty_activity(finding)),
            "severity_id": severity_id,
            "severity": self._get_severity_name(severity_id),
            "confidence_id": self._map_guardduty_confidence(finding.get("Confidence", 0)),
            "finding_info": {
                "uid": finding.get("Id"),
                "title": finding.get("Title", ""),
                "desc": finding.get("Description", ""),
                "types": [finding.get("Type", "")],
                "created_time": self._parse_aws_timestamp(finding.get("CreatedAt")),
                "modified_time": self._parse_aws_timestamp(finding.get("UpdatedAt")),
                "product_uid": finding.get("Arn", ""),
            },
            "resources": [
                {
                    "uid": resource.get("AccessKeyDetails", {}).get("AccessKeyId")
                    or resource.get("InstanceDetails", {}).get("InstanceId")
                    or "unknown",
                    "type": resource_type,
                    "cloud_partition": finding.get("Partition", "aws"),
                    "region": finding.get("Region", ""),
                }
            ],
            "cloud": {
                "provider": "AWS",
                "account": {
                    "uid": finding.get("AccountId", ""),
                },
                "region": finding.get("Region", ""),
            },
            "raw_data": finding,
        }

        return ocsf_finding

    def securityhub_to_ocsf(self, finding: dict) -> dict:
        """
        Map AWS Security Hub finding to OCSF Security Finding (Class 2001)

        :param dict finding: Security Hub finding in native AWS format
        :return: OCSF-formatted security finding
        :rtype: dict
        """
        severity = finding.get("Severity", {})
        severity_label = severity.get("Label", "INFORMATIONAL")
        severity_id = constants.map_securityhub_severity(severity_label)

        # Extract workflow status
        workflow = finding.get("Workflow", {})
        workflow_status = workflow.get("Status", "NEW")
        status_id = constants.map_securityhub_status(workflow_status)

        # Extract resource information
        resources = finding.get("Resources", [{}])

        # Build OCSF finding
        ocsf_finding = {
            "metadata": {
                "version": self.ocsf_version,
                "product": {
                    "name": "AWS Security Hub",
                    "vendor_name": AWS_VENDOR_NAME,
                    "feature": {
                        "name": finding.get("ProductName", ""),
                    },
                },
                "logged_time": self._parse_aws_timestamp(finding.get("UpdatedAt")),
            },
            "class_uid": constants.CLASS_SECURITY_FINDING,
            "class_name": "Security Finding",
            "category_uid": 2,  # Findings
            "category_name": "Findings",
            "activity_id": self._map_securityhub_activity(workflow_status),
            "activity_name": self._get_activity_name(self._map_securityhub_activity(workflow_status)),
            "severity_id": severity_id,
            "severity": self._get_severity_name(severity_id),
            "status_id": status_id,
            "status": self._get_status_name(status_id),
            "finding_info": {
                "uid": finding.get("Id"),
                "title": finding.get("Title", ""),
                "desc": finding.get("Description", ""),
                "types": finding.get("Types", []),
                "created_time": self._parse_aws_timestamp(finding.get("CreatedAt")),
                "modified_time": self._parse_aws_timestamp(finding.get("UpdatedAt")),
                "first_seen_time": self._parse_aws_timestamp(finding.get("FirstObservedAt")),
                "last_seen_time": self._parse_aws_timestamp(finding.get("LastObservedAt")),
                "product_uid": finding.get("ProductArn", ""),
            },
            "compliance": {
                "status": finding.get("Compliance", {}).get("Status", ""),
                "requirements": finding.get("Compliance", {}).get("RelatedRequirements", []),
            },
            "resources": self._map_securityhub_resources(resources),
            "cloud": {
                "provider": "AWS",
                "account": {
                    "uid": finding.get("AwsAccountId", ""),
                },
                "region": finding.get("Region", ""),
            },
            "vulnerabilities": self._extract_vulnerabilities(finding),
            "remediation": {
                "desc": finding.get("Remediation", {}).get("Recommendation", {}).get("Text", ""),
                "references": finding.get("Remediation", {}).get("Recommendation", {}).get("Url", ""),
            },
            "raw_data": finding,
        }

        return ocsf_finding

    def cloudtrail_event_to_ocsf(self, event: dict) -> dict:
        """
        Map AWS CloudTrail event to OCSF Cloud API Activity (Class 3005)

        :param dict event: CloudTrail event in native AWS format
        :return: OCSF-formatted cloud API activity
        :rtype: dict
        """
        ocsf_event = {
            "metadata": {
                "version": self.ocsf_version,
                "product": {
                    "name": "AWS CloudTrail",
                    "vendor_name": AWS_VENDOR_NAME,
                },
                "logged_time": self._parse_aws_timestamp(event.get("EventTime")),
            },
            "class_uid": constants.CLASS_CLOUD_API,
            "class_name": "Cloud API",
            "category_uid": 3,  # Cloud Activity
            "category_name": "Cloud Activity",
            "activity_id": 1 if event.get("EventName") else 99,
            "activity_name": event.get("EventName", "Unknown"),
            "severity_id": self._determine_cloudtrail_severity(event),
            "api": {
                "operation": event.get("EventName", ""),
                "service": {
                    "name": event.get("EventSource", "").split(".")[0],
                },
                "request": {
                    "uid": event.get("RequestID", ""),
                },
                "response": {
                    "error": event.get("ErrorCode"),
                    "message": event.get("ErrorMessage"),
                },
            },
            "cloud": {
                "provider": "AWS",
                "account": {
                    "uid": event.get("RecipientAccountId", ""),
                },
                "region": event.get("AwsRegion", ""),
            },
            "actor": {
                "user": {
                    "name": event.get("UserIdentity", {}).get("UserName"),
                    "uid": event.get("UserIdentity", {}).get("PrincipalId"),
                    "type": event.get("UserIdentity", {}).get("Type"),
                },
            },
            "src_endpoint": {
                "ip": event.get("SourceIPAddress"),
                "domain": event.get("UserAgent"),
            },
            "http_request": {
                "user_agent": event.get("UserAgent"),
            },
            "resources": self._map_cloudtrail_resources(event.get("Resources", [])),
            "raw_data": event,
        }

        return ocsf_event

    def _map_guardduty_activity(self, finding: dict) -> int:
        """
        Map GuardDuty finding to OCSF activity ID

        :param dict finding: GuardDuty finding
        :return: OCSF activity ID
        :rtype: int
        """
        service_info = finding.get("Service", {})
        if service_info.get("Archived"):
            return constants.ACTIVITY_CLOSE
        elif service_info.get("Count", 1) == 1:
            return constants.ACTIVITY_CREATE
        else:
            return constants.ACTIVITY_UPDATE

    def _map_securityhub_activity(self, workflow_status: str) -> int:
        """
        Map Security Hub workflow status to OCSF activity ID

        :param str workflow_status: Security Hub workflow status
        :return: OCSF activity ID
        :rtype: int
        """
        status_activity_map = {
            "NEW": constants.ACTIVITY_CREATE,
            "NOTIFIED": constants.ACTIVITY_UPDATE,
            "RESOLVED": constants.ACTIVITY_CLOSE,
            "SUPPRESSED": constants.ACTIVITY_CLOSE,
        }
        return status_activity_map.get(workflow_status.upper(), constants.ACTIVITY_OTHER)

    def _map_guardduty_confidence(self, confidence: float) -> int:
        """
        Map GuardDuty confidence score to OCSF confidence ID

        :param float confidence: GuardDuty confidence (0.0-10.0)
        :return: OCSF confidence ID
        :rtype: int
        """
        if confidence >= 7.0:
            return constants.CONFIDENCE_HIGH
        elif confidence >= 4.0:
            return constants.CONFIDENCE_MEDIUM
        elif confidence > 0:
            return constants.CONFIDENCE_LOW
        return constants.CONFIDENCE_UNKNOWN

    def _map_securityhub_resources(self, resources: list) -> list:
        """
        Map Security Hub resources to OCSF resource format

        :param list resources: Security Hub resources
        :return: OCSF resources
        :rtype: list
        """
        ocsf_resources = []
        for resource in resources:
            ocsf_resource = {
                "uid": resource.get("Id", ""),
                "type": resource.get("Type", ""),
                "region": resource.get("Region", ""),
                "partition": resource.get("Partition", "aws"),
            }

            # Add resource details if available
            details = resource.get("Details", {})
            if details:
                ocsf_resource["data"] = details

            ocsf_resources.append(ocsf_resource)

        return ocsf_resources

    def _map_cloudtrail_resources(self, resources: list) -> list:
        """
        Map CloudTrail resources to OCSF resource format

        :param list resources: CloudTrail resources
        :return: OCSF resources
        :rtype: list
        """
        ocsf_resources = []
        for resource in resources:
            ocsf_resources.append(
                {
                    "uid": resource.get("ARN", ""),
                    "type": resource.get("ResourceType", ""),
                    "name": resource.get("ResourceName", ""),
                }
            )
        return ocsf_resources

    def _extract_vulnerabilities(self, finding: dict) -> list:
        """
        Extract vulnerability information from Security Hub finding

        :param dict finding: Security Hub finding
        :return: OCSF vulnerabilities
        :rtype: list
        """
        vulnerabilities = finding.get("Vulnerabilities", [])
        ocsf_vulns = []

        for vuln in vulnerabilities:
            ocsf_vuln = {
                "cve": {
                    "uid": vuln.get("Id", ""),
                },
                "references": vuln.get("ReferenceUrls", []),
                "vendor_name": vuln.get("Vendor", {}).get("Name", ""),
            }

            # Add CVSS scores if available
            cvss = vuln.get("Cvss", [])
            if cvss:
                ocsf_vuln["cvss"] = cvss

            ocsf_vulns.append(ocsf_vuln)

        return ocsf_vulns if ocsf_vulns else None

    def _determine_cloudtrail_severity(self, event: dict) -> int:
        """
        Determine severity for CloudTrail event based on error codes

        :param dict event: CloudTrail event
        :return: OCSF severity ID
        :rtype: int
        """
        error_code = event.get("ErrorCode")
        if error_code:
            # Failed API calls are more severe
            if error_code in ["UnauthorizedOperation", "AccessDenied"]:
                return constants.SEVERITY_MEDIUM
            return constants.SEVERITY_LOW
        return constants.SEVERITY_INFORMATIONAL

    def _parse_aws_timestamp(self, timestamp: Optional[str]) -> Optional[int]:
        """
        Parse AWS timestamp to Unix epoch milliseconds

        :param Optional[str] timestamp: AWS timestamp string
        :return: Unix epoch milliseconds or None
        :rtype: Optional[int]
        """
        if not timestamp:
            return None

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return int(dt.timestamp() * 1000)
        except (ValueError, AttributeError) as ex:
            logger.warning("Failed to parse timestamp %s: %s", timestamp, ex)
            return None

    def _get_severity_name(self, severity_id: int) -> str:
        """
        Get OCSF severity name from severity ID

        :param int severity_id: OCSF severity ID
        :return: Severity name
        :rtype: str
        """
        severity_names = {
            constants.SEVERITY_UNKNOWN: "Unknown",
            constants.SEVERITY_INFORMATIONAL: "Informational",
            constants.SEVERITY_LOW: "Low",
            constants.SEVERITY_MEDIUM: "Medium",
            constants.SEVERITY_HIGH: "High",
            constants.SEVERITY_CRITICAL: "Critical",
            constants.SEVERITY_FATAL: "Fatal",
        }
        return severity_names.get(severity_id, "Unknown")

    def _get_status_name(self, status_id: int) -> str:
        """
        Get OCSF status name from status ID

        :param int status_id: OCSF status ID
        :return: Status name
        :rtype: str
        """
        status_names = {
            constants.STATUS_NEW: "New",
            constants.STATUS_IN_PROGRESS: "In Progress",
            constants.STATUS_SUPPRESSED: "Suppressed",
            constants.STATUS_RESOLVED: "Resolved",
            constants.STATUS_OTHER: "Other",
        }
        return status_names.get(status_id, "Other")

    def _get_activity_name(self, activity_id: int) -> str:
        """
        Get OCSF activity name from activity ID

        :param int activity_id: OCSF activity ID
        :return: Activity name
        :rtype: str
        """
        activity_names = {
            constants.ACTIVITY_CREATE: "Create",
            constants.ACTIVITY_UPDATE: "Update",
            constants.ACTIVITY_CLOSE: "Close",
            constants.ACTIVITY_OTHER: "Other",
        }
        return activity_names.get(activity_id, "Other")
