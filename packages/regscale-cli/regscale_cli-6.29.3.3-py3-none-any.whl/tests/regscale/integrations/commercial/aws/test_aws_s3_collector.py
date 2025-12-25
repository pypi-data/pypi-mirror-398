#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS S3 Collector in RegScale CLI."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.s3 import S3Collector


class TestS3Collector:
    """Test suite for AWS S3 Collector."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AWS session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def s3_collector(self, mock_session):
        """Create an S3Collector instance for testing."""
        return S3Collector(session=mock_session, region="us-east-1", account_id="123456789012")

    @pytest.fixture
    def s3_collector_no_account(self, mock_session):
        """Create an S3Collector instance without account_id."""
        return S3Collector(session=mock_session, region="us-west-2")

    # Test 1: Initialization with account_id
    def test_initialization_with_account_id(self, s3_collector):
        """Should initialize S3Collector with account_id."""
        assert s3_collector.region == "us-east-1"
        assert s3_collector.account_id == "123456789012"

    # Test 2: Initialization without account_id
    def test_initialization_without_account_id(self, s3_collector_no_account):
        """Should initialize S3Collector without account_id."""
        assert s3_collector_no_account.region == "us-west-2"
        assert s3_collector_no_account.account_id is None

    # Test 3: Successful collection of buckets with full details
    def test_collect_buckets_successfully(self, s3_collector, mock_s3_client):
        """Should successfully collect S3 buckets with full details."""
        # Mock the _get_client method
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        # Mock list_buckets response
        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "test-bucket-1", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "test-bucket-2", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
            ]
        }

        # Mock bucket location (both in us-east-1)
        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1 returns None
            {"LocationConstraint": None},
        ]

        # Mock encryption configuration
        mock_s3_client.get_bucket_encryption.side_effect = [
            {
                "ServerSideEncryptionConfiguration": {
                    "Rules": [
                        {
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "AES256",
                            }
                        }
                    ]
                }
            },
            {
                "ServerSideEncryptionConfiguration": {
                    "Rules": [
                        {
                            "ApplyServerSideEncryptionByDefault": {
                                "SSEAlgorithm": "aws:kms",
                                "KMSMasterKeyID": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                            }
                        }
                    ]
                }
            },
        ]

        # Mock versioning configuration
        mock_s3_client.get_bucket_versioning.side_effect = [
            {"Status": "Enabled", "MFADelete": "Disabled"},
            {"Status": "Disabled", "MFADelete": "Disabled"},
        ]

        # Mock public access block
        mock_s3_client.get_public_access_block.side_effect = [
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                }
            },
            {
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": False,
                    "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False,
                    "RestrictPublicBuckets": False,
                }
            },
        ]

        # Mock bucket policy status
        mock_s3_client.get_bucket_policy_status.side_effect = [
            {"PolicyStatus": {"IsPublic": False}},
            {"PolicyStatus": {"IsPublic": True}},
        ]

        # Mock bucket ACL
        mock_s3_client.get_bucket_acl.side_effect = [
            {
                "Owner": {"DisplayName": "owner1", "ID": "owner-id-1"},
                "Grants": [{"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"}],
            },
            {
                "Owner": {"DisplayName": "owner2", "ID": "owner-id-2"},
                "Grants": [
                    {"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"},
                    {"Grantee": {"Type": "Group"}, "Permission": "READ"},
                ],
            },
        ]

        # Mock bucket tagging
        mock_s3_client.get_bucket_tagging.side_effect = [
            {"TagSet": [{"Key": "Environment", "Value": "Production"}, {"Key": "Owner", "Value": "TeamA"}]},
            {"TagSet": [{"Key": "Environment", "Value": "Development"}]},
        ]

        # Mock bucket logging
        mock_s3_client.get_bucket_logging.side_effect = [
            {"LoggingEnabled": {"TargetBucket": "log-bucket", "TargetPrefix": "logs/"}},
            {},
        ]

        result = s3_collector.collect()

        assert "Buckets" in result
        assert len(result["Buckets"]) == 2

        # Verify first bucket
        bucket1 = result["Buckets"][0]
        assert bucket1["Name"] == "test-bucket-1"
        assert bucket1["Region"] == "us-east-1"
        assert bucket1["Location"] == "us-east-1"
        assert bucket1["Encryption"]["Enabled"] is True
        assert bucket1["Encryption"]["Algorithm"] == "AES256"
        assert bucket1["Versioning"]["Status"] == "Enabled"
        assert bucket1["PublicAccessBlock"]["BlockPublicAcls"] is True
        assert bucket1["PolicyStatus"]["IsPublic"] is False
        assert bucket1["ACL"]["GrantCount"] == 1
        assert len(bucket1["Tags"]) == 2
        assert bucket1["Logging"]["Enabled"] is True

        # Verify second bucket
        bucket2 = result["Buckets"][1]
        assert bucket2["Name"] == "test-bucket-2"
        assert bucket2["Encryption"]["Algorithm"] == "aws:kms"
        assert bucket2["PublicAccessBlock"]["BlockPublicAcls"] is False
        assert bucket2["PolicyStatus"]["IsPublic"] is True
        assert bucket2["ACL"]["GrantCount"] == 2
        assert len(bucket2["Tags"]) == 1
        assert bucket2["Logging"]["Enabled"] is False

    # Test 4: Bucket location retrieval
    def test_get_bucket_location_us_east_1(self, s3_collector, mock_s3_client):
        """Should return us-east-1 when LocationConstraint is None."""
        mock_s3_client.get_bucket_location.return_value = {"LocationConstraint": None}

        location = s3_collector._get_bucket_location(mock_s3_client, "test-bucket")

        assert location == "us-east-1"

    def test_get_bucket_location_other_region(self, s3_collector, mock_s3_client):
        """Should return correct region when LocationConstraint is set."""
        mock_s3_client.get_bucket_location.return_value = {"LocationConstraint": "us-west-2"}

        location = s3_collector._get_bucket_location(mock_s3_client, "test-bucket")

        assert location == "us-west-2"

    def test_get_bucket_location_error(self, s3_collector, mock_s3_client):
        """Should return unknown when ClientError occurs."""
        mock_s3_client.get_bucket_location.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_location"
        )

        location = s3_collector._get_bucket_location(mock_s3_client, "test-bucket")

        assert location == "unknown"

    # Test 5: Bucket encryption configuration (enabled)
    def test_get_bucket_encryption_aes256(self, s3_collector, mock_s3_client):
        """Should return encryption configuration with AES256 algorithm."""
        mock_s3_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            }
        }

        encryption = s3_collector._get_bucket_encryption(mock_s3_client, "test-bucket")

        assert encryption["Enabled"] is True
        assert encryption["Algorithm"] == "AES256"
        assert encryption["KMSMasterKeyID"] is None

    def test_get_bucket_encryption_kms(self, s3_collector, mock_s3_client):
        """Should return encryption configuration with KMS algorithm."""
        kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
        mock_s3_client.get_bucket_encryption.return_value = {
            "ServerSideEncryptionConfiguration": {
                "Rules": [
                    {
                        "ApplyServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms",
                            "KMSMasterKeyID": kms_key_id,
                        }
                    }
                ]
            }
        }

        encryption = s3_collector._get_bucket_encryption(mock_s3_client, "test-bucket")

        assert encryption["Enabled"] is True
        assert encryption["Algorithm"] == "aws:kms"
        assert encryption["KMSMasterKeyID"] == kms_key_id

    # Test 6: Bucket encryption configuration (disabled)
    def test_get_bucket_encryption_not_found(self, s3_collector, mock_s3_client):
        """Should return Enabled False when ServerSideEncryptionConfigurationNotFoundError occurs."""
        mock_s3_client.get_bucket_encryption.side_effect = ClientError(
            {"Error": {"Code": "ServerSideEncryptionConfigurationNotFoundError", "Message": "Not found"}},
            "get_bucket_encryption",
        )

        encryption = s3_collector._get_bucket_encryption(mock_s3_client, "test-bucket")

        assert encryption["Enabled"] is False

    def test_get_bucket_encryption_empty_rules(self, s3_collector, mock_s3_client):
        """Should return Enabled False when encryption rules are empty."""
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}

        encryption = s3_collector._get_bucket_encryption(mock_s3_client, "test-bucket")

        assert encryption["Enabled"] is False

    def test_get_bucket_encryption_other_error(self, s3_collector, mock_s3_client):
        """Should return empty dict for other ClientError."""
        mock_s3_client.get_bucket_encryption.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_encryption"
        )

        encryption = s3_collector._get_bucket_encryption(mock_s3_client, "test-bucket")

        assert encryption == {}

    # Test 7: Bucket versioning configuration
    def test_get_bucket_versioning_enabled(self, s3_collector, mock_s3_client):
        """Should return versioning status as Enabled."""
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Enabled", "MFADelete": "Enabled"}

        versioning = s3_collector._get_bucket_versioning(mock_s3_client, "test-bucket")

        assert versioning["Status"] == "Enabled"
        assert versioning["MFADelete"] == "Enabled"

    def test_get_bucket_versioning_disabled(self, s3_collector, mock_s3_client):
        """Should return versioning status as Disabled when not set."""
        mock_s3_client.get_bucket_versioning.return_value = {}

        versioning = s3_collector._get_bucket_versioning(mock_s3_client, "test-bucket")

        assert versioning["Status"] == "Disabled"
        assert versioning["MFADelete"] == "Disabled"

    def test_get_bucket_versioning_error(self, s3_collector, mock_s3_client):
        """Should return empty dict when ClientError occurs."""
        mock_s3_client.get_bucket_versioning.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_versioning"
        )

        versioning = s3_collector._get_bucket_versioning(mock_s3_client, "test-bucket")

        assert versioning == {}

    # Test 8: Public access block configuration (enabled)
    def test_get_public_access_block_enabled(self, s3_collector, mock_s3_client):
        """Should return public access block configuration when enabled."""
        mock_s3_client.get_public_access_block.return_value = {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }
        }

        public_access_block = s3_collector._get_public_access_block(mock_s3_client, "test-bucket")

        assert public_access_block["BlockPublicAcls"] is True
        assert public_access_block["IgnorePublicAcls"] is True
        assert public_access_block["BlockPublicPolicy"] is True
        assert public_access_block["RestrictPublicBuckets"] is True

    # Test 9: Public access block configuration (disabled)
    def test_get_public_access_block_disabled(self, s3_collector, mock_s3_client):
        """Should return all False when NoSuchPublicAccessBlockConfiguration occurs."""
        mock_s3_client.get_public_access_block.side_effect = ClientError(
            {"Error": {"Code": "NoSuchPublicAccessBlockConfiguration", "Message": "Not found"}},
            "get_public_access_block",
        )

        public_access_block = s3_collector._get_public_access_block(mock_s3_client, "test-bucket")

        assert public_access_block["BlockPublicAcls"] is False
        assert public_access_block["IgnorePublicAcls"] is False
        assert public_access_block["BlockPublicPolicy"] is False
        assert public_access_block["RestrictPublicBuckets"] is False

    def test_get_public_access_block_other_error(self, s3_collector, mock_s3_client):
        """Should return empty dict for other ClientError."""
        mock_s3_client.get_public_access_block.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_public_access_block"
        )

        public_access_block = s3_collector._get_public_access_block(mock_s3_client, "test-bucket")

        assert public_access_block == {}

    # Test 10: Bucket policy status (public and private)
    def test_get_bucket_policy_status_public(self, s3_collector, mock_s3_client):
        """Should return IsPublic True when bucket policy is public."""
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": True}}

        policy_status = s3_collector._get_bucket_policy_status(mock_s3_client, "test-bucket")

        assert policy_status["IsPublic"] is True

    def test_get_bucket_policy_status_private(self, s3_collector, mock_s3_client):
        """Should return IsPublic False when bucket policy is private."""
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}

        policy_status = s3_collector._get_bucket_policy_status(mock_s3_client, "test-bucket")

        assert policy_status["IsPublic"] is False

    def test_get_bucket_policy_status_no_policy(self, s3_collector, mock_s3_client):
        """Should return IsPublic False when NoSuchBucketPolicy error occurs."""
        mock_s3_client.get_bucket_policy_status.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucketPolicy", "Message": "Not found"}}, "get_bucket_policy_status"
        )

        policy_status = s3_collector._get_bucket_policy_status(mock_s3_client, "test-bucket")

        assert policy_status["IsPublic"] is False

    def test_get_bucket_policy_status_other_error(self, s3_collector, mock_s3_client):
        """Should return empty dict for other ClientError."""
        mock_s3_client.get_bucket_policy_status.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_policy_status"
        )

        policy_status = s3_collector._get_bucket_policy_status(mock_s3_client, "test-bucket")

        assert policy_status == {}

    # Test 11: Bucket ACL retrieval
    def test_get_bucket_acl_single_grant(self, s3_collector, mock_s3_client):
        """Should return ACL information with single grant."""
        mock_s3_client.get_bucket_acl.return_value = {
            "Owner": {"DisplayName": "owner1", "ID": "owner-id-1"},
            "Grants": [{"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"}],
        }

        acl = s3_collector._get_bucket_acl(mock_s3_client, "test-bucket")

        assert acl["Owner"]["DisplayName"] == "owner1"
        assert acl["Owner"]["ID"] == "owner-id-1"
        assert acl["GrantCount"] == 1

    def test_get_bucket_acl_multiple_grants(self, s3_collector, mock_s3_client):
        """Should return ACL information with multiple grants."""
        mock_s3_client.get_bucket_acl.return_value = {
            "Owner": {"DisplayName": "owner1", "ID": "owner-id-1"},
            "Grants": [
                {"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"},
                {"Grantee": {"Type": "Group"}, "Permission": "READ"},
                {"Grantee": {"Type": "Group"}, "Permission": "WRITE"},
            ],
        }

        acl = s3_collector._get_bucket_acl(mock_s3_client, "test-bucket")

        assert acl["GrantCount"] == 3

    def test_get_bucket_acl_error(self, s3_collector, mock_s3_client):
        """Should return empty dict when ClientError occurs."""
        mock_s3_client.get_bucket_acl.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_acl"
        )

        acl = s3_collector._get_bucket_acl(mock_s3_client, "test-bucket")

        assert acl == {}

    # Test 12: Bucket tagging (with tags)
    def test_get_bucket_tagging_with_tags(self, s3_collector, mock_s3_client):
        """Should return bucket tags when tags exist."""
        mock_s3_client.get_bucket_tagging.return_value = {
            "TagSet": [
                {"Key": "Environment", "Value": "Production"},
                {"Key": "Owner", "Value": "TeamA"},
                {"Key": "CostCenter", "Value": "Engineering"},
            ]
        }

        tags = s3_collector._get_bucket_tagging(mock_s3_client, "test-bucket")

        assert len(tags) == 3
        assert tags[0]["Key"] == "Environment"
        assert tags[0]["Value"] == "Production"
        assert tags[1]["Key"] == "Owner"
        assert tags[1]["Value"] == "TeamA"

    # Test 13: Bucket tagging (without tags)
    def test_get_bucket_tagging_no_tags(self, s3_collector, mock_s3_client):
        """Should return empty list when NoSuchTagSet error occurs."""
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"
        )

        tags = s3_collector._get_bucket_tagging(mock_s3_client, "test-bucket")

        assert tags == []

    def test_get_bucket_tagging_other_error(self, s3_collector, mock_s3_client):
        """Should return empty list for other ClientError."""
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_tagging"
        )

        tags = s3_collector._get_bucket_tagging(mock_s3_client, "test-bucket")

        assert tags == []

    # Test 14: Bucket logging configuration
    def test_get_bucket_logging_enabled(self, s3_collector, mock_s3_client):
        """Should return logging configuration when logging is enabled."""
        mock_s3_client.get_bucket_logging.return_value = {
            "LoggingEnabled": {
                "TargetBucket": "log-bucket",
                "TargetPrefix": "logs/",
            }
        }

        logging_config = s3_collector._get_bucket_logging(mock_s3_client, "test-bucket")

        assert logging_config["Enabled"] is True
        assert logging_config["TargetBucket"] == "log-bucket"
        assert logging_config["TargetPrefix"] == "logs/"

    def test_get_bucket_logging_disabled(self, s3_collector, mock_s3_client):
        """Should return Enabled False when logging is not configured."""
        mock_s3_client.get_bucket_logging.return_value = {}

        logging_config = s3_collector._get_bucket_logging(mock_s3_client, "test-bucket")

        assert logging_config["Enabled"] is False

    def test_get_bucket_logging_error(self, s3_collector, mock_s3_client):
        """Should return empty dict when ClientError occurs."""
        mock_s3_client.get_bucket_logging.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_logging"
        )

        logging_config = s3_collector._get_bucket_logging(mock_s3_client, "test-bucket")

        assert logging_config == {}

    # Test 15: Region filtering
    def test_region_filtering_excludes_other_regions(self, s3_collector, mock_s3_client):
        """Should only include buckets in the target region."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket-us-east-1", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "bucket-us-west-2", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
                {"Name": "bucket-eu-west-1", "CreationDate": datetime(2023, 3, 1, 12, 0, 0)},
            ]
        }

        # First bucket is in us-east-1 (target region)
        # Second bucket is in us-west-2
        # Third bucket is in eu-west-1
        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1
            {"LocationConstraint": "us-west-2"},
            {"LocationConstraint": "eu-west-1"},
        ]

        # Mock other required calls for the bucket in target region
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Disabled"}
        mock_s3_client.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": {}}
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        mock_s3_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"
        )
        mock_s3_client.get_bucket_logging.return_value = {}

        result = s3_collector.collect()

        # Only the bucket in us-east-1 should be included
        assert len(result["Buckets"]) == 1
        assert result["Buckets"][0]["Name"] == "bucket-us-east-1"
        assert result["Buckets"][0]["Region"] == "us-east-1"

    def test_region_filtering_verifies_region_tag(self, s3_collector, mock_s3_client):
        """Should verify Region tag is set for all buckets in target region."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "test-bucket-1", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "test-bucket-2", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
            ]
        }

        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1
            {"LocationConstraint": None},  # us-east-1
        ]

        # Mock other required calls
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Disabled"}
        mock_s3_client.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": {}}
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        mock_s3_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
        mock_s3_client.get_bucket_tagging.side_effect = [
            ClientError({"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"),
            ClientError({"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"),
        ]
        mock_s3_client.get_bucket_logging.return_value = {}

        result = s3_collector.collect()

        # Verify all buckets have Region tag
        assert len(result["Buckets"]) == 2
        for bucket in result["Buckets"]:
            assert "Region" in bucket
            assert bucket["Region"] == "us-east-1"

    # Test 16: Error handling - AccessDenied during list_buckets
    def test_collect_handles_access_denied_list_buckets(self, s3_collector, mock_s3_client):
        """Should handle AccessDenied error when listing buckets."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "list_buckets"
        )

        with patch("regscale.integrations.commercial.aws.inventory.resources.s3.logger") as mock_logger:
            result = s3_collector.collect()

            assert result["Buckets"] == []
            mock_logger.warning.assert_called_once()

    # Test 17: Error handling - NoSuchBucket during bucket details retrieval
    def test_list_buckets_handles_nosuchbucket_error(self, s3_collector, mock_s3_client):
        """Should skip bucket when NoSuchBucket error occurs during details retrieval."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket-exists", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "bucket-deleted", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
            ]
        }

        # First bucket succeeds, second bucket throws NoSuchBucket
        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1
            ClientError({"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}}, "get_bucket_location"),
        ]

        # Mock other required calls for the first bucket
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Disabled"}
        mock_s3_client.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": {}}
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        mock_s3_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"
        )
        mock_s3_client.get_bucket_logging.return_value = {}

        result = s3_collector.collect()

        # Only the first bucket should be included
        assert len(result["Buckets"]) == 1
        assert result["Buckets"][0]["Name"] == "bucket-exists"

    # Test 18: Error handling - AccessDenied during bucket details retrieval
    def test_list_buckets_handles_access_denied_details(self, s3_collector, mock_s3_client):
        """Should skip bucket when AccessDenied error occurs during details retrieval."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket-accessible", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "bucket-restricted", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
            ]
        }

        # First bucket succeeds, second bucket throws AccessDenied
        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1
            ClientError({"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "get_bucket_location"),
        ]

        # Mock other required calls for the first bucket
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Disabled"}
        mock_s3_client.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": {}}
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        mock_s3_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"
        )
        mock_s3_client.get_bucket_logging.return_value = {}

        result = s3_collector.collect()

        # Only the first bucket should be included
        assert len(result["Buckets"]) == 1
        assert result["Buckets"][0]["Name"] == "bucket-accessible"

    # Test 19: Error handling - Unexpected error during collection
    def test_collect_handles_unexpected_error(self, s3_collector, mock_s3_client):
        """Should handle unexpected errors during collection."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.side_effect = Exception("Unexpected error")

        with patch("regscale.integrations.commercial.aws.inventory.resources.s3.logger") as mock_logger:
            result = s3_collector.collect()

            assert result["Buckets"] == []
            mock_logger.error.assert_called_once()

    # Test 20: Collect with ClientError during main operation
    def test_collect_handles_client_error(self, s3_collector, mock_s3_client):
        """Should handle ClientError during main collection operation."""
        s3_collector._get_client = MagicMock(
            side_effect=ClientError({"Error": {"Code": "UnauthorizedOperation", "Message": "Unauthorized"}}, "client")
        )

        result = s3_collector.collect()

        # The error should be handled by _handle_error method
        assert result["Buckets"] == []

    # Test 21: Error handling for other exceptions during bucket details retrieval
    def test_list_buckets_handles_other_errors(self, s3_collector, mock_s3_client):
        """Should skip bucket when non-AccessDenied/NoSuchBucket error occurs during details retrieval."""
        s3_collector._get_client = MagicMock(return_value=mock_s3_client)

        mock_s3_client.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket-ok", "CreationDate": datetime(2023, 1, 1, 12, 0, 0)},
                {"Name": "bucket-error", "CreationDate": datetime(2023, 2, 1, 12, 0, 0)},
            ]
        }

        # First bucket succeeds, second bucket throws unexpected error
        mock_s3_client.get_bucket_location.side_effect = [
            {"LocationConstraint": None},  # us-east-1
            ClientError({"Error": {"Code": "InternalError", "Message": "Internal Error"}}, "get_bucket_location"),
        ]

        # Mock other required calls for the first bucket
        mock_s3_client.get_bucket_encryption.return_value = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        mock_s3_client.get_bucket_versioning.return_value = {"Status": "Disabled"}
        mock_s3_client.get_public_access_block.return_value = {"PublicAccessBlockConfiguration": {}}
        mock_s3_client.get_bucket_policy_status.return_value = {"PolicyStatus": {"IsPublic": False}}
        mock_s3_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
        mock_s3_client.get_bucket_tagging.side_effect = ClientError(
            {"Error": {"Code": "NoSuchTagSet", "Message": "Not found"}}, "get_bucket_tagging"
        )
        mock_s3_client.get_bucket_logging.return_value = {}

        result = s3_collector.collect()

        # Only the first bucket should be included (second bucket skipped due to error)
        assert len(result["Buckets"]) == 1
        assert result["Buckets"][0]["Name"] == "bucket-ok"
