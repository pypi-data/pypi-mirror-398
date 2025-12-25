"""
Tests for batched Issue creation in scanner_integration.

This tests the optimization where:
1. Issues are created with bulk_create=True (queued with id=0)
2. After Issue.bulk_save(), issues have real IDs
3. Properties are only created for issues with valid IDs
"""

from typing import Iterator, List
from unittest.mock import MagicMock, patch

import pytest

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.scanner_integration import (
    ScannerIntegration,
    ScannerIntegrationType,
    IntegrationAsset,
    IntegrationFinding,
)
from regscale.models import regscale_models
from tests.fixtures.test_fixture import CLITestFixture


class SimpleBatchTestScanner(ScannerIntegration):
    """Simple test scanner for batch Issue creation tests."""

    title = "Batch Issue Test Scanner"
    asset_identifier_field = "identifier"
    type = ScannerIntegrationType.VULNERABILITY

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        return iter([])

    def fetch_findings(self, *args, **kwargs) -> List[IntegrationFinding]:
        return []


class TestBatchedIssueCreation(CLITestFixture):
    """Test batched Issue creation functionality."""

    plan_id = 1
    tenant_id = 1

    @patch("regscale.models.regscale_models.issue.Issue.create_or_update")
    def test_issue_creation_uses_bulk_create(self, mock_create_or_update):
        """Test that new issue creation uses bulk_create=True."""
        # Mock issue with id=0 (queued for bulk save)
        mock_issue = regscale_models.Issue(
            id=0,
            parentId=1,
            parentModule="securityplans",
            title="Test Issue",
            status=regscale_models.IssueStatus.Open,
        )
        mock_create_or_update.return_value = mock_issue

        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Create test finding
        finding = IntegrationFinding(
            title="Test Finding",
            external_id="FINDING-001",
            plugin_id="TEST-001",
            plugin_name="Test Plugin",
            severity="High",
            status="Open",
            control_labels=[],
            category="Vulnerability",
            description="Test vulnerability description",
            first_seen=get_current_datetime(),
            last_seen=get_current_datetime(),
        )

        # Call create_or_update_issue_from_finding
        scanner.create_or_update_issue_from_finding(
            title=finding.title,
            finding=finding,
        )

        # Verify create_or_update was called with bulk_create=True
        mock_create_or_update.assert_called()
        call_kwargs = mock_create_or_update.call_args.kwargs
        assert call_kwargs.get("bulk_create") is True
        assert call_kwargs.get("bulk_update") is True

    @patch("regscale.integrations.scanner_integration.ScannerIntegration.extra_data_to_properties")
    @patch("regscale.models.regscale_models.issue.Issue.create_or_update")
    def test_properties_not_created_for_bulk_issue(self, mock_create_or_update, mock_extra_data_to_properties):
        """Test that extra_data_to_properties is NOT called when issue.id is 0."""
        # Mock issue with id=0 (queued for bulk save)
        mock_issue = regscale_models.Issue(
            id=0,
            parentId=1,
            parentModule="securityplans",
            title="Test Issue",
            status=regscale_models.IssueStatus.Open,
        )
        mock_create_or_update.return_value = mock_issue

        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Create test finding with extra_data
        finding = IntegrationFinding(
            title="Test Finding",
            external_id="FINDING-001",
            plugin_id="TEST-001",
            plugin_name="Test Plugin",
            severity="High",
            status="Open",
            control_labels=[],
            category="Vulnerability",
            description="Test vulnerability description",
            first_seen=get_current_datetime(),
            last_seen=get_current_datetime(),
            extra_data={"source_file_path": "/path/to/source"},
        )

        # Call create_or_update_issue_from_finding
        scanner.create_or_update_issue_from_finding(
            title=finding.title,
            finding=finding,
        )

        # Verify extra_data_to_properties was NOT called (since issue.id == 0)
        mock_extra_data_to_properties.assert_not_called()

    @patch("regscale.integrations.scanner_integration.ScannerIntegration.extra_data_to_properties")
    @patch("regscale.models.regscale_models.issue.Issue.create_or_update")
    def test_properties_created_for_real_issue_id(self, mock_create_or_update, mock_extra_data_to_properties):
        """Test that extra_data_to_properties IS called when issue has real ID."""
        # Mock issue with real id (created immediately, not batched)
        mock_issue = regscale_models.Issue(
            id=12345,
            parentId=1,
            parentModule="securityplans",
            title="Test Issue",
            status=regscale_models.IssueStatus.Open,
        )
        mock_create_or_update.return_value = mock_issue

        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Create test finding with extra_data
        finding = IntegrationFinding(
            title="Test Finding",
            external_id="FINDING-001",
            plugin_id="TEST-001",
            plugin_name="Test Plugin",
            severity="High",
            status="Open",
            control_labels=[],
            category="Vulnerability",
            description="Test vulnerability description",
            first_seen=get_current_datetime(),
            last_seen=get_current_datetime(),
            extra_data={"source_file_path": "/path/to/source"},
        )

        # Call create_or_update_issue_from_finding
        scanner.create_or_update_issue_from_finding(
            title=finding.title,
            finding=finding,
        )

        # Verify extra_data_to_properties WAS called with real issue ID
        mock_extra_data_to_properties.assert_called_once_with(finding, 12345)

    def test_property_safe_skips_invalid_issue_id(self):
        """Test that _create_property_safe skips creation when issue.id is 0."""
        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Create issue with id=0 (queued for bulk save)
        issue = regscale_models.Issue(
            id=0,
            parentId=1,
            parentModule="securityplans",
            title="Test Issue",
            status=regscale_models.IssueStatus.Open,
        )

        # Call _create_property_safe - should NOT make API call or force create
        with patch("regscale.models.regscale_models.property.Property.create_or_update") as mock_property_create:
            scanner._create_property_safe(issue, "POC", "test@example.com", "POC property")

            # Verify NO API call was made for property creation
            mock_property_create.assert_not_called()

    @patch("regscale.models.regscale_models.property.Property.create_or_update")
    def test_property_safe_creates_for_valid_issue_id(self, mock_property_create):
        """Test that _create_property_safe creates property when issue has valid ID."""
        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Create issue with valid id
        issue = regscale_models.Issue(
            id=12345,
            parentId=1,
            parentModule="securityplans",
            title="Test Issue",
            status=regscale_models.IssueStatus.Open,
        )

        # Call _create_property_safe
        scanner._create_property_safe(issue, "POC", "test@example.com", "POC property")

        # Verify property creation was called
        mock_property_create.assert_called_once()


class TestIssueBulkSavePerformance(CLITestFixture):
    """Test Issue bulk_save performance in batch operations."""

    plan_id = 1
    tenant_id = 1

    @patch("regscale.models.regscale_models.issue.Issue.bulk_save")
    @patch("regscale.models.regscale_models.asset.Asset.bulk_save")
    def test_issue_bulk_save_uses_configured_batch_size(self, mock_asset_bulk_save, mock_issue_bulk_save):
        """Test that Issue.bulk_save is called with configured batch_size."""
        mock_asset_bulk_save.return_value = {"created": [], "updated": []}
        mock_issue_bulk_save.return_value = {"created": [], "updated": []}

        scanner = SimpleBatchTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        # Verify batch size is loaded from ScannerVariables
        assert hasattr(scanner, "issue_batch_size")
        assert scanner.issue_batch_size == 500  # Default from ScannerVariables

        # Call _perform_batch_operations
        progress = MagicMock()
        scanner._perform_batch_operations(progress)

        # Verify Issue.bulk_save was called with the configured batch_size
        mock_issue_bulk_save.assert_called_once()
        call_kwargs = mock_issue_bulk_save.call_args.kwargs
        assert call_kwargs.get("batch_size") == 500
