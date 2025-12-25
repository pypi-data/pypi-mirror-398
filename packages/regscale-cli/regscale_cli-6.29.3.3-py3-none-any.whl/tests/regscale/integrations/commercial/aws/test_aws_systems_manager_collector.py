#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Systems Manager resource collector."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.systems_manager import SystemsManagerCollector

logger = logging.getLogger("regscale")

PATH = "regscale.integrations.commercial.aws.inventory.resources.systems_manager"


class TestSystemsManagerCollector:
    """Test suite for AWS Systems Manager resource collector."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_ssm_client(self):
        """Create a mock SSM client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def collector(self, mock_session):
        """Create a SystemsManagerCollector instance."""
        return SystemsManagerCollector(session=mock_session, region="us-east-1", account_id="123456789012")

    @pytest.fixture
    def collector_no_account(self, mock_session):
        """Create a SystemsManagerCollector instance without account_id."""
        return SystemsManagerCollector(session=mock_session, region="us-east-1", account_id=None)

    def test_init_with_account_id(self, mock_session):
        """Test initialization with account ID."""
        collector = SystemsManagerCollector(session=mock_session, region="us-west-2", account_id="123456789012")

        assert collector.session == mock_session
        assert collector.region == "us-west-2"
        assert collector.account_id == "123456789012"

    def test_init_without_account_id(self, mock_session):
        """Test initialization without account ID."""
        collector = SystemsManagerCollector(session=mock_session, region="us-east-1")

        assert collector.session == mock_session
        assert collector.region == "us-east-1"
        assert collector.account_id is None

    @patch(f"{PATH}.SystemsManagerCollector._get_compliance_summary")
    @patch(f"{PATH}.SystemsManagerCollector._list_associations")
    @patch(f"{PATH}.SystemsManagerCollector._list_maintenance_windows")
    @patch(f"{PATH}.SystemsManagerCollector._list_patch_baselines")
    @patch(f"{PATH}.SystemsManagerCollector._list_documents")
    @patch(f"{PATH}.SystemsManagerCollector._list_parameters")
    @patch(f"{PATH}.SystemsManagerCollector._list_managed_instances")
    def test_collect_success(
        self,
        mock_list_instances,
        mock_list_params,
        mock_list_docs,
        mock_list_baselines,
        mock_list_windows,
        mock_list_assocs,
        mock_get_compliance,
        collector,
        mock_ssm_client,
    ):
        """Test successful collection of all Systems Manager resources."""
        collector.session.client.return_value = mock_ssm_client

        mock_list_instances.return_value = [
            {"InstanceId": "i-12345", "PingStatus": "Online"},
            {"InstanceId": "i-67890", "PingStatus": "Online"},
        ]
        mock_list_params.return_value = [{"Name": "/test/param1"}]
        mock_list_docs.return_value = [{"Name": "TestDocument"}]
        mock_list_baselines.return_value = [{"BaselineId": "pb-12345"}]
        mock_list_windows.return_value = [{"WindowId": "mw-12345"}]
        mock_list_assocs.return_value = [{"AssociationId": "assoc-12345"}]
        mock_get_compliance.return_value = {"TotalCompliant": 10, "TotalNonCompliant": 2}

        result = collector.collect()

        assert result["ManagedInstances"] == mock_list_instances.return_value
        assert result["Parameters"] == mock_list_params.return_value
        assert result["Documents"] == mock_list_docs.return_value
        assert result["PatchBaselines"] == mock_list_baselines.return_value
        assert result["MaintenanceWindows"] == mock_list_windows.return_value
        assert result["Associations"] == mock_list_assocs.return_value
        assert result["ComplianceSummary"] == mock_get_compliance.return_value
        assert len(result["ManagedInstances"]) == 2

        collector.session.client.assert_called_once_with("ssm", region_name="us-east-1")
        mock_list_instances.assert_called_once_with(mock_ssm_client)
        mock_list_params.assert_called_once_with(mock_ssm_client)
        mock_list_docs.assert_called_once_with(mock_ssm_client)
        mock_list_baselines.assert_called_once_with(mock_ssm_client)
        mock_list_windows.assert_called_once_with(mock_ssm_client)
        mock_list_assocs.assert_called_once_with(mock_ssm_client)
        mock_get_compliance.assert_called_once_with(mock_ssm_client)

    @patch(f"{PATH}.SystemsManagerCollector._handle_error")
    def test_collect_client_error(self, mock_handle_error, collector, mock_ssm_client):
        """Test collect handles ClientError from _get_client."""
        error = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "CreateClient")
        collector.session.client.side_effect = error

        result = collector.collect()

        assert result["ManagedInstances"] == []
        assert result["Parameters"] == []
        assert result["Documents"] == []
        mock_handle_error.assert_called_once_with(error, "Systems Manager resources")

    @patch(f"{PATH}.logger")
    def test_collect_unexpected_error(self, mock_logger, collector, mock_ssm_client):
        """Test collect handles unexpected errors."""
        collector.session.client.return_value = mock_ssm_client
        error = ValueError("Unexpected error")

        mock_ssm_client.get_paginator.side_effect = error

        result = collector.collect()

        assert result["ManagedInstances"] == []
        assert result["Parameters"] == []
        mock_logger.error.assert_called()
        assert "Unexpected error collecting Systems Manager resources" in str(mock_logger.error.call_args)

    def test_list_managed_instances_success(self, collector, mock_ssm_client):
        """Test successful listing of managed instances with pagination."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        mock_paginator.paginate.return_value = [
            {
                "InstanceInformationList": [
                    {
                        "InstanceId": "i-12345",
                        "PingStatus": "Online",
                        "LastPingDateTime": test_datetime,
                        "AgentVersion": "3.1.0",
                        "IsLatestVersion": True,
                        "PlatformType": "Linux",
                        "PlatformName": "Amazon Linux",
                        "PlatformVersion": "2",
                        "ResourceType": "EC2Instance",
                        "IPAddress": "10.0.1.5",
                        "ComputerName": "test-instance",
                        "AssociationStatus": "Success",
                        "LastAssociationExecutionDate": test_datetime,
                        "LastSuccessfulAssociationExecutionDate": test_datetime,
                    }
                ]
            },
            {
                "InstanceInformationList": [
                    {
                        "InstanceId": "i-67890",
                        "PingStatus": "ConnectionLost",
                        "LastPingDateTime": test_datetime,
                        "AgentVersion": "3.0.0",
                        "PlatformType": "Windows",
                        "PlatformName": "Windows Server",
                        "PlatformVersion": "2019",
                        "ResourceType": "ManagedInstance",
                        "IPAddress": "10.0.1.6",
                        "ComputerName": "windows-server",
                    }
                ]
            },
        ]

        with patch.object(collector, "_get_instance_patches") as mock_get_patches:
            mock_get_patches.side_effect = [
                {"TotalPatches": 10, "Installed": 8, "Missing": 2},
                {"TotalPatches": 15, "Installed": 15, "Missing": 0},
            ]

            result = collector._list_managed_instances(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["InstanceId"] == "i-12345"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["PingStatus"] == "Online"
        assert result[0]["AgentVersion"] == "3.1.0"
        assert result[0]["IsLatestVersion"] is True
        assert result[0]["PatchSummary"]["TotalPatches"] == 10
        assert result[1]["InstanceId"] == "i-67890"
        assert result[1]["PatchSummary"]["TotalPatches"] == 15

        mock_ssm_client.get_paginator.assert_called_once_with("describe_instance_information")
        assert mock_get_patches.call_count == 2

    @patch(f"{PATH}.logger")
    def test_list_managed_instances_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing managed instances with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeInstanceInformation"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_managed_instances(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list managed instances in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_managed_instances_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing managed instances with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "DescribeInstanceInformation"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_managed_instances(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing managed instances" in str(mock_logger.error.call_args)

    def test_get_instance_patches_success(self, collector, mock_ssm_client):
        """Test successful retrieval of instance patches."""
        mock_ssm_client.describe_instance_patches.return_value = {
            "Patches": [
                {"State": "Installed"},
                {"State": "Installed"},
                {"State": "InstalledOther"},
                {"State": "Missing"},
                {"State": "Missing"},
                {"State": "Failed"},
                {"State": "NotApplicable"},
            ]
        }

        result = collector._get_instance_patches(mock_ssm_client, "i-12345")

        assert result["TotalPatches"] == 7
        assert result["Installed"] == 2
        assert result["InstalledOther"] == 1
        assert result["Missing"] == 2
        assert result["Failed"] == 1
        assert result["NotApplicable"] == 1

        mock_ssm_client.describe_instance_patches.assert_called_once_with(InstanceId="i-12345", MaxResults=50)

    def test_get_instance_patches_empty(self, collector, mock_ssm_client):
        """Test instance patches with no patches returned."""
        mock_ssm_client.describe_instance_patches.return_value = {"Patches": []}

        result = collector._get_instance_patches(mock_ssm_client, "i-12345")

        assert result["TotalPatches"] == 0
        assert result["Installed"] == 0
        assert result["Missing"] == 0

    @patch(f"{PATH}.logger")
    def test_get_instance_patches_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test instance patches with access denied error."""
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeInstancePatches"
        )

        mock_ssm_client.describe_instance_patches.side_effect = error

        result = collector._get_instance_patches(mock_ssm_client, "i-12345")

        assert result == {}
        mock_logger.debug.assert_not_called()

    @patch(f"{PATH}.logger")
    def test_get_instance_patches_invalid_instance(self, mock_logger, collector, mock_ssm_client):
        """Test instance patches with invalid instance ID error."""
        error = ClientError(
            {"Error": {"Code": "InvalidInstanceId", "Message": "Invalid instance"}}, "DescribeInstancePatches"
        )

        mock_ssm_client.describe_instance_patches.side_effect = error

        result = collector._get_instance_patches(mock_ssm_client, "i-invalid")

        assert result == {}
        mock_logger.debug.assert_not_called()

    @patch(f"{PATH}.logger")
    def test_get_instance_patches_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test instance patches with other ClientError."""
        error = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "DescribeInstancePatches"
        )

        mock_ssm_client.describe_instance_patches.side_effect = error

        result = collector._get_instance_patches(mock_ssm_client, "i-12345")

        assert result == {}
        mock_logger.debug.assert_called_once()
        assert "Error getting patches for instance i-12345" in str(mock_logger.debug.call_args)

    def test_list_parameters_success(self, collector, mock_ssm_client):
        """Test successful listing of parameters with pagination."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        mock_paginator.paginate.return_value = [
            {
                "Parameters": [
                    {
                        "Name": "/test/param1",
                        "Type": "String",
                        "KeyId": "key-12345",
                        "LastModifiedDate": test_datetime,
                        "Description": "Test parameter 1",
                        "Version": 1,
                        "Tier": "Standard",
                        "Policies": [],
                        "DataType": "text",
                    },
                    {
                        "Name": "/test/param2",
                        "Type": "SecureString",
                        "LastModifiedDate": test_datetime,
                        "Version": 2,
                        "Tier": "Advanced",
                    },
                ]
            }
        ]

        result = collector._list_parameters(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["Name"] == "/test/param1"
        assert result[0]["Type"] == "String"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["KeyId"] == "key-12345"
        assert result[1]["Name"] == "/test/param2"
        assert result[1]["Type"] == "SecureString"

        mock_ssm_client.get_paginator.assert_called_once_with("describe_parameters")

    @patch(f"{PATH}.logger")
    def test_list_parameters_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing parameters with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeParameters"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_parameters(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list parameters in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_parameters_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing parameters with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError({"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "DescribeParameters")

        mock_paginator.paginate.side_effect = error

        result = collector._list_parameters(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing parameters" in str(mock_logger.error.call_args)

    def test_list_documents_with_account_filter(self, collector, mock_ssm_client):
        """Test listing documents with account ID filtering."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "DocumentIdentifiers": [
                    {
                        "Name": "MyDocument",
                        "Owner": "123456789012",
                        "VersionName": "v1",
                        "PlatformTypes": ["Linux"],
                        "DocumentVersion": "1",
                        "DocumentType": "Command",
                        "SchemaVersion": "2.2",
                        "DocumentFormat": "JSON",
                        "TargetType": "/AWS::EC2::Instance",
                        "Tags": [{"Key": "Environment", "Value": "Test"}],
                    },
                    {
                        "Name": "AmazonDocument",
                        "Owner": "Amazon",
                        "PlatformTypes": ["Windows", "Linux"],
                        "DocumentType": "Automation",
                        "SchemaVersion": "0.3",
                        "DocumentFormat": "YAML",
                    },
                    {
                        "Name": "OtherAccountDoc",
                        "Owner": "999999999999",
                        "PlatformTypes": ["Linux"],
                        "DocumentType": "Command",
                    },
                ]
            }
        ]

        result = collector._list_documents(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["Name"] == "MyDocument"
        assert result[0]["Owner"] == "123456789012"
        assert result[0]["Region"] == "us-east-1"
        assert result[1]["Name"] == "AmazonDocument"
        assert result[1]["Owner"] == "Amazon"

        mock_paginator.paginate.assert_called_once_with(Filters=[{"Key": "Owner", "Values": ["123456789012"]}])

    def test_list_documents_without_account_filter(self, collector_no_account, mock_ssm_client):
        """Test listing documents without account ID filtering."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "DocumentIdentifiers": [
                    {
                        "Name": "Document1",
                        "Owner": "123456789012",
                        "PlatformTypes": ["Linux"],
                        "DocumentType": "Command",
                        "SchemaVersion": "2.2",
                        "DocumentFormat": "JSON",
                    }
                ]
            }
        ]

        result = collector_no_account._list_documents(mock_ssm_client)

        assert len(result) == 1
        assert result[0]["Name"] == "Document1"

        mock_paginator.paginate.assert_called_once_with(Filters=[])

    @patch(f"{PATH}.logger")
    def test_list_documents_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing documents with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError({"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListDocuments")

        mock_paginator.paginate.side_effect = error

        result = collector._list_documents(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list documents in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_documents_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing documents with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError({"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "ListDocuments")

        mock_paginator.paginate.side_effect = error

        result = collector._list_documents(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing documents" in str(mock_logger.error.call_args)

    def test_list_patch_baselines_with_account_filter(self, collector, mock_ssm_client):
        """Test listing patch baselines with account ID filtering."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        mock_paginator.paginate.return_value = [
            {
                "BaselineIdentities": [
                    {
                        "BaselineId": "pb-12345",
                        "BaselineName": "MyBaseline",
                        "OperatingSystem": "AMAZON_LINUX_2",
                        "DefaultBaseline": True,
                    },
                    {
                        "BaselineId": "pb-67890",
                        "BaselineName": "WindowsBaseline",
                        "OperatingSystem": "WINDOWS",
                        "DefaultBaseline": False,
                    },
                ]
            }
        ]

        mock_ssm_client.get_patch_baseline.side_effect = [
            {
                "BaselineDescription": "Test baseline for Linux",
                "ApprovalRules": {"PatchRules": [{"PatchFilterGroup": {}}]},
                "ApprovedPatches": ["KB123456"],
                "RejectedPatches": ["KB999999"],
                "CreatedDate": test_datetime,
                "ModifiedDate": test_datetime,
            },
            {
                "BaselineDescription": "Test baseline for Windows",
                "ApprovalRules": {},
                "ApprovedPatches": [],
                "RejectedPatches": [],
                "CreatedDate": test_datetime,
            },
        ]

        result = collector._list_patch_baselines(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["BaselineId"] == "pb-12345"
        assert result[0]["BaselineName"] == "MyBaseline"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["DefaultBaseline"] is True
        assert result[0]["Description"] == "Test baseline for Linux"
        assert result[1]["BaselineId"] == "pb-67890"
        assert result[1]["OperatingSystem"] == "WINDOWS"

        mock_paginator.paginate.assert_called_once_with(Filters=[{"Key": "OWNER", "Values": ["123456789012"]}])
        assert mock_ssm_client.get_patch_baseline.call_count == 2

    def test_list_patch_baselines_without_account_filter(self, collector_no_account, mock_ssm_client):
        """Test listing patch baselines without account ID filtering."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "BaselineIdentities": [
                    {
                        "BaselineId": "pb-12345",
                        "BaselineName": "Baseline1",
                        "OperatingSystem": "AMAZON_LINUX_2",
                    }
                ]
            }
        ]

        mock_ssm_client.get_patch_baseline.return_value = {
            "BaselineDescription": "Test baseline",
            "ApprovalRules": {},
            "ApprovedPatches": [],
            "RejectedPatches": [],
        }

        result = collector_no_account._list_patch_baselines(mock_ssm_client)

        assert len(result) == 1
        assert result[0]["BaselineId"] == "pb-12345"

        mock_paginator.paginate.assert_called_once_with(Filters=[])

    @patch(f"{PATH}.logger")
    def test_list_patch_baselines_baseline_detail_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing patch baselines with error getting baseline details."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "BaselineIdentities": [
                    {"BaselineId": "pb-12345", "BaselineName": "Baseline1", "OperatingSystem": "AMAZON_LINUX_2"},
                    {"BaselineId": "pb-67890", "BaselineName": "Baseline2", "OperatingSystem": "WINDOWS"},
                ]
            }
        ]

        error = ClientError({"Error": {"Code": "DoesNotExistException", "Message": "Not found"}}, "GetPatchBaseline")
        mock_ssm_client.get_patch_baseline.side_effect = error

        result = collector._list_patch_baselines(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_not_called()

    @patch(f"{PATH}.logger")
    def test_list_patch_baselines_baseline_detail_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing patch baselines with access denied getting baseline details."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "BaselineIdentities": [
                    {"BaselineId": "pb-12345", "BaselineName": "Baseline1", "OperatingSystem": "AMAZON_LINUX_2"}
                ]
            }
        ]

        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "GetPatchBaseline"
        )
        mock_ssm_client.get_patch_baseline.side_effect = error

        result = collector._list_patch_baselines(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_not_called()

    @patch(f"{PATH}.logger")
    def test_list_patch_baselines_baseline_detail_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing patch baselines with other error getting baseline details."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "BaselineIdentities": [
                    {"BaselineId": "pb-12345", "BaselineName": "Baseline1", "OperatingSystem": "AMAZON_LINUX_2"}
                ]
            }
        ]

        error = ClientError({"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "GetPatchBaseline")
        mock_ssm_client.get_patch_baseline.side_effect = error

        result = collector._list_patch_baselines(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error getting baseline pb-12345" in str(mock_logger.error.call_args)

    @patch(f"{PATH}.logger")
    def test_list_patch_baselines_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing patch baselines with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribePatchBaselines"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_patch_baselines(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list patch baselines in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_patch_baselines_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing patch baselines with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "DescribePatchBaselines"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_patch_baselines(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing patch baselines" in str(mock_logger.error.call_args)

    def test_list_maintenance_windows_success(self, collector, mock_ssm_client):
        """Test successful listing of maintenance windows with pagination."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        mock_paginator.paginate.return_value = [
            {
                "WindowIdentities": [
                    {
                        "WindowId": "mw-12345",
                        "Name": "PatchWindow",
                        "Description": "Weekly patching window",
                        "Enabled": True,
                        "Duration": 2,
                        "Cutoff": 0,
                        "Schedule": "cron(0 2 ? * SUN *)",
                        "ScheduleTimezone": "America/New_York",
                        "NextExecutionTime": "2024-01-07T02:00:00Z",
                    },
                    {
                        "WindowId": "mw-67890",
                        "Name": "MaintenanceWindow",
                        "Enabled": False,
                        "Duration": 4,
                        "Cutoff": 1,
                        "Schedule": "rate(7 days)",
                    },
                ]
            }
        ]

        result = collector._list_maintenance_windows(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["WindowId"] == "mw-12345"
        assert result[0]["Name"] == "PatchWindow"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["Enabled"] is True
        assert result[0]["Duration"] == 2
        assert result[1]["WindowId"] == "mw-67890"
        assert result[1]["Enabled"] is False

        mock_ssm_client.get_paginator.assert_called_once_with("describe_maintenance_windows")

    @patch(f"{PATH}.logger")
    def test_list_maintenance_windows_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing maintenance windows with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "DescribeMaintenanceWindows"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_maintenance_windows(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list maintenance windows in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_maintenance_windows_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing maintenance windows with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "DescribeMaintenanceWindows"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_maintenance_windows(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing maintenance windows" in str(mock_logger.error.call_args)

    def test_list_associations_success(self, collector, mock_ssm_client):
        """Test successful listing of associations with pagination."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator

        test_datetime = datetime(2024, 1, 1, 12, 0, 0)
        mock_paginator.paginate.return_value = [
            {
                "Associations": [
                    {
                        "AssociationId": "assoc-12345",
                        "AssociationName": "PatchAssociation",
                        "InstanceId": "i-12345",
                        "DocumentVersion": "1",
                        "Targets": [{"Key": "tag:Environment", "Values": ["Production"]}],
                        "LastExecutionDate": test_datetime,
                        "ScheduleExpression": "rate(1 day)",
                        "AssociationVersion": "1",
                    },
                    {
                        "AssociationId": "assoc-67890",
                        "AssociationName": "ConfigureAssociation",
                        "DocumentVersion": "2",
                        "Targets": [],
                        "AssociationVersion": "2",
                    },
                ]
            }
        ]

        result = collector._list_associations(mock_ssm_client)

        assert len(result) == 2
        assert result[0]["AssociationId"] == "assoc-12345"
        assert result[0]["AssociationName"] == "PatchAssociation"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["InstanceId"] == "i-12345"
        assert len(result[0]["Targets"]) == 1
        assert result[1]["AssociationId"] == "assoc-67890"
        assert result[1]["Targets"] == []

        mock_ssm_client.get_paginator.assert_called_once_with("list_associations")

    @patch(f"{PATH}.logger")
    def test_list_associations_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test listing associations with access denied error."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListAssociations"
        )

        mock_paginator.paginate.side_effect = error

        result = collector._list_associations(mock_ssm_client)

        assert result == []
        mock_logger.warning.assert_called_once()
        assert "Access denied to list associations in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_list_associations_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test listing associations with other ClientError."""
        mock_paginator = MagicMock()
        mock_ssm_client.get_paginator.return_value = mock_paginator
        error = ClientError({"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "ListAssociations")

        mock_paginator.paginate.side_effect = error

        result = collector._list_associations(mock_ssm_client)

        assert result == []
        mock_logger.error.assert_called_once()
        assert "Error listing associations" in str(mock_logger.error.call_args)

    def test_get_compliance_summary_success(self, collector, mock_ssm_client):
        """Test successful retrieval of compliance summary."""
        mock_ssm_client.list_compliance_summaries.return_value = {
            "ComplianceSummaryItems": [
                {"ComplianceType": "Patch", "CompliantCount": 50, "NonCompliantCount": 5},
                {"ComplianceType": "Association", "CompliantCount": 30, "NonCompliantCount": 2},
                {"ComplianceType": "Custom:Security", "CompliantCount": 20, "NonCompliantCount": 0},
            ]
        }

        result = collector._get_compliance_summary(mock_ssm_client)

        assert result["TotalCompliant"] == 100
        assert result["TotalNonCompliant"] == 7
        assert len(result["ComplianceTypes"]) == 3
        assert result["ComplianceTypes"][0]["ComplianceType"] == "Patch"
        assert result["ComplianceTypes"][0]["CompliantCount"] == 50
        assert result["ComplianceTypes"][1]["NonCompliantCount"] == 2

        mock_ssm_client.list_compliance_summaries.assert_called_once_with(MaxResults=50)

    def test_get_compliance_summary_empty(self, collector, mock_ssm_client):
        """Test compliance summary with no summaries returned."""
        mock_ssm_client.list_compliance_summaries.return_value = {"ComplianceSummaryItems": []}

        result = collector._get_compliance_summary(mock_ssm_client)

        assert result == {}

    def test_get_compliance_summary_missing_counts(self, collector, mock_ssm_client):
        """Test compliance summary with missing count fields."""
        mock_ssm_client.list_compliance_summaries.return_value = {
            "ComplianceSummaryItems": [
                {"ComplianceType": "Patch"},
                {"ComplianceType": "Association", "CompliantCount": 10},
            ]
        }

        result = collector._get_compliance_summary(mock_ssm_client)

        assert result["TotalCompliant"] == 10
        assert result["TotalNonCompliant"] == 0
        assert result["ComplianceTypes"][0]["CompliantCount"] == 0
        assert result["ComplianceTypes"][0]["NonCompliantCount"] == 0

    @patch(f"{PATH}.logger")
    def test_get_compliance_summary_access_denied(self, mock_logger, collector, mock_ssm_client):
        """Test compliance summary with access denied error."""
        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}}, "ListComplianceSummaries"
        )

        mock_ssm_client.list_compliance_summaries.side_effect = error

        result = collector._get_compliance_summary(mock_ssm_client)

        assert result == {}
        mock_logger.warning.assert_called_once()
        assert "Access denied to get compliance summary in us-east-1" in str(mock_logger.warning.call_args)

    @patch(f"{PATH}.logger")
    def test_get_compliance_summary_other_error(self, mock_logger, collector, mock_ssm_client):
        """Test compliance summary with other ClientError."""
        error = ClientError(
            {"Error": {"Code": "InternalServerError", "Message": "Server error"}}, "ListComplianceSummaries"
        )

        mock_ssm_client.list_compliance_summaries.side_effect = error

        result = collector._get_compliance_summary(mock_ssm_client)

        assert result == {}
        mock_logger.debug.assert_called_once()
        assert "Error getting compliance summary" in str(mock_logger.debug.call_args)
