#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS KMS Collector."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.kms import KMSCollector

logger = logging.getLogger("regscale")


class TestKMSCollector:
    """Test suite for KMSCollector class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_kms_client(self):
        """Create a mock KMS client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def collector(self, mock_session):
        """Create a KMSCollector instance without account filtering."""
        return KMSCollector(session=mock_session, region="us-east-1", account_id=None)

    @pytest.fixture
    def collector_with_account_filter(self, mock_session):
        """Create a KMSCollector instance with account filtering."""
        return KMSCollector(session=mock_session, region="us-east-1", account_id="123456789012")

    @pytest.fixture
    def sample_key_metadata(self):
        """Create sample KMS key metadata."""
        return {
            "KeyId": "1234abcd-12ab-34cd-56ef-1234567890ab",
            "Arn": "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab",
            "Description": "Test key",
            "Enabled": True,
            "KeyState": "Enabled",
            "CreationDate": datetime(2023, 1, 1, 0, 0, 0),
            "DeletionDate": None,
            "Origin": "AWS_KMS",
            "KeyManager": "CUSTOMER",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "KeyUsage": "ENCRYPT_DECRYPT",
            "MultiRegion": False,
            "MultiRegionConfiguration": None,
        }

    @pytest.fixture
    def sample_key_info(self, sample_key_metadata):
        """Create sample key info dictionary."""
        return {
            "KeyId": sample_key_metadata["KeyId"],
            "Arn": sample_key_metadata["Arn"],
            "Description": sample_key_metadata["Description"],
            "Enabled": sample_key_metadata["Enabled"],
            "KeyState": sample_key_metadata["KeyState"],
            "CreationDate": str(sample_key_metadata["CreationDate"]),
            "DeletionDate": None,
            "Origin": sample_key_metadata["Origin"],
            "KeyManager": sample_key_metadata["KeyManager"],
            "KeySpec": sample_key_metadata["KeySpec"],
            "KeyUsage": sample_key_metadata["KeyUsage"],
            "MultiRegion": sample_key_metadata["MultiRegion"],
            "MultiRegionConfiguration": sample_key_metadata["MultiRegionConfiguration"],
        }

    @pytest.fixture
    def sample_alias(self):
        """Create sample KMS alias."""
        return {
            "AliasName": "alias/test-key",
            "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/test-key",
            "TargetKeyId": "1234abcd-12ab-34cd-56ef-1234567890ab",
        }

    # Test initialization
    def test_collector_initialization_without_account_id(self, mock_session):
        """Test collector initialization without account ID filtering."""
        collector = KMSCollector(session=mock_session, region="us-west-2", account_id=None)
        assert collector.session == mock_session
        assert collector.region == "us-west-2"
        assert collector.account_id is None

    def test_collector_initialization_with_account_id(self, mock_session):
        """Test collector initialization with account ID filtering."""
        collector = KMSCollector(session=mock_session, region="us-east-1", account_id="123456789012")
        assert collector.session == mock_session
        assert collector.region == "us-east-1"
        assert collector.account_id == "123456789012"

    # Test collect() method
    @patch.object(KMSCollector, "_get_client")
    @patch.object(KMSCollector, "_list_keys")
    @patch.object(KMSCollector, "_list_aliases")
    def test_collect_success(self, mock_list_aliases, mock_list_keys, mock_get_client, collector, sample_key_info):
        """Test successful collection of KMS resources."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_keys.return_value = [sample_key_info]
        mock_list_aliases.return_value = [
            {
                "Region": "us-east-1",
                "AliasName": "alias/test-key",
                "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/test-key",
                "TargetKeyId": "1234abcd-12ab-34cd-56ef-1234567890ab",
            }
        ]

        result = collector.collect()

        assert "Keys" in result
        assert "Aliases" in result
        assert len(result["Keys"]) == 1
        assert len(result["Aliases"]) == 1
        assert result["Keys"][0]["KeyId"] == sample_key_info["KeyId"]
        assert result["Aliases"][0]["AliasName"] == "alias/test-key"

        mock_get_client.assert_called_once_with("kms")
        mock_list_keys.assert_called_once_with(mock_client)
        mock_list_aliases.assert_called_once_with(mock_client)

    @patch.object(KMSCollector, "_get_client")
    @patch.object(KMSCollector, "_handle_error")
    def test_collect_client_error(self, mock_handle_error, mock_get_client, collector):
        """Test collect method handles ClientError."""
        mock_get_client.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListKeys"
        )

        result = collector.collect()

        assert result == {"Keys": [], "Aliases": []}
        mock_handle_error.assert_called_once()

    @patch.object(KMSCollector, "_get_client")
    def test_collect_unexpected_error(self, mock_get_client, collector, caplog):
        """Test collect method handles unexpected errors."""
        mock_get_client.side_effect = Exception("Unexpected error")

        with caplog.at_level(logging.ERROR):
            result = collector.collect()

        assert result == {"Keys": [], "Aliases": []}
        assert "Unexpected error collecting KMS resources" in caplog.text

    # Test _list_keys() method
    @patch.object(KMSCollector, "_describe_key")
    @patch.object(KMSCollector, "_get_key_rotation_status")
    @patch.object(KMSCollector, "_get_key_policy")
    @patch.object(KMSCollector, "_list_grants")
    @patch.object(KMSCollector, "_list_resource_tags")
    def test_list_keys_success(
        self,
        mock_list_tags,
        mock_list_grants,
        mock_get_policy,
        mock_get_rotation,
        mock_describe_key,
        collector,
        mock_kms_client,
        sample_key_info,
    ):
        """Test successful listing of KMS keys."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "1234abcd-12ab-34cd-56ef-1234567890ab"}]}]

        # Setup method returns
        mock_describe_key.return_value = sample_key_info
        mock_get_rotation.return_value = True
        mock_get_policy.return_value = '{"Version": "2012-10-17"}'
        mock_list_grants.return_value = [{"GrantId": "grant1"}]
        mock_list_tags.return_value = [{"TagKey": "Environment", "TagValue": "Test"}]

        result = collector._list_keys(mock_kms_client)

        assert len(result) == 1
        assert result[0]["KeyId"] == "1234abcd-12ab-34cd-56ef-1234567890ab"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["RotationEnabled"] is True
        assert result[0]["Policy"] == '{"Version": "2012-10-17"}'
        assert result[0]["GrantCount"] == 1
        assert len(result[0]["Tags"]) == 1

        mock_kms_client.get_paginator.assert_called_once_with("list_keys")
        mock_describe_key.assert_called_once()
        mock_get_rotation.assert_called_once()
        mock_get_policy.assert_called_once()
        mock_list_grants.assert_called_once()
        mock_list_tags.assert_called_once()

    @patch.object(KMSCollector, "_describe_key")
    def test_list_keys_skip_none_key_info(self, mock_describe_key, collector, mock_kms_client, sample_key_info):
        """Test listing keys skips keys with no metadata."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "key1"}, {"KeyId": "key2"}]}]

        # First key returns None, second returns valid info
        mock_describe_key.side_effect = [None, sample_key_info]

        result = collector._list_keys(mock_kms_client)

        # Should only get one key (the second one)
        assert len(result) == 1
        assert mock_describe_key.call_count == 2

    @patch.object(KMSCollector, "_describe_key")
    @patch.object(KMSCollector, "_matches_account_id")
    def test_list_keys_with_account_filter(
        self, mock_matches_account, mock_describe_key, collector_with_account_filter, mock_kms_client, sample_key_info
    ):
        """Test listing keys with account ID filtering."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "key1"}, {"KeyId": "key2"}]}]

        # Both keys return valid info
        mock_describe_key.return_value = sample_key_info
        # First key doesn't match account, second does
        mock_matches_account.side_effect = [False, True]

        result = collector_with_account_filter._list_keys(mock_kms_client)

        # Should only get one key (the second one that matches)
        assert len(result) == 1
        assert mock_matches_account.call_count == 2

    def test_list_keys_handle_not_found_exception(self, collector, mock_kms_client, caplog):
        """Test listing keys handles NotFoundException gracefully."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "key1"}]}]

        # describe_key raises NotFoundException
        mock_kms_client.describe_key.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "DescribeKey"
        )

        with caplog.at_level(logging.DEBUG):
            result = collector._list_keys(mock_kms_client)

        # Should return empty list and not log error
        assert len(result) == 0
        assert "Error getting details for key" not in caplog.text

    def test_list_keys_handle_access_denied_exception(self, collector, mock_kms_client, caplog):
        """Test listing keys handles AccessDeniedException gracefully."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "key1"}]}]

        # describe_key raises AccessDeniedException
        mock_kms_client.describe_key.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeKey"
        )

        with caplog.at_level(logging.DEBUG):
            result = collector._list_keys(mock_kms_client)

        # Should return empty list and not log error
        assert len(result) == 0
        assert "Error getting details for key" not in caplog.text

    @patch.object(KMSCollector, "_describe_key")
    def test_list_keys_handle_other_client_error(self, mock_describe_key, collector, mock_kms_client, caplog):
        """Test listing keys logs other ClientErrors."""
        # Setup paginator
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Keys": [{"KeyId": "key1"}]}]

        # _describe_key raises different error (not NotFoundException or AccessDeniedException)
        mock_describe_key.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "DescribeKey"
        )

        with caplog.at_level(logging.ERROR):
            result = collector._list_keys(mock_kms_client)

        # Should return empty list and log error through the except handler
        assert len(result) == 0

    def test_list_keys_pagination_error_access_denied(self, collector, mock_kms_client, caplog):
        """Test listing keys handles pagination AccessDeniedException."""
        # Setup paginator to raise AccessDeniedException
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListKeys"
        )

        with caplog.at_level(logging.WARNING):
            result = collector._list_keys(mock_kms_client)

        assert len(result) == 0
        assert "Access denied to list KMS keys" in caplog.text

    def test_list_keys_pagination_error_other(self, collector, mock_kms_client, caplog):
        """Test listing keys handles other pagination errors."""
        # Setup paginator to raise different error
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "ListKeys"
        )

        with caplog.at_level(logging.ERROR):
            result = collector._list_keys(mock_kms_client)

        assert len(result) == 0
        assert "Error listing KMS keys" in caplog.text

    # Test _describe_key() method
    def test_describe_key_success(self, collector, mock_kms_client, sample_key_metadata):
        """Test successful key description."""
        mock_kms_client.describe_key.return_value = {"KeyMetadata": sample_key_metadata}

        result = collector._describe_key(mock_kms_client, "1234abcd-12ab-34cd-56ef-1234567890ab")

        assert result is not None
        assert result["KeyId"] == sample_key_metadata["KeyId"]
        assert result["Arn"] == sample_key_metadata["Arn"]
        assert result["Description"] == sample_key_metadata["Description"]
        assert result["Enabled"] == sample_key_metadata["Enabled"]
        assert result["KeyState"] == sample_key_metadata["KeyState"]
        assert result["CreationDate"] == str(sample_key_metadata["CreationDate"])
        assert result["DeletionDate"] is None
        assert result["Origin"] == sample_key_metadata["Origin"]
        assert result["KeyManager"] == sample_key_metadata["KeyManager"]
        assert result["KeySpec"] == sample_key_metadata["KeySpec"]
        assert result["KeyUsage"] == sample_key_metadata["KeyUsage"]
        assert result["MultiRegion"] == sample_key_metadata["MultiRegion"]
        assert result["MultiRegionConfiguration"] == sample_key_metadata["MultiRegionConfiguration"]

        mock_kms_client.describe_key.assert_called_once_with(KeyId="1234abcd-12ab-34cd-56ef-1234567890ab")

    def test_describe_key_with_deletion_date(self, collector, mock_kms_client, sample_key_metadata):
        """Test key description with deletion date."""
        sample_key_metadata["DeletionDate"] = datetime(2024, 12, 31, 23, 59, 59)
        mock_kms_client.describe_key.return_value = {"KeyMetadata": sample_key_metadata}

        result = collector._describe_key(mock_kms_client, "key-id")

        assert result is not None
        assert result["DeletionDate"] == str(sample_key_metadata["DeletionDate"])

    def test_describe_key_not_found(self, collector, mock_kms_client):
        """Test describe key handles NotFoundException."""
        mock_kms_client.describe_key.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "DescribeKey"
        )

        result = collector._describe_key(mock_kms_client, "non-existent-key")

        assert result is None

    def test_describe_key_access_denied(self, collector, mock_kms_client):
        """Test describe key handles AccessDeniedException."""
        mock_kms_client.describe_key.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeKey"
        )

        result = collector._describe_key(mock_kms_client, "key-id")

        assert result is None

    def test_describe_key_other_error(self, collector, mock_kms_client, caplog):
        """Test describe key logs other errors."""
        mock_kms_client.describe_key.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "DescribeKey"
        )

        with caplog.at_level(logging.ERROR):
            result = collector._describe_key(mock_kms_client, "key-id")

        assert result is None
        assert "Error describing key" in caplog.text

    # Test _get_key_rotation_status() method
    def test_get_key_rotation_status_enabled(self, collector, mock_kms_client):
        """Test getting rotation status when enabled."""
        mock_kms_client.get_key_rotation_status.return_value = {"KeyRotationEnabled": True}

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is True
        mock_kms_client.get_key_rotation_status.assert_called_once_with(KeyId="key-id")

    def test_get_key_rotation_status_disabled(self, collector, mock_kms_client):
        """Test getting rotation status when disabled."""
        mock_kms_client.get_key_rotation_status.return_value = {"KeyRotationEnabled": False}

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is False

    def test_get_key_rotation_status_not_found(self, collector, mock_kms_client):
        """Test getting rotation status handles NotFoundException."""
        mock_kms_client.get_key_rotation_status.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "GetKeyRotationStatus"
        )

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is False

    def test_get_key_rotation_status_access_denied(self, collector, mock_kms_client):
        """Test getting rotation status handles AccessDeniedException."""
        mock_kms_client.get_key_rotation_status.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "GetKeyRotationStatus"
        )

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is False

    def test_get_key_rotation_status_unsupported_operation(self, collector, mock_kms_client):
        """Test getting rotation status handles UnsupportedOperationException."""
        mock_kms_client.get_key_rotation_status.side_effect = ClientError(
            {"Error": {"Code": "UnsupportedOperationException", "Message": "Unsupported"}}, "GetKeyRotationStatus"
        )

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is False

    def test_get_key_rotation_status_other_error(self, collector, mock_kms_client):
        """Test getting rotation status logs other errors."""
        mock_kms_client.get_key_rotation_status.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "GetKeyRotationStatus"
        )

        result = collector._get_key_rotation_status(mock_kms_client, "key-id")

        assert result is False

    # Test _get_key_policy() method
    def test_get_key_policy_success(self, collector, mock_kms_client):
        """Test successful key policy retrieval."""
        policy = '{"Version": "2012-10-17", "Statement": []}'
        mock_kms_client.get_key_policy.return_value = {"Policy": policy}

        result = collector._get_key_policy(mock_kms_client, "key-id")

        assert result == policy
        mock_kms_client.get_key_policy.assert_called_once_with(KeyId="key-id", PolicyName="default")

    def test_get_key_policy_not_found(self, collector, mock_kms_client):
        """Test getting key policy handles NotFoundException."""
        mock_kms_client.get_key_policy.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "GetKeyPolicy"
        )

        result = collector._get_key_policy(mock_kms_client, "key-id")

        assert result is None

    def test_get_key_policy_access_denied(self, collector, mock_kms_client):
        """Test getting key policy handles AccessDeniedException."""
        mock_kms_client.get_key_policy.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "GetKeyPolicy"
        )

        result = collector._get_key_policy(mock_kms_client, "key-id")

        assert result is None

    def test_get_key_policy_other_error(self, collector, mock_kms_client):
        """Test getting key policy logs other errors."""
        mock_kms_client.get_key_policy.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "GetKeyPolicy"
        )

        result = collector._get_key_policy(mock_kms_client, "key-id")

        assert result is None

    # Test _list_grants() method
    def test_list_grants_success(self, collector, mock_kms_client):
        """Test successful grant listing."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Grants": [{"GrantId": "grant1"}, {"GrantId": "grant2"}]},
            {"Grants": [{"GrantId": "grant3"}]},
        ]

        result = collector._list_grants(mock_kms_client, "key-id")

        assert len(result) == 3
        assert result[0]["GrantId"] == "grant1"
        assert result[1]["GrantId"] == "grant2"
        assert result[2]["GrantId"] == "grant3"

        mock_kms_client.get_paginator.assert_called_once_with("list_grants")
        mock_paginator.paginate.assert_called_once_with(KeyId="key-id")

    def test_list_grants_empty(self, collector, mock_kms_client):
        """Test listing grants when none exist."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Grants": []}]

        result = collector._list_grants(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_grants_not_found(self, collector, mock_kms_client):
        """Test listing grants handles NotFoundException."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "ListGrants"
        )

        result = collector._list_grants(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_grants_access_denied(self, collector, mock_kms_client):
        """Test listing grants handles AccessDeniedException."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListGrants"
        )

        result = collector._list_grants(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_grants_other_error(self, collector, mock_kms_client):
        """Test listing grants logs other errors."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "ListGrants"
        )

        result = collector._list_grants(mock_kms_client, "key-id")

        assert len(result) == 0

    # Test _list_resource_tags() method
    def test_list_resource_tags_success(self, collector, mock_kms_client):
        """Test successful tag listing."""
        tags = [{"TagKey": "Environment", "TagValue": "Production"}, {"TagKey": "Owner", "TagValue": "Team"}]
        mock_kms_client.list_resource_tags.return_value = {"Tags": tags}

        result = collector._list_resource_tags(mock_kms_client, "key-id")

        assert len(result) == 2
        assert result[0]["TagKey"] == "Environment"
        assert result[0]["TagValue"] == "Production"
        assert result[1]["TagKey"] == "Owner"
        assert result[1]["TagValue"] == "Team"

        mock_kms_client.list_resource_tags.assert_called_once_with(KeyId="key-id")

    def test_list_resource_tags_empty(self, collector, mock_kms_client):
        """Test listing tags when none exist."""
        mock_kms_client.list_resource_tags.return_value = {"Tags": []}

        result = collector._list_resource_tags(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_resource_tags_not_found(self, collector, mock_kms_client):
        """Test listing tags handles NotFoundException."""
        mock_kms_client.list_resource_tags.side_effect = ClientError(
            {"Error": {"Code": "NotFoundException", "Message": "Not found"}}, "ListResourceTags"
        )

        result = collector._list_resource_tags(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_resource_tags_access_denied(self, collector, mock_kms_client):
        """Test listing tags handles AccessDeniedException."""
        mock_kms_client.list_resource_tags.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListResourceTags"
        )

        result = collector._list_resource_tags(mock_kms_client, "key-id")

        assert len(result) == 0

    def test_list_resource_tags_other_error(self, collector, mock_kms_client):
        """Test listing tags logs other errors."""
        mock_kms_client.list_resource_tags.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "ListResourceTags"
        )

        result = collector._list_resource_tags(mock_kms_client, "key-id")

        assert len(result) == 0

    # Test _list_aliases() method
    def test_list_aliases_success_without_filter(self, collector, mock_kms_client):
        """Test successful alias listing without account filtering."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Aliases": [
                    {
                        "AliasName": "alias/test-key-1",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/test-key-1",
                        "TargetKeyId": "key1",
                    },
                    {
                        "AliasName": "alias/aws/s3",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/aws/s3",
                        "TargetKeyId": "key2",
                    },
                ]
            }
        ]

        result = collector._list_aliases(mock_kms_client)

        # Should include both aliases when no account filtering
        assert len(result) == 2
        assert result[0]["AliasName"] == "alias/test-key-1"
        assert result[0]["Region"] == "us-east-1"
        assert result[1]["AliasName"] == "alias/aws/s3"

        mock_kms_client.get_paginator.assert_called_once_with("list_aliases")

    @patch.object(KMSCollector, "_describe_key")
    @patch.object(KMSCollector, "_matches_account_id")
    def test_list_aliases_with_account_filter_skip_aws_managed(
        self, mock_matches_account, mock_describe_key, collector_with_account_filter, mock_kms_client, sample_key_info
    ):
        """Test alias listing with account filter skips AWS managed aliases."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Aliases": [
                    {
                        "AliasName": "alias/test-key-1",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/test-key-1",
                        "TargetKeyId": "key1",
                    },
                    {
                        "AliasName": "alias/aws/s3",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/aws/s3",
                        "TargetKeyId": "key2",
                    },
                ]
            }
        ]

        mock_describe_key.return_value = sample_key_info
        mock_matches_account.return_value = True

        result = collector_with_account_filter._list_aliases(mock_kms_client)

        # Should skip AWS managed alias
        assert len(result) == 1
        assert result[0]["AliasName"] == "alias/test-key-1"

    @patch.object(KMSCollector, "_describe_key")
    @patch.object(KMSCollector, "_matches_account_id")
    def test_list_aliases_with_account_filter_check_target_key(
        self, mock_matches_account, mock_describe_key, collector_with_account_filter, mock_kms_client, sample_key_info
    ):
        """Test alias listing with account filter checks target key account."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Aliases": [
                    {
                        "AliasName": "alias/key-in-account",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/key-in-account",
                        "TargetKeyId": "key1",
                    },
                    {
                        "AliasName": "alias/key-different-account",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/key-different-account",
                        "TargetKeyId": "key2",
                    },
                ]
            }
        ]

        mock_describe_key.return_value = sample_key_info
        # First key matches account, second doesn't
        mock_matches_account.side_effect = [True, False]

        result = collector_with_account_filter._list_aliases(mock_kms_client)

        # Should only include alias for matching account
        assert len(result) == 1
        assert result[0]["AliasName"] == "alias/key-in-account"
        assert mock_describe_key.call_count == 2
        assert mock_matches_account.call_count == 2

    def test_list_aliases_without_target_key_id(self, collector_with_account_filter, mock_kms_client):
        """Test alias listing when alias has no target key ID."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Aliases": [
                    {
                        "AliasName": "alias/no-target",
                        "AliasArn": "arn:aws:kms:us-east-1:123456789012:alias/no-target",
                    }
                ]
            }
        ]

        result = collector_with_account_filter._list_aliases(mock_kms_client)

        # Should include alias even without target key
        assert len(result) == 1
        assert result[0]["AliasName"] == "alias/no-target"
        assert result[0]["TargetKeyId"] is None

    def test_list_aliases_access_denied(self, collector, mock_kms_client, caplog):
        """Test listing aliases handles AccessDeniedException."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListAliases"
        )

        with caplog.at_level(logging.WARNING):
            result = collector._list_aliases(mock_kms_client)

        assert len(result) == 0
        assert "Access denied to list KMS aliases" in caplog.text

    def test_list_aliases_other_error(self, collector, mock_kms_client, caplog):
        """Test listing aliases logs other errors."""
        mock_paginator = MagicMock()
        mock_kms_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "InternalException", "Message": "Internal error"}}, "ListAliases"
        )

        with caplog.at_level(logging.ERROR):
            result = collector._list_aliases(mock_kms_client)

        assert len(result) == 0
        assert "Error listing KMS aliases" in caplog.text

    # Test _matches_account_id() method
    def test_matches_account_id_no_filter(self, collector):
        """Test account matching when no filter is specified."""
        result = collector._matches_account_id("arn:aws:kms:us-east-1:999999999999:key/test")

        # Should return True when no account_id filter
        assert result is True

    def test_matches_account_id_matching(self, collector_with_account_filter):
        """Test account matching with matching account ID."""
        arn = "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"

        result = collector_with_account_filter._matches_account_id(arn)

        assert result is True

    def test_matches_account_id_not_matching(self, collector_with_account_filter):
        """Test account matching with non-matching account ID."""
        arn = "arn:aws:kms:us-east-1:999999999999:key/1234abcd-12ab-34cd-56ef-1234567890ab"

        result = collector_with_account_filter._matches_account_id(arn)

        assert result is False

    def test_matches_account_id_invalid_arn_format(self, collector_with_account_filter):
        """Test account matching with invalid ARN format."""
        invalid_arn = "invalid:arn:format"

        result = collector_with_account_filter._matches_account_id(invalid_arn)

        # Invalid format won't have enough parts, returns False
        assert result is False

    def test_matches_account_id_short_arn(self, collector_with_account_filter):
        """Test account matching with short ARN."""
        short_arn = "arn:aws:kms"

        result = collector_with_account_filter._matches_account_id(short_arn)

        # Short ARN won't have enough parts (< 5), returns False
        assert result is False

    def test_matches_account_id_none_arn(self, collector_with_account_filter):
        """Test account matching with None ARN."""
        result = collector_with_account_filter._matches_account_id(None)

        # None ARN is caught by AttributeError in try/except, returns False
        assert result is False

    # Integration tests
    @patch.object(KMSCollector, "_get_client")
    def test_full_collection_workflow_with_pagination(
        self, mock_get_client, collector, sample_key_metadata, sample_alias
    ):
        """Test full collection workflow with multiple pages."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Setup paginators
        key_paginator = MagicMock()
        key_paginator.paginate.return_value = [
            {"Keys": [{"KeyId": "key1"}]},
            {"Keys": [{"KeyId": "key2"}]},
        ]

        grants_paginator1 = MagicMock()
        grants_paginator1.paginate.return_value = [{"Grants": []}]

        grants_paginator2 = MagicMock()
        grants_paginator2.paginate.return_value = [{"Grants": []}]

        alias_paginator = MagicMock()
        alias_paginator.paginate.return_value = [{"Aliases": [sample_alias]}]

        # Return paginators in order they're called
        mock_client.get_paginator.side_effect = [
            key_paginator,  # For list_keys
            grants_paginator1,  # For list_grants (key1)
            grants_paginator2,  # For list_grants (key2)
            alias_paginator,  # For list_aliases
        ]

        # Setup describe_key responses
        mock_client.describe_key.side_effect = [
            {"KeyMetadata": {**sample_key_metadata, "KeyId": "key1"}},
            {"KeyMetadata": {**sample_key_metadata, "KeyId": "key2"}},
        ]

        # Setup other responses
        mock_client.get_key_rotation_status.return_value = {"KeyRotationEnabled": True}
        mock_client.get_key_policy.return_value = {"Policy": "{}"}
        mock_client.list_resource_tags.return_value = {"Tags": []}

        result = collector.collect()

        assert len(result["Keys"]) == 2
        assert len(result["Aliases"]) == 1
        assert result["Keys"][0]["KeyId"] == "key1"
        assert result["Keys"][1]["KeyId"] == "key2"

    @patch.object(KMSCollector, "_get_client")
    def test_full_collection_workflow_with_multi_region_key(self, mock_get_client, collector, sample_key_metadata):
        """Test collection of multi-region key."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Setup multi-region key metadata
        multi_region_metadata = {
            **sample_key_metadata,
            "MultiRegion": True,
            "MultiRegionConfiguration": {
                "MultiRegionKeyType": "PRIMARY",
                "PrimaryKey": {"Arn": sample_key_metadata["Arn"], "Region": "us-east-1"},
                "ReplicaKeys": [{"Arn": "arn:aws:kms:us-west-2:123456789012:key/replica", "Region": "us-west-2"}],
            },
        }

        # Setup key pagination
        key_paginator = MagicMock()
        mock_client.get_paginator.side_effect = [
            key_paginator,  # For list_keys
            MagicMock(),  # For list_grants
            MagicMock(),  # For list_aliases
        ]

        key_paginator.paginate.return_value = [{"Keys": [{"KeyId": "multi-region-key"}]}]

        # Setup describe_key response
        mock_client.describe_key.return_value = {"KeyMetadata": multi_region_metadata}

        # Setup other responses
        mock_client.get_key_rotation_status.return_value = {"KeyRotationEnabled": True}
        mock_client.get_key_policy.return_value = {"Policy": "{}"}
        mock_client.list_resource_tags.return_value = {"Tags": []}

        # Setup grants pagination
        grants_paginator = MagicMock()
        grants_paginator.paginate.return_value = [{"Grants": []}]

        # Setup aliases pagination
        alias_paginator = MagicMock()
        alias_paginator.paginate.return_value = [{"Aliases": []}]

        result = collector.collect()

        assert len(result["Keys"]) == 1
        assert result["Keys"][0]["MultiRegion"] is True
        assert result["Keys"][0]["MultiRegionConfiguration"]["MultiRegionKeyType"] == "PRIMARY"
        assert len(result["Keys"][0]["MultiRegionConfiguration"]["ReplicaKeys"]) == 1
