#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test configuration for AWS integrations using moto for AWS service mocking."""

import os
from unittest.mock import MagicMock, patch

import pytest
from moto import mock_aws


class AWSResponseMock(dict):
    """
    A dict subclass that returns None for common AWS pagination keys.

    This prevents infinite loops when code checks `response.get("NextToken")` etc.
    With regular MagicMock, `.get("NextToken")` returns another MagicMock (truthy),
    which causes pagination loops to never terminate.
    """

    # Common AWS pagination keys that should return None by default
    PAGINATION_KEYS = {
        "NextToken",
        "nextToken",
        "NextMarker",
        "nextMarker",
        "Marker",
        "ContinuationToken",
        "ExclusiveStartKey",
        "LastEvaluatedKey",
    }

    # Common AWS boolean pagination keys that should return False by default
    PAGINATION_BOOL_KEYS = {
        "IsTruncated",
        "HasMoreDeliveryStreams",
        "HasMore",
        "Truncated",
    }

    def get(self, key, default=None):
        """Return None for pagination keys, False for boolean pagination keys."""
        if key in self.PAGINATION_KEYS and key not in self:
            return None
        if key in self.PAGINATION_BOOL_KEYS and key not in self:
            return False
        return super().get(key, default)


def create_aws_response(**kwargs) -> AWSResponseMock:
    """
    Create an AWS API response mock that handles pagination correctly.

    Usage:
        mock_client.list_work_groups.return_value = create_aws_response(
            WorkGroups=[{"Name": "primary"}]
        )

    This automatically sets NextToken=None to terminate pagination.
    """
    return AWSResponseMock(kwargs)


@pytest.fixture(scope="function", autouse=True)
def aws_credentials():
    """
    Set fake AWS credentials for moto.

    This prevents tests from trying to use real AWS credentials
    and ensures moto mocking works correctly.
    """
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    yield


@pytest.fixture(scope="function", autouse=True)
def mock_all_aws_services():
    """
    Mock all AWS services using moto.

    This fixture automatically mocks ALL AWS services for every test.
    Moto handles:
    - Pagination (no infinite loops!)
    - Proper response structures
    - Realistic AWS behavior
    - No real API calls
    """
    with mock_aws():
        yield


@pytest.fixture(autouse=True)
def mock_boto3_session_legacy():
    """
    Mock boto3 session creation to prevent real AWS API calls.

    This fixture runs automatically for all tests in the AWS test directory.
    It ensures that boto3.Session() returns a properly configured mock
    that prevents any real AWS API calls during testing.
    """
    with patch("boto3.Session") as mock_session_class:
        mock_session = MagicMock()
        mock_client = MagicMock()

        # Configure default mock client responses for common Audit Manager operations
        # IMPORTANT: All paginated responses must include nextToken=None to prevent infinite loops
        mock_client.list_assessments.return_value = {"assessmentMetadata": [], "nextToken": None}
        mock_client.list_assessment_frameworks.return_value = {"frameworkMetadataList": [], "nextToken": None}
        mock_client.list_controls.return_value = {"controlMetadataList": [], "nextToken": None}
        mock_client.get_settings.return_value = {"settings": {}}
        mock_client.get_assessment.return_value = {"assessment": {}}
        mock_client.list_tags_for_resource.return_value = {"tags": {}}
        mock_client.get_paginator.return_value = MagicMock()
        # Audit Manager evidence collection - must have nextToken=None to terminate pagination
        mock_client.get_evidence_folders_by_assessment.return_value = {"evidenceFolders": [], "nextToken": None}
        mock_client.get_evidence_folders_by_assessment_control.return_value = {"evidenceFolders": [], "nextToken": None}
        mock_client.get_evidence_by_evidence_folder.return_value = {"evidence": [], "nextToken": None}

        # Configure default mock client responses for Security Hub operations
        mock_client.get_findings.return_value = {"Findings": [], "NextToken": None}
        mock_client.describe_hub.return_value = {}

        # Configure default mock client responses for GuardDuty operations
        mock_client.list_detectors.return_value = {"DetectorIds": [], "NextToken": None}
        mock_client.list_findings.return_value = {"FindingIds": [], "NextToken": None}
        mock_client.get_findings.return_value = {"Findings": [], "NextToken": None}

        # Configure default mock client responses for IAM operations
        # IAM uses 'Marker' for pagination instead of 'NextToken'
        mock_client.list_users.return_value = {"Users": [], "Marker": None, "IsTruncated": False}
        mock_client.list_roles.return_value = {"Roles": [], "Marker": None, "IsTruncated": False}
        mock_client.list_groups.return_value = {"Groups": [], "Marker": None, "IsTruncated": False}
        mock_client.list_policies.return_value = {"Policies": [], "Marker": None, "IsTruncated": False}

        # Configure default mock client responses for S3 operations
        mock_client.list_buckets.return_value = {"Buckets": []}

        # Configure default mock client responses for KMS operations
        mock_client.list_keys.return_value = {"Keys": [], "NextMarker": None, "Truncated": False}

        # Configure default mock client responses for CloudTrail operations
        mock_client.describe_trails.return_value = {"trailList": []}

        # Configure default mock client responses for Config operations
        mock_client.describe_config_rules.return_value = {"ConfigRules": [], "NextToken": None}
        mock_client.describe_conformance_packs.return_value = {"ConformancePackDetails": [], "NextToken": None}

        # Configure default mock client responses for SSM operations
        mock_client.describe_instance_information.return_value = {"InstanceInformationList": [], "NextToken": None}

        # Configure default mock client responses for Inspector operations
        mock_client.list_findings.return_value = {"findings": [], "nextToken": None}

        # Configure default mock client responses for VPC operations
        mock_client.describe_vpcs.return_value = {"Vpcs": [], "NextToken": None}
        mock_client.describe_subnets.return_value = {"Subnets": [], "NextToken": None}
        mock_client.describe_security_groups.return_value = {"SecurityGroups": [], "NextToken": None}

        # Configure default mock client responses for STS operations
        mock_client.get_caller_identity.return_value = {
            "UserId": "AIDAEXAMPLE123456789",
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/testuser",
        }

        # Configure default mock client responses for Organizations operations
        mock_client.describe_organization.return_value = {"Organization": {}}
        mock_client.list_accounts.return_value = {"Accounts": [], "NextToken": None}

        # Set up the session to return the mock client
        mock_session.client.return_value = mock_client
        mock_session.region_name = "us-east-1"
        mock_session_class.return_value = mock_session

        yield {
            "session_class": mock_session_class,
            "session": mock_session,
            "client": mock_client,
        }


@pytest.fixture
def mock_audit_manager_client():
    """
    Create a mock Audit Manager client with configurable responses.

    This fixture provides a dedicated mock client for Audit Manager tests
    that allows tests to configure specific responses for their scenarios.
    """
    client = MagicMock()

    # Setup default paginator behavior
    paginator = MagicMock()
    paginator.paginate.return_value = []
    client.get_paginator.return_value = paginator

    # Setup default responses
    client.list_assessments.return_value = {"assessmentMetadata": []}
    client.list_assessment_frameworks.return_value = {"frameworkMetadataList": []}
    client.list_controls.return_value = {"controlMetadataList": []}
    client.get_settings.return_value = {"settings": {}}
    client.get_assessment.return_value = {"assessment": {}}
    client.list_tags_for_resource.return_value = {"tags": {}}

    return client
