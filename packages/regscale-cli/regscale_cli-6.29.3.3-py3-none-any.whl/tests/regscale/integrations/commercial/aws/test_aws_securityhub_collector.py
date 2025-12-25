#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Security Hub collector."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.securityhub import SecurityHubCollector


class TestSecurityHubCollector:
    """Test suite for AWS Security Hub collector."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock AWS session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_client(self):
        """Create a mock Security Hub client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def collector_no_account(self, mock_session):
        """Create a SecurityHub collector without account_id."""
        return SecurityHubCollector(session=mock_session, region="us-east-1", account_id=None)

    @pytest.fixture
    def collector_with_account(self, mock_session):
        """Create a SecurityHub collector with account_id."""
        return SecurityHubCollector(session=mock_session, region="us-east-1", account_id="123456789012")

    def test_initialization_without_account_id(self, mock_session):
        """Test initialization without account_id."""
        collector = SecurityHubCollector(session=mock_session, region="us-west-2")

        assert collector.session == mock_session
        assert collector.region == "us-west-2"
        assert collector.account_id is None

    def test_initialization_with_account_id(self, mock_session):
        """Test initialization with account_id."""
        collector = SecurityHubCollector(session=mock_session, region="us-west-2", account_id="123456789012")

        assert collector.session == mock_session
        assert collector.region == "us-west-2"
        assert collector.account_id == "123456789012"

    @patch.object(SecurityHubCollector, "_get_client")
    @patch.object(SecurityHubCollector, "_describe_hub")
    @patch.object(SecurityHubCollector, "_get_enabled_standards")
    @patch.object(SecurityHubCollector, "_describe_standards")
    @patch.object(SecurityHubCollector, "_list_security_controls")
    @patch.object(SecurityHubCollector, "_get_findings")
    @patch.object(SecurityHubCollector, "_get_insights")
    @patch.object(SecurityHubCollector, "_list_members")
    def test_collect_success(
        self,
        mock_list_members,
        mock_get_insights,
        mock_get_findings,
        mock_list_controls,
        mock_describe_standards,
        mock_get_enabled_standards,
        mock_describe_hub,
        mock_get_client,
        collector_no_account,
        mock_client,
    ):
        """Test successful collection of all Security Hub resources."""
        mock_get_client.return_value = mock_client

        # Setup mock returns
        mock_hub_config = {"HubArn": "arn:aws:securityhub:us-east-1:123456789012:hub/default", "Region": "us-east-1"}
        mock_describe_hub.return_value = mock_hub_config

        mock_enabled_stds = [
            {
                "StandardsArn": "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0"
            }
        ]
        mock_get_enabled_standards.return_value = mock_enabled_stds

        mock_standards = [
            {
                "StandardsArn": "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0",
                "Name": "AWS Foundational Security Best Practices",
            }
        ]
        mock_describe_standards.return_value = mock_standards

        mock_controls = [
            {"SecurityControlId": "IAM.1", "Title": "IAM policies should not allow full '*' administrative privileges"}
        ]
        mock_list_controls.return_value = mock_controls

        mock_findings = [{"Id": "finding-1", "Title": "Test Finding", "Region": "us-east-1"}]
        mock_get_findings.return_value = mock_findings

        mock_insights = [
            {
                "InsightArn": "arn:aws:securityhub:us-east-1:123456789012:insight/123456789012/custom/abc123",
                "Name": "Test Insight",
            }
        ]
        mock_get_insights.return_value = mock_insights

        mock_members = [{"AccountId": "123456789012", "Email": "test@example.com"}]
        mock_list_members.return_value = mock_members

        # Execute
        result = collector_no_account.collect()

        # Verify structure
        assert "Findings" in result
        assert "Standards" in result
        assert "EnabledStandards" in result
        assert "SecurityControls" in result
        assert "HubConfiguration" in result
        assert "Members" in result
        assert "Insights" in result

        # Verify content
        assert result["HubConfiguration"] == mock_hub_config
        assert result["EnabledStandards"] == mock_enabled_stds
        assert result["Standards"] == mock_standards
        assert result["SecurityControls"] == mock_controls
        assert result["Findings"] == mock_findings
        assert result["Insights"] == mock_insights
        assert result["Members"] == mock_members

        # Verify method calls
        mock_get_client.assert_called_once_with("securityhub")
        mock_describe_hub.assert_called_once()
        mock_get_enabled_standards.assert_called_once()
        mock_describe_standards.assert_called_once()
        mock_list_controls.assert_called_once()
        mock_get_findings.assert_called_once()
        mock_get_insights.assert_called_once()
        mock_list_members.assert_called_once()

    def test_describe_hub_success(self, collector_no_account, mock_client):
        """Test successful hub configuration retrieval."""
        mock_response = {
            "HubArn": "arn:aws:securityhub:us-east-1:123456789012:hub/default",
            "SubscribedAt": datetime(2024, 1, 1, 12, 0, 0),
            "AutoEnableControls": True,
            "ControlFindingGenerator": "SECURITY_CONTROL",
        }
        mock_client.describe_hub.return_value = mock_response

        result = collector_no_account._describe_hub(mock_client)

        assert result["Region"] == "us-east-1"
        assert result["HubArn"] == "arn:aws:securityhub:us-east-1:123456789012:hub/default"
        assert result["AutoEnableControls"] is True
        assert result["ControlFindingGenerator"] == "SECURITY_CONTROL"
        assert "2024-01-01" in result["SubscribedAt"]
        mock_client.describe_hub.assert_called_once()

    def test_describe_hub_invalid_access_exception(self, collector_no_account, mock_client):
        """Test hub configuration retrieval with InvalidAccessException."""
        mock_client.describe_hub.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Account is not subscribed"}},
            "DescribeHub",
        )

        result = collector_no_account._describe_hub(mock_client)

        assert result == {}
        mock_client.describe_hub.assert_called_once()

    def test_describe_hub_resource_not_found_exception(self, collector_no_account, mock_client):
        """Test hub configuration retrieval with ResourceNotFoundException."""
        mock_client.describe_hub.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Hub not found"}},
            "DescribeHub",
        )

        result = collector_no_account._describe_hub(mock_client)

        assert result == {}
        mock_client.describe_hub.assert_called_once()

    def test_describe_hub_other_error(self, collector_no_account, mock_client):
        """Test hub configuration retrieval with other ClientError."""
        mock_client.describe_hub.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Internal error"}},
            "DescribeHub",
        )

        result = collector_no_account._describe_hub(mock_client)

        assert result == {}
        mock_client.describe_hub.assert_called_once()

    def test_get_enabled_standards_success_single_page(self, collector_no_account, mock_client):
        """Test successful enabled standards retrieval (single page)."""
        mock_response = {
            "StandardsSubscriptions": [
                {
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0",
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0",
                    "StandardsInput": {},
                    "StandardsStatus": "READY",
                }
            ]
        }
        mock_client.get_enabled_standards.return_value = mock_response

        result = collector_no_account._get_enabled_standards(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["StandardsStatus"] == "READY"
        assert "StandardsArn" in result[0]
        mock_client.get_enabled_standards.assert_called_once_with()

    def test_get_enabled_standards_pagination(self, collector_no_account, mock_client):
        """Test enabled standards retrieval with pagination."""
        mock_response_page1 = {
            "StandardsSubscriptions": [
                {
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/standard1",
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/standard1",
                    "StandardsInput": {},
                    "StandardsStatus": "READY",
                }
            ],
            "NextToken": "token123",
        }
        mock_response_page2 = {
            "StandardsSubscriptions": [
                {
                    "StandardsSubscriptionArn": "arn:aws:securityhub:us-east-1:123456789012:subscription/standard2",
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/standard2",
                    "StandardsInput": {},
                    "StandardsStatus": "READY",
                }
            ]
        }
        mock_client.get_enabled_standards.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._get_enabled_standards(mock_client)

        assert len(result) == 2
        assert result[0]["StandardsArn"] == "arn:aws:securityhub:us-east-1::standards/standard1"
        assert result[1]["StandardsArn"] == "arn:aws:securityhub:us-east-1::standards/standard2"
        assert mock_client.get_enabled_standards.call_count == 2

    def test_get_enabled_standards_invalid_access_exception(self, collector_no_account, mock_client):
        """Test enabled standards retrieval with InvalidAccessException."""
        mock_client.get_enabled_standards.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "GetEnabledStandards",
        )

        result = collector_no_account._get_enabled_standards(mock_client)

        assert result == []
        mock_client.get_enabled_standards.assert_called_once()

    def test_describe_standards_success_single_page(self, collector_no_account, mock_client):
        """Test successful standards description (single page)."""
        mock_response = {
            "Standards": [
                {
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0",
                    "Name": "AWS Foundational Security Best Practices",
                    "Description": "AWS Foundational Security Best Practices standard",
                    "EnabledByDefault": True,
                }
            ]
        }
        mock_client.describe_standards.return_value = mock_response

        result = collector_no_account._describe_standards(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["Name"] == "AWS Foundational Security Best Practices"
        assert result[0]["EnabledByDefault"] is True
        mock_client.describe_standards.assert_called_once_with()

    def test_describe_standards_pagination(self, collector_no_account, mock_client):
        """Test standards description with pagination."""
        mock_response_page1 = {
            "Standards": [
                {
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/standard1",
                    "Name": "Standard 1",
                    "Description": "First standard",
                    "EnabledByDefault": True,
                }
            ],
            "NextToken": "token123",
        }
        mock_response_page2 = {
            "Standards": [
                {
                    "StandardsArn": "arn:aws:securityhub:us-east-1::standards/standard2",
                    "Name": "Standard 2",
                    "Description": "Second standard",
                    "EnabledByDefault": False,
                }
            ]
        }
        mock_client.describe_standards.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._describe_standards(mock_client)

        assert len(result) == 2
        assert result[0]["Name"] == "Standard 1"
        assert result[1]["Name"] == "Standard 2"
        assert mock_client.describe_standards.call_count == 2

    def test_describe_standards_invalid_access_exception(self, collector_no_account, mock_client):
        """Test standards description with InvalidAccessException."""
        mock_client.describe_standards.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "DescribeStandards",
        )

        result = collector_no_account._describe_standards(mock_client)

        assert result == []
        mock_client.describe_standards.assert_called_once()

    def test_list_security_controls_success_single_page(self, collector_no_account, mock_client):
        """Test successful security controls listing (single page)."""
        mock_response = {
            "SecurityControlDefinitions": [
                {
                    "SecurityControlId": "IAM.1",
                    "Title": "IAM policies should not allow full '*' administrative privileges",
                    "Description": "This control checks whether the IAM policies allow full '*' administrative privileges",
                    "RemediationUrl": "https://docs.aws.amazon.com/console/securityhub/IAM.1/remediation",
                    "SeverityRating": "HIGH",
                    "CurrentRegionAvailability": "AVAILABLE",
                }
            ]
        }
        mock_client.list_security_control_definitions.return_value = mock_response

        result = collector_no_account._list_security_controls(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["SecurityControlId"] == "IAM.1"
        assert result[0]["SeverityRating"] == "HIGH"
        mock_client.list_security_control_definitions.assert_called_once_with(MaxResults=100)

    def test_list_security_controls_pagination(self, collector_no_account, mock_client):
        """Test security controls listing with pagination."""
        mock_response_page1 = {
            "SecurityControlDefinitions": [
                {
                    "SecurityControlId": "IAM.1",
                    "Title": "Control 1",
                    "Description": "Description 1",
                    "RemediationUrl": "https://example.com/1",
                    "SeverityRating": "HIGH",
                    "CurrentRegionAvailability": "AVAILABLE",
                }
            ],
            "NextToken": "token123",
        }
        mock_response_page2 = {
            "SecurityControlDefinitions": [
                {
                    "SecurityControlId": "IAM.2",
                    "Title": "Control 2",
                    "Description": "Description 2",
                    "RemediationUrl": "https://example.com/2",
                    "SeverityRating": "MEDIUM",
                    "CurrentRegionAvailability": "AVAILABLE",
                }
            ]
        }
        mock_client.list_security_control_definitions.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._list_security_controls(mock_client)

        assert len(result) == 2
        assert result[0]["SecurityControlId"] == "IAM.1"
        assert result[1]["SecurityControlId"] == "IAM.2"
        assert mock_client.list_security_control_definitions.call_count == 2

    def test_list_security_controls_invalid_access_exception(self, collector_no_account, mock_client):
        """Test security controls listing with InvalidAccessException."""
        mock_client.list_security_control_definitions.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "ListSecurityControlDefinitions",
        )

        result = collector_no_account._list_security_controls(mock_client)

        assert result == []
        mock_client.list_security_control_definitions.assert_called_once_with(MaxResults=100)

    def test_get_findings_success_single_page_no_account_filter(self, collector_no_account, mock_client):
        """Test successful findings retrieval (single page, no account filter)."""
        mock_response = {
            "Findings": [
                {
                    "Id": "finding-1",
                    "Title": "Test Finding 1",
                    "Description": "Test Description",
                    "Severity": {"Label": "HIGH"},
                }
            ]
        }
        mock_client.get_findings.return_value = mock_response

        result = collector_no_account._get_findings(mock_client)

        assert len(result) == 1
        assert result[0]["Id"] == "finding-1"
        assert result[0]["Region"] == "us-east-1"  # Verify Region tagging
        mock_client.get_findings.assert_called_once_with(MaxResults=100)

    def test_get_findings_success_with_account_filter(self, collector_with_account, mock_client):
        """Test successful findings retrieval with account filter."""
        mock_response = {
            "Findings": [
                {
                    "Id": "finding-1",
                    "Title": "Test Finding 1",
                    "AwsAccountId": "123456789012",
                    "Severity": {"Label": "HIGH"},
                }
            ]
        }
        mock_client.get_findings.return_value = mock_response

        result = collector_with_account._get_findings(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"  # Verify Region tagging
        # Verify account filter was applied
        call_args = mock_client.get_findings.call_args
        assert "Filters" in call_args[1]
        assert call_args[1]["Filters"]["AwsAccountId"][0]["Value"] == "123456789012"
        assert call_args[1]["Filters"]["AwsAccountId"][0]["Comparison"] == "EQUALS"

    def test_get_findings_pagination(self, collector_no_account, mock_client):
        """Test findings retrieval with pagination."""
        mock_response_page1 = {
            "Findings": [{"Id": "finding-1", "Title": "Finding 1"}],
            "NextToken": "token123",
        }
        mock_response_page2 = {"Findings": [{"Id": "finding-2", "Title": "Finding 2"}]}
        mock_client.get_findings.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._get_findings(mock_client)

        assert len(result) == 2
        assert result[0]["Id"] == "finding-1"
        assert result[0]["Region"] == "us-east-1"  # Verify Region tagging
        assert result[1]["Id"] == "finding-2"
        assert result[1]["Region"] == "us-east-1"  # Verify Region tagging
        assert mock_client.get_findings.call_count == 2

    def test_get_findings_invalid_access_exception(self, collector_no_account, mock_client):
        """Test findings retrieval with InvalidAccessException."""
        mock_client.get_findings.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "GetFindings",
        )

        result = collector_no_account._get_findings(mock_client)

        assert result == []
        mock_client.get_findings.assert_called_once()

    def test_get_insights_success_single_page(self, collector_no_account, mock_client):
        """Test successful insights retrieval (single page)."""
        mock_response = {
            "Insights": [
                {
                    "InsightArn": "arn:aws:securityhub:us-east-1:123456789012:insight/123456789012/custom/abc123",
                    "Name": "Test Insight",
                    "Filters": {"SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}]},
                    "GroupByAttribute": "ResourceType",
                }
            ]
        }
        mock_client.get_insights.return_value = mock_response

        result = collector_no_account._get_insights(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["Name"] == "Test Insight"
        assert result[0]["GroupByAttribute"] == "ResourceType"
        mock_client.get_insights.assert_called_once_with(MaxResults=100)

    def test_get_insights_pagination(self, collector_no_account, mock_client):
        """Test insights retrieval with pagination."""
        mock_response_page1 = {
            "Insights": [
                {
                    "InsightArn": "arn:aws:securityhub:us-east-1:123456789012:insight/123456789012/custom/abc123",
                    "Name": "Insight 1",
                    "Filters": {},
                    "GroupByAttribute": "ResourceType",
                }
            ],
            "NextToken": "token123",
        }
        mock_response_page2 = {
            "Insights": [
                {
                    "InsightArn": "arn:aws:securityhub:us-east-1:123456789012:insight/123456789012/custom/def456",
                    "Name": "Insight 2",
                    "Filters": {},
                    "GroupByAttribute": "SeverityLabel",
                }
            ]
        }
        mock_client.get_insights.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._get_insights(mock_client)

        assert len(result) == 2
        assert result[0]["Name"] == "Insight 1"
        assert result[1]["Name"] == "Insight 2"
        assert mock_client.get_insights.call_count == 2

    def test_get_insights_invalid_access_exception(self, collector_no_account, mock_client):
        """Test insights retrieval with InvalidAccessException."""
        mock_client.get_insights.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "GetInsights",
        )

        result = collector_no_account._get_insights(mock_client)

        assert result == []
        mock_client.get_insights.assert_called_once()

    def test_list_members_success_single_page_no_account_filter(self, collector_no_account, mock_client):
        """Test successful members listing (single page, no account filter)."""
        mock_response = {
            "Members": [
                {
                    "AccountId": "123456789012",
                    "Email": "account1@example.com",
                    "MasterId": "999999999999",
                    "AdministratorId": "999999999999",
                    "MemberStatus": "ENABLED",
                    "InvitedAt": datetime(2024, 1, 1, 12, 0, 0),
                    "UpdatedAt": datetime(2024, 1, 2, 12, 0, 0),
                }
            ]
        }
        mock_client.list_members.return_value = mock_response

        result = collector_no_account._list_members(mock_client)

        assert len(result) == 1
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["AccountId"] == "123456789012"
        assert result[0]["MemberStatus"] == "ENABLED"
        assert "2024-01-01" in result[0]["InvitedAt"]
        assert "2024-01-02" in result[0]["UpdatedAt"]
        mock_client.list_members.assert_called_once_with(MaxResults=50)

    def test_list_members_with_account_filter(self, collector_with_account, mock_client):
        """Test members listing with account filter."""
        mock_response = {
            "Members": [
                {
                    "AccountId": "123456789012",
                    "Email": "account1@example.com",
                    "MemberStatus": "ENABLED",
                },
                {
                    "AccountId": "999999999999",
                    "Email": "account2@example.com",
                    "MemberStatus": "ENABLED",
                },
            ]
        }
        mock_client.list_members.return_value = mock_response

        result = collector_with_account._list_members(mock_client)

        # Only the account matching the filter should be returned
        assert len(result) == 1
        assert result[0]["AccountId"] == "123456789012"
        assert result[0]["Region"] == "us-east-1"

    def test_list_members_pagination(self, collector_no_account, mock_client):
        """Test members listing with pagination."""
        mock_response_page1 = {
            "Members": [
                {
                    "AccountId": "123456789012",
                    "Email": "account1@example.com",
                    "MemberStatus": "ENABLED",
                }
            ],
            "NextToken": "token123",
        }
        mock_response_page2 = {
            "Members": [
                {
                    "AccountId": "999999999999",
                    "Email": "account2@example.com",
                    "MemberStatus": "ENABLED",
                }
            ]
        }
        mock_client.list_members.side_effect = [mock_response_page1, mock_response_page2]

        result = collector_no_account._list_members(mock_client)

        assert len(result) == 2
        assert result[0]["AccountId"] == "123456789012"
        assert result[1]["AccountId"] == "999999999999"
        assert mock_client.list_members.call_count == 2

    def test_list_members_invalid_access_exception(self, collector_no_account, mock_client):
        """Test members listing with InvalidAccessException."""
        mock_client.list_members.side_effect = ClientError(
            {"Error": {"Code": "InvalidAccessException", "Message": "Access denied"}},
            "ListMembers",
        )

        result = collector_no_account._list_members(mock_client)

        assert result == []
        mock_client.list_members.assert_called_once()

    def test_list_members_no_invited_at(self, collector_no_account, mock_client):
        """Test members listing with no InvitedAt or UpdatedAt fields."""
        mock_response = {
            "Members": [
                {
                    "AccountId": "123456789012",
                    "Email": "account1@example.com",
                    "MemberStatus": "ENABLED",
                }
            ]
        }
        mock_client.list_members.return_value = mock_response

        result = collector_no_account._list_members(mock_client)

        assert len(result) == 1
        assert result[0]["InvitedAt"] is None
        assert result[0]["UpdatedAt"] is None

    @patch.object(SecurityHubCollector, "_get_client")
    @patch.object(SecurityHubCollector, "_describe_hub")
    @patch.object(SecurityHubCollector, "_get_enabled_standards")
    @patch.object(SecurityHubCollector, "_describe_standards")
    @patch.object(SecurityHubCollector, "_list_security_controls")
    @patch.object(SecurityHubCollector, "_get_findings")
    @patch.object(SecurityHubCollector, "_get_insights")
    @patch.object(SecurityHubCollector, "_list_members")
    @patch.object(SecurityHubCollector, "_handle_error")
    def test_collect_handles_client_error(
        self,
        mock_handle_error,
        mock_list_members,
        mock_get_insights,
        mock_get_findings,
        mock_list_controls,
        mock_describe_standards,
        mock_get_enabled_standards,
        mock_describe_hub,
        mock_get_client,
        collector_no_account,
    ):
        """Test that collect properly handles ClientError."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        error = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "Access denied"}},
            "DescribeHub",
        )
        mock_describe_hub.side_effect = error

        # Mock other methods to return empty data
        mock_get_enabled_standards.return_value = []
        mock_describe_standards.return_value = []
        mock_list_controls.return_value = []
        mock_get_findings.return_value = []
        mock_get_insights.return_value = []
        mock_list_members.return_value = []

        result = collector_no_account.collect()

        # Should return empty structure
        assert "Findings" in result
        assert "Standards" in result
        assert result["Findings"] == []
        mock_handle_error.assert_called_once()

    @patch.object(SecurityHubCollector, "_get_client")
    @patch.object(SecurityHubCollector, "_describe_hub")
    @patch.object(SecurityHubCollector, "_get_enabled_standards")
    @patch.object(SecurityHubCollector, "_describe_standards")
    @patch.object(SecurityHubCollector, "_list_security_controls")
    @patch.object(SecurityHubCollector, "_get_findings")
    @patch.object(SecurityHubCollector, "_get_insights")
    @patch.object(SecurityHubCollector, "_list_members")
    def test_collect_handles_unexpected_error(
        self,
        mock_list_members,
        mock_get_insights,
        mock_get_findings,
        mock_list_controls,
        mock_describe_standards,
        mock_get_enabled_standards,
        mock_describe_hub,
        mock_get_client,
        collector_no_account,
    ):
        """Test that collect properly handles unexpected errors."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Cause an unexpected error
        mock_describe_hub.side_effect = ValueError("Unexpected error")

        # Mock other methods to return empty data
        mock_get_enabled_standards.return_value = []
        mock_describe_standards.return_value = []
        mock_list_controls.return_value = []
        mock_get_findings.return_value = []
        mock_get_insights.return_value = []
        mock_list_members.return_value = []

        result = collector_no_account.collect()

        # Should return empty structure and not raise
        assert "Findings" in result
        assert "Standards" in result
        assert result["Findings"] == []

    def test_region_tagging_in_all_methods(self, collector_no_account, mock_client):
        """Test that all methods properly tag resources with Region."""
        # Test _describe_hub
        mock_client.describe_hub.return_value = {"HubArn": "arn:test"}
        hub_result = collector_no_account._describe_hub(mock_client)
        assert hub_result["Region"] == "us-east-1"

        # Test _get_enabled_standards
        mock_client.get_enabled_standards.return_value = {
            "StandardsSubscriptions": [{"StandardsArn": "arn:test", "StandardsStatus": "READY"}]
        }
        standards_result = collector_no_account._get_enabled_standards(mock_client)
        assert all(s["Region"] == "us-east-1" for s in standards_result)

        # Test _describe_standards
        mock_client.describe_standards.return_value = {"Standards": [{"StandardsArn": "arn:test", "Name": "Test"}]}
        desc_standards_result = collector_no_account._describe_standards(mock_client)
        assert all(s["Region"] == "us-east-1" for s in desc_standards_result)

        # Test _list_security_controls
        mock_client.list_security_control_definitions.return_value = {
            "SecurityControlDefinitions": [{"SecurityControlId": "TEST.1", "Title": "Test"}]
        }
        controls_result = collector_no_account._list_security_controls(mock_client)
        assert all(c["Region"] == "us-east-1" for c in controls_result)

        # Test _get_findings
        mock_client.get_findings.return_value = {"Findings": [{"Id": "finding-1"}]}
        findings_result = collector_no_account._get_findings(mock_client)
        assert all(f["Region"] == "us-east-1" for f in findings_result)

        # Test _get_insights
        mock_client.get_insights.return_value = {"Insights": [{"InsightArn": "arn:test", "Name": "Test"}]}
        insights_result = collector_no_account._get_insights(mock_client)
        assert all(i["Region"] == "us-east-1" for i in insights_result)

        # Test _list_members
        mock_client.list_members.return_value = {
            "Members": [{"AccountId": "123456789012", "Email": "test@example.com"}]
        }
        members_result = collector_no_account._list_members(mock_client)
        assert all(m["Region"] == "us-east-1" for m in members_result)
