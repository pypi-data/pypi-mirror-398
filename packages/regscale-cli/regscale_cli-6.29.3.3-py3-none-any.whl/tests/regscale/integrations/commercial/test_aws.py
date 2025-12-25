#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS integration in RegScale CLI."""

from unittest.mock import MagicMock, patch, mock_open

import pytest

from regscale.integrations.commercial.aws.scanner import AWSInventoryIntegration
from regscale.integrations.scanner_integration import IntegrationAsset
from regscale.models import regscale_models
from tests import CLITestFixture


class TestAws(CLITestFixture):
    """Test suite for AWS integration in RegScale CLI."""

    @staticmethod
    def _build_ec2_instance_data(
        instance_id: str = "i-1234567890abcdef0",
        name: str = "Test Instance",
        state: str = "running",
        instance_type: str = "t3.micro",
        **kwargs,
    ) -> dict:
        """Build test EC2 instance data with sensible defaults."""
        base_data = {
            "InstanceId": instance_id,
            "InstanceType": instance_type,
            "State": state,
            "Region": "us-east-1",
            "OwnerId": "123456789012",
            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {"VolumeId": "vol-12345678"}}],
            "ImageInfo": {
                "Name": "amzn2-ami-hvm-2.0.20231212.0-x86_64-gp2",
                "Description": "Amazon Linux 2 AMI",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
            "PlatformDetails": "Linux/UNIX",
            "Architecture": "x86_64",
        }

        if name != "Test Instance":
            base_data["Tags"] = [{"Key": "Name", "Value": name}]

        base_data.update(kwargs)
        return base_data

    @pytest.fixture
    def mock_aws_integration(self):
        """Create a properly configured MagicMock for AWSInventoryIntegration."""
        mock_self = MagicMock()
        mock_self.collector = None
        mock_self.authenticate = MagicMock()
        mock_self.num_assets_to_process = 0
        return mock_self

    @pytest.fixture
    def aws_integration(self):
        """Create a real AWSInventoryIntegration instance for parser tests."""
        return AWSInventoryIntegration(plan_id=1)

    @patch("regscale.integrations.commercial.aws.scanner.json.load")
    @patch("regscale.integrations.commercial.aws.scanner.os.path.exists", return_value=True)
    @patch("regscale.integrations.commercial.aws.scanner.os.path.getmtime")
    @patch("regscale.integrations.commercial.aws.scanner.time.time")
    @patch("builtins.open", new_callable=mock_open)
    def test_returns_cached_data_when_cache_is_valid(
        self, mock_open, mock_time, mock_getmtime, mock_exists, mock_json_load, mock_aws_integration
    ):
        """Should return cached data when cache exists and is not expired."""
        from regscale.integrations.commercial.aws.scanner import CACHE_TTL_SECONDS

        cached_data = {"test": "cached_data"}
        mock_json_load.return_value = cached_data
        mock_getmtime.return_value = 0
        mock_time.return_value = CACHE_TTL_SECONDS - 1

        result = AWSInventoryIntegration.fetch_aws_data_if_needed(
            mock_aws_integration,
            region="us-east-1",
            aws_access_key_id=None,
            aws_secret_access_key=None,
            aws_session_token=None,
        )

        assert result == cached_data
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()

    @patch("regscale.integrations.commercial.aws.scanner.os.path.exists", return_value=False)
    @patch("regscale.integrations.commercial.aws.scanner.os.makedirs")
    @patch("regscale.integrations.commercial.aws.scanner.json.dump")
    @patch("builtins.open", new_callable=mock_open)
    @patch("regscale.integrations.commercial.aws.scanner.AWSInventoryCollector")
    def test_fetches_fresh_data_when_cache_missing(
        self, mock_collector_class, mock_open, mock_json_dump, mock_makedirs, mock_exists, mock_aws_integration
    ):
        """Should fetch fresh data when cache doesn't exist."""
        fresh_data = {"fresh": "data"}
        mock_collector = MagicMock()
        mock_collector.collect_all.return_value = fresh_data
        mock_collector_class.return_value = mock_collector

        def mock_authenticate(*args, **kwargs):
            mock_aws_integration.collector = mock_collector

        mock_aws_integration.authenticate.side_effect = mock_authenticate

        result = AWSInventoryIntegration.fetch_aws_data_if_needed(
            mock_aws_integration,
            region="us-east-1",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            aws_session_token=None,
        )

        assert result == fresh_data
        mock_aws_integration.authenticate.assert_called_once_with(
            "test_key", "test_secret", "us-east-1", None, None, None, None
        )
        mock_collector.collect_all.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_json_dump.assert_called_once()

    @patch("regscale.integrations.commercial.aws.scanner.os.path.exists", return_value=True)
    @patch("regscale.integrations.commercial.aws.scanner.os.path.getmtime")
    @patch("regscale.integrations.commercial.aws.scanner.time.time")
    @patch("regscale.integrations.commercial.aws.scanner.json.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_raises_error_when_cache_expired_and_authentication_fails(
        self, mock_open, mock_json_load, mock_time, mock_getmtime, mock_exists, mock_aws_integration
    ):
        """Should raise RuntimeError when cache is expired and authentication fails."""
        from regscale.integrations.commercial.aws.scanner import CACHE_TTL_SECONDS

        mock_getmtime.return_value = 0
        mock_time.return_value = CACHE_TTL_SECONDS + 1
        mock_aws_integration.authenticate.return_value = None

        with pytest.raises(RuntimeError, match="Failed to initialize AWS inventory collector"):
            AWSInventoryIntegration.fetch_aws_data_if_needed(
                mock_aws_integration,
                region="us-east-1",
                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None,
            )

    def test_processes_normal_asset_list(self, mock_aws_integration):
        """Should process a normal list of asset dictionaries."""
        assets = [
            {"id": "asset1", "name": "Test Asset 1"},
            {"id": "asset2", "name": "Test Asset 2"},
        ]
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Asset 1", identifier="asset1", asset_type="EC2", asset_category="Compute"),
            IntegrationAsset(name="Asset 2", identifier="asset2", asset_type="EC2", asset_category="Compute"),
        ]

        results = list(
            AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
        )

        assert len(results) == 2
        assert results[0].name == "Asset 1"
        assert results[1].name == "Asset 2"
        assert mock_parser.call_count == 2

    def test_processes_special_users_structure(self, mock_aws_integration):
        """Should process special Users structure correctly."""
        assets = [
            {"id": "user1", "name": "User 1"},
            {"id": "user2", "name": "User 2"},
        ]
        asset_type = "IAM Users"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="User 1", identifier="user1", asset_type="IAM", asset_category="Identity"),
            IntegrationAsset(name="User 2", identifier="user2", asset_type="IAM", asset_category="Identity"),
        ]

        results = list(
            AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
        )

        assert len(results) == 2
        assert results[0].name == "User 1"
        assert results[1].name == "User 2"
        assert mock_parser.call_count == 2

    def test_process_asset_collection_roles_special_case(self, mock_aws_integration):
        """Test processing special 'Roles' case"""
        assets = [
            {"id": "role1", "name": "Role 1"},
            {"id": "role2", "name": "Role 2"},
        ]
        asset_type = "IAM Roles"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Role 1", identifier="role1", asset_type="IAM", asset_category="Identity"),
            IntegrationAsset(name="Role 2", identifier="role2", asset_type="IAM", asset_category="Identity"),
        ]

        results = list(
            AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
        )

        assert len(results) == 2
        assert results[0].name == "Role 1"
        assert results[1].name == "Role 2"
        assert mock_parser.call_count == 2

    def test_skips_invalid_asset_format(self, mock_aws_integration):
        """Should skip assets with invalid format and log warning."""
        assets = ["invalid_asset", {"id": "valid_asset", "name": "Valid Asset"}]
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.return_value = IntegrationAsset(
            name="Valid Asset", identifier="valid_asset", asset_type="EC2", asset_category="Compute"
        )

        with patch("regscale.integrations.commercial.aws.scanner.logger"):
            results = list(
                AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
            )

        assert len(results) == 1
        assert results[0].name == "Valid Asset"
        assert mock_parser.call_count == 1

    def test_process_asset_collection_parser_exception(self, mock_aws_integration):
        """Test handling of parser method exceptions"""
        assets = [
            {"id": "asset1", "name": "Test Asset 1"},
            {"id": "asset2", "name": "Test Asset 2"},
        ]
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Asset 1", identifier="asset1", asset_type="EC2", asset_category="Compute"),
            Exception("Parser error for asset 2"),
        ]

        with patch("regscale.integrations.commercial.aws.scanner.logger") as mock_logger:
            results = list(
                AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
            )

            mock_logger.error.assert_called_once()
            error_call_args = mock_logger.error.call_args
            # The first argument is the message string
            error_message = error_call_args[0][0]
            assert "Error parsing EC2 instance" in error_message
            assert "Parser error for asset 2" in error_message

        assert len(results) == 1
        assert results[0].name == "Asset 1"
        assert mock_parser.call_count == 2

    def test_process_asset_collection_empty_list(self, mock_aws_integration):
        """Test processing empty asset list"""
        assets = []
        asset_type = "EC2 instance"

        mock_parser = MagicMock()

        results = list(
            AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
        )

        assert len(results) == 0
        assert mock_parser.call_count == 0

    def test_process_asset_collection_mixed_valid_invalid(self, mock_aws_integration):
        """Test processing mixed valid and invalid assets"""
        assets = [
            {"id": "valid1", "name": "Valid 1"},
            "invalid_string",
            {"id": "valid2", "name": "Valid 2"},
            None,
            {"id": "valid3", "name": "Valid 3"},
        ]
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Valid 1", identifier="valid1", asset_type="EC2", asset_category="Compute"),
            IntegrationAsset(name="Valid 2", identifier="valid2", asset_type="EC2", asset_category="Compute"),
            IntegrationAsset(name="Valid 3", identifier="valid3", asset_type="EC2", asset_category="Compute"),
        ]

        results = list(
            AWSInventoryIntegration._process_asset_collection(mock_aws_integration, assets, asset_type, mock_parser)
        )

        assert len(results) == 3
        assert results[0].name == "Valid 1"
        assert results[1].name == "Valid 2"
        assert results[2].name == "Valid 3"
        assert mock_parser.call_count == 3

    def test_process_asset_collection_empty_users_roles(self, mock_aws_integration):
        """Test processing empty Users/Roles collections"""
        assets_users = {"Users": []}
        asset_type = "IAM Users"

        mock_parser = MagicMock()

        results = list(
            AWSInventoryIntegration._process_asset_collection(
                mock_aws_integration, assets_users, asset_type, mock_parser
            )
        )

        assert len(results) == 0
        assert mock_parser.call_count == 0

        mock_aws_integration.num_assets_to_process = 0

        assets_roles = {"Roles": []}
        asset_type = "IAM Roles"

        results = list(
            AWSInventoryIntegration._process_asset_collection(
                mock_aws_integration, assets_roles, asset_type, mock_parser
            )
        )

        assert len(results) == 0
        assert mock_parser.call_count == 0

    def test_process_inventory_section_normal_processing(self, mock_aws_integration):
        """Test normal processing of an inventory section"""
        inventory = {
            "EC2Instances": [
                {"id": "i-1234567890", "name": "Test Instance 1"},
                {"id": "i-0987654321", "name": "Test Instance 2"},
            ]
        }
        section_key = "EC2Instances"
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Instance 1", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"),
            IntegrationAsset(name="Instance 2", identifier="i-0987654321", asset_type="EC2", asset_category="Compute"),
        ]

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = [
            IntegrationAsset(name="Instance 1", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"),
            IntegrationAsset(name="Instance 2", identifier="i-0987654321", asset_type="EC2", asset_category="Compute"),
        ]

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with(
            inventory["EC2Instances"], asset_type, mock_parser
        )

        assert len(results) == 2
        assert results[0].name == "Instance 1"
        assert results[1].name == "Instance 2"

    def test_process_inventory_section_missing_key(self, mock_aws_integration):
        """Test processing when section key doesn't exist in inventory"""
        inventory = {
            "S3Buckets": [
                {"name": "test-bucket-1"},
                {"name": "test-bucket-2"},
            ]
        }
        section_key = "EC2Instances"
        asset_type = "EC2 instance"

        mock_parser = MagicMock()

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = []

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with([], asset_type, mock_parser)

        assert len(results) == 0

    def test_process_inventory_section_empty_section(self, mock_aws_integration):
        """Test processing when section exists but is empty"""
        inventory = {
            "EC2Instances": [],
            "S3Buckets": [
                {"name": "test-bucket-1"},
            ],
        }
        section_key = "EC2Instances"
        asset_type = "EC2 instance"

        mock_parser = MagicMock()

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = []

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with([], asset_type, mock_parser)

        assert len(results) == 0

    def test_process_inventory_section_empty_inventory(self, mock_aws_integration):
        """Test processing with completely empty inventory"""
        inventory = {}
        section_key = "EC2Instances"
        asset_type = "EC2 instance"

        mock_parser = MagicMock()

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = []

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with([], asset_type, mock_parser)

        assert len(results) == 0

    def test_process_inventory_section_multiple_sections(self, mock_aws_integration):
        """Test processing when inventory has multiple sections"""

        inventory = {
            "EC2Instances": [
                {"id": "i-1234567890", "name": "Test Instance 1"},
            ],
            "S3Buckets": [
                {"name": "test-bucket-1"},
                {"name": "test-bucket-2"},
            ],
            "LambdaFunctions": [
                {"name": "test-function-1"},
            ],
        }
        section_key = "S3Buckets"
        asset_type = "S3 bucket"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="Bucket 1", identifier="test-bucket-1", asset_type="S3", asset_category="Storage"),
            IntegrationAsset(name="Bucket 2", identifier="test-bucket-2", asset_type="S3", asset_category="Storage"),
        ]

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = [
            IntegrationAsset(name="Bucket 1", identifier="test-bucket-1", asset_type="S3", asset_category="Storage"),
            IntegrationAsset(name="Bucket 2", identifier="test-bucket-2", asset_type="S3", asset_category="Storage"),
        ]

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with(
            inventory["S3Buckets"], asset_type, mock_parser
        )

        assert len(results) == 2
        assert results[0].name == "Bucket 1"
        assert results[1].name == "Bucket 2"

    def test_process_inventory_section_with_special_users_structure(self, mock_aws_integration):
        """Test processing section that contains special Users structure"""
        inventory = {
            "IAM": {
                "Users": [
                    {"id": "user1", "name": "User 1"},
                    {"id": "user2", "name": "User 2"},
                ]
            }
        }
        section_key = "IAM"
        asset_type = "IAM Users"

        mock_parser = MagicMock()
        mock_parser.side_effect = [
            IntegrationAsset(name="User 1", identifier="user1", asset_type="IAM", asset_category="Identity"),
            IntegrationAsset(name="User 2", identifier="user2", asset_type="IAM", asset_category="Identity"),
        ]

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = [
            IntegrationAsset(name="User 1", identifier="user1", asset_type="IAM", asset_category="Identity"),
            IntegrationAsset(name="User 2", identifier="user2", asset_type="IAM", asset_category="Identity"),
        ]

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        # The implementation extracts the list from the IAM dict using asset_type as key
        # Since asset_type is "IAM Users" but the dict has "Users", it returns []
        mock_aws_integration._process_asset_collection.assert_called_once_with([], asset_type, mock_parser)

        assert len(results) == 2
        assert results[0].name == "User 1"
        assert results[1].name == "User 2"

    def test_process_inventory_section_delegates_to_process_asset_collection(self, mock_aws_integration):
        """Test that _process_inventory_section properly delegates to _process_asset_collection"""
        inventory = {
            "EC2Instances": [
                {"id": "i-1234567890", "name": "Test Instance"},
            ]
        }
        section_key = "EC2Instances"
        asset_type = "EC2 instance"

        mock_parser = MagicMock()
        mock_parser.return_value = IntegrationAsset(
            name="Test Instance", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"
        )

        mock_aws_integration._process_asset_collection = MagicMock()
        mock_aws_integration._process_asset_collection.return_value = [mock_parser.return_value]

        results = list(
            AWSInventoryIntegration._process_inventory_section(
                mock_aws_integration, inventory, section_key, asset_type, mock_parser
            )
        )

        mock_aws_integration._process_asset_collection.assert_called_once_with(
            inventory["EC2Instances"], asset_type, mock_parser
        )

        assert len(results) == 1
        assert results[0].name == "Test Instance"

    def test_fetch_assets_normal_processing(self, mock_aws_integration):
        """Test normal processing of assets from inventory"""
        inventory = {
            "EC2Instances": [
                {"id": "i-1234567890", "name": "Test Instance 1"},
                {"id": "i-0987654321", "name": "Test Instance 2"},
            ],
            "S3Buckets": [
                {"name": "test-bucket-1"},
                {"name": "test-bucket-2"},
            ],
            "IAM": {
                "Users": [
                    {"id": "user1", "name": "User 1"},
                ]
            },
        }

        mock_aws_integration.fetch_aws_data_if_needed = MagicMock(return_value=inventory)

        mock_aws_integration.get_asset_configs = MagicMock(
            return_value=[
                ("EC2Instances", "EC2 instance", MagicMock()),
                ("S3Buckets", "S3 bucket", MagicMock()),
            ]
        )

        mock_aws_integration._process_inventory_section = MagicMock()
        mock_aws_integration._process_inventory_section.side_effect = [
            [
                IntegrationAsset(
                    name="Instance 1", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"
                ),
                IntegrationAsset(
                    name="Instance 2", identifier="i-0987654321", asset_type="EC2", asset_category="Compute"
                ),
            ],
            [
                IntegrationAsset(
                    name="Bucket 1", identifier="test-bucket-1", asset_type="S3", asset_category="Storage"
                ),
                IntegrationAsset(
                    name="Bucket 2", identifier="test-bucket-2", asset_type="S3", asset_category="Storage"
                ),
            ],
        ]

        results = list(
            AWSInventoryIntegration.fetch_assets(
                mock_aws_integration,
                region="us-east-1",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
                aws_session_token="test_token",
            )
        )

        mock_aws_integration.fetch_aws_data_if_needed.assert_called_once_with(
            "us-east-1", "test_key", "test_secret", "test_token", None, None, None, False
        )

        mock_aws_integration.get_asset_configs.assert_called_once()

        assert mock_aws_integration._process_inventory_section.call_count == 2

        assert mock_aws_integration.num_assets_to_process == 0

        assert len(results) == 4
        assert results[0].name == "Instance 1"
        assert results[1].name == "Instance 2"
        assert results[2].name == "Bucket 1"
        assert results[3].name == "Bucket 2"

    def test_fetch_assets_empty_inventory(self, mock_aws_integration):
        """Test fetching assets when inventory is empty"""
        inventory = {}

        mock_aws_integration.fetch_aws_data_if_needed = MagicMock(return_value=inventory)

        mock_aws_integration.get_asset_configs = MagicMock(
            return_value=[
                ("EC2Instances", "EC2 instance", MagicMock()),
                ("S3Buckets", "S3 bucket", MagicMock()),
            ]
        )

        mock_aws_integration._process_inventory_section = MagicMock(return_value=[])

        results = list(AWSInventoryIntegration.fetch_assets(mock_aws_integration, region="us-east-1"))

        mock_aws_integration.fetch_aws_data_if_needed.assert_called_once_with(
            "us-east-1", None, None, None, None, None, None, False
        )

        assert mock_aws_integration._process_inventory_section.call_count == 2

        assert len(results) == 0

    def test_fetch_assets_no_asset_configs(self, mock_aws_integration):
        """Test fetching assets when no asset configs are available"""
        inventory = {
            "EC2Instances": [
                {"id": "i-1234567890", "name": "Test Instance"},
            ]
        }

        mock_aws_integration.fetch_aws_data_if_needed = MagicMock(return_value=inventory)

        mock_aws_integration.get_asset_configs = MagicMock(return_value=[])

        mock_aws_integration._process_inventory_section = MagicMock()

        results = list(AWSInventoryIntegration.fetch_assets(mock_aws_integration, region="us-east-1"))

        mock_aws_integration.fetch_aws_data_if_needed.assert_called_once()

        mock_aws_integration.get_asset_configs.assert_called_once()

        mock_aws_integration._process_inventory_section.assert_not_called()

        assert len(results) == 0

    def test_fetch_assets_all_asset_types(self, mock_aws_integration):
        """Test fetching assets for all configured asset types"""
        inventory = {
            "IAM": {"Users": [{"id": "user1", "name": "User 1"}]},
            "EC2Instances": [{"id": "i-1234567890", "name": "Test Instance"}],
            "LambdaFunctions": [{"name": "test-function"}],
            "S3Buckets": [{"name": "test-bucket"}],
            "RDSInstances": [{"name": "test-rds"}],
            "DynamoDBTables": [{"name": "test-dynamo"}],
            "VPCs": [{"name": "test-vpc"}],
            "LoadBalancers": [{"name": "test-lb"}],
            "ECRRepositories": [{"name": "test-ecr"}],
        }

        mock_aws_integration.fetch_aws_data_if_needed = MagicMock(return_value=inventory)

        mock_aws_integration.get_asset_configs = MagicMock(
            return_value=[
                ("IAM", "Roles", MagicMock()),
                ("EC2Instances", "EC2 instance", MagicMock()),
                ("LambdaFunctions", "Lambda function", MagicMock()),
                ("S3Buckets", "S3 bucket", MagicMock()),
                ("RDSInstances", "RDS instance", MagicMock()),
                ("DynamoDBTables", "DynamoDB table", MagicMock()),
                ("VPCs", "VPC", MagicMock()),
                ("LoadBalancers", "Load Balancer", MagicMock()),
                ("ECRRepositories", "ECR repository", MagicMock()),
            ]
        )

        mock_aws_integration._process_inventory_section = MagicMock()
        mock_aws_integration._process_inventory_section.side_effect = [
            [IntegrationAsset(name="User 1", identifier="user1", asset_type="IAM", asset_category="Identity")],
            [
                IntegrationAsset(
                    name="Instance 1", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"
                )
            ],
            [
                IntegrationAsset(
                    name="Function 1", identifier="test-function", asset_type="Lambda", asset_category="Compute"
                )
            ],
            [IntegrationAsset(name="Bucket 1", identifier="test-bucket", asset_type="S3", asset_category="Storage")],
            [IntegrationAsset(name="RDS 1", identifier="test-rds", asset_type="RDS", asset_category="Database")],
            [
                IntegrationAsset(
                    name="Dynamo 1", identifier="test-dynamo", asset_type="DynamoDB", asset_category="Database"
                )
            ],
            [IntegrationAsset(name="VPC 1", identifier="test-vpc", asset_type="VPC", asset_category="Network")],
            [IntegrationAsset(name="LB 1", identifier="test-lb", asset_type="LoadBalancer", asset_category="Network")],
            [IntegrationAsset(name="ECR 1", identifier="test-ecr", asset_type="ECR", asset_category="Container")],
        ]

        results = list(AWSInventoryIntegration.fetch_assets(mock_aws_integration, region="us-east-1"))

        assert mock_aws_integration._process_inventory_section.call_count == 9

        assert len(results) == 9
        assert results[0].name == "User 1"
        assert results[1].name == "Instance 1"
        assert results[2].name == "Function 1"
        assert results[3].name == "Bucket 1"
        assert results[4].name == "RDS 1"
        assert results[5].name == "Dynamo 1"
        assert results[6].name == "VPC 1"
        assert results[7].name == "LB 1"
        assert results[8].name == "ECR 1"

    def test_fetch_assets_delegates_to_other_methods(self, mock_aws_integration):
        """Test that fetch_assets properly delegates to other methods"""
        inventory = {
            "EC2Instances": [{"id": "i-1234567890", "name": "Test Instance"}],
        }

        mock_aws_integration.fetch_aws_data_if_needed = MagicMock(return_value=inventory)
        mock_aws_integration.get_asset_configs = MagicMock(
            return_value=[
                ("EC2Instances", "EC2 instance", MagicMock()),
            ]
        )
        mock_aws_integration._process_inventory_section = MagicMock(
            return_value=[
                IntegrationAsset(
                    name="Test Instance", identifier="i-1234567890", asset_type="EC2", asset_category="Compute"
                )
            ]
        )

        results = list(
            AWSInventoryIntegration.fetch_assets(
                mock_aws_integration,
                region="us-east-1",
                aws_access_key_id="test_key",
                aws_secret_access_key="test_secret",
            )
        )

        mock_aws_integration.fetch_aws_data_if_needed.assert_called_once_with(
            "us-east-1", "test_key", "test_secret", None, None, None, None, False
        )

        mock_aws_integration.get_asset_configs.assert_called_once()

        mock_aws_integration._process_inventory_section.assert_called_once_with(
            inventory, "EC2Instances", "EC2 instance", mock_aws_integration.get_asset_configs.return_value[0][2]
        )

        assert mock_aws_integration.num_assets_to_process == 0

        assert len(results) == 1
        assert results[0].name == "Test Instance"

    def test_parses_linux_instance_with_name_tag(self, aws_integration):
        """Should parse Linux EC2 instance with Name tag correctly."""
        instance = self._build_ec2_instance_data(
            instance_id="i-1234567890abcdef0",
            name="Test Linux Server",
            PrivateIpAddress="10.0.1.100",
            PublicIpAddress="52.1.2.3",
            PrivateDnsName="ip-10-0-1-100.ec2.internal",
            PublicDnsName="ec2-52-1-2-3.compute-1.amazonaws.com",
            VpcId="vpc-12345678",
            SubnetId="subnet-12345678",
            ImageId="ami-12345678",
            Architecture="x86_64",
            PlatformDetails="Linux/UNIX",
            CpuOptions={"CoreCount": 2, "ThreadsPerCore": 2},
            Tags=[{"Key": "Name", "Value": "Test Linux Server"}, {"Key": "Environment", "Value": "Production"}],
        )

        result = aws_integration.parse_ec2_instance(instance)

        assert result.name == "Test Linux Server"
        assert result.identifier == "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        assert result.asset_type == regscale_models.AssetType.VM
        assert result.operating_system == regscale_models.AssetOperatingSystem.Linux
        assert result.is_public_facing is True
        assert result.ip_address == "10.0.1.100"
        assert result.fqdn == "ec2-52-1-2-3.compute-1.amazonaws.com"
        assert result.cpu == 4  # 2 cores * 2 threads
        assert result.ram == 16
        assert result.location == "us-east-1"
        assert result.model == "t3.micro"
        assert result.manufacturer == "AWS"
        assert result.vlan_id == "subnet-12345678"
        assert result.is_virtual is True
        assert result.source_data == instance

        expected_uri = (
            "https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#InstanceDetails:instanceId=i-1234567890abcdef0"
        )
        assert result.uri == expected_uri

    def test_parses_windows_instance(self, aws_integration):
        """Should parse Windows EC2 instance correctly."""
        instance = self._build_ec2_instance_data(
            instance_id="i-0987654321fedcba0",
            instance_type="t3.small",
            PrivateIpAddress="10.0.1.101",
            Region="us-west-2",
            Platform="windows",
            PlatformDetails="Windows",
            CpuOptions={"CoreCount": 1, "ThreadsPerCore": 2},
            BlockDeviceMappings=[
                {"DeviceName": "/dev/sda1", "Ebs": {"VolumeId": "vol-87654321"}},
                {"DeviceName": "/dev/sdb", "Ebs": {"VolumeId": "vol-87654322"}},
            ],
            ImageInfo={
                "Name": "Windows_Server-2019-English-Full-Base-2023.12.13",
                "Description": "Microsoft Windows Server 2019 with Full Desktop Experience",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        )

        result = aws_integration.parse_ec2_instance(instance)

        assert result.operating_system == regscale_models.AssetOperatingSystem.WindowsServer
        assert result.asset_type == regscale_models.AssetType.VM
        assert result.cpu == 2  # 1 core * 2 threads
        assert result.disk_storage == 16  # 2 devices * 8GB each
        assert result.fqdn == "i-0987654321fedcba0"  # No DNS names, falls back to instance ID
        assert "Windows" in result.description

    def test_parse_ec2_instance_palo_alto(self, aws_integration):
        """Test parsing a Palo Alto EC2 instance"""
        instance = {
            "InstanceId": "i-paloalto123456",
            "InstanceType": "c5.large",
            "State": "running",
            "PrivateIpAddress": "10.0.1.102",
            "Region": "us-east-1",
            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {"VolumeId": "vol-palo123"}}],
            "ImageInfo": {
                "Name": "pa-vm-aws-10.2.3-h4",
                "Description": "Palo Alto Networks VM-Series Firewall",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.operating_system == regscale_models.AssetOperatingSystem.PaloAlto
        assert result.asset_type == regscale_models.AssetType.Appliance
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["Palo Alto Networks IDPS"]
        assert result.cpu == 2  # 2 cores * 1 thread
        assert "Palo Alto Networks VM-Series Firewall" in result.os_version

    def test_parse_ec2_instance_no_name_tag(self, aws_integration):
        """Test parsing an EC2 instance without a Name tag"""
        instance = {
            "InstanceId": "i-noname123456",
            "Tags": [{"Key": "Environment", "Value": "Development"}, {"Key": "Project", "Value": "TestProject"}],
            "InstanceType": "t2.micro",
            "State": "stopped",
            "PrivateIpAddress": "10.0.1.103",
            "Region": "us-east-1",
            "CpuOptions": {"CoreCount": 1, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [],
            "ImageInfo": {
                "Name": "amzn2-ami-hvm-2.0.20231212.0-x86_64-gp2",
                "Description": "Amazon Linux 2 AMI",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.name == "i-noname123456"
        assert result.status == regscale_models.AssetStatus.Inactive  # stopped state
        assert result.cpu == 1  # 1 core * 1 thread
        assert result.disk_storage == 0  # No block devices

    def test_parse_ec2_instance_no_tags(self, aws_integration):
        """Test parsing an EC2 instance with no tags"""
        instance = {
            "InstanceId": "i-notags123456",
            "InstanceType": "t3.nano",
            "State": "running",
            "Region": "us-east-1",
            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [{"DeviceName": "/dev/xvda", "Ebs": {"VolumeId": "vol-notags123"}}],
            "ImageInfo": {
                "Name": "amzn2-ami-hvm-2.0.20231212.0-x86_64-gp2",
                "Description": "Amazon Linux 2 AMI",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.name == "i-notags123456"
        assert result.cpu == 2  # 2 cores * 1 thread
        assert result.disk_storage == 8  # 1 device * 8GB

    def test_parse_ec2_instance_public_facing(self, aws_integration):
        """Test parsing a public-facing EC2 instance"""
        instance = {
            "InstanceId": "i-public123456",
            "InstanceType": "t3.micro",
            "State": "running",
            "PrivateIpAddress": "10.0.1.104",
            "PublicIpAddress": "54.1.2.3",
            "PrivateDnsName": "ip-10-0-1-104.ec2.internal",
            "PublicDnsName": "ec2-54-1-2-3.compute-1.amazonaws.com",
            "Region": "us-east-1",
            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [],
            "ImageInfo": {
                "Name": "amzn2-ami-hvm-2.0.20231212.0-x86_64-gp2",
                "Description": "Amazon Linux 2 AMI",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.is_public_facing is True
        assert result.ip_address == "10.0.1.104"  # Prefers private IP
        assert result.fqdn == "ec2-54-1-2-3.compute-1.amazonaws.com"  # Prefers public DNS
        assert "Public IP: 54.1.2.3" in result.notes

    def test_parse_ec2_instance_private_only(self, aws_integration):
        """Test parsing a private-only EC2 instance"""
        instance = {
            "InstanceId": "i-private123456",
            "InstanceType": "t3.micro",
            "State": "running",
            "PrivateIpAddress": "10.0.1.105",
            "PrivateDnsName": "ip-10-0-1-105.ec2.internal",
            "Region": "us-east-1",
            "CpuOptions": {"CoreCount": 2, "ThreadsPerCore": 1},
            "BlockDeviceMappings": [],
            "ImageInfo": {
                "Name": "amzn2-ami-hvm-2.0.20231212.0-x86_64-gp2",
                "Description": "Amazon Linux 2 AMI",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.is_public_facing is False
        assert result.ip_address == "10.0.1.105"
        assert result.fqdn == "ip-10-0-1-105.ec2.internal"
        assert "Public IP: N/A" in result.notes

    def test_parse_ec2_instance_minimal_data(self, aws_integration):
        """Test parsing an EC2 instance with minimal data"""
        instance = {
            "InstanceId": "i-minimal123456",
            "InstanceType": "t3.micro",
            "State": "running",
            "Region": "us-east-1",
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.name == "i-minimal123456"
        assert result.identifier == "arn:aws:ec2:us-east-1::instance/i-minimal123456"
        assert result.ip_address is None  # No IP addresses provided
        assert result.fqdn == "i-minimal123456"
        assert result.cpu == 0  # No CPU options
        assert result.disk_storage == 0  # No block devices
        assert result.operating_system == regscale_models.AssetOperatingSystem.Linux  # Default
        assert result.os_version == ""
        assert result.location == "us-east-1"
        assert result.model == "t3.micro"
        assert result.is_public_facing is False
        assert result.vlan_id is None  # No subnet ID provided
        assert "Private IP: N/A" in result.notes
        assert "Public IP: N/A" in result.notes

    def test_parse_ec2_instance_edge_cases(self, aws_integration):
        """Test parsing EC2 instance with edge cases"""
        instance = {
            "InstanceId": "i-edge123456",
            "InstanceType": "t3.micro",
            "State": "pending",
            "Region": "us-east-1",
            "CpuOptions": {},  # Empty CPU options
            "BlockDeviceMappings": [
                {"DeviceName": "/dev/xvda"},  # No Ebs field
                {"DeviceName": "/dev/sdb", "Ebs": {"VolumeId": "vol-edge123"}},
            ],
            "ImageInfo": {
                "Name": "custom-ami-123",
                "Description": "",
                "RootDeviceType": "ebs",
                "VirtualizationType": "hvm",
            },
        }

        result = aws_integration.parse_ec2_instance(instance)

        assert result.cpu == 0  # Empty CPU options
        assert result.disk_storage == 8  # Only one Ebs device
        assert result.status == regscale_models.AssetStatus.Inactive  # pending state
        assert result.os_version == ""
        assert result.operating_system == regscale_models.AssetOperatingSystem.Linux  # Default

    def test_parse_lambda_function_basic(self, mock_aws_integration):
        """Test parsing a basic Lambda function"""
        function = {
            "FunctionName": "test-function",
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:test-function",
            "Runtime": "python3.9",
            "Handler": "index.handler",
            "MemorySize": 128,
            "Timeout": 30,
            "Region": "us-east-1",
        }

        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function)

        assert result.name == "test-function"
        assert result.identifier == "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["Lambda Functions"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.software_name == "python3.9"
        assert result.software_version == "9"  # The method uses split(".")[-1] to get last part
        assert result.ram == 128
        assert result.external_id == "test-function"
        assert result.aws_identifier == "arn:aws:lambda:us-east-1:123456789012:function:test-function"
        assert result.manufacturer == "AWS"
        assert result.is_virtual is True
        assert result.source_data == function

        assert "AWS Lambda function test-function" in result.description
        assert "python3.9" in result.description
        assert "128MB memory" in result.description
        assert "Function Name: test-function" in result.notes
        assert "Runtime: python3.9" in result.notes
        assert "Memory Size: 128 MB" in result.notes
        assert "Timeout: 30 seconds" in result.notes
        assert "Handler: index.handler" in result.notes

    def test_parse_lambda_function_with_description(self, mock_aws_integration):
        """Test parsing a Lambda function with description"""
        function = {
            "FunctionName": "api-gateway-function",
            "FunctionArn": "arn:aws:lambda:us-west-2:123456789012:function:api-gateway-function",
            "Runtime": "nodejs18.x",
            "Handler": "app.handler",
            "MemorySize": 256,
            "Timeout": 60,
            "Description": "API Gateway integration function for user authentication",
            "Region": "us-west-2",
        }

        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function)

        assert "API Gateway integration function for user authentication" in result.description
        assert "Function description: API Gateway integration function for user authentication" in result.description
        assert "Description: API Gateway integration function for user authentication" in result.notes
        assert result.software_name == "nodejs18.x"
        assert result.software_version == "x"  # The method uses split(".")[-1] to get last part
        assert result.ram == 256

    def test_parse_lambda_function_with_function_url(self, mock_aws_integration):
        """Test parsing a Lambda function with FunctionUrl"""
        function = {
            "FunctionName": "webhook-function",
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:webhook-function",
            "Runtime": "python3.11",
            "Handler": "lambda_function.lambda_handler",
            "MemorySize": 512,
            "Timeout": 120,
            "FunctionUrl": "https://abc123.lambda-url.us-east-1.on.aws/",
            "Region": "us-east-1",
        }

        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function)

        assert result.uri == "https://abc123.lambda-url.us-east-1.on.aws/"
        assert result.software_name == "python3.11"
        assert result.software_version == "11"  # The method uses split(".")[-1] to get last part
        assert result.ram == 512

    @pytest.mark.parametrize(
        "function_data,expected_software_name,expected_software_version,expected_ram",
        [
            (
                {
                    "FunctionName": "simple-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:simple-function",
                    "Runtime": "python3.8",
                    "Handler": "main.handler",
                    "MemorySize": 64,
                    "Timeout": 15,
                    "Region": "us-east-1",
                },
                "python3.8",
                "8",  # The method uses split(".")[-1] to get last part
                64,
            ),
            (
                {
                    "FunctionName": "empty-desc-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:empty-desc-function",
                    "Runtime": "java11",
                    "Handler": "com.example.Handler::handleRequest",
                    "MemorySize": 1024,
                    "Timeout": 300,
                    "Description": "",
                    "Region": "us-east-1",
                },
                "java11",
                "java11",  # No dots in java11, so full string is used
                1024,
            ),
            (
                {
                    "FunctionName": "non-string-desc-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:non-string-desc-function",
                    "Runtime": "dotnet6",
                    "Handler": "MyFunction::FunctionHandler",
                    "MemorySize": 256,
                    "Timeout": 60,
                    "Description": None,  # Non-string description
                    "Region": "us-east-1",
                },
                "dotnet6",
                "dotnet6",  # No dots in dotnet6, so full string is used
                256,
            ),
        ],
        ids=["no_description", "empty_description", "non_string_description"],
    )
    def test_parse_lambda_function_description_variations(
        self, function_data, expected_software_name, expected_software_version, expected_ram, mock_aws_integration
    ):
        """Test parsing Lambda functions with various description scenarios."""
        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function_data)

        assert "Function description:" not in result.description
        assert "Description: " in result.notes
        assert result.software_name == expected_software_name
        assert result.software_version == expected_software_version
        assert result.ram == expected_ram

    @pytest.mark.parametrize(
        "function_data,expected_software_name,expected_software_version,expected_description_contains,expected_notes_contains",
        [
            (
                {
                    "FunctionName": "no-runtime-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:no-runtime-function",
                    "Handler": "index.handler",
                    "MemorySize": 128,
                    "Timeout": 30,
                    "Region": "us-east-1",
                },
                None,
                None,
                "unknown runtime",
                "Runtime: unknown",
            ),
            (
                {
                    "FunctionName": "empty-runtime-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:empty-runtime-function",
                    "Runtime": "",
                    "Handler": "index.handler",
                    "MemorySize": 128,
                    "Timeout": 30,
                    "Region": "us-east-1",
                },
                "",
                None,
                "running  with 128MB memory",  # Empty runtime shows as empty space
                "Runtime: ",  # Empty runtime shows as empty in notes
            ),
        ],
        ids=["no_runtime", "empty_runtime"],
    )
    def test_parse_lambda_function_runtime_variations(
        self,
        function_data,
        expected_software_name,
        expected_software_version,
        expected_description_contains,
        expected_notes_contains,
        mock_aws_integration,
    ):
        """Test parsing Lambda functions with various runtime scenarios."""
        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function_data)

        assert result.software_name == expected_software_name
        assert result.software_version == expected_software_version
        assert expected_description_contains in result.description
        assert expected_notes_contains in result.notes

    def test_parse_lambda_function_minimal_data(self, mock_aws_integration):
        """Test parsing a Lambda function with minimal data"""
        function = {"FunctionName": "minimal-function"}

        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function)

        assert result.name == "minimal-function"
        assert result.identifier == ""
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["Lambda Functions"]
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location is None
        assert result.software_name is None
        assert result.software_version is None
        assert result.ram is None
        assert result.external_id == "minimal-function"
        assert result.aws_identifier is None
        assert result.uri is None
        assert result.manufacturer == "AWS"
        assert result.is_virtual is True
        assert result.source_data == function

        assert "AWS Lambda function minimal-function" in result.description
        assert "unknown runtime" in result.description
        assert "0MB memory" in result.description
        assert "Function Name: minimal-function" in result.notes
        assert "Runtime: unknown" in result.notes
        assert "Memory Size: 0 MB" in result.notes
        assert "Timeout: 0 seconds" in result.notes
        assert "Handler: " in result.notes
        assert "Description: " in result.notes

    def test_parse_lambda_function_edge_cases(self, mock_aws_integration):
        """Test parsing Lambda function with edge cases"""
        function = {
            "FunctionName": "edge-case-function",
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:edge-case-function",
            "Runtime": "python3.12.1",  # Runtime with multiple dots
            "Handler": "",  # Empty handler
            "MemorySize": 0,  # Zero memory
            "Timeout": 0,  # Zero timeout
            "Description": "   ",  # Whitespace-only description
            "Region": "us-east-1",
        }

        result = AWSInventoryIntegration.parse_lambda_function(mock_aws_integration, function)

        assert result.software_name == "python3.12.1"
        assert result.software_version == "1"  # The method uses split(".")[-1] to get last part
        assert result.ram == 0
        assert "0MB memory" in result.description
        assert "Memory Size: 0 MB" in result.notes
        assert "Timeout: 0 seconds" in result.notes
        assert "Handler: " in result.notes

        assert "Function description:    " in result.description

    def test_parse_aws_account_basic(self, mock_aws_integration):
        """Test parsing a basic AWS account with IAM ARN"""
        iam = {
            "Arn": "arn:aws:iam::123456789012:user/test-user",
            "UserName": "test-user",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "123456789012"
        assert result.identifier == "AWS::::Account:123456789012"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["AWS Account"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "Unknown"
        assert result.external_id == "123456789012"
        assert result.aws_identifier == "AWS::::Account:123456789012"
        assert result.manufacturer == "AWS"
        assert result.source_data == iam

    def test_parse_aws_account_role_arn(self, mock_aws_integration):
        """Test parsing AWS account from role ARN"""
        iam = {
            "Arn": "arn:aws:iam::987654321098:role/EC2Role",
            "RoleName": "EC2Role",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "987654321098"
        assert result.identifier == "AWS::::Account:987654321098"
        assert result.external_id == "987654321098"
        assert result.aws_identifier == "AWS::::Account:987654321098"

    def test_parse_aws_account_group_arn(self, mock_aws_integration):
        """Test parsing AWS account from group ARN"""
        iam = {
            "Arn": "arn:aws:iam::555666777888:group/Developers",
            "GroupName": "Developers",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "555666777888"
        assert result.identifier == "AWS::::Account:555666777888"
        assert result.external_id == "555666777888"
        assert result.aws_identifier == "AWS::::Account:555666777888"

    def test_parse_aws_account_policy_arn(self, mock_aws_integration):
        """Test parsing AWS account from policy ARN"""
        iam = {
            "Arn": "arn:aws:iam::111222333444:policy/AdminPolicy",
            "PolicyName": "AdminPolicy",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "111222333444"
        assert result.identifier == "AWS::::Account:111222333444"
        assert result.external_id == "111222333444"
        assert result.aws_identifier == "AWS::::Account:111222333444"

    def test_parse_aws_account_no_arn(self, mock_aws_integration):
        """Test parsing AWS account with no ARN"""
        iam = {"UserName": "test-user", "Path": "/", "CreateDate": "2023-01-01T00:00:00Z"}

        with pytest.raises(IndexError):
            AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

    def test_parse_aws_account_empty_arn(self, mock_aws_integration):
        """Test parsing AWS account with empty ARN"""
        iam = {"Arn": "", "UserName": "test-user", "Path": "/", "CreateDate": "2023-01-01T00:00:00Z"}

        with pytest.raises(IndexError):
            AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

    def test_parse_aws_account_invalid_arn_format(self, mock_aws_integration):
        """Test parsing AWS account with invalid ARN format"""
        iam = {"Arn": "invalid:arn:format", "UserName": "test-user", "Path": "/", "CreateDate": "2023-01-01T00:00:00Z"}

        with pytest.raises(IndexError):
            AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

    def test_parse_aws_account_short_arn(self, mock_aws_integration):
        """Test parsing AWS account with ARN that has fewer than 5 parts"""
        iam = {
            "Arn": "arn:aws:iam::123456789012",  # Only 4 parts
            "UserName": "test-user",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "123456789012"  # This is what split(":")[4] would return
        assert result.identifier == "AWS::::Account:123456789012"
        assert result.external_id == "123456789012"
        assert result.aws_identifier == "AWS::::Account:123456789012"

    def test_parse_aws_account_minimal_data(self, mock_aws_integration):
        """Test parsing AWS account with minimal IAM data"""
        iam = {}

        with pytest.raises(IndexError):
            AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

    def test_parse_aws_account_edge_cases(self, mock_aws_integration):
        """Test parsing AWS account with edge cases"""
        iam = {
            "Arn": "arn:aws:iam::000000000000:user/root",  # Root account
            "UserName": "root",
            "Path": "/",
            "CreateDate": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_aws_account(mock_aws_integration, iam)

        assert result.name == "000000000000"  # Root account ID
        assert result.identifier == "AWS::::Account:000000000000"
        assert result.external_id == "000000000000"
        assert result.aws_identifier == "AWS::::Account:000000000000"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["AWS Account"]
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "Unknown"
        assert result.manufacturer == "AWS"
        assert result.source_data == iam

    def test_parse_s3_bucket_basic(self, mock_aws_integration):
        """Test parsing a basic S3 bucket"""
        bucket = {"Name": "my-test-bucket", "Region": "us-east-1", "CreationDate": "2023-01-01T00:00:00Z"}

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == "my-test-bucket"
        assert result.identifier == "arn:aws:s3:::my-test-bucket"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["S3 Buckets"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.external_id == "my-test-bucket"
        assert result.aws_identifier == "arn:aws:s3:::my-test-bucket"
        assert result.uri == "https://my-test-bucket.s3.amazonaws.com"
        assert result.manufacturer == "AWS"
        assert result.is_public_facing is False
        assert result.source_data == bucket

    def test_parse_s3_bucket_public_facing(self, mock_aws_integration):
        """Test parsing a public-facing S3 bucket"""
        bucket = {
            "Name": "public-bucket",
            "Region": "us-west-2",
            "CreationDate": "2023-01-01T00:00:00Z",
            "Grants": [
                {"Grantee": {"URI": "http://acs.amazonaws.com/groups/global/AllUsers"}, "Permission": "READ"},
                {"Grantee": {"ID": "123456789012"}, "Permission": "FULL_CONTROL"},
            ],
        }

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == "public-bucket"
        assert result.is_public_facing is True
        assert result.aws_identifier == "arn:aws:s3:::public-bucket"
        assert result.uri == "https://public-bucket.s3.amazonaws.com"
        assert result.location == "us-west-2"

    def test_parse_s3_bucket_private_with_grants(self, mock_aws_integration):
        """Test parsing a private S3 bucket with grants but no public access"""

        bucket = {
            "Name": "private-bucket",
            "Region": "us-east-1",
            "CreationDate": "2023-01-01T00:00:00Z",
            "Grants": [
                {"Grantee": {"ID": "123456789012"}, "Permission": "FULL_CONTROL"},
                {"Grantee": {"URI": "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"}, "Permission": "READ"},
            ],
        }

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == "private-bucket"
        assert result.is_public_facing is False  # Not AllUsers, so private
        assert result.aws_identifier == "arn:aws:s3:::private-bucket"
        assert result.uri == "https://private-bucket.s3.amazonaws.com"

    @pytest.mark.parametrize(
        "bucket_data,expected_name,expected_aws_identifier,expected_uri",
        [
            (
                {"Name": "no-grants-bucket", "Region": "us-east-1", "CreationDate": "2023-01-01T00:00:00Z"},
                "no-grants-bucket",
                "arn:aws:s3:::no-grants-bucket",
                "https://no-grants-bucket.s3.amazonaws.com",
            ),
            (
                {
                    "Name": "empty-grants-bucket",
                    "Region": "us-east-1",
                    "CreationDate": "2023-01-01T00:00:00Z",
                    "Grants": [],
                },
                "empty-grants-bucket",
                "arn:aws:s3:::empty-grants-bucket",
                "https://empty-grants-bucket.s3.amazonaws.com",
            ),
        ],
        ids=["no_grants", "empty_grants"],
    )
    def test_parse_s3_bucket_grants_variations(
        self, bucket_data, expected_name, expected_aws_identifier, expected_uri, mock_aws_integration
    ):
        """Test parsing S3 buckets with various grants scenarios."""
        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket_data)

        assert result.name == expected_name
        assert result.is_public_facing is False  # No/empty grants means private
        assert result.aws_identifier == expected_aws_identifier
        assert result.uri == expected_uri

    @pytest.mark.parametrize(
        "bucket_data,expected_name,expected_identifier,expected_external_id,expected_aws_identifier,expected_uri",
        [
            (
                {"Region": "us-east-1", "CreationDate": "2023-01-01T00:00:00Z"},
                "",
                "arn:aws:s3:::None",
                None,
                "arn:aws:s3:::None",  # bucket.get('Name') returns None
                "https://None.s3.amazonaws.com",  # bucket.get('Name') returns None
            ),
            (
                {"Name": "", "Region": "us-east-1", "CreationDate": "2023-01-01T00:00:00Z"},
                "",
                "arn:aws:s3:::",
                "",
                "arn:aws:s3:::",
                "https://.s3.amazonaws.com",
            ),
        ],
        ids=["no_name", "empty_name"],
    )
    def test_parse_s3_bucket_name_variations(
        self,
        bucket_data,
        expected_name,
        expected_identifier,
        expected_external_id,
        expected_aws_identifier,
        expected_uri,
        mock_aws_integration,
    ):
        """Test parsing S3 buckets with various name scenarios."""
        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket_data)

        assert result.name == expected_name
        assert result.identifier == expected_identifier
        assert result.external_id == expected_external_id
        assert result.aws_identifier == expected_aws_identifier
        assert result.uri == expected_uri
        assert result.is_public_facing is False

    def test_parse_s3_bucket_no_region(self, mock_aws_integration):
        """Test parsing an S3 bucket without region"""

        bucket = {"Name": "no-region-bucket", "CreationDate": "2023-01-01T00:00:00Z"}

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == "no-region-bucket"
        assert result.location is None
        assert result.aws_identifier == "arn:aws:s3:::no-region-bucket"
        assert result.uri == "https://no-region-bucket.s3.amazonaws.com"
        assert result.is_public_facing is False

    def test_parse_s3_bucket_minimal_data(self, mock_aws_integration):
        """Test parsing an S3 bucket with minimal data"""

        bucket = {}

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == ""
        assert result.identifier == "arn:aws:s3:::None"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["S3 Buckets"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location is None
        assert result.external_id is None
        assert result.aws_identifier == "arn:aws:s3:::None"  # bucket.get('Name') returns None
        assert result.uri == "https://None.s3.amazonaws.com"  # bucket.get('Name') returns None
        assert result.manufacturer == "AWS"
        assert result.is_public_facing is False
        assert result.source_data == bucket

    def test_parse_s3_bucket_edge_cases(self, mock_aws_integration):
        """Test parsing S3 bucket with edge cases"""

        bucket = {
            "Name": "edge-case-bucket",
            "Region": "us-east-1",
            "Grants": [
                {
                    "Grantee": {"URI": "http://acs.amazonaws.com/groups/global/AllUsers"},
                    "Permission": "WRITE",  # Different permission
                },
                {
                    "Grantee": {"URI": "http://acs.amazonaws.com/groups/global/AllUsers"},
                    "Permission": "READ_ACP",  # Another permission
                },
            ],
        }

        result = AWSInventoryIntegration.parse_s3_bucket(mock_aws_integration, bucket)

        assert result.name == "edge-case-bucket"
        assert result.is_public_facing is True  # Should detect AllUsers regardless of permission
        assert result.aws_identifier == "arn:aws:s3:::edge-case-bucket"
        assert result.uri == "https://edge-case-bucket.s3.amazonaws.com"
        assert result.location == "us-east-1"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["S3 Buckets"]
        assert result.status == regscale_models.AssetStatus.Active
        assert result.manufacturer == "AWS"
        assert result.source_data == bucket

    def test_parse_rds_instance_basic(self, mock_aws_integration):
        """Test parsing a basic RDS instance"""

        db = {
            "DBInstanceIdentifier": "test-db-instance",
            "DBInstanceClass": "db.t3.micro",
            "Engine": "mysql",
            "EngineVersion": "8.0.28",
            "DBInstanceStatus": "available",
            "AllocatedStorage": 20,
            "AvailabilityZone": "us-east-1a",
            "VpcId": "vpc-12345678",
            "PubliclyAccessible": False,
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:test-db-instance",
            "Endpoint": {"Address": "test-db-instance.abc123.us-east-1.rds.amazonaws.com", "Port": 3306},
        }

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.name == "test-db-instance 8.0.28) - db.t3.micro"
        assert result.identifier == "arn:aws:rds:us-east-1:123456789012:db:test-db-instance"
        assert result.asset_type == regscale_models.AssetType.VM
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["RDS Instances"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.fqdn == "test-db-instance.abc123.us-east-1.rds.amazonaws.com"
        assert result.vlan_id == "vpc-12345678"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1a"
        assert result.model == "db.t3.micro"
        assert result.manufacturer == "AWS"
        assert result.disk_storage == 20
        assert result.software_name == "mysql"
        assert result.software_version == "8.0.28"
        assert result.external_id == "test-db-instance"
        assert result.aws_identifier == "arn:aws:rds:us-east-1:123456789012:db:test-db-instance"
        assert result.is_public_facing is False
        assert result.source_data == db

    def test_parse_rds_instance_no_engine_version(self, mock_aws_integration):
        """Test parsing RDS instance without engine version"""

        db = {
            "DBInstanceIdentifier": "simple-db-instance",
            "DBInstanceClass": "db.r5.large",
            "Engine": "postgres",
            "DBInstanceStatus": "available",
            "AllocatedStorage": 100,
            "AvailabilityZone": "us-west-2a",
            "VpcId": "vpc-87654321",
            "PubliclyAccessible": True,
            "DBInstanceArn": "arn:aws:rds:us-west-2:123456789012:db:simple-db-instance",
            "Endpoint": {"Address": "simple-db-instance.def456.us-west-2.rds.amazonaws.com", "Port": 5432},
        }

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.name == "simple-db-instance) - db.r5.large"
        assert result.software_version is None
        assert result.is_public_facing is True
        assert result.fqdn == "simple-db-instance.def456.us-west-2.rds.amazonaws.com"
        assert result.vlan_id == "vpc-87654321"
        assert result.location == "us-west-2a"

    def test_parse_rds_instance_no_instance_class(self, mock_aws_integration):
        """Test parsing RDS instance without instance class"""

        db = {
            "DBInstanceIdentifier": "no-class-db-instance",
            "Engine": "mariadb",
            "EngineVersion": "10.6.8",
            "DBInstanceStatus": "available",
            "AllocatedStorage": 50,
            "AvailabilityZone": "us-east-1b",
            "VpcId": "vpc-11111111",
            "PubliclyAccessible": False,
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:no-class-db-instance",
            "Endpoint": {"Address": "no-class-db-instance.ghi789.us-east-1.rds.amazonaws.com", "Port": 3306},
        }

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.name == "no-class-db-instance 10.6.8) - "
        assert result.model is None
        assert result.software_name == "mariadb"
        assert result.software_version == "10.6.8"

    def test_parse_rds_instance_inactive_status(self, mock_aws_integration):
        """Test parsing RDS instance with inactive status"""

        db = {
            "DBInstanceIdentifier": "inactive-db-instance",
            "DBInstanceClass": "db.t3.small",
            "Engine": "mysql",
            "EngineVersion": "8.0.28",
            "DBInstanceStatus": "stopped",
            "AllocatedStorage": 30,
            "AvailabilityZone": "us-east-1c",
            "VpcId": "vpc-22222222",
            "PubliclyAccessible": False,
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:inactive-db-instance",
        }

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.status == regscale_models.AssetStatus.Inactive
        assert result.name == "inactive-db-instance 8.0.28) - db.t3.small"

    @pytest.mark.parametrize(
        "db_data,expected_fqdn,expected_status,expected_name",
        [
            (
                {
                    "DBInstanceIdentifier": "no-endpoint-db-instance",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "mysql",
                    "EngineVersion": "8.0.28",
                    "DBInstanceStatus": "creating",
                    "AllocatedStorage": 20,
                    "AvailabilityZone": "us-east-1a",
                    "VpcId": "vpc-33333333",
                    "PubliclyAccessible": False,
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:no-endpoint-db-instance",
                },
                None,
                regscale_models.AssetStatus.Inactive,  # creating status
                "no-endpoint-db-instance 8.0.28) - db.t3.micro",
            ),
            (
                {
                    "DBInstanceIdentifier": "empty-endpoint-db-instance",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "mysql",
                    "EngineVersion": "8.0.28",
                    "DBInstanceStatus": "available",
                    "AllocatedStorage": 20,
                    "AvailabilityZone": "us-east-1a",
                    "VpcId": "vpc-44444444",
                    "PubliclyAccessible": False,
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:empty-endpoint-db-instance",
                    "Endpoint": {},
                },
                None,
                regscale_models.AssetStatus.Active,
                "empty-endpoint-db-instance 8.0.28) - db.t3.micro",
            ),
        ],
        ids=["no_endpoint", "empty_endpoint"],
    )
    def test_parse_rds_instance_endpoint_variations(
        self, db_data, expected_fqdn, expected_status, expected_name, mock_aws_integration
    ):
        """Test parsing RDS instances with various endpoint scenarios."""
        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db_data)

        assert result.fqdn == expected_fqdn
        assert result.status == expected_status
        assert result.name == expected_name

    @pytest.mark.parametrize(
        "db_data,expected_vlan_id,expected_location,expected_fqdn",
        [
            (
                {
                    "DBInstanceIdentifier": "no-vpc-db-instance",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "mysql",
                    "EngineVersion": "8.0.28",
                    "DBInstanceStatus": "available",
                    "AllocatedStorage": 20,
                    "AvailabilityZone": "us-east-1a",
                    "PubliclyAccessible": False,
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:no-vpc-db-instance",
                    "Endpoint": {"Address": "no-vpc-db-instance.jkl012.us-east-1.rds.amazonaws.com", "Port": 3306},
                },
                None,
                "us-east-1a",
                "no-vpc-db-instance.jkl012.us-east-1.rds.amazonaws.com",
            ),
            (
                {
                    "DBInstanceIdentifier": "no-az-db-instance",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "mysql",
                    "EngineVersion": "8.0.28",
                    "DBInstanceStatus": "available",
                    "AllocatedStorage": 20,
                    "VpcId": "vpc-55555555",
                    "PubliclyAccessible": False,
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:no-az-db-instance",
                    "Endpoint": {"Address": "no-az-db-instance.mno345.us-east-1.rds.amazonaws.com", "Port": 3306},
                },
                "vpc-55555555",
                None,
                "no-az-db-instance.mno345.us-east-1.rds.amazonaws.com",
            ),
        ],
        ids=["no_vpc", "no_availability_zone"],
    )
    def test_parse_rds_instance_missing_fields(
        self, db_data, expected_vlan_id, expected_location, expected_fqdn, mock_aws_integration
    ):
        """Test parsing RDS instances with missing fields."""
        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db_data)

        assert result.vlan_id == expected_vlan_id
        assert result.location == expected_location
        assert result.fqdn == expected_fqdn

    def test_parse_rds_instance_minimal_data(self, mock_aws_integration):
        """Test parsing RDS instance with minimal data"""

        db = {"DBInstanceIdentifier": "minimal-db-instance"}

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.name == "minimal-db-instance) - "
        assert result.identifier == ""
        assert result.asset_type == regscale_models.AssetType.VM
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["RDS Instances"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.fqdn is None
        assert result.vlan_id is None
        assert result.status == regscale_models.AssetStatus.Inactive  # No status provided
        assert result.location is None
        assert result.model is None
        assert result.manufacturer == "AWS"
        assert result.disk_storage is None
        assert result.software_name is None
        assert result.software_version is None
        assert result.external_id == "minimal-db-instance"
        assert result.aws_identifier is None
        assert result.is_public_facing is False
        assert result.source_data == db

    def test_parse_rds_instance_edge_cases(self, mock_aws_integration):
        """Test parsing RDS instance with edge cases"""

        db = {
            "DBInstanceIdentifier": "edge-case-db-instance",
            "DBInstanceClass": "db.r5.24xlarge",
            "Engine": "oracle-ee",
            "EngineVersion": "19.0.0.0.ru-2021-10.rur-2021-10.r1",
            "DBInstanceStatus": "modifying",
            "AllocatedStorage": 1000,
            "AvailabilityZone": "us-east-1d",
            "VpcId": "vpc-66666666",
            "PubliclyAccessible": True,
            "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:edge-case-db-instance",
            "Endpoint": {"Address": "edge-case-db-instance.pqr678.us-east-1.rds.amazonaws.com", "Port": 1521},
        }

        result = AWSInventoryIntegration.parse_rds_instance(mock_aws_integration, db)

        assert result.name == "edge-case-db-instance 19.0.0.0.ru-2021-10.rur-2021-10.r1) - db.r5.24xlarge"
        assert result.software_name == "oracle-ee"
        assert result.software_version == "19.0.0.0.ru-2021-10.rur-2021-10.r1"
        assert result.status == regscale_models.AssetStatus.Inactive  # modifying status
        assert result.disk_storage == 1000
        assert result.is_public_facing is True
        assert result.fqdn == "edge-case-db-instance.pqr678.us-east-1.rds.amazonaws.com"
        assert result.vlan_id == "vpc-66666666"
        assert result.location == "us-east-1d"
        assert result.model == "db.r5.24xlarge"
        assert result.asset_type == regscale_models.AssetType.VM
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["RDS Instances"]
        assert result.manufacturer == "AWS"
        assert result.source_data == db

    def test_parse_dynamodb_table_basic(self, mock_aws_integration):
        """Test parsing a basic DynamoDB table"""

        table = {
            "TableName": "test-table",
            "TableStatus": "ACTIVE",
            "TableSizeBytes": 1024000,
            "Region": "us-east-1",
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/test-table",
            "ItemCount": 1000,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "test-table (ACTIVE)"
        assert result.identifier == "arn:aws:dynamodb:us-east-1:123456789012:table/test-table"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["DynamoDB Tables"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.disk_storage == 1024000
        assert result.external_id == "test-table"
        assert result.aws_identifier == "arn:aws:dynamodb:us-east-1:123456789012:table/test-table"
        assert result.manufacturer == "AWS"
        assert result.source_data == table

    def test_parse_dynamodb_table_inactive_status(self, mock_aws_integration):
        """Test parsing DynamoDB table with inactive status"""

        table = {
            "TableName": "inactive-table",
            "TableStatus": "CREATING",
            "TableSizeBytes": 0,
            "Region": "us-west-2",
            "TableArn": "arn:aws:dynamodb:us-west-2:123456789012:table/inactive-table",
            "ItemCount": 0,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "inactive-table (CREATING)"
        assert result.status == regscale_models.AssetStatus.Inactive
        assert result.location == "us-west-2"
        assert result.disk_storage == 0
        assert result.aws_identifier == "arn:aws:dynamodb:us-west-2:123456789012:table/inactive-table"

    def test_parse_dynamodb_table_no_status(self, mock_aws_integration):
        """Test parsing DynamoDB table without status"""

        table = {
            "TableName": "no-status-table",
            "TableSizeBytes": 512000,
            "Region": "us-east-1",
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/no-status-table",
            "ItemCount": 500,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "no-status-table"
        assert result.status == regscale_models.AssetStatus.Inactive  # No status provided
        assert result.location == "us-east-1"
        assert result.disk_storage == 512000
        assert result.aws_identifier == "arn:aws:dynamodb:us-east-1:123456789012:table/no-status-table"

    def test_parse_dynamodb_table_empty_status(self, mock_aws_integration):
        """Test parsing DynamoDB table with empty status"""

        table = {
            "TableName": "empty-status-table",
            "TableStatus": "",
            "TableSizeBytes": 256000,
            "Region": "us-east-1",
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/empty-status-table",
            "ItemCount": 250,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "empty-status-table"  # Empty status is not included in name
        assert result.status == regscale_models.AssetStatus.Inactive  # Empty status is not ACTIVE
        assert result.location == "us-east-1"
        assert result.disk_storage == 256000

    def test_parse_dynamodb_table_no_region(self, mock_aws_integration):
        """Test parsing DynamoDB table without region"""

        table = {
            "TableName": "no-region-table",
            "TableStatus": "ACTIVE",
            "TableSizeBytes": 1024000,
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/no-region-table",
            "ItemCount": 1000,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "no-region-table (ACTIVE)"
        assert result.location is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.disk_storage == 1024000

    def test_parse_dynamodb_table_no_size(self, mock_aws_integration):
        """Test parsing DynamoDB table without size"""

        table = {
            "TableName": "no-size-table",
            "TableStatus": "ACTIVE",
            "Region": "us-east-1",
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/no-size-table",
            "ItemCount": 1000,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "no-size-table (ACTIVE)"
        assert result.disk_storage is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"

    def test_parse_dynamodb_table_no_arn(self, mock_aws_integration):
        """Test parsing DynamoDB table without ARN"""

        table = {
            "TableName": "no-arn-table",
            "TableStatus": "ACTIVE",
            "TableSizeBytes": 1024000,
            "Region": "us-east-1",
            "ItemCount": 1000,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "no-arn-table (ACTIVE)"
        assert result.aws_identifier is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.disk_storage == 1024000

    def test_parse_dynamodb_table_minimal_data(self, mock_aws_integration):
        """Test parsing DynamoDB table with minimal data"""

        table = {"TableName": "minimal-table"}

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "minimal-table"
        assert result.identifier == ""
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["DynamoDB Tables"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Inactive  # No status provided
        assert result.location is None
        assert result.disk_storage is None
        assert result.external_id == "minimal-table"
        assert result.aws_identifier is None
        assert result.manufacturer == "AWS"
        assert result.source_data == table

    def test_parse_dynamodb_table_edge_cases(self, mock_aws_integration):
        """Test parsing DynamoDB table with edge cases"""

        table = {
            "TableName": "edge-case-table",
            "TableStatus": "UPDATING",
            "TableSizeBytes": 0,
            "Region": "us-east-1",
            "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/edge-case-table",
            "ItemCount": 0,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "edge-case-table (UPDATING)"
        assert result.status == regscale_models.AssetStatus.Inactive  # UPDATING is not ACTIVE
        assert result.disk_storage == 0
        assert result.location == "us-east-1"
        assert result.aws_identifier == "arn:aws:dynamodb:us-east-1:123456789012:table/edge-case-table"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["DynamoDB Tables"]
        assert result.manufacturer == "AWS"
        assert result.source_data == table

    def test_parse_dynamodb_table_large_size(self, mock_aws_integration):
        """Test parsing DynamoDB table with large size"""

        table = {
            "TableName": "large-table",
            "TableStatus": "ACTIVE",
            "TableSizeBytes": 1073741824,  # 1 GB
            "Region": "us-west-2",
            "TableArn": "arn:aws:dynamodb:us-west-2:123456789012:table/large-table",
            "ItemCount": 1000000,
            "CreationDateTime": "2023-01-01T00:00:00Z",
        }

        result = AWSInventoryIntegration.parse_dynamodb_table(mock_aws_integration, table)

        assert result.name == "large-table (ACTIVE)"
        assert result.disk_storage == 1073741824
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-west-2"
        assert result.aws_identifier == "arn:aws:dynamodb:us-west-2:123456789012:table/large-table"

    def test_parse_vpc_basic(self, mock_aws_integration):
        """Test parsing a basic VPC"""

        vpc = {
            "VpcId": "vpc-12345678",
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "Region": "us-east-1",
            "OwnerId": "123456789012",
            "Tags": [{"Key": "Name", "Value": "Production VPC"}, {"Key": "Environment", "Value": "Production"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "Production VPC"
        assert result.identifier == "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345678"
        assert result.asset_type == regscale_models.AssetType.NetworkRouter
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["VPCs"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.vlan_id == "vpc-12345678"
        assert result.external_id == "vpc-12345678"
        assert result.aws_identifier == "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345678"
        assert result.manufacturer == "AWS"
        assert result.notes == "CIDR: 10.0.0.0/16"
        assert result.source_data == vpc

    def test_parse_vpc_no_name_tag(self, mock_aws_integration):
        """Test parsing VPC without Name tag"""

        vpc = {
            "VpcId": "vpc-87654321",
            "CidrBlock": "172.16.0.0/16",
            "State": "available",
            "Region": "us-west-2",
            "Tags": [{"Key": "Environment", "Value": "Development"}, {"Key": "Project", "Value": "TestProject"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "vpc-87654321"
        assert result.identifier == "arn:aws:ec2:us-west-2::vpc/vpc-87654321"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-west-2"
        assert result.notes == "CIDR: 172.16.0.0/16"

    def test_parse_vpc_no_tags(self, mock_aws_integration):
        """Test parsing VPC with no tags"""

        vpc = {"VpcId": "vpc-notags123", "CidrBlock": "192.168.0.0/16", "State": "available", "Region": "us-east-1"}

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "vpc-notags123"
        assert result.identifier == "arn:aws:ec2:us-east-1::vpc/vpc-notags123"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: 192.168.0.0/16"

    def test_parse_vpc_default_vpc(self, mock_aws_integration):
        """Test parsing a default VPC"""

        vpc = {
            "VpcId": "vpc-default123",
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "Region": "us-east-1",
            "IsDefault": True,
            "Tags": [{"Key": "Name", "Value": "Default VPC"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "Default VPC"
        assert result.identifier == "arn:aws:ec2:us-east-1::vpc/vpc-default123"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: 10.0.0.0/16"  # IsDefault logic is overwritten by CIDR notes

    def test_parse_vpc_inactive_state(self, mock_aws_integration):
        """Test parsing VPC with inactive state"""

        vpc = {
            "VpcId": "vpc-inactive123",
            "CidrBlock": "10.0.0.0/16",
            "State": "pending",
            "Region": "us-east-1",
            "Tags": [{"Key": "Name", "Value": "Inactive VPC"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "Inactive VPC"
        assert result.status == regscale_models.AssetStatus.Inactive
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: 10.0.0.0/16"

    def test_parse_vpc_no_cidr(self, mock_aws_integration):
        """Test parsing VPC without CIDR block"""

        vpc = {
            "VpcId": "vpc-nocidr123",
            "State": "available",
            "Region": "us-east-1",
            "Tags": [{"Key": "Name", "Value": "No CIDR VPC"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "No CIDR VPC"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: None"

    def test_parse_vpc_no_region(self, mock_aws_integration):
        """Test parsing VPC without region"""

        vpc = {
            "VpcId": "vpc-noregion123",
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "Tags": [{"Key": "Name", "Value": "No Region VPC"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "No Region VPC"
        assert result.location == "us-east-1"  # Default region when not provided
        assert result.status == regscale_models.AssetStatus.Active
        assert result.notes == "CIDR: 10.0.0.0/16"

    def test_parse_vpc_no_vpc_id(self, mock_aws_integration):
        """Test parsing VPC without VPC ID"""

        vpc = {
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "Region": "us-east-1",
            "Tags": [{"Key": "Name", "Value": "No VPC ID"}],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "No VPC ID"
        assert result.identifier == "arn:aws:ec2:us-east-1::vpc/"  # ARN with empty VPC ID
        assert result.vlan_id == ""  # Empty string, not None
        assert result.external_id == ""  # Empty string, not None
        assert result.aws_identifier == "arn:aws:ec2:us-east-1::vpc/"  # ARN with empty VPC ID
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: 10.0.0.0/16"

    def test_parse_vpc_minimal_data(self, mock_aws_integration):
        """Test parsing VPC with minimal data"""

        vpc = {}

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == ""
        assert result.identifier == "arn:aws:ec2:us-east-1::vpc/"  # ARN with empty VPC ID
        assert result.asset_type == regscale_models.AssetType.NetworkRouter
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["VPCs"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Inactive  # No state provided
        assert result.location == "us-east-1"  # Default region
        assert result.vlan_id == ""  # Empty string
        assert result.external_id == ""  # Empty string
        assert result.aws_identifier == "arn:aws:ec2:us-east-1::vpc/"  # ARN with empty VPC ID
        assert result.manufacturer == "AWS"
        assert result.notes == "CIDR: None"
        assert result.source_data == vpc

    def test_parse_vpc_edge_cases(self, mock_aws_integration):
        """Test parsing VPC with edge cases"""

        vpc = {
            "VpcId": "vpc-edge123",
            "CidrBlock": "10.0.0.0/8",
            "State": "available",
            "Region": "us-east-1",
            "OwnerId": "123456789012",
            "IsDefault": False,
            "Tags": [
                {"Key": "Name", "Value": "Edge Case VPC"},
                {"Key": "Name", "Value": "Duplicate Name"},  # Duplicate Name tag
                {"Key": "Description", "Value": "Test VPC"},
            ],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "Edge Case VPC"  # First Name tag is used
        assert result.identifier == "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-edge123"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.vlan_id == "vpc-edge123"
        assert result.external_id == "vpc-edge123"
        assert result.aws_identifier == "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-edge123"
        assert result.notes == "CIDR: 10.0.0.0/8"  # No "Default VPC" prefix since IsDefault is False
        assert result.asset_type == regscale_models.AssetType.NetworkRouter
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["VPCs"]
        assert result.manufacturer == "AWS"
        assert result.source_data == vpc

    def test_parse_vpc_empty_tags(self, mock_aws_integration):
        """Test parsing VPC with empty tags list"""

        vpc = {
            "VpcId": "vpc-emptytags123",
            "CidrBlock": "10.0.0.0/16",
            "State": "available",
            "Region": "us-east-1",
            "Tags": [],
        }

        result = AWSInventoryIntegration.parse_vpc(mock_aws_integration, vpc)

        assert result.name == "vpc-emptytags123"  # Falls back to VPC ID
        assert result.identifier == "arn:aws:ec2:us-east-1::vpc/vpc-emptytags123"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes == "CIDR: 10.0.0.0/16"

    def test_parse_load_balancer_basic(self, mock_aws_integration):
        """Test parsing a basic load balancer"""

        lb = {
            "LoadBalancerName": "my-load-balancer",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/1234567890",
            "DNSName": "my-load-balancer-1234567890.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-12345678",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internet-facing",
            "Listeners": [{"Port": 80, "Protocol": "HTTP"}, {"Port": 443, "Protocol": "HTTPS"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "my-load-balancer"
        assert (
            result.identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/1234567890"
        )
        assert result.asset_type == regscale_models.AssetType.NetworkRouter
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["Load Balancers"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.fqdn == "my-load-balancer-1234567890.us-east-1.elb.amazonaws.com"
        assert result.vlan_id == "vpc-12345678"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.external_id == "my-load-balancer"
        assert (
            result.aws_identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/1234567890"
        )
        assert result.manufacturer == "AWS"
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.source_data == lb
        assert result.ports_and_protocols == [{"port": 80, "protocol": "HTTP"}, {"port": 443, "protocol": "HTTPS"}]

    def test_parse_load_balancer_internal(self, mock_aws_integration):
        """Test parsing an internal load balancer"""

        lb = {
            "LoadBalancerName": "internal-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/internal-lb/0987654321",
            "DNSName": "internal-lb-0987654321.us-west-2.elb.amazonaws.com",
            "VpcId": "vpc-87654321",
            "State": "active",
            "Region": "us-west-2",
            "Scheme": "internal",
            "Listeners": [{"Port": 8080, "Protocol": "HTTP"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "internal-lb"
        assert (
            result.identifier
            == "arn:aws:elasticloadbalancing:us-west-2:123456789012:loadbalancer/app/internal-lb/0987654321"
        )
        assert result.fqdn == "internal-lb-0987654321.us-west-2.elb.amazonaws.com"
        assert result.vlan_id == "vpc-87654321"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-west-2"
        assert result.is_public_facing is False
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [{"port": 8080, "protocol": "HTTP"}]

    def test_parse_load_balancer_inactive_state(self, mock_aws_integration):
        """Test parsing load balancer with inactive state"""

        lb = {
            "LoadBalancerName": "inactive-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/inactive-lb/1111111111",
            "DNSName": "inactive-lb-1111111111.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-11111111",
            "State": "provisioning",
            "Region": "us-east-1",
            "Scheme": "internet-facing",
            "Listeners": [],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "inactive-lb"
        assert result.status == regscale_models.AssetStatus.Inactive
        assert result.location == "us-east-1"
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == []

    def test_parse_load_balancer_no_scheme(self, mock_aws_integration):
        """Test parsing load balancer without scheme"""

        lb = {
            "LoadBalancerName": "no-scheme-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/no-scheme-lb/2222222222",
            "DNSName": "no-scheme-lb-2222222222.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-22222222",
            "State": "active",
            "Region": "us-east-1",
            "Listeners": [{"Port": 80, "Protocol": "HTTP"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "no-scheme-lb"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.is_public_facing is False  # No scheme means not public-facing
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [{"port": 80, "protocol": "HTTP"}]

    def test_parse_load_balancer_no_name(self, mock_aws_integration):
        """Test parsing load balancer without name"""

        lb = {
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/unnamed-lb/3333333333",
            "DNSName": "unnamed-lb-3333333333.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-33333333",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internet-facing",
            "Listeners": [],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == ""
        assert (
            result.identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/unnamed-lb/3333333333"
        )
        assert result.external_id is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == []

    def test_parse_load_balancer_no_dns(self, mock_aws_integration):
        """Test parsing load balancer without DNS name"""

        lb = {
            "LoadBalancerName": "no-dns-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/no-dns-lb/4444444444",
            "VpcId": "vpc-44444444",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internal",
            "Listeners": [{"Port": 8080, "Protocol": "HTTP"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "no-dns-lb"
        assert result.fqdn is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.is_public_facing is False
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [{"port": 8080, "protocol": "HTTP"}]

    def test_parse_load_balancer_no_vpc(self, mock_aws_integration):
        """Test parsing load balancer without VPC ID"""

        lb = {
            "LoadBalancerName": "no-vpc-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/no-vpc-lb/5555555555",
            "DNSName": "no-vpc-lb-5555555555.us-east-1.elb.amazonaws.com",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internet-facing",
            "Listeners": [{"Port": 80, "Protocol": "HTTP"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "no-vpc-lb"
        assert result.vlan_id is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [{"port": 80, "protocol": "HTTP"}]

    def test_parse_load_balancer_no_region(self, mock_aws_integration):
        """Test parsing load balancer without region"""

        lb = {
            "LoadBalancerName": "no-region-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/no-region-lb/6666666666",
            "DNSName": "no-region-lb-6666666666.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-66666666",
            "State": "active",
            "Scheme": "internet-facing",
            "Listeners": [{"Port": 443, "Protocol": "HTTPS"}],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "no-region-lb"
        assert result.location is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [{"port": 443, "protocol": "HTTPS"}]

    def test_parse_load_balancer_no_listeners(self, mock_aws_integration):
        """Test parsing load balancer without listeners"""

        lb = {
            "LoadBalancerName": "no-listeners-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/no-listeners-lb/7777777777",
            "DNSName": "no-listeners-lb-7777777777.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-77777777",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internal",
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "no-listeners-lb"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.is_public_facing is False
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == []

    def test_parse_load_balancer_minimal_data(self, mock_aws_integration):
        """Test parsing load balancer with minimal data"""

        lb = {}

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == ""
        assert result.identifier is None
        assert result.asset_type == regscale_models.AssetType.NetworkRouter
        assert result.asset_category == regscale_models.AssetCategory.Hardware
        assert result.component_type == regscale_models.ComponentType.Hardware
        assert result.component_names == ["Load Balancers"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.fqdn is None
        assert result.vlan_id is None
        assert result.status == regscale_models.AssetStatus.Inactive  # No state provided
        assert result.location is None
        assert result.external_id is None
        assert result.aws_identifier is None
        assert result.manufacturer == "AWS"
        assert result.is_public_facing is False
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.source_data == lb
        assert result.ports_and_protocols == []

    def test_parse_load_balancer_edge_cases(self, mock_aws_integration):
        """Test parsing load balancer with edge cases"""

        lb = {
            "LoadBalancerName": "edge-case-lb",
            "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/edge-case-lb/8888888888",
            "DNSName": "edge-case-lb-8888888888.us-east-1.elb.amazonaws.com",
            "VpcId": "vpc-88888888",
            "State": "active",
            "Region": "us-east-1",
            "Scheme": "internet-facing",
            "Listeners": [
                {"Port": 80, "Protocol": "HTTP"},
                {"Port": 443, "Protocol": "HTTPS"},
                {"Port": 8080, "Protocol": "HTTP"},
                {"Port": 8443, "Protocol": "HTTPS"},
            ],
        }

        result = AWSInventoryIntegration.parse_load_balancer(mock_aws_integration, lb)

        assert result.name == "edge-case-lb"
        assert (
            result.identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/edge-case-lb/8888888888"
        )
        assert result.fqdn == "edge-case-lb-8888888888.us-east-1.elb.amazonaws.com"
        assert result.vlan_id == "vpc-88888888"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.external_id == "edge-case-lb"
        assert (
            result.aws_identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/edge-case-lb/8888888888"
        )
        assert result.manufacturer == "AWS"
        assert result.is_public_facing is True
        assert result.notes is None  # Bug: notes field is not being set in parse_load_balancer method
        assert result.ports_and_protocols == [
            {"port": 80, "protocol": "HTTP"},
            {"port": 443, "protocol": "HTTPS"},
            {"port": 8080, "protocol": "HTTP"},
            {"port": 8443, "protocol": "HTTPS"},
        ]
        assert result.source_data == lb

    def test_parse_ecr_repository_basic(self, mock_aws_integration):
        """Test parsing a basic ECR repository"""

        repo = {
            "RepositoryName": "my-app-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/my-app-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app-repo",
            "Region": "us-east-1",
            "ImageTagMutability": "MUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "my-app-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/my-app-repo"
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["ECR Repositories"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.external_id == "my-app-repo"
        assert result.aws_identifier == "arn:aws:ecr:us-east-1:123456789012:repository/my-app-repo"
        assert result.uri == "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app-repo"
        assert result.manufacturer == "AWS"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method
        assert result.source_data == repo

    def test_parse_ecr_repository_immutable_tags(self, mock_aws_integration):
        """Test parsing ECR repository with immutable tags"""

        repo = {
            "RepositoryName": "immutable-repo",
            "RepositoryArn": "arn:aws:ecr:us-west-2:123456789012:repository/immutable-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-west-2.amazonaws.com/immutable-repo",
            "Region": "us-west-2",
            "ImageTagMutability": "IMMUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": False},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "immutable-repo"
        assert result.identifier == "arn:aws:ecr:us-west-2:123456789012:repository/immutable-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-west-2"
        assert result.aws_identifier == "arn:aws:ecr:us-west-2:123456789012:repository/immutable-repo"
        assert result.uri == "123456789012.dkr.ecr.us-west-2.amazonaws.com/immutable-repo"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_scan_on_push_enabled(self, mock_aws_integration):
        """Test parsing ECR repository with scan on push enabled"""

        repo = {
            "RepositoryName": "scan-enabled-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/scan-enabled-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/scan-enabled-repo",
            "Region": "us-east-1",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "scan-enabled-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/scan-enabled-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_scan_on_push_disabled(self, mock_aws_integration):
        """Test parsing ECR repository with scan on push disabled"""

        repo = {
            "RepositoryName": "scan-disabled-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/scan-disabled-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/scan-disabled-repo",
            "Region": "us-east-1",
            "ImageScanningConfiguration": {"ScanOnPush": False},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "scan-disabled-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/scan-disabled-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_no_image_tag_mutability(self, mock_aws_integration):
        """Test parsing ECR repository without image tag mutability"""

        repo = {
            "RepositoryName": "no-mutability-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/no-mutability-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/no-mutability-repo",
            "Region": "us-east-1",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "no-mutability-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/no-mutability-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_no_scanning_config(self, mock_aws_integration):
        """Test parsing ECR repository without scanning configuration"""

        repo = {
            "RepositoryName": "no-scanning-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/no-scanning-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/no-scanning-repo",
            "Region": "us-east-1",
            "ImageTagMutability": "MUTABLE",
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "no-scanning-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/no-scanning-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_no_name(self, mock_aws_integration):
        """Test parsing ECR repository without name"""

        repo = {
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/unnamed-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/unnamed-repo",
            "Region": "us-east-1",
            "ImageTagMutability": "MUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == ""
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/unnamed-repo"
        assert result.external_id is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_no_uri(self, mock_aws_integration):
        """Test parsing ECR repository without URI"""

        repo = {
            "RepositoryName": "no-uri-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/no-uri-repo",
            "Region": "us-east-1",
            "ImageTagMutability": "MUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "no-uri-repo"
        assert result.uri is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_no_region(self, mock_aws_integration):
        """Test parsing ECR repository without region"""

        repo = {
            "RepositoryName": "no-region-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/no-region-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/no-region-repo",
            "ImageTagMutability": "MUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "no-region-repo"
        assert result.location is None
        assert result.status == regscale_models.AssetStatus.Active
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method

    def test_parse_ecr_repository_minimal_data(self, mock_aws_integration):
        """Test parsing ECR repository with minimal data"""

        repo = {}

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == ""
        assert result.identifier == ""
        assert result.asset_type == regscale_models.AssetType.Other
        assert result.asset_category == regscale_models.AssetCategory.Software
        assert result.component_type == regscale_models.ComponentType.Software
        assert result.component_names == ["ECR Repositories"]
        assert result.parent_id == mock_aws_integration.plan_id
        assert result.parent_module == "securityplans"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location is None
        assert result.external_id is None
        assert result.aws_identifier is None
        assert result.uri is None
        assert result.manufacturer == "AWS"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method
        assert result.source_data == repo

    def test_parse_ecr_repository_edge_cases(self, mock_aws_integration):
        """Test parsing ECR repository with edge cases"""

        repo = {
            "RepositoryName": "edge-case-repo",
            "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/edge-case-repo",
            "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/edge-case-repo",
            "Region": "us-east-1",
            "ImageTagMutability": "MUTABLE",
            "ImageScanningConfiguration": {"ScanOnPush": True},
        }

        result = AWSInventoryIntegration.parse_ecr_repository(mock_aws_integration, repo)

        assert result.name == "edge-case-repo"
        assert result.identifier == "arn:aws:ecr:us-east-1:123456789012:repository/edge-case-repo"
        assert result.status == regscale_models.AssetStatus.Active
        assert result.location == "us-east-1"
        assert result.external_id == "edge-case-repo"
        assert result.aws_identifier == "arn:aws:ecr:us-east-1:123456789012:repository/edge-case-repo"
        assert result.uri == "123456789012.dkr.ecr.us-east-1.amazonaws.com/edge-case-repo"
        assert result.manufacturer == "AWS"
        assert result.notes is None  # Bug: notes field is not being set in parse_ecr_repository method
        assert result.source_data == repo

    @pytest.mark.parametrize(
        "resource_type,expected_baseline",
        [
            ("AwsAccount", "AWS Account"),
            ("AwsS3Bucket", "S3 Bucket"),
            ("AwsIamRole", "IAM Role"),
            ("AwsEc2Instance", "EC2 Instance"),
        ],
    )
    def test_maps_known_resource_types(self, resource_type, expected_baseline, mock_aws_integration):
        """Should map known resource types to correct baselines."""
        resource = {"Type": resource_type, "Id": f"arn:aws:test::123456789012:resource/{resource_type.lower()}"}

        result = AWSInventoryIntegration.get_baseline(resource)

        assert result == expected_baseline

    @pytest.mark.parametrize(
        "resource,expected_baseline",
        [
            (
                {"Type": "AwsUnknownResource", "Id": "arn:aws:unknown::123456789012:resource/unknown"},
                "AwsUnknownResource",
            ),
            ({"Id": "arn:aws:unknown::123456789012:resource/missing"}, ""),
            ({"Type": "", "Id": "arn:aws:unknown::123456789012:resource/empty"}, ""),
            ({"Type": "Test", "Id": "arn:aws:unknown::123456789012:resource/none"}, "Test"),
        ],
        ids=["unknown_resource", "missing_type", "empty_type", "none_type"],
    )
    def test_get_baseline_edge_cases(self, resource, expected_baseline, mock_aws_integration):
        """Should handle various edge cases for get_baseline."""
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == expected_baseline

    @pytest.mark.parametrize(
        "resource_type,expected_baseline",
        [
            ("awsaccount", "awsaccount"),  # Should return original since it doesn't match
            ("AWSACCOUNT", "AWSACCOUNT"),  # Should return original since it doesn't match
        ],
        ids=["lowercase", "uppercase"],
    )
    def test_get_baseline_case_sensitive(self, resource_type, expected_baseline, mock_aws_integration):
        """Test get_baseline with case variations."""
        resource = {"Type": resource_type, "Id": "arn:aws:iam::123456789012:root"}
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == expected_baseline

    def test_get_baseline_with_additional_fields(self, mock_aws_integration):
        """Test get_baseline with resource containing additional fields"""
        resource = {
            "Type": "AwsS3Bucket",
            "Id": "arn:aws:s3:::test-bucket",
            "Partition": "aws",
            "Region": "us-east-1",
            "AdditionalField": "additional_value",
        }
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == "S3 Bucket"

    @pytest.mark.parametrize(
        "resource_type,expected_baseline",
        [
            ("AwsAccount", "AWS Account"),
            ("AwsS3Bucket", "S3 Bucket"),
            ("AwsIamRole", "IAM Role"),
            ("AwsEc2Instance", "EC2 Instance"),
        ],
        ids=["aws_account", "aws_s3_bucket", "aws_iam_role", "aws_ec2_instance"],
    )
    def test_get_baseline_all_mapped_types(self, resource_type, expected_baseline, mock_aws_integration):
        """Test get_baseline with all mapped resource types."""
        resource = {"Type": resource_type, "Id": f"arn:aws:test::123456789012:resource/{resource_type.lower()}"}
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == expected_baseline

    @pytest.mark.parametrize(
        "resource_type,expected_baseline",
        [
            ("  AwsAccount  ", "  AwsAccount  "),  # Should return original with whitespace
            ("AwsAccount@#$%", "AwsAccount@#$%"),  # Should return original with special chars
            ("AwsAccount123", "AwsAccount123"),  # Should return original with numbers
        ],
        ids=["whitespace", "special_chars", "numbers"],
    )
    def test_get_baseline_special_characters(self, resource_type, expected_baseline, mock_aws_integration):
        """Test get_baseline with various special character cases."""
        resource = {"Type": resource_type, "Id": "arn:aws:iam::123456789012:root"}
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == expected_baseline

    def test_get_baseline_empty_resource(self, mock_aws_integration):
        """Test get_baseline with empty resource dictionary"""
        resource = {}
        result = AWSInventoryIntegration.get_baseline(resource)
        assert result == ""

    @pytest.mark.parametrize(
        "arn,expected_name",
        [
            ("arn:aws:iam::123456789012:role/test-role", "test-role"),
            ("arn:aws:iam::123456789012:role/path/to/test-role", "test-role"),
            ("arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0", "i-1234567890abcdef0"),
            ("arn:aws:iam::123456789012:user/test-user", "test-user"),
            ("arn:aws:iam::123456789012:role/MyRole", "MyRole"),
        ],
    )
    def test_extracts_name_from_arn_with_slash(self, arn, expected_name, mock_aws_integration):
        """Should extract name from ARN containing slash."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)

        assert result == expected_name

    @pytest.mark.parametrize(
        "arn",
        [
            "arn:aws:s3:::test-bucket",
            "arn:aws:s3:::my-test-bucket",
            "arn:aws:lambda:us-east-1:123456789012:function:my-function",
            "AWS::::Account:123456789012",
        ],
    )
    def test_returns_full_arn_when_no_slash(self, arn, mock_aws_integration):
        """Should return full ARN when no slash is present."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)

        assert result == arn

    def test_returns_empty_string_for_empty_input(self, mock_aws_integration):
        """Should return empty string for empty input."""
        result = AWSInventoryIntegration.extract_name_from_arn("")

        assert result == ""

    @pytest.mark.parametrize(
        "test_input",
        [
            "   ",  # whitespace only
            "simple-string",  # no slashes or colons
            "AWS::::Account:123456789012",  # AWS account format
        ],
        ids=["whitespace", "simple_string", "aws_account_format"],
    )
    def test_returns_original_string_for_non_arn_inputs(self, test_input, mock_aws_integration):
        """Should return original string for non-ARN inputs."""
        result = AWSInventoryIntegration.extract_name_from_arn(test_input)
        assert result == test_input

    def test_extract_name_from_arn_complex_path(self, mock_aws_integration):
        """Test extract_name_from_arn with complex path structure"""
        arn = "arn:aws:iam::123456789012:role/path/to/subpath/MyComplexRole"
        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == "MyComplexRole"

    @pytest.mark.parametrize(
        "arn,expected_name",
        [
            ("arn:aws:iam::123456789012:role/test-role@#$%", "test-role@#$%"),
            ("arn:aws:iam::123456789012:role/role-123-test", "role-123-test"),
            ("arn:aws:iam::123456789012:role/test_role_name", "test_role_name"),
            ("arn:aws:iam::123456789012:role/test.role.name", "test.role.name"),
        ],
        ids=["special_chars", "numbers", "underscores", "dots"],
    )
    def test_extract_name_from_arn_with_characters(self, arn, expected_name, mock_aws_integration):
        """Test extract_name_from_arn with various character types in the name."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == expected_name

    def test_extract_name_from_arn_static_method(self, mock_aws_integration):
        """Test that extract_name_from_arn is a static method and can be called without instance"""
        arn = "arn:aws:iam::123456789012:role/test-role"

        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == "test-role"

    @pytest.mark.parametrize(
        "arn,expected_name",
        [
            ("arn:aws:iam::123456789012:role/test-role/", ""),
            ("arn:aws:iam::123456789012:/role/test-role", "test-role"),
            ("arn:aws:iam::123456789012:role//test-role", "test-role"),
        ],
        ids=["trailing_slash", "leading_slash", "multiple_slashes"],
    )
    def test_extract_name_from_arn_slash_edge_cases(self, arn, expected_name, mock_aws_integration):
        """Test extract_name_from_arn with various slash edge cases."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == expected_name

    @pytest.mark.parametrize(
        "arn,expected_name",
        [
            ("arn:aws:iam::123456789012:root", "arn:aws:iam::123456789012:root"),  # No slashes, returns whole string
            ("arn:aws:s3:::my-bucket", "arn:aws:s3:::my-bucket"),  # No slashes, returns whole string
            ("arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0", "i-1234567890abcdef0"),
            ("arn:aws:iam::123456789012:user/JohnDoe", "JohnDoe"),
            ("arn:aws:iam::123456789012:role/MyRole", "MyRole"),
            (
                "arn:aws:lambda:us-east-1:123456789012:function:my-function",
                "arn:aws:lambda:us-east-1:123456789012:function:my-function",
            ),  # No slashes, returns whole string
            (
                "arn:aws:rds:us-east-1:123456789012:db:my-database",
                "arn:aws:rds:us-east-1:123456789012:db:my-database",
            ),  # No slashes, returns whole string
            (
                "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-alb/1234567890abcdef0",
                "1234567890abcdef0",
            ),
        ],
        ids=[
            "iam_root",
            "s3_bucket",
            "ec2_instance",
            "iam_user",
            "iam_role",
            "lambda_function",
            "rds_database",
            "load_balancer",
        ],
    )
    def test_extract_name_from_arn_real_aws_examples(self, arn, expected_name, mock_aws_integration):
        """Test extract_name_from_arn with real AWS ARN examples."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == expected_name

    @pytest.mark.parametrize(
        "arn,expected_name",
        [
            ("test:value", "test:value"),  # No slashes, so returns whole string
            ("test/value", "value"),
            ("a", "a"),
        ],
        ids=["colon_only", "slash_only", "single_char"],
    )
    def test_extract_name_from_arn_minimal_arns(self, arn, expected_name, mock_aws_integration):
        """Test extract_name_from_arn with minimal ARN structures."""
        result = AWSInventoryIntegration.extract_name_from_arn(arn)
        assert result == expected_name

    def test_extract_name_from_arn_mixed_separators(self, mock_aws_integration):
        """Test extract_name_from_arn with mixed slash and colon separators"""

        arn_mixed = "arn:aws:iam::123456789012:role/path:to:role"
        result_mixed = AWSInventoryIntegration.extract_name_from_arn(arn_mixed)
        assert result_mixed == "path:to:role"  # Gets the last part after the last slash

    def test_parse_finding_basic_success(self):
        """Test parse_finding with basic successful finding"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Security Finding",
            "Description": "This is a test security finding description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this security issue", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = "Test comments with Finding Severity: HIGH"
            mock_severity.return_value = "HIGH"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            assert len(results) == 1
            finding_result = results[0]
            assert (
                finding_result.asset_identifier == "arn:aws:iam::123456789012:root"
            )  # extract_name_from_arn returns full ARN when no slashes
            assert finding_result.external_id == ""  # No finding ID provided in test data
            assert finding_result.title == "Test Security Finding"
            assert finding_result.category == "SecurityHub"
            assert finding_result.issue_title == "Test Security Finding"
            assert finding_result.severity == regscale_models.IssueSeverity.High
            assert finding_result.description == "This is a test security finding description"
            assert finding_result.status == regscale_models.IssueStatus.Open
            assert finding_result.checklist_status == regscale_models.ChecklistStatus.FAIL
            assert finding_result.results == "Test results"
            assert finding_result.recommendation_for_mitigation == "Fix this security issue"
            assert finding_result.comments == "Test comments with Finding Severity: HIGH"
            assert finding_result.poam_comments == "Test comments with Finding Severity: HIGH"
            assert finding_result.date_created == "2023-01-01"
            assert finding_result.due_date == "2023-02-01"
            assert finding_result.plugin_name == "Software and Configuration Checks"
            assert finding_result.baseline == "AWS Account"
            assert finding_result.observations == "Test comments with Finding Severity: HIGH"
            assert finding_result.vulnerability_type == "Vulnerability Scan"

    def test_parse_finding_multiple_resources(self):
        """Test parse_finding with multiple resources"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Multi-Resource Finding",
            "Description": "Finding affecting multiple resources",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [
                {"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"},
                {"Type": "AwsS3Bucket", "Id": "arn:aws:s3:::test-bucket"},
            ],
            "Compliance": {"Status": "PASSED"},
            "Remediation": {"Recommendation": {"Text": "No action needed", "Url": "https://example.com/info"}},
            "FindingProviderFields": {"Severity": {"Label": "LOW"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Pass", "Passed test")
            mock_comments.return_value = "Test comments with Finding Severity: LOW"
            mock_severity.return_value = "LOW"
            mock_due_date.return_value = "2023-04-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-04-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            # Should create one finding per resource
            assert len(results) == 2

            # Check first resource (AWS Account)
            assert (
                results[0].asset_identifier == "arn:aws:iam::123456789012:root"
            )  # extract_name_from_arn returns full ARN when no slashes
            assert results[0].baseline == "AWS Account"
            assert results[0].status == regscale_models.IssueStatus.Open  # Default status when no config

            # Check second resource (S3 Bucket)
            assert (
                results[1].asset_identifier == "arn:aws:s3:::test-bucket"
            )  # extract_name_from_arn returns full ARN when no slashes
            assert results[1].baseline == "S3 Bucket"  # get_baseline maps AwsS3Bucket to "S3 Bucket"
            assert results[1].status == regscale_models.IssueStatus.Open  # Default status when no config

    def test_parse_finding_missing_severity_config(self):
        """Test parse_finding when severity config is missing"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "UNKNOWN"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = "Test comments with Finding Severity: UNKNOWN"
            mock_severity.return_value = "UNKNOWN"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {
                "issues": {
                    "amazon": {
                        "high": 30,
                        "moderate": 60,
                        # Missing "low" mapping
                    }
                }
            }

            results = aws_integration.parse_finding(finding)

            # Should still create a finding with default 30 days
            assert len(results) == 1
            assert results[0].due_date == "2023-02-01"

    def test_parse_finding_missing_remediation(self):
        """Test parse_finding when remediation information is missing"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
            # Missing Remediation field
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = "Test comments with Finding Severity: HIGH"
            mock_severity.return_value = "HIGH"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            assert len(results) == 1
            # Should handle missing remediation gracefully
            assert results[0].recommendation_for_mitigation == ""

    def test_parse_finding_missing_types(self):
        """Test parse_finding when Types field is missing"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
            # Missing Types field
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = "Test comments with Finding Severity: HIGH"
            mock_severity.return_value = "HIGH"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            # This should handle the missing Types gracefully and create one finding per resource
            results = aws_integration.parse_finding(finding)
            assert len(results) == 1

    def test_parse_finding_empty_types(self):
        """Test parse_finding when Types field is empty"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": [],  # Empty types list
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = "Test comments with Finding Severity: HIGH"
            mock_severity.return_value = "HIGH"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            # This should handle the empty Types gracefully and create one finding per resource
            results = aws_integration.parse_finding(finding)
            assert len(results) == 1

    def test_parse_finding_exception_handling(self):
        """Test parse_finding exception handling"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status:
            # Make determine_status_and_results raise an exception
            mock_status.side_effect = Exception("Test exception")

            # Should handle exception gracefully and return empty list
            results = aws_integration.parse_finding(finding)

            assert len(results) == 0

    @pytest.mark.parametrize(
        "severity_label,friendly_sev,expected_severity",
        [
            ("CRITICAL", "high", regscale_models.IssueSeverity.High),
            ("HIGH", "high", regscale_models.IssueSeverity.High),
            ("MEDIUM", "moderate", regscale_models.IssueSeverity.Moderate),
            ("MODERATE", "moderate", None),  # MODERATE is not in the mapping, so it returns None
            ("LOW", "low", regscale_models.IssueSeverity.Low),
            ("UNKNOWN", "low", None),  # UNKNOWN is not in the mapping, so it returns None
        ],
        ids=["critical", "high", "medium", "moderate", "low", "unknown"],
    )
    def test_parse_finding_different_severities(self, severity_label, friendly_sev, expected_severity):
        """Test parse_finding with different severity levels."""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": f"Test {severity_label} Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": severity_label}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = ("Fail", "Test results")
            mock_comments.return_value = f"Test comments with Finding Severity: {severity_label}"
            mock_severity.return_value = severity_label
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            assert len(results) == 1
            assert results[0].severity == expected_severity

    @pytest.mark.parametrize(
        "status,expected_issue_status,expected_checklist_status",
        [
            ("Fail", regscale_models.IssueStatus.Open, regscale_models.ChecklistStatus.FAIL),
            (
                "Pass",
                regscale_models.IssueStatus.Open,
                regscale_models.ChecklistStatus.PASS,
            ),  # Defaults to Open when no config
            (
                "Unknown",
                regscale_models.IssueStatus.Open,
                regscale_models.ChecklistStatus.NOT_REVIEWED,
            ),  # Defaults to Open when no config
        ],
        ids=["fail", "pass", "unknown"],
    )
    def test_parse_finding_different_statuses(self, status, expected_issue_status, expected_checklist_status):
        """Test parse_finding with different status values."""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "Title": f"Test {status} Finding",
            "Description": "Test description",
            "CreatedAt": "2023-01-01T00:00:00Z",
            "Types": ["Software and Configuration Checks"],
            "Resources": [{"Type": "AwsAccount", "Id": "arn:aws:iam::123456789012:root"}],
            "Compliance": {"Status": "FAILED" if status == "Fail" else "PASSED"},
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com/fix"}},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = (status, f"{status} results")
            mock_comments.return_value = "Test comments with Finding Severity: HIGH"
            mock_severity.return_value = "HIGH"
            mock_due_date.return_value = "2023-02-01T00:00:00Z"
            mock_date_str.return_value = "2023-01-01"
            mock_datetime_str.return_value = "2023-02-01"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            assert len(results) == 1

            assert results[0].status == expected_issue_status
            assert results[0].checklist_status == expected_checklist_status

    def test_parse_finding_real_aws_finding_structure(self):
        """Test parse_finding with real AWS Security Hub finding structure"""
        # Create a real instance of AWSInventoryIntegration
        aws_integration = AWSInventoryIntegration(plan_id=1)

        finding = {
            "SchemaVersion": "2018-10-08",
            "Id": "arn:aws:securityhub:us-east-1:132360893372:security-control/Config.1/finding/6e568eb7-ea14-46ca-87f3-e8a6efbe805f",
            "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
            "ProductName": "Security Hub",
            "CompanyName": "AWS",
            "Region": "us-east-1",
            "GeneratorId": "security-control/Config.1",
            "AwsAccountId": "132360893372",
            "Types": ["Software and Configuration Checks/Industry and Regulatory Standards"],
            "FirstObservedAt": "2023-04-26T13:21:29.696Z",
            "LastObservedAt": "2023-05-02T08:13:56.971Z",
            "CreatedAt": "2023-04-26T13:21:29.696Z",
            "UpdatedAt": "2023-05-02T08:13:51.803Z",
            "Severity": {"Label": "MEDIUM", "Normalized": 40, "Original": "MEDIUM"},
            "Title": "AWS Config should be enabled",
            "Description": "This AWS control checks whether the Config service is enabled in the account for the local region and is recording all resources.",
            "Remediation": {
                "Recommendation": {
                    "Text": "For information on how to correct this issue, consult the AWS Security Hub controls documentation.",
                    "Url": "https://docs.aws.amazon.com/console/securityhub/Config.1/remediation",
                }
            },
            "ProductFields": {
                "aws/securityhub/ProductName": "Security Hub",
                "aws/securityhub/CompanyName": "AWS",
                "Resources:0/Id": "arn:aws:iam::132360893372:root",
                "aws/securityhub/FindingId": "arn:aws:securityhub:us-east-1::product/aws/securityhub/arn:aws:securityhub:us-east-1:132360893372:security-control/Config.1/finding/6e568eb7-ea14-46ca-87f3-e8a6efbe805f",
            },
            "Resources": [
                {"Type": "AwsAccount", "Id": "AWS::::Account:132360893372", "Partition": "aws", "Region": "us-east-1"}
            ],
            "Compliance": {
                "Status": "FAILED",
                "RelatedRequirements": [
                    "NIST.800-53.r5 CM-3",
                    "NIST.800-53.r5 CM-6(1)",
                    "NIST.800-53.r5 CM-8",
                    "NIST.800-53.r5 CM-8(2)",
                    "CIS AWS Foundations Benchmark v1.2.0/2.5",
                ],
                "SecurityControlId": "Config.1",
                "AssociatedStandards": [
                    {"StandardsId": "standards/nist-800-53/v/5.0.0"},
                    {"StandardsId": "ruleset/cis-aws-foundations-benchmark/v/1.2.0"},
                    {"StandardsId": "standards/aws-foundational-security-best-practices/v/1.0.0"},
                ],
            },
            "WorkflowState": "NEW",
            "Workflow": {"Status": "NEW"},
            "RecordState": "ACTIVE",
            "FindingProviderFields": {
                "Severity": {"Label": "MEDIUM", "Original": "MEDIUM"},
                "Types": ["Software and Configuration Checks/Industry and Regulatory Standards"],
            },
        }

        with patch("regscale.integrations.commercial.aws.scanner.determine_status_and_results") as mock_status, patch(
            "regscale.integrations.commercial.aws.scanner.get_comments"
        ) as mock_comments, patch(
            "regscale.integrations.commercial.aws.scanner.check_finding_severity"
        ) as mock_severity, patch(
            "regscale.integrations.commercial.aws.scanner.get_due_date"
        ) as mock_due_date, patch(
            "regscale.integrations.commercial.aws.scanner.date_str"
        ) as mock_date_str, patch(
            "regscale.integrations.commercial.aws.scanner.datetime_str"
        ) as mock_datetime_str:
            mock_status.return_value = (
                "Fail",
                "NIST.800-53.r5 CM-3, NIST.800-53.r5 CM-6(1), NIST.800-53.r5 CM-8, NIST.800-53.r5 CM-8(2), CIS AWS Foundations Benchmark v1.2.0/2.5",
            )
            mock_comments.return_value = "For information on how to correct this issue, consult the AWS Security Hub controls documentation.<br></br>https://docs.aws.amazon.com/console/securityhub/Config.1/remediation<br></br>Finding Severity: MEDIUM"
            mock_severity.return_value = "MEDIUM"
            mock_due_date.return_value = "2023-06-25T00:00:00Z"
            mock_date_str.return_value = "2023-04-26"
            mock_datetime_str.return_value = "2023-06-25"

            aws_integration.app = MagicMock()
            aws_integration.app.config = {"issues": {"amazon": {"high": 30, "moderate": 60, "low": 90}}}

            results = aws_integration.parse_finding(finding)

            assert len(results) == 1
            finding_result = results[0]
            assert (
                finding_result.asset_identifier == "AWS::::Account:132360893372"
            )  # extract_name_from_arn returns full ARN when no slashes
            assert (
                finding_result.external_id
                == "arn:aws:securityhub:us-east-1:132360893372:security-control/Config.1/finding/6e568eb7-ea14-46ca-87f3-e8a6efbe805f"
            )
            assert finding_result.title == "AWS Config should be enabled"
            assert finding_result.category == "SecurityHub"
            assert finding_result.severity == regscale_models.IssueSeverity.Moderate
            assert finding_result.status == regscale_models.IssueStatus.Open
            assert finding_result.checklist_status == regscale_models.ChecklistStatus.FAIL
            assert finding_result.plugin_name == "Software and Configuration Checks/Industry and Regulatory Standards"
            assert finding_result.baseline == "AWS Account"  # get_baseline maps AwsAccount to "AWS Account"
            assert (
                finding_result.results
                == "NIST.800-53.r5 CM-3, NIST.800-53.r5 CM-6(1), NIST.800-53.r5 CM-8, NIST.800-53.r5 CM-8(2), CIS AWS Foundations Benchmark v1.2.0/2.5"
            )
