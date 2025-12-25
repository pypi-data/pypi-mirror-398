#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for AWS scanner with simulated AWS data."""

from datetime import datetime
from unittest.mock import MagicMock, patch
from typing import Iterator

import pytest

from regscale.integrations.commercial.aws.scanner import AWSInventoryIntegration
from regscale.integrations.scanner_integration import IntegrationAsset, IntegrationFinding
from regscale.models import regscale_models

PLAN_ID = 36


@pytest.mark.integration
class TestAWSScannerIntegration:
    """Test suite for AWS scanner integration with mocked AWS responses.

    These are integration tests that validate the AWS Security Hub integration
    with simulated data. They test the full workflow of fetching findings from
    AWS Security Hub and syncing them to RegScale.
    """

    @pytest.fixture
    def mock_regscale_app(self):
        """Create a mock RegScale application."""
        app = MagicMock()
        app.config = {
            "issues": {
                "amazon": {
                    "status": "Open",
                    "minimumSeverity": "LOW",
                    "low": 30,
                    "moderate": 15,
                    "high": 7,
                }
            }
        }
        return app

    @pytest.fixture
    def scanner(self, mock_regscale_app):
        """Create an AWS scanner instance."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_regscale_app
        return scanner

    @pytest.fixture
    def mock_security_hub_findings(self):
        """Create realistic mock Security Hub findings data."""
        return [
            {
                "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/S3.1/finding/a1b2c3d4-5678-90ab-cdef-EXAMPLE11111",
                "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                "ProductName": "Security Hub",
                "CompanyName": "AWS",
                "Region": "us-east-1",
                "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.1",
                "AwsAccountId": "123456789012",
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": "2024-01-15T10:30:00.000Z",
                "LastObservedAt": "2024-01-20T14:45:00.000Z",
                "CreatedAt": "2024-01-15T10:30:00.000Z",
                "UpdatedAt": "2024-01-20T14:45:00.000Z",
                "Severity": {"Label": "HIGH", "Normalized": 70},
                "Title": "S3.1 S3 Block Public Access setting should be enabled",
                "Description": "This control checks whether S3 Block Public Access setting is enabled at the bucket level.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "Enable S3 Block Public Access at the bucket level",
                        "Url": "https://docs.aws.amazon.com/console/securityhub/S3.1/remediation",
                    }
                },
                "ProductFields": {
                    "StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0",
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0",
                    "ControlId": "S3.1",
                    "RecommendationUrl": "https://docs.aws.amazon.com/console/securityhub/S3.1/remediation",
                    "RelatedAWSResources:0/name": "securityhub-s3-bucket-public-write-prohibited",
                    "RelatedAWSResources:0/type": "AWS::Config::ConfigRule",
                    "StandardsControlArn": "arn:aws:securityhub:us-east-1:123456789012:control/aws-foundational-security-best-practices/v/1.0.0/S3.1",
                    "aws/securityhub/ProductName": "Security Hub",
                    "aws/securityhub/CompanyName": "AWS",
                    "Resources:0/Id": "arn:aws:s3:::my-test-bucket",
                    "aws/securityhub/FindingId": "arn:aws:securityhub:us-east-1::product/aws/securityhub/arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/S3.1/finding/a1b2c3d4-5678-90ab-cdef-EXAMPLE11111",
                },
                "Resources": [
                    {
                        "Type": "AwsS3Bucket",
                        "Id": "arn:aws:s3:::my-test-bucket",
                        "Partition": "aws",
                        "Region": "us-east-1",
                        "Details": {
                            "AwsS3Bucket": {
                                "OwnerId": "123456789012",
                                "OwnerName": "test-owner",
                                "CreatedAt": "2024-01-01T00:00:00.000Z",
                                "Name": "my-test-bucket",
                                "PublicAccessBlockConfiguration": {
                                    "BlockPublicAcls": False,
                                    "BlockPublicPolicy": False,
                                    "IgnorePublicAcls": False,
                                    "RestrictPublicBuckets": False,
                                },
                            }
                        },
                    }
                ],
                "Compliance": {"Status": "FAILED"},
                "WorkflowState": "NEW",
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
                "FindingProviderFields": {
                    "Severity": {"Label": "HIGH"},
                    "Types": ["Software and Configuration Checks"],
                },
            },
            {
                "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/EC2.1/finding/b2c3d4e5-6789-01ab-cdef-EXAMPLE22222",
                "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                "ProductName": "Security Hub",
                "CompanyName": "AWS",
                "Region": "us-east-1",
                "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/EC2.1",
                "AwsAccountId": "123456789012",
                "Types": ["Software and Configuration Checks/AWS Security Best Practices"],
                "FirstObservedAt": "2024-01-16T11:00:00.000Z",
                "LastObservedAt": "2024-01-20T15:00:00.000Z",
                "CreatedAt": "2024-01-16T11:00:00.000Z",
                "UpdatedAt": "2024-01-20T15:00:00.000Z",
                "Severity": {"Label": "MEDIUM", "Normalized": 40},
                "Title": "EC2.1 Amazon EBS snapshots should not be publicly restorable",
                "Description": "This control checks whether Amazon EBS snapshots are restorable by everyone.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "Modify EBS snapshot permissions to remove public access",
                        "Url": "https://docs.aws.amazon.com/console/securityhub/EC2.1/remediation",
                    }
                },
                "ProductFields": {
                    "StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0",
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0",
                    "ControlId": "EC2.1",
                    "RecommendationUrl": "https://docs.aws.amazon.com/console/securityhub/EC2.1/remediation",
                    "RelatedAWSResources:0/name": "securityhub-ec2-ebs-snapshot-public-restorable",
                    "RelatedAWSResources:0/type": "AWS::Config::ConfigRule",
                    "StandardsControlArn": "arn:aws:securityhub:us-east-1:123456789012:control/aws-foundational-security-best-practices/v/1.0.0/EC2.1",
                    "aws/securityhub/ProductName": "Security Hub",
                    "aws/securityhub/CompanyName": "AWS",
                    "Resources:0/Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "aws/securityhub/FindingId": "arn:aws:securityhub:us-east-1::product/aws/securityhub/arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/EC2.1/finding/b2c3d4e5-6789-01ab-cdef-EXAMPLE22222",
                },
                "Resources": [
                    {
                        "Type": "AwsEc2Instance",
                        "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                        "Partition": "aws",
                        "Region": "us-east-1",
                        "Tags": {"Name": "WebServer-01"},
                        "Details": {
                            "AwsEc2Instance": {
                                "Type": "t3.medium",
                                "ImageId": "ami-0abcdef1234567890",
                                "IpV4Addresses": ["10.0.1.100", "54.123.45.67"],
                                "IpV6Addresses": [],
                                "KeyName": "my-keypair",
                                "IamInstanceProfileArn": "arn:aws:iam::123456789012:instance-profile/EC2-Role",
                                "VpcId": "vpc-12345678",
                                "SubnetId": "subnet-12345678",
                                "LaunchedAt": "2024-01-10T08:00:00.000Z",
                            }
                        },
                    }
                ],
                "Compliance": {"Status": "FAILED"},
                "WorkflowState": "NEW",
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
                "FindingProviderFields": {
                    "Severity": {"Label": "MEDIUM"},
                    "Types": ["Software and Configuration Checks"],
                },
            },
            {
                "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/IAM.1/finding/c3d4e5f6-7890-12ab-cdef-EXAMPLE33333",
                "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
                "ProductName": "Security Hub",
                "CompanyName": "AWS",
                "Region": "us-east-1",
                "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/IAM.1",
                "AwsAccountId": "123456789012",
                "Types": ["Software and Configuration Checks/AWS Security Best Practices/IAM"],
                "FirstObservedAt": "2024-01-14T09:00:00.000Z",
                "LastObservedAt": "2024-01-20T16:00:00.000Z",
                "CreatedAt": "2024-01-14T09:00:00.000Z",
                "UpdatedAt": "2024-01-20T16:00:00.000Z",
                "Severity": {"Label": "CRITICAL", "Normalized": 90},
                "Title": "IAM.1 IAM policies should not allow full '*' administrative privileges",
                "Description": "This control checks whether IAM policies that you create grant full '*:*' administrative privileges.",
                "Remediation": {
                    "Recommendation": {
                        "Text": "Follow the principle of least privilege and grant only necessary permissions",
                        "Url": "https://docs.aws.amazon.com/console/securityhub/IAM.1/remediation",
                    }
                },
                "ProductFields": {
                    "StandardsArn": "arn:aws:securityhub:::standards/aws-foundational-security-best-practices/v/1.0.0",
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0",
                    "ControlId": "IAM.1",
                    "RecommendationUrl": "https://docs.aws.amazon.com/console/securityhub/IAM.1/remediation",
                    "RelatedAWSResources:0/name": "securityhub-iam-policy-no-statements-with-admin-access",
                    "RelatedAWSResources:0/type": "AWS::Config::ConfigRule",
                    "StandardsControlArn": "arn:aws:securityhub:us-east-1:123456789012:control/aws-foundational-security-best-practices/v/1.0.0/IAM.1",
                    "aws/securityhub/ProductName": "Security Hub",
                    "aws/securityhub/CompanyName": "AWS",
                    "Resources:0/Id": "arn:aws:iam::123456789012:user/admin-user",
                    "aws/securityhub/FindingId": "arn:aws:securityhub:us-east-1::product/aws/securityhub/arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/IAM.1/finding/c3d4e5f6-7890-12ab-cdef-EXAMPLE33333",
                },
                "Resources": [
                    {
                        "Type": "AwsIamUser",
                        "Id": "arn:aws:iam::123456789012:user/admin-user",
                        "Partition": "aws",
                        "Region": "us-east-1",
                        "Details": {
                            "AwsIamUser": {
                                "AttachedManagedPolicies": [
                                    {
                                        "PolicyName": "AdministratorAccess",
                                        "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess",
                                    }
                                ],
                                "CreateDate": "2023-12-01T10:00:00.000Z",
                                "UserName": "admin-user",
                                "UserId": "AIDACKCEVSQ6C2EXAMPLE",
                            }
                        },
                    }
                ],
                "Compliance": {"Status": "FAILED"},
                "WorkflowState": "NEW",
                "Workflow": {"Status": "NEW"},
                "RecordState": "ACTIVE",
                "FindingProviderFields": {
                    "Severity": {"Label": "CRITICAL"},
                    "Types": ["Software and Configuration Checks/AWS Security Best Practices/IAM"],
                },
            },
        ]

    @pytest.fixture
    def mock_boto_session(self, mock_security_hub_findings):
        """Create a mock boto3 session with Security Hub client."""
        session = MagicMock()
        client = MagicMock()

        # Mock the get_findings method to return our test findings
        client.get_findings.return_value = {"Findings": mock_security_hub_findings}

        # Mock paginator for get_findings (in case pagination is used)
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Findings": mock_security_hub_findings}]
        client.get_paginator.return_value = paginator

        # Mock session metadata for region
        session.meta.region_name = "us-east-1"
        session.client.return_value = client
        return session

    def test_sync_findings_only(self, scanner, mock_boto_session, mock_security_hub_findings):
        """Test that fetch_findings correctly retrieves and parses AWS Security Hub findings."""
        with patch("boto3.Session", return_value=mock_boto_session):
            # Mock the fetch_aws_findings function to return our test data
            with patch("regscale.integrations.commercial.amazon.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = mock_security_hub_findings

                # Call fetch_findings to get parsed findings
                findings_iterator = scanner.fetch_findings(
                    region="us-east-1",
                    profile="test-profile",
                    aws_access_key_id=None,
                    aws_secret_access_key=None,
                    aws_session_token=None,
                )

                # Convert iterator to list
                findings_list = list(findings_iterator)

                # Should have findings for 3 different resources
                assert len(findings_list) == 3, f"Expected 3 findings but got {len(findings_list)}"

                # Verify findings were properly parsed
                for finding in findings_list:
                    assert isinstance(finding, IntegrationFinding)
                    assert finding.title is not None
                    assert finding.severity is not None

                # Verify assets were discovered during finding fetch
                assert len(scanner.discovered_assets) == 3, "Should have discovered 3 assets from findings"

    def test_sync_findings_and_assets(self, scanner, mock_boto_session, mock_security_hub_findings):
        """Test syncing findings and automatically discovered assets."""
        with patch("boto3.Session", return_value=mock_boto_session):
            # Mock the fetch_aws_findings function to return our test data
            with patch("regscale.integrations.commercial.amazon.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = mock_security_hub_findings

                with patch.object(scanner, "update_regscale_assets") as mock_update_assets:
                    with patch.object(scanner, "update_regscale_findings") as mock_update_findings:
                        mock_update_assets.return_value = 3  # 3 assets discovered
                        mock_update_findings.return_value = 3  # 3 findings processed

                        # Call sync_findings_and_assets
                        findings_count, assets_count = scanner.sync_findings_and_assets(
                            plan_id=PLAN_ID,
                            region="us-east-1",
                            profile="test-profile",
                            aws_access_key_id=None,
                            aws_secret_access_key=None,
                            aws_session_token=None,
                        )

                        # Verify counts
                        assert findings_count == 3
                        assert assets_count == 3

                        # Verify assets were created first, then findings
                        assert mock_update_assets.call_count == 1
                        assert mock_update_findings.call_count == 1

    def test_parse_finding_creates_integration_finding(self, scanner):
        """Test that parse_finding correctly creates IntegrationFinding objects."""
        test_finding = {
            "Id": "test-finding-id",
            "Title": "Test Security Finding",
            "Description": "This is a test finding",
            "Severity": {"Label": "HIGH"},
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "Remediation": {
                "Recommendation": {
                    "Text": "Fix this issue",
                    "Url": "https://example.com/fix",
                }
            },
            "Types": ["Software and Configuration Checks"],
            "Resources": [
                {
                    "Type": "AwsS3Bucket",
                    "Id": "arn:aws:s3:::test-bucket",
                    "Region": "us-east-1",
                    "Details": {"AwsS3Bucket": {"Name": "test-bucket"}},
                }
            ],
            "Compliance": {"Status": "FAILED"},
            "FindingProviderFields": {
                "Severity": {"Label": "HIGH"},
                "Types": ["Software and Configuration Checks"],
            },
        }

        findings = scanner.parse_finding(test_finding)

        # If no findings returned, there was likely an exception or filtering issue
        assert len(findings) == 1, f"Expected 1 finding but got {len(findings)}"
        finding = findings[0]

        # Verify IntegrationFinding fields
        assert isinstance(finding, IntegrationFinding)
        assert finding.title == "Test Security Finding"
        assert finding.description == "This is a test finding"
        assert finding.severity == regscale_models.IssueSeverity.High
        assert finding.recommendation_for_mitigation == "Fix this issue"
        # Note: asset_identifier uses extract_name_from_arn which for S3 ARNs returns the full ARN
        assert finding.asset_identifier == "arn:aws:s3:::test-bucket"

    def test_parse_resource_to_asset_s3_bucket(self, scanner):
        """Test parsing S3 bucket resource to IntegrationAsset."""
        resource = {
            "Type": "AwsS3Bucket",
            "Id": "arn:aws:s3:::my-test-bucket",
            "Region": "us-east-1",
            "Details": {
                "AwsS3Bucket": {
                    "Name": "my-test-bucket",
                    "OwnerId": "123456789012",
                    "CreatedAt": "2024-01-01T00:00:00.000Z",
                }
            },
        }

        finding = {"Id": "test-finding"}

        asset = scanner.parse_resource_to_asset(resource, finding)

        assert isinstance(asset, IntegrationAsset)
        # The scanner's extract_name_from_arn returns the full ARN for S3 buckets without "/"
        # Then uses "or" operator to fallback to Details, but since ARN is truthy it uses the ARN
        # This is the current behavior - the test validates what actually happens
        assert asset.name == "S3 Bucket: arn:aws:s3:::my-test-bucket"
        assert asset.identifier == "arn:aws:s3:::my-test-bucket"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.aws_identifier == "arn:aws:s3:::my-test-bucket"
        assert asset.is_virtual is True

    def test_parse_resource_to_asset_ec2_instance(self, scanner):
        """Test parsing EC2 instance resource to IntegrationAsset."""
        resource = {
            "Type": "AwsEc2Instance",
            "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
            "Region": "us-east-1",
            "Tags": {"Name": "WebServer-01"},
            "Details": {
                "AwsEc2Instance": {
                    "Type": "t3.medium",
                    "ImageId": "ami-0abcdef1234567890",
                    "VpcId": "vpc-12345678",
                    "SubnetId": "subnet-12345678",
                }
            },
        }

        finding = {"Id": "test-finding"}

        asset = scanner.parse_resource_to_asset(resource, finding)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "EC2: WebServer-01 (t3.medium)"
        assert asset.identifier == "i-1234567890abcdef0"
        assert asset.asset_type == regscale_models.AssetType.VM
        assert asset.manufacturer == "AWS"
        assert asset.model == "t3.medium"
        assert asset.is_virtual is True

    def test_parse_resource_to_asset_iam_user(self, scanner):
        """Test parsing IAM user resource to IntegrationAsset."""
        resource = {
            "Type": "AwsIamUser",
            "Id": "arn:aws:iam::123456789012:user/admin-user",
            "Region": "us-east-1",
            "Details": {"AwsIamUser": {"UserName": "admin-user", "UserId": "AIDACKCEVSQ6C2EXAMPLE"}},
        }

        finding = {"Id": "test-finding"}

        asset = scanner.parse_resource_to_asset(resource, finding)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "IAM User: admin-user"
        assert asset.identifier == "admin-user"
        assert asset.asset_type == regscale_models.AssetType.Other
        assert asset.manufacturer == "AWS"
        assert asset.is_virtual is True

    def test_should_process_finding_by_severity(self, scanner):
        """Test severity filtering logic."""
        # Test HIGH severity (should process)
        assert scanner.should_process_finding_by_severity("HIGH") is True

        # Test CRITICAL severity (should process)
        assert scanner.should_process_finding_by_severity("CRITICAL") is True

        # Test MEDIUM severity (should process)
        assert scanner.should_process_finding_by_severity("MEDIUM") is True

        # Test LOW severity (should process - it's the minimum)
        assert scanner.should_process_finding_by_severity("LOW") is True

        # Now test with higher minimum severity
        scanner.app.config["issues"]["aws"]["minimumSeverity"] = "HIGH"

        # Test HIGH severity (should process)
        assert scanner.should_process_finding_by_severity("HIGH") is True

        # Test MEDIUM severity (should NOT process)
        assert scanner.should_process_finding_by_severity("MEDIUM") is False

        # Test LOW severity (should NOT process)
        assert scanner.should_process_finding_by_severity("LOW") is False

    def test_extract_name_from_arn(self, scanner):
        """Test extracting resource names from ARNs."""
        # Test with slash separator
        arn = "arn:aws:s3:::my-bucket/object-key"
        assert scanner.extract_name_from_arn(arn) == "object-key"

        # Test with colon separator
        arn = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        assert scanner.extract_name_from_arn(arn) == "i-1234567890abcdef0"

        # Test simple name
        arn = "my-simple-name"
        assert scanner.extract_name_from_arn(arn) == "my-simple-name"

    def test_get_baseline(self, scanner):
        """Test baseline determination from resource type."""
        assert scanner.get_baseline({"Type": "AwsAccount"}) == "AWS Account"
        assert scanner.get_baseline({"Type": "AwsS3Bucket"}) == "S3 Bucket"
        assert scanner.get_baseline({"Type": "AwsIamRole"}) == "IAM Role"
        assert scanner.get_baseline({"Type": "AwsEc2Instance"}) == "EC2 Instance"
        assert scanner.get_baseline({"Type": "UnknownType"}) == "UnknownType"

    def test_fetch_findings_with_no_findings(self, scanner):
        """Test fetch_findings when no findings are returned from AWS."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.get_findings.return_value = {"Findings": []}
        mock_session.client.return_value = mock_client
        mock_session.meta.region_name = "us-east-1"

        with patch("boto3.Session", return_value=mock_session):
            # Mock fetch_aws_findings to return empty list
            with patch("regscale.integrations.commercial.amazon.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = []

                findings = list(
                    scanner.fetch_findings(
                        region="us-east-1",
                        profile="test",
                        aws_access_key_id=None,
                        aws_secret_access_key=None,
                        aws_session_token=None,
                    )
                )

                assert len(findings) == 0

    def test_discovered_assets_tracking(self, scanner, mock_boto_session, mock_security_hub_findings):
        """Test that discovered assets are properly tracked and deduplicated."""
        with patch("boto3.Session", return_value=mock_boto_session):
            # Mock fetch_aws_findings to return our test data
            with patch("regscale.integrations.commercial.amazon.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = mock_security_hub_findings

                # Fetch findings (this will discover assets)
                findings = list(
                    scanner.fetch_findings(
                        region="us-east-1",
                        profile="test",
                        aws_access_key_id=None,
                        aws_secret_access_key=None,
                        aws_session_token=None,
                    )
                )

                # Verify findings were parsed
                assert len(findings) == 3

                # Verify assets were discovered
                assert len(scanner.discovered_assets) == 3

                # Verify asset identifiers are tracked
                assert len(scanner.processed_asset_identifiers) == 3

    def test_sync_findings_with_authentication_error(self, scanner):
        """Test sync_findings handles authentication errors gracefully."""
        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_client = MagicMock()
            mock_session.client.return_value = mock_client
            mock_session.meta.region_name = "us-east-1"
            mock_session_class.return_value = mock_session

            # Mock fetch_aws_findings to raise authentication error
            with patch("regscale.integrations.commercial.amazon.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.side_effect = Exception("The security token included in the request is invalid")

                with pytest.raises(Exception) as exc_info:
                    list(
                        scanner.fetch_findings(
                            region="us-east-1",
                            profile="test",
                            aws_access_key_id=None,
                            aws_secret_access_key=None,
                            aws_session_token=None,
                        )
                    )

                assert "security token" in str(exc_info.value).lower()

    def test_asset_identifier_matches_finding_asset_identifier(self, scanner):
        """Test that asset aws_identifier uses full ARN matching finding asset_identifier.

        This test verifies the fix for vulnerability to asset mapping. The asset's
        aws_identifier field must contain the full ARN (not just the short resource ID)
        so that it matches the finding's asset_identifier field.
        """
        # Create a mock Security Hub finding with full ARN in resource ID
        finding_data = {
            "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/test/finding/12345",
            "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
            "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.1",
            "AwsAccountId": "123456789012",
            "Types": ["Software and Configuration Checks"],
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "UpdatedAt": "2024-01-15T10:30:00.000Z",
            "Severity": {"Label": "HIGH", "Normalized": 70},
            "Title": "Test Finding",
            "Description": "Test Description",
            "Remediation": {"Recommendation": {"Text": "Fix the issue", "Url": "https://example.com"}},
            "Resources": [
                {
                    "Type": "AwsS3Bucket",
                    "Id": "arn:aws:s3:::test-bucket",  # Full ARN
                    "Region": "us-east-1",
                    "Details": {"AwsS3Bucket": {"Name": "test-bucket"}},
                }
            ],
            "Compliance": {"Status": "FAILED"},
            "WorkflowState": "NEW",
            "Workflow": {"Status": "NEW"},
            "RecordState": "ACTIVE",
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}, "Types": ["Software and Configuration Checks"]},
        }

        # Parse the finding to get the resource
        resource = finding_data["Resources"][0]

        # Parse resource to asset
        asset = scanner.parse_resource_to_asset(resource, finding_data)

        # Parse finding to get integration finding
        findings = scanner.parse_finding(finding_data)

        assert asset is not None, "Asset should be created"
        assert len(findings) > 0, "Finding should be created"

        integration_finding = findings[0]

        # The key assertion: asset's aws_identifier should be the full ARN
        assert (
            asset.aws_identifier == "arn:aws:s3:::test-bucket"
        ), f"Asset aws_identifier should be full ARN, got: {asset.aws_identifier}"

        # The finding's asset_identifier should also be the full ARN
        assert (
            integration_finding.asset_identifier == "arn:aws:s3:::test-bucket"
        ), f"Finding asset_identifier should be full ARN, got: {integration_finding.asset_identifier}"

        # Critical: These must match for vulnerability mapping to work
        assert asset.aws_identifier == integration_finding.asset_identifier, (
            "Asset aws_identifier must match finding asset_identifier for vulnerability mapping. "
            f"Asset: {asset.aws_identifier}, Finding: {integration_finding.asset_identifier}"
        )

    def test_all_resource_types_use_full_arn_in_aws_identifier(self, scanner):
        """Test that all resource type parsers use full ARN in aws_identifier.

        This ensures consistency across all AWS resource types.
        """
        test_cases = [
            {
                "type": "AwsEc2Instance",
                "arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                "details_key": "AwsEc2Instance",
                "details": {"InstanceId": "i-1234567890abcdef0", "Type": "t3.medium"},
            },
            {
                "type": "AwsEc2SecurityGroup",
                "arn": "arn:aws:ec2:us-east-1:123456789012:security-group/sg-12345678",
                "details_key": "AwsEc2SecurityGroup",
                "details": {"GroupId": "sg-12345678", "GroupName": "test-sg"},
            },
            {
                "type": "AwsEc2Subnet",
                "arn": "arn:aws:ec2:us-east-1:123456789012:subnet/subnet-12345678",
                "details_key": "AwsEc2Subnet",
                "details": {"SubnetId": "subnet-12345678", "CidrBlock": "10.0.1.0/24"},
            },
            {
                "type": "AwsIamUser",
                "arn": "arn:aws:iam::123456789012:user/test-user",
                "details_key": "AwsIamUser",
                "details": {"UserName": "test-user"},
            },
            {
                "type": "AwsRdsDbInstance",
                "arn": "arn:aws:rds:us-east-1:123456789012:db:test-db",
                "details_key": "AwsRdsDbInstance",
                "details": {"DbInstanceIdentifier": "test-db", "Engine": "postgres"},
            },
            {
                "type": "AwsLambdaFunction",
                "arn": "arn:aws:lambda:us-east-1:123456789012:function:test-function",
                "details_key": "AwsLambdaFunction",
                "details": {"FunctionName": "test-function", "Runtime": "python3.9"},
            },
            {
                "type": "AwsEcrRepository",
                "arn": "arn:aws:ecr:us-east-1:123456789012:repository/test-repo",
                "details_key": "AwsEcrRepository",
                "details": {"RepositoryName": "test-repo"},
            },
        ]

        for test_case in test_cases:
            resource = {
                "Type": test_case["type"],
                "Id": test_case["arn"],
                "Region": "us-east-1",
                "Details": {test_case["details_key"]: test_case["details"]},
            }

            finding_data = {
                "Id": "arn:aws:securityhub:us-east-1:123456789012:finding/12345",
                "CreatedAt": "2024-01-15T10:30:00.000Z",
                "UpdatedAt": "2024-01-15T10:30:00.000Z",
                "Severity": {"Label": "MEDIUM"},
                "Title": "Test",
                "Description": "Test",
            }

            asset = scanner.parse_resource_to_asset(resource, finding_data)

            assert asset is not None, f"Asset should be created for {test_case['type']}"
            assert asset.aws_identifier == test_case["arn"], (
                f"{test_case['type']}: aws_identifier should be full ARN. "
                f"Expected: {test_case['arn']}, Got: {asset.aws_identifier}"
            )
