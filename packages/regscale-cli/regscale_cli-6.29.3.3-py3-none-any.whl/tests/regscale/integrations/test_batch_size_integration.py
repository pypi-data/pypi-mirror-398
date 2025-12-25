"""
Tests for batch size configuration in ScannerIntegration.

These tests verify that:
1. ScannerIntegration has configurable batch size attributes
2. Batch sizes are loaded from ScannerVariables
3. _perform_batch_operations passes correct batch sizes to bulk_save
4. VulnerabilityMapping batch_create uses configured batch size
"""

from typing import Iterator, List
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from regscale.integrations.scanner_integration import (
    ScannerIntegration,
    ScannerIntegrationType,
    IntegrationAsset,
    IntegrationFinding,
)
from regscale.models import regscale_models
from tests.fixtures.test_fixture import CLITestFixture


class MockScanner(ScannerIntegration):
    """Mock scanner for testing batch size configuration."""

    title = "Mock Scanner"
    asset_identifier_field = "otherTrackingNumber"
    type = ScannerIntegrationType.VULNERABILITY

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """Return empty iterator for testing."""
        return iter([])

    def fetch_findings(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """Return empty iterator for testing."""
        return iter([])


class TestScannerIntegrationBatchSizeAttributes(CLITestFixture):
    """Test batch size attributes in ScannerIntegration."""

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    def test_scanner_has_batch_size_attributes(
        self,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that ScannerIntegration has batch size attributes."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        scanner = MockScanner(plan_id=1, tenant_id=1)

        # Verify batch size attributes exist
        assert hasattr(scanner, "asset_batch_size")
        assert hasattr(scanner, "issue_batch_size")
        assert hasattr(scanner, "vulnerability_batch_size")
        assert hasattr(scanner, "vulnerability_mapping_batch_size")

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    def test_default_batch_sizes_are_set(
        self,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that default batch sizes are set to reasonable values."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        scanner = MockScanner(plan_id=1, tenant_id=1)

        # Verify default batch sizes are reasonable
        assert scanner.asset_batch_size >= 100
        assert scanner.issue_batch_size >= 100
        assert scanner.vulnerability_batch_size >= 100
        assert scanner.vulnerability_mapping_batch_size >= 100


class TestPerformBatchOperationsBatchSizes(CLITestFixture):
    """Test that _perform_batch_operations uses configured batch sizes."""

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    @patch("regscale.integrations.scanner_integration.regscale_models.Asset.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Vulnerability.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Property.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Data.bulk_save")
    def test_perform_batch_operations_passes_asset_batch_size(
        self,
        mock_data_save,
        mock_property_save,
        mock_vuln_save,
        mock_issue_save,
        mock_asset_save,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that _perform_batch_operations passes asset_batch_size to Asset.bulk_save."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        # Setup bulk_save mocks
        mock_asset_save.return_value = {"created": [], "updated": []}
        mock_issue_save.return_value = {"created": [], "updated": []}
        mock_vuln_save.return_value = {"created": [], "updated": []}
        mock_property_save.return_value = {"created": [], "updated": []}
        mock_data_save.return_value = {"created": [], "updated": []}

        scanner = MockScanner(plan_id=1, tenant_id=1)
        scanner.asset_batch_size = 1000  # Set custom batch size

        progress = MagicMock()
        scanner._perform_batch_operations(progress)

        # Verify Asset.bulk_save was called with batch_size
        mock_asset_save.assert_called_once()
        call_kwargs = mock_asset_save.call_args.kwargs
        assert call_kwargs.get("batch_size") == 1000

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    @patch("regscale.integrations.scanner_integration.regscale_models.Asset.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Vulnerability.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Property.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Data.bulk_save")
    def test_perform_batch_operations_passes_issue_batch_size(
        self,
        mock_data_save,
        mock_property_save,
        mock_vuln_save,
        mock_issue_save,
        mock_asset_save,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that _perform_batch_operations passes issue_batch_size to Issue.bulk_save."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        # Setup bulk_save mocks
        mock_asset_save.return_value = {"created": [], "updated": []}
        mock_issue_save.return_value = {"created": [], "updated": []}
        mock_vuln_save.return_value = {"created": [], "updated": []}
        mock_property_save.return_value = {"created": [], "updated": []}
        mock_data_save.return_value = {"created": [], "updated": []}

        scanner = MockScanner(plan_id=1, tenant_id=1)
        scanner.issue_batch_size = 750  # Set custom batch size

        progress = MagicMock()
        scanner._perform_batch_operations(progress)

        # Verify Issue.bulk_save was called with batch_size
        mock_issue_save.assert_called_once()
        call_kwargs = mock_issue_save.call_args.kwargs
        assert call_kwargs.get("batch_size") == 750

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    @patch("regscale.integrations.scanner_integration.regscale_models.Asset.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Vulnerability.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Property.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Data.bulk_save")
    def test_perform_batch_operations_passes_vulnerability_batch_size(
        self,
        mock_data_save,
        mock_property_save,
        mock_vuln_save,
        mock_issue_save,
        mock_asset_save,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that _perform_batch_operations passes vulnerability_batch_size to Vulnerability.bulk_save."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        # Setup bulk_save mocks
        mock_asset_save.return_value = {"created": [], "updated": []}
        mock_issue_save.return_value = {"created": [], "updated": []}
        mock_vuln_save.return_value = {"created": [], "updated": []}
        mock_property_save.return_value = {"created": [], "updated": []}
        mock_data_save.return_value = {"created": [], "updated": []}

        scanner = MockScanner(plan_id=1, tenant_id=1)
        scanner.vulnerability_batch_size = 5000  # Set custom batch size

        progress = MagicMock()
        scanner._perform_batch_operations(progress)

        # Verify Vulnerability.bulk_save was called with batch_size
        mock_vuln_save.assert_called_once()
        call_kwargs = mock_vuln_save.call_args.kwargs
        assert call_kwargs.get("batch_size") == 5000


class TestVulnerabilityMappingBatchSize(CLITestFixture):
    """Test VulnerabilityMapping batch_create uses configured batch size."""

    @patch("regscale.integrations.scanner_integration.Application")
    @patch("regscale.integrations.scanner_integration.APIHandler")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.get_open_issues_ids_by_implementation_id")
    @patch(
        "regscale.integrations.scanner_integration.regscale_models.ControlImplementation.get_control_id_map_by_parent"
    )
    @patch("regscale.integrations.scanner_integration.pull_cisa_kev")
    @patch("regscale.integrations.scanner_integration.regscale_models.Asset.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Issue.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Vulnerability.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Property.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.Data.bulk_save")
    @patch("regscale.integrations.scanner_integration.regscale_models.VulnerabilityMapping.batch_create")
    @patch("regscale.integrations.scanner_integration.regscale_models.Vulnerability.get_cached_object")
    def test_vulnerability_mapping_uses_configured_batch_size(
        self,
        mock_get_cached,
        mock_mapping_batch_create,
        mock_data_save,
        mock_property_save,
        mock_vuln_save,
        mock_issue_save,
        mock_asset_save,
        mock_kev,
        mock_control_id_map,
        mock_open_issues,
        mock_control_label_map,
        mock_api_handler,
        mock_app,
    ):
        """Test that VulnerabilityMapping.batch_create uses vulnerability_mapping_batch_size."""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {}
        mock_app.return_value = mock_app_instance
        mock_api_handler_instance = MagicMock()
        mock_api_handler_instance.regscale_version = "5.0.0"
        mock_api_handler.return_value = mock_api_handler_instance
        mock_control_label_map.return_value = {}
        mock_open_issues.return_value = {}
        mock_control_id_map.return_value = {}
        mock_kev.return_value = {}

        # Setup bulk_save mocks
        mock_asset_save.return_value = {"created": [], "updated": []}
        mock_issue_save.return_value = {"created": [], "updated": []}
        mock_vuln_save.return_value = {"created": [], "updated": []}
        mock_property_save.return_value = {"created": [], "updated": []}
        mock_data_save.return_value = {"created": [], "updated": []}
        mock_mapping_batch_create.return_value = []

        # Setup mock cached vulnerability with real ID
        mock_vuln = MagicMock()
        mock_vuln.id = 123
        mock_get_cached.return_value = mock_vuln

        scanner = MockScanner(plan_id=1, tenant_id=1)
        scanner.vulnerability_mapping_batch_size = 2000  # Set custom batch size

        # Add pending vulnerability mappings
        scanner._pending_vulnerability_mappings = [
            {
                "vulnerability_cache_key": "test_key_1",
                "finding": MagicMock(),
                "asset": MagicMock(),
                "scan_history": MagicMock(),
            }
        ]

        # Mock _build_vulnerability_mapping
        with patch.object(scanner, "_build_vulnerability_mapping", return_value=MagicMock()):
            progress = MagicMock()
            scanner._perform_batch_operations(progress)

        # Verify VulnerabilityMapping.batch_create was called with batch_size
        mock_mapping_batch_create.assert_called_once()
        call_kwargs = mock_mapping_batch_create.call_args.kwargs
        assert call_kwargs.get("batch_size") == 2000
