#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS CloudTrail Control Mappings."""

import pytest

from regscale.integrations.commercial.aws.cloudtrail_control_mappings import (
    CLOUDTRAIL_CONTROL_MAPPINGS,
    CloudTrailControlMapper,
)


class TestCloudTrailControlMapper:
    """Test CloudTrailControlMapper class."""

    def test_init_default_framework(self):
        """Test initialization with default framework."""
        mapper = CloudTrailControlMapper()
        assert mapper.framework == "NIST800-53R5"
        assert mapper.mappings == CLOUDTRAIL_CONTROL_MAPPINGS

    def test_init_custom_framework(self):
        """Test initialization with custom framework."""
        mapper = CloudTrailControlMapper(framework="ISO27001")
        assert mapper.framework == "ISO27001"
        assert mapper.mappings == CLOUDTRAIL_CONTROL_MAPPINGS

    def test_get_mapped_controls(self):
        """Test getting list of mapped controls."""
        mapper = CloudTrailControlMapper()
        controls = mapper.get_mapped_controls()
        assert isinstance(controls, list)
        assert len(controls) > 0
        assert "AU-2" in controls
        assert "AU-3" in controls
        assert "AU-6" in controls
        assert "AU-9" in controls
        assert "AU-11" in controls
        assert "AU-12" in controls
        assert "SI-4" in controls

    def test_get_control_description_valid(self):
        """Test getting control description for valid control."""
        mapper = CloudTrailControlMapper()
        description = mapper.get_control_description("AU-2")
        assert description is not None
        assert "Event Logging" in description
        assert "Identify the types of events" in description

    def test_get_control_description_invalid(self):
        """Test getting control description for invalid control."""
        mapper = CloudTrailControlMapper()
        description = mapper.get_control_description("INVALID-CONTROL")
        assert description is None

    def test_get_check_details_valid(self):
        """Test getting check details for valid control."""
        mapper = CloudTrailControlMapper()
        checks = mapper.get_check_details("AU-2")
        assert checks is not None
        assert isinstance(checks, dict)
        assert "trail_enabled" in checks
        assert "management_events" in checks
        assert checks["trail_enabled"]["weight"] == 100

    def test_get_check_details_invalid(self):
        """Test getting check details for invalid control."""
        mapper = CloudTrailControlMapper()
        checks = mapper.get_check_details("INVALID-CONTROL")
        assert checks is None


class TestAssessTrailCompliance:
    """Test assess_trail_compliance method."""

    def test_assess_trail_compliance_all_pass(self):
        """Test assessment when all controls pass."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True, "DataResources": [{"Type": "AWS::S3::Object"}]}],
            "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:test",
            "LogFileValidationEnabled": True,
            "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/test",
            "S3BucketName": "test-bucket",
            "IsMultiRegionTrail": True,
            "SnsTopicARN": "arn:aws:sns:us-east-1:123456789012:test-topic",
        }
        results = mapper.assess_trail_compliance(trail_data)
        assert results["AU-2"] == "PASS"
        assert results["AU-3"] == "PASS"
        assert results["AU-6"] == "PASS"
        assert results["AU-9"] == "PASS"
        assert results["AU-11"] == "PASS"
        assert results["AU-12"] == "PASS"
        assert results["SI-4"] == "PASS"

    def test_assess_trail_compliance_non_nist_framework(self):
        """Test assessment with non-NIST framework returns empty results."""
        mapper = CloudTrailControlMapper(framework="ISO27001")
        trail_data = {"Name": "test-trail"}
        results = mapper.assess_trail_compliance(trail_data)
        assert results == {}


class TestAssessAU2:
    """Test _assess_au2 (Event Logging) compliance."""

    def test_au2_pass_logging_enabled_with_management_events(self):
        """Test AU-2 passes when trail is logging with management events."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True}],
        }
        result = mapper._assess_au2(trail_data)
        assert result == "PASS"

    def test_au2_fail_logging_disabled(self):
        """Test AU-2 fails when trail is not logging."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": False},
            "EventSelectors": [{"IncludeManagementEvents": True}],
        }
        result = mapper._assess_au2(trail_data)
        assert result == "FAIL"

    def test_au2_fail_no_management_events(self):
        """Test AU-2 fails when management events not enabled."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": False}],
        }
        result = mapper._assess_au2(trail_data)
        assert result == "FAIL"

    def test_au2_fail_empty_event_selectors(self):
        """Test AU-2 fails with empty event selectors."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "Status": {"IsLogging": True}, "EventSelectors": []}
        result = mapper._assess_au2(trail_data)
        assert result == "FAIL"

    def test_au2_pass_multiple_event_selectors(self):
        """Test AU-2 passes with multiple event selectors where one has management events."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": True},
            "EventSelectors": [
                {"IncludeManagementEvents": False},
                {"IncludeManagementEvents": True},
            ],
        }
        result = mapper._assess_au2(trail_data)
        assert result == "PASS"


class TestAssessAU3:
    """Test _assess_au3 (Content of Audit Records) compliance."""

    def test_au3_pass_event_selectors_configured(self):
        """Test AU-3 passes when event selectors are configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "EventSelectors": [{"IncludeManagementEvents": True}]}
        result = mapper._assess_au3(trail_data)
        assert result == "PASS"

    def test_au3_fail_no_event_selectors(self):
        """Test AU-3 fails when no event selectors configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "EventSelectors": []}
        result = mapper._assess_au3(trail_data)
        assert result == "FAIL"

    def test_au3_fail_missing_event_selectors(self):
        """Test AU-3 fails when EventSelectors key is missing."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_au3(trail_data)
        assert result == "FAIL"


class TestAssessAU6:
    """Test _assess_au6 (Audit Record Review) compliance."""

    def test_au6_pass_cloudwatch_integration(self):
        """Test AU-6 passes when CloudWatch Logs integration is configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:test",
        }
        result = mapper._assess_au6(trail_data)
        assert result == "PASS"

    def test_au6_fail_no_cloudwatch_integration(self):
        """Test AU-6 fails when no CloudWatch Logs integration."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_au6(trail_data)
        assert result == "FAIL"

    def test_au6_fail_empty_cloudwatch_arn(self):
        """Test AU-6 fails when CloudWatch ARN is empty."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "CloudWatchLogsLogGroupArn": ""}
        result = mapper._assess_au6(trail_data)
        assert result == "FAIL"


class TestAssessAU9:
    """Test _assess_au9 (Protection of Audit Information) compliance."""

    def test_au9_pass_log_validation_and_encryption(self):
        """Test AU-9 passes when log validation and encryption are enabled."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "LogFileValidationEnabled": True,
            "KmsKeyId": "arn:aws:kms:us-east-1:123456789012:key/test",
        }
        result = mapper._assess_au9(trail_data)
        assert result == "PASS"

    def test_au9_pass_log_validation_without_encryption(self):
        """Test AU-9 passes when log validation enabled but no encryption (recommended)."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "LogFileValidationEnabled": True}
        result = mapper._assess_au9(trail_data)
        assert result == "PASS"

    def test_au9_fail_no_log_validation(self):
        """Test AU-9 fails when log file validation not enabled."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "LogFileValidationEnabled": False}
        result = mapper._assess_au9(trail_data)
        assert result == "FAIL"

    def test_au9_fail_missing_log_validation_key(self):
        """Test AU-9 fails when LogFileValidationEnabled key is missing."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_au9(trail_data)
        assert result == "FAIL"


class TestAssessAU11:
    """Test _assess_au11 (Audit Record Retention) compliance."""

    def test_au11_pass_s3_bucket_configured(self):
        """Test AU-11 passes when S3 bucket is configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "S3BucketName": "test-bucket"}
        result = mapper._assess_au11(trail_data)
        assert result == "PASS"

    def test_au11_fail_no_s3_bucket(self):
        """Test AU-11 fails when no S3 bucket configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_au11(trail_data)
        assert result == "FAIL"

    def test_au11_fail_empty_s3_bucket(self):
        """Test AU-11 fails when S3 bucket name is empty."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "S3BucketName": ""}
        result = mapper._assess_au11(trail_data)
        assert result == "FAIL"


class TestAssessAU12:
    """Test _assess_au12 (Audit Record Generation) compliance."""

    def test_au12_pass_multi_region_with_data_events(self):
        """Test AU-12 passes when multi-region trail with data events."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "IsMultiRegionTrail": True,
            "EventSelectors": [{"DataResources": [{"Type": "AWS::S3::Object"}]}],
        }
        result = mapper._assess_au12(trail_data)
        assert result == "PASS"

    def test_au12_pass_multi_region_without_data_events(self):
        """Test AU-12 passes when multi-region trail without data events (recommended)."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "IsMultiRegionTrail": True, "EventSelectors": []}
        result = mapper._assess_au12(trail_data)
        assert result == "PASS"

    def test_au12_fail_not_multi_region(self):
        """Test AU-12 fails when not a multi-region trail."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "IsMultiRegionTrail": False, "EventSelectors": []}
        result = mapper._assess_au12(trail_data)
        assert result == "FAIL"

    def test_au12_fail_missing_multi_region_key(self):
        """Test AU-12 fails when IsMultiRegionTrail key is missing."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_au12(trail_data)
        assert result == "FAIL"


class TestAssessSI4:
    """Test _assess_si4 (System Monitoring) compliance."""

    def test_si4_pass_sns_notifications_configured(self):
        """Test SI-4 passes when SNS notifications are configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "SnsTopicARN": "arn:aws:sns:us-east-1:123456789012:test-topic"}
        result = mapper._assess_si4(trail_data)
        assert result == "PASS"

    def test_si4_fail_no_sns_notifications(self):
        """Test SI-4 fails when no SNS notifications configured."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail"}
        result = mapper._assess_si4(trail_data)
        assert result == "FAIL"

    def test_si4_fail_empty_sns_arn(self):
        """Test SI-4 fails when SNS ARN is empty."""
        mapper = CloudTrailControlMapper()
        trail_data = {"Name": "test-trail", "SnsTopicARN": ""}
        result = mapper._assess_si4(trail_data)
        assert result == "FAIL"


class TestAssessAllTrailsCompliance:
    """Test assess_all_trails_compliance method."""

    def test_assess_empty_trails_list(self):
        """Test assessment with empty trails list."""
        mapper = CloudTrailControlMapper()
        results = mapper.assess_all_trails_compliance([])
        assert results["AU-2"] == "FAIL"
        assert results["AU-3"] == "FAIL"
        assert results["AU-6"] == "FAIL"
        assert results["AU-9"] == "FAIL"
        assert results["AU-11"] == "FAIL"
        assert results["AU-12"] == "FAIL"
        assert results["SI-4"] == "FAIL"

    def test_assess_single_trail_all_pass(self):
        """Test assessment with single trail that passes all controls."""
        mapper = CloudTrailControlMapper()
        trail_data = {
            "Name": "test-trail",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True}],
            "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:test",
            "LogFileValidationEnabled": True,
            "S3BucketName": "test-bucket",
            "IsMultiRegionTrail": True,
            "SnsTopicARN": "arn:aws:sns:us-east-1:123456789012:test-topic",
        }
        results = mapper.assess_all_trails_compliance([trail_data])
        assert results["AU-2"] == "PASS"
        assert results["AU-3"] == "PASS"
        assert results["AU-6"] == "PASS"
        assert results["AU-9"] == "PASS"
        assert results["AU-11"] == "PASS"
        assert results["AU-12"] == "PASS"
        assert results["SI-4"] == "PASS"

    def test_assess_multiple_trails_aggregate_pass(self):
        """Test assessment with multiple trails where aggregate results pass."""
        mapper = CloudTrailControlMapper()
        trail1 = {
            "Name": "trail1",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True}],
            "CloudWatchLogsLogGroupArn": "arn:aws:logs:us-east-1:123456789012:log-group:test",
            "LogFileValidationEnabled": True,
            "S3BucketName": "test-bucket",
            "IsMultiRegionTrail": False,
            "SnsTopicARN": "arn:aws:sns:us-east-1:123456789012:test-topic",
        }
        trail2 = {
            "Name": "trail2",
            "Status": {"IsLogging": True},
            "EventSelectors": [{"IncludeManagementEvents": True}],
            "CloudWatchLogsLogGroupArn": "",
            "LogFileValidationEnabled": True,
            "S3BucketName": "test-bucket",
            "IsMultiRegionTrail": True,
            "SnsTopicARN": "",
        }
        results = mapper.assess_all_trails_compliance([trail1, trail2])
        assert results["AU-2"] == "PASS"
        assert results["AU-12"] == "PASS"

    def test_assess_multiple_trails_all_fail(self):
        """Test assessment with multiple trails where all fail a control."""
        mapper = CloudTrailControlMapper()
        trail1 = {"Name": "trail1", "Status": {"IsLogging": False}, "EventSelectors": []}
        trail2 = {"Name": "trail2", "Status": {"IsLogging": False}, "EventSelectors": []}
        results = mapper.assess_all_trails_compliance([trail1, trail2])
        assert results["AU-2"] == "FAIL"


class TestCloudTrailControlMappings:
    """Test CLOUDTRAIL_CONTROL_MAPPINGS structure."""

    def test_mappings_exist(self):
        """Test that mappings dictionary exists and has content."""
        assert len(CLOUDTRAIL_CONTROL_MAPPINGS) > 0

    def test_au2_mapping_structure(self):
        """Test AU-2 mapping structure."""
        assert "AU-2" in CLOUDTRAIL_CONTROL_MAPPINGS
        au2 = CLOUDTRAIL_CONTROL_MAPPINGS["AU-2"]
        assert "name" in au2
        assert "description" in au2
        assert "checks" in au2
        assert "trail_enabled" in au2["checks"]
        assert "management_events" in au2["checks"]

    def test_au9_mapping_structure(self):
        """Test AU-9 mapping structure with multiple checks."""
        assert "AU-9" in CLOUDTRAIL_CONTROL_MAPPINGS
        au9 = CLOUDTRAIL_CONTROL_MAPPINGS["AU-9"]
        assert len(au9["checks"]) >= 2
        assert "log_file_validation" in au9["checks"]
        assert "s3_encryption" in au9["checks"]

    def test_all_controls_have_required_fields(self):
        """Test all control mappings have required fields."""
        for control_id, control_data in CLOUDTRAIL_CONTROL_MAPPINGS.items():
            assert "name" in control_data
            assert "description" in control_data
            assert "checks" in control_data
            assert isinstance(control_data["checks"], dict)
            for check_name, check_data in control_data["checks"].items():
                assert "weight" in check_data
                assert "pass_criteria" in check_data
                assert "fail_criteria" in check_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
