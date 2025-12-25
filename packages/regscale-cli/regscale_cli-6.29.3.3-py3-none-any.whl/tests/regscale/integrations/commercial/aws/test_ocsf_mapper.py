"""Unit tests for AWS OCSF Mapper."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.commercial.aws.ocsf import constants
from regscale.integrations.commercial.aws.ocsf.mapper import AWSOCSFMapper


class TestAWSOCSFMapper(unittest.TestCase):
    """Test cases for AWSOCSFMapper."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = AWSOCSFMapper()

    def test_init(self):
        """Test AWSOCSFMapper initialization."""
        assert self.mapper.ocsf_version == constants.OCSF_VERSION

    def test_guardduty_to_ocsf(self):
        """Test GuardDuty finding to OCSF mapping."""
        finding = {
            "Id": "test-finding-123",
            "Arn": "arn:aws:guardduty:us-east-1:123456789012:detector/test/finding/test-finding-123",
            "AccountId": "123456789012",
            "Region": "us-east-1",
            "Partition": "aws",
            "Severity": 8.0,
            "Confidence": 7.5,
            "Type": "UnauthorizedAccess:IAMUser/MaliciousIPCaller.Custom",
            "Title": "Test Finding",
            "Description": "Test description",
            "CreatedAt": "2025-10-13T12:00:00Z",
            "UpdatedAt": "2025-10-13T12:30:00Z",
            "Service": {
                "Archived": False,
                "Count": 1,
            },
            "Resource": {
                "ResourceType": "Instance",
                "InstanceDetails": {
                    "InstanceId": "i-1234567890abcdef0",
                },
            },
        }

        result = self.mapper.guardduty_to_ocsf(finding)

        # Verify OCSF structure
        assert result["class_uid"] == constants.CLASS_DETECTION_FINDING
        assert result["class_name"] == "Detection Finding"
        assert result["severity_id"] == constants.SEVERITY_HIGH
        assert result["confidence_id"] == constants.CONFIDENCE_HIGH
        assert result["finding_info"]["uid"] == "test-finding-123"
        assert result["finding_info"]["title"] == "Test Finding"
        assert result["cloud"]["provider"] == "AWS"
        assert result["cloud"]["account"]["uid"] == "123456789012"
        assert result["raw_data"] == finding

    def test_securityhub_to_ocsf(self):
        """Test Security Hub finding to OCSF mapping."""
        finding = {
            "Id": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/EC2.1/finding/test",
            "ProductArn": "arn:aws:securityhub:us-east-1::product/aws/securityhub",
            "ProductName": "Security Hub",
            "AwsAccountId": "123456789012",
            "Region": "us-east-1",
            "Title": "Test Security Finding",
            "Description": "Test security description",
            "Severity": {
                "Label": "HIGH",
                "Normalized": 70,
            },
            "Workflow": {
                "Status": "NEW",
            },
            "Types": [
                "Software and Configuration Checks/AWS Security Best Practices",
            ],
            "CreatedAt": "2025-10-13T12:00:00Z",
            "UpdatedAt": "2025-10-13T12:30:00Z",
            "FirstObservedAt": "2025-10-13T11:00:00Z",
            "LastObservedAt": "2025-10-13T12:30:00Z",
            "Compliance": {
                "Status": "FAILED",
                "RelatedRequirements": ["PCI-DSS 3.2.1/1.2.1"],
            },
            "Resources": [
                {
                    "Type": "AwsEc2Instance",
                    "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "Region": "us-east-1",
                    "Partition": "aws",
                    "Details": {},
                }
            ],
            "Vulnerabilities": [
                {
                    "Id": "CVE-2021-1234",
                    "ReferenceUrls": ["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-1234"],
                    "Vendor": {"Name": "AWS"},
                    "Cvss": [{"BaseScore": 7.5}],
                }
            ],
            "Remediation": {
                "Recommendation": {
                    "Text": "Enable VPC flow logs",
                    "Url": "https://docs.aws.amazon.com/",
                }
            },
        }

        result = self.mapper.securityhub_to_ocsf(finding)

        # Verify OCSF structure
        assert result["class_uid"] == constants.CLASS_SECURITY_FINDING
        assert result["class_name"] == "Security Finding"
        assert result["severity_id"] == constants.SEVERITY_HIGH
        assert result["status_id"] == constants.STATUS_NEW
        assert result["finding_info"]["title"] == "Test Security Finding"
        assert result["compliance"]["status"] == "FAILED"
        assert len(result["resources"]) == 1
        assert result["vulnerabilities"] is not None
        assert result["remediation"]["desc"] == "Enable VPC flow logs"

    def test_cloudtrail_event_to_ocsf(self):
        """Test CloudTrail event to OCSF mapping."""
        event = {
            "EventTime": "2025-10-13T12:00:00Z",
            "EventName": "DescribeInstances",
            "EventSource": "ec2.amazonaws.com",
            "RequestID": "test-request-123",
            "RecipientAccountId": "123456789012",
            "AwsRegion": "us-east-1",
            "UserIdentity": {
                "Type": "IAMUser",
                "PrincipalId": "AIDAI23HXS8K7EXAMPLE",
                "UserName": "testuser",
            },
            "SourceIPAddress": "203.0.113.1",
            "UserAgent": "aws-cli/2.0.0",
            "Resources": [
                {
                    "ARN": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                    "ResourceType": "AWS::EC2::Instance",
                    "ResourceName": "test-instance",
                }
            ],
        }

        result = self.mapper.cloudtrail_event_to_ocsf(event)

        # Verify OCSF structure
        assert result["class_uid"] == constants.CLASS_CLOUD_API
        assert result["class_name"] == "Cloud API"
        assert result["activity_name"] == "DescribeInstances"
        assert result["api"]["operation"] == "DescribeInstances"
        assert result["api"]["service"]["name"] == "ec2"
        assert result["actor"]["user"]["name"] == "testuser"
        assert result["src_endpoint"]["ip"] == "203.0.113.1"
        assert len(result["resources"]) == 1

    def test_cloudtrail_event_with_error(self):
        """Test CloudTrail event with error code."""
        event = {
            "EventTime": "2025-10-13T12:00:00Z",
            "EventName": "DescribeInstances",
            "EventSource": "ec2.amazonaws.com",
            "RequestID": "test-request-123",
            "RecipientAccountId": "123456789012",
            "AwsRegion": "us-east-1",
            "ErrorCode": "AccessDenied",
            "ErrorMessage": "User is not authorized",
            "UserIdentity": {},
        }

        result = self.mapper.cloudtrail_event_to_ocsf(event)

        # Error events should have higher severity
        assert result["severity_id"] == constants.SEVERITY_MEDIUM
        assert result["api"]["response"]["error"] == "AccessDenied"
        assert result["api"]["response"]["message"] == "User is not authorized"

    def test_map_guardduty_activity_create(self):
        """Test GuardDuty activity mapping for new finding."""
        finding = {
            "Service": {
                "Archived": False,
                "Count": 1,
            }
        }

        result = self.mapper._map_guardduty_activity(finding)
        assert result == constants.ACTIVITY_CREATE

    def test_map_guardduty_activity_update(self):
        """Test GuardDuty activity mapping for updated finding."""
        finding = {
            "Service": {
                "Archived": False,
                "Count": 5,
            }
        }

        result = self.mapper._map_guardduty_activity(finding)
        assert result == constants.ACTIVITY_UPDATE

    def test_map_guardduty_activity_close(self):
        """Test GuardDuty activity mapping for archived finding."""
        finding = {
            "Service": {
                "Archived": True,
                "Count": 3,
            }
        }

        result = self.mapper._map_guardduty_activity(finding)
        assert result == constants.ACTIVITY_CLOSE

    def test_map_securityhub_activity(self):
        """Test Security Hub activity mapping."""
        assert self.mapper._map_securityhub_activity("NEW") == constants.ACTIVITY_CREATE
        assert self.mapper._map_securityhub_activity("NOTIFIED") == constants.ACTIVITY_UPDATE
        assert self.mapper._map_securityhub_activity("RESOLVED") == constants.ACTIVITY_CLOSE
        assert self.mapper._map_securityhub_activity("SUPPRESSED") == constants.ACTIVITY_CLOSE
        assert self.mapper._map_securityhub_activity("UNKNOWN") == constants.ACTIVITY_OTHER

    def test_map_guardduty_confidence(self):
        """Test GuardDuty confidence mapping."""
        assert self.mapper._map_guardduty_confidence(8.0) == constants.CONFIDENCE_HIGH
        assert self.mapper._map_guardduty_confidence(5.0) == constants.CONFIDENCE_MEDIUM
        assert self.mapper._map_guardduty_confidence(2.0) == constants.CONFIDENCE_LOW
        assert self.mapper._map_guardduty_confidence(0) == constants.CONFIDENCE_UNKNOWN

    def test_map_securityhub_resources(self):
        """Test Security Hub resources mapping."""
        resources = [
            {
                "Id": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
                "Type": "AwsEc2Instance",
                "Region": "us-east-1",
                "Partition": "aws",
                "Details": {"AwsEc2Instance": {"InstanceId": "i-1234567890abcdef0"}},
            }
        ]

        result = self.mapper._map_securityhub_resources(resources)

        assert len(result) == 1
        assert result[0]["uid"] == "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"
        assert result[0]["type"] == "AwsEc2Instance"
        assert result[0]["region"] == "us-east-1"
        assert "data" in result[0]

    def test_map_cloudtrail_resources(self):
        """Test CloudTrail resources mapping."""
        resources = [
            {
                "ARN": "arn:aws:s3:::test-bucket",
                "ResourceType": "AWS::S3::Bucket",
                "ResourceName": "test-bucket",
            }
        ]

        result = self.mapper._map_cloudtrail_resources(resources)

        assert len(result) == 1
        assert result[0]["uid"] == "arn:aws:s3:::test-bucket"
        assert result[0]["type"] == "AWS::S3::Bucket"
        assert result[0]["name"] == "test-bucket"

    def test_extract_vulnerabilities(self):
        """Test vulnerability extraction from Security Hub finding."""
        finding = {
            "Vulnerabilities": [
                {
                    "Id": "CVE-2021-1234",
                    "ReferenceUrls": ["https://cve.mitre.org/"],
                    "Vendor": {"Name": "AWS"},
                    "Cvss": [{"BaseScore": 7.5}],
                }
            ]
        }

        result = self.mapper._extract_vulnerabilities(finding)

        assert len(result) == 1
        assert result[0]["cve"]["uid"] == "CVE-2021-1234"
        assert result[0]["vendor_name"] == "AWS"
        assert "cvss" in result[0]

    def test_extract_vulnerabilities_empty(self):
        """Test vulnerability extraction with no vulnerabilities."""
        finding = {"Vulnerabilities": []}

        result = self.mapper._extract_vulnerabilities(finding)

        assert result is None

    def test_determine_cloudtrail_severity(self):
        """Test CloudTrail event severity determination."""
        # Unauthorized access
        assert self.mapper._determine_cloudtrail_severity({"ErrorCode": "AccessDenied"}) == constants.SEVERITY_MEDIUM
        assert (
            self.mapper._determine_cloudtrail_severity({"ErrorCode": "UnauthorizedOperation"})
            == constants.SEVERITY_MEDIUM
        )

        # Other errors
        assert self.mapper._determine_cloudtrail_severity({"ErrorCode": "InvalidParameter"}) == constants.SEVERITY_LOW

        # Success
        assert self.mapper._determine_cloudtrail_severity({}) == constants.SEVERITY_INFORMATIONAL

    @patch("regscale.integrations.commercial.aws.ocsf.mapper.logger")
    def test_parse_aws_timestamp_success(self, mock_logger):
        """Test AWS timestamp parsing success."""
        timestamp = "2025-10-13T12:00:00Z"
        result = self.mapper._parse_aws_timestamp(timestamp)

        assert result is not None
        assert isinstance(result, int)

    @patch("regscale.integrations.commercial.aws.ocsf.mapper.logger")
    def test_parse_aws_timestamp_none(self, mock_logger):
        """Test AWS timestamp parsing with None."""
        result = self.mapper._parse_aws_timestamp(None)
        assert result is None

    @patch("regscale.integrations.commercial.aws.ocsf.mapper.logger")
    def test_parse_aws_timestamp_invalid(self, mock_logger):
        """Test AWS timestamp parsing with invalid format."""
        result = self.mapper._parse_aws_timestamp("invalid-timestamp")
        assert result is None
        mock_logger.warning.assert_called_once()

    def test_get_severity_name(self):
        """Test OCSF severity name retrieval."""
        assert self.mapper._get_severity_name(constants.SEVERITY_CRITICAL) == "Critical"
        assert self.mapper._get_severity_name(constants.SEVERITY_HIGH) == "High"
        assert self.mapper._get_severity_name(constants.SEVERITY_MEDIUM) == "Medium"
        assert self.mapper._get_severity_name(constants.SEVERITY_LOW) == "Low"
        assert self.mapper._get_severity_name(constants.SEVERITY_INFORMATIONAL) == "Informational"
        assert self.mapper._get_severity_name(constants.SEVERITY_UNKNOWN) == "Unknown"
        assert self.mapper._get_severity_name(999) == "Unknown"

    def test_get_status_name(self):
        """Test OCSF status name retrieval."""
        assert self.mapper._get_status_name(constants.STATUS_NEW) == "New"
        assert self.mapper._get_status_name(constants.STATUS_IN_PROGRESS) == "In Progress"
        assert self.mapper._get_status_name(constants.STATUS_SUPPRESSED) == "Suppressed"
        assert self.mapper._get_status_name(constants.STATUS_RESOLVED) == "Resolved"
        assert self.mapper._get_status_name(constants.STATUS_OTHER) == "Other"
        assert self.mapper._get_status_name(999) == "Other"

    def test_get_activity_name(self):
        """Test OCSF activity name retrieval."""
        assert self.mapper._get_activity_name(constants.ACTIVITY_CREATE) == "Create"
        assert self.mapper._get_activity_name(constants.ACTIVITY_UPDATE) == "Update"
        assert self.mapper._get_activity_name(constants.ACTIVITY_CLOSE) == "Close"
        assert self.mapper._get_activity_name(constants.ACTIVITY_OTHER) == "Other"
        assert self.mapper._get_activity_name(999) == "Other"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
