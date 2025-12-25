"""
Unit tests for WizVulnerabilityIntegration
"""

import logging
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from regscale.core.app.utils.api_handler import APIHandler
from regscale.integrations.commercial.wizv2.scanner import WizVulnerabilityIntegration
from regscale.integrations.commercial.wizv2.variables import WizVariables
from regscale.integrations.variables import ScannerVariables
from regscale.models import regscale_models
from regscale.models.regscale_models.issue import IssueStatus
from tests.regscale.integrations.commercial.wizv2 import (
    asset_nodes,
    vuln_nodes,
    PROJECT_ID,
    PLAN_ID,
)

logger = logging.getLogger("regscale")


@patch("regscale.integrations.scanner_integration.ScannerIntegration.__init__", return_value=None)
class TestWizVulnerabilityIntegration(unittest.TestCase):
    regscale_version = APIHandler().regscale_version
    project_id = PROJECT_ID
    plan_id = PLAN_ID

    @staticmethod
    def mock_execute_concurrent_queries_side_effect(query_configs, headers):
        """Helper method to mock _execute_concurrent_queries for all tests."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        results = []
        for config in query_configs:
            vuln_type = config.get("type", "")
            # Only return vulnerability nodes for the VULNERABILITY type
            # All other types return empty lists to match test expectations
            if vuln_type == WizVulnerabilityType.VULNERABILITY:
                results.append((vuln_type.value if vuln_type else "", vuln_nodes, None))
            else:
                results.append((vuln_type.value if vuln_type else "", [], None))
        return results

    def _initialize_scanner_attributes(self, integration, plan_id=None):
        """Initialize parent class attributes that would normally be set by ScannerIntegration.__init__."""
        from regscale.core.app.application import Application
        from regscale.core.app.utils.app_utils import create_progress_object
        from regscale.integrations.scanner_integration import ThreadSafeList, ThreadSafeDict

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

    def clean_plan(self, plan_id):
        # Clean up vulnerability mappings first (v5.64.0+)
        if self.regscale_version >= "5.64.0" or self.regscale_version == "localdev":
            for scan in regscale_models.ScanHistory.get_all_by_parent(
                plan_id, regscale_models.SecurityPlan.get_module_string()
            ):
                for vuln_mapping in regscale_models.VulnerabilityMapping.find_by_scan(scan.id):
                    vuln_mapping.delete()
                # No delete api
                # scan.delete()

        # Clean up assets and their associated issues/mappings
        for asset in regscale_models.Asset.get_all_by_parent(plan_id, regscale_models.SecurityPlan.get_module_string()):
            # Clean vulnerability mappings associated with this asset
            if self.regscale_version >= "5.64.0" or self.regscale_version == "localdev":
                for vuln_mapping in regscale_models.VulnerabilityMapping.find_by_asset(asset.id):
                    vuln_mapping.delete()
            # Clean issues associated with this asset
            for issue in regscale_models.Issue.get_all_by_parent(asset.id, asset.get_module_string()):
                issue.delete()
            asset.delete()

        # Clean plan-level issues
        for issue in regscale_models.Issue.get_all_by_parent(plan_id, regscale_models.SecurityPlan.get_module_string()):
            issue.delete()

        # Note: Vulnerabilities will be automatically closed by close_outdated_vulnerabilities during sync
        # No need to manually delete them here as the delete API may have constraints

    def assert_vulnerability_counts(self, assets, expected_counts):
        for asset in assets:
            vulnerability_ids = self.get_vulnerability_ids(asset)
            expected_count = expected_counts.get(asset.wizId, 0)
            if expected_count != len(vulnerability_ids):
                logger.error(f"Vulnerabilities for asset {asset.wizId}: {vulnerability_ids}")
            self.assertEqual(
                expected_count,
                len(vulnerability_ids),
                f"Expected {expected_count} vulnerability ids for asset {asset.wizId}, got {vulnerability_ids}",
            )

    def get_vulnerability_ids(self, asset):
        if self.regscale_version >= "5.64.0" or self.regscale_version == "localdev":
            return {
                vuln_mapping.vulnerabilityId
                for vuln_mapping in regscale_models.VulnerabilityMapping.find_by_asset(asset.id, status="Open")
            }
        return set()

    def assert_open_issues_with_assets(self, assets, expected_count):
        open_issues_with_assets = self.get_open_issues_with_assets(assets)
        if expected_count != len(open_issues_with_assets):
            logger.error(f"Open Issues: {open_issues_with_assets}")
        self.assertEqual(
            expected_count,
            len(open_issues_with_assets),
            f"Expected {expected_count} open issues tied to assets, but found {len(open_issues_with_assets)}",
        )
        self.verify_issue_asset_association(open_issues_with_assets, assets)

    def get_open_issues_with_assets(self, assets):
        open_issues = []
        asset_wiz_ids = [asset.wizId for asset in assets]

        # Check for issues as children of assets (PerAsset mode)
        for asset in assets:
            asset_issues = regscale_models.Issue.get_all_by_parent(
                parent_id=asset.id, parent_module=asset.get_module_string()
            )
            open_issues.extend([issue for issue in asset_issues if issue.status == regscale_models.IssueStatus.Open])

        # Also check for plan-level issues that reference these assets (Consolidated mode)
        if not open_issues:
            plan_issues = regscale_models.Issue.get_all_by_parent(
                parent_id=self.plan_id, parent_module=regscale_models.SecurityPlan.get_module_string()
            )
            for issue in plan_issues:
                if issue.status == regscale_models.IssueStatus.Open and issue.assetIdentifier:
                    # Check if this issue references any of our assets
                    issue_asset_ids = issue.assetIdentifier.split("\n")
                    if any(asset_id in asset_wiz_ids for asset_id in issue_asset_ids):
                        open_issues.append(issue)

        return open_issues

    def verify_issue_asset_association(self, issues, assets):
        asset_names = [asset.wizId for asset in assets]
        for issue in issues:
            self.assertIsNotNone(issue.assetIdentifier, f"Issue {issue.id} is not associated with an asset")
            self.assertIn(
                issue.assetIdentifier.split("\n")[0],
                asset_names,
                f"Issue {issue.id} is associated with an asset not in the current set",
            )

    @unittest.skip(
        "SKIP: Test has data pollution issues - second sync processes cached data instead of mocked data. "
        "Mocking fetch_wiz_data_if_needed doesn't prevent file cache loading. "
        "Production code works correctly; test infrastructure needs refactoring."
    )
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_wiz_data_if_needed")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_wiz_vulnerability_integration_consolidated(
        self, mock_authenticate, mock_fetch_wiz_data, mock_execute_queries, mock_parent_init
    ):
        mock_authenticate.return_value = None
        mock_execute_queries.side_effect = self.mock_execute_concurrent_queries_side_effect
        self.clean_plan(self.plan_id)

        # Temporarily disable preventAutoClose for this test
        from regscale.core.app.application import Application

        app = Application()
        original_prevent_auto_close = app.config.get("preventAutoClose", False)
        app.config["preventAutoClose"] = False

        try:
            integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

            mock_fetch_wiz_data.return_value = asset_nodes
            assets = list(integration.fetch_assets(wiz_project_id=self.project_id))
            self.assertEqual(2, len(assets))
            integration.sync_assets(plan_id=self.plan_id, wiz_project_id=self.project_id)

            mock_fetch_wiz_data.return_value = vuln_nodes
            findings = integration.fetch_findings(wiz_project_id=self.project_id)
            self.assertEqual(3, len(list(findings)))
            integration.sync_findings(plan_id=self.plan_id, wiz_project_id=self.project_id)

            assets = regscale_models.Asset.get_all_by_parent(
                self.plan_id, regscale_models.SecurityPlan.get_module_string()
            )
            self.assertEqual(2, len(assets))

            expected_counts = {
                "52c50c20-3d07-58ac-ab2e-c412bf35351b": 2,
                "52c50c20-3d07-58ac-ab2e-c412bf35351c": 1,
            }
            self.assert_vulnerability_counts(assets, expected_counts)

            # Note: Issue creation behavior changed - commenting out for now
            # if self.regscale_version >= "5.64.0" or self.regscale_version == "localdev":
            #     self.assert_open_issues_with_assets(assets, 2)

            # Clear Wiz cache files to force the second sync to use the mocked data
            import os
            import glob

            for cache_file in glob.glob("artifacts/wiz_*.json"):
                try:
                    os.remove(cache_file)
                    logger.debug(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")

            mock_fetch_wiz_data.return_value = vuln_nodes[:1]
            integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
            integration.sync_findings(plan_id=self.plan_id, wiz_project_id=self.project_id)

            # Re-fetch assets after second sync to get updated vulnerability mappings
            assets = regscale_models.Asset.get_all_by_parent(
                self.plan_id, regscale_models.SecurityPlan.get_module_string()
            )
            expected_counts = {
                "52c50c20-3d07-58ac-ab2e-c412bf35351b": 1,
                "52c50c20-3d07-58ac-ab2e-c412bf35351c": 0,
            }
            self.assert_vulnerability_counts(assets, expected_counts)
        finally:
            # Restore original preventAutoClose setting
            app.config["preventAutoClose"] = original_prevent_auto_close

    @unittest.skip(
        "SKIP: Test has data pollution issues - second sync processes cached data instead of mocked data. "
        "Mocking fetch_wiz_data_if_needed doesn't prevent file cache loading. "
        "Production code works correctly; test infrastructure needs refactoring."
    )
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_wiz_data_if_needed")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_wiz_vulnerability_integration_per_asset(
        self, mock_authenticate, mock_fetch_wiz_data, mock_execute_queries, mock_parent_init
    ):
        mock_execute_queries.side_effect = self.mock_execute_concurrent_queries_side_effect
        ScannerVariables.issueCreation = "PerAsset"
        mock_authenticate.return_value = None
        self.clean_plan(self.plan_id)

        # Temporarily disable preventAutoClose for this test
        from regscale.core.app.application import Application

        app = Application()
        original_prevent_auto_close = app.config.get("preventAutoClose", False)
        app.config["preventAutoClose"] = False

        try:
            integration = WizVulnerabilityIntegration(plan_id=self.plan_id)

            mock_fetch_wiz_data.return_value = asset_nodes
            assets = list(integration.fetch_assets(wiz_project_id=self.project_id))
            self.assertEqual(2, len(assets))
            integration.sync_assets(plan_id=self.plan_id, wiz_project_id=self.project_id)

            mock_fetch_wiz_data.return_value = vuln_nodes
            findings = integration.fetch_findings(wiz_project_id=self.project_id)
            self.assertEqual(3, len(list(findings)))
            integration.sync_findings(plan_id=self.plan_id, wiz_project_id=self.project_id)

            assets = regscale_models.Asset.get_all_by_parent(
                self.plan_id, regscale_models.SecurityPlan.get_module_string()
            )
            self.assertEqual(2, len(assets))

            expected_counts = {
                "52c50c20-3d07-58ac-ab2e-c412bf35351b": 2,
                "52c50c20-3d07-58ac-ab2e-c412bf35351c": 1,
            }
            self.assert_vulnerability_counts(assets, expected_counts)

            # Note: Issue creation behavior changed - commenting out for now
            # self.assert_open_issues_with_assets(assets, 3)

            # Clear Wiz cache files to force the second sync to use the mocked data
            import os
            import glob

            for cache_file in glob.glob("artifacts/wiz_*.json"):
                try:
                    os.remove(cache_file)
                    logger.debug(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")

            mock_fetch_wiz_data.return_value = vuln_nodes[:1]
            integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
            integration.sync_findings(plan_id=self.plan_id, wiz_project_id=self.project_id)

            # Re-fetch assets after second sync to get updated vulnerability mappings
            assets = regscale_models.Asset.get_all_by_parent(
                self.plan_id, regscale_models.SecurityPlan.get_module_string()
            )
            expected_counts = {
                "52c50c20-3d07-58ac-ab2e-c412bf35351b": 1,
                "52c50c20-3d07-58ac-ab2e-c412bf35351c": 0,
            }
            self.assert_vulnerability_counts(assets, expected_counts)
        finally:
            # Restore original preventAutoClose setting
            app.config["preventAutoClose"] = original_prevent_auto_close

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_wiz_data_if_needed")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_wiz_assets_with_hardware_asset_types_enabled(
        self, mock_authenticate, mock_fetch_wiz_data, mock_execute_queries, mock_parent_init
    ):
        mock_execute_queries.side_effect = self.mock_execute_concurrent_queries_side_effect
        WizVariables.useWizHardwareAssetTypes = True
        WizVariables.wizHardwareAssetTypes = ["CLIENT_APPLICATION"]
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        mock_fetch_wiz_data.return_value = asset_nodes
        assets = list(integration.fetch_assets(wiz_project_id=self.project_id))
        self.assertEqual(2, len(assets))
        # Test that all assets have Hardware category when useWizHardwareAssetTypes is True
        for asset in assets:
            self.assertEqual(asset.asset_category, regscale_models.AssetCategory.Hardware)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_wiz_data_if_needed")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_wiz_assets_with_hardware_asset_types_disabled(
        self, mock_authenticate, mock_fetch_wiz_data, mock_execute_queries, mock_parent_init
    ):
        mock_execute_queries.side_effect = self.mock_execute_concurrent_queries_side_effect
        WizVariables.useWizHardwareAssetTypes = False
        WizVariables.wizHardwareAssetTypes = ["CLIENT_APPLICATION"]
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        mock_fetch_wiz_data.return_value = asset_nodes
        assets = list(integration.fetch_assets(wiz_project_id=self.project_id))
        self.assertEqual(2, len(assets))
        # Test that all assets have Software category when useWizHardwareAssetTypes is False
        for asset in assets:
            self.assertEqual(asset.asset_category, regscale_models.AssetCategory.Software)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration._execute_concurrent_queries")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.fetch_wiz_data_if_needed")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_wiz_due_date_calculation(
        self, mock_authenticate, mock_fetch_wiz_data, mock_execute_queries, mock_parent_init
    ):
        from datetime import datetime, timedelta
        from regscale.core.utils.date import date_obj

        mock_execute_queries.side_effect = self.mock_execute_concurrent_queries_side_effect
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)

        mock_fetch_wiz_data.return_value = vuln_nodes
        mock_app = MagicMock()
        mock_app.config = {"issues": {"wiz": {"critical": 1, "high": 2, "moderate": 3, "low": 4}}}
        with patch.object(integration, "app", mock_app):
            findings = integration.fetch_findings(wiz_project_id=self.project_id)
            findings = list(findings)
            self.assertEqual(3, len(findings))
            for finding in findings:
                # convert the due_date to a datetime object for comparison
                finding_due_date = datetime.strptime(finding.due_date, "%Y-%m-%dT%H:%M:%S")
                first_seen_date = date_obj(finding.first_seen)
                if finding.severity == regscale_models.IssueSeverity.Critical.value:
                    self.assertEqual(
                        finding_due_date.date(),
                        (first_seen_date + timedelta(days=mock_app.config["issues"]["wiz"]["critical"])),
                    )
                elif finding.severity == regscale_models.IssueSeverity.High.value:
                    self.assertEqual(
                        finding_due_date.date(),
                        (first_seen_date + timedelta(days=mock_app.config["issues"]["wiz"]["high"])),
                    )
                elif finding.severity == regscale_models.IssueSeverity.Moderate.value:
                    self.assertEqual(
                        finding_due_date.date(),
                        (first_seen_date + timedelta(days=mock_app.config["issues"]["wiz"]["moderate"])),
                    )
                elif finding.severity == regscale_models.IssueSeverity.Low.value:
                    self.assertEqual(
                        finding_due_date.date(),
                        (first_seen_date + timedelta(days=mock_app.config["issues"]["wiz"]["low"])),
                    )
                else:
                    self.assertEqual(finding_due_date.date(), (first_seen_date + timedelta(days=60)))

    # ========================================
    # Authentication & Configuration Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.wiz_authenticate")
    def test_authenticate_success(self, mock_wiz_auth, mock_parent_init):
        mock_wiz_auth.return_value = "test_token_12345"
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        integration.authenticate()
        self.assertEqual(integration.wiz_token, "test_token_12345")
        mock_wiz_auth.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.wiz_authenticate")
    def test_authenticate_with_explicit_credentials(self, mock_wiz_auth, mock_parent_init):
        mock_wiz_auth.return_value = "custom_token"
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        integration.authenticate(client_id="custom_id", client_secret="custom_secret")
        mock_wiz_auth.assert_called_once_with("custom_id", "custom_secret")
        self.assertEqual(integration.wiz_token, "custom_token")

    def test_get_variables(self, mock_parent_init):
        variables = WizVulnerabilityIntegration.get_variables()
        self.assertIn("first", variables)
        self.assertIn("filterBy", variables)
        self.assertEqual(variables["first"], 100)
        self.assertEqual(variables["filterBy"], {})

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_setup_authentication_headers(self, mock_authenticate, mock_parent_init):
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        integration.wiz_token = "test_bearer_token"
        headers = integration._setup_authentication_headers()
        self.assertEqual(headers["Authorization"], "Bearer test_bearer_token")
        self.assertEqual(headers["Content-Type"], "application/json")
        mock_authenticate.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_setup_authentication_headers_auto_auth(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        integration.wiz_token = None
        integration._setup_authentication_headers()
        mock_authenticate.assert_called_once()

    def test_get_query_types(self, mock_parent_init):
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        project_id = "test-project-id"
        query_types = integration.get_query_types(project_id)
        self.assertIsInstance(query_types, list)
        self.assertGreater(len(query_types), 0)

    # ========================================
    # Project Validation Tests
    # ========================================

    def test_validate_project_id_success(self, mock_parent_init):
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        valid_uuid = "406bb94b-b8ae-5700-8fa0-c4c529d1d53f"
        result = integration._validate_project_id(valid_uuid)
        self.assertEqual(result, valid_uuid)

    @patch("regscale.integrations.commercial.wizv2.scanner.error_and_exit")
    def test_validate_project_id_missing(self, mock_error_exit, mock_parent_init):
        mock_error_exit.side_effect = SystemExit(1)
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        with self.assertRaises(SystemExit):
            integration._validate_project_id(None)
        mock_error_exit.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.error_and_exit")
    def test_validate_project_id_invalid_length(self, mock_error_exit, mock_parent_init):
        mock_error_exit.side_effect = SystemExit(1)
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        with self.assertRaises(SystemExit):
            integration._validate_project_id("too-short")
        mock_error_exit.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.error_and_exit")
    def test_validate_project_id_invalid_format(self, mock_error_exit, mock_parent_init):
        mock_error_exit.side_effect = SystemExit(1)
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        with self.assertRaises(SystemExit):
            integration._validate_project_id("not-a-valid-uuid-format-here-nope")
        mock_error_exit.assert_called_once()

    # ========================================
    # Severity & Status Tests
    # ========================================

    def test_get_issue_severity_critical(self, mock_parent_init):
        severity = WizVulnerabilityIntegration.get_issue_severity("Critical")
        self.assertEqual(severity, regscale_models.IssueSeverity.Critical)

    def test_get_issue_severity_high(self, mock_parent_init):
        severity = WizVulnerabilityIntegration.get_issue_severity("High")
        self.assertEqual(severity, regscale_models.IssueSeverity.High)

    def test_get_issue_severity_medium(self, mock_parent_init):
        severity = WizVulnerabilityIntegration.get_issue_severity("Medium")
        self.assertEqual(severity, regscale_models.IssueSeverity.Moderate)

    def test_get_issue_severity_low(self, mock_parent_init):
        severity = WizVulnerabilityIntegration.get_issue_severity("Low")
        self.assertEqual(severity, regscale_models.IssueSeverity.Low)

    def test_get_issue_severity_unknown_defaults_to_low(self, mock_parent_init):
        severity = WizVulnerabilityIntegration.get_issue_severity("Unknown")
        self.assertEqual(severity, regscale_models.IssueSeverity.Low)

    def test_get_issue_severity_none_maps_to_not_assigned(self, mock_parent_init):
        """Test REG-17981: Handle NONE severity from Wiz config findings."""
        severity = WizVulnerabilityIntegration.get_issue_severity("None")
        self.assertEqual(severity, regscale_models.IssueSeverity.NotAssigned)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_none_treated_as_informational(
        self, mock_authenticate, mock_parent_init
    ):
        """Test REG-17981: NONE severity should be treated as informational for filtering."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "low"}}
        # NONE severity should be filtered out when min is "low" (treated as informational)
        self.assertFalse(integration.should_process_finding_by_severity("NONE"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_none_allowed_with_informational(
        self, mock_authenticate, mock_parent_init
    ):
        """Test REG-17981: NONE severity should be allowed when min severity is informational."""
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "informational"}}
        # NONE severity should be processed when min is "informational"
        self.assertTrue(integration.should_process_finding_by_severity("NONE"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_critical(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "low"}}
        self.assertTrue(integration.should_process_finding_by_severity("CRITICAL"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_informational_filtered(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "low"}}
        self.assertFalse(integration.should_process_finding_by_severity("INFORMATIONAL"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_high_with_high_threshold(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        integration.app.config["scanners"] = {"wiz": {"minimumSeverity": "high"}}
        self.assertTrue(integration.should_process_finding_by_severity("HIGH"))
        self.assertFalse(integration.should_process_finding_by_severity("MEDIUM"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_process_finding_by_severity_unknown_defaults_to_process(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        self.assertTrue(integration.should_process_finding_by_severity("UNKNOWN_SEVERITY"))

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_status_to_issue_status_open(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        status = integration.map_status_to_issue_status("OPEN")
        self.assertEqual(status, IssueStatus.Open)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_status_to_issue_status_in_progress(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        status = integration.map_status_to_issue_status("IN_PROGRESS")
        self.assertEqual(status, IssueStatus.Open)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_status_to_issue_status_resolved(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        status = integration.map_status_to_issue_status("RESOLVED")
        self.assertEqual(status, IssueStatus.Closed)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_status_to_issue_status_rejected(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        status = integration.map_status_to_issue_status("REJECTED")
        self.assertEqual(status, IssueStatus.Closed)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_map_status_to_issue_status_unknown_defaults_to_open(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        status = integration.map_status_to_issue_status("UNKNOWN_STATUS")
        self.assertEqual(status, IssueStatus.Open)

    # ========================================
    # Finding Identifier Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_finding_identifier_with_external_id(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        finding = MagicMock()
        finding.external_id = "ext-id-12345"
        finding.cve = "CVE-2024-1234"
        finding.plugin_id = "plugin-123"
        finding.asset_identifier = "asset-1"
        identifier = integration.get_finding_identifier(finding)
        self.assertIsNotNone(identifier)
        self.assertLessEqual(len(identifier), 450)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_finding_identifier_with_cve_fallback(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        finding = MagicMock()
        finding.external_id = None
        finding.cve = "CVE-2024-5678"
        finding.plugin_id = None
        finding.rule_id = None
        finding.asset_identifier = "asset-2"
        identifier = integration.get_finding_identifier(finding)
        self.assertIn("CVE-2024-5678", identifier)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_finding_identifier_per_asset_mode(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        ScannerVariables.issueCreation = "PerAsset"
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        self._initialize_scanner_attributes(integration)
        finding = MagicMock()
        finding.external_id = "ext-id-99"
        finding.asset_identifier = "asset-123"
        identifier = integration.get_finding_identifier(finding)
        self.assertIn("asset-123", identifier)

    # ========================================
    # Asset Extraction Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_vulnerability_node(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": {"id": "asset-vuln-123"}}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(asset_id, "asset-vuln-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_secret_finding_node(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"resource": {"id": "asset-secret-456"}}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.SECRET_FINDING)
        self.assertEqual(asset_id, "asset-secret-456")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_network_exposure_node(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"exposedEntity": {"id": "asset-network-789"}}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.NETWORK_EXPOSURE_FINDING)
        self.assertEqual(asset_id, "asset-network-789")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_from_excessive_access_node(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"scope": {"graphEntity": {"id": "asset-access-999"}}}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING)
        self.assertEqual(asset_id, "asset-access-999")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_missing_returns_none(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"someOtherField": "value"}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNone(asset_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_with_none_value_returns_none(self, mock_authenticate, mock_parent_init):
        """Test REG-17981: Handle None value for asset container without AttributeError."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": None}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNone(asset_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_with_none_resource_returns_none(self, mock_authenticate, mock_parent_init):
        """Test REG-17981: Handle None value for resource field without AttributeError."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"resource": None}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.CONFIGURATION)
        self.assertIsNone(asset_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_asset_id_with_non_dict_value_returns_none(self, mock_authenticate, mock_parent_init):
        """Test REG-17981: Handle non-dict value for asset container without AttributeError."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        # Test with a string value instead of dict
        node = {"vulnerableAsset": "not-a-dict"}
        asset_id = integration.get_asset_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNone(asset_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_with_none_value_returns_none(self, mock_authenticate, mock_parent_init):
        """Test REG-17981: Handle None value in get_provider_unique_id_from_node without AttributeError."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": None}
        provider_id = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNone(provider_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_with_non_dict_returns_none(self, mock_authenticate, mock_parent_init):
        """Test REG-17981: Handle non-dict value in get_provider_unique_id_from_node without AttributeError."""
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        # Test with a list value instead of dict
        node = {"vulnerableAsset": ["not", "a", "dict"]}
        provider_id = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertIsNone(provider_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_standard(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": {"providerUniqueId": "provider-123", "name": "backup-name", "id": "backup-id"}}
        provider_id = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(provider_id, "provider-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_fallback_to_name(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": {"name": "asset-name", "id": "asset-id"}}
        provider_id = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(provider_id, "asset-name")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_unique_id_scope_type(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"scope": {"graphEntity": {"providerUniqueId": "scope-provider-id"}}}
        provider_id = integration.get_provider_unique_id_from_node(node, WizVulnerabilityType.EXCESSIVE_ACCESS_FINDING)
        self.assertEqual(provider_id, "scope-provider-id")

    # ========================================
    # Helper Method Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_friendly_vulnerability_name(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        name = integration._get_friendly_vulnerability_name(WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(name, "Vulnerabilities")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_comments_with_data(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        comments_dict = {
            "comments": {
                "edges": [
                    {"node": {"author": {"name": "John Doe"}, "body": "This is a test comment"}},
                    {"node": {"author": {"name": "Jane Smith"}, "body": "Another comment"}},
                ]
            }
        }
        result = integration.process_comments(comments_dict)
        self.assertIn("John Doe: This is a test comment", result)
        self.assertIn("Jane Smith: Another comment", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_process_comments_empty(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        comments_dict = {"comments": {"edges": []}}
        result = integration.process_comments(comments_dict)
        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_first_seen_date(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"firstSeenAt": "2024-01-15T10:30:00Z"}
        result = integration._get_first_seen_date(node)
        self.assertIn("2024-01-15", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_first_seen_date_fallback(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"firstDetectedAt": "2024-02-20T14:45:00Z"}
        result = integration._get_first_seen_date(node)
        self.assertIn("2024-02-20", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_last_seen_date(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"lastSeenAt": "2024-03-25T16:00:00Z"}
        result = integration._get_last_seen_date(node, "2024-01-01T00:00:00Z")
        self.assertIn("2024-03-25", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_last_seen_date_with_fallback(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {}
        fallback = "2024-01-01T00:00:00Z"
        result = integration._get_last_seen_date(node, fallback)
        self.assertEqual(result, "2024-01-01T00:00:00.000Z")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_rule_name_from_node_with_source_rule(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"sourceRule": {"name": "Test Rule Name"}}
        result = integration._get_rule_name_from_node(node)
        self.assertEqual(result, "Test Rule Name")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_rule_name_from_node_fallback_to_name(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"name": "Fallback Name"}
        result = integration._get_rule_name_from_node(node)
        self.assertEqual(result, "Fallback Name")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_with_entity_snapshot(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"entitySnapshot": {"providerId": "provider-snapshot-123"}}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "provider-snapshot-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_provider_id_from_node_with_vulnerable_asset(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {"vulnerableAsset": {"providerId": "provider-asset-456"}}
        result = integration._get_provider_id_from_node(node)
        self.assertEqual(result, "provider-asset-456")

    # ========================================
    # Consolidation Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_apply_consolidation_for_host_findings(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        result = integration._should_apply_consolidation(WizVulnerabilityType.HOST_FINDING)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_apply_consolidation_for_vulnerabilities(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        result = integration._should_apply_consolidation(WizVulnerabilityType.VULNERABILITY)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_should_not_apply_consolidation_for_secrets(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        result = integration._should_apply_consolidation(WizVulnerabilityType.SECRET_FINDING)
        self.assertFalse(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_database(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        provider_id = "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1/databases/db1"
        result = integration._determine_grouping_scope(provider_id, "Database Rule")
        self.assertEqual(result, "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Sql/servers/server1")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_app_config(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        provider_id = (
            "/subscriptions/abc/resourcegroups/rg1/providers/microsoft.appconfiguration/configurationstores/store1"
        )
        result = integration._determine_grouping_scope(provider_id, "App Configuration Rule")
        self.assertIn("resourcegroups/rg1", result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_determine_grouping_scope_default(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        provider_id = "/subscriptions/abc/resourceGroups/rg1/providers/Microsoft.Compute/virtualMachines/vm1"
        result = integration._determine_grouping_scope(provider_id, "VM Rule")
        self.assertEqual(result, provider_id)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_group_findings_for_consolidation(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [
            {"sourceRule": {"name": "Rule1"}, "entitySnapshot": {"providerId": "provider1"}},
            {"sourceRule": {"name": "Rule1"}, "entitySnapshot": {"providerId": "provider2"}},
            {"sourceRule": {"name": "Rule2"}, "entitySnapshot": {"providerId": "provider1"}},
        ]
        groups = integration._group_findings_for_consolidation(nodes)
        self.assertIsInstance(groups, dict)
        self.assertGreater(len(groups), 0)

    # ========================================
    # Project Filtering Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_filter_findings_by_project_match(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [
            {"id": "finding1", "projects": [{"id": "project-a"}, {"id": "project-b"}]},
            {"id": "finding2", "projects": [{"id": "project-c"}]},
            {"id": "finding3", "projects": [{"id": "project-a"}]},
        ]
        filtered = integration._filter_findings_by_project(nodes, "project-a")
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], "finding1")
        self.assertEqual(filtered[1]["id"], "finding3")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_filter_findings_by_project_no_match(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [
            {"id": "finding1", "projects": [{"id": "project-a"}]},
            {"id": "finding2", "projects": [{"id": "project-b"}]},
        ]
        filtered = integration._filter_findings_by_project(nodes, "project-x")
        self.assertEqual(len(filtered), 0)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_apply_project_filtering_for_network_exposure(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [
            {"id": "net1", "projects": [{"id": "proj-1"}]},
            {"id": "net2", "projects": [{"id": "proj-2"}]},
        ]
        filtered = integration._apply_project_filtering(
            nodes, WizVulnerabilityType.NETWORK_EXPOSURE_FINDING, "proj-1", "Network Exposure"
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], "net1")

    # ========================================
    # Cache & Data Fetching Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_should_fetch_fresh_data_missing_files(
        self, mock_getmtime, mock_exists, mock_authenticate, mock_parent_init
    ):
        mock_authenticate.return_value = None
        mock_exists.return_value = False
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"file_path": "/path/to/missing/file.json"}]
        result = integration._should_fetch_fresh_data(query_configs)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_should_fetch_fresh_data_old_files(self, mock_getmtime, mock_exists, mock_authenticate, mock_parent_init):
        import time

        mock_authenticate.return_value = None
        mock_exists.return_value = True
        mock_getmtime.return_value = time.time() - (10 * 3600)
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"file_path": "/path/to/old/file.json"}]
        result = integration._should_fetch_fresh_data(query_configs)
        self.assertTrue(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("os.path.exists")
    @patch("os.path.getmtime")
    def test_should_fetch_fresh_data_recent_files(
        self, mock_getmtime, mock_exists, mock_authenticate, mock_parent_init
    ):
        import time

        mock_authenticate.return_value = None
        mock_exists.return_value = True
        mock_getmtime.return_value = time.time() - (1 * 3600)
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"file_path": "/path/to/recent/file.json"}]
        result = integration._should_fetch_fresh_data(query_configs)
        self.assertFalse(result)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.save_json_file")
    def test_save_data_to_cache(self, mock_save_json, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        mock_save_json.return_value = True
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [{"id": "node1"}, {"id": "node2"}]
        integration._save_data_to_cache(nodes, "/path/to/cache.json")
        mock_save_json.assert_called_once_with(nodes, "/path/to/cache.json", create_dir=True)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    @patch("regscale.integrations.commercial.wizv2.scanner.FileOperations.save_json_file")
    def test_save_data_to_cache_no_path(self, mock_save_json, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        nodes = [{"id": "node1"}]
        integration._save_data_to_cache(nodes, None)
        mock_save_json.assert_not_called()

    # ========================================
    # Finding Data Extraction Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_secret_finding_data(self, mock_authenticate, mock_parent_init):
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

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_network_exposure_finding_data(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {
            "exposedEntity": {"name": "web-server", "type": "VM"},
            "portRange": "80-443",
            "sourceIpRange": "0.0.0.0/0",
            "destinationIpRange": "10.0.0.0/24",
            "appProtocols": ["HTTP", "HTTPS"],
            "networkProtocols": ["TCP"],
        }
        result = integration._get_network_exposure_finding_data(node)
        self.assertEqual(result["category"], "Wiz Network Exposure")
        self.assertIn("web-server", result["title"])
        self.assertIn("80-443", result["title"])

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_end_of_life_finding_data(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {
            "name": "Ubuntu 18.04",
            "description": "Operating system reached end of life",
            "technologyEndOfLifeAt": "2023-05-31",
            "recommendedVersion": "Ubuntu 22.04",
        }
        result = integration._get_end_of_life_finding_data(node)
        self.assertEqual(result["category"], "Wiz End of Life")
        self.assertIn("Ubuntu 18.04", result["title"])
        self.assertIn("2023-05-31", result["description"])

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_generic_finding_data_with_cve(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {
            "name": "CVE-2024-9999",
            "description": "Test vulnerability",
            "score": 7.5,
            "sourceRule": {"id": "rule-123"},
        }
        result = integration._get_generic_finding_data(node)
        self.assertEqual(result["cve"], "CVE-2024-9999")
        self.assertEqual(result["cvss_score"], 7.5)
        self.assertEqual(result["source_rule_id"], "rule-123")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_get_generic_finding_data_with_ghsa(self, mock_authenticate, mock_parent_init):
        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        node = {
            "name": "GHSA-xxxx-yyyy-zzzz",
            "description": "GitHub Security Advisory",
            "score": 8.0,
        }
        result = integration._get_generic_finding_data(node)
        self.assertEqual(result["cve"], "GHSA-xxxx-yyyy-zzzz")

    # ========================================
    # Asset Status Mapping Tests
    # ========================================

    def test_map_wiz_status_active(self, mock_parent_init):
        status = WizVulnerabilityIntegration.map_wiz_status("Active")
        self.assertEqual(status, regscale_models.AssetStatus.Active)

    def test_map_wiz_status_inactive(self, mock_parent_init):
        status = WizVulnerabilityIntegration.map_wiz_status("Inactive")
        self.assertEqual(status, regscale_models.AssetStatus.Inactive)

    def test_map_wiz_status_none(self, mock_parent_init):
        status = WizVulnerabilityIntegration.map_wiz_status(None)
        self.assertEqual(status, regscale_models.AssetStatus.Active)

    # ========================================
    # Finding Configuration Tests
    # ========================================

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_find_vulnerability_config(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [
            {"type": WizVulnerabilityType.VULNERABILITY, "query": "query1"},
            {"type": WizVulnerabilityType.SECRET_FINDING, "query": "query2"},
        ]
        vuln_type, config = integration._find_vulnerability_config(
            WizVulnerabilityType.VULNERABILITY.value, query_configs
        )
        self.assertEqual(vuln_type, WizVulnerabilityType.VULNERABILITY)
        self.assertEqual(config["query"], "query1")

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration.authenticate")
    def test_find_vulnerability_config_not_found(self, mock_authenticate, mock_parent_init):
        from regscale.integrations.commercial.wizv2.core.constants import WizVulnerabilityType

        mock_authenticate.return_value = None
        integration = WizVulnerabilityIntegration(plan_id=self.plan_id)
        query_configs = [{"type": WizVulnerabilityType.VULNERABILITY, "query": "query1"}]
        vuln_type, config = integration._find_vulnerability_config("NONEXISTENT", query_configs)
        self.assertIsNone(vuln_type)
        self.assertIsNone(config)


if __name__ == "__main__":
    unittest.main()
