"""
Comprehensive unit tests for WizVulnerabilityIntegration scanner class.
Focuses on achieving 90%+ code coverage with emphasis on previously uncovered lines.
"""

import logging
import os
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, AsyncMock, patch, call

from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType
from regscale.integrations.commercial.wizv2.scanner import WizVulnerabilityIntegration
from regscale.integrations.commercial.wizv2.variables import WizVariables
from regscale.integrations.variables import ScannerVariables
from regscale.models import regscale_models
from regscale.models.regscale_models.issue import IssueStatus
from tests.regscale.integrations.commercial.wizv2 import (
    PROJECT_ID,
    PLAN_ID,
    asset_nodes,
    vuln_nodes,
)

logger = logging.getLogger("regscale")


@patch("regscale.integrations.scanner_integration.ScannerIntegration.__init__", return_value=None)
class TestWizVulnerabilityIntegrationScanner(unittest.TestCase):
    """Test class for WizVulnerabilityIntegration scanner methods."""

    def setUp(self, mock_parent_init=None):
        """Set up test fixtures."""
        self.plan_id = PLAN_ID
        self.project_id = PROJECT_ID

    def _initialize_scanner_attributes(self, integration, plan_id=None):
        """Initialize parent class attributes that would normally be set by ScannerIntegration.__init__."""
        from regscale.core.app.application import Application
        from regscale.core.app.utils.app_utils import create_progress_object
        from regscale.utils.threading import ThreadSafeList, ThreadSafeDict

        integration.app = Application()
        integration.plan_id = plan_id if plan_id is not None else self.plan_id
        integration.tenant_id = 1
        integration.is_component = False
        integration.parent_module = regscale_models.SecurityPlan.get_module_string()
        integration.asset_progress = create_progress_object()
        integration.finding_progress = create_progress_object()
        integration.components_by_title = ThreadSafeDict()
        integration.components_by_id = ThreadSafeDict()
        integration.components = ThreadSafeList()
        integration.errors = []
        integration.asset_map_by_identifier = ThreadSafeDict()
        integration.software_to_create = ThreadSafeList()
        integration.software_to_update = ThreadSafeList()
        integration.data_to_create = ThreadSafeList()
        integration.data_to_update = ThreadSafeList()
        integration.link_to_create = ThreadSafeList()
        integration.link_to_update = ThreadSafeList()
        integration.existing_issues_map = ThreadSafeDict()
        integration.alerted_assets = set()
        from datetime import datetime

        integration.scan_date = datetime.now().strftime("%Y-%m-%d")

    # ========================================
    # Initialization and Configuration Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_init_sets_suppress_asset_not_found_errors(self, mock_authenticate, mock_parent_init):
        """Test that initialization sets suppress_asset_not_found_errors to True."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self.assertTrue(integration.suppress_asset_not_found_errors)
        self.assertIsInstance(integration._missing_asset_types, set)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_query_types_with_filter_by(self, mock_authenticate, mock_parent_init):
        """Test get_query_types with custom filter_by parameter."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        filter_by = {"severity": "HIGH"}
        query_types = integration.get_query_types(self.project_id, filter_by=filter_by)
        self.assertIsInstance(query_types, list)
        self.assertGreater(len(query_types), 0)

    # ========================================
    # Fetch Findings Tests (Lines 158-170, 388-396)
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_findings_async")
    def test_fetch_findings_uses_async_by_default(self, mock_async, mock_authenticate, mock_parent_init):
        """Test that fetch_findings uses async by default."""
        mock_authenticate.return_value = None
        mock_async.return_value = iter([])
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        list(integration.fetch_findings(wiz_project_id=self.project_id))
        mock_async.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_findings_sync")
    def test_fetch_findings_uses_sync_when_requested(self, mock_sync, mock_authenticate, mock_parent_init):
        """Test that fetch_findings uses sync when use_async=False."""
        mock_authenticate.return_value = None
        mock_sync.return_value = iter([])
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        list(integration.fetch_findings(wiz_project_id=self.project_id, use_async=False))
        mock_sync.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_findings_async")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_findings_sync")
    def test_fetch_findings_fallback_on_async_error(self, mock_sync, mock_async, mock_authenticate, mock_parent_init):
        """Test fetch_findings falls back to sync on async error (line 165)."""
        mock_authenticate.return_value = None
        mock_async.side_effect = Exception("Async error")
        mock_sync.return_value = iter([])
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        list(integration.fetch_findings(wiz_project_id=self.project_id, use_async=True))
        mock_sync.assert_called_once()

    # ========================================
    # Async Findings Fetch Tests (Lines 388-408)
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._validate_project_id")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.get_query_types")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._setup_authentication_headers")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._should_fetch_fresh_data")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._process_query_results")
    def test_fetch_findings_async_success_with_missing_asset_types(
        self,
        mock_process,
        mock_should_fetch,
        mock_execute,
        mock_headers,
        mock_query_types,
        mock_validate,
        mock_authenticate,
        mock_parent_init,
    ):
        """Test fetch_findings_async with missing asset types tracking (lines 399-404)."""
        mock_authenticate.return_value = None
        mock_validate.return_value = self.project_id
        mock_query_types.return_value = [
            {"type": WizVulnerabilityType.VULNERABILITY, "query": "test_query", "variables": {}}
        ]
        mock_headers.return_value = {"Authorization": "Bearer test"}
        mock_execute.return_value = []
        mock_should_fetch.return_value = True
        mock_process.return_value = iter([])

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration._missing_asset_types = {"VM", "DATABASE"}
        list(integration.fetch_findings_async(wiz_project_id=self.project_id))

        # Verify missing asset types were tracked
        self.assertEqual(integration._missing_asset_types, {"VM", "DATABASE"})

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._validate_project_id")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_findings_sync")
    def test_fetch_findings_async_error_fallback(self, mock_sync, mock_validate, mock_authenticate, mock_parent_init):
        """Test fetch_findings_async falls back to sync on error (lines 388-396)."""
        mock_authenticate.return_value = None
        mock_validate.side_effect = Exception("Validation error")
        mock_sync.return_value = iter([])

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        list(integration.fetch_findings_async(wiz_project_id=self.project_id))

        mock_sync.assert_called_once()

    # ========================================
    # Process Query Results Tests (Lines 264-273)
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_query_results_with_error(self, mock_authenticate, mock_parent_init):
        """Test _process_query_results handles errors properly (lines 264-266)."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        results = [("VULNERABILITY", [], Exception("Test error"))]
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "test",
                "file_path": "/tmp/test.json",
            }
        ]

        findings = list(integration._process_query_results(results, query_configs, self.project_id, False))
        self.assertEqual(len(findings), 0)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_query_results_missing_vulnerability_type(self, mock_authenticate, mock_parent_init):
        """Test _process_query_results with missing vulnerability type (lines 271-273)."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        results = [("UNKNOWN_TYPE", [{"id": "test"}], None)]
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "test",
                "file_path": "/tmp/test.json",
            }
        ]

        findings = list(integration._process_query_results(results, query_configs, self.project_id, False))
        self.assertEqual(len(findings), 0)

    # ========================================
    # Cache Management Tests (Lines 230-241)
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.run_async_queries")
    def test_execute_concurrent_queries_fetches_fresh_data(self, mock_run_async, mock_authenticate, mock_parent_init):
        """Test _execute_concurrent_queries fetches fresh data (lines 232-240)."""
        mock_authenticate.return_value = None
        mock_run_async.return_value = []

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "test_query",
                "variables": {},
                "file_path": "/tmp/nonexistent.json",
            }
        ]
        headers = {"Authorization": "Bearer test"}

        with patch.object(integration, "_should_fetch_fresh_data", return_value=True):
            integration._execute_concurrent_queries(query_configs, headers)

        mock_run_async.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.load_cached_findings")
    def test_execute_concurrent_queries_loads_cached_data(self, mock_load_cached, mock_authenticate, mock_parent_init):
        """Test _execute_concurrent_queries loads cached data (line 241)."""
        mock_authenticate.return_value = None
        mock_load_cached.return_value = []

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "test_query",
                "variables": {},
                "file_path": "/tmp/test.json",
            }
        ]
        headers = {"Authorization": "Bearer test"}

        with patch.object(integration, "_should_fetch_fresh_data", return_value=False):
            integration._execute_concurrent_queries(query_configs, headers)

        mock_load_cached.assert_called_once()

    # ========================================
    # Should Fetch Fresh Data Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("os.path.exists")
    def test_should_fetch_fresh_data_missing_file(self, mock_exists, mock_authenticate, mock_parent_init):
        """Test _should_fetch_fresh_data returns True for missing file."""
        mock_authenticate.return_value = None
        mock_exists.return_value = False

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"file_path": "/tmp/missing.json"}]

        result = integration._should_fetch_fresh_data(query_configs)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_should_fetch_fresh_data_old_file(self, mock_getmtime, mock_exists, mock_authenticate, mock_parent_init):
        """Test _should_fetch_fresh_data returns True for old file."""
        mock_authenticate.return_value = None
        mock_exists.return_value = True
        # File modified 10 hours ago
        mock_getmtime.return_value = time.time() - (10 * 3600)

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"file_path": "/tmp/old.json"}]

        result = integration._should_fetch_fresh_data(query_configs)
        self.assertTrue(result)

    # ========================================
    # Load Cached Data with Progress Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.load_cached_findings")
    def test_load_cached_data_with_progress(self, mock_load_cached, mock_authenticate, mock_parent_init):
        """Test _load_cached_data_with_progress loads data correctly."""
        mock_authenticate.return_value = None
        mock_load_cached.return_value = [("VULNERABILITY", [{"id": "test"}], None)]

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        query_configs = [
            {
                "type": WizVulnerabilityType.VULNERABILITY,
                "query": "test",
                "file_path": "/tmp/test.json",
            }
        ]

        results = integration._load_cached_data_with_progress(query_configs)
        self.assertEqual(len(results), 1)
        mock_load_cached.assert_called_once()

    # ========================================
    # Save Data to Cache Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.save_json_file")
    def test_save_data_to_cache_success(self, mock_save, mock_authenticate, mock_parent_init):
        """Test _save_data_to_cache saves successfully."""
        mock_authenticate.return_value = None
        mock_save.return_value = True

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [{"id": "test1"}, {"id": "test2"}]
        integration._save_data_to_cache(nodes, "/tmp/cache.json")

        mock_save.assert_called_once_with(nodes, "/tmp/cache.json", create_dir=True)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.save_json_file")
    def test_save_data_to_cache_no_path(self, mock_save, mock_authenticate, mock_parent_init):
        """Test _save_data_to_cache skips when no path provided."""
        mock_authenticate.return_value = None

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [{"id": "test1"}]
        integration._save_data_to_cache(nodes, None)

        mock_save.assert_not_called()

    # ========================================
    # Parse Findings Tests (Lines 744-748)
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_parse_findings_all_filtered_by_severity(self, mock_authenticate, mock_parent_init):
        """Test parse_findings when all findings are filtered by severity (lines 744-748)."""
        mock_authenticate.return_value = None

        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "critical"}}

        # Create nodes with only LOW severity
        nodes = [
            {"id": "test1", "severity": "LOW", "status": "OPEN"},
            {"id": "test2", "severity": "MEDIUM", "status": "OPEN"},
        ]

        findings = list(integration.parse_findings(nodes, WizVulnerabilityType.VULNERABILITY))
        self.assertEqual(len(findings), 0)

    # ========================================
    # Consolidation Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_apply_consolidation_for_data_finding(self, mock_authenticate, mock_parent_init):
        """Test _should_apply_consolidation for DATA_FINDING type."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        result = integration._should_apply_consolidation(WizVulnerabilityType.DATA_FINDING)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_not_apply_consolidation_for_secrets(self, mock_authenticate, mock_parent_init):
        """Test _should_apply_consolidation returns False for SECRET_FINDING."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        result = integration._should_apply_consolidation(WizVulnerabilityType.SECRET_FINDING)
        self.assertFalse(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_group_findings_for_consolidation(self, mock_authenticate, mock_parent_init):
        """Test _group_findings_for_consolidation groups correctly."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        nodes = [
            {"sourceRule": {"name": "Rule1"}, "entitySnapshot": {"providerId": "provider1"}},
            {"sourceRule": {"name": "Rule1"}, "entitySnapshot": {"providerId": "provider1"}},
            {"sourceRule": {"name": "Rule2"}, "entitySnapshot": {"providerId": "provider2"}},
        ]

        groups = integration._group_findings_for_consolidation(nodes)
        self.assertIsInstance(groups, dict)
        # Should have 2 groups: Rule1|provider1 and Rule2|provider2
        self.assertGreaterEqual(len(groups), 2)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_create_consolidated_scanner_finding(self, mock_authenticate, mock_parent_init):
        """Test _create_consolidated_scanner_finding creates consolidated finding."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        nodes = [
            {
                "id": "finding1",
                "name": "CVE-2024-1234",
                "severity": "HIGH",
                "status": "OPEN",
                "vulnerableAsset": {"id": "asset1", "name": "Asset 1", "providerUniqueId": "provider1"},
            },
            {
                "id": "finding2",
                "name": "CVE-2024-1234",
                "severity": "HIGH",
                "status": "OPEN",
                "vulnerableAsset": {"id": "asset2", "name": "Asset 2", "providerUniqueId": "provider2"},
            },
        ]

        result = integration._create_consolidated_scanner_finding(nodes, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNotNone(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_create_consolidated_scanner_finding_no_asset_ids(self, mock_authenticate, mock_parent_init):
        """Test _create_consolidated_scanner_finding falls back when no asset IDs."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        nodes = [
            {
                "id": "finding1",
                "name": "CVE-2024-1234",
                "severity": "HIGH",
                "status": "OPEN",
            }
        ]

        with patch.object(integration, "get_asset_id_from_node", return_value=None):
            with patch.object(integration, "parse_finding", return_value=Mock()) as mock_parse:
                consolidated_finding = integration._create_consolidated_scanner_finding(
                    nodes, WizVulnerabilityType.VULNERABILITY
                )
                self.assertIsNotNone(consolidated_finding)
                mock_parse.assert_called_once()

    # ========================================
    # Determine Grouping Scope Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_database(self, mock_authenticate, mock_parent_init):
        """Test _determine_grouping_scope for database resources."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        provider_id = "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1/databases/db1"
        result = integration._determine_grouping_scope(provider_id, "Database Rule")

        self.assertEqual(result, "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_app_configuration(self, mock_authenticate, mock_parent_init):
        """Test _determine_grouping_scope for app configuration resources."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        provider_id = (
            "/subscriptions/abc/resourcegroups/rg1/providers/microsoft.appconfiguration/configurationstores/store1"
        )
        result = integration._determine_grouping_scope(provider_id, "App Configuration Rule")

        self.assertIn("resourcegroups/rg1", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_default(self, mock_authenticate, mock_parent_init):
        """Test _determine_grouping_scope default behavior."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        provider_id = "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1"
        result = integration._determine_grouping_scope(provider_id, "Other Rule")

        self.assertEqual(result, provider_id)

    # ========================================
    # Get Rule Name from Node Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_rule_name_from_node_with_source_rule(self, mock_authenticate, mock_parent_init):
        """Test _get_rule_name_from_node extracts from sourceRule."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"sourceRule": {"name": "Test Rule"}}
        result = integration._get_rule_name_from_node(node)
        self.assertEqual(result, "Test Rule")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_rule_name_from_node_fallback_to_name(self, mock_authenticate, mock_parent_init):
        """Test _get_rule_name_from_node falls back to name field."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"name": "Fallback Name"}
        result = integration._get_rule_name_from_node(node)
        self.assertEqual(result, "Fallback Name")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_rule_name_from_node_fallback_to_title(self, mock_authenticate, mock_parent_init):
        """Test _get_rule_name_from_node falls back to title field."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"title": "Title Name"}
        result = integration._get_rule_name_from_node(node)
        self.assertEqual(result, "Title Name")

    # ========================================
    # Get Provider ID from Node Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_entity_snapshot(self, mock_authenticate, mock_parent_init):
        """Test _get_provider_id_from_node with entitySnapshot."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"entitySnapshot": {"providerId": "provider-123"}}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "provider-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_vulnerable_asset(self, mock_authenticate, mock_parent_init):
        """Test _get_provider_id_from_node with vulnerableAsset."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"vulnerableAsset": {"providerId": "provider-456"}}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "provider-456")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_fallback_to_asset_id(self, mock_authenticate, mock_parent_init):
        """Test _get_provider_id_from_node falls back to asset ID."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"vulnerableAsset": {"id": "asset-789"}}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "asset-789")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_empty(self, mock_authenticate, mock_parent_init):
        """Test _get_provider_id_from_node returns empty string when not found."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"someOtherField": "value"}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "")

    # ========================================
    # Get Asset ID from Node Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_node_configuration_finding(self, mock_authenticate, mock_parent_init):
        """Test get_asset_id_from_node for CONFIGURATION type."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"resource": {"id": "resource-123"}}
        result = integration.get_asset_id_from_node(node, WizVulnerabilityType.CONFIGURATION)
        self.assertEqual(result, "resource-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_node_issue_type(self, mock_authenticate, mock_parent_init):
        """Test get_asset_id_from_node for ISSUE type."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"entitySnapshot": {"id": "entity-456"}}
        result = integration.get_asset_id_from_node(node, WizVulnerabilityType.ISSUE)
        self.assertEqual(result, "entity-456")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_node_with_fallback(self, mock_authenticate, mock_parent_init):
        """Test get_asset_id_from_node uses fallback when primary key not found."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        # Node doesn't have vulnerableAsset, but has resource
        node = {"resource": {"id": "fallback-resource"}}
        result = integration.get_asset_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(result, "fallback-resource")

    # ========================================
    # Get Provider Unique ID from Node Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_from_node_issue_type(self, mock_authenticate, mock_parent_init):
        """Test get_provider_unique_id_from_node for ISSUE type."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"entitySnapshot": {"providerId": "provider-issue-123"}}
        result = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.ISSUE)
        self.assertEqual(result, "provider-issue-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_from_node_issue_type_fallback(self, mock_authenticate, mock_parent_init):
        """Test get_provider_unique_id_from_node for ISSUE type with fallback."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"entitySnapshot": {"name": "issue-name"}}
        result = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.ISSUE)
        self.assertEqual(result, "issue-name")

    # ========================================
    # Parse Finding Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_parse_finding_configuration_type(self, mock_authenticate, mock_parent_init):
        """Test parse_finding routes to generic parsing for CONFIGURATION type."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {
            "id": "config-1",
            "name": "Configuration Finding",
            "severity": "HIGH",
            "status": "OPEN",
            "resource": {"id": "resource-1"},
        }

        with patch.object(integration, "_parse_generic_finding") as mock_parse:
            mock_parse.return_value = Mock()
            finding = integration.parse_finding(node, WizVulnerabilityType.CONFIGURATION)
            self.assertIsNotNone(finding)
            mock_parse.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_parse_finding_error_handling(self, mock_authenticate, mock_parent_init):
        """Test parse_finding handles errors gracefully."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {"id": "error-node"}

        with patch.object(integration, "_parse_generic_finding", side_effect=KeyError("Missing key")):
            finding = integration.parse_finding(node, WizVulnerabilityType.VULNERABILITY)
            self.assertIsNone(finding)

    # ========================================
    # Severity Filtering Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_unknown_severity(self, mock_authenticate, mock_parent_init):
        """Test should_process_finding_by_severity with unknown severity defaults to processing."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "low"}}

        result = integration.should_process_finding_by_severity("UNKNOWN_SEVERITY")
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_value_error(self, mock_authenticate, mock_parent_init):
        """Test should_process_finding_by_severity handles ValueError gracefully."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "invalid_severity"}}

        result = integration.should_process_finding_by_severity("HIGH")
        # Should default to processing when config is invalid
        self.assertTrue(result)

    # ========================================
    # Finding Data Extraction Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_secret_finding_data(self, mock_authenticate, mock_parent_init):
        """Test _get_secret_finding_data extracts data correctly."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        node = {
            "type": "AWS_SECRET_KEY",
            "resource": {"name": "test-resource"},
            "confidence": "High",
            "isEncrypted": False,
            "isManaged": True,
            "rule": {"name": "AWS Secret Detection"},
        }

        result = integration._get_secret_finding_data(node)
        self.assertEqual(result["category"], "Wiz Secret Detection")
        self.assertIn("AWS_SECRET_KEY", result["title"])
        self.assertIn("Confidence: High", result["description"])

    # ========================================
    # Status Mapping Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_wiz_status_active(self, mock_authenticate, mock_parent_init):
        """Test map_wiz_status for Active status."""
        mock_authenticate.return_value = None
        status = WizVulnerabilityIntegration.map_wiz_status("Active")
        self.assertEqual(status, regscale_models.AssetStatus.Active)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_wiz_status_inactive(self, mock_authenticate, mock_parent_init):
        """Test map_wiz_status for Inactive status."""
        mock_authenticate.return_value = None
        status = WizVulnerabilityIntegration.map_wiz_status("Inactive")
        self.assertEqual(status, regscale_models.AssetStatus.Inactive)

    # ========================================
    # Process Comments Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_comments_empty_edges(self, mock_authenticate, mock_parent_init):
        """Test process_comments with empty edges."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        comments_dict = {"comments": {"edges": []}}
        result = integration.process_comments(comments_dict)
        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_comments_with_data(self, mock_authenticate, mock_parent_init):
        """Test process_comments with comment data."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

        comments_dict = {
            "comments": {
                "edges": [
                    {"node": {"author": {"name": "John Doe"}, "body": "Comment 1"}},
                    {"node": {"author": {"name": "Jane Smith"}, "body": "Comment 2"}},
                ]
            }
        }
        result = integration.process_comments(comments_dict)
        self.assertIn("John Doe: Comment 1", result)
        self.assertIn("Jane Smith: Comment 2", result)

    # ========================================
    # Integration Tests with Real Data
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_parse_findings_integration_with_consolidation(self, mock_authenticate, mock_parent_init):
        """Integration test for parse_findings with consolidation."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        # Use real test data
        findings = list(integration.parse_findings(vuln_nodes, WizVulnerabilityType.VULNERABILITY))

        # Should have processed some findings
        self.assertGreater(len(findings), 0)


if __name__ == "__main__":
    unittest.main()
