#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS S3 Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.s3_control_mappings import (
    S3_CONTROL_MAPPINGS,
    S3ControlMapper,
)


class TestS3ControlMappings:
    """Test S3 control mappings constants."""

    def test_s3_control_mappings_exist(self):
        """Test that S3 control mappings dictionary exists and has content."""
        assert len(S3_CONTROL_MAPPINGS) > 0
        assert "SC-13" in S3_CONTROL_MAPPINGS
        assert "SC-28" in S3_CONTROL_MAPPINGS
        assert "AC-3" in S3_CONTROL_MAPPINGS
        assert "AC-6" in S3_CONTROL_MAPPINGS
        assert "AU-2" in S3_CONTROL_MAPPINGS
        assert "AU-9" in S3_CONTROL_MAPPINGS
        assert "CP-9" in S3_CONTROL_MAPPINGS

    def test_sc13_mapping_structure(self):
        """Test SC-13 mapping structure."""
        sc13 = S3_CONTROL_MAPPINGS["SC-13"]
        assert "name" in sc13
        assert "description" in sc13
        assert "checks" in sc13
        assert "encryption_at_rest" in sc13["checks"]
        assert "encryption_algorithm" in sc13["checks"]

    def test_sc28_mapping_structure(self):
        """Test SC-28 mapping structure."""
        sc28 = S3_CONTROL_MAPPINGS["SC-28"]
        assert "name" in sc28
        assert "description" in sc28
        assert "checks" in sc28
        assert "bucket_encryption" in sc28["checks"]
        assert "versioning_enabled" in sc28["checks"]

    def test_ac3_mapping_structure(self):
        """Test AC-3 mapping structure."""
        ac3 = S3_CONTROL_MAPPINGS["AC-3"]
        assert "name" in ac3
        assert "description" in ac3
        assert "checks" in ac3
        assert "public_access_blocked" in ac3["checks"]
        assert "bucket_policy" in ac3["checks"]


class TestS3ControlMapperInitialization:
    """Test S3ControlMapper initialization."""

    def test_init_with_nist_framework(self):
        """Test initialization with NIST framework."""
        mapper = S3ControlMapper(framework="NIST800-53R5")
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == S3_CONTROL_MAPPINGS

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = S3ControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == S3_CONTROL_MAPPINGS


class TestAssessBucketCompliance:
    """Test assess_bucket_compliance method."""

    def test_assess_compliant_bucket(self):
        """Test assessing a fully compliant bucket."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "compliant-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Enabled"},
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
            "ACL": {"GrantCount": 2},
            "Logging": {"Enabled": True, "TargetBucket": "logs-bucket"},
        }

        results = mapper.assess_bucket_compliance(bucket_data)

        assert results["SC-13"] == "PASS"
        assert results["SC-28"] == "PASS"
        assert results["AC-3"] == "PASS"
        assert results["AC-6"] == "PASS"
        assert results["AU-2"] == "PASS"
        assert results["AU-9"] == "PASS"
        assert results["CP-9"] == "PASS"

    def test_assess_bucket_without_encryption(self):
        """Test assessing bucket without encryption."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "unencrypted-bucket",
            "Encryption": {"Enabled": False},
            "Versioning": {"Status": "Enabled"},
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
            "ACL": {"GrantCount": 2},
            "Logging": {"Enabled": True},
        }

        results = mapper.assess_bucket_compliance(bucket_data)

        assert results["SC-13"] == "FAIL"
        assert results["SC-28"] == "FAIL"

    def test_assess_bucket_with_public_access(self):
        """Test assessing bucket with public access."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "public-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Enabled"},
            "PublicAccessBlock": {
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
            "PolicyStatus": {"IsPublic": True},
            "ACL": {"GrantCount": 2},
            "Logging": {"Enabled": False},
        }

        results = mapper.assess_bucket_compliance(bucket_data)

        assert results["AC-3"] == "FAIL"
        assert results["AC-6"] == "FAIL"
        assert results["AU-2"] == "FAIL"

    def test_assess_bucket_without_versioning(self):
        """Test assessing bucket without versioning."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "no-versioning-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Disabled"},
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
            "ACL": {"GrantCount": 2},
            "Logging": {"Enabled": True},
        }

        results = mapper.assess_bucket_compliance(bucket_data)

        assert results["SC-28"] == "FAIL"
        assert results["CP-9"] == "FAIL"


class TestAssessAllBucketsCompliance:
    """Test assess_all_buckets_compliance method."""

    def test_assess_all_compliant_buckets(self):
        """Test assessing all compliant buckets."""
        mapper = S3ControlMapper()
        buckets = [
            {
                "Name": "bucket1",
                "Encryption": {"Enabled": True, "Algorithm": "AES256"},
                "Versioning": {"Status": "Enabled"},
                "PublicAccessBlock": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
                "PolicyStatus": {"IsPublic": False},
                "ACL": {"GrantCount": 2},
                "Logging": {"Enabled": True},
            },
            {
                "Name": "bucket2",
                "Encryption": {"Enabled": True, "Algorithm": "aws:kms"},
                "Versioning": {"Status": "Enabled"},
                "PublicAccessBlock": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
                "PolicyStatus": {"IsPublic": False},
                "ACL": {"GrantCount": 1},
                "Logging": {"Enabled": True},
            },
        ]

        results = mapper.assess_all_buckets_compliance(buckets)

        assert all(result == "PASS" for result in results.values())

    def test_assess_buckets_with_one_non_compliant(self):
        """Test assessing buckets where one is non-compliant."""
        mapper = S3ControlMapper()
        buckets = [
            {
                "Name": "bucket1",
                "Encryption": {"Enabled": True, "Algorithm": "AES256"},
                "Versioning": {"Status": "Enabled"},
                "PublicAccessBlock": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
                "PolicyStatus": {"IsPublic": False},
                "ACL": {"GrantCount": 2},
                "Logging": {"Enabled": True},
            },
            {
                "Name": "bucket2",
                "Encryption": {"Enabled": False},
                "Versioning": {"Status": "Disabled"},
                "PublicAccessBlock": {
                    "BlockPublicAcls": False,
                    "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False,
                    "RestrictPublicBuckets": False,
                },
                "PolicyStatus": {"IsPublic": True},
                "ACL": {"GrantCount": 10},
                "Logging": {"Enabled": False},
            },
        ]

        results = mapper.assess_all_buckets_compliance(buckets)

        # All controls should fail because one bucket fails each control
        assert results["SC-13"] == "FAIL"
        assert results["SC-28"] == "FAIL"
        assert results["AC-3"] == "FAIL"
        assert results["AC-6"] == "FAIL"
        assert results["AU-2"] == "FAIL"
        assert results["CP-9"] == "FAIL"

    def test_assess_empty_bucket_list(self):
        """Test assessing empty bucket list."""
        mapper = S3ControlMapper()
        results = mapper.assess_all_buckets_compliance([])

        # Empty list should pass all controls
        assert all(result == "PASS" for result in results.values())


class TestAssessSC13:
    """Test _assess_sc13 method."""

    def test_bucket_with_aes256_encryption_passes(self):
        """Test bucket with AES256 encryption passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Encryption": {"Enabled": True, "Algorithm": "AES256"}}

        result = mapper._assess_sc13(bucket_data)
        assert result == "PASS"

    def test_bucket_with_kms_encryption_passes(self):
        """Test bucket with KMS encryption passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Encryption": {"Enabled": True, "Algorithm": "aws:kms"}}

        result = mapper._assess_sc13(bucket_data)
        assert result == "PASS"

    def test_bucket_without_encryption_fails(self):
        """Test bucket without encryption fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Encryption": {"Enabled": False}}

        result = mapper._assess_sc13(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_weak_algorithm_fails(self):
        """Test bucket with weak encryption algorithm fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Encryption": {"Enabled": True, "Algorithm": "WEAK_ALGO"}}

        result = mapper._assess_sc13(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_missing_encryption_key_fails(self):
        """Test bucket with missing Encryption key fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket"}

        result = mapper._assess_sc13(bucket_data)
        assert result == "FAIL"


class TestAssessSC28:
    """Test _assess_sc28 method."""

    def test_bucket_with_encryption_and_versioning_passes(self):
        """Test bucket with encryption and versioning passes."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Enabled"},
        }

        result = mapper._assess_sc28(bucket_data)
        assert result == "PASS"

    def test_bucket_without_encryption_fails(self):
        """Test bucket without encryption fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "Encryption": {"Enabled": False},
            "Versioning": {"Status": "Enabled"},
        }

        result = mapper._assess_sc28(bucket_data)
        assert result == "FAIL"

    def test_bucket_without_versioning_fails(self):
        """Test bucket without versioning fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Disabled"},
        }

        result = mapper._assess_sc28(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_suspended_versioning_fails(self):
        """Test bucket with suspended versioning fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "Encryption": {"Enabled": True, "Algorithm": "AES256"},
            "Versioning": {"Status": "Suspended"},
        }

        result = mapper._assess_sc28(bucket_data)
        assert result == "FAIL"


class TestAssessAC3:
    """Test _assess_ac3 method."""

    def test_bucket_with_all_public_access_blocks_passes(self):
        """Test bucket with all public access blocks enabled passes."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac3(bucket_data)
        assert result == "PASS"

    def test_bucket_without_block_public_acls_fails(self):
        """Test bucket without BlockPublicAcls fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "PublicAccessBlock": {
                "BlockPublicAcls": False,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac3(bucket_data)
        assert result == "FAIL"

    def test_bucket_without_ignore_public_acls_fails(self):
        """Test bucket without IgnorePublicAcls fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac3(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_public_policy_fails(self):
        """Test bucket with public policy fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": True},
        }

        result = mapper._assess_ac3(bucket_data)
        assert result == "FAIL"


class TestAssessAC6:
    """Test _assess_ac6 method."""

    def test_bucket_with_minimal_acl_grants_passes(self):
        """Test bucket with minimal ACL grants passes."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "ACL": {"GrantCount": 2},
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac6(bucket_data)
        assert result == "PASS"

    def test_bucket_with_excessive_acl_grants_fails(self):
        """Test bucket with excessive ACL grants fails."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "ACL": {"GrantCount": 10},
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac6(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_public_policy_fails(self):
        """Test bucket with public policy fails AC-6."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "ACL": {"GrantCount": 2},
            "PolicyStatus": {"IsPublic": True},
        }

        result = mapper._assess_ac6(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_zero_acl_grants_passes(self):
        """Test bucket with zero ACL grants passes."""
        mapper = S3ControlMapper()
        bucket_data = {
            "Name": "test-bucket",
            "ACL": {"GrantCount": 0},
            "PolicyStatus": {"IsPublic": False},
        }

        result = mapper._assess_ac6(bucket_data)
        assert result == "PASS"


class TestAssessAU2:
    """Test _assess_au2 method."""

    def test_bucket_with_logging_enabled_passes(self):
        """Test bucket with access logging enabled passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Logging": {"Enabled": True, "TargetBucket": "logs-bucket"}}

        result = mapper._assess_au2(bucket_data)
        assert result == "PASS"

    def test_bucket_without_logging_fails(self):
        """Test bucket without access logging fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Logging": {"Enabled": False}}

        result = mapper._assess_au2(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_missing_logging_key_fails(self):
        """Test bucket with missing Logging key fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket"}

        result = mapper._assess_au2(bucket_data)
        assert result == "FAIL"


class TestAssessAU9:
    """Test _assess_au9 method."""

    def test_bucket_with_logging_configuration_passes(self):
        """Test bucket with logging configuration passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Logging": {"Enabled": True, "TargetBucket": "logs-bucket"}}

        result = mapper._assess_au9(bucket_data)
        assert result == "PASS"

    def test_bucket_without_logging_passes(self):
        """Test bucket without logging passes (N/A case)."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Logging": {"Enabled": False}}

        result = mapper._assess_au9(bucket_data)
        assert result == "PASS"

    def test_bucket_with_empty_logging_passes(self):
        """Test bucket with empty logging configuration passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Logging": {}}

        result = mapper._assess_au9(bucket_data)
        assert result == "PASS"


class TestAssessCP9:
    """Test _assess_cp9 method."""

    def test_bucket_with_versioning_enabled_passes(self):
        """Test bucket with versioning enabled passes."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Versioning": {"Status": "Enabled"}}

        result = mapper._assess_cp9(bucket_data)
        assert result == "PASS"

    def test_bucket_without_versioning_fails(self):
        """Test bucket without versioning fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Versioning": {"Status": "Disabled"}}

        result = mapper._assess_cp9(bucket_data)
        assert result == "FAIL"

    def test_bucket_with_suspended_versioning_fails(self):
        """Test bucket with suspended versioning fails."""
        mapper = S3ControlMapper()
        bucket_data = {"Name": "test-bucket", "Versioning": {"Status": "Suspended"}}

        result = mapper._assess_cp9(bucket_data)
        assert result == "FAIL"


class TestGetControlDescription:
    """Test get_control_description method."""

    def test_get_sc13_description(self):
        """Test getting SC-13 description."""
        mapper = S3ControlMapper()
        description = mapper.get_control_description("SC-13")

        assert description is not None
        assert "Cryptographic Protection" in description

    def test_get_sc28_description(self):
        """Test getting SC-28 description."""
        mapper = S3ControlMapper()
        description = mapper.get_control_description("SC-28")

        assert description is not None
        assert "Protection of Information at Rest" in description

    def test_get_ac3_description(self):
        """Test getting AC-3 description."""
        mapper = S3ControlMapper()
        description = mapper.get_control_description("AC-3")

        assert description is not None
        assert "Access Enforcement" in description

    def test_get_unknown_control_description(self):
        """Test getting description for unknown control."""
        mapper = S3ControlMapper()
        description = mapper.get_control_description("UNKNOWN-1")

        assert description is None


class TestGetMappedControls:
    """Test get_mapped_controls method."""

    def test_get_mapped_controls(self):
        """Test getting all mapped controls."""
        mapper = S3ControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == 7
        assert "SC-13" in controls
        assert "SC-28" in controls
        assert "AC-3" in controls
        assert "AC-6" in controls
        assert "AU-2" in controls
        assert "AU-9" in controls
        assert "CP-9" in controls

    def test_controls_are_unique(self):
        """Test that returned controls are unique."""
        mapper = S3ControlMapper()
        controls = mapper.get_mapped_controls()

        assert len(controls) == len(set(controls))


class TestGetCheckDetails:
    """Test get_check_details method."""

    def test_get_sc13_check_details(self):
        """Test getting SC-13 check details."""
        mapper = S3ControlMapper()
        details = mapper.get_check_details("SC-13")

        assert details is not None
        assert "encryption_at_rest" in details
        assert "encryption_algorithm" in details
        assert details["encryption_at_rest"]["weight"] == 100

    def test_get_ac3_check_details(self):
        """Test getting AC-3 check details."""
        mapper = S3ControlMapper()
        details = mapper.get_check_details("AC-3")

        assert details is not None
        assert "public_access_blocked" in details
        assert "bucket_policy" in details

    def test_get_unknown_control_check_details(self):
        """Test getting check details for unknown control."""
        mapper = S3ControlMapper()
        details = mapper.get_check_details("UNKNOWN-1")

        assert details is None

    def test_check_details_structure(self):
        """Test check details have required structure."""
        mapper = S3ControlMapper()
        details = mapper.get_check_details("SC-13")

        for check_name, check_data in details.items():
            assert "weight" in check_data
            assert "pass_criteria" in check_data
            assert "fail_criteria" in check_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
