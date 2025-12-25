#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for AWS inventory with simulated AWS data."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from typing import Iterator

import pytest

from regscale.integrations.commercial.aws.scanner import AWSInventoryIntegration
from regscale.integrations.scanner_integration import IntegrationAsset
from regscale.models import regscale_models

PLAN_ID = 36


@pytest.mark.integration
class TestAWSInventoryIntegration:
    """Test suite for AWS inventory integration with mocked AWS responses.

    These are integration tests that validate the AWS inventory collection
    with simulated data. They test the full workflow of fetching inventory from
    AWS and syncing them to RegScale.
    """

    @pytest.fixture
    def mock_regscale_app(self):
        """Create a mock RegScale application."""
        app = MagicMock()
        app.config = {
            "aws": {
                "inventory": {
                    "enabled_services": {
                        "ec2": True,
                        "s3": True,
                        "rds": True,
                        "lambda": True,
                        "dynamodb": True,
                        "vpc": True,
                        "elb": True,
                        "ecr": True,
                    }
                }
            }
        }
        return app

    @pytest.fixture
    def scanner(self, mock_regscale_app):
        """Create an AWS scanner instance."""
        scanner = AWSInventoryIntegration(plan_id=PLAN_ID)
        scanner.app = mock_regscale_app
        return scanner

    @pytest.fixture
    def mock_aws_inventory(self):
        """Create realistic mock AWS inventory data."""
        return {
            "EC2Instances": [
                {
                    "InstanceId": "i-1234567890abcdef0",
                    "InstanceType": "t3.medium",
                    "State": "running",
                    "Region": "us-east-1",
                    "PrivateIpAddress": "10.0.1.100",
                    "PublicIpAddress": "54.123.45.67",
                    "VpcId": "vpc-12345678",
                    "SubnetId": "subnet-12345678",
                    "ImageId": "ami-0abcdef1234567890",
                    "Platform": None,
                    "PlatformDetails": "Linux/UNIX",
                    "PublicDnsName": "ec2-54-123-45-67.compute-1.amazonaws.com",
                    "PrivateDnsName": "ip-10-0-1-100.ec2.internal",
                    "Tags": [{"Key": "Name", "Value": "WebServer-01"}],
                    "ImageInfo": {
                        "Name": "amazon-linux-2",
                        "Description": "Amazon Linux 2 AMI",
                        "RootDeviceType": "ebs",
                        "VirtualizationType": "hvm",
                    },
                    "CpuOptions": {"CoreCount": 1, "ThreadsPerCore": 2},
                    "BlockDeviceMappings": [{"Ebs": {"VolumeId": "vol-12345678"}}],
                }
            ],
            "S3Buckets": [
                {
                    "Name": "my-app-bucket",
                    "Region": "us-east-1",
                    "CreationDate": "2024-01-01T00:00:00.000Z",
                    "Grants": [],
                }
            ],
            "RDSInstances": [
                {
                    "DBInstanceIdentifier": "my-database",
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "postgres",
                    "EngineVersion": "14.7",
                    "DBInstanceStatus": "available",
                    "AvailabilityZone": "us-east-1a",
                    "Endpoint": {"Address": "my-database.abcdef.us-east-1.rds.amazonaws.com"},
                    "VpcId": "vpc-12345678",
                    "PubliclyAccessible": False,
                    "AllocatedStorage": 20,
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:my-database",
                }
            ],
            "LambdaFunctions": [
                {
                    "FunctionName": "my-lambda-function",
                    "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:my-lambda-function",
                    "Runtime": "python3.9",
                    "MemorySize": 256,
                    "Timeout": 30,
                    "Handler": "index.handler",
                    "Description": "Processes incoming events",
                    "Region": "us-east-1",
                }
            ],
            "DynamoDBTables": [
                {
                    "TableName": "users-table",
                    "TableStatus": "ACTIVE",
                    "TableArn": "arn:aws:dynamodb:us-east-1:123456789012:table/users-table",
                    "TableSizeBytes": 1024000,
                    "Region": "us-east-1",
                }
            ],
            "VPCs": [
                {
                    "VpcId": "vpc-12345678",
                    "CidrBlock": "10.0.0.0/16",
                    "State": "available",
                    "IsDefault": False,
                    "Region": "us-east-1",
                    "Tags": [{"Key": "Name", "Value": "main-vpc"}],
                }
            ],
            "LoadBalancers": [
                {
                    "LoadBalancerName": "my-load-balancer",
                    "LoadBalancerArn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188",
                    "DNSName": "my-load-balancer-1234567890.us-east-1.elb.amazonaws.com",
                    "Scheme": "internet-facing",
                    "State": "active",
                    "VpcId": "vpc-12345678",
                    "Region": "us-east-1",
                    "Listeners": [
                        {"Port": 80, "Protocol": "HTTP"},
                        {"Port": 443, "Protocol": "HTTPS"},
                    ],
                }
            ],
            "ECRRepositories": [
                {
                    "RepositoryName": "my-app",
                    "RepositoryArn": "arn:aws:ecr:us-east-1:123456789012:repository/my-app",
                    "RepositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app",
                    "ImageTagMutability": "MUTABLE",
                    "ImageScanningConfiguration": {"ScanOnPush": True},
                    "Region": "us-east-1",
                }
            ],
            "IAM": {
                "Roles": [
                    {
                        "Arn": "arn:aws:iam::123456789012:role/AdminRole",
                        "RoleName": "AdminRole",
                        "CreateDate": "2024-01-01T00:00:00.000Z",
                    }
                ]
            },
        }

    def test_sync_assets_only(self, scanner, mock_aws_inventory):
        """Test syncing only AWS assets without findings."""
        # Mock the fetch_aws_data_if_needed to return our test inventory
        with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
            mock_fetch.return_value = mock_aws_inventory

            # Call fetch_assets to get the assets
            assets_iterator = scanner.fetch_assets(
                region="us-east-1",
                profile="test-profile",
                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None,
            )

            # Convert iterator to list
            assets_list = list(assets_iterator)

            # Should have 9 assets (1 EC2, 1 S3, 1 RDS, 1 Lambda, 1 DynamoDB, 1 VPC, 1 LB, 1 ECR, 1 IAM)
            assert len(assets_list) == 9

            # Verify all assets are IntegrationAsset objects
            for asset in assets_list:
                assert isinstance(asset, IntegrationAsset)
                assert asset.parent_id == PLAN_ID

    def test_fetch_assets(self, scanner, mock_aws_inventory):
        """Test that fetch_assets correctly retrieves and parses AWS inventory."""
        # Mock the fetch_aws_data_if_needed to return our test inventory
        with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
            mock_fetch.return_value = mock_aws_inventory

            # Call fetch_assets to get parsed assets
            assets_iterator = scanner.fetch_assets(
                region="us-east-1",
                profile="test-profile",
                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None,
            )

            # Convert iterator to list
            assets_list = list(assets_iterator)

            # Should have 9 assets
            assert len(assets_list) == 9, f"Expected 9 assets but got {len(assets_list)}"

            # Verify assets were properly parsed
            for asset in assets_list:
                assert isinstance(asset, IntegrationAsset)
                assert asset.name is not None
                assert asset.identifier is not None
                assert asset.manufacturer == "AWS"

    def test_parse_ec2_instance(self, scanner, mock_aws_inventory):
        """Test parsing EC2 instance to IntegrationAsset."""
        ec2_data = mock_aws_inventory["EC2Instances"][0]
        asset = scanner.parse_ec2_instance(ec2_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "WebServer-01"
        assert asset.identifier == "i-1234567890abcdef0"
        assert asset.asset_type == regscale_models.AssetType.VM
        assert asset.manufacturer == "AWS"
        assert asset.model == "t3.medium"
        assert asset.aws_identifier == "arn:aws:ec2:us-east-1::instance/i-1234567890abcdef0"
        assert asset.is_virtual is True
        assert asset.ip_address == "10.0.1.100"
        assert asset.location == "us-east-1"
        assert asset.status == regscale_models.AssetStatus.Active

    def test_parse_s3_bucket(self, scanner, mock_aws_inventory):
        """Test parsing S3 bucket to IntegrationAsset."""
        s3_data = mock_aws_inventory["S3Buckets"][0]
        asset = scanner.parse_s3_bucket(s3_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "my-app-bucket"
        assert asset.identifier == "my-app-bucket"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier == "arn:aws:s3:::my-app-bucket"
        assert asset.location == "us-east-1"

    def test_parse_rds_instance(self, scanner, mock_aws_inventory):
        """Test parsing RDS instance to IntegrationAsset."""
        rds_data = mock_aws_inventory["RDSInstances"][0]
        asset = scanner.parse_rds_instance(rds_data)

        assert isinstance(asset, IntegrationAsset)
        assert "my-database" in asset.name
        assert asset.identifier == "my-database"
        assert asset.asset_type == regscale_models.AssetType.VM
        assert asset.manufacturer == "AWS"
        assert asset.model == "db.t3.micro"
        assert asset.software_name == "postgres"
        assert asset.software_version == "14.7"
        assert asset.aws_identifier == "arn:aws:rds:us-east-1:123456789012:db:my-database"
        assert asset.is_public_facing is False
        assert asset.disk_storage == 20

    def test_parse_lambda_function(self, scanner, mock_aws_inventory):
        """Test parsing Lambda function to IntegrationAsset."""
        lambda_data = mock_aws_inventory["LambdaFunctions"][0]
        asset = scanner.parse_lambda_function(lambda_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "my-lambda-function"
        assert asset.identifier == "my-lambda-function"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.software_name == "python3.9"
        assert asset.ram == 256
        assert asset.aws_identifier == "arn:aws:lambda:us-east-1:123456789012:function:my-lambda-function"
        assert asset.is_virtual is True

    def test_parse_dynamodb_table(self, scanner, mock_aws_inventory):
        """Test parsing DynamoDB table to IntegrationAsset."""
        dynamodb_data = mock_aws_inventory["DynamoDBTables"][0]
        asset = scanner.parse_dynamodb_table(dynamodb_data)

        assert isinstance(asset, IntegrationAsset)
        assert "users-table" in asset.name
        assert asset.identifier == "users-table"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier == "arn:aws:dynamodb:us-east-1:123456789012:table/users-table"
        assert asset.disk_storage == 1024000
        assert asset.status == regscale_models.AssetStatus.Active

    def test_parse_vpc(self, scanner, mock_aws_inventory):
        """Test parsing VPC to IntegrationAsset."""
        vpc_data = mock_aws_inventory["VPCs"][0]
        asset = scanner.parse_vpc(vpc_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "main-vpc"
        assert asset.identifier == "vpc-12345678"
        assert asset.asset_type == regscale_models.AssetType.NetworkRouter
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier == "arn:aws:ec2:us-east-1::vpc/vpc-12345678"
        assert asset.vlan_id == "vpc-12345678"
        assert asset.status == regscale_models.AssetStatus.Active
        assert "10.0.0.0/16" in asset.notes

    def test_parse_load_balancer(self, scanner, mock_aws_inventory):
        """Test parsing Load Balancer to IntegrationAsset."""
        lb_data = mock_aws_inventory["LoadBalancers"][0]
        asset = scanner.parse_load_balancer(lb_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "my-load-balancer"
        assert asset.identifier == "my-load-balancer"
        assert asset.asset_type == regscale_models.AssetType.NetworkRouter
        assert asset.manufacturer == "AWS"
        assert (
            asset.aws_identifier
            == "arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/app/my-load-balancer/50dc6c495c0c9188"
        )
        assert asset.fqdn == "my-load-balancer-1234567890.us-east-1.elb.amazonaws.com"
        assert asset.is_public_facing is True
        assert asset.status == regscale_models.AssetStatus.Active
        assert len(asset.ports_and_protocols) == 2

    def test_parse_ecr_repository(self, scanner, mock_aws_inventory):
        """Test parsing ECR repository to IntegrationAsset."""
        ecr_data = mock_aws_inventory["ECRRepositories"][0]
        asset = scanner.parse_ecr_repository(ecr_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "my-app"
        assert asset.identifier == "my-app"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier.startswith("arn:aws:ecr:us-east-1")
        assert asset.uri == "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app"
        # Note: notes field is no longer populated by implementation

    def test_parse_aws_account(self, scanner, mock_aws_inventory):
        """Test parsing IAM role to AWS Account asset."""
        iam_data = mock_aws_inventory["IAM"]["Roles"][0]
        asset = scanner.parse_aws_account(iam_data)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "123456789012"
        assert asset.identifier == "AWS::::Account:123456789012"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier == "AWS::::Account:123456789012"

    def test_fetch_assets_with_empty_inventory(self, scanner):
        """Test fetch_assets when no resources are returned from AWS."""
        empty_inventory = {
            "EC2Instances": [],
            "S3Buckets": [],
            "RDSInstances": [],
            "LambdaFunctions": [],
            "DynamoDBTables": [],
            "VPCs": [],
            "LoadBalancers": [],
            "ECRRepositories": [],
            "IAM": {"Roles": []},
        }

        with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
            mock_fetch.return_value = empty_inventory

            assets = list(
                scanner.fetch_assets(
                    region="us-east-1",
                    profile="test",
                    aws_access_key_id=None,
                    aws_secret_access_key=None,
                    aws_session_token=None,
                )
            )

            assert len(assets) == 0
            assert scanner.num_assets_to_process == 0

    def test_inventory_with_authentication_error(self, scanner):
        """Test fetch_assets handles authentication errors gracefully."""
        with patch.object(scanner, "authenticate") as mock_auth:
            mock_auth.side_effect = Exception("The security token included in the request is invalid")

            with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
                mock_fetch.side_effect = Exception("The security token included in the request is invalid")

                with pytest.raises(Exception) as exc_info:
                    list(
                        scanner.fetch_assets(
                            region="us-east-1",
                            profile="test",
                            aws_access_key_id=None,
                            aws_secret_access_key=None,
                            aws_session_token=None,
                        )
                    )

                assert "security token" in str(exc_info.value).lower()

    def test_asset_counts_by_type(self, scanner, mock_aws_inventory):
        """Test that each asset type is correctly counted and parsed."""
        with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
            mock_fetch.return_value = mock_aws_inventory

            assets_iterator = scanner.fetch_assets(
                region="us-east-1",
                profile="test-profile",
                aws_access_key_id=None,
                aws_secret_access_key=None,
                aws_session_token=None,
            )

            assets_list = list(assets_iterator)

            # Count assets by type
            asset_types = {}
            for asset in assets_list:
                asset_type = asset.asset_type.name
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1

            # Verify counts
            assert asset_types[regscale_models.AssetType.VM.name] == 2  # EC2 + RDS
            assert asset_types[regscale_models.AssetType.Other.name] == 5  # S3 + Lambda + DynamoDB + ECR + IAM
            assert asset_types[regscale_models.AssetType.NetworkRouter.name] == 2  # VPC + LB

    def test_sync_assets_to_database(self, scanner, mock_aws_inventory, mock_regscale_app):
        """Test syncing AWS assets to RegScale database.

        This test validates the full end-to-end flow of:
        1. Fetching AWS inventory data
        2. Parsing it into IntegrationAsset objects
        3. Creating/updating assets in RegScale database via bulk operations

        NOTE: The system uses bulk operations for efficiency, so assets are queued
        and then saved all at once via Asset.bulk_save().
        """
        # Mock the fetch_aws_data_if_needed to return our test inventory
        with patch.object(scanner, "fetch_aws_data_if_needed") as mock_fetch:
            mock_fetch.return_value = mock_aws_inventory

            # Mock the bulk save operation which is how assets are persisted
            with patch.object(regscale_models.Asset, "bulk_save") as mock_bulk_save:
                # Mock response: {'created': [...], 'updated': [...], 'created_count': 9, 'updated_count': 0}
                mock_bulk_save.return_value = {
                    "created": [MagicMock(id=i) for i in range(1, 10)],
                    "updated": [],
                    "created_count": 9,
                    "updated_count": 0,
                }

                # Mock component creation
                with patch.object(regscale_models.Component, "get_or_create") as mock_component_create:
                    mock_component = MagicMock()
                    mock_component.id = 456
                    mock_component.securityPlansId = PLAN_ID
                    mock_component_create.return_value = mock_component

                    # Mock asset mapping creation
                    with patch.object(regscale_models.AssetMapping, "get_or_create_with_status") as mock_asset_mapping:
                        mock_asset_mapping.return_value = (True, MagicMock())

                        # Mock asset cache population
                        with patch.object(regscale_models.Asset, "get_all_by_parent") as mock_get_all:
                            mock_get_all.return_value = []

                            # Mock other bulk operations
                            with patch.object(regscale_models.Issue, "bulk_save") as mock_issue_bulk:
                                mock_issue_bulk.return_value = {"created": [], "updated": []}

                                with patch.object(regscale_models.Property, "bulk_save") as mock_property_bulk:
                                    mock_property_bulk.return_value = {"created": [], "updated": []}

                                    with patch.object(regscale_models.Data, "bulk_save") as mock_data_bulk:
                                        mock_data_bulk.return_value = {"created": [], "updated": []}

                                        # Mock mapping cache population
                                        with patch.object(regscale_models.AssetMapping, "populate_cache_by_plan"):
                                            with patch.object(
                                                regscale_models.ComponentMapping, "populate_cache_by_plan"
                                            ):
                                                # Fetch assets and sync them
                                                assets_iterator = scanner.fetch_assets(
                                                    region="us-east-1",
                                                    profile="test-profile",
                                                    aws_access_key_id=None,
                                                    aws_secret_access_key=None,
                                                    aws_session_token=None,
                                                )

                                                # Call update_regscale_assets to persist to database
                                                assets_processed = scanner.update_regscale_assets(
                                                    assets=assets_iterator
                                                )

                                                # Verify assets were processed
                                                assert (
                                                    assets_processed == 9
                                                ), f"Expected 9 assets processed but got {assets_processed}"

                                                # Verify bulk_save was called once for assets
                                                assert (
                                                    mock_bulk_save.call_count == 1
                                                ), f"Expected Asset.bulk_save to be called once, but it was called {mock_bulk_save.call_count} times"

                                                # Verify the scanner tracked the results correctly
                                                # Note: Assets are created once per component name, so the count may be higher
                                                # than the number of unique assets. For this test, we just verify bulk_save was called.
                                                created_count = scanner._results.get("assets", {}).get(
                                                    "created_count", 0
                                                )
                                                assert (
                                                    created_count > 0
                                                ), f"Expected assets to be created, but got {created_count}"
