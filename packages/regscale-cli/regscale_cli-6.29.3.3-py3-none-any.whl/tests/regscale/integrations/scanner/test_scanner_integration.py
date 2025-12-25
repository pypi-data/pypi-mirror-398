"""
Integration tests for scanner package components.

These tests verify that scanner package components work together correctly:
- AssetCache + AssetHandler integration
- IssueCache + IssueHandler integration
- ScannerContext sharing state between components
- End-to-end workflow scenarios
- Batch processing with caches
- Thread safety across components
- Error propagation and handling
"""

import logging
import threading
from typing import Iterator, List
from unittest.mock import MagicMock, patch

import pytest

from regscale.integrations.scanner.cache import AssetCache, IssueCache
from regscale.integrations.scanner.context import ScannerContext
from regscale.integrations.scanner.handlers import AssetHandler, IssueHandler
from regscale.integrations.scanner.models import IntegrationAsset, IntegrationFinding
from regscale.integrations.scanner.models.enums import ScannerIntegrationType
from regscale.models import regscale_models
from regscale.utils.threading import ThreadSafeDict
from tests.fixtures.test_fixture import CLITestFixture

logger = logging.getLogger("regscale")


class TestAssetCacheAndHandlerIntegration(CLITestFixture):
    """Test AssetCache and AssetHandler working together."""

    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_asset_handler_uses_cache_for_lookups(self, mock_get_all):
        """Test that AssetHandler uses AssetCache for efficient lookups."""
        # Setup
        context = ScannerContext(plan_id=123, tenant_id=1)
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            identifier_field="otherTrackingNumber",
        )
        handler = AssetHandler(context, asset_cache)

        # Create mock assets
        mock_asset1 = MagicMock(spec=regscale_models.Asset)
        mock_asset1.id = 1
        mock_asset1.otherTrackingNumber = "ASSET-001"
        mock_asset1.name = "Test Asset 1"
        mock_asset1.ipAddress = "192.168.1.1"

        mock_asset2 = MagicMock(spec=regscale_models.Asset)
        mock_asset2.id = 2
        mock_asset2.otherTrackingNumber = "ASSET-002"
        mock_asset2.name = "Test Asset 2"
        mock_asset2.ipAddress = "192.168.1.2"

        mock_get_all.return_value = [mock_asset1, mock_asset2]

        # Warm the cache
        asset_cache.warm_cache()

        # Verify cache is populated
        assert len(asset_cache) == 2
        assert "ASSET-001" in asset_cache
        assert "ASSET-002" in asset_cache

        # Test handler uses cache for lookups (no additional API calls)
        found_asset = handler.get_asset_by_identifier("ASSET-001")
        assert found_asset is not None
        assert found_asset.id == 1
        assert found_asset.name == "Test Asset 1"

        # Verify only one API call was made (during cache warming)
        mock_get_all.assert_called_once()

    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_asset_handler_fallback_lookups(self, mock_get_all):
        """Test that AssetHandler falls back to IP/FQDN when primary identifier not found."""
        # Setup
        context = ScannerContext(plan_id=123, tenant_id=1)
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            identifier_field="otherTrackingNumber",
        )
        _handler = AssetHandler(context, asset_cache)  # noqa: F841

        # Create mock asset with IP address
        mock_asset = MagicMock()
        mock_asset.id = 1
        mock_asset.otherTrackingNumber = "ASSET-001"
        mock_asset.ipAddress = "192.168.1.100"
        mock_asset.fqdn = "server.example.com"

        mock_get_all.return_value = [mock_asset]
        asset_cache.warm_cache()

        # Lookup by IP address (fallback)
        found_by_ip = asset_cache.get_by_identifier("192.168.1.100")
        assert found_by_ip is not None
        assert found_by_ip.id == 1

        # Lookup by FQDN (fallback)
        found_by_fqdn = asset_cache.get_by_identifier("server.example.com")
        assert found_by_fqdn is not None
        assert found_by_fqdn.id == 1

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Issue.get_user_id")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_asset_handler_updates_cache_after_creation(self, mock_get_all, mock_asset_class, mock_user_id):
        """Test that AssetHandler updates cache when creating new assets."""
        # Setup
        mock_user_id.return_value = "user123"
        context = ScannerContext(plan_id=123, tenant_id=1)
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            identifier_field="otherTrackingNumber",
        )
        handler = AssetHandler(context, asset_cache)

        # Mock empty initial cache
        mock_get_all.return_value = []
        asset_cache.warm_cache()
        assert len(asset_cache) == 0

        # Create integration asset
        integration_asset = IntegrationAsset(
            name="New Asset",
            identifier="NEW-001",
            asset_type="Virtual Machine (VM)",
            asset_category="Hardware",
        )

        # Mock asset creation
        mock_created_asset = MagicMock()
        mock_created_asset.id = 100
        mock_created_asset.otherTrackingNumber = "NEW-001"
        mock_created_asset.name = "New Asset"

        mock_asset_instance = MagicMock()
        mock_asset_instance.create_or_update_with_status.return_value = ("created", mock_created_asset)
        mock_asset_class.return_value = mock_asset_instance

        # Create asset through handler
        created, new_asset = handler.create_new_asset(integration_asset, component=None)

        # Verify cache was updated
        assert created is True
        assert len(asset_cache) == 1
        assert "NEW-001" in asset_cache
        cached_asset = asset_cache.get_by_identifier("NEW-001")
        assert cached_asset.id == 100


class TestIssueCacheAndHandlerIntegration(CLITestFixture):
    """Test IssueCache and IssueHandler working together."""

    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_issue_handler_uses_cache_for_deduplication(self, mock_open_issues, mock_fetch_issues):
        """Test that IssueHandler delegates deduplication to server-side batch operations.

        With server-side deduplication:
        - find_existing_issue() returns None (server handles deduplication via UniqueKeyFields)
        - Cache is still warmed for statistics tracking
        - No client-side create vs update decisions
        """
        # Setup
        _context = ScannerContext(plan_id=123, tenant_id=1)  # noqa: F841
        issue_cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Scanner",
            issue_identifier_field="otherIdentifier",
        )

        # Create mock existing issues
        mock_issue1 = MagicMock(spec=regscale_models.Issue)
        mock_issue1.id = 1
        mock_issue1.integrationFindingId = "FINDING-001"
        mock_issue1.status = regscale_models.IssueStatus.Open
        mock_issue1.otherIdentifier = "EXT-001"

        mock_issue2 = MagicMock(spec=regscale_models.Issue)
        mock_issue2.id = 2
        mock_issue2.integrationFindingId = "FINDING-002"
        mock_issue2.status = regscale_models.IssueStatus.Closed
        mock_issue2.otherIdentifier = "EXT-002"

        mock_fetch_issues.return_value = [mock_issue1, mock_issue2]
        mock_open_issues.return_value = {}

        # Warm the cache
        issue_cache.warm_cache()

        # Create handler with cache
        handler = IssueHandler(
            plan_id=123,
            parent_module="securityplans",
            issue_cache=issue_cache,
            assessor_id="user123",
            title="Test Scanner",
            issue_identifier_field="otherIdentifier",
        )

        # Create finding
        finding = IntegrationFinding(
            control_labels=["AC-1"],
            title="Test Finding",
            category="Security",
            plugin_name="Test Plugin",
            severity=regscale_models.IssueSeverity.High,
            description="Test description",
            status=regscale_models.IssueStatus.Open,
            external_id="EXT-001",
        )

        # With server-side deduplication, find_existing_issue returns None
        # The server handles deduplication via UniqueKeyFields in batch options
        existing_issue = handler.find_existing_issue(finding)

        # Verify server-side deduplication pattern - client doesn't do lookups
        assert existing_issue is None

        # Verify cache was still warmed (for statistics tracking)
        mock_fetch_issues.assert_called_once()

    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_all_by_parent")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_issue_cache_fallback_to_identifier_field(self, mock_open_issues, mock_fetch_issues, mock_get_all):
        """Test IssueCache falls back to identifier field when integrationFindingId not matched."""
        # Setup
        issue_cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Scanner",
            issue_identifier_field="otherIdentifier",
        )

        # Mock issue without integrationFindingId but with otherIdentifier
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.integrationFindingId = None  # Not indexed
        mock_issue.otherIdentifier = "EXT-003"
        mock_issue.sourceReport = "Test Scanner"
        mock_issue.status = regscale_models.IssueStatus.Open

        mock_fetch_issues.return_value = [mock_issue]
        mock_open_issues.return_value = {}
        mock_get_all.return_value = [mock_issue]  # For fallback lookup

        # Warm cache
        issue_cache.warm_cache()

        # Create finding with external_id
        finding = IntegrationFinding(
            control_labels=["AC-1"],
            title="Test Finding",
            category="Security",
            plugin_name="Test Plugin",
            severity=regscale_models.IssueSeverity.High,
            description="Test description",
            status=regscale_models.IssueStatus.Open,
            external_id="EXT-003",
        )

        # Should find issue via fallback (external_id -> otherIdentifier)
        existing_issues = issue_cache._get_existing_issues_for_finding("FINDING-999", finding)
        assert len(existing_issues) > 0
        assert existing_issues[0].id == 1

    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_issue_cache_effectiveness_metrics(self, mock_open_issues, mock_fetch_issues):
        """Test that IssueCache tracks hit/miss statistics correctly."""
        # Setup
        issue_cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Scanner",
        )

        mock_issue1 = MagicMock(spec=regscale_models.Issue)
        mock_issue1.id = 1
        mock_issue1.integrationFindingId = "FINDING-001"

        mock_fetch_issues.return_value = [mock_issue1]
        mock_open_issues.return_value = {}

        issue_cache.warm_cache()

        # Cache hit
        finding1 = IntegrationFinding(
            control_labels=[],
            title="Test",
            category="Security",
            plugin_name="Test",
            severity=regscale_models.IssueSeverity.Moderate,
            description="",
            status=regscale_models.IssueStatus.Open,
        )
        issue_cache._get_existing_issues_for_finding("FINDING-001", finding1)

        # Cache miss
        finding2 = IntegrationFinding(
            control_labels=[],
            title="Test",
            category="Security",
            plugin_name="Test",
            severity=regscale_models.IssueSeverity.Moderate,
            description="",
            status=regscale_models.IssueStatus.Open,
        )
        issue_cache._get_existing_issues_for_finding("FINDING-999", finding2)

        # Check stats
        stats = issue_cache.get_cache_stats()
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 50.0
        assert stats["total_lookups"] == 2


class TestScannerContextStateSharing(CLITestFixture):
    """Test ScannerContext sharing state between components."""

    def test_context_shared_between_handlers(self):
        """Test that handlers share state through ScannerContext."""
        # Create context with shared state
        context = ScannerContext(
            plan_id=123,
            tenant_id=1,
            title="Test Scanner",
            scanner_type=ScannerIntegrationType.VULNERABILITY,
        )

        # Populate shared state
        context.asset_map_by_identifier["ASSET-001"] = MagicMock()
        context.existing_issues_map["ISSUE-001"] = MagicMock()

        # Create handlers that share the context
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            external_cache=context.asset_map_by_identifier,
        )
        _asset_handler = AssetHandler(context, asset_cache)  # noqa: F841

        issue_cache = IssueCache(plan_id=123, parent_module="securityplans")
        _issue_handler = IssueHandler(  # noqa: F841
            plan_id=123,
            parent_module="securityplans",
            issue_cache=issue_cache,
            assessor_id="user123",
            title="Test Scanner",
        )

        # Verify shared state is accessible
        assert len(context.asset_map_by_identifier) == 1
        assert "ASSET-001" in context.asset_map_by_identifier

    def test_context_lock_registry_thread_safety(self):
        """Test that ScannerContext lock registry provides thread-safe access."""
        context = ScannerContext(plan_id=123, tenant_id=1)

        # Get locks for same key from different threads
        locks = []

        def get_lock_in_thread(key):
            lock = context.get_lock(key)
            locks.append(lock)

        threads = [threading.Thread(target=get_lock_in_thread, args=("test_key",)) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads should get the same lock instance
        assert len(locks) == 5
        assert all(lock is locks[0] for lock in locks)

    def test_context_result_tracking(self):
        """Test that ScannerContext tracks results correctly."""
        context = ScannerContext(plan_id=123, tenant_id=1)

        # Update results
        context.update_result_counts("assets", {"created": [1, 2, 3], "updated": [4, 5]})
        context.update_result_counts("issues", {"created": [10], "updated": [11, 12, 13]})

        # Verify results tracked
        assert context._results["assets"]["created_count"] == 3
        assert context._results["assets"]["updated_count"] == 2
        assert context._results["issues"]["created_count"] == 1
        assert context._results["issues"]["updated_count"] == 3

        # Update again to test accumulation
        context.update_result_counts("assets", {"created": [6], "updated": []})
        assert context._results["assets"]["created_count"] == 4
        assert context._results["assets"]["updated_count"] == 2


class TestEndToEndWorkflows(CLITestFixture):
    """Test end-to-end workflows with multiple components."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Issue.get_user_id")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_asset_creation_to_finding_processing(self, mock_get_all, mock_asset_class, mock_user_id):
        """Test complete workflow: asset creation → finding processing → issue creation."""
        # Setup
        mock_user_id.return_value = "user123"

        # Setup context and caches
        context = ScannerContext(
            plan_id=123,
            tenant_id=1,
            title="Test Scanner",
            scanner_type=ScannerIntegrationType.VULNERABILITY,
        )

        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            identifier_field="otherTrackingNumber",
        )

        issue_cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Scanner",
        )

        # Create handlers
        asset_handler = AssetHandler(context, asset_cache)
        issue_handler = IssueHandler(
            plan_id=123,
            parent_module="securityplans",
            issue_cache=issue_cache,
            assessor_id="user123",
            title="Test Scanner",
        )

        # Mock empty initial state
        mock_get_all.return_value = []
        asset_cache.warm_cache()

        # Step 1: Create assets
        integration_asset = IntegrationAsset(
            name="Web Server",
            identifier="WEB-001",
            asset_type="Virtual Machine (VM)",
            asset_category="Hardware",
            ip_address="10.0.0.100",
        )

        mock_created_asset = MagicMock()
        mock_created_asset.id = 100
        mock_created_asset.otherTrackingNumber = "WEB-001"
        mock_created_asset.name = "Web Server"
        mock_created_asset.ipAddress = "10.0.0.100"

        mock_asset_instance = MagicMock()
        mock_asset_instance.create_or_update_with_status.return_value = ("created", mock_created_asset)
        mock_asset_class.return_value = mock_asset_instance

        created, asset = asset_handler.create_new_asset(integration_asset, component=None)

        # Verify asset created and cached
        assert created is True
        assert asset.id == 100
        assert "WEB-001" in asset_cache

        # Step 2: Process finding for the asset
        with patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp") as mock_fetch:
            with patch(
                "regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id"
            ) as mock_open:
                mock_fetch.return_value = []
                mock_open.return_value = {}
                issue_cache.warm_cache()

                finding = IntegrationFinding(
                    control_labels=["AC-1"],
                    title="Critical Vulnerability on Web Server",
                    category="Security",
                    plugin_name="CVE-2024-1234",
                    severity=regscale_models.IssueSeverity.Critical,
                    description="Critical vulnerability found",
                    status=regscale_models.IssueStatus.Open,
                    asset_identifier="WEB-001",
                    external_id="VULN-001",
                )

                # Create issue from finding (server-side deduplication pattern)
                with patch.object(issue_handler, "_build_issue_from_finding") as mock_build:
                    mock_issue = MagicMock()
                    mock_issue.id = 200
                    mock_build.return_value = mock_issue

                    issue = issue_handler.create_or_update_issue("Test Issue", finding)

                    # Verify issue built (server handles create vs update via batch options)
                    assert issue.id == 200
                    mock_build.assert_called_once()

    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_processing_100_assets_with_cache_warming(self, mock_get_all):
        """Test processing 100 assets with efficient cache warming."""
        # Setup
        context = ScannerContext(plan_id=123, tenant_id=1)
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            identifier_field="otherTrackingNumber",
        )

        # Create 100 mock existing assets
        existing_assets = []
        for i in range(100):
            asset = MagicMock()
            asset.id = i + 1
            asset.otherTrackingNumber = f"ASSET-{i:03d}"
            asset.name = f"Asset {i}"
            asset.ipAddress = f"192.168.1.{i}"
            existing_assets.append(asset)

        mock_get_all.return_value = existing_assets

        # Warm cache (single API call)
        asset_cache.warm_cache()

        # Verify cache populated
        assert len(asset_cache) == 100
        assert asset_cache.is_loaded

        # Simulate processing: lookup each asset (should use cache only)
        handler = AssetHandler(context, asset_cache)
        found_count = 0
        for i in range(100):
            asset = handler.get_asset_by_identifier(f"ASSET-{i:03d}")
            if asset:
                found_count += 1

        # All lookups successful
        assert found_count == 100

        # Verify only one API call was made (during warming)
        mock_get_all.assert_called_once()

    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_all_by_parent")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_processing_50_findings_with_server_side_deduplication(
        self, mock_open_issues, mock_fetch_issues, mock_get_all
    ):
        """Test processing 50 findings with server-side deduplication.

        With server-side deduplication:
        - find_existing_issue() returns None (server handles deduplication via UniqueKeyFields)
        - All findings are queued for batch processing
        - The server uses integrationFindingId to create or update accordingly
        - Cache is warmed for statistics but not used for create vs update decisions
        """
        # Setup
        issue_cache = IssueCache(
            plan_id=123,
            parent_module="securityplans",
            title="Test Scanner",
        )

        # Create 25 existing issues (simulate 50% duplicate rate on server)
        existing_issues = []
        for i in range(25):
            issue = MagicMock()
            issue.id = i + 1
            issue.integrationFindingId = f"FINDING-{i:03d}"
            issue.status = regscale_models.IssueStatus.Open
            existing_issues.append(issue)

        mock_fetch_issues.return_value = existing_issues
        mock_open_issues.return_value = {}
        mock_get_all.return_value = existing_issues  # For fallback lookup

        # Warm cache (for statistics tracking)
        issue_cache.warm_cache()

        # Create handler
        handler = IssueHandler(
            plan_id=123,
            parent_module="securityplans",
            issue_cache=issue_cache,
            assessor_id="user123",
            title="Test Scanner",
        )

        # Process 50 findings - with server-side deduplication, all go to batch queue
        findings_processed = 0

        for i in range(50):
            finding = IntegrationFinding(
                control_labels=[],
                title=f"Finding {i}",
                category="Security",
                plugin_name="Test",
                severity=regscale_models.IssueSeverity.Moderate,
                description="Test",
                status=regscale_models.IssueStatus.Open,
            )

            # With server-side deduplication, find_existing_issue returns None
            existing = handler.find_existing_issue(finding)
            assert existing is None  # Server handles deduplication, not client
            findings_processed += 1

        # All 50 findings processed (server will deduplicate in batch operation)
        assert findings_processed == 50

        # Cache was still warmed (for stats tracking) - verify by checking cache_size
        stats = issue_cache.get_cache_stats()
        assert stats["cache_size"] == 25  # 25 issues were indexed in the cache


class TestBatchProcessingWithCaches(CLITestFixture):
    """Test batch processing operations with caching."""

    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_batch_asset_operations_with_cache_updates(self, mock_get_all):
        """Test batch asset operations update cache correctly."""
        # Setup
        _context = ScannerContext(plan_id=123, tenant_id=1, asset_batch_size=10)  # noqa: F841
        asset_cache = AssetCache(plan_id=123, parent_module="securityplans")

        # Start with empty cache
        mock_get_all.return_value = []
        asset_cache.warm_cache()
        assert len(asset_cache) == 0

        # Simulate batch creation of 50 assets
        created_assets = []
        for i in range(50):
            asset = MagicMock()
            asset.id = i + 1
            asset.otherTrackingNumber = f"NEW-{i:03d}"
            asset.name = f"New Asset {i}"
            created_assets.append(asset)
            asset_cache.add(asset)

        # Verify cache updated
        assert len(asset_cache) == 50
        for i in range(50):
            assert f"NEW-{i:03d}" in asset_cache

    def test_concurrent_asset_processing_thread_safety(self):
        """Test concurrent asset processing is thread-safe."""
        _context = ScannerContext(plan_id=123, tenant_id=1)  # noqa: F841
        shared_cache = ThreadSafeDict()
        asset_cache = AssetCache(
            plan_id=123,
            parent_module="securityplans",
            external_cache=shared_cache,
        )

        results = []
        errors = []

        def process_asset_in_thread(asset_id):
            try:
                # Simulate adding asset to cache
                asset = MagicMock()
                asset.id = asset_id
                asset.otherTrackingNumber = f"ASSET-{asset_id:03d}"
                asset_cache.add(asset)
                results.append(asset_id)
            except Exception as e:
                errors.append((asset_id, str(e)))

        # Process 20 assets concurrently
        threads = [threading.Thread(target=process_asset_in_thread, args=(i,)) for i in range(20)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors and all assets added
        assert len(errors) == 0
        assert len(results) == 20
        assert len(asset_cache) == 20


class TestErrorPropagationAndHandling(CLITestFixture):
    """Test error propagation and handling across components."""

    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    def test_asset_cache_handles_api_errors_gracefully(self, mock_get_all):
        """Test AssetCache handles API errors gracefully."""
        # Setup
        asset_cache = AssetCache(plan_id=123, parent_module="securityplans")

        # Simulate API error
        mock_get_all.side_effect = Exception("API Error")

        # Cache warming should propagate error
        with pytest.raises(Exception) as exc_info:
            asset_cache.warm_cache()

        assert "API Error" in str(exc_info.value)

    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_issue_cache_handles_malformed_data(self, mock_open_issues, mock_fetch_issues):
        """Test IssueCache handles malformed data gracefully."""
        # Setup
        issue_cache = IssueCache(plan_id=123, parent_module="securityplans")

        # Return malformed data (missing required attributes)
        mock_issue = MagicMock()
        mock_issue.integrationFindingId = None  # Missing
        mock_issue.id = None  # Missing

        mock_fetch_issues.return_value = [mock_issue]
        mock_open_issues.return_value = {}

        # Should handle gracefully without crashing
        issue_cache.warm_cache()

        # Cache should still be functional
        assert issue_cache._integration_finding_id_cache is not None

    def test_context_tracks_errors(self):
        """Test ScannerContext tracks errors during processing."""
        context = ScannerContext(plan_id=123, tenant_id=1)

        # Add errors
        context.errors.append("Failed to process asset ASSET-001")
        context.errors.append("Failed to create issue for finding FINDING-001")

        # Verify errors tracked
        assert len(context.errors) == 2
        assert "ASSET-001" in context.errors[0]
        assert "FINDING-001" in context.errors[1]


class TestComplexIntegrationScenarios(CLITestFixture):
    """Test complex integration scenarios."""

    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Issue.get_user_id")
    @patch("regscale.integrations.scanner.handlers.asset_handler.regscale_models.Asset")
    @patch("regscale.integrations.scanner.cache.asset_cache.regscale_models.Asset.get_all_by_parent")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.fetch_issues_by_ssp")
    @patch("regscale.integrations.scanner.cache.issue_cache.Issue.get_open_issues_ids_by_implementation_id")
    def test_vulnerability_scan_with_asset_discovery(
        self, mock_open_issues, mock_fetch_issues, mock_get_all_assets, mock_asset_class, mock_user_id
    ):
        """Test vulnerability scan with automatic asset discovery."""
        # Setup
        mock_user_id.return_value = "user123"

        context = ScannerContext(
            plan_id=123,
            tenant_id=1,
            title="Vulnerability Scanner",
            scanner_type=ScannerIntegrationType.VULNERABILITY,
        )

        asset_cache = AssetCache(plan_id=123, parent_module="securityplans")
        issue_cache = IssueCache(plan_id=123, parent_module="securityplans", title="Vulnerability Scanner")

        # Start with 5 existing assets
        existing_assets = []
        for i in range(5):
            asset = MagicMock()
            asset.id = i + 1
            asset.otherTrackingNumber = f"EXISTING-{i}"
            asset.ipAddress = f"10.0.0.{i}"
            asset.fqdn = None
            asset.dns = None
            existing_assets.append(asset)

        mock_get_all_assets.return_value = existing_assets
        mock_fetch_issues.return_value = []
        mock_open_issues.return_value = {}

        # Manually populate asset cache instead of using warm_cache()
        # to avoid mock issues with get_all_by_parent
        for asset in existing_assets:
            asset_cache.add(asset)
        asset_cache._loaded = True

        # Warm issue cache
        issue_cache.warm_cache()

        # Create handlers
        asset_handler = AssetHandler(context, asset_cache)
        _issue_handler = IssueHandler(  # noqa: F841
            plan_id=123,
            parent_module="securityplans",
            issue_cache=issue_cache,
            assessor_id="user123",
            title="Vulnerability Scanner",
        )

        # Scan finds 10 assets (5 existing, 5 new)
        scanned_assets = []
        for i in range(10):
            identifier = f"EXISTING-{i}" if i < 5 else f"NEW-{i - 5}"
            asset = IntegrationAsset(
                name=f"Server {i}",
                identifier=identifier,
                asset_type="Virtual Machine (VM)",
                asset_category="Hardware",
                ip_address=f"10.0.0.{i}",
            )
            scanned_assets.append(asset)

        # Mock new asset creation
        mock_asset_instance = MagicMock()

        def create_side_effect(*args, **kwargs):
            new_asset = MagicMock()
            new_asset.id = 100 + len(asset_cache)
            new_asset.otherTrackingNumber = args[0].identifier if args else "UNKNOWN"
            return ("created", new_asset)

        mock_asset_instance.create_or_update_with_status.side_effect = create_side_effect
        mock_asset_class.return_value = mock_asset_instance

        # Process assets
        created_count = 0
        found_count = 0

        for integration_asset in scanned_assets:
            existing = asset_handler.get_asset_by_identifier(integration_asset.identifier)
            if existing:
                found_count += 1
            else:
                created, _ = asset_handler.create_new_asset(integration_asset, component=None)
                if created:
                    created_count += 1

        # Verify results
        assert found_count == 5  # Found 5 existing
        assert created_count == 5  # Created 5 new
        assert len(asset_cache) == 10  # Total 10 assets in cache

    @patch("regscale.integrations.variables.ScannerVariables")
    def test_context_configuration_propagation(self, mock_scanner_vars):
        """Test that context configuration propagates to handlers correctly."""
        # Mock ScannerVariables to avoid overwriting batch sizes
        mock_scanner_vars.assetBatchSize = 250
        mock_scanner_vars.issueBatchSize = 500
        mock_scanner_vars.vulnerabilityBatchSize = 1000

        # Create context with specific configuration
        context = ScannerContext(
            plan_id=123,
            tenant_id=1,
            title="Test Scanner",
            scanner_type=ScannerIntegrationType.CONTROL_TEST,
            asset_identifier_field="ipAddress",
            issue_identifier_field="wizId",
            enable_cci_mapping=True,
            close_outdated_findings=False,
        )

        # Manually set batch sizes (since __post_init__ will override)
        context.asset_batch_size = 250
        context.issue_batch_size = 500
        context.vulnerability_batch_size = 1000

        # Verify context settings
        assert context.plan_id == 123
        assert context.tenant_id == 1
        assert context.title == "Test Scanner"
        assert context.scanner_type == ScannerIntegrationType.CONTROL_TEST
        assert context.asset_identifier_field == "ipAddress"
        assert context.issue_identifier_field == "wizId"
        assert context.enable_cci_mapping is True
        assert context.close_outdated_findings is False

        # Create handlers with context
        asset_cache = AssetCache(
            plan_id=context.plan_id,
            parent_module=context.parent_module,
            identifier_field=context.asset_identifier_field,
        )

        # Verify cache configured from context
        assert asset_cache.plan_id == 123
        assert asset_cache.identifier_field == "ipAddress"
