#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for AWS Security Hub config filtering functionality."""

from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.commercial.aws.scanner import AWSInventoryIntegration
from regscale.integrations.commercial.aws.security_hub import SecurityHubPuller


class TestSecurityHubSeverityFiltering:
    """Test suite for SecurityHubPuller severity filtering functionality."""

    def test_get_severity_filters_from_minimum_critical(self):
        """Test severity filter generation with CRITICAL minimum."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("CRITICAL")
        assert result == ["CRITICAL"]

    def test_get_severity_filters_from_minimum_high(self):
        """Test severity filter generation with HIGH minimum."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("HIGH")
        assert result == ["HIGH", "CRITICAL"]

    def test_get_severity_filters_from_minimum_medium(self):
        """Test severity filter generation with MEDIUM minimum."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("MEDIUM")
        # MODERATE is excluded as it's an alias
        assert result == ["MEDIUM", "HIGH", "CRITICAL"]

    def test_get_severity_filters_from_minimum_moderate_alias(self):
        """Test severity filter generation with MODERATE minimum (alias for MEDIUM)."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("MODERATE")
        # Should convert MODERATE to MEDIUM and exclude MODERATE from results
        assert result == ["MEDIUM", "HIGH", "CRITICAL"]
        assert "MODERATE" not in result

    def test_get_severity_filters_from_minimum_low(self):
        """Test severity filter generation with LOW minimum."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("LOW")
        # MODERATE is excluded as it's an alias
        assert result == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "MODERATE" not in result

    def test_get_severity_filters_from_minimum_informational(self):
        """Test severity filter generation with INFORMATIONAL minimum."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("INFORMATIONAL")
        # Should return all severities except MODERATE (alias)
        assert result == ["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "MODERATE" not in result

    def test_get_severity_filters_from_minimum_case_insensitive(self):
        """Test severity filter generation is case insensitive."""
        result_lower = SecurityHubPuller.get_severity_filters_from_minimum("high")
        result_upper = SecurityHubPuller.get_severity_filters_from_minimum("HIGH")
        result_mixed = SecurityHubPuller.get_severity_filters_from_minimum("HiGh")

        assert result_lower == result_upper == result_mixed
        assert result_lower == ["HIGH", "CRITICAL"]

    def test_get_severity_filters_from_minimum_unknown_defaults_to_low(self):
        """Test severity filter generation with unknown severity defaults to LOW."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("UNKNOWN")
        # Should default to LOW
        assert result == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_get_severity_filters_from_minimum_empty_string_defaults_to_low(self):
        """Test severity filter generation with empty string defaults to LOW."""
        result = SecurityHubPuller.get_severity_filters_from_minimum("")
        # Should default to LOW
        assert result == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class TestAWSInventoryIntegrationServiceFiltering:
    """Test suite for AWSInventoryIntegration enabled_services filtering."""

    @pytest.fixture
    def mock_app_all_services_enabled(self):
        """Create mock app with all services enabled."""
        app = MagicMock()
        app.config = {
            "aws": {
                "inventory": {
                    "enabled_services": {
                        "compute": {"enabled": True, "services": {"ec2": True, "lambda": True}},
                        "storage": {"enabled": True, "services": {"s3": True}},
                        "database": {"enabled": True, "services": {"rds": True, "dynamodb": True}},
                        "networking": {"enabled": True, "services": {"vpc": True}},
                        "security": {
                            "enabled": True,
                            "services": {
                                "iam": True,
                                "kms": True,
                                "secrets_manager": True,
                                "securityhub": True,
                                "cloudtrail": True,
                                "config": True,
                                "guardduty": True,
                                "inspector": True,
                                "audit_manager": True,
                            },
                        },
                        "containers": {"enabled": True, "services": {"ecr": True}},
                    }
                }
            }
        }
        return app

    @pytest.fixture
    def mock_app_partial_services_enabled(self):
        """Create mock app with only some services enabled."""
        app = MagicMock()
        app.config = {
            "aws": {
                "inventory": {
                    "enabled_services": {
                        "compute": {"enabled": True, "services": {"ec2": True, "lambda": False}},
                        "storage": {"enabled": True, "services": {"s3": True}},
                        "database": {"enabled": True, "services": {"rds": False, "dynamodb": True}},
                        "security": {"enabled": True, "services": {"iam": True, "kms": False, "securityhub": True}},
                    }
                }
            }
        }
        return app

    @pytest.fixture
    def mock_app_no_config(self):
        """Create mock app with no enabled_services config."""
        app = MagicMock()
        app.config = {}
        return app

    @pytest.fixture
    def scanner_all_enabled(self, mock_app_all_services_enabled):
        """Create scanner with all services enabled."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_all_services_enabled
        return scanner

    @pytest.fixture
    def scanner_partial_enabled(self, mock_app_partial_services_enabled):
        """Create scanner with partial services enabled."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_partial_services_enabled
        return scanner

    @pytest.fixture
    def scanner_no_config(self, mock_app_no_config):
        """Create scanner with no config."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_no_config
        return scanner

    def test_is_service_enabled_for_resource_ec2_enabled(self, scanner_all_enabled):
        """Test EC2 resource when EC2 service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsEc2Instance") is True

    def test_is_service_enabled_for_resource_ec2_disabled(self, scanner_partial_enabled):
        """Test EC2 resource when EC2 service is enabled (partial config)."""
        # EC2 is enabled in partial config
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsEc2Instance") is True

    def test_is_service_enabled_for_resource_lambda_enabled(self, scanner_all_enabled):
        """Test Lambda resource when Lambda service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsLambdaFunction") is True

    def test_is_service_enabled_for_resource_lambda_disabled(self, scanner_partial_enabled):
        """Test Lambda resource when Lambda service is disabled."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsLambdaFunction") is False

    def test_is_service_enabled_for_resource_s3_enabled(self, scanner_all_enabled):
        """Test S3 resource when S3 service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsS3Bucket") is True

    def test_is_service_enabled_for_resource_s3_enabled_partial(self, scanner_partial_enabled):
        """Test S3 resource when S3 service is enabled (partial config)."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsS3Bucket") is True

    def test_is_service_enabled_for_resource_rds_enabled(self, scanner_all_enabled):
        """Test RDS resource when RDS service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsRdsDbInstance") is True

    def test_is_service_enabled_for_resource_rds_disabled(self, scanner_partial_enabled):
        """Test RDS resource when RDS service is disabled."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsRdsDbInstance") is False

    def test_is_service_enabled_for_resource_dynamodb_enabled(self, scanner_all_enabled):
        """Test DynamoDB resource when DynamoDB service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsDynamoDbTable") is True

    def test_is_service_enabled_for_resource_dynamodb_enabled_partial(self, scanner_partial_enabled):
        """Test DynamoDB resource when DynamoDB service is enabled (partial config)."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsDynamoDbTable") is True

    def test_is_service_enabled_for_resource_iam_enabled(self, scanner_all_enabled):
        """Test IAM User resource when IAM service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsIamUser") is True

    def test_is_service_enabled_for_resource_iam_role_enabled(self, scanner_all_enabled):
        """Test IAM Role resource when IAM service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsIamRole") is True

    def test_is_service_enabled_for_resource_iam_enabled_partial(self, scanner_partial_enabled):
        """Test IAM resources when IAM service is enabled (partial config)."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsIamUser") is True
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsIamRole") is True

    def test_is_service_enabled_for_resource_kms_enabled(self, scanner_all_enabled):
        """Test KMS resource when KMS service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsKmsKey") is True

    def test_is_service_enabled_for_resource_kms_disabled(self, scanner_partial_enabled):
        """Test KMS resource when KMS service is disabled."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsKmsKey") is False

    def test_is_service_enabled_for_resource_secrets_manager_enabled(self, scanner_all_enabled):
        """Test Secrets Manager resource when service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsSecretsManagerSecret") is True

    def test_is_service_enabled_for_resource_security_group_enabled(self, scanner_all_enabled):
        """Test Security Group resource when SecurityHub is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsEc2SecurityGroup") is True

    def test_is_service_enabled_for_resource_security_group_enabled_partial(self, scanner_partial_enabled):
        """Test Security Group resource when SecurityHub is enabled (partial config)."""
        assert scanner_partial_enabled.is_service_enabled_for_resource("AwsEc2SecurityGroup") is True

    def test_is_service_enabled_for_resource_subnet_enabled(self, scanner_all_enabled):
        """Test Subnet resource when VPC service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsEc2Subnet") is True

    def test_is_service_enabled_for_resource_ecr_enabled(self, scanner_all_enabled):
        """Test ECR resource when ECR service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsEcrRepository") is True

    def test_is_service_enabled_for_resource_cloudtrail_enabled(self, scanner_all_enabled):
        """Test CloudTrail resource when CloudTrail service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsCloudTrailTrail") is True

    def test_is_service_enabled_for_resource_config_enabled(self, scanner_all_enabled):
        """Test Config resource when Config service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsConfigConfigurationRecorder") is True

    def test_is_service_enabled_for_resource_guardduty_enabled(self, scanner_all_enabled):
        """Test GuardDuty resource when GuardDuty service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsGuardDutyDetector") is True

    def test_is_service_enabled_for_resource_inspector_enabled(self, scanner_all_enabled):
        """Test Inspector resource when Inspector service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsInspector2") is True

    def test_is_service_enabled_for_resource_audit_manager_enabled(self, scanner_all_enabled):
        """Test Audit Manager resource when Audit Manager service is enabled."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsAuditManagerAssessment") is True

    def test_is_service_enabled_for_resource_unknown_type_defaults_true(self, scanner_all_enabled):
        """Test unknown resource type defaults to enabled (fail-safe)."""
        assert scanner_all_enabled.is_service_enabled_for_resource("AwsUnknownResource") is True

    def test_is_service_enabled_for_resource_no_config_defaults_true(self, scanner_no_config):
        """Test resource with no config defaults to enabled (fail-safe)."""
        assert scanner_no_config.is_service_enabled_for_resource("AwsEc2Instance") is True
        assert scanner_no_config.is_service_enabled_for_resource("AwsS3Bucket") is True
        assert scanner_no_config.is_service_enabled_for_resource("AwsIamUser") is True

    def test_is_service_enabled_for_resource_empty_string_defaults_true(self, scanner_all_enabled):
        """Test empty resource type defaults to enabled (fail-safe)."""
        assert scanner_all_enabled.is_service_enabled_for_resource("") is True


class TestAWSInventoryIntegrationConfigReading:
    """Test suite for AWSInventoryIntegration config reading in fetch_findings."""

    @pytest.fixture
    def mock_app_with_severity_config(self):
        """Create mock app with minimumSeverity config."""
        app = MagicMock()
        app.config = {
            "issues": {
                "amazon": {
                    "status": "Open",
                    "minimumSeverity": "HIGH",
                    "low": 30,
                    "moderate": 15,
                    "high": 7,
                }
            },
            "aws": {"inventory": {"enabled_services": {"compute": {"ec2": True}}}},
        }
        return app

    @pytest.fixture
    def scanner_with_config(self, mock_app_with_severity_config):
        """Create scanner with severity config."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_with_severity_config
        return scanner

    def test_fetch_findings_reads_minimum_severity_from_config(self, scanner_with_config):
        """Test that fetch_findings reads minimumSeverity from config."""
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.meta.region_name = "us-east-1"

        with patch("boto3.Session", return_value=mock_session):
            with patch("regscale.integrations.commercial.aws.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = []

                # Call fetch_findings
                list(
                    scanner_with_config.fetch_findings(
                        region="us-east-1",
                        profile="test",
                        aws_access_key_id=None,
                        aws_secret_access_key=None,
                        aws_session_token=None,
                    )
                )

                # Verify fetch_aws_findings was called with minimum_severity
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                assert call_args[1]["minimum_severity"] == "HIGH"

    def test_fetch_findings_passes_none_when_no_severity_config(self):
        """Test that fetch_findings passes None when no minimumSeverity config."""
        app = MagicMock()
        app.config = {"issues": {"amazon": {"status": "Open"}}}
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = app

        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_session.meta.region_name = "us-east-1"

        with patch("boto3.Session", return_value=mock_session):
            with patch("regscale.integrations.commercial.aws.common.fetch_aws_findings") as mock_fetch:
                mock_fetch.return_value = []

                # Call fetch_findings
                list(
                    scanner.fetch_findings(
                        region="us-east-1",
                        profile="test",
                        aws_access_key_id=None,
                        aws_secret_access_key=None,
                        aws_session_token=None,
                    )
                )

                # Verify fetch_aws_findings was called with None
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                assert call_args[1]["minimum_severity"] is None


class TestParseFindingServiceFiltering:
    """Test suite for parse_finding service filtering logic."""

    @pytest.fixture
    def mock_app_ec2_disabled(self):
        """Create mock app with EC2 service disabled."""
        app = MagicMock()
        app.config = {
            "issues": {"amazon": {"status": "Open", "minimumSeverity": "LOW"}},
            "aws": {"inventory": {"enabled_services": {"compute": {"enabled": True, "services": {"ec2": False}}}}},
        }
        return app

    @pytest.fixture
    def mock_app_s3_disabled(self):
        """Create mock app with S3 service disabled."""
        app = MagicMock()
        app.config = {
            "issues": {"amazon": {"status": "Open", "minimumSeverity": "LOW"}},
            "aws": {"inventory": {"enabled_services": {"storage": {"enabled": True, "services": {"s3": False}}}}},
        }
        return app

    @pytest.fixture
    def scanner_ec2_disabled(self, mock_app_ec2_disabled):
        """Create scanner with EC2 disabled."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_ec2_disabled
        return scanner

    @pytest.fixture
    def scanner_s3_disabled(self, mock_app_s3_disabled):
        """Create scanner with S3 disabled."""
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = mock_app_s3_disabled
        return scanner

    def test_parse_finding_filters_disabled_ec2_resource(self, scanner_ec2_disabled):
        """Test that parse_finding filters out findings for disabled EC2 service."""
        finding = {
            "Id": "test-finding-id",
            "Title": "Test EC2 Finding",
            "Description": "Test description",
            "Severity": {"Label": "HIGH"},
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com"}},
            "Types": ["Software and Configuration Checks"],
            "Resources": [
                {
                    "Type": "AwsEc2Instance",
                    "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "Region": "us-east-1",
                    "Details": {"AwsEc2Instance": {"Type": "t3.medium"}},
                }
            ],
            "Compliance": {"Status": "FAILED"},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        findings = scanner_ec2_disabled.parse_finding(finding)

        # Should return empty list because EC2 is disabled
        assert len(findings) == 0

    def test_parse_finding_filters_disabled_s3_resource(self, scanner_s3_disabled):
        """Test that parse_finding filters out findings for disabled S3 service."""
        finding = {
            "Id": "test-finding-id",
            "Title": "Test S3 Finding",
            "Description": "Test description",
            "Severity": {"Label": "HIGH"},
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com"}},
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
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        findings = scanner_s3_disabled.parse_finding(finding)

        # Should return empty list because S3 is disabled
        assert len(findings) == 0

    def test_parse_finding_allows_enabled_service(self):
        """Test that parse_finding allows findings for enabled services."""
        app = MagicMock()
        app.config = {
            "issues": {"amazon": {"status": "Open", "minimumSeverity": "LOW"}},
            "aws": {"inventory": {"enabled_services": {"compute": {"enabled": True, "services": {"ec2": True}}}}},
        }
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = app

        finding = {
            "Id": "test-finding-id",
            "Title": "Test EC2 Finding",
            "Description": "Test description",
            "Severity": {"Label": "HIGH"},
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com"}},
            "Types": ["Software and Configuration Checks"],
            "Resources": [
                {
                    "Type": "AwsEc2Instance",
                    "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "Region": "us-east-1",
                    "Tags": {"Name": "test-instance"},
                    "Details": {"AwsEc2Instance": {"Type": "t3.medium"}},
                }
            ],
            "Compliance": {"Status": "FAILED"},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        findings = scanner.parse_finding(finding)

        # Should return the finding because EC2 is enabled
        assert len(findings) == 1
        assert findings[0].title == "Test EC2 Finding"

    def test_parse_finding_with_multiple_resources_mixed_enabled(self):
        """Test parse_finding with multiple resources where some services are disabled."""
        app = MagicMock()
        app.config = {
            "issues": {"amazon": {"status": "Open", "minimumSeverity": "LOW"}},
            "aws": {
                "inventory": {
                    "enabled_services": {
                        "compute": {"enabled": True, "services": {"ec2": True}},
                        "storage": {"enabled": True, "services": {"s3": False}},
                    }
                }
            },
        }
        scanner = AWSInventoryIntegration(plan_id=36)
        scanner.app = app

        finding = {
            "Id": "test-finding-id",
            "Title": "Test Multi-Resource Finding",
            "Description": "Test description",
            "Severity": {"Label": "HIGH"},
            "CreatedAt": "2024-01-15T10:30:00.000Z",
            "Remediation": {"Recommendation": {"Text": "Fix this", "Url": "https://example.com"}},
            "Types": ["Software and Configuration Checks"],
            "Resources": [
                {
                    "Type": "AwsEc2Instance",
                    "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "Region": "us-east-1",
                    "Tags": {"Name": "test-instance"},
                    "Details": {"AwsEc2Instance": {"Type": "t3.medium"}},
                },
                {
                    "Type": "AwsS3Bucket",
                    "Id": "arn:aws:s3:::test-bucket",
                    "Region": "us-east-1",
                    "Details": {"AwsS3Bucket": {"Name": "test-bucket"}},
                },
            ],
            "Compliance": {"Status": "FAILED"},
            "FindingProviderFields": {"Severity": {"Label": "HIGH"}},
        }

        findings = scanner.parse_finding(finding)

        # Should return only 1 finding for EC2 (S3 is filtered out)
        assert len(findings) == 1
        # The asset_identifier is the full resource ID (ARN) from the finding
        assert findings[0].asset_identifier == "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
