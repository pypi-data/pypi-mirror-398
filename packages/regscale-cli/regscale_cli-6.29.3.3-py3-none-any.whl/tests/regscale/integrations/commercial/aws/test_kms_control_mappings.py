#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS KMS Control Mappings."""

import json
import logging
import pytest

from regscale.integrations.commercial.aws.kms_control_mappings import (
    APPROVED_KEY_SPECS,
    ISO_27001_MAPPINGS,
    KMS_CONTROL_MAPPINGS,
    KMSControlMapper,
    NON_COMPLIANT_KEY_STATES,
)


class TestKMSControlMappings:
    """Test KMS control mappings constants."""

    def test_kms_control_mappings_exist(self):
        """Test that KMS control mappings dictionary exists and has content."""
        assert len(KMS_CONTROL_MAPPINGS) > 0
        assert "SC-12" in KMS_CONTROL_MAPPINGS
        assert "SC-13" in KMS_CONTROL_MAPPINGS
        assert "SC-28" in KMS_CONTROL_MAPPINGS

    def test_sc12_mapping_structure(self):
        """Test SC-12 mapping structure."""
        sc12 = KMS_CONTROL_MAPPINGS["SC-12"]
        assert "name" in sc12
        assert "description" in sc12
        assert "checks" in sc12
        assert "rotation_enabled" in sc12["checks"]
        assert "key_state" in sc12["checks"]
        assert "key_manager" in sc12["checks"]

    def test_sc13_mapping_structure(self):
        """Test SC-13 mapping structure."""
        sc13 = KMS_CONTROL_MAPPINGS["SC-13"]
        assert "name" in sc13
        assert "description" in sc13
        assert "checks" in sc13
        assert "key_spec" in sc13["checks"]
        assert "key_usage" in sc13["checks"]
        assert "key_origin" in sc13["checks"]

    def test_sc28_mapping_structure(self):
        """Test SC-28 mapping structure."""
        sc28 = KMS_CONTROL_MAPPINGS["SC-28"]
        assert "name" in sc28
        assert "description" in sc28
        assert "checks" in sc28
        assert "key_exists" in sc28["checks"]
        assert "multi_region" in sc28["checks"]
        assert "grants" in sc28["checks"]

    def test_iso_27001_mappings_exist(self):
        """Test ISO 27001 mappings exist."""
        assert len(ISO_27001_MAPPINGS) > 0
        assert "A.10.1.1" in ISO_27001_MAPPINGS
        assert "A.10.1.2" in ISO_27001_MAPPINGS

    def test_approved_key_specs(self):
        """Test approved key specifications list."""
        assert "SYMMETRIC_DEFAULT" in APPROVED_KEY_SPECS
        assert "RSA_2048" in APPROVED_KEY_SPECS
        assert "ECC_NIST_P256" in APPROVED_KEY_SPECS
        assert "HMAC_256" in APPROVED_KEY_SPECS

    def test_non_compliant_key_states(self):
        """Test non-compliant key states list."""
        assert "PendingDeletion" in NON_COMPLIANT_KEY_STATES
        assert "PendingImport" in NON_COMPLIANT_KEY_STATES
        assert "Unavailable" in NON_COMPLIANT_KEY_STATES


class TestKMSControlMapperInitialization:
    """Test KMSControlMapper initialization."""

    def test_init_with_nist_framework(self):
        """Test initialization with NIST framework."""
        mapper = KMSControlMapper(framework="NIST800-53R5")
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == KMS_CONTROL_MAPPINGS

    def test_init_with_iso_framework(self):
        """Test initialization with ISO framework."""
        mapper = KMSControlMapper(framework="ISO27001")
        assert mapper.framework == "ISO27001"
        assert mapper.mappings == ISO_27001_MAPPINGS

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = KMSControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == KMS_CONTROL_MAPPINGS


class TestAssessKeyCompliance:
    """Test assess_key_compliance method."""

    def test_assess_compliant_customer_key(self):
        """Test assessing a compliant customer-managed key."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-123",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Enabled",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "Enabled": True,
        }

        results = mapper.assess_key_compliance(key_data)

        assert results["SC-12"] == "PASS"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "PASS"

    def test_assess_aws_managed_key(self):
        """Test assessing AWS-managed key."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "aws-managed-key",
            "KeyManager": "AWS",
            "RotationEnabled": False,
            "KeyState": "Enabled",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "Enabled": True,
        }

        results = mapper.assess_key_compliance(key_data)

        # AWS-managed keys pass SC-12 even without explicit rotation
        assert results["SC-12"] == "PASS"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "PASS"

    def test_assess_key_without_rotation(self):
        """Test assessing customer key without rotation."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-456",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": False,
            "KeyState": "Enabled",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "Enabled": True,
        }

        results = mapper.assess_key_compliance(key_data)

        assert results["SC-12"] == "FAIL"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "PASS"

    def test_assess_key_pending_deletion(self):
        """Test assessing key in PendingDeletion state."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-789",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "PendingDeletion",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "Enabled": False,
        }

        results = mapper.assess_key_compliance(key_data)

        assert results["SC-12"] == "FAIL"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "FAIL"

    def test_assess_key_with_unapproved_spec(self):
        """Test assessing key with unapproved key spec."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-invalid",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Enabled",
            "KeySpec": "INVALID_SPEC",
            "Origin": "AWS_KMS",
            "Enabled": True,
        }

        results = mapper.assess_key_compliance(key_data)

        assert results["SC-12"] == "PASS"
        assert results["SC-13"] == "FAIL"
        assert results["SC-28"] == "PASS"

    def test_assess_key_with_external_origin(self):
        """Test assessing key with external origin (warning case)."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-external",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Enabled",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "EXTERNAL",
            "Enabled": True,
        }

        results = mapper.assess_key_compliance(key_data)

        # External origin should still pass but generate warning
        assert results["SC-12"] == "PASS"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "PASS"

    def test_assess_disabled_key(self):
        """Test assessing disabled key."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-disabled",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Disabled",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "Enabled": False,
        }

        results = mapper.assess_key_compliance(key_data)

        # Note: "Disabled" is not in NON_COMPLIANT_KEY_STATES, so SC-12 passes
        # but SC-28 checks the Enabled flag, so it fails
        assert results["SC-12"] == "PASS"
        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "FAIL"


class TestAssessSC12:
    """Test _assess_sc12 method."""

    def test_aws_managed_key_passes(self):
        """Test that AWS-managed keys automatically pass SC-12."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "aws-key",
            "KeyManager": "AWS",
            "RotationEnabled": False,
            "KeyState": "Enabled",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "PASS"

    def test_customer_key_with_rotation_passes(self):
        """Test customer-managed key with rotation passes."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "customer-key",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Enabled",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "PASS"

    def test_customer_key_without_rotation_fails(self):
        """Test customer-managed key without rotation fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "customer-key-no-rotation",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": False,
            "KeyState": "Enabled",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "FAIL"

    def test_key_in_pending_deletion_fails(self):
        """Test key in PendingDeletion state fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "key-pending-deletion",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "PendingDeletion",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "FAIL"

    def test_key_in_pending_import_fails(self):
        """Test key in PendingImport state fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "key-pending-import",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "PendingImport",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "FAIL"

    def test_key_unavailable_fails(self):
        """Test unavailable key fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "key-unavailable",
            "KeyManager": "CUSTOMER",
            "RotationEnabled": True,
            "KeyState": "Unavailable",
        }

        result = mapper._assess_sc12(key_data)
        assert result == "FAIL"


class TestAssessSC13:
    """Test _assess_sc13 method."""

    def test_symmetric_default_passes(self):
        """Test SYMMETRIC_DEFAULT key spec passes."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
        }

        result = mapper._assess_sc13(key_data)
        assert result == "PASS"

    def test_rsa_key_specs_pass(self):
        """Test RSA key specs pass."""
        mapper = KMSControlMapper()

        for key_spec in ["RSA_2048", "RSA_3072", "RSA_4096"]:
            key_data = {"KeyId": f"test-key-{key_spec}", "KeySpec": key_spec, "Origin": "AWS_KMS"}
            result = mapper._assess_sc13(key_data)
            assert result == "PASS"

    def test_ecc_key_specs_pass(self):
        """Test ECC key specs pass."""
        mapper = KMSControlMapper()

        for key_spec in ["ECC_NIST_P256", "ECC_NIST_P384", "ECC_NIST_P521", "ECC_SECG_P256K1"]:
            key_data = {"KeyId": f"test-key-{key_spec}", "KeySpec": key_spec, "Origin": "AWS_KMS"}
            result = mapper._assess_sc13(key_data)
            assert result == "PASS"

    def test_hmac_key_specs_pass(self):
        """Test HMAC key specs pass."""
        mapper = KMSControlMapper()

        for key_spec in ["HMAC_224", "HMAC_256", "HMAC_384", "HMAC_512"]:
            key_data = {"KeyId": f"test-key-{key_spec}", "KeySpec": key_spec, "Origin": "AWS_KMS"}
            result = mapper._assess_sc13(key_data)
            assert result == "PASS"

    def test_unapproved_key_spec_fails(self):
        """Test unapproved key spec fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-invalid",
            "KeySpec": "INVALID_ALGORITHM",
            "Origin": "AWS_KMS",
        }

        result = mapper._assess_sc13(key_data)
        assert result == "FAIL"

    def test_external_origin_passes_with_warning(self, caplog):
        """Test external origin passes but generates warning."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-external",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "EXTERNAL",
        }

        with caplog.at_level(logging.WARNING):
            result = mapper._assess_sc13(key_data)

        assert result == "PASS"
        assert any("EXTERNAL origin" in record.message for record in caplog.records)

    def test_cloudhsm_origin_passes(self):
        """Test AWS_CLOUDHSM origin passes."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-cloudhsm",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_CLOUDHSM",
        }

        result = mapper._assess_sc13(key_data)
        assert result == "PASS"


class TestAssessSC28:
    """Test _assess_sc28 method."""

    def test_enabled_key_passes(self):
        """Test enabled key passes."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-enabled",
            "KeyState": "Enabled",
            "Enabled": True,
        }

        result = mapper._assess_sc28(key_data)
        assert result == "PASS"

    def test_disabled_key_fails(self):
        """Test disabled key fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-disabled",
            "KeyState": "Disabled",
            "Enabled": False,
        }

        result = mapper._assess_sc28(key_data)
        assert result == "FAIL"

    def test_key_pending_deletion_fails(self):
        """Test key in PendingDeletion fails."""
        mapper = KMSControlMapper()
        key_data = {
            "KeyId": "test-key-pending-deletion",
            "KeyState": "PendingDeletion",
            "Enabled": False,
        }

        result = mapper._assess_sc28(key_data)
        assert result == "FAIL"

    def test_key_with_permissive_policy_passes_with_warning(self, caplog):
        """Test key with overly permissive policy passes but generates warning."""
        mapper = KMSControlMapper()
        policy = json.dumps({"Statement": [{"Effect": "Allow", "Principal": "*", "Action": "kms:*"}]})

        key_data = {"KeyId": "test-key-permissive", "KeyState": "Enabled", "Enabled": True, "Policy": policy}

        with caplog.at_level(logging.WARNING):
            result = mapper._assess_sc28(key_data)

        assert result == "PASS"
        assert any("overly permissive" in record.message for record in caplog.records)

    def test_key_with_safe_policy_passes(self):
        """Test key with safe policy passes."""
        mapper = KMSControlMapper()
        policy = json.dumps(
            {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                        "Action": "kms:*",
                    }
                ]
            }
        )

        key_data = {"KeyId": "test-key-safe", "KeyState": "Enabled", "Enabled": True, "Policy": policy}

        result = mapper._assess_sc28(key_data)
        assert result == "PASS"


class TestHasOverlyPermissivePolicy:
    """Test _has_overly_permissive_policy method."""

    def test_wildcard_principal_detected(self):
        """Test detection of wildcard principal."""
        mapper = KMSControlMapper()
        policy = json.dumps({"Statement": [{"Effect": "Allow", "Principal": "*", "Action": "kms:*"}]})

        result = mapper._has_overly_permissive_policy(policy)
        assert result is True

    def test_wildcard_aws_principal_detected(self):
        """Test detection of wildcard AWS principal."""
        mapper = KMSControlMapper()
        policy = json.dumps({"Statement": [{"Effect": "Allow", "Principal": {"AWS": "*"}, "Action": "kms:*"}]})

        result = mapper._has_overly_permissive_policy(policy)
        assert result is True

    def test_specific_principal_allowed(self):
        """Test specific principal is allowed."""
        mapper = KMSControlMapper()
        policy = json.dumps(
            {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                        "Action": "kms:*",
                    }
                ]
            }
        )

        result = mapper._has_overly_permissive_policy(policy)
        assert result is False

    def test_deny_effect_with_wildcard_allowed(self):
        """Test Deny effect with wildcard is allowed."""
        mapper = KMSControlMapper()
        policy = json.dumps({"Statement": [{"Effect": "Deny", "Principal": "*", "Action": "kms:*"}]})

        result = mapper._has_overly_permissive_policy(policy)
        assert result is False

    def test_invalid_json_returns_false(self):
        """Test invalid JSON returns False."""
        mapper = KMSControlMapper()
        policy = "invalid json"

        result = mapper._has_overly_permissive_policy(policy)
        assert result is False

    def test_missing_statement_returns_false(self):
        """Test policy without Statement returns False."""
        mapper = KMSControlMapper()
        policy = json.dumps({"Version": "2012-10-17"})

        result = mapper._has_overly_permissive_policy(policy)
        assert result is False


class TestGetControlDescription:
    """Test get_control_description method."""

    def test_get_sc12_description(self):
        """Test getting SC-12 description."""
        mapper = KMSControlMapper()
        description = mapper.get_control_description("SC-12")

        assert description is not None
        assert "Cryptographic Key Establishment and Management" in description

    def test_get_sc13_description(self):
        """Test getting SC-13 description."""
        mapper = KMSControlMapper()
        description = mapper.get_control_description("SC-13")

        assert description is not None
        assert "Cryptographic Protection" in description

    def test_get_sc28_description(self):
        """Test getting SC-28 description."""
        mapper = KMSControlMapper()
        description = mapper.get_control_description("SC-28")

        assert description is not None
        assert "Protection of Information at Rest" in description

    def test_get_unknown_control_description(self):
        """Test getting description for unknown control."""
        mapper = KMSControlMapper()
        description = mapper.get_control_description("UNKNOWN-1")

        assert description is None

    def test_get_iso_control_description(self):
        """Test getting ISO control description."""
        mapper = KMSControlMapper(framework="ISO27001")
        description = mapper.get_control_description("A.10.1.1")

        assert description is not None
        assert "cryptographic controls" in description.lower()


class TestGetMappedControls:
    """Test get_mapped_controls method."""

    def test_get_nist_controls(self):
        """Test getting NIST controls."""
        mapper = KMSControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) > 0
        assert "SC-12" in controls
        assert "SC-13" in controls
        assert "SC-28" in controls

    def test_get_iso_controls(self):
        """Test getting ISO controls."""
        mapper = KMSControlMapper(framework="ISO27001")
        controls = mapper.get_mapped_controls()

        assert len(controls) > 0
        assert "A.10.1.1" in controls
        assert "A.10.1.2" in controls

    def test_controls_are_unique(self):
        """Test that returned controls are unique."""
        mapper = KMSControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == len(set(controls))


class TestGetCheckDetails:
    """Test get_check_details method."""

    def test_get_sc12_check_details(self):
        """Test getting SC-12 check details."""
        mapper = KMSControlMapper()
        details = mapper.get_check_details("SC-12")

        assert details is not None
        assert "rotation_enabled" in details
        assert "key_state" in details
        assert "key_manager" in details
        assert details["rotation_enabled"]["weight"] == 100

    def test_get_sc13_check_details(self):
        """Test getting SC-13 check details."""
        mapper = KMSControlMapper()
        details = mapper.get_check_details("SC-13")

        assert details is not None
        assert "key_spec" in details
        assert "key_usage" in details
        assert "key_origin" in details

    def test_get_unknown_control_check_details(self):
        """Test getting check details for unknown control."""
        mapper = KMSControlMapper()
        details = mapper.get_check_details("UNKNOWN-1")

        assert details is None

    def test_check_details_structure(self):
        """Test check details have required structure."""
        mapper = KMSControlMapper()
        details = mapper.get_check_details("SC-12")

        for check_name, check_data in details.items():
            assert "weight" in check_data
            assert "pass_criteria" in check_data
            assert "fail_criteria" in check_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
