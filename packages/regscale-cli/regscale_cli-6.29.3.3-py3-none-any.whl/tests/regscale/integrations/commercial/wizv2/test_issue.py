import pytest
from unittest.mock import patch
from regscale.integrations.commercial.wizv2.issue import WizIssue
from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType
from regscale.models import IssueSeverity, IssueStatus


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_parse_finding_control_labels(mock_get_assessor):
    """Test that WizIssue correctly parses control labels from a Wiz issue."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    # Create test instance with a test plan ID
    wiz_issue = WizIssue(plan_id=1)

    # Sample Wiz issue data with security subcategories
    test_issue = {
        "id": "66013c7a-de84-4b46-a3c7-934521cb9e3b",
        "sourceRule": {
            "__typename": "Control",
            "id": "wc-id-15",
            "name": "Publicly exposed PaaS database server",
            "controlDescription": "This database is exposed to the public internet.",
            "resolutionRecommendation": "Limit external exposure",
            "securitySubCategories": [
                {
                    "title": "AC-4(21) Information Flow Enforcement | Physical or Logical Separation of Information Flows",
                    "externalId": "AC-4(21)",
                    "category": {"name": "AC Access Control", "framework": {"name": "NIST SP 800-53 Revision 5"}},
                },
                {
                    "title": "SC-7 Boundary Protection",
                    "externalId": "SC-7",
                    "category": {
                        "name": "SC System And Communications Protection",
                        "framework": {"name": "NIST SP 800-53 Revision 5"},
                    },
                },
                {
                    "title": "AC-3 Access Enforcement",
                    "externalId": "AC-3",
                    "category": {"name": "AC Access Control", "framework": {"name": "NIST SP 800-53 Revision 5"}},
                },
            ],
        },
        "severity": "HIGH",
        "status": "OPEN",
        "createdAt": "2024-02-21T08:22:22.696689Z",
        "entitySnapshot": {
            "id": "474c2882-b98a-5b2b-b2f5-40f6cbdbf04f",
            "type": "DB_SERVER",
            "name": "releasetest-sqlserver",
        },
    }

    # Parse the finding
    finding = wiz_issue.parse_finding(test_issue, WizVulnerabilityType.ISSUE)

    # Expected control labels based on NIST SP 800-53 controls
    expected_control_labels = ["ac-4.21", "sc-7", "ac-3"]

    # Verify the finding attributes
    assert finding is not None
    assert finding.control_labels == expected_control_labels
    assert finding.severity == IssueSeverity.High
    assert finding.title == "Publicly exposed PaaS database server"
    assert finding.asset_identifier == "474c2882-b98a-5b2b-b2f5-40f6cbdbf04f"
    assert finding.external_id == "66013c7a-de84-4b46-a3c7-934521cb9e3b"
    assert finding.plugin_name == "Wiz-Control-AC"
    assert finding.source_rule_id == "Control-wc-id-15"
    assert finding.vulnerability_type == WizVulnerabilityType.ISSUE.value


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_parse_finding_no_security_subcategories(mock_get_assessor):
    """Test that WizIssue handles issues without security subcategories."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    test_issue = {
        "id": "test-id",
        "sourceRule": {
            "__typename": "Control",
            "id": "wc-id-1",
            "name": "Test security configuration",
            "controlDescription": "Test description",
            "resolutionRecommendation": "Test recommendation",
            "securitySubCategories": [],
        },
        "severity": "MEDIUM",
        "status": "OPEN",
        "createdAt": "2024-02-21T08:22:22Z",
        "entitySnapshot": {"id": "test-entity-id", "type": "DB_SERVER", "name": "test-server"},
    }

    finding = wiz_issue.parse_finding(test_issue, WizVulnerabilityType.VULNERABILITY)

    assert finding is not None
    assert finding.control_labels == []
    assert finding.severity == IssueSeverity.Moderate
    assert finding.title == "Test security configuration"
    assert finding.plugin_name == "Wiz-Control-Test"
    assert finding.source_rule_id == "Control-wc-id-1"
    assert finding.vulnerability_type == WizVulnerabilityType.VULNERABILITY.value


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_parse_finding_non_nist_controls(mock_get_assessor):
    """Test that WizIssue correctly handles non-NIST controls."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    test_issue = {
        "id": "test-id",
        "sourceRule": {
            "__typename": "Control",
            "id": "wc-id-1",
            "name": "Database exposed to internet",
            "controlDescription": "Test description",
            "resolutionRecommendation": "Test recommendation",
            "securitySubCategories": [
                {
                    "title": "8.12 Data leakage prevention",
                    "externalId": "8.12",
                    "category": {"name": "Technological controls", "framework": {"name": "ISO/IEC 27001-2022"}},
                }
            ],
        },
        "severity": "LOW",
        "status": "OPEN",
        "createdAt": "2024-02-21T08:22:22Z",
        "entitySnapshot": {"id": "test-entity-id", "type": "DB_SERVER", "name": "test-server"},
    }

    finding = wiz_issue.parse_finding(test_issue, WizVulnerabilityType.HOST_FINDING)

    assert finding is not None
    assert finding.control_labels == []
    assert finding.severity == IssueSeverity.Low
    assert finding.title == "Database exposed to internet"
    assert finding.plugin_name == "Wiz-Control-Database"
    assert finding.source_rule_id == "Control-wc-id-1"
    assert finding.vulnerability_type == WizVulnerabilityType.HOST_FINDING.value


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_parse_finding_cloud_config_rule(mock_get_assessor):
    """Test that WizIssue correctly parses a cloud configuration rule."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    test_issue = {
        "id": "test-id",
        "sourceRule": {
            "__typename": "CloudConfigurationRule",
            "id": "ffcade8d-7961-4b71-93d3-0098d7e4b3e1",
            "name": "App Configuration public network access should be disabled",
            "cloudConfigurationRuleDescription": "Test description",
            "remediationInstructions": "Test remediation",
            "serviceType": "Azure",
        },
        "severity": "HIGH",
        "status": "OPEN",
        "createdAt": "2024-02-21T08:22:22Z",
        "entitySnapshot": {"id": "test-entity-id", "type": "SERVICE_CONFIGURATION", "name": "test-config"},
    }

    finding = wiz_issue.parse_finding(test_issue, WizVulnerabilityType.CONFIGURATION)

    assert finding is not None
    assert finding.plugin_name == "Wiz-Azure-AppConfiguration"
    assert finding.severity == IssueSeverity.High
    assert finding.title == "App Configuration public network access should be disabled"
    assert finding.source_rule_id == "CloudConfigurationRule-Azure-ffcade8d-7961-4b71-93d3-0098d7e4b3e1"
    assert finding.vulnerability_type == WizVulnerabilityType.CONFIGURATION.value


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_parse_finding_cloud_event(mock_get_assessor):
    """Test that WizIssue correctly parses a cloud event rule."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    test_issue = {
        "id": "test-id",
        "sourceRule": {
            "__typename": "CloudEventRule",
            "id": "event-1",
            "name": "Suspicious activity detection in cloud resources",
            "cloudEventRuleDescription": "Test description",
            "sourceType": "test",
            "type": "test",
            "serviceType": "AWS",
        },
        "severity": "LOW",
        "status": "OPEN",
        "createdAt": "2024-02-21T08:22:22Z",
        "entitySnapshot": {"id": "test-entity-id", "type": "CLOUD_ORGANIZATION", "name": "test-org"},
    }

    finding = wiz_issue.parse_finding(test_issue, WizVulnerabilityType.DATA_FINDING)

    assert finding is not None
    assert finding.plugin_name == "Wiz-AWS-SuspiciousActivity"
    assert finding.severity == IssueSeverity.Low
    assert finding.title == "Suspicious activity detection in cloud resources"
    assert finding.source_rule_id == "CloudEventRule-AWS-event-1"
    assert finding.vulnerability_type == WizVulnerabilityType.DATA_FINDING.value


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_title_based_consolidation(mock_get_assessor):
    """Test that issues with same title are consolidated regardless of asset."""
    # Mock the assessor ID
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    # Create two issues with same title but different assets
    issue1 = {
        "id": "issue-576",
        "sourceRule": {
            "__typename": "CloudConfigurationRule",
            "id": "rule-app-config",
            "name": "App Configuration public network access should be disabled",
            "serviceType": "Azure",
            "resolutionRecommendation": "Disable public network access",
        },
        "severity": "HIGH",
        "status": "OPEN",
        "createdAt": "2024-01-15T10:00:00Z",
        "entitySnapshot": {
            "id": "asset-001",
            "providerId": "/subscriptions/sub1/resourceGroups/rg1/providers/Microsoft.AppConfiguration/configurationStores/store1",
            "type": "SERVICE_CONFIGURATION",
            "name": "store1",
        },
    }

    issue2 = {
        "id": "issue-663",
        "sourceRule": {
            "__typename": "CloudConfigurationRule",
            "id": "rule-app-config",
            "name": "App Configuration public network access should be disabled",
            "serviceType": "Azure",
            "resolutionRecommendation": "Disable public network access",
        },
        "severity": "MEDIUM",
        "status": "RESOLVED",
        "createdAt": "2024-01-20T10:00:00Z",
        "entitySnapshot": {
            "id": "asset-002",
            "providerId": "/subscriptions/sub1/resourceGroups/rg2/providers/Microsoft.AppConfiguration/configurationStores/store2",
            "type": "SERVICE_CONFIGURATION",
            "name": "store2",
        },
    }

    # Test grouping - should group by title only
    groups = wiz_issue._group_issues_for_consolidation([issue1, issue2])

    # Should have only 1 group with the same title
    assert len(groups) == 1, f"Expected 1 group, got {len(groups)}"

    group_key = "App Configuration public network access should be disabled"
    assert group_key in groups, f"Expected to find '{group_key}' in groups"
    assert len(groups[group_key]) == 2, f"Expected 2 issues in group, got {len(groups[group_key])}"

    # Test consolidation
    consolidated = wiz_issue._create_consolidated_finding(groups[group_key], WizVulnerabilityType.CONFIGURATION)

    # Verify consolidation properties
    assert consolidated.title == "App Configuration public network access should be disabled"
    assert consolidated.severity == IssueSeverity.High  # Should use highest severity
    assert consolidated.status == IssueStatus.Open  # Should use most urgent status
    assert consolidated.asset_identifier == "asset-001"  # Primary asset

    # Should have both provider IDs
    provider_ids = consolidated.issue_asset_identifier_value.split("\n")
    assert len(provider_ids) == 2, f"Expected 2 provider IDs, got {len(provider_ids)}"
    assert "/configurationStores/store1" in provider_ids[0]
    assert "/configurationStores/store2" in provider_ids[1]


@patch("regscale.integrations.scanner_integration.ScannerIntegration.get_assessor_id")
def test_consolidation_priority_rules(mock_get_assessor):
    """Test that consolidation correctly applies priority rules for severity and status."""
    mock_get_assessor.return_value = "test-assessor"

    wiz_issue = WizIssue(plan_id=1)

    # Create issues with different severities and statuses
    issues = [
        {
            "id": "issue-1",
            "sourceRule": {"name": "Test Rule", "__typename": "Control"},
            "severity": "LOW",
            "status": "RESOLVED",
            "createdAt": "2024-01-20T10:00:00Z",
            "entitySnapshot": {"id": "asset-1", "providerId": "provider-1"},
        },
        {
            "id": "issue-2",
            "sourceRule": {"name": "Test Rule", "__typename": "Control"},
            "severity": "CRITICAL",  # Highest severity
            "status": "RESOLVED",
            "createdAt": "2024-01-15T10:00:00Z",  # Earlier date
            "entitySnapshot": {"id": "asset-2", "providerId": "provider-2"},
        },
        {
            "id": "issue-3",
            "sourceRule": {"name": "Test Rule", "__typename": "Control"},
            "severity": "MEDIUM",
            "status": "OPEN",  # Most urgent status
            "createdAt": "2024-01-18T10:00:00Z",
            "entitySnapshot": {"id": "asset-3", "providerId": "provider-3"},
        },
    ]

    consolidated = wiz_issue._create_consolidated_finding(issues, WizVulnerabilityType.ISSUE)

    # Should use CRITICAL severity (highest)
    assert consolidated.severity == IssueSeverity.Critical

    # Should use OPEN status (most urgent)
    assert consolidated.status == IssueStatus.Open

    # Should use earliest date
    assert "2024-01-15" in consolidated.date_created

    # Should have all 3 provider IDs
    provider_ids = consolidated.issue_asset_identifier_value.split("\n")
    assert len(provider_ids) == 3
