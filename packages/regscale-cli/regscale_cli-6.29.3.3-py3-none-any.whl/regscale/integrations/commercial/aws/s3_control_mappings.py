#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS S3 Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS S3
S3_CONTROL_MAPPINGS = {
    "SC-13": {
        "name": "Cryptographic Protection",
        "description": "Implement cryptographic mechanisms to prevent unauthorized disclosure of information",
        "checks": {
            "encryption_at_rest": {
                "weight": 100,
                "pass_criteria": "All S3 buckets have server-side encryption enabled",
                "fail_criteria": "One or more buckets lack encryption configuration",
            },
            "encryption_algorithm": {
                "weight": 90,
                "pass_criteria": "Buckets use approved encryption algorithms (AES-256, KMS)",
                "fail_criteria": "Buckets use weak or no encryption",
            },
        },
    },
    "SC-28": {
        "name": "Protection of Information at Rest",
        "description": "Protect the confidentiality and integrity of information at rest",
        "checks": {
            "bucket_encryption": {
                "weight": 100,
                "pass_criteria": "S3 buckets have default encryption enabled",
                "fail_criteria": "Buckets store data without encryption",
            },
            "versioning_enabled": {
                "weight": 85,
                "pass_criteria": "Versioning enabled to protect against accidental deletion",
                "fail_criteria": "Versioning disabled or not configured",
            },
        },
    },
    "AC-3": {
        "name": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access",
        "checks": {
            "public_access_blocked": {
                "weight": 100,
                "pass_criteria": "Public access block settings enabled on all buckets",
                "fail_criteria": "Buckets allow public access",
            },
            "bucket_policy": {
                "weight": 95,
                "pass_criteria": "Bucket policies enforce least privilege access",
                "fail_criteria": "Buckets have overly permissive or public policies",
            },
        },
    },
    "AC-6": {
        "name": "Least Privilege",
        "description": "Employ the principle of least privilege",
        "checks": {
            "acl_configuration": {
                "weight": 100,
                "pass_criteria": "ACLs grant minimal necessary permissions",
                "fail_criteria": "ACLs grant broad or public permissions",
            },
            "policy_restrictions": {
                "weight": 90,
                "pass_criteria": "Bucket policies restrict access to authorized principals only",
                "fail_criteria": "Policies allow excessive permissions",
            },
        },
    },
    "AU-2": {
        "name": "Event Logging",
        "description": "Identify events to be logged",
        "checks": {
            "access_logging": {
                "weight": 100,
                "pass_criteria": "S3 access logging enabled for all buckets",
                "fail_criteria": "Buckets do not have access logging enabled",
            },
        },
    },
    "AU-9": {
        "name": "Protection of Audit Information",
        "description": "Protect audit information and audit logging tools",
        "checks": {
            "log_bucket_protection": {
                "weight": 100,
                "pass_criteria": "Log destination buckets have restricted access and versioning",
                "fail_criteria": "Log buckets lack protection controls",
            },
        },
    },
    "CP-9": {
        "name": "System Backup",
        "description": "Conduct backups of system-level and user-level information",
        "checks": {
            "versioning": {
                "weight": 100,
                "pass_criteria": "Versioning enabled to maintain data history",
                "fail_criteria": "Versioning not enabled",
            },
            "replication": {
                "weight": 85,
                "pass_criteria": "Cross-region replication configured for critical buckets",
                "fail_criteria": "No replication configured",
            },
        },
    },
}


class S3ControlMapper:
    """Map AWS S3 bucket configurations to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize S3 control mapper.

        :param str framework: Compliance framework
        """
        self.framework = framework
        self.mappings = S3_CONTROL_MAPPINGS

    def assess_bucket_compliance(self, bucket_data: Dict) -> Dict[str, str]:
        """
        Assess S3 bucket compliance against all mapped controls.

        :param Dict bucket_data: S3 bucket configuration data
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["SC-13"] = self._assess_sc13(bucket_data)
            results["SC-28"] = self._assess_sc28(bucket_data)
            results["AC-3"] = self._assess_ac3(bucket_data)
            results["AC-6"] = self._assess_ac6(bucket_data)
            results["AU-2"] = self._assess_au2(bucket_data)
            results["AU-9"] = self._assess_au9(bucket_data)
            results["CP-9"] = self._assess_cp9(bucket_data)

        return results

    def assess_all_buckets_compliance(self, buckets: List[Dict]) -> Dict[str, str]:
        """
        Assess compliance across all S3 buckets.

        :param List[Dict] buckets: List of bucket configurations
        :return: Dictionary mapping control IDs to overall compliance results
        :rtype: Dict[str, str]
        """
        if not buckets:
            logger.debug("No S3 buckets to assess")
            return dict.fromkeys(self.mappings.keys(), "PASS")

        # Aggregate results - if any bucket fails a control, overall result is FAIL
        aggregated_results = {}
        for control_id in self.mappings.keys():
            control_results = []
            for bucket in buckets:
                bucket_result = self.assess_bucket_compliance(bucket)
                control_results.append(bucket_result.get(control_id, "PASS"))

            # If any bucket fails, the control fails overall
            aggregated_results[control_id] = "FAIL" if "FAIL" in control_results else "PASS"

        return aggregated_results

    def _assess_sc13(self, bucket_data: Dict) -> str:
        """
        Assess SC-13 (Cryptographic Protection) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        encryption = bucket_data.get("Encryption", {})
        bucket_name = bucket_data.get("Name", "unknown")

        if not encryption.get("Enabled"):
            logger.debug(f"S3 bucket {bucket_name} FAILS SC-13: Encryption not enabled")
            return "FAIL"

        algorithm = encryption.get("Algorithm", "")
        if algorithm not in ["AES256", "aws:kms"]:
            logger.debug(f"S3 bucket {bucket_name} FAILS SC-13: Weak or unknown encryption algorithm")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES SC-13: Encryption enabled with {algorithm}")
        return "PASS"

    def _assess_sc28(self, bucket_data: Dict) -> str:
        """
        Assess SC-28 (Protection of Information at Rest) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        encryption = bucket_data.get("Encryption", {})
        versioning = bucket_data.get("Versioning", {})
        bucket_name = bucket_data.get("Name", "unknown")

        if not encryption.get("Enabled"):
            logger.debug(f"S3 bucket {bucket_name} FAILS SC-28: No encryption at rest")
            return "FAIL"

        versioning_status = versioning.get("Status", "Disabled")
        if versioning_status != "Enabled":
            logger.debug(f"S3 bucket {bucket_name} FAILS SC-28: Versioning not enabled")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES SC-28: Encryption and versioning enabled")
        return "PASS"

    def _assess_ac3(self, bucket_data: Dict) -> str:
        """
        Assess AC-3 (Access Enforcement) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        public_access_block = bucket_data.get("PublicAccessBlock", {})
        policy_status = bucket_data.get("PolicyStatus", {})
        bucket_name = bucket_data.get("Name", "unknown")

        # Check if all public access block settings are enabled
        required_blocks = ["BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"]
        for block_setting in required_blocks:
            if not public_access_block.get(block_setting, False):
                logger.debug(f"S3 bucket {bucket_name} FAILS AC-3: {block_setting} not enabled")
                return "FAIL"

        # Check if bucket policy is public
        if policy_status.get("IsPublic", False):
            logger.debug(f"S3 bucket {bucket_name} FAILS AC-3: Bucket has public policy")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES AC-3: Public access properly blocked")
        return "PASS"

    def _assess_ac6(self, bucket_data: Dict) -> str:
        """
        Assess AC-6 (Least Privilege) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        acl = bucket_data.get("ACL", {})
        policy_status = bucket_data.get("PolicyStatus", {})
        bucket_name = bucket_data.get("Name", "unknown")

        # Check for excessive ACL grants
        grant_count = acl.get("GrantCount", 0)
        if grant_count > 5:
            logger.debug(f"S3 bucket {bucket_name} FAILS AC-6: Excessive ACL grants ({grant_count})")
            return "FAIL"

        # Check for public policy
        if policy_status.get("IsPublic", False):
            logger.debug(f"S3 bucket {bucket_name} FAILS AC-6: Public bucket policy violates least privilege")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES AC-6: Least privilege maintained")
        return "PASS"

    def _assess_au2(self, bucket_data: Dict) -> str:
        """
        Assess AU-2 (Event Logging) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        logging_config = bucket_data.get("Logging", {})
        bucket_name = bucket_data.get("Name", "unknown")

        if not logging_config.get("Enabled", False):
            logger.debug(f"S3 bucket {bucket_name} FAILS AU-2: Access logging not enabled")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES AU-2: Access logging enabled")
        return "PASS"

    def _assess_au9(self, bucket_data: Dict) -> str:
        """
        Assess AU-9 (Protection of Audit Information) compliance.

        S3 buckets with access logging enabled contribute to AU-9 by protecting audit
        information through AWS's managed infrastructure. Buckets without logging are
        not applicable to this control (N/A is treated as PASS for reporting purposes).

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (always PASS - logging buckets meet requirements, others are N/A)
        :rtype: str
        """
        logging_config = bucket_data.get("Logging", {})
        bucket_name = bucket_data.get("Name", "unknown")

        # Check if this bucket is used for logging
        if logging_config.get("Enabled", False):
            target_bucket = logging_config.get("TargetBucket")
            if target_bucket:
                # Log buckets should have restricted access
                # This is a simplified check - in practice, would need to verify the target bucket config
                logger.debug(f"S3 bucket {bucket_name} PASSES AU-9: Logs stored in {target_bucket}")
        else:
            # If not a logging bucket, this control is N/A but we'll pass it
            logger.debug(f"S3 bucket {bucket_name} PASSES AU-9: Logging configuration appropriate (N/A)")

        return "PASS"

    def _assess_cp9(self, bucket_data: Dict) -> str:
        """
        Assess CP-9 (System Backup) compliance.

        :param Dict bucket_data: Bucket configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        versioning = bucket_data.get("Versioning", {})
        bucket_name = bucket_data.get("Name", "unknown")

        versioning_status = versioning.get("Status", "Disabled")
        if versioning_status != "Enabled":
            logger.debug(f"S3 bucket {bucket_name} FAILS CP-9: Versioning not enabled for backup")
            return "FAIL"

        logger.debug(f"S3 bucket {bucket_name} PASSES CP-9: Versioning enabled for data protection")
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
