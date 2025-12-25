#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS S3 Evidence Integration."""

import gzip
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from regscale.integrations.commercial.aws.s3_evidence import (
    S3ComplianceItem,
    AWSS3EvidenceIntegration,
)

PATH = "regscale.integrations.commercial.aws.s3_evidence"


class TestS3ComplianceItem:
    """Test S3ComplianceItem class."""

    def test_init_with_complete_data(self):
        """Test initialization with complete bucket data."""
        bucket_data = {
            "Name": "test-bucket",
            "Region": "us-east-1",
            "CreationDate": "2023-01-01T00:00:00.000Z",
            "Encryption": {"Enabled": True, "SSEAlgorithm": "AES256"},
            "Versioning": {"Status": "Enabled"},
            "PublicAccessBlock": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
            "PolicyStatus": {"IsPublic": False},
            "ACL": {"Grants": []},
            "Logging": {"Enabled": True, "TargetBucket": "log-bucket"},
            "Tags": [{"Key": "Environment", "Value": "Production"}],
        }

        item = S3ComplianceItem(bucket_data)

        assert item.bucket_name == "test-bucket"
        assert item.region == "us-east-1"
        assert item.creation_date == "2023-01-01T00:00:00.000Z"
        assert item.encryption == {"Enabled": True, "SSEAlgorithm": "AES256"}
        assert item.versioning == {"Status": "Enabled"}
        assert item.public_access_block["BlockPublicAcls"] is True
        assert item.policy_status == {"IsPublic": False}
        assert item.acl == {"Grants": []}
        assert item.logging == {"Enabled": True, "TargetBucket": "log-bucket"}
        assert item.tags == [{"Key": "Environment", "Value": "Production"}]

    def test_init_with_minimal_data(self):
        """Test initialization with minimal bucket data."""
        bucket_data = {}

        item = S3ComplianceItem(bucket_data)

        assert item.bucket_name == ""
        assert item.region == ""
        assert item.creation_date == ""
        assert item.encryption == {}
        assert item.versioning == {}
        assert item.public_access_block == {}
        assert item.policy_status == {}
        assert item.acl == {}
        assert item.logging == {}
        assert item.tags == []

    def test_to_dict(self):
        """Test conversion to dictionary."""
        bucket_data = {
            "Name": "test-bucket",
            "Region": "us-west-2",
            "Encryption": {"Enabled": False},
        }

        item = S3ComplianceItem(bucket_data)
        result = item.to_dict()

        assert result == bucket_data
        assert result is item.raw_data


class TestAWSS3EvidenceIntegration:
    """Test AWSS3EvidenceIntegration class."""

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_init_with_defaults(self, mock_api, mock_mapper):
        """Test initialization with default parameters."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.account_id is None
        assert integration.tags == {}
        assert integration.bucket_name_filter is None
        assert integration.create_evidence is False
        assert integration.create_ssp_attachment is True
        assert integration.evidence_control_ids == []
        assert integration.force_refresh is False
        assert integration.aws_profile is None
        assert integration.aws_access_key_id is None
        assert integration.aws_secret_access_key is None
        assert integration.aws_session_token is None
        assert integration.session is None
        assert integration.collector is None
        assert integration.cache_ttl_hours == 4
        assert integration.raw_s3_data == {}
        assert integration.buckets == []
        mock_api.assert_called_once()
        mock_mapper.assert_called_once_with(framework="NIST800-53R5")

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_init_with_custom_parameters(self, mock_api, mock_mapper):
        """Test initialization with custom parameters."""
        integration = AWSS3EvidenceIntegration(
            plan_id=456,
            region="us-west-2",
            account_id="123456789012",
            tags={"Environment": "Production"},
            bucket_name_filter="prod",
            create_evidence=True,
            create_ssp_attachment=False,
            evidence_control_ids=["AC-3", "SC-13"],
            force_refresh=True,
            aws_profile="test-profile",
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
        )

        assert integration.plan_id == 456
        assert integration.region == "us-west-2"
        assert integration.account_id == "123456789012"
        assert integration.tags == {"Environment": "Production"}
        assert integration.bucket_name_filter == "prod"
        assert integration.create_evidence is True
        assert integration.create_ssp_attachment is False
        assert integration.evidence_control_ids == ["AC-3", "SC-13"]
        assert integration.force_refresh is True
        assert integration.aws_profile == "test-profile"
        assert integration.aws_access_key_id == "AKIATEST"
        assert integration.aws_secret_access_key == "secret"
        assert integration.aws_session_token == "token"

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_file_path(self, mock_api, mock_mapper):
        """Test cache file path generation."""
        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")

        cache_path = integration._get_cache_file_path()

        assert isinstance(cache_path, Path)
        assert cache_path.name == "s3_buckets_us-east-1_123456789012.json"
        assert "regscale" in str(cache_path)
        assert "aws_s3_cache" in str(cache_path)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_file_path_without_account_id(self, mock_api, mock_mapper):
        """Test cache file path generation without account ID."""
        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-west-2")

        cache_path = integration._get_cache_file_path()

        assert cache_path.name == "s3_buckets_us-west-2_default.json"

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_no_cache(self, mock_api, mock_mapper):
        """Test cache validation when cache file doesn't exist."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        # Ensure cache directory exists (it gets created during init)
        cache_file = integration._get_cache_file_path()
        if cache_file.exists():
            cache_file.unlink()

        is_valid = integration._is_cache_valid()

        assert is_valid is False

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_expired(self, mock_api, mock_mapper):
        """Test cache validation when cache is expired."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        # Create cache directory and file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("[]")

        # Set modification time to 5 hours ago (expired)
        five_hours_ago = datetime.now() - timedelta(hours=5)
        os.utime(cache_file, (five_hours_ago.timestamp(), five_hours_ago.timestamp()))

        is_valid = integration._is_cache_valid()

        assert is_valid is False

        # Cleanup
        cache_file.unlink()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_fresh(self, mock_api, mock_mapper):
        """Test cache validation when cache is fresh."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        # Create cache directory and file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("[]")

        is_valid = integration._is_cache_valid()

        assert is_valid is True

        # Cleanup
        cache_file.unlink()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_save_cache(self, mock_api, mock_mapper):
        """Test saving data to cache."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        test_data = [{"Name": "test-bucket"}]

        integration._save_cache(test_data)

        assert cache_file.exists()
        with open(cache_file) as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

        # Cleanup
        cache_file.unlink()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_save_cache_error(self, mock_api, mock_mapper, caplog):
        """Test saving cache with error."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            integration._save_cache({"test": "data"})

        assert "Failed to save cache" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_load_cached_data(self, mock_api, mock_mapper):
        """Test loading data from cache."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        test_data = [{"Name": "test-bucket"}]

        # Create cache
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(test_data, f)

        loaded_data = integration._load_cached_data()

        assert loaded_data == test_data

        # Cleanup
        cache_file.unlink()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_load_cached_data_error(self, mock_api, mock_mapper, caplog):
        """Test loading cache with error."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        result = integration._load_cached_data()

        assert result is None
        # Cache loading can fail either due to file error or invalid format
        assert "Failed to load cache" in caplog.text or "Invalid cache format" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_age_hours_no_cache(self, mock_api, mock_mapper):
        """Test getting cache age when no cache exists."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        age = integration._get_cache_age_hours()

        assert age == float("inf")

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_age_hours_with_cache(self, mock_api, mock_mapper):
        """Test getting cache age with existing cache."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        # Create cache
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("[]")

        # Set modification time to 2 hours ago
        two_hours_ago = datetime.now() - timedelta(hours=2)
        os.utime(cache_file, (two_hours_ago.timestamp(), two_hours_ago.timestamp()))

        age = integration._get_cache_age_hours()

        assert 1.9 < age < 2.1  # Allow small variance

        # Cleanup
        cache_file.unlink()

    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_with_keys(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with access keys."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSS3EvidenceIntegration(
            plan_id=123,
            region="us-west-2",
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
        )

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
            region_name="us-west-2",
        )
        assert integration.session == mock_session

    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_with_profile(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with profile."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1", aws_profile="test-profile")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(profile_name="test-profile", region_name="us-east-1")
        assert integration.session == mock_session

    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_default(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with default credentials."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(region_name="us-east-1")
        assert integration.session == mock_session

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_compliance_data_from_cache(self, mock_api, mock_mapper):
        """Test fetching compliance data from cache."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        cached_data = [{"Name": "test-bucket"}]

        with patch.object(integration, "_is_cache_valid", return_value=True):
            with patch.object(integration, "_load_cached_data", return_value=cached_data):
                result = integration.fetch_compliance_data()

        assert result == cached_data

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_compliance_data_force_refresh(self, mock_api, mock_mapper):
        """Test fetching compliance data with force refresh."""
        integration = AWSS3EvidenceIntegration(plan_id=123, force_refresh=True)

        fresh_data = [{"Name": "fresh-bucket"}]

        with patch.object(integration, "_fetch_fresh_s3_data", return_value=fresh_data):
            result = integration.fetch_compliance_data()

        assert result == fresh_data

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_compliance_data_cache_empty(self, mock_api, mock_mapper):
        """Test fetching compliance data when cache returns None."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        fresh_data = [{"Name": "fresh-bucket"}]

        with patch.object(integration, "_is_cache_valid", return_value=True):
            with patch.object(integration, "_load_cached_data", return_value=None):
                with patch.object(integration, "_fetch_fresh_s3_data", return_value=fresh_data):
                    result = integration.fetch_compliance_data()

        assert result == fresh_data

    @patch(f"{PATH}.S3Collector")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_fresh_s3_data(self, mock_api, mock_mapper, mock_collector_class):
        """Test fetching fresh S3 data."""
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect.return_value = {
            "Buckets": [{"Name": "bucket-1"}, {"Name": "bucket-2"}],
        }

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1")

        mock_session = MagicMock()
        integration.session = mock_session

        with patch.object(integration, "_save_cache"):
            result = integration._fetch_fresh_s3_data()

        assert len(result) == 2
        assert result[0]["Name"] == "bucket-1"
        mock_collector_class.assert_called_once_with(session=mock_session, region="us-east-1", account_id=None, tags={})

    @patch(f"{PATH}.S3Collector")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_fresh_s3_data_with_filter(self, mock_api, mock_mapper, mock_collector_class):
        """Test fetching fresh S3 data with bucket name filter."""
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect.return_value = {
            "Buckets": [
                {"Name": "prod-bucket"},
                {"Name": "dev-bucket"},
                {"Name": "prod-bucket-2"},
            ],
        }

        integration = AWSS3EvidenceIntegration(plan_id=123, bucket_name_filter="prod")

        mock_session = MagicMock()
        integration.session = mock_session

        with patch.object(integration, "_save_cache"):
            result = integration._fetch_fresh_s3_data()

        assert len(result) == 2
        assert all("prod" in bucket["Name"] for bucket in result)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_fresh_s3_data_initializes_session(self, mock_api, mock_mapper):
        """Test that fetch_fresh_s3_data initializes session if needed."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        with patch.object(integration, "_initialize_aws_session") as mock_init:
            with patch(f"{PATH}.S3Collector"):
                integration._fetch_fresh_s3_data()

        mock_init.assert_called_once()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_compliance_item(self, mock_api, mock_mapper):
        """Test creating a compliance item from raw data."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        raw_data = {
            "Name": "test-bucket",
            "Region": "us-east-1",
        }

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, S3ComplianceItem)
        assert result.bucket_name == "test-bucket"

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_assess_compliance(self, mock_api, mock_mapper):
        """Test assessing compliance."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance

        mock_mapper_instance.assess_bucket_compliance.return_value = {
            "SC-13": "PASS",
            "SC-28": "FAIL",
        }
        mock_mapper_instance.assess_all_buckets_compliance.return_value = {
            "SC-13": "PASS",
            "SC-28": "FAIL",
            "AC-3": "FAIL",
        }

        integration = AWSS3EvidenceIntegration(plan_id=123)
        integration.buckets = [
            S3ComplianceItem({"Name": "bucket-1"}),
            S3ComplianceItem({"Name": "bucket-2"}),
        ]

        result = integration._assess_compliance()

        assert "overall" in result
        assert "buckets" in result
        assert len(result["buckets"]) == 2
        assert result["overall"] == {"SC-13": "PASS", "SC-28": "FAIL", "AC-3": "FAIL"}

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_no_buckets(self, mock_api, mock_mapper, caplog):
        """Test sync_compliance_data with no buckets."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        with patch.object(integration, "fetch_compliance_data", return_value=[]):
            integration.sync_compliance_data()

        assert "No S3 bucket data to sync" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_with_buckets(self, mock_api, mock_mapper):
        """Test sync_compliance_data with buckets."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_bucket_compliance.return_value = {"SC-13": "PASS"}
        mock_mapper_instance.assess_all_buckets_compliance.return_value = {"SC-13": "PASS"}

        integration = AWSS3EvidenceIntegration(plan_id=123, create_evidence=False, create_ssp_attachment=False)

        bucket_data = [{"Name": "test-bucket"}]

        with patch.object(integration, "fetch_compliance_data", return_value=bucket_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        assert len(integration.buckets) == 1
        mock_create_evidence.assert_not_called()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_with_evidence(self, mock_api, mock_mapper):
        """Test sync_compliance_data with evidence creation."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_bucket_compliance.return_value = {"SC-13": "PASS"}
        mock_mapper_instance.assess_all_buckets_compliance.return_value = {"SC-13": "PASS"}

        integration = AWSS3EvidenceIntegration(plan_id=123, create_evidence=True)

        bucket_data = [{"Name": "test-bucket"}]

        with patch.object(integration, "fetch_compliance_data", return_value=bucket_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        mock_create_evidence.assert_called_once()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_file(self, mock_api, mock_mapper):
        """Test creating evidence file."""
        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")
        integration.buckets = [
            S3ComplianceItem(
                {
                    "Name": "test-bucket",
                    "Region": "us-east-1",
                    "Encryption": {"Enabled": True, "SSEAlgorithm": "AES256"},
                    "Versioning": {"Status": "Enabled"},
                    "PublicAccessBlock": {
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                    "PolicyStatus": {"IsPublic": False},
                    "ACL": {"Grants": []},
                    "Logging": {"Enabled": True},
                    "Tags": [{"Key": "Environment", "Value": "Test"}],
                }
            )
        ]

        compliance_results = {
            "overall": {"SC-13": "PASS", "SC-28": "FAIL"},
            "buckets": [{"bucket_name": "test-bucket", "controls": {"SC-13": "PASS"}}],
        }

        evidence_file = integration._create_evidence_file(compliance_results)

        assert os.path.exists(evidence_file)
        assert evidence_file.endswith(".jsonl.gz")

        # Verify file contents
        with gzip.open(evidence_file, "rt", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 3  # metadata, summary, bucket record

        # Parse and verify metadata
        metadata = json.loads(lines[0])
        assert metadata["type"] == "metadata"
        assert metadata["region"] == "us-east-1"
        assert metadata["account_id"] == "123456789012"
        assert metadata["bucket_count"] == 1

        # Parse and verify summary
        summary = json.loads(lines[1])
        assert summary["type"] == "compliance_summary"
        assert summary["results"]["SC-13"] == "PASS"

        # Parse and verify bucket record
        bucket_record = json.loads(lines[2])
        assert bucket_record["type"] == "bucket_configuration"
        assert bucket_record["bucket_name"] == "test-bucket"
        assert bucket_record["encryption"]["Enabled"] is True

        # Cleanup
        os.remove(evidence_file)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_file_error(self, mock_api, mock_mapper):
        """Test creating evidence file with error."""
        integration = AWSS3EvidenceIntegration(plan_id=123)
        integration.buckets = []

        compliance_results = {"overall": {}, "buckets": []}

        with patch("gzip.open", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                integration._create_evidence_file(compliance_results)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_with_evidence(self, mock_api, mock_mapper, mock_file):
        """Test creating SSP attachment with evidence."""
        mock_file.upload_file_to_regscale.return_value = True

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1")

        # Create temporary evidence file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        compliance_results = {"overall": {"SC-13": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        mock_file.upload_file_to_regscale.assert_called_once()
        call_kwargs = mock_file.upload_file_to_regscale.call_args[1]
        assert call_kwargs["parent_id"] == 123
        assert call_kwargs["parent_module"] == "securityplans"
        assert "s3_evidence" in call_kwargs["file_name"]
        assert "aws,s3,storage,compliance,automated" == call_kwargs["tags"]

        # Cleanup
        os.remove(evidence_file_path)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_duplicate_check(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with duplicate check."""
        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-west-2")

        evidence_file_path = "/tmp/test_evidence.jsonl.gz"
        compliance_results = {"overall": {"SC-13": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=True):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        mock_file.upload_file_to_regscale.assert_not_called()
        assert "already exists for today" in caplog.text

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_upload_failure(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with upload failure."""
        mock_file.upload_file_to_regscale.return_value = False

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1")

        # Create temporary evidence file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        compliance_results = {"overall": {"SC-13": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        assert "Failed to upload S3 evidence file" in caplog.text

        # Cleanup
        os.remove(evidence_file_path)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_error_handling(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with error."""
        integration = AWSS3EvidenceIntegration(plan_id=123)

        evidence_file_path = "/tmp/nonexistent.jsonl.gz"
        compliance_results = {"overall": {}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        assert "Failed to create SSP attachment" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts(self, mock_api, mock_mapper):
        """Test creating evidence artifacts."""
        integration = AWSS3EvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.buckets = []

        compliance_results = {"overall": {}, "buckets": []}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz") as mock_create:
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove") as mock_remove:
                        integration._create_evidence_artifacts(compliance_results)

        mock_create.assert_called_once_with(compliance_results)
        mock_upload.assert_called_once()
        mock_remove.assert_called_once_with("/tmp/test.jsonl.gz")

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts_no_ssp_attachment(self, mock_api, mock_mapper):
        """Test creating evidence artifacts without SSP attachment."""
        integration = AWSS3EvidenceIntegration(plan_id=123, create_ssp_attachment=False)
        integration.buckets = []

        compliance_results = {"overall": {}, "buckets": []}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz"):
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove"):
                        integration._create_evidence_artifacts(compliance_results)

        mock_upload.assert_not_called()

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts_cleanup(self, mock_api, mock_mapper):
        """Test evidence artifacts cleanup."""
        integration = AWSS3EvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.buckets = []

        compliance_results = {"overall": {}, "buckets": []}

        # Create actual temp file to test cleanup
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name

        with patch.object(integration, "_create_evidence_file", return_value=evidence_file_path):
            with patch.object(integration, "_create_ssp_attachment_with_evidence"):
                integration._create_evidence_artifacts(compliance_results)

        # Verify file was cleaned up
        assert not os.path.exists(evidence_file_path)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_records(self, mock_api, mock_mapper):
        """Test creating evidence records."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.create_evidence.return_value = {"id": 999}

        integration = AWSS3EvidenceIntegration(plan_id=123, evidence_control_ids=["SC-13", "SC-28"])
        integration.buckets = []

        evidence_file_path = "/tmp/test.jsonl.gz"
        compliance_results = {"overall": {"SC-13": "PASS"}}

        with patch.object(integration, "_build_evidence_description", return_value="Test description"):
            with patch.object(integration, "_upload_evidence_file") as mock_upload:
                with patch.object(integration, "_link_evidence_to_controls") as mock_link:
                    integration._create_evidence_records(evidence_file_path, compliance_results)

        mock_api_instance.create_evidence.assert_called_once()
        mock_upload.assert_called_once_with(999, evidence_file_path)
        mock_link.assert_called_once_with(999, is_attachment=False)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_upload_evidence_file(self, mock_api, mock_mapper):
        """Test uploading evidence file."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        integration = AWSS3EvidenceIntegration(plan_id=123)

        evidence_id = 999
        file_path = "/tmp/test.jsonl.gz"

        integration._upload_evidence_file(evidence_id, file_path)

        mock_api_instance.upload_evidence_file.assert_called_once_with(evidence_id, file_path)

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_upload_evidence_file_error(self, mock_api, mock_mapper, caplog):
        """Test uploading evidence file with error."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.upload_evidence_file.side_effect = Exception("Upload failed")

        integration = AWSS3EvidenceIntegration(plan_id=123)

        integration._upload_evidence_file(999, "/tmp/test.jsonl.gz")

        assert "Failed to upload evidence file" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_link_evidence_to_controls(self, mock_api, mock_mapper):
        """Test linking evidence to controls."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        integration = AWSS3EvidenceIntegration(plan_id=123, evidence_control_ids=["SC-13", "SC-28"])

        integration._link_evidence_to_controls(999, is_attachment=False)

        assert mock_api_instance.link_evidence_to_control.call_count == 2

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_link_evidence_to_controls_as_attachment(self, mock_api, mock_mapper):
        """Test linking evidence to controls as attachment."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        integration = AWSS3EvidenceIntegration(plan_id=123, evidence_control_ids=["SC-13", "SC-28"])

        integration._link_evidence_to_controls(999, is_attachment=True)

        assert mock_api_instance.link_ssp_attachment_to_control.call_count == 2

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_link_evidence_to_controls_error(self, mock_api, mock_mapper, caplog):
        """Test linking evidence to controls with error."""
        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance
        mock_api_instance.link_evidence_to_control.side_effect = Exception("Link failed")

        integration = AWSS3EvidenceIntegration(plan_id=123, evidence_control_ids=["SC-13"])

        integration._link_evidence_to_controls(999, is_attachment=False)

        assert "Failed to link evidence to controls" in caplog.text

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_build_evidence_description(self, mock_api, mock_mapper):
        """Test building HTML-formatted evidence description."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.get_control_description.side_effect = lambda x: f"{x} description"

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")
        integration.buckets = [
            S3ComplianceItem(
                {
                    "Name": "bucket-1",
                    "Encryption": {"Enabled": True},
                    "Versioning": {"Status": "Enabled"},
                }
            ),
            S3ComplianceItem(
                {
                    "Name": "bucket-2",
                    "Encryption": {"Enabled": False},
                    "Versioning": {"Status": "Disabled"},
                }
            ),
        ]

        compliance_results = {
            "overall": {"SC-13": "PASS", "SC-28": "FAIL"},
        }

        description = integration._build_evidence_description(compliance_results)

        assert "AWS S3 Storage Configuration Evidence" in description
        assert "us-east-1" in description
        assert "123456789012" in description
        assert "Total Buckets:</strong> 2" in description
        assert "Controls Passed:</strong> 1" in description
        assert "SC-13" in description
        assert "Controls Failed:</strong> 1" in description
        assert "SC-28" in description
        assert "bucket-1" in description
        assert "Encryption=Enabled" in description
        assert "Versioning=Enabled" in description

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_build_evidence_description_many_buckets(self, mock_api, mock_mapper):
        """Test building evidence description with many buckets (limit to 10)."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.get_control_description.return_value = "Test description"

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1")
        integration.buckets = [
            S3ComplianceItem({"Name": f"bucket-{i}", "Encryption": {}, "Versioning": {}}) for i in range(15)
        ]

        compliance_results = {"overall": {"SC-13": "PASS"}}

        description = integration._build_evidence_description(compliance_results)

        assert "bucket-0" in description
        assert "bucket-9" in description
        assert "... and 5 more buckets" in description

    @patch(f"{PATH}.S3ControlMapper")
    @patch(f"{PATH}.Api")
    def test_build_evidence_description_with_filtering(self, mock_api, mock_mapper):
        """Test building evidence description with control filtering."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.get_control_description.side_effect = lambda x: f"{x} description"

        integration = AWSS3EvidenceIntegration(plan_id=123, region="us-east-1", evidence_control_ids=["SC-13"])
        integration.buckets = []

        compliance_results = {
            "overall": {"SC-13": "PASS", "SC-28": "PASS"},
        }

        description = integration._build_evidence_description(compliance_results)

        # Should include all controls in the description, filtering is for linking only
        assert "SC-13" in description
        assert "SC-28" in description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
