#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Systems Manager Evidence Integration."""

import gzip
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest

from regscale.integrations.commercial.aws.ssm_evidence import (
    SSMComplianceItem,
    AWSSSMEvidenceIntegration,
)

PATH = "regscale.integrations.commercial.aws.ssm_evidence"


class TestSSMComplianceItem:
    """Test SSMComplianceItem class."""

    def test_init_with_complete_data(self):
        """Test initialization with complete SSM data."""
        ssm_data = {
            "ManagedInstances": [
                {"InstanceId": "i-1234567890abcdef0", "PingStatus": "Online"},
                {"InstanceId": "i-1234567890abcdef1", "PingStatus": "Online"},
            ],
            "Parameters": [{"Name": "param1"}, {"Name": "param2"}],
            "Documents": [{"Name": "doc1"}],
            "PatchBaselines": [{"BaselineId": "pb-123"}],
            "MaintenanceWindows": [{"WindowId": "mw-123"}],
            "Associations": [{"AssociationId": "assoc-123"}],
            "InventoryEntries": [{"TypeName": "AWS:Application"}],
            "ComplianceSummary": {"TotalCompliant": 10, "TotalNonCompliant": 2},
        }

        item = SSMComplianceItem(ssm_data)

        assert len(item.managed_instances) == 2
        assert len(item.parameters) == 2
        assert len(item.documents) == 1
        assert len(item.patch_baselines) == 1
        assert len(item.maintenance_windows) == 1
        assert len(item.associations) == 1
        assert len(item.inventory_entries) == 1
        assert item.compliance_summary["TotalCompliant"] == 10
        assert item.raw_data == ssm_data

    def test_init_with_minimal_data(self):
        """Test initialization with minimal SSM data."""
        ssm_data = {}

        item = SSMComplianceItem(ssm_data)

        assert item.managed_instances == []
        assert item.parameters == []
        assert item.documents == []
        assert item.patch_baselines == []
        assert item.maintenance_windows == []
        assert item.associations == []
        assert item.inventory_entries == []
        assert item.compliance_summary == {}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        ssm_data = {
            "ManagedInstances": [{"InstanceId": "i-123"}],
            "Parameters": [{"Name": "param1"}],
        }

        item = SSMComplianceItem(ssm_data)
        result = item.to_dict()

        assert result == ssm_data
        assert result is item.raw_data


class TestAWSSSMEvidenceIntegration:
    """Test AWSSSMEvidenceIntegration class."""

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_init_with_defaults(self, mock_api, mock_mapper):
        """Test initialization with default parameters."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        assert integration.plan_id == 123
        assert integration.region == "us-east-1"
        assert integration.account_id is None
        assert integration.tags == {}
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
        assert integration.raw_ssm_data == {}
        assert integration.ssm_item is None
        mock_api.assert_called_once()
        mock_mapper.assert_called_once_with(framework="NIST800-53R5")

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_init_with_custom_parameters(self, mock_api, mock_mapper):
        """Test initialization with custom parameters."""
        integration = AWSSSMEvidenceIntegration(
            plan_id=456,
            region="us-west-2",
            account_id="123456789012",
            tags={"Environment": "Production"},
            create_evidence=True,
            create_ssp_attachment=False,
            evidence_control_ids=["CM-2", "CM-6"],
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
        assert integration.create_evidence is True
        assert integration.create_ssp_attachment is False
        assert integration.evidence_control_ids == ["CM-2", "CM-6"]
        assert integration.force_refresh is True
        assert integration.aws_profile == "test-profile"
        assert integration.aws_access_key_id == "AKIATEST"
        assert integration.aws_secret_access_key == "secret"
        assert integration.aws_session_token == "token"

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_file_path(self, mock_api, mock_mapper):
        """Test cache file path generation."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")

        cache_path = integration._get_cache_file_path()

        assert isinstance(cache_path, Path)
        assert cache_path.name == "ssm_data_us-east-1_123456789012.json"
        assert "regscale" in str(cache_path)
        assert "aws_ssm_cache" in str(cache_path)

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_file_path_without_account_id(self, mock_api, mock_mapper):
        """Test cache file path generation without account ID."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-west-2")

        cache_path = integration._get_cache_file_path()

        assert cache_path.name == "ssm_data_us-west-2_default.json"

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_no_cache(self, mock_api, mock_mapper):
        """Test cache validation when cache file doesn't exist."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        cache_file = integration._get_cache_file_path()
        if cache_file.exists():
            cache_file.unlink()

        is_valid = integration._is_cache_valid()

        assert is_valid is False

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_expired(self, mock_api, mock_mapper):
        """Test cache validation when cache is expired."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{}")

        five_hours_ago = datetime.now() - timedelta(hours=5)
        os.utime(cache_file, (five_hours_ago.timestamp(), five_hours_ago.timestamp()))

        is_valid = integration._is_cache_valid()

        assert is_valid is False

        cache_file.unlink()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_is_cache_valid_fresh(self, mock_api, mock_mapper):
        """Test cache validation when cache is fresh."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{}")

        is_valid = integration._is_cache_valid()

        assert is_valid is True

        cache_file.unlink()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_save_cache(self, mock_api, mock_mapper):
        """Test saving data to cache."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        test_data = {"ManagedInstances": [{"InstanceId": "i-123"}]}

        integration._save_cache(test_data)

        assert cache_file.exists()
        with open(cache_file) as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

        cache_file.unlink()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_save_cache_error(self, mock_api, mock_mapper, caplog):
        """Test saving cache with error."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            integration._save_cache({"test": "data"})

        assert "Failed to save cache" in caplog.text

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_load_cached_data(self, mock_api, mock_mapper):
        """Test loading data from cache."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        test_data = {"ManagedInstances": [{"InstanceId": "i-123"}]}

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(test_data, f)

        loaded_data = integration._load_cached_data()

        assert loaded_data == test_data

        cache_file.unlink()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_load_cached_data_error(self, mock_api, mock_mapper, caplog):
        """Test loading cache with error."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        result = integration._load_cached_data()

        assert result is None
        assert "Failed to load cache" in caplog.text

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_age_hours_no_cache(self, mock_api, mock_mapper):
        """Test getting cache age when no cache exists."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        age = integration._get_cache_age_hours()

        assert age == float("inf")

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_get_cache_age_hours_with_cache(self, mock_api, mock_mapper):
        """Test getting cache age with existing cache."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        cache_file = integration._get_cache_file_path()

        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{}")

        two_hours_ago = datetime.now() - timedelta(hours=2)
        os.utime(cache_file, (two_hours_ago.timestamp(), two_hours_ago.timestamp()))

        age = integration._get_cache_age_hours()

        assert 1.9 < age < 2.1

        cache_file.unlink()

    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_with_keys(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with access keys."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSSSMEvidenceIntegration(
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
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_with_profile(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with profile."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1", aws_profile="test-profile")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(profile_name="test-profile", region_name="us-east-1")
        assert integration.session == mock_session

    @patch(f"{PATH}.boto3.Session")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_initialize_aws_session_default(self, mock_api, mock_mapper, mock_boto_session):
        """Test AWS session initialization with default credentials."""
        mock_session = MagicMock()
        mock_boto_session.return_value = mock_session

        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1")

        integration._initialize_aws_session()

        mock_boto_session.assert_called_once_with(region_name="us-east-1")
        assert integration.session == mock_session

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_compliance_data_from_cache(self, mock_api, mock_mapper):
        """Test fetching compliance data from cache."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        cached_data = {"ManagedInstances": [{"InstanceId": "i-123"}]}

        with patch.object(integration, "_is_cache_valid", return_value=True):
            with patch.object(integration, "_load_cached_data", return_value=cached_data):
                result = integration.fetch_compliance_data()

        assert result == cached_data

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_compliance_data_force_refresh(self, mock_api, mock_mapper):
        """Test fetching compliance data with force refresh."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, force_refresh=True)

        fresh_data = {"ManagedInstances": [{"InstanceId": "i-fresh"}]}

        with patch.object(integration, "_fetch_fresh_ssm_data", return_value=fresh_data):
            result = integration.fetch_compliance_data()

        assert result == fresh_data

    @patch(f"{PATH}.SystemsManagerCollector")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_fresh_ssm_data(self, mock_api, mock_mapper, mock_collector_class):
        """Test fetching fresh SSM data."""
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_collector.collect.return_value = {
            "ManagedInstances": [{"InstanceId": "i-1"}, {"InstanceId": "i-2"}],
            "Parameters": [{"Name": "param1"}],
            "Documents": [{"Name": "doc1"}],
            "PatchBaselines": [{"BaselineId": "pb-1"}],
        }

        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1")

        mock_session = MagicMock()
        integration.session = mock_session

        with patch.object(integration, "_save_cache"):
            result = integration._fetch_fresh_ssm_data()

        assert len(result["ManagedInstances"]) == 2
        assert len(result["Parameters"]) == 1
        mock_collector_class.assert_called_once_with(session=mock_session, region="us-east-1", account_id=None, tags={})

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_fetch_fresh_ssm_data_initializes_session(self, mock_api, mock_mapper):
        """Test that fetch_fresh_ssm_data initializes session if needed."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        with patch.object(integration, "_initialize_aws_session") as mock_init:
            with patch(f"{PATH}.SystemsManagerCollector"):
                integration._fetch_fresh_ssm_data()

        mock_init.assert_called_once()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_compliance_item(self, mock_api, mock_mapper):
        """Test creating a compliance item from raw data."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        raw_data = {
            "ManagedInstances": [{"InstanceId": "i-123"}],
            "Parameters": [],
        }

        result = integration.create_compliance_item(raw_data)

        assert isinstance(result, SSMComplianceItem)
        assert len(result.managed_instances) == 1

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_assess_compliance(self, mock_api, mock_mapper):
        """Test assessing compliance."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance

        mock_mapper_instance.assess_ssm_compliance.return_value = {
            "CM-2": "PASS",
            "CM-6": "FAIL",
        }

        integration = AWSSSMEvidenceIntegration(plan_id=123)
        integration.ssm_item = SSMComplianceItem(
            {
                "ManagedInstances": [{"InstanceId": "i-1"}],
                "Parameters": [{"Name": "param1"}],
                "Documents": [{"Name": "doc1"}],
                "PatchBaselines": [{"BaselineId": "pb-1"}],
            }
        )

        result = integration._assess_compliance()

        assert "overall" in result
        assert result["overall"] == {"CM-2": "PASS", "CM-6": "FAIL"}

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_no_data(self, mock_api, mock_mapper, caplog):
        """Test sync_compliance_data with no SSM data."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        with patch.object(integration, "fetch_compliance_data", return_value=None):
            integration.sync_compliance_data()

        assert "No Systems Manager data to sync" in caplog.text

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_with_data(self, mock_api, mock_mapper):
        """Test sync_compliance_data with SSM data."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_ssm_compliance.return_value = {"CM-2": "PASS"}

        integration = AWSSSMEvidenceIntegration(plan_id=123, create_evidence=False, create_ssp_attachment=False)

        ssm_data = {"ManagedInstances": [{"InstanceId": "i-123"}]}

        with patch.object(integration, "fetch_compliance_data", return_value=ssm_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        assert integration.ssm_item is not None
        mock_create_evidence.assert_not_called()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_sync_compliance_data_with_evidence(self, mock_api, mock_mapper):
        """Test sync_compliance_data with evidence creation."""
        mock_mapper_instance = MagicMock()
        mock_mapper.return_value = mock_mapper_instance
        mock_mapper_instance.assess_ssm_compliance.return_value = {"CM-2": "PASS"}

        integration = AWSSSMEvidenceIntegration(plan_id=123, create_evidence=True)

        ssm_data = {"ManagedInstances": [{"InstanceId": "i-123"}]}

        with patch.object(integration, "fetch_compliance_data", return_value=ssm_data):
            with patch.object(integration, "_create_evidence_artifacts") as mock_create_evidence:
                integration.sync_compliance_data()

        mock_create_evidence.assert_called_once()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_file(self, mock_api, mock_mapper):
        """Test creating evidence file."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1", account_id="123456789012")
        integration.ssm_item = SSMComplianceItem(
            {
                "ManagedInstances": [
                    {
                        "InstanceId": "i-123",
                        "PingStatus": "Online",
                        "PlatformName": "Amazon Linux",
                        "AgentVersion": "3.0.0",
                        "PatchSummary": {"InstalledCount": 10},
                    }
                ],
                "Parameters": [{"Name": "param1"}],
                "Documents": [{"Name": "doc1"}],
                "PatchBaselines": [
                    {
                        "BaselineId": "pb-123",
                        "BaselineName": "test-baseline",
                        "OperatingSystem": "AMAZON_LINUX",
                        "DefaultBaseline": True,
                    }
                ],
                "MaintenanceWindows": [
                    {
                        "WindowId": "mw-123",
                        "Name": "test-window",
                        "Enabled": True,
                        "Schedule": "cron(0 2 ? * SUN *)",
                    }
                ],
                "ComplianceSummary": {
                    "TotalCompliant": 10,
                    "TotalNonCompliant": 2,
                    "ComplianceTypes": ["Association", "Patch"],
                },
            }
        )

        compliance_results = {
            "overall": {"CM-2": "PASS", "CM-6": "FAIL"},
        }

        evidence_file = integration._create_evidence_file(compliance_results)

        assert os.path.exists(evidence_file)
        assert evidence_file.endswith(".jsonl.gz")

        with gzip.open(evidence_file, "rt", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) >= 2

        metadata = json.loads(lines[0])
        assert metadata["type"] == "metadata"
        assert metadata["region"] == "us-east-1"
        assert metadata["account_id"] == "123456789012"
        assert metadata["managed_instances_count"] == 1

        summary = json.loads(lines[1])
        assert summary["type"] == "compliance_summary"
        assert summary["results"]["CM-2"] == "PASS"

        os.remove(evidence_file)

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_file_error(self, mock_api, mock_mapper):
        """Test creating evidence file with error."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)
        integration.ssm_item = SSMComplianceItem({})

        compliance_results = {"overall": {}}

        with patch("gzip.open", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                integration._create_evidence_file(compliance_results)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_with_evidence(self, mock_api, mock_mapper, mock_file):
        """Test creating SSP attachment with evidence."""
        mock_file.upload_file_to_regscale.return_value = True

        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1")

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        compliance_results = {"overall": {"CM-2": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        mock_file.upload_file_to_regscale.assert_called_once()
        call_kwargs = mock_file.upload_file_to_regscale.call_args[1]
        assert call_kwargs["parent_id"] == 123
        assert call_kwargs["parent_module"] == "securityplans"
        assert "ssm_evidence" in call_kwargs["file_name"]
        assert "aws,ssm,systems-manager,patch,config,compliance,automated" == call_kwargs["tags"]

        os.remove(evidence_file_path)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_duplicate_check(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with duplicate check."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-west-2")

        evidence_file_path = "/tmp/test_evidence.jsonl.gz"
        compliance_results = {"overall": {"CM-2": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=True):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        mock_file.upload_file_to_regscale.assert_not_called()
        assert "already exists for today" in caplog.text

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_upload_failure(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with upload failure."""
        mock_file.upload_file_to_regscale.return_value = False

        integration = AWSSSMEvidenceIntegration(plan_id=123, region="us-east-1")

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name
            with gzip.open(tmp_file, "wt") as f:
                f.write("{}\n")

        compliance_results = {"overall": {"CM-2": "PASS"}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        assert "Failed to upload Systems Manager evidence file" in caplog.text

        os.remove(evidence_file_path)

    @patch(f"{PATH}.File")
    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_ssp_attachment_error_handling(self, mock_api, mock_mapper, mock_file, caplog):
        """Test creating SSP attachment with error."""
        integration = AWSSSMEvidenceIntegration(plan_id=123)

        evidence_file_path = "/tmp/nonexistent.jsonl.gz"
        compliance_results = {"overall": {}}

        with patch.object(integration, "check_for_existing_evidence", return_value=False):
            integration._create_ssp_attachment_with_evidence(evidence_file_path, compliance_results)

        assert "Failed to create SSP attachment" in caplog.text

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts(self, mock_api, mock_mapper):
        """Test creating evidence artifacts."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.ssm_item = SSMComplianceItem({})

        compliance_results = {"overall": {}}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz") as mock_create:
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove") as mock_remove:
                        integration._create_evidence_artifacts(compliance_results)

        mock_create.assert_called_once_with(compliance_results)
        mock_upload.assert_called_once()
        mock_remove.assert_called_once_with("/tmp/test.jsonl.gz")

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts_no_ssp_attachment(self, mock_api, mock_mapper):
        """Test creating evidence artifacts without SSP attachment."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, create_ssp_attachment=False)
        integration.ssm_item = SSMComplianceItem({})

        compliance_results = {"overall": {}}

        with patch.object(integration, "_create_evidence_file", return_value="/tmp/test.jsonl.gz"):
            with patch.object(integration, "_create_ssp_attachment_with_evidence") as mock_upload:
                with patch("os.path.exists", return_value=True):
                    with patch("os.remove"):
                        integration._create_evidence_artifacts(compliance_results)

        mock_upload.assert_not_called()

    @patch(f"{PATH}.SSMControlMapper")
    @patch(f"{PATH}.Api")
    def test_create_evidence_artifacts_cleanup(self, mock_api, mock_mapper):
        """Test evidence artifacts cleanup."""
        integration = AWSSSMEvidenceIntegration(plan_id=123, create_ssp_attachment=True)
        integration.ssm_item = SSMComplianceItem({})

        compliance_results = {"overall": {}}

        with tempfile.NamedTemporaryFile(suffix=".jsonl.gz", delete=False) as tmp_file:
            evidence_file_path = tmp_file.name

        with patch.object(integration, "_create_evidence_file", return_value=evidence_file_path):
            with patch.object(integration, "_create_ssp_attachment_with_evidence"):
                integration._create_evidence_artifacts(compliance_results)

        assert not os.path.exists(evidence_file_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
