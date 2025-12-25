"""
Integration tests for server-side vulnerability mapping creation.

This tests the optimization where vulnerabilities are sent to the streaming
endpoint with enableAssetDiscovery=True, and the server creates
VulnerabilityMappings automatically (no local mapping creation needed).
"""

import time
from typing import Any, Dict, Iterator, List
from unittest.mock import MagicMock, patch, call

import pytest
from rich.progress import Progress

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.scanner_integration import (
    ScannerIntegration,
    ScannerIntegrationType,
    IntegrationAsset,
    IntegrationFinding,
)
from regscale.models import regscale_models
from tests.fixtures.test_fixture import CLITestFixture


class LargeScaleTestScanner(ScannerIntegration):
    """Test scanner that simulates large-scale vulnerability processing."""

    title = "Large Scale Test Scanner"
    asset_identifier_field = "identifier"
    type = ScannerIntegrationType.VULNERABILITY

    def __init__(self, plan_id: int, tenant_id: int = 1, num_findings: int = 1000):
        """Initialize with configurable number of findings."""
        super().__init__(plan_id, tenant_id)
        self.num_findings = num_findings

    def fetch_assets(self, *args, **kwargs) -> Iterator[IntegrationAsset]:
        """Fetch test assets."""
        return iter(
            [
                IntegrationAsset(
                    identifier=f"asset_{i}",
                    name=f"Test Asset {i}",
                    asset_type="Server",
                    asset_category="Virtual",
                    software_inventory=[],
                    ports_and_protocols=[],
                    source_data={},
                )
                for i in range(1, min(self.num_findings, 100) + 1)  # Limit assets to 100
            ]
        )

    def fetch_findings(self, *args, **kwargs) -> List[IntegrationFinding]:
        """Fetch large number of test findings."""
        findings = []
        for i in range(1, self.num_findings + 1):
            asset_id = ((i - 1) % 100) + 1  # Distribute findings across assets
            findings.append(
                IntegrationFinding(
                    title=f"Test Vulnerability {i}",
                    asset_identifier=f"asset_{asset_id}",
                    description=f"Test vulnerability description {i}",
                    external_id=f"VULN-{i:05d}",
                    plugin_id=f"PLUGIN-{i:05d}",
                    plugin_name=f"Test Plugin {i}",
                    control_labels=[],
                    category="Vulnerability",
                    severity="High" if i % 3 == 0 else "Medium",
                    status="Open",
                    cve=f"CVE-2024-{i:05d}" if i % 2 == 0 else None,
                    first_seen=get_current_datetime(),
                    last_seen=get_current_datetime(),
                )
            )
        return findings


class TestServerSideVulnerabilityMapping(CLITestFixture):
    """Tests for server-side vulnerability mapping creation."""

    plan_id = 1
    tenant_id = 1

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability.bulk_save")
    def test_bulk_save_called_with_options(self, mock_bulk_save):
        """Test that Vulnerability.bulk_save is called with server-side options."""
        mock_bulk_save.return_value = {"created": [], "updated": []}

        scanner = LargeScaleTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id, num_findings=10)

        # Call _perform_batch_operations
        progress = MagicMock(spec=Progress)
        scanner._perform_batch_operations(progress)

        # Verify bulk_save was called
        mock_bulk_save.assert_called_once()

        # Verify options were passed
        call_kwargs = mock_bulk_save.call_args.kwargs
        assert "options" in call_kwargs
        options = call_kwargs["options"]

        # Verify server-side asset discovery is enabled
        assert options.get("enableAssetDiscovery") is True
        assert options.get("suppressAssetNotFoundWarnings") is True
        assert options.get("parentId") == self.plan_id
        assert options.get("parentModule") == "securityplans"

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability.bulk_save")
    def test_source_set_to_scanner_title(self, mock_bulk_save):
        """Test that source is set to the scanner's title."""
        mock_bulk_save.return_value = {"created": [], "updated": []}

        scanner = LargeScaleTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id)

        progress = MagicMock(spec=Progress)
        scanner._perform_batch_operations(progress)

        call_kwargs = mock_bulk_save.call_args.kwargs
        options = call_kwargs["options"]

        # Verify source is set to scanner title
        assert options.get("source") == "Large Scale Test Scanner"

    @patch("regscale.models.regscale_models.vulnerability_mapping.VulnerabilityMapping.batch_create")
    @patch("regscale.models.regscale_models.vulnerability.Vulnerability.bulk_save")
    def test_no_local_mapping_creation(self, mock_bulk_save, mock_mapping_batch_create):
        """Test that VulnerabilityMapping.batch_create is NOT called (server handles it)."""
        mock_bulk_save.return_value = {"created": [], "updated": []}

        scanner = LargeScaleTestScanner(plan_id=self.plan_id, tenant_id=self.tenant_id, num_findings=100)

        # Process some findings to simulate normal workflow
        original_create_or_update = regscale_models.Vulnerability.create_or_update

        def mock_create_or_update(self, *args, **kwargs):
            temp_vuln = regscale_models.Vulnerability(**self.model_dump())
            temp_vuln.id = 0
            return temp_vuln

        regscale_models.Vulnerability.create_or_update = mock_create_or_update

        try:
            # Setup assets
            with patch("regscale.models.regscale_models.asset.Asset.create_or_update") as mock_asset_create:
                mock_asset_create.side_effect = lambda *args, **kwargs: args[0] if args else kwargs.get("self")

                assets = list(scanner.fetch_assets())
                for asset in assets:
                    asset.id = int(asset.identifier.split("_")[1])
                    asset.parentId = 1
                    asset.parentModule = "securityplans"
                    scanner.asset_map_by_identifier[asset.identifier] = asset

            scan_history = regscale_models.ScanHistory(
                id=999, scanningTool="Test Scanner", parentId=self.plan_id, parentModule="securityplans"
            )

            # Process a few findings
            findings = scanner.fetch_findings()[:10]
            for finding in findings:
                asset = scanner.asset_map_by_identifier.get(finding.asset_identifier)
                if asset:
                    scanner.create_vulnerability_from_finding(finding, asset, scan_history)

            # Perform batch operations
            progress = MagicMock(spec=Progress)
            scanner._perform_batch_operations(progress)

            # Verify local mapping creation was NOT called
            # Server handles mapping creation via enableAssetDiscovery=True
            mock_mapping_batch_create.assert_not_called()

        finally:
            regscale_models.Vulnerability.create_or_update = original_create_or_update


class TestVulnerabilityBatchCreateOrUpdate(CLITestFixture):
    """Tests for Vulnerability.batch_create_or_update with proper payload format."""

    plan_id = 1
    tenant_id = 1

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability._get_api_handler")
    def test_sends_proper_payload_format(self, mock_get_api_handler):
        """Test that batch_create_or_update sends proper payload with options."""
        mock_api = MagicMock()
        mock_api.post.return_value = {"items": [], "summary": {"totalCreated": 1, "totalUpdated": 0}}
        mock_get_api_handler.return_value = mock_api

        # Create test vulnerabilities
        vulns = [
            regscale_models.Vulnerability(
                plugInId="TEST-001",
                plugInName="Test Plugin",
                parentId=self.plan_id,
                parentModule="securityplans",
                severity="High",
            )
        ]

        options: regscale_models.VulnerabilityBatchOptions = {
            "source": "Test Scanner",
            "enableAssetDiscovery": True,
            "parentId": self.plan_id,
            "parentModule": "securityplans",
        }

        # Call batch_create_or_update
        regscale_models.Vulnerability.batch_create_or_update(
            items=vulns,
            batch_size=100,
            options=options,
        )

        # Verify API was called with proper payload format
        mock_api.post.assert_called_once()
        call_kwargs = mock_api.post.call_args.kwargs
        payload = call_kwargs["data"]

        # Verify payload structure
        assert "vulnerabilities" in payload
        assert "options" in payload
        assert isinstance(payload["vulnerabilities"], list)
        assert len(payload["vulnerabilities"]) == 1

        # Verify options are passed through
        assert payload["options"]["enableAssetDiscovery"] is True
        assert payload["options"]["source"] == "Test Scanner"

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability._get_api_handler")
    def test_default_options_set_when_not_provided(self, mock_get_api_handler):
        """Test that default options are set when not provided."""
        mock_api = MagicMock()
        mock_api.post.return_value = {"items": [], "summary": {"totalCreated": 0, "totalUpdated": 0}}
        mock_get_api_handler.return_value = mock_api

        vulns = [
            regscale_models.Vulnerability(
                plugInId="TEST-001",
                plugInName="Test Plugin",
                parentId=self.plan_id,
                parentModule="securityplans",
            )
        ]

        # Call without options
        regscale_models.Vulnerability.batch_create_or_update(items=vulns, batch_size=100)

        call_kwargs = mock_api.post.call_args.kwargs
        payload = call_kwargs["data"]

        # Verify default options are set
        assert payload["options"]["enableAssetDiscovery"] is True
        assert payload["options"]["suppressAssetNotFoundWarnings"] is True


class TestVulnerabilityBulkSave(CLITestFixture):
    """Tests for Vulnerability.bulk_save with server-side options."""

    plan_id = 1
    tenant_id = 1

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability.batch_create_or_update")
    def test_bulk_save_uses_batch_create_or_update(self, mock_batch_create_or_update):
        """Test that bulk_save uses batch_create_or_update instead of separate batch_create/batch_update."""
        mock_batch_create_or_update.return_value = []

        # Clear any existing pending items
        regscale_models.Vulnerability.clear_cache()

        # Create a vulnerability and queue it for creation
        vuln = regscale_models.Vulnerability(
            plugInId="TEST-001",
            plugInName="Test Plugin",
            parentId=self.plan_id,
            parentModule="securityplans",
        )
        vuln.create_or_update(bulk_create=True)

        # Call bulk_save with options
        options: regscale_models.VulnerabilityBatchOptions = {
            "source": "Test",
            "enableAssetDiscovery": True,
        }
        regscale_models.Vulnerability.bulk_save(options=options)

        # Verify batch_create_or_update was called (not batch_create + batch_update)
        mock_batch_create_or_update.assert_called_once()

        # Verify options were passed
        call_kwargs = mock_batch_create_or_update.call_args.kwargs
        assert call_kwargs["options"] == options

    @patch("regscale.models.regscale_models.vulnerability.Vulnerability.batch_create_or_update")
    def test_bulk_save_passes_batch_size(self, mock_batch_create_or_update):
        """Test that bulk_save passes batch_size to batch_create_or_update."""
        mock_batch_create_or_update.return_value = []

        regscale_models.Vulnerability.clear_cache()

        vuln = regscale_models.Vulnerability(
            plugInId="TEST-002",
            plugInName="Test Plugin 2",
            parentId=self.plan_id,
            parentModule="securityplans",
        )
        vuln.create_or_update(bulk_create=True)

        # Call bulk_save with custom batch_size
        regscale_models.Vulnerability.bulk_save(batch_size=500)

        call_kwargs = mock_batch_create_or_update.call_args.kwargs
        assert call_kwargs["batch_size"] == 500
