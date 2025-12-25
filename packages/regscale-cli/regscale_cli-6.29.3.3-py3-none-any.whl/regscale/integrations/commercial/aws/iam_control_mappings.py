#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS IAM Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS IAM
IAM_CONTROL_MAPPINGS = {
    "AC-2": {
        "name": "Account Management",
        "description": "Manage system accounts including creation, enabling, modification, and removal",
        "checks": {
            "user_mfa": {
                "weight": 100,
                "pass_criteria": "All IAM users have MFA enabled",
                "fail_criteria": "IAM users without MFA enabled",
            },
            "inactive_users": {
                "weight": 90,
                "pass_criteria": "No inactive users (password age > 90 days)",
                "fail_criteria": "Users with credentials unused for extended period",
            },
            "root_account_usage": {
                "weight": 100,
                "pass_criteria": "Root account has MFA and no access keys",
                "fail_criteria": "Root account without MFA or with active access keys",
            },
        },
    },
    "AC-6": {
        "name": "Least Privilege",
        "description": "Employ the principle of least privilege",
        "checks": {
            "admin_policies": {
                "weight": 100,
                "pass_criteria": "No users with direct AdministratorAccess policy attachment",
                "fail_criteria": "Users with full admin (*:*) permissions",
            },
            "inline_policies": {
                "weight": 80,
                "pass_criteria": "Minimal use of inline policies, prefer managed policies",
                "fail_criteria": "Excessive inline policies indicating poor policy management",
            },
        },
    },
    "IA-2": {
        "name": "Identification and Authentication (Organizational Users)",
        "description": "Uniquely identify and authenticate organizational users",
        "checks": {
            "password_policy": {
                "weight": 100,
                "pass_criteria": "Strong password policy enforced (length, complexity, rotation)",
                "fail_criteria": "Weak or no password policy",
            },
            "mfa_enforcement": {
                "weight": 100,
                "pass_criteria": "MFA required for all users",
                "fail_criteria": "Users without MFA",
            },
        },
    },
    "IA-5": {
        "name": "Authenticator Management",
        "description": "Manage system authenticators",
        "checks": {
            "access_key_rotation": {
                "weight": 100,
                "pass_criteria": "Access keys rotated within 90 days",
                "fail_criteria": "Access keys older than 90 days",
            },
            "unused_credentials": {
                "weight": 90,
                "pass_criteria": "No unused credentials (password or access keys)",
                "fail_criteria": "Credentials not used in 90+ days",
            },
        },
    },
    "AC-3": {
        "name": "Access Enforcement",
        "description": "Enforce approved authorizations for logical access",
        "checks": {
            "role_trust_policies": {
                "weight": 100,
                "pass_criteria": "IAM roles have restrictive trust policies",
                "fail_criteria": "Roles with overly permissive trust relationships",
            },
            "group_based_access": {
                "weight": 80,
                "pass_criteria": "Users assigned to groups rather than direct policy attachments",
                "fail_criteria": "Users with direct policy attachments instead of group membership",
            },
        },
    },
}

# ISO 27001 Control Mappings
ISO_27001_MAPPINGS = {
    "A.9.2.1": {
        "name": "User registration and de-registration",
        "iam_attributes": ["users", "user_status", "last_activity"],
    },
    "A.9.2.2": {
        "name": "User access provisioning",
        "iam_attributes": ["policies", "groups", "roles"],
    },
    "A.9.4.3": {
        "name": "Password management system",
        "iam_attributes": ["password_policy", "mfa_status"],
    },
}

# Password policy requirements (strong policy)
STRONG_PASSWORD_POLICY = {
    "MinimumPasswordLength": 14,
    "RequireSymbols": True,
    "RequireNumbers": True,
    "RequireUppercaseCharacters": True,
    "RequireLowercaseCharacters": True,
    "MaxPasswordAge": 90,
    "PasswordReusePrevention": 24,
}

# Age thresholds (in days)
ACCESS_KEY_MAX_AGE_DAYS = 90
PASSWORD_MAX_AGE_DAYS = 90
CREDENTIAL_UNUSED_DAYS = 90


class IAMControlMapper:
    """Map AWS IAM resources to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize IAM control mapper.

        :param str framework: Compliance framework (NIST800-53R5 or ISO27001)
        """
        self.framework = framework
        self.mappings = IAM_CONTROL_MAPPINGS if framework == "NIST800-53R5" else ISO_27001_MAPPINGS

    def assess_iam_compliance(self, iam_data: Dict) -> Dict[str, str]:
        """
        Assess AWS IAM compliance against all mapped controls.

        :param Dict iam_data: IAM resources and configuration
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["AC-2"] = self._assess_ac2(iam_data)
            results["AC-6"] = self._assess_ac6(iam_data)
            results["IA-2"] = self._assess_ia2(iam_data)
            results["IA-5"] = self._assess_ia5(iam_data)
            results["AC-3"] = self._assess_ac3(iam_data)

        return results

    def _assess_ac2(self, iam_data: Dict) -> str:
        """
        Assess AC-2 (Account Management) compliance.

        :param Dict iam_data: IAM data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        users = iam_data.get("users", [])
        account_summary = iam_data.get("account_summary", {})

        # Check MFA for users
        users_without_mfa = [u for u in users if not u.get("MfaEnabled", False)]
        if users_without_mfa:
            logger.debug(f"IAM FAILS AC-2: {len(users_without_mfa)} users without MFA")
            return "FAIL"

        # Check root account
        root_mfa = account_summary.get("AccountMFAEnabled", False)
        if not root_mfa:
            logger.debug("IAM FAILS AC-2: Root account does not have MFA enabled")
            return "FAIL"

        # Check for root access keys
        root_access_keys = account_summary.get("AccountAccessKeysPresent", 0)
        if root_access_keys > 0:
            logger.debug("IAM FAILS AC-2: Root account has active access keys")
            return "FAIL"

        logger.debug("IAM PASSES AC-2: All users have MFA, root account secured")
        return "PASS"

    def _assess_ac6(self, iam_data: Dict) -> str:
        """
        Assess AC-6 (Least Privilege) compliance.

        :param Dict iam_data: IAM data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        users = iam_data.get("users", [])

        # Check for users with AdministratorAccess
        users_with_admin = []
        for user in users:
            attached_policies = user.get("AttachedPolicies", [])
            inline_policies = user.get("InlinePolicies", [])

            # Check attached policies
            if any("AdministratorAccess" in p.get("PolicyName", "") for p in attached_policies):
                users_with_admin.append(user.get("UserName"))

            # Check inline policies for broad permissions
            for policy in inline_policies:
                policy_doc = policy.get("PolicyDocument", {})
                if self._has_full_admin_permissions(policy_doc):
                    users_with_admin.append(user.get("UserName"))

        if users_with_admin:
            logger.debug(f"IAM FAILS AC-6: {len(users_with_admin)} users with administrator access")
            return "FAIL"

        logger.debug("IAM PASSES AC-6: No users with direct administrator access")
        return "PASS"

    def _assess_ia2(self, iam_data: Dict) -> str:
        """
        Assess IA-2 (Identification and Authentication) compliance.

        :param Dict iam_data: IAM data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        users = iam_data.get("users", [])
        password_policy = iam_data.get("password_policy", {})

        # Check password policy strength
        if not self._is_strong_password_policy(password_policy):
            logger.debug("IAM FAILS IA-2: Weak password policy")
            return "FAIL"

        # Check MFA enforcement
        users_without_mfa = [u for u in users if not u.get("MfaEnabled", False)]
        if users_without_mfa:
            logger.debug(f"IAM FAILS IA-2: {len(users_without_mfa)} users without MFA")
            return "FAIL"

        logger.debug("IAM PASSES IA-2: Strong password policy and MFA enforced")
        return "PASS"

    def _assess_ia5(self, iam_data: Dict) -> str:
        """
        Assess IA-5 (Authenticator Management) compliance.

        :param Dict iam_data: IAM data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        users = iam_data.get("users", [])

        # Check access key age
        old_access_keys = []
        unused_credentials = []

        for user in users:
            access_keys = user.get("AccessKeys", [])
            for key in access_keys:
                age_days = key.get("AgeDays", 0)
                if age_days > ACCESS_KEY_MAX_AGE_DAYS:
                    old_access_keys.append(key.get("AccessKeyId"))

            # Check credential usage
            password_last_used = user.get("PasswordLastUsed")
            if password_last_used and password_last_used.get("DaysSinceUsed", 0) > CREDENTIAL_UNUSED_DAYS:
                unused_credentials.append(user.get("UserName"))

        if old_access_keys:
            logger.debug(
                f"IAM FAILS IA-5: {len(old_access_keys)} access keys older than {ACCESS_KEY_MAX_AGE_DAYS} days"
            )
            return "FAIL"

        if unused_credentials:
            logger.debug(f"IAM FAILS IA-5: {len(unused_credentials)} users with unused credentials")
            return "FAIL"

        logger.debug("IAM PASSES IA-5: All access keys rotated, no unused credentials")
        return "PASS"

    def _assess_ac3(self, iam_data: Dict) -> str:
        """
        Assess AC-3 (Access Enforcement) compliance.

        :param Dict iam_data: IAM data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        roles = iam_data.get("roles", [])

        # Check for overly permissive role trust policies
        permissive_roles = []
        for role in roles:
            trust_policy = role.get("AssumeRolePolicyDocument", {})
            if self._has_permissive_trust_policy(trust_policy):
                permissive_roles.append(role.get("RoleName"))

        if permissive_roles:
            logger.debug(f"IAM FAILS AC-3: {len(permissive_roles)} roles with overly permissive trust policies")
            return "FAIL"

        logger.debug("IAM PASSES AC-3: All roles have restrictive trust policies")
        return "PASS"

    def _has_full_admin_permissions(self, policy_doc: Dict) -> bool:
        """Check if policy grants full admin permissions."""
        statements = policy_doc.get("Statement", [])
        for statement in statements:
            if statement.get("Effect") == "Allow":
                actions = statement.get("Action", [])
                resources = statement.get("Resource", [])
                if ("*" in actions or "*:*" in actions) and ("*" in resources):
                    return True
        return False

    def _has_permissive_trust_policy(self, trust_policy: Dict) -> bool:
        """Check if trust policy is overly permissive."""
        statements = trust_policy.get("Statement", [])
        for statement in statements:
            principal = statement.get("Principal", {})
            if principal == "*" or (isinstance(principal, dict) and principal.get("AWS") == "*"):
                return True
        return False

    def _is_strong_password_policy(self, policy: Dict) -> bool:
        """Check if password policy meets strong requirements."""
        if not policy:
            return False

        checks = [
            policy.get("MinimumPasswordLength", 0) >= STRONG_PASSWORD_POLICY["MinimumPasswordLength"],
            policy.get("RequireSymbols", False),
            policy.get("RequireNumbers", False),
            policy.get("RequireUppercaseCharacters", False),
            policy.get("RequireLowercaseCharacters", False),
            policy.get("MaxPasswordAge", 0) <= STRONG_PASSWORD_POLICY["MaxPasswordAge"],
        ]

        return all(checks)

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
