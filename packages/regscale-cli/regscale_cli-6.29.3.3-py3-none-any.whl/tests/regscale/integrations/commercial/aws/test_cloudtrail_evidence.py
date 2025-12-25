#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS CloudTrail Evidence Integration."""

import gzip
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import boto3
import pytest

from regscale.integrations.commercial.aws.cloudtrail_evidence import (
    CloudTrailComplianceItem,
    AWSCloudTrailEvidenceIntegration,
)


class TestCloudTrailComplianceItem:
    """Test CloudTrailComplianceItem class."""

    def test_init_with_complete_data(self):
        """Test initialization with complete trail data."""
        trail_data = {
            "Name": "test-trail",
            "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
            "S3BucketName": "test-bucket",
            "IsMultiRegionTrail": True,
            "IsOrganizationTrail": False,
            "LogFileValidationEnabled": True,
            "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/test-key",
            "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:cloudtrail",
            "SnsTopicARN": "arn:aws:sns:us-east-1:123456789012:cloudtrail-topic",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True}],
            "Tags": {"Environment": "Production"},
            "Region": "us-east-1",
        }

        item = CloudTrailComplianceItem(trail_data)

        assert item.trail_name == "test-trail"
        assert item.trail_arn == "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail"
        assert item.s3_bucket_name == "test-bucket"
        assert item.is_multi_region is True
        assert item.is_organization_trail is False
        assert item.log_file_validation_enabled is True
        assert item.kms_key_id == "arn:aws:kms:us-east-1:123456789012:key/test-key"
        assert item.cloud_watch_logs_log_group_arn == "arn:aws:logs:us-east-1:123456789012:log-group:cloudtrail"
        assert item.sns_topic_arn == "arn:aws:sns:us-east-1:123456789012:cloudtrail-topic"
        assert item.status == {"IsLogging": True}
        assert item.event_selectors == [{"IncludeManagementEvents": True}]
        assert item.tags == {"Environment": "Production"}
        assert item.region == "us-east-1"

    def test_init_with_minimal_data(self):
        """Test initialization with minimal trail data."""
        trail_data = {}

        item = CloudTrailComplianceItem(trail_data)

        assert item.trail_name == ""
        assert item.trail_arn == ""
        assert item.s3_bucket_name == ""
        assert item.is_multi_region is False
        assert item.is_organization_trail is False
        assert item.log_file_validation_enabled is False
        assert item.kms_key_id is None
        assert item.cloud_watch_logs_log_group_arn is None
        assert item.sns_topic_arn is None
        assert item.status == {}
        assert item.event_selectors == []
        assert item.tags == {}
        assert item.region == ""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        trail_data = {
            "Name": "test-trail",
            "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
            "S3BucketName": "test-bucket",
        }

        item = CloudTrailComplianceItem(trail_data)
        result = item.to_dict()

        assert result == trail_data
        assert result is item.raw_data


class TestAWSCloudTrailEvidenceIntegration:
    """Test AWSCloudTrailEvidenceIntegration class."""

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_init_with_defaults(self, mock_api, mock_mapper):
        """Test initialization with default parameters."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.account_id is None
        assert integration.tags == {}
        assert integration.trail_name_filter is None
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
        assert integration.raw_cloudtrail_data == {}
        assert integration.trails == []
        mock_api.assert_called_once()
        mock_mapper.assert_called_once_with(framework="NIST800-53R5")

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_init_with_custom_parameters(self, mock_api, mock_mapper):
        """Test initialization with custom parameters."""
        integration = AWSCloudTrailEvidenceIntegration(
            plan_id=456,
            region="us-west-2",
            account_id="123456789012",
            tags={"Environment": "Production"},
            trail_name_filter="prod",
            create_evidence=True,
            create_ssp_attachment=False,
            evidence_control_ids=["AC-2", "AU-3"],
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
        assert integration.trail_name_filter == "prod"
        assert integration.create_evidence is True
        assert integration.create_ssp_attachment is False
        assert integration.evidence_control_ids == ["AC-2", "AU-3"]
        assert integration.force_refresh is True
        assert integration.aws_profile == "test-profile"
        assert integration.aws_access_key_id == "AKIATEST"
        assert integration.aws_secret_access_key == "secret"
        assert integration.aws_session_token == "token"

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_get_cache_file_path(self, mock_api, mock_mapper):
        """Test cache file path generation."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")

        cache_path = integration._get_cache_file_path()

        assert isinstance(cache_path, Path)
        assert cache_path.name == "cloudtrail_trails_us-east-1_123456789012.json"
        assert "regscale" in str(cache_path)
        assert "aws_cloudtrail_cache" in str(cache_path)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_get_cache_file_path_without_account_id(self, mock_api, mock_mapper):
        """Test cache file path generation without account ID."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-west-2")

        cache_path = integration._get_cache_file_path()

        assert cache_path.name == "cloudtrail_trails_us-west-2_default.json"

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_is_cache_valid_no_cache(self, mock_api, mock_mapper):
        """Test cache validation when cache file doesn't exist."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        # Ensure cache directory exists (it gets created during init)
        cache_file = integration._get_cache_file_path()
        if cache_file.exists():
            cache_file.unlink()

        is_valid = integration._is_cache_valid()

        assert is_valid is False

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_is_cache_valid_expired(self, mock_api, mock_mapper):
        """Test cache validation when cache is expired."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
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

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_is_cache_valid_fresh(self, mock_api, mock_mapper):
        """Test cache validation when cache is fresh."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        # Create cache directory and file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("[]")

        is_valid = integration._is_cache_valid()

        assert is_valid is True

        # Cleanup
        cache_file.unlink()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_save_cache(self, mock_api, mock_mapper):
        """Test saving data to cache."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        test_data = {"trails": [{"Name": "test-trail"}]}

        integration._save_cache(test_data)

        assert cache_file.exists()
        with open(cache_file) as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

        # Cleanup
        cache_file.unlink()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_save_cache_error(self, mock_api, mock_mapper, caplog):
        """Test saving cache with error."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            integration._save_cache({"test": "data"})

        assert "Failed to save cache" in caplog.text

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_load_cached_data(self, mock_api, mock_mapper):
        """Test loading data from cache."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        # Test data should be a list of trail dicts (not wrapped in a dict)
        test_data = [{"Name": "test-trail"}]

        # Create cache
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(test_data, f)

        loaded_data = integration._load_cached_data()

        assert loaded_data == test_data

        # Cleanup
        cache_file.unlink()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_load_cached_data_error(self, mock_api, mock_mapper, caplog):
        """Test loading cache with error."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        result = integration._load_cached_data()

        assert result is None
        # Cache loading can fail either due to file error or invalid format
        assert "Failed to load cache" in caplog.text or "Invalid cache format" in caplog.text

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_get_cache_age_hours_no_cache(self, mock_api, mock_mapper):
        """Test getting cache age when no cache exists."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        age = integration._get_cache_age_hours()

        assert age == float("inf")

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_get_cache_age_hours_with_cache(self, mock_api, mock_mapper):
        """Test getting cache age with existing cache."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
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

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.boto3.Session")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_initialize_aws_session_with_keys(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with access keys."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSCloudTrailEvidenceIntegration(
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

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.boto3.Session")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_initialize_aws_session_with_profile(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with profile."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1", aws_profile="test-profile")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(profile_name="test-profile", region_name="us-east-1")
        assert integration.session == mock_session

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.boto3.Session")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_initialize_aws_session_default(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with default credentials."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(region_name="us-east-1")
        assert integration.session == mock_session

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_fetch_compliance_data_from_cache(self, mock_api, mock_mapper):
        """Test fetching compliance data from cache."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        cached_data = [{"Name": "test-trail"}]

        with patch.object(integration, "_is_cache_valid", return_value=True):
            with patch.object(integration, "_load_cached_data", return_value=cached_data):
                result = integration.fetch_compliance_data()

        assert result == cached_data

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_fetch_compliance_data_force_refresh(self, mock_api, mock_mapper):
        """Test fetching compliance data with force refresh."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, force_refresh=True)

        fresh_data = [{"Name": "fresh-trail"}]

        with patch.object(integration, "_fetch_fresh_cloudtrail_data", return_value=fresh_data):
            result = integration.fetch_compliance_data()

        assert result == fresh_data

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailCollector")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_fetch_fresh_cloudtrail_data(self, mock_api, mock_mapper, mock_collector_class):
        """Test fetching fresh CloudTrail data."""
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect.return_value = {
            "Trails": [{"Name": "trail-1"}, {"Name": "trail-2"}],
        }

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1")

        mock_session = MagicMock()
        integration.session = mock_session

        with patch.object(integration, "_save_cache"):
            result = integration._fetch_fresh_cloudtrail_data()

        assert len(result) == 2
        assert result[0]["Name"] == "trail-1"
        mock_collector_class.assert_called_once_with(session=mock_session, region="us-east-1", account_id=None, tags={})

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailCollector")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_fetch_fresh_cloudtrail_data_with_filter(self, mock_api, mock_mapper, mock_collector_class):
        """Test fetching fresh CloudTrail data with trail name filter."""
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect.return_value = {
            "Trails": [
                {"Name": "prod-trail"},
                {"Name": "dev-trail"},
                {"Name": "prod-trail-2"},
            ],
        }

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, trail_name_filter="prod")

        mock_session = MagicMock()
        integration.session = mock_session

        with patch.object(integration, "_save_cache"):
            result = integration._fetch_fresh_cloudtrail_data()

        assert len(result) == 2
        assert all("prod" in trail["Name"] for trail in result)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_fetch_fresh_cloudtrail_data_initializes_session(self, mock_api, mock_mapper):
        """Test that fetch_fresh_cloudtrail_data initializes session if needed."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        with patch.object(integration, "_initialize_aws_session") as mock_init:
            with patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailCollector"):
                integration._fetch_fresh_cloudtrail_data()

        mock_init.assert_called_once()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_compliance_item(self, mock_api, mock_mapper):
        """Test creating a compliance item from raw data."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        raw_data = {
            "Name": "test-trail",
            "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
        }

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, CloudTrailComplianceItem)
        assert result.trail_name == "test-trail"

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_assess_compliance(self, mock_api, mock_mapper):
        """Test assessing compliance."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance

        mock_mapper_instance.assess_trail_compliance.return_value = {
            "AU-2": "PASS",
            "AU-3": "FAIL",
        }
        mock_mapper_instance.assess_all_trails_compliance.return_value = {
            "AU-2": "PASS",
            "AU-3": "FAIL",
            "AU-6": "FAIL",
        }

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
        integration.trails = [
            CloudTrailComplianceItem({"Name": "trail-1"}),
            CloudTrailComplianceItem({"Name": "trail-2"}),
        ]

        result = integration._assess_compliance()

        assert "overall" in result
        assert "trails" in result
        assert len(result["trails"]) == 2
        assert result["overall"] == {"AU-2": "PASS", "AU-3": "FAIL", "AU-6": "FAIL"}

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_sync_compliance_data_no_trails(self, mock_api, mock_mapper, caplog):
        """Test sync_compliance_data with no trails."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        with patch.object(integration, "fetch_compliance_data", return_value=[]):
            integration.sync_compliance_data()

        assert "No CloudTrail trail data to sync" in caplog.text

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_sync_compliance_data_with_trails(self, mock_api, mock_mapper):
        """Test sync_compliance_data with trails."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_trail_compliance.return_value = {"AU-2": "PASS"}
        mock_mapper_instance.assess_all_trails_compliance.return_value = {"AU-2": "PASS"}

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, create_evidence=False, create_ssp_attachment=False)

        trail_data = [{"Name": "test-trail"}]

        with patch.object(integration, "fetch_compliance_data", return_value=trail_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        assert len(integration.trails) == 1
        mock_create_evidence.assert_not_called()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_sync_compliance_data_with_evidence(self, mock_api, mock_mapper):
        """Test sync_compliance_data with evidence creation."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_trail_compliance.return_value = {"AU-2": "PASS"}
        mock_mapper_instance.assess_all_trails_compliance.return_value = {"AU-2": "PASS"}

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, create_evidence=True)

        trail_data = [{"Name": "test-trail"}]

        with patch.object(integration, "fetch_compliance_data", return_value=trail_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        mock_create_evidence.assert_called_once()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_evidence_file(self, mock_api, mock_mapper):
        """Test creating evidence file."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")
        integration.trails = [
            CloudTrailComplianceItem(
                {
                    "Name": "test-trail",
                    "TrailARN": "arn:aws:cloudtrail:us-east-1:123456789012:trail/test-trail",
                    "S3BucketName": "test-bucket",
                    "IsMultiRegionTrail": True,
                    "IsOrganizationTrail": False,
                    "LogFileValidationEnabled": True,
                    "KmsKeyId": "test-key",
                    "CloudWatchLogsLogGroupArn": "test-log-group",
                    "SnsTopicARN": "test-topic",
                    "Status": {"IsLogging": True},
                    "EventSelectors": [{"IncludeManagementEvents": True}],
                    "Tags": {"Environment": "Test"},
                }
            )
        ]

        compliance_results = {
            "overall": {"AU-2": "PASS", "AU-3": "FAIL"},
            "trails": [{"trail_name": "test-trail", "controls": {"AU-2": "PASS"}}],
        }

        evidence_file = integration._create_evidence_file(compliance_results)

        assert os.path.exists(evidence_file)
        assert evidence_file.endswith(".jsonl.gz")

        # Verify file contents
        with gzip.open(evidence_file, "rt", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 3  # metadata, summary, trail record

        # Parse and verify metadata
        metadata = json.loads(lines[0])
        assert metadata["type"] == "metadata"
        assert metadata["region"] == "us-east-1"
        assert metadata["account_id"] == "123456789012"
        assert metadata["trail_count"] == 1

        # Parse and verify summary
        summary = json.loads(lines[1])
        assert summary["type"] == "compliance_summary"
        assert summary["results"]["AU-2"] == "PASS"

        # Parse and verify trail record
        trail_record = json.loads(lines[2])
        assert trail_record["type"] == "trail_configuration"
        assert trail_record["trail_name"] == "test-trail"
        assert trail_record["multi_region"] is True

        # Cleanup
        os.remove(evidence_file)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_evidence_file_error(self, mock_api, mock_mapper):
        """Test creating evidence file with error."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)
        integration.trails = []

        compliance_results = {"overall": {}, "trails": []}

        with patch("gzip.open", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                integration._create_evidence_file(compliance_results)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.File")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_ssp_attachment_with_evidence(self, mock_api, mock_mapper, mock_file):
        """Test creating SSP attachment with evidence."""
        mock_file.upload_file_to_regscale.return_value = True

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1")

        # Create temporary evidence file
        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path)

        mock_file.upload_file_to_regscale.assert_called_once()
        call_kwargs = mock_file.upload_file_to_regscale.call_args[1]
        assert call_kwargs["parent_id"] == 123
        assert call_kwargs["parent_module"] == "securityplans"
        assert "cloudtrail_evidence" in call_kwargs["file_name"]
        assert "aws,cloudtrail,audit,logging,compliance,automated" == call_kwargs["tags"]

        # Cleanup
        os.remove(evidence_file_path)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.File")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_ssp_attachment_duplicate_check(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with duplicate check."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-west-2")

        evidence_file_path = "/tmp/test_evidence.jsonl.gz"

        with caplog.at_level(logging.INFO):
            with patch.object(integration, "check_for_existing_evidence", return_value=True):
                integration._create_ssp_attachment_with_evidence(evidence_file_path)

        mock_file.upload_file_to_regscale.assert_not_called()
        assert "already exists for today" in caplog.text

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.File")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_ssp_attachment_upload_failure(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with upload failure."""
        mock_file.upload_file_to_regscale.return_value = False

        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, region="us-east-1")

        # Create temporary evidence file
        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        with caplog.at_level(logging.ERROR):
            with patch.object(integration, "check_for_existing_evidence", return_value=False):
                integration._create_ssp_attachment_with_evidence(evidence_file_path)

        assert "Failed to upload CloudTrail evidence file" in caplog.text

        # Cleanup
        os.remove(evidence_file_path)

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.File")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_ssp_attachment_error_handling(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with error."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123)

        evidence_file_path = "/tmp/nonexistent.jsonl.gz"

        with caplog.at_level(logging.ERROR):
            with patch.object(integration, "check_for_existing_evidence", return_value=False):
                integration._create_ssp_attachment_with_evidence(evidence_file_path)

        assert "Failed to create SSP attachment" in caplog.text

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_evidence_artifacts(self, mock_api, mock_mapper):
        """Test creating evidence artifacts."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.trails = []

        compliance_results = {"overall": {}, "trails": []}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz") as mock_create:
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove") as mock_remove:
                        integration._create_evidence_artifacts(compliance_results)

        mock_create.assert_called_once_with(compliance_results)
        mock_upload.assert_called_once()
        mock_remove.assert_called_once_with("/tmp/test.jsonl.gz")

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_evidence_artifacts_no_ssp_attachment(self, mock_api, mock_mapper):
        """Test creating evidence artifacts without SSP attachment."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, create_ssp_attachment=False)
        integration.trails = []

        compliance_results = {"overall": {}, "trails": []}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz"):
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove"):
                        integration._create_evidence_artifacts(compliance_results)

        mock_upload.assert_not_called()

    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.CloudTrailControlMapper")
    @patch("regscale.integrations.commercial.aws.cloudtrail_evidence.Api")
    def test_create_evidence_artifacts_cleanup(self, mock_api, mock_mapper):
        """Test evidence artifacts cleanup."""
        integration = AWSCloudTrailEvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.trails = []

        compliance_results = {"overall": {}, "trails": []}

        # Create actual temp file to test cleanup
        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name

        with patch.object(integration, "_create_evidence_file", return_value=evidence_file_path):
            with patch.object(integration, "_create_ssp_attachment_with_evidence"):
                integration._create_evidence_artifacts(compliance_results)

        # Verify file was cleaned up
        assert not os.path.exists(evidence_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
