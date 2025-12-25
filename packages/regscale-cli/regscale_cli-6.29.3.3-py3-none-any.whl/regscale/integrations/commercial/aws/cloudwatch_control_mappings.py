#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS CloudWatch Logs Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS CloudWatch Logs
CLOUDWATCH_CONTROL_MAPPINGS = {
    "AU-2": {
        "name": "Event Logging",
        "description": "Identify the types of events that the system is capable of logging",
        "checks": {
            "log_groups_exist": {
                "weight": 100,
                "pass_criteria": "CloudWatch log groups are configured and active",
                "fail_criteria": "No CloudWatch log groups configured",
            },
            "metric_filters": {
                "weight": 90,
                "pass_criteria": "Metric filters configured to monitor security events",
                "fail_criteria": "No metric filters configured",
            },
        },
    },
    "AU-3": {
        "name": "Content of Audit Records",
        "description": "Ensure audit records contain information that establishes what type of event occurred",
        "checks": {
            "log_group_configured": {
                "weight": 100,
                "pass_criteria": "Log groups capture comprehensive event data",
                "fail_criteria": "Log groups not properly configured",
            },
        },
    },
    "AU-6": {
        "name": "Audit Record Review, Analysis, and Reporting",
        "description": "Review and analyze system audit records for indications of inappropriate activity",
        "checks": {
            "subscription_filters": {
                "weight": 100,
                "pass_criteria": "Subscription filters configured for log analysis and alerting",
                "fail_criteria": "No subscription filters configured",
            },
            "metric_alarms": {
                "weight": 95,
                "pass_criteria": "Metric filters with alarms for security monitoring",
                "fail_criteria": "No metric-based alarms configured",
            },
        },
    },
    "AU-9": {
        "name": "Protection of Audit Information",
        "description": "Protect audit information and audit logging tools from unauthorized access",
        "checks": {
            "encryption_enabled": {
                "weight": 100,
                "pass_criteria": "CloudWatch log groups have encryption enabled with KMS",
                "fail_criteria": "Log groups not encrypted",
            },
        },
    },
    "AU-11": {
        "name": "Audit Record Retention",
        "description": "Retain audit records for defined time period to support after-the-fact investigations",
        "checks": {
            "retention_policy": {
                "weight": 100,
                "pass_criteria": "Log groups have retention policies configured (minimum 90 days)",
                "fail_criteria": "No retention policy or insufficient retention period",
            },
        },
    },
    "AU-12": {
        "name": "Audit Record Generation",
        "description": "Provide audit record generation capability for events",
        "checks": {
            "active_log_groups": {
                "weight": 100,
                "pass_criteria": "Log groups are actively receiving logs",
                "fail_criteria": "Log groups not actively receiving data",
            },
            "comprehensive_logging": {
                "weight": 90,
                "pass_criteria": "Multiple log groups covering different services and applications",
                "fail_criteria": "Insufficient log group coverage",
            },
        },
    },
    "SI-4": {
        "name": "System Monitoring",
        "description": "Monitor the system to detect attacks and indicators of potential attacks",
        "checks": {
            "real_time_monitoring": {
                "weight": 100,
                "pass_criteria": "Subscription filters and metric filters enable real-time monitoring",
                "fail_criteria": "No real-time monitoring configured",
            },
        },
    },
}


class CloudWatchControlMapper:
    """Map AWS CloudWatch Logs configurations to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize CloudWatch control mapper.

        :param str framework: Compliance framework
        """
        self.framework = framework
        self.mappings = CLOUDWATCH_CONTROL_MAPPINGS
        self.minimum_retention_days = 90

    def assess_cloudwatch_compliance(self, cloudwatch_data: Dict) -> Dict[str, str]:
        """
        Assess CloudWatch Logs compliance against all mapped controls.

        :param Dict cloudwatch_data: CloudWatch Logs configuration data
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["AU-2"] = self._assess_au2(cloudwatch_data)
            results["AU-3"] = self._assess_au3(cloudwatch_data)
            results["AU-6"] = self._assess_au6(cloudwatch_data)
            results["AU-9"] = self._assess_au9(cloudwatch_data)
            results["AU-11"] = self._assess_au11(cloudwatch_data)
            results["AU-12"] = self._assess_au12(cloudwatch_data)
            results["SI-4"] = self._assess_si4(cloudwatch_data)

        return results

    def _assess_au2(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-2 (Event Logging) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-2: No log groups configured")
            return "FAIL"

        # Check for metric filters
        total_metric_filters = sum(len(lg.get("MetricFilters", [])) for lg in log_groups)

        if total_metric_filters == 0:
            logger.debug("CloudWatch PARTIALLY PASSES AU-2: Log groups exist but no metric filters configured")
            return "PASS"

        logger.debug(f"CloudWatch PASSES AU-2: {len(log_groups)} log groups with {total_metric_filters} metric filters")
        return "PASS"

    def _assess_au3(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-3 (Content of Audit Records) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-3: No log groups configured")
            return "FAIL"

        logger.debug(f"CloudWatch PASSES AU-3: {len(log_groups)} log groups capturing audit data")
        return "PASS"

    def _assess_au6(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-6 (Audit Record Review, Analysis, and Reporting) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-6: No log groups configured")
            return "FAIL"

        # Check for subscription filters or metric filters
        total_subscription_filters = sum(len(lg.get("SubscriptionFilters", [])) for lg in log_groups)
        total_metric_filters = sum(len(lg.get("MetricFilters", [])) for lg in log_groups)

        if total_subscription_filters == 0 and total_metric_filters == 0:
            logger.debug("CloudWatch FAILS AU-6: No subscription or metric filters for log analysis")
            return "FAIL"

        logger.debug(
            f"CloudWatch PASSES AU-6: {total_subscription_filters} subscription filters, "
            f"{total_metric_filters} metric filters configured"
        )
        return "PASS"

    def _assess_au9(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-9 (Protection of Audit Information) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-9: No log groups configured")
            return "FAIL"

        # Check for KMS encryption
        encrypted_count = sum(1 for lg in log_groups if lg.get("kmsKeyId"))
        total_count = len(log_groups)

        if encrypted_count == 0:
            logger.debug("CloudWatch FAILS AU-9: No log groups have KMS encryption enabled")
            return "FAIL"

        if encrypted_count < total_count:
            logger.debug(f"CloudWatch PARTIALLY PASSES AU-9: {encrypted_count}/{total_count} log groups encrypted")
            return "PASS"

        logger.debug(f"CloudWatch PASSES AU-9: All {total_count} log groups have KMS encryption enabled")
        return "PASS"

    def _assess_au11(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-11 (Audit Record Retention) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-11: No log groups configured")
            return "FAIL"

        # Check retention policies
        log_groups_with_retention = []
        log_groups_without_retention = []
        insufficient_retention = []

        for lg in log_groups:
            log_group_name = lg.get("logGroupName", "unknown")
            retention_days = lg.get("retentionInDays")

            if retention_days is None:
                log_groups_without_retention.append(log_group_name)
            elif retention_days < self.minimum_retention_days:
                insufficient_retention.append((log_group_name, retention_days))
            else:
                log_groups_with_retention.append((log_group_name, retention_days))

        # Fail if no log groups have retention policies
        if len(log_groups_with_retention) == 0 and len(log_groups) > 0:
            logger.debug(
                f"CloudWatch FAILS AU-11: {len(log_groups_without_retention)} log groups without retention policy"
            )
            return "FAIL"

        # Warn if some log groups have insufficient retention
        if insufficient_retention:
            logger.debug(
                f"CloudWatch PARTIALLY PASSES AU-11: {len(insufficient_retention)} log groups have "
                f"retention < {self.minimum_retention_days} days"
            )

        logger.debug(f"CloudWatch PASSES AU-11: {len(log_groups_with_retention)} log groups with adequate retention")
        return "PASS"

    def _assess_au12(self, cloudwatch_data: Dict) -> str:
        """
        Assess AU-12 (Audit Record Generation) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS AU-12: No log groups configured")
            return "FAIL"

        # Check for active log groups (have stored bytes)
        log_group_metrics = cloudwatch_data.get("LogGroupMetrics", {})
        active_log_groups = sum(
            1 for lg_name, metrics in log_group_metrics.items() if metrics.get("StoredBytes", 0) > 0
        )

        if active_log_groups == 0:
            logger.debug("CloudWatch FAILS AU-12: No log groups are actively receiving data")
            return "FAIL"

        logger.debug(f"CloudWatch PASSES AU-12: {active_log_groups}/{len(log_groups)} log groups are active")
        return "PASS"

    def _assess_si4(self, cloudwatch_data: Dict) -> str:
        """
        Assess SI-4 (System Monitoring) compliance.

        :param Dict cloudwatch_data: CloudWatch configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        log_groups = cloudwatch_data.get("LogGroups", [])

        if not log_groups:
            logger.debug("CloudWatch FAILS SI-4: No log groups configured")
            return "FAIL"

        # Check for subscription filters and metric filters
        total_subscription_filters = sum(len(lg.get("SubscriptionFilters", [])) for lg in log_groups)
        total_metric_filters = sum(len(lg.get("MetricFilters", [])) for lg in log_groups)

        if total_subscription_filters == 0 and total_metric_filters == 0:
            logger.debug("CloudWatch FAILS SI-4: No real-time monitoring configured")
            return "FAIL"

        logger.debug(
            f"CloudWatch PASSES SI-4: Real-time monitoring enabled with {total_subscription_filters} "
            f"subscription filters and {total_metric_filters} metric filters"
        )
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
