#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS IAM Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.iam_control_mappings import (
    ACCESS_KEY_MAX_AGE_DAYS,
    CREDENTIAL_UNUSED_DAYS,
    IAM_CONTROL_MAPPINGS,
    ISO_27001_MAPPINGS,
    PASSWORD_MAX_AGE_DAYS,
    STRONG_PASSWORD_POLICY,
    IAMControlMapper,
)


class TestIAMControlMapper:
    """Test IAMControlMapper class."""

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = IAMControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == IAM_CONTROL_MAPPINGS

    def test_init_iso27001_framework(self):
        """Test initialization with ISO27001 framework."""
        mapper = IAMControlMapper(framework="ISO27001")
        assert mapper.framework == "ISO27001"
        assert mapper.mappings == ISO_27001_MAPPINGS

    def test_init_nist_framework_explicit(self):
        """Test initialization with explicit NIST framework."""
        mapper = IAMControlMapper(framework="NIST800-53R5")
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == IAM_CONTROL_MAPPINGS

    def test_get_mapped_controls_nist(self):
        """Test getting list of mapped controls for NIST."""
        mapper = IAMControlMapper()
        controls = mapper.get_mapped_controls()
        assert isinstance(controls, list)
        assert len(controls) > 0
        assert "AC-2" in controls
        assert "AC-6" in controls
        assert "IA-2" in controls
        assert "IA-5" in controls
        assert "AC-3" in controls

    def test_get_mapped_controls_iso(self):
        """Test getting list of mapped controls for ISO27001."""
        mapper = IAMControlMapper(framework="ISO27001")
        controls = mapper.get_mapped_controls()
        assert isinstance(controls, list)
        assert len(controls) > 0
        assert "A.9.2.1" in controls
        assert "A.9.2.2" in controls
        assert "A.9.4.3" in controls

    def test_get_control_description_valid(self):
        """Test getting control description for valid control."""
        mapper = IAMControlMapper()
        description = mapper.get_control_description("AC-2")
        assert description is not None
        assert "Account Management" in description
        assert "Manage system accounts" in description

    def test_get_control_description_invalid(self):
        """Test getting control description for invalid control."""
        mapper = IAMControlMapper()
        description = mapper.get_control_description("INVALID-CONTROL")
        assert description is None

    def test_get_check_details_valid(self):
        """Test getting check details for valid control."""
        mapper = IAMControlMapper()
        checks = mapper.get_check_details("AC-2")
        assert checks is not None
        assert isinstance(checks, dict)
        assert "user_mfa" in checks
        assert "inactive_users" in checks
        assert "root_account_usage" in checks
        assert checks["user_mfa"]["weight"] == 100

    def test_get_check_details_invalid(self):
        """Test getting check details for invalid control."""
        mapper = IAMControlMapper()
        checks = mapper.get_check_details("INVALID-CONTROL")
        assert checks is None


class TestAssessIAMCompliance:
    """Test assess_iam_compliance method."""

    def test_assess_compliance_all_pass(self):
        """Test assessment when all controls pass."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True, "AttachedPolicies": [], "InlinePolicies": []}],
            "account_summary": {
                "AccountMFAEnabled": True,
                "AccountAccessKeysPresent": 0,
            },
            "password_policy": {
                "MinimumPasswordLength": 14,
                "RequireSymbols": True,
                "RequireNumbers": True,
                "RequireUppercaseCharacters": True,
                "RequireLowercaseCharacters": True,
                "MaxPasswordAge": 90,
                "PasswordReusePrevention": 24,
            },
            "roles": [
                {
                    "RoleName": "test-role",
                    "AssumeRolePolicyDocument": {"Statement": [{"Principal": {"Service": "ec2.amazonaws.com"}}]},
                }
            ],
        }
        results = mapper.assess_iam_compliance(iam_data)
        assert results["AC-2"] == "PASS"
        assert results["AC-6"] == "PASS"
        assert results["IA-2"] == "PASS"
        assert results["IA-5"] == "PASS"
        assert results["AC-3"] == "PASS"

    def test_assess_compliance_non_nist_framework(self):
        """Test assessment with non-NIST framework returns empty results."""
        mapper = IAMControlMapper(framework="ISO27001")
        iam_data = {"users": []}
        results = mapper.assess_iam_compliance(iam_data)
        assert results == {}


class TestAssessAC2:
    """Test _assess_ac2 (Account Management) compliance."""

    def test_ac2_pass_all_requirements_met(self):
        """Test AC-2 passes when all requirements met."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True}],
            "account_summary": {
                "AccountMFAEnabled": True,
                "AccountAccessKeysPresent": 0,
            },
        }
        result = mapper._assess_ac2(iam_data)
        assert result == "PASS"

    def test_ac2_fail_user_without_mfa(self):
        """Test AC-2 fails when user doesn't have MFA."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": False}],
            "account_summary": {
                "AccountMFAEnabled": True,
                "AccountAccessKeysPresent": 0,
            },
        }
        result = mapper._assess_ac2(iam_data)
        assert result == "FAIL"

    def test_ac2_fail_root_without_mfa(self):
        """Test AC-2 fails when root account doesn't have MFA."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True}],
            "account_summary": {
                "AccountMFAEnabled": False,
                "AccountAccessKeysPresent": 0,
            },
        }
        result = mapper._assess_ac2(iam_data)
        assert result == "FAIL"

    def test_ac2_fail_root_has_access_keys(self):
        """Test AC-2 fails when root account has access keys."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True}],
            "account_summary": {
                "AccountMFAEnabled": True,
                "AccountAccessKeysPresent": 2,
            },
        }
        result = mapper._assess_ac2(iam_data)
        assert result == "FAIL"

    def test_ac2_pass_multiple_users_with_mfa(self):
        """Test AC-2 passes with multiple users all having MFA."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {"UserName": "user1", "MfaEnabled": True},
                {"UserName": "user2", "MfaEnabled": True},
            ],
            "account_summary": {
                "AccountMFAEnabled": True,
                "AccountAccessKeysPresent": 0,
            },
        }
        result = mapper._assess_ac2(iam_data)
        assert result == "PASS"


class TestAssessAC6:
    """Test _assess_ac6 (Least Privilege) compliance."""

    def test_ac6_pass_no_admin_users(self):
        """Test AC-6 passes when no users have admin access."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AttachedPolicies": [{"PolicyName": "ReadOnlyAccess"}],
                    "InlinePolicies": [],
                }
            ]
        }
        result = mapper._assess_ac6(iam_data)
        assert result == "PASS"

    def test_ac6_fail_user_with_administrator_access(self):
        """Test AC-6 fails when user has AdministratorAccess policy."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "admin-user",
                    "AttachedPolicies": [{"PolicyName": "AdministratorAccess"}],
                    "InlinePolicies": [],
                }
            ]
        }
        result = mapper._assess_ac6(iam_data)
        assert result == "FAIL"

    def test_ac6_fail_inline_policy_full_admin(self):
        """Test AC-6 fails when user has inline policy with full admin permissions."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AttachedPolicies": [],
                    "InlinePolicies": [
                        {
                            "PolicyName": "custom-admin",
                            "PolicyDocument": {
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Action": "*",
                                        "Resource": "*",
                                    }
                                ]
                            },
                        }
                    ],
                }
            ]
        }
        result = mapper._assess_ac6(iam_data)
        assert result == "FAIL"

    def test_ac6_pass_inline_policy_restricted(self):
        """Test AC-6 passes with restricted inline policies."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AttachedPolicies": [],
                    "InlinePolicies": [
                        {
                            "PolicyName": "s3-read-only",
                            "PolicyDocument": {
                                "Statement": [
                                    {
                                        "Effect": "Allow",
                                        "Action": "s3:GetObject",
                                        "Resource": "arn:aws:s3:::bucket/*",
                                    }
                                ]
                            },
                        }
                    ],
                }
            ]
        }
        result = mapper._assess_ac6(iam_data)
        assert result == "PASS"


class TestAssessIA2:
    """Test _assess_ia2 (Identification and Authentication) compliance."""

    def test_ia2_pass_strong_policy_and_mfa(self):
        """Test IA-2 passes with strong password policy and MFA."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True}],
            "password_policy": {
                "MinimumPasswordLength": 14,
                "RequireSymbols": True,
                "RequireNumbers": True,
                "RequireUppercaseCharacters": True,
                "RequireLowercaseCharacters": True,
                "MaxPasswordAge": 90,
            },
        }
        result = mapper._assess_ia2(iam_data)
        assert result == "PASS"

    def test_ia2_fail_weak_password_policy(self):
        """Test IA-2 fails with weak password policy."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": True}],
            "password_policy": {
                "MinimumPasswordLength": 8,
                "RequireSymbols": False,
                "RequireNumbers": False,
                "RequireUppercaseCharacters": False,
                "RequireLowercaseCharacters": False,
                "MaxPasswordAge": 180,
            },
        }
        result = mapper._assess_ia2(iam_data)
        assert result == "FAIL"

    def test_ia2_fail_no_mfa(self):
        """Test IA-2 fails when users don't have MFA."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [{"UserName": "user1", "MfaEnabled": False}],
            "password_policy": {
                "MinimumPasswordLength": 14,
                "RequireSymbols": True,
                "RequireNumbers": True,
                "RequireUppercaseCharacters": True,
                "RequireLowercaseCharacters": True,
                "MaxPasswordAge": 90,
            },
        }
        result = mapper._assess_ia2(iam_data)
        assert result == "FAIL"


class TestAssessIA5:
    """Test _assess_ia5 (Authenticator Management) compliance."""

    def test_ia5_pass_all_keys_rotated(self):
        """Test IA-5 passes when all access keys are rotated."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AccessKeys": [{"AccessKeyId": "key1", "AgeDays": 30}],
                    "PasswordLastUsed": {"DaysSinceUsed": 10},
                }
            ]
        }
        result = mapper._assess_ia5(iam_data)
        assert result == "PASS"

    def test_ia5_fail_old_access_key(self):
        """Test IA-5 fails when access key is too old."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AccessKeys": [{"AccessKeyId": "key1", "AgeDays": 120}],
                    "PasswordLastUsed": {"DaysSinceUsed": 10},
                }
            ]
        }
        result = mapper._assess_ia5(iam_data)
        assert result == "FAIL"

    def test_ia5_fail_unused_credentials(self):
        """Test IA-5 fails when credentials are unused for too long."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AccessKeys": [],
                    "PasswordLastUsed": {"DaysSinceUsed": 120},
                }
            ]
        }
        result = mapper._assess_ia5(iam_data)
        assert result == "FAIL"

    def test_ia5_pass_no_access_keys(self):
        """Test IA-5 passes when user has no access keys."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AccessKeys": [],
                    "PasswordLastUsed": {"DaysSinceUsed": 10},
                }
            ]
        }
        result = mapper._assess_ia5(iam_data)
        assert result == "PASS"

    def test_ia5_pass_no_password_last_used(self):
        """Test IA-5 passes when PasswordLastUsed is None."""
        mapper = IAMControlMapper()
        iam_data = {
            "users": [
                {
                    "UserName": "user1",
                    "AccessKeys": [{"AccessKeyId": "key1", "AgeDays": 30}],
                    "PasswordLastUsed": None,
                }
            ]
        }
        result = mapper._assess_ia5(iam_data)
        assert result == "PASS"


class TestAssessAC3:
    """Test _assess_ac3 (Access Enforcement) compliance."""

    def test_ac3_pass_restrictive_trust_policies(self):
        """Test AC-3 passes when roles have restrictive trust policies."""
        mapper = IAMControlMapper()
        iam_data = {
            "roles": [
                {
                    "RoleName": "test-role",
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Principal": {"Service": "ec2.amazonaws.com"},
                            }
                        ]
                    },
                }
            ]
        }
        result = mapper._assess_ac3(iam_data)
        assert result == "PASS"

    def test_ac3_fail_wildcard_principal(self):
        """Test AC-3 fails when role has wildcard principal."""
        mapper = IAMControlMapper()
        iam_data = {
            "roles": [
                {
                    "RoleName": "public-role",
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Principal": "*",
                            }
                        ]
                    },
                }
            ]
        }
        result = mapper._assess_ac3(iam_data)
        assert result == "FAIL"

    def test_ac3_fail_wildcard_aws_principal(self):
        """Test AC-3 fails when role has wildcard AWS principal."""
        mapper = IAMControlMapper()
        iam_data = {
            "roles": [
                {
                    "RoleName": "overly-permissive-role",
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Principal": {"AWS": "*"},
                            }
                        ]
                    },
                }
            ]
        }
        result = mapper._assess_ac3(iam_data)
        assert result == "FAIL"

    def test_ac3_pass_empty_roles_list(self):
        """Test AC-3 passes when no roles exist."""
        mapper = IAMControlMapper()
        iam_data = {"roles": []}
        result = mapper._assess_ac3(iam_data)
        assert result == "PASS"


class TestHelperMethods:
    """Test helper methods."""

    def test_has_full_admin_permissions_true(self):
        """Test detection of full admin permissions."""
        mapper = IAMControlMapper()
        policy_doc = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "*",
                    "Resource": "*",
                }
            ]
        }
        assert mapper._has_full_admin_permissions(policy_doc) is True

    def test_has_full_admin_permissions_star_star_true(self):
        """Test detection of *:* admin permissions."""
        mapper = IAMControlMapper()
        policy_doc = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "*:*",
                    "Resource": "*",
                }
            ]
        }
        assert mapper._has_full_admin_permissions(policy_doc) is True

    def test_has_full_admin_permissions_false_limited_action(self):
        """Test no false positive for limited action."""
        mapper = IAMControlMapper()
        policy_doc = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "s3:GetObject",
                    "Resource": "*",
                }
            ]
        }
        assert mapper._has_full_admin_permissions(policy_doc) is False

    def test_has_full_admin_permissions_false_limited_resource(self):
        """Test no false positive for limited resource."""
        mapper = IAMControlMapper()
        policy_doc = {
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:*"],
                    "Resource": "arn:aws:s3:::bucket/*",
                }
            ]
        }
        assert mapper._has_full_admin_permissions(policy_doc) is False

    def test_has_permissive_trust_policy_wildcard(self):
        """Test detection of wildcard trust policy."""
        mapper = IAMControlMapper()
        trust_policy = {"Statement": [{"Principal": "*"}]}
        assert mapper._has_permissive_trust_policy(trust_policy) is True

    def test_has_permissive_trust_policy_aws_wildcard(self):
        """Test detection of AWS wildcard trust policy."""
        mapper = IAMControlMapper()
        trust_policy = {"Statement": [{"Principal": {"AWS": "*"}}]}
        assert mapper._has_permissive_trust_policy(trust_policy) is True

    def test_has_permissive_trust_policy_false(self):
        """Test no false positive for restricted trust policy."""
        mapper = IAMControlMapper()
        trust_policy = {"Statement": [{"Principal": {"Service": "ec2.amazonaws.com"}}]}
        assert mapper._has_permissive_trust_policy(trust_policy) is False

    def test_is_strong_password_policy_true(self):
        """Test strong password policy detection."""
        mapper = IAMControlMapper()
        policy = {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "MaxPasswordAge": 90,
        }
        assert mapper._is_strong_password_policy(policy) is True

    def test_is_strong_password_policy_false_short_length(self):
        """Test weak password policy with short length."""
        mapper = IAMControlMapper()
        policy = {
            "MinimumPasswordLength": 8,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "MaxPasswordAge": 90,
        }
        assert mapper._is_strong_password_policy(policy) is False

    def test_is_strong_password_policy_false_no_complexity(self):
        """Test weak password policy without complexity requirements."""
        mapper = IAMControlMapper()
        policy = {
            "MinimumPasswordLength": 14,
            "RequireSymbols": False,
            "RequireNumbers": False,
            "RequireUppercaseCharacters": False,
            "RequireLowercaseCharacters": False,
            "MaxPasswordAge": 90,
        }
        assert mapper._is_strong_password_policy(policy) is False

    def test_is_strong_password_policy_false_long_max_age(self):
        """Test weak password policy with long max age."""
        mapper = IAMControlMapper()
        policy = {
            "MinimumPasswordLength": 14,
            "RequireSymbols": True,
            "RequireNumbers": True,
            "RequireUppercaseCharacters": True,
            "RequireLowercaseCharacters": True,
            "MaxPasswordAge": 180,
        }
        assert mapper._is_strong_password_policy(policy) is False

    def test_is_strong_password_policy_false_empty(self):
        """Test empty password policy is not strong."""
        mapper = IAMControlMapper()
        assert mapper._is_strong_password_policy({}) is False

    def test_is_strong_password_policy_false_none(self):
        """Test None password policy is not strong."""
        mapper = IAMControlMapper()
        assert mapper._is_strong_password_policy(None) is False


class TestIAMControlMappings:
    """Test IAM_CONTROL_MAPPINGS structure."""

    def test_mappings_exist(self):
        """Test that mappings dictionary exists and has content."""
        assert len(IAM_CONTROL_MAPPINGS) > 0

    def test_ac2_mapping_structure(self):
        """Test AC-2 mapping structure."""
        assert "AC-2" in IAM_CONTROL_MAPPINGS
        ac2 = IAM_CONTROL_MAPPINGS["AC-2"]
        assert "name" in ac2
        assert "description" in ac2
        assert "checks" in ac2
        assert "user_mfa" in ac2["checks"]
        assert "inactive_users" in ac2["checks"]
        assert "root_account_usage" in ac2["checks"]

    def test_ac6_mapping_structure(self):
        """Test AC-6 mapping structure."""
        assert "AC-6" in IAM_CONTROL_MAPPINGS
        ac6 = IAM_CONTROL_MAPPINGS["AC-6"]
        assert len(ac6["checks"]) >= 2
        assert "admin_policies" in ac6["checks"]
        assert "inline_policies" in ac6["checks"]

    def test_all_controls_have_required_fields(self):
        """Test all control mappings have required fields."""
        for control_id, control_data in IAM_CONTROL_MAPPINGS.items():
            assert "name" in control_data
            assert "description" in control_data
            assert "checks" in control_data
            assert isinstance(control_data["checks"], dict)
            for check_name, check_data in control_data["checks"].items():
                assert "weight" in check_data
                assert "pass_criteria" in check_data
                assert "fail_criteria" in check_data


class TestISO27001Mappings:
    """Test ISO_27001_MAPPINGS structure."""

    def test_iso_mappings_exist(self):
        """Test that ISO mappings exist."""
        assert len(ISO_27001_MAPPINGS) > 0

    def test_iso_mapping_structure(self):
        """Test ISO mapping structure."""
        for control_id, control_data in ISO_27001_MAPPINGS.items():
            assert "name" in control_data
            assert "iam_attributes" in control_data
            assert isinstance(control_data["iam_attributes"], list)


class TestConstants:
    """Test constant values."""

    def test_strong_password_policy_constant(self):
        """Test STRONG_PASSWORD_POLICY constant."""
        assert STRONG_PASSWORD_POLICY["MinimumPasswordLength"] == 14
        assert STRONG_PASSWORD_POLICY["RequireSymbols"] is True
        assert STRONG_PASSWORD_POLICY["RequireNumbers"] is True
        assert STRONG_PASSWORD_POLICY["RequireUppercaseCharacters"] is True
        assert STRONG_PASSWORD_POLICY["RequireLowercaseCharacters"] is True
        assert STRONG_PASSWORD_POLICY["MaxPasswordAge"] == 90
        assert STRONG_PASSWORD_POLICY["PasswordReusePrevention"] == 24

    def test_age_threshold_constants(self):
        """Test age threshold constants."""
        assert ACCESS_KEY_MAX_AGE_DAYS == 90
        assert PASSWORD_MAX_AGE_DAYS == 90
        assert CREDENTIAL_UNUSED_DAYS == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
