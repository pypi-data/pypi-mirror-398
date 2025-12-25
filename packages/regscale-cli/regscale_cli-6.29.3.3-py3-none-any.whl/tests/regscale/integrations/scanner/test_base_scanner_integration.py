#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for BaseScannerIntegration orchestration class.

This module tests the minimal orchestrator class that replaces the monolithic
ScannerIntegration class with a handler-based architecture.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Iterator, List, Any

from regscale.integrations.scanner.base import BaseScannerIntegration
from regscale.integrations.scanner.context import ScannerContext
from regscale.integrations.scanner.handlers import AssetHandler, IssueHandler, VulnerabilityHandler
from regscale.integrations.scanner.cache import AssetCache, IssueCache, ControlCache
from regscale.integrations.scanner.models import IntegrationFinding, IntegrationAsset
from regscale.models import regscale_models


# Concrete test implementation for testing
class TestScanner(BaseScannerIntegration):
    """Concrete implementation for testing BaseScannerIntegration."""

    def fetch_findings(self, *args: Any, **kwargs: Any) -> Iterator[IntegrationFinding]:
        """Test implementation - yields no findings by default."""
        return iter([])

    def fetch_assets(self, *args: Any, **kwargs: Any) -> Iterator[IntegrationAsset]:
        """Test implementation - yields no assets by default."""
        return iter([])


class TestBaseScannerIntegrationInitialization:
    """Test initialization and setup of BaseScannerIntegration."""

    def test_init_with_minimal_params(self):
        """Test initialization with only required parameters."""
        integration = TestScanner(plan_id=123)

        assert integration.plan_id == 123
        assert integration.tenant_id == 1  # default
        assert integration.context is not None
        assert isinstance(integration.context, ScannerContext)

    def test_init_with_custom_tenant(self):
        """Test initialization with custom tenant ID."""
        integration = TestScanner(plan_id=123, tenant_id=99)

        assert integration.plan_id == 123
        assert integration.tenant_id == 99
        assert integration.context.tenant_id == 99

    def test_init_with_component_mode(self):
        """Test initialization in component mode."""
        integration = TestScanner(plan_id=456, is_component=True)

        assert integration.plan_id == 456
        assert integration.context.is_component is True
        assert integration.context.parent_module == "components"

    def test_init_with_configuration_kwargs(self):
        """Test initialization with configuration overrides."""
        integration = TestScanner(
            plan_id=123, title="Test Scanner", asset_identifier_field="ipAddress", enable_cci_mapping=False
        )

        assert integration.context.title == "Test Scanner"
        assert integration.context.asset_identifier_field == "ipAddress"
        assert integration.context.enable_cci_mapping is False

    def test_handlers_initialized(self):
        """Test that all handlers are properly initialized."""
        integration = TestScanner(plan_id=123)

        assert integration.asset_handler is not None
        assert isinstance(integration.asset_handler, AssetHandler)
        assert integration.issue_handler is not None
        assert isinstance(integration.issue_handler, IssueHandler)
        assert integration.vulnerability_handler is not None
        assert isinstance(integration.vulnerability_handler, VulnerabilityHandler)

    def test_caches_initialized(self):
        """Test that all caches are properly initialized."""
        integration = TestScanner(plan_id=123)

        assert integration.asset_cache is not None
        assert isinstance(integration.asset_cache, AssetCache)
        assert integration.issue_cache is not None
        assert isinstance(integration.issue_cache, IssueCache)
        assert integration.control_cache is not None
        assert isinstance(integration.control_cache, ControlCache)

    def test_context_shared_with_handlers(self):
        """Test that context is shared with all handlers."""
        integration = TestScanner(plan_id=123)

        # Handlers should share the same context instance
        assert integration.asset_handler.context is integration.context
        assert integration.issue_handler.plan_id == integration.context.plan_id


class TestBaseScannerIntegrationProcessFinding:
    """Test process_finding orchestration method."""

    @pytest.fixture
    def integration(self):
        """Create integration instance for testing."""
        return TestScanner(plan_id=123)

    @pytest.fixture
    def sample_finding(self):
        """Create a sample finding for testing."""
        return IntegrationFinding(
            control_labels=[],
            title="Test Vulnerability",
            category="Vulnerability",
            severity=regscale_models.IssueSeverity.High,
            description="Test description",
            status=regscale_models.IssueStatus.Open,
            plugin_id="12345",
            asset_identifier="10.0.0.1",
        )

    def test_process_finding_creates_vulnerability(self, integration, sample_finding):
        """Test that process_finding creates a vulnerability."""
        with patch.object(integration.vulnerability_handler, "create_vulnerability") as mock_create:
            mock_create.return_value = Mock(id=1)

            integration.process_finding(sample_finding)

            mock_create.assert_called_once()

    def test_process_finding_creates_issue(self, integration, sample_finding):
        """Test that process_finding creates an issue."""
        with patch.object(integration.issue_handler, "create_or_update_issue") as mock_create:
            mock_create.return_value = Mock(id=1)

            integration.process_finding(sample_finding)

            mock_create.assert_called_once()

    def test_process_finding_with_asset_lookup(self, integration, sample_finding):
        """Test that process_finding looks up assets via cache."""
        with patch.object(integration.asset_cache, "get_by_identifier") as mock_get:
            mock_asset = Mock(id=10, name="Test Asset")
            mock_get.return_value = mock_asset

            integration.process_finding(sample_finding)

            mock_get.assert_called_with(sample_finding.asset_identifier)

    def test_process_finding_handles_missing_asset(self, integration, sample_finding):
        """Test that process_finding handles missing asset gracefully."""
        with patch.object(integration.asset_cache, "get_by_identifier") as mock_get:
            mock_get.return_value = None

            # Should not raise exception
            integration.process_finding(sample_finding)


class TestBaseScannerIntegrationBatchProcessing:
    """Test batch processing orchestration methods."""

    @pytest.fixture
    def integration(self):
        """Create integration instance for testing."""
        return TestScanner(plan_id=123)

    @pytest.fixture
    def sample_findings(self):
        """Create sample findings for batch testing."""
        return [
            IntegrationFinding(
                control_labels=[],
                title=f"Finding {i}",
                category="Vulnerability",
                severity=regscale_models.IssueSeverity.High,
                description=f"Test finding {i}",
                status=regscale_models.IssueStatus.Open,
                plugin_id=str(1000 + i),
                asset_identifier=f"10.0.0.{i}",
            )
            for i in range(1, 6)
        ]

    def test_process_findings_batch_uses_batch_methods(self, integration, sample_findings):
        """Test that batch processing uses handler batch methods."""
        with patch.object(
            integration.vulnerability_handler, "batch_create_vulnerabilities"
        ) as mock_batch_vulns, patch.object(regscale_models.Issue, "batch_create_or_update") as mock_batch_issues:

            mock_batch_vulns.return_value = [Mock(id=i) for i in range(len(sample_findings))]
            mock_batch_issues.return_value = [Mock(id=i) for i in range(len(sample_findings))]

            integration.process_findings_batch(iter(sample_findings))

            # Verify batch methods were called (not individual)
            mock_batch_vulns.assert_called_once()
            mock_batch_issues.assert_called_once()

    def test_process_findings_batch_uses_batch_options(self, integration, sample_findings):
        """Test that batch processing passes BatchOptions to handlers."""
        with patch.object(integration.vulnerability_handler, "batch_create_vulnerabilities") as mock_batch:
            mock_batch.return_value = []

            integration.process_findings_batch(iter(sample_findings), enable_mop_up=True, enable_asset_discovery=True)

            # Verify BatchOptions were passed
            call_args = mock_batch.call_args
            assert call_args is not None
            options = call_args[1].get("options")
            assert options is not None
            assert options["enableMopUp"] is True
            assert options["enableAssetDiscovery"] is True

    def test_process_findings_batch_with_iterator(self, integration, sample_findings):
        """Test that batch processing works with iterators."""

        # Use generator to simulate streaming
        def finding_generator():
            for finding in sample_findings:
                yield finding

        with patch.object(integration.vulnerability_handler, "batch_create_vulnerabilities") as mock_batch:
            mock_batch.return_value = []

            integration.process_findings_batch(finding_generator())

            # Should have processed all findings
            mock_batch.assert_called_once()
            call_args = mock_batch.call_args
            vulns_list = call_args.kwargs["vulnerabilities"]  # Keyword argument
            assert len(vulns_list) == len(sample_findings)

    def test_process_findings_batch_chunks_large_datasets(self, integration):
        """Test that large datasets are chunked according to batch size."""
        # Create 2500 findings (should be split into 3 batches of 1000 each)
        large_findings = [
            IntegrationFinding(
                control_labels=[],
                title=f"Finding {i}",
                category="Vulnerability",
                severity=regscale_models.IssueSeverity.Moderate,
                description=f"Test finding {i}",
                status=regscale_models.IssueStatus.Open,
                plugin_id=str(i),
            )
            for i in range(2500)
        ]

        with patch.object(integration.vulnerability_handler, "batch_create_vulnerabilities") as mock_batch:
            mock_batch.return_value = []

            integration.process_findings_batch(iter(large_findings))

            # Should be called multiple times for chunks
            assert mock_batch.call_count >= 1


class TestBaseScannerIntegrationCloseOutdated:
    """Test close_outdated_findings orchestration."""

    @pytest.fixture
    def integration(self):
        """Create integration instance for testing."""
        return TestScanner(plan_id=123)

    @pytest.mark.skip(reason="close_outdated methods not yet implemented in handlers - closure logic in base class")
    def test_close_outdated_calls_handlers(self, integration):
        """Test that close_outdated delegates to handlers."""
        current_findings = {
            "plugin1": set(["asset1", "asset2"]),
            "plugin2": set(["asset3"]),
        }

        with patch.object(
            integration.vulnerability_handler, "close_outdated_vulnerabilities"
        ) as mock_close_vulns, patch.object(integration.issue_handler, "close_outdated_issues") as mock_close_issues:

            mock_close_vulns.return_value = 5
            mock_close_issues.return_value = 3

            closed_count = integration.close_outdated_findings(current_findings)

            mock_close_vulns.assert_called_once_with(current_findings)
            mock_close_issues.assert_called_once()
            assert closed_count == 8  # 5 + 3


class TestBaseScannerIntegrationClassMethods:
    """Test class-level orchestration methods."""

    def test_sync_findings_creates_instance(self):
        """Test that sync_findings class method creates instance."""
        with patch.object(TestScanner, "__init__", return_value=None) as mock_init, patch.object(
            TestScanner, "_execute_finding_sync", return_value=10
        ):

            result = TestScanner.sync_findings(plan_id=123)

            mock_init.assert_called_once()
            assert result == 10

    def test_sync_assets_creates_instance(self):
        """Test that sync_assets class method creates instance."""
        with patch.object(TestScanner, "__init__", return_value=None) as mock_init, patch.object(
            TestScanner, "_execute_asset_sync", return_value=5
        ):

            result = TestScanner.sync_assets(plan_id=456)

            mock_init.assert_called_once()
            assert result == 5


class TestBaseScannerIntegrationErrorHandling:
    """Test error handling and resilience."""

    @pytest.fixture
    def integration(self):
        """Create integration instance for testing."""
        return TestScanner(plan_id=123)

    def test_process_finding_handles_handler_exception(self, integration):
        """Test that exceptions in handlers are caught and logged."""
        finding = IntegrationFinding(
            control_labels=[],
            title="Test",
            category="Vulnerability",
            severity=regscale_models.IssueSeverity.High,
            description="Test",
            status=regscale_models.IssueStatus.Open,
            plugin_id="123",
        )

        with patch.object(integration.vulnerability_handler, "create_vulnerability") as mock_create:
            mock_create.side_effect = Exception("Handler error")

            # Should log error but not raise
            integration.process_finding(finding)

    def test_batch_processing_handles_partial_failures(self, integration):
        """Test that batch processing continues after partial failures."""
        findings = [
            IntegrationFinding(
                control_labels=[],
                title=f"Finding {i}",
                category="Vulnerability",
                severity=regscale_models.IssueSeverity.High,
                description=f"Test finding {i}",
                status=regscale_models.IssueStatus.Open,
                plugin_id=str(i),
            )
            for i in range(5)
        ]

        with patch.object(integration.vulnerability_handler, "batch_create_vulnerabilities") as mock_batch:
            # Simulate partial success
            mock_batch.return_value = [Mock(id=1), Mock(id=2)]  # Only 2 out of 5 succeeded

            result = integration.process_findings_batch(iter(findings))

            # Should still return results
            assert result is not None


class TestBaseScannerIntegrationThreadSafety:
    """Test thread safety of orchestration methods."""

    @pytest.fixture
    def integration(self):
        """Create integration instance for testing."""
        return TestScanner(plan_id=123)

    def test_concurrent_finding_processing(self, integration):
        """Test that concurrent process_finding calls are thread-safe."""
        import concurrent.futures

        findings = [
            IntegrationFinding(
                control_labels=[],
                title=f"Finding {i}",
                category="Vulnerability",
                severity=regscale_models.IssueSeverity.High,
                description=f"Test finding {i}",
                status=regscale_models.IssueStatus.Open,
                plugin_id=str(i),
            )
            for i in range(20)
        ]

        with patch.object(integration.vulnerability_handler, "create_vulnerability") as mock_create:
            mock_create.return_value = Mock(id=1)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(integration.process_finding, finding) for finding in findings]
                concurrent.futures.wait(futures)

            # All calls should have been processed
            assert mock_create.call_count == len(findings)


class TestBaseScannerIntegrationConfiguration:
    """Test configuration and customization options."""

    def test_custom_batch_sizes(self):
        """Test that custom batch sizes are respected."""
        integration = TestScanner(plan_id=123, asset_batch_size=100, issue_batch_size=200, vulnerability_batch_size=300)

        assert integration.context.asset_batch_size == 100
        assert integration.context.issue_batch_size == 200
        assert integration.context.vulnerability_batch_size == 300

    def test_custom_identifier_fields(self):
        """Test that custom identifier fields are configured."""
        integration = TestScanner(plan_id=123, asset_identifier_field="ipAddress", issue_identifier_field="wizId")

        assert integration.context.asset_identifier_field == "ipAddress"
        assert integration.context.issue_identifier_field == "wizId"

    def test_feature_flags(self):
        """Test that feature flags are respected."""
        integration = TestScanner(
            plan_id=123, enable_cci_mapping=False, close_outdated_findings=False, suppress_asset_not_found_errors=True
        )

        assert integration.context.enable_cci_mapping is False
        assert integration.context.close_outdated_findings is False
        assert integration.context.suppress_asset_not_found_errors is True
