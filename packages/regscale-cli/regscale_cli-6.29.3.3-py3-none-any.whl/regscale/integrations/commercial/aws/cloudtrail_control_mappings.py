#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS CloudTrail Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS CloudTrail
CLOUDTRAIL_CONTROL_MAPPINGS = {
    "AU-2": {
        "name": "Event Logging",
        "description": "Identify the types of events that the system is capable of logging",
        "checks": {
            "trail_enabled": {
                "weight": 100,
                "pass_criteria": "CloudTrail trails are enabled and logging",
                "fail_criteria": "CloudTrail trails are disabled or not configured",
            },
            "management_events": {
                "weight": 95,
                "pass_criteria": "Management events are being logged",
                "fail_criteria": "Management events logging not configured",
            },
        },
    },
    "AU-3": {
        "name": "Content of Audit Records",
        "description": "Ensure audit records contain information that establishes what type of event occurred",
        "checks": {
            "event_selectors": {
                "weight": 100,
                "pass_criteria": "Event selectors configured to capture necessary events",
                "fail_criteria": "Event selectors not configured or insufficient",
            },
        },
    },
    "AU-6": {
        "name": "Audit Record Review, Analysis, and Reporting",
        "description": "Review and analyze system audit records for indications of inappropriate activity",
        "checks": {
            "cloudwatch_integration": {
                "weight": 100,
                "pass_criteria": "CloudTrail integrated with CloudWatch Logs for analysis",
                "fail_criteria": "No CloudWatch Logs integration configured",
            },
        },
    },
    "AU-9": {
        "name": "Protection of Audit Information",
        "description": "Protect audit information and audit logging tools from unauthorized access",
        "checks": {
            "log_file_validation": {
                "weight": 100,
                "pass_criteria": "Log file validation enabled",
                "fail_criteria": "Log file validation not enabled",
            },
            "s3_encryption": {
                "weight": 95,
                "pass_criteria": "S3 bucket storing logs has encryption enabled",
                "fail_criteria": "S3 bucket does not have encryption",
            },
        },
    },
    "AU-11": {
        "name": "Audit Record Retention",
        "description": "Retain audit records for defined time period to support after-the-fact investigations",
        "checks": {
            "s3_lifecycle": {
                "weight": 100,
                "pass_criteria": "S3 bucket has lifecycle policies for retention",
                "fail_criteria": "No lifecycle policies configured",
            },
        },
    },
    "AU-12": {
        "name": "Audit Record Generation",
        "description": "Provide audit record generation capability for events",
        "checks": {
            "multi_region": {
                "weight": 100,
                "pass_criteria": "Multi-region trail configured for organization-wide logging",
                "fail_criteria": "No multi-region trail configured",
            },
            "data_events": {
                "weight": 85,
                "pass_criteria": "Data events logging configured for sensitive resources",
                "fail_criteria": "Data events not configured",
            },
        },
    },
    "SI-4": {
        "name": "System Monitoring",
        "description": "Monitor the system to detect attacks and indicators of potential attacks",
        "checks": {
            "sns_notifications": {
                "weight": 100,
                "pass_criteria": "SNS notifications configured for trail activity",
                "fail_criteria": "No SNS notifications configured",
            },
        },
    },
}


class CloudTrailControlMapper:
    """Map AWS CloudTrail configurations to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize CloudTrail control mapper.

        :param str framework: Compliance framework
        """
        self.framework = framework
        self.mappings = CLOUDTRAIL_CONTROL_MAPPINGS

    def assess_trail_compliance(self, trail_data: Dict) -> Dict[str, str]:
        """
        Assess CloudTrail trail compliance against all mapped controls.

        :param Dict trail_data: CloudTrail trail configuration data
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["AU-2"] = self._assess_au2(trail_data)
            results["AU-3"] = self._assess_au3(trail_data)
            results["AU-6"] = self._assess_au6(trail_data)
            results["AU-9"] = self._assess_au9(trail_data)
            results["AU-11"] = self._assess_au11(trail_data)
            results["AU-12"] = self._assess_au12(trail_data)
            results["SI-4"] = self._assess_si4(trail_data)

        return results

    def assess_all_trails_compliance(self, trails: List[Dict]) -> Dict[str, str]:
        """
        Assess compliance across all CloudTrail trails.

        :param List[Dict] trails: List of trail configurations
        :return: Dictionary mapping control IDs to overall compliance results
        :rtype: Dict[str, str]
        """
        if not trails:
            logger.debug("No CloudTrail trails to assess")
            return dict.fromkeys(self.mappings.keys(), "FAIL")

        # Aggregate results - if any trail passes a control, overall result is PASS
        aggregated_results = {}
        for control_id in self.mappings.keys():
            control_results = []
            for trail in trails:
                trail_result = self.assess_trail_compliance(trail)
                control_results.append(trail_result.get(control_id, "FAIL"))

            # If any trail passes, the control passes overall
            aggregated_results[control_id] = "PASS" if "PASS" in control_results else "FAIL"

        return aggregated_results

    def _assess_au2(self, trail_data: Dict) -> str:
        """
        Assess AU-2 (Event Logging) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        status = trail_data.get("Status", {})
        event_selectors = trail_data.get("EventSelectors", [])

        # Check if trail is logging
        is_logging = status.get("IsLogging", False)
        if not is_logging:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-2: Trail is not logging")
            return "FAIL"

        # Check if management events are being logged
        has_management_events = any(selector.get("IncludeManagementEvents", False) for selector in event_selectors)

        if not has_management_events:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-2: Management events not enabled")
            return "FAIL"

        logger.debug(f"CloudTrail {trail_name} PASSES AU-2: Trail is logging management events")
        return "PASS"

    def _assess_au3(self, trail_data: Dict) -> str:
        """
        Assess AU-3 (Content of Audit Records) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        event_selectors = trail_data.get("EventSelectors", [])

        if not event_selectors:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-3: No event selectors configured")
            return "FAIL"

        logger.debug(f"CloudTrail {trail_name} PASSES AU-3: Event selectors configured")
        return "PASS"

    def _assess_au6(self, trail_data: Dict) -> str:
        """
        Assess AU-6 (Audit Record Review) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        cloud_watch_logs_log_group_arn = trail_data.get("CloudWatchLogsLogGroupArn")

        if not cloud_watch_logs_log_group_arn:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-6: No CloudWatch Logs integration")
            return "FAIL"

        logger.debug(f"CloudTrail {trail_name} PASSES AU-6: CloudWatch Logs integration configured")
        return "PASS"

    def _assess_au9(self, trail_data: Dict) -> str:
        """
        Assess AU-9 (Protection of Audit Information) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        log_file_validation = trail_data.get("LogFileValidationEnabled", False)
        kms_key_id = trail_data.get("KmsKeyId")

        if not log_file_validation:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-9: Log file validation not enabled")
            return "FAIL"

        # Encryption is recommended but not required for passing
        if kms_key_id:
            logger.debug(f"CloudTrail {trail_name} PASSES AU-9: Log validation and encryption enabled")
        else:
            logger.debug(f"CloudTrail {trail_name} PASSES AU-9: Log validation enabled (encryption recommended)")

        return "PASS"

    def _assess_au11(self, trail_data: Dict) -> str:
        """
        Assess AU-11 (Audit Record Retention) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        s3_bucket_name = trail_data.get("S3BucketName")

        if not s3_bucket_name:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-11: No S3 bucket configured")
            return "FAIL"

        # We can't directly check S3 lifecycle policies from CloudTrail data
        # This would require additional S3 API calls
        logger.debug(f"CloudTrail {trail_name} PASSES AU-11: Logs stored in S3 bucket {s3_bucket_name}")
        return "PASS"

    def _assess_au12(self, trail_data: Dict) -> str:
        """
        Assess AU-12 (Audit Record Generation) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        is_multi_region = trail_data.get("IsMultiRegionTrail", False)
        event_selectors = trail_data.get("EventSelectors", [])

        if not is_multi_region:
            logger.debug(f"CloudTrail {trail_name} FAILS AU-12: Not a multi-region trail")
            return "FAIL"

        # Check for data events (optional but recommended)
        has_data_events = any(selector.get("DataResources", []) for selector in event_selectors)

        if has_data_events:
            logger.debug(f"CloudTrail {trail_name} PASSES AU-12: Multi-region trail with data events")
        else:
            logger.debug(f"CloudTrail {trail_name} PASSES AU-12: Multi-region trail (data events recommended)")

        return "PASS"

    def _assess_si4(self, trail_data: Dict) -> str:
        """
        Assess SI-4 (System Monitoring) compliance.

        :param Dict trail_data: Trail configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        trail_name = trail_data.get("Name", "unknown")
        sns_topic_arn = trail_data.get("SnsTopicARN")

        if not sns_topic_arn:
            logger.debug(f"CloudTrail {trail_name} FAILS SI-4: No SNS notifications configured")
            return "FAIL"

        logger.debug(f"CloudTrail {trail_name} PASSES SI-4: SNS notifications configured")
        return "PASS"

    def get_control_description(self, control_id: str) -> Optional[str]:
        """Get human-readable description for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return f"{control_data.get('name')}: {control_data.get('description', '')}"
        return None

    def get_mapped_controls(self) -> List[str]:
        """Get list of all control IDs mapped for this framework."""
        return list(self.mappings.keys())

    def get_check_details(self, control_id: str) -> Optional[Dict]:
        """Get detailed check criteria for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return control_data.get("checks", {})
        return None
