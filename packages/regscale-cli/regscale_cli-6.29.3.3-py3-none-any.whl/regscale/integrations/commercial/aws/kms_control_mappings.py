#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS KMS Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS KMS
KMS_CONTROL_MAPPINGS = {
    "SC-12": {
        "name": "Cryptographic Key Establishment and Management",
        "description": "Establish and manage cryptographic keys for cryptography employed in organizational systems",
        "checks": {
            "rotation_enabled": {
                "weight": 100,
                "pass_criteria": "Customer-managed key with automatic rotation enabled",
                "fail_criteria": "Customer-managed key with automatic rotation disabled",
            },
            "key_state": {
                "weight": 80,
                "pass_criteria": "Key is in Enabled state",
                "fail_criteria": "Key is PendingDeletion or Disabled",
            },
            "key_manager": {
                "weight": 40,
                "pass_criteria": "Customer-managed key (not AWS-managed)",
                "fail_criteria": "AWS-managed key (limited rotation control)",
            },
        },
    },
    "SC-13": {
        "name": "Cryptographic Protection",
        "description": "Implement FIPS-validated or NSA-approved cryptography",
        "checks": {
            "key_spec": {
                "weight": 100,
                "pass_criteria": "Using approved algorithms (SYMMETRIC_DEFAULT, RSA_*, ECC_*)",
                "fail_criteria": "Using deprecated or non-approved algorithms",
            },
            "key_usage": {
                "weight": 80,
                "pass_criteria": "Key usage appropriate for workload (ENCRYPT_DECRYPT, SIGN_VERIFY)",
                "fail_criteria": "Key usage mismatch or GENERATE_VERIFY_MAC without proper controls",
            },
            "key_origin": {
                "weight": 60,
                "pass_criteria": "Key generated in AWS_KMS (FIPS 140-2 Level 2+)",
                "fail_criteria": "External key material without documented FIPS compliance",
            },
        },
    },
    "SC-28": {
        "name": "Protection of Information at Rest",
        "description": "Protect information at rest using cryptographic mechanisms",
        "checks": {
            "key_exists": {
                "weight": 100,
                "pass_criteria": "KMS key exists and is enabled for data-at-rest encryption",
                "fail_criteria": "No KMS key configured for data-at-rest protection",
            },
            "multi_region": {
                "weight": 60,
                "pass_criteria": "Multi-region key for disaster recovery scenarios",
                "fail_criteria": "Single-region key may impact availability",
            },
            "grants": {
                "weight": 40,
                "pass_criteria": "Grants follow least-privilege principle",
                "fail_criteria": "Excessive grants or overly permissive policies",
            },
        },
    },
}

# ISO 27001 A.10.1 Control Mappings
ISO_27001_MAPPINGS = {
    "A.10.1.1": {
        "name": "Policy on the use of cryptographic controls",
        "kms_attributes": ["rotation_enabled", "key_policy", "key_manager"],
    },
    "A.10.1.2": {
        "name": "Key management",
        "kms_attributes": ["rotation_enabled", "key_state", "creation_date", "deletion_date"],
    },
}

# Approved KMS key specifications (FIPS-validated algorithms)
APPROVED_KEY_SPECS = [
    "SYMMETRIC_DEFAULT",  # AES-256-GCM
    "RSA_2048",
    "RSA_3072",
    "RSA_4096",
    "ECC_NIST_P256",
    "ECC_NIST_P384",
    "ECC_NIST_P521",
    "ECC_SECG_P256K1",
    "HMAC_224",
    "HMAC_256",
    "HMAC_384",
    "HMAC_512",
    "SM2",  # China State Cryptography Administration standard
]

# Key states that indicate compliance issues
NON_COMPLIANT_KEY_STATES = [
    "PendingDeletion",
    "PendingImport",
    "Unavailable",
]


class KMSControlMapper:
    """Map AWS KMS key attributes to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize KMS control mapper.

        :param str framework: Compliance framework (NIST800-53R5 or ISO27001)
        """
        self.framework = framework
        self.mappings = KMS_CONTROL_MAPPINGS if framework == "NIST800-53R5" else ISO_27001_MAPPINGS

    def assess_key_compliance(self, key_data: Dict) -> Dict[str, str]:
        """
        Assess KMS key compliance against all mapped controls.

        :param Dict key_data: KMS key metadata and attributes
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["SC-12"] = self._assess_sc12(key_data)
            results["SC-13"] = self._assess_sc13(key_data)
            results["SC-28"] = self._assess_sc28(key_data)

        return results

    def _assess_sc12(self, key_data: Dict) -> str:
        """
        Assess SC-12 (Cryptographic Key Management) compliance.

        :param Dict key_data: KMS key metadata
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        # Critical: Rotation must be enabled for customer-managed keys
        key_manager = key_data.get("KeyManager", "CUSTOMER")
        rotation_enabled = key_data.get("RotationEnabled", False)
        key_state = key_data.get("KeyState", "Unknown")

        # AWS-managed keys have automatic rotation, so they pass
        if key_manager == "AWS":
            logger.debug(f"Key {key_data.get('KeyId')} is AWS-managed, auto-passing SC-12")
            return "PASS"

        # Customer-managed keys MUST have rotation enabled
        if not rotation_enabled:
            logger.debug(f"Key {key_data.get('KeyId')} FAILS SC-12: rotation disabled")
            return "FAIL"

        # Key must be in enabled state
        if key_state in NON_COMPLIANT_KEY_STATES:
            logger.debug(f"Key {key_data.get('KeyId')} FAILS SC-12: key state is {key_state}")
            return "FAIL"

        logger.debug(f"Key {key_data.get('KeyId')} PASSES SC-12: rotation enabled, state {key_state}")
        return "PASS"

    def _assess_sc13(self, key_data: Dict) -> str:
        """
        Assess SC-13 (Cryptographic Protection) compliance.

        :param Dict key_data: KMS key metadata
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        key_spec = key_data.get("KeySpec", "SYMMETRIC_DEFAULT")
        key_origin = key_data.get("Origin", "AWS_KMS")

        # Check for approved key specifications
        if key_spec not in APPROVED_KEY_SPECS:
            logger.debug(f"Key {key_data.get('KeyId')} FAILS SC-13: unapproved key spec {key_spec}")
            return "FAIL"

        # Prefer AWS_KMS origin for FIPS 140-2 Level 2+ compliance
        # EXTERNAL origin requires additional documentation
        if key_origin == "EXTERNAL":
            logger.warning(f"Key {key_data.get('KeyId')} uses EXTERNAL origin - verify FIPS compliance documentation")

        # AWS_CLOUDHSM origin is acceptable (FIPS 140-2 Level 3)
        # AWS_KMS origin is acceptable (FIPS 140-2 Level 2)
        logger.debug(f"Key {key_data.get('KeyId')} PASSES SC-13: spec {key_spec}, origin {key_origin}")
        return "PASS"

    def _assess_sc28(self, key_data: Dict) -> str:
        """
        Assess SC-28 (Protection of Information at Rest) compliance.

        :param Dict key_data: KMS key metadata
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        key_state = key_data.get("KeyState", "Unknown")
        enabled = key_data.get("Enabled", False)

        # Key must be enabled and available for data-at-rest encryption
        if key_state in NON_COMPLIANT_KEY_STATES:
            logger.debug(f"Key {key_data.get('KeyId')} FAILS SC-28: key state is {key_state}")
            return "FAIL"

        if not enabled:
            logger.debug(f"Key {key_data.get('KeyId')} FAILS SC-28: key is disabled")
            return "FAIL"

        # Check for overly permissive policies (simplified check)
        policy = key_data.get("Policy")
        if policy and self._has_overly_permissive_policy(policy):
            logger.warning(f"Key {key_data.get('KeyId')} has overly permissive policy - review required")

        logger.debug(f"Key {key_data.get('KeyId')} PASSES SC-28: enabled and available")
        return "PASS"

    def _has_overly_permissive_policy(self, policy: str) -> bool:
        """
        Check if key policy is overly permissive.

        :param str policy: Key policy JSON string
        :return: True if policy has security concerns
        :rtype: bool
        """
        import json

        try:
            policy_dict = json.loads(policy)
            statements = policy_dict.get("Statement", [])

            for statement in statements:
                # Check for wildcard principals
                principal = statement.get("Principal", {})
                if principal == "*" or (isinstance(principal, dict) and principal.get("AWS") == "*"):
                    effect = statement.get("Effect", "Deny")
                    if effect == "Allow":
                        return True

        except (json.JSONDecodeError, AttributeError):
            logger.debug("Could not parse key policy for security analysis")

        return False

    def get_control_description(self, control_id: str) -> Optional[str]:
        """
        Get human-readable description for a control.

        :param str control_id: Control identifier (e.g., SC-12)
        :return: Control description or None
        :rtype: Optional[str]
        """
        control_data = self.mappings.get(control_id)
        if control_data:
            return f"{control_data.get('name')}: {control_data.get('description', '')}"
        return None

    def get_mapped_controls(self) -> List[str]:
        """
        Get list of all control IDs mapped for this framework.

        :return: List of control IDs
        :rtype: List[str]
        """
        return list(self.mappings.keys())

    def get_check_details(self, control_id: str) -> Optional[Dict]:
        """
        Get detailed check criteria for a control.

        :param str control_id: Control identifier
        :return: Dictionary of check details or None
        :rtype: Optional[Dict]
        """
        control_data = self.mappings.get(control_id)
        if control_data:
            return control_data.get("checks", {})
        return None
