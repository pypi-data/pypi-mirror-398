"""
Unit tests for WizSbomIntegration
"""

import json
import logging
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open

from regscale.integrations.commercial.wizv2.sbom import WizSbomIntegration
from regscale.models.regscale_models.sbom import Sbom

logger = logging.getLogger("regscale")

PATH = "regscale.integrations.commercial.wizv2.sbom"


class TestWizSbomIntegration(unittest.TestCase):
    """Test cases for WizSbomIntegration class"""

    def setUp(self):
        """Set up test fixtures"""
        self.wiz_project_id = "test-project-123"
        self.regscale_id = 100
        self.regscale_module = "securityPlans"
        self.client_id = "test-client-id"
        self.client_secret = "test-client-secret"
        self.filter_by_override = None

        # Sample SBOM data from Wiz
        self.sample_sbom_nodes = [
            {
                "id": "sbom-1",
                "name": "express",
                "type": {
                    "group": "npm",
                    "codeLibraryLanguage": "JavaScript",
                    "osPackageManager": None,
                    "hostedTechnology": None,
                    "plugin": None,
                },
                "versions": {
                    "nodes": [
                        {"version": "4.18.0"},
                        {"version": "4.18.1"},
                        {"version": "4.18.2"},
                    ]
                },
            },
            {
                "id": "sbom-2",
                "name": "lodash",
                "type": {
                    "group": "npm",
                    "codeLibraryLanguage": "JavaScript",
                    "osPackageManager": None,
                    "hostedTechnology": None,
                    "plugin": None,
                },
                "versions": {
                    "nodes": [
                        {"version": "4.17.21"},
                    ]
                },
            },
            {
                "id": "sbom-3",
                "name": "pytest",
                "type": {
                    "group": "pip",
                    "codeLibraryLanguage": "Python",
                    "osPackageManager": None,
                    "hostedTechnology": None,
                    "plugin": None,
                },
                "versions": {"nodes": []},
            },
        ]

    @patch(f"{PATH}.WizMixin.__init__")
    def test_init_with_project_id_from_parameter(self, mock_wiz_mixin_init):
        """Test initialization with project ID passed as parameter"""
        mock_wiz_mixin_init.return_value = None

        # Mock the config attribute on the instance
        mock_config = {"wizProjectId": "config-project-id"}

        integration = WizSbomIntegration(
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        integration.config = mock_config

        self.assertEqual(integration.wiz_project_id, self.wiz_project_id)
        self.assertEqual(integration.regscale_id, self.regscale_id)
        self.assertEqual(integration.regscale_module, self.regscale_module)
        self.assertEqual(integration.filter_by, None)
        self.assertEqual(integration.topic_key, "sbomArtifactsGroupedByName")
        self.assertIsInstance(integration.sbom_list, list)
        self.assertEqual(len(integration.sbom_list), 0)

    @patch(f"{PATH}.WizMixin.__init__")
    def test_init_with_project_id_from_config(self, mock_wiz_mixin_init):
        """Test initialization with project ID from config when parameter is None"""
        mock_wiz_mixin_init.return_value = None

        # Create the instance first and manually set config before checking wiz_project_id
        integration = WizSbomIntegration.__new__(WizSbomIntegration)
        integration.config = {"wizProjectId": "config-project-id"}

        # Now call __init__ with None for wiz_project_id
        WizSbomIntegration.__init__(
            integration,
            wiz_project_id=None,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        # Should pick up project ID from config
        self.assertEqual(integration.wiz_project_id, "config-project-id")

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_init_without_project_id_exits(self, mock_wiz_mixin_init, mock_error_exit):
        """Test initialization without project ID calls error_and_exit"""
        mock_wiz_mixin_init.return_value = None
        mock_error_exit.side_effect = SystemExit(1)

        # Create an instance and manually set config to empty dict
        with self.assertRaises(SystemExit):
            integration = WizSbomIntegration.__new__(WizSbomIntegration)
            integration.config = {}
            # Call __init__ manually to trigger the error check
            WizSbomIntegration.__init__(
                integration,
                wiz_project_id=None,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

        mock_error_exit.assert_called_once_with("Wiz project ID not provided")

    @patch(f"{PATH}.WizMixin.__init__")
    def test_init_with_filter_by_override(self, mock_wiz_mixin_init):
        """Test initialization with filterBy override"""
        mock_wiz_mixin_init.return_value = None
        filter_by_json = '{"project": "override-project", "custom": "filter"}'

        # Create the instance first and manually set config
        integration = WizSbomIntegration.__new__(WizSbomIntegration)
        integration.config = {"wizProjectId": self.wiz_project_id}

        # Now call __init__ with filter_by_override
        WizSbomIntegration.__init__(
            integration,
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=filter_by_json,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        expected_filter = {"project": "override-project", "custom": "filter"}
        self.assertEqual(integration.filter_by, expected_filter)
        # Verify variables use the override filter
        self.assertEqual(integration.variables["filterBy"], expected_filter)

    @patch(f"{PATH}.Sbom.get_all_by_parent")
    @patch(f"{PATH}.WizSbomIntegration.fetch_sbom_data")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_run_with_no_sbom_data(self, mock_wiz_mixin_init, mock_fetch_sbom, mock_get_all):
        """Test run method when no SBOM data is found"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Mock fetch_sbom_data to set empty list
            def set_empty_list():
                integration.sbom_list = []

            mock_fetch_sbom.side_effect = set_empty_list

            with self.assertRaises(SystemExit) as cm:
                integration.run()

            self.assertEqual(cm.exception.code, 0)
            mock_fetch_sbom.assert_called_once()
            mock_get_all.assert_not_called()

    @patch(f"{PATH}.Sbom.get_all_by_parent")
    @patch(f"{PATH}.WizSbomIntegration.fetch_sbom_data")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_run_creates_new_sboms(self, mock_wiz_mixin_init, mock_fetch_sbom, mock_get_all):
        """Test run method creates new SBOMs when they don't exist"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Create mock SBOM objects
            mock_sbom1 = MagicMock(spec=Sbom)
            mock_sbom1.name = "express"
            mock_sbom1.create = MagicMock()

            mock_sbom2 = MagicMock(spec=Sbom)
            mock_sbom2.name = "lodash"
            mock_sbom2.create = MagicMock()

            # Mock fetch_sbom_data to populate sbom_list
            def populate_sbom_list():
                integration.sbom_list = [mock_sbom1, mock_sbom2]

            mock_fetch_sbom.side_effect = populate_sbom_list

            # Mock get_all_by_parent to return empty list (no existing SBOMs)
            mock_get_all.return_value = []

            integration.run()

            mock_fetch_sbom.assert_called_once()
            mock_get_all.assert_called_once_with(parent_id=self.regscale_id, parent_module=self.regscale_module)
            mock_sbom1.create.assert_called_once()
            mock_sbom2.create.assert_called_once()

    @patch(f"{PATH}.Sbom.get_all_by_parent")
    @patch(f"{PATH}.WizSbomIntegration.fetch_sbom_data")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_run_skips_existing_sboms(self, mock_wiz_mixin_init, mock_fetch_sbom, mock_get_all):
        """Test run method skips SBOMs that already exist"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Create mock SBOM objects
            mock_sbom1 = MagicMock(spec=Sbom)
            mock_sbom1.name = "express"
            mock_sbom1.create = MagicMock()

            mock_sbom2 = MagicMock(spec=Sbom)
            mock_sbom2.name = "lodash"
            mock_sbom2.create = MagicMock()

            # Mock fetch_sbom_data to populate sbom_list
            def populate_sbom_list():
                integration.sbom_list = [mock_sbom1, mock_sbom2]

            mock_fetch_sbom.side_effect = populate_sbom_list

            # Mock existing SBOM with name "express"
            existing_sbom = MagicMock(spec=Sbom)
            existing_sbom.name = "express"
            mock_get_all.return_value = [existing_sbom]

            integration.run()

            mock_fetch_sbom.assert_called_once()
            mock_get_all.assert_called_once_with(parent_id=self.regscale_id, parent_module=self.regscale_module)
            # express should not be created (already exists)
            mock_sbom1.create.assert_not_called()
            # lodash should be created (doesn't exist)
            mock_sbom2.create.assert_called_once()

    @patch(f"{PATH}.WizSbomIntegration.map_sbom_data")
    @patch(f"{PATH}.WizSbomIntegration.fetch_data_if_needed")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_fetch_sbom_data(self, mock_wiz_mixin_init, mock_fetch_data, mock_map_sbom):
        """Test fetch_sbom_data method"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(
            WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id, "wizFullPullLimitHours": 8}
        ):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            mock_fetch_data.return_value = self.sample_sbom_nodes

            integration.fetch_sbom_data()

            # Verify fetch_data_if_needed was called with correct parameters
            from regscale.integrations.commercial.wizv2.core.constants import SBOM_QUERY, SBOM_FILE_PATH

            mock_fetch_data.assert_called_once_with(
                file_path=SBOM_FILE_PATH,
                query=SBOM_QUERY,
                topic_key="sbomArtifactsGroupedByName",
                interval_hours=8,
                variables={
                    "first": 200,
                    "filterBy": {"project": self.wiz_project_id},
                    "orderBy": {"field": "NAME", "direction": "ASC"},
                },
            )

            # Verify map_sbom_data was called with the nodes
            mock_map_sbom.assert_called_once_with(self.sample_sbom_nodes)

    @patch(f"{PATH}.WizSbomIntegration.map_sbom_data")
    @patch(f"{PATH}.WizSbomIntegration.fetch_data_if_needed")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_fetch_sbom_data_with_custom_interval(self, mock_wiz_mixin_init, mock_fetch_data, mock_map_sbom):
        """Test fetch_sbom_data with custom interval hours from config"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(
            WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id, "wizFullPullLimitHours": 12}
        ):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            mock_fetch_data.return_value = self.sample_sbom_nodes

            integration.fetch_sbom_data()

            # Verify interval_hours was set to custom value
            call_kwargs = mock_fetch_data.call_args[1]
            self.assertEqual(call_kwargs["interval_hours"], 12)

    @patch("regscale.models.regscale_models.sbom.RegScaleModel.get_user_id")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data(self, mock_wiz_mixin_init, mock_get_user_id):
        """Test map_sbom_data method with valid data"""
        mock_wiz_mixin_init.return_value = None
        mock_get_user_id.return_value = "test-user-id"

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            integration.map_sbom_data(self.sample_sbom_nodes)

            # Verify SBOM objects were created
            self.assertEqual(len(integration.sbom_list), 3)

            # Check first SBOM
            sbom1 = integration.sbom_list[0]
            self.assertEqual(sbom1.name, "express")
            self.assertEqual(sbom1.sbomStandard, "JavaScript")
            self.assertEqual(sbom1.standardVersion, "4.18.0,4.18.1,4.18.2")
            self.assertEqual(sbom1.tool, "npm")
            self.assertEqual(sbom1.parentId, self.regscale_id)
            self.assertEqual(sbom1.parentModule, self.regscale_module)
            self.assertIsNotNone(sbom1.results)
            self.assertIsInstance(json.loads(sbom1.results), dict)

            # Check second SBOM
            sbom2 = integration.sbom_list[1]
            self.assertEqual(sbom2.name, "lodash")
            self.assertEqual(sbom2.sbomStandard, "JavaScript")
            self.assertEqual(sbom2.standardVersion, "4.17.21")
            self.assertEqual(sbom2.tool, "npm")

            # Check third SBOM (with no versions)
            sbom3 = integration.sbom_list[2]
            self.assertEqual(sbom3.name, "pytest")
            self.assertEqual(sbom3.sbomStandard, "Python")
            self.assertEqual(sbom3.standardVersion, "")
            self.assertEqual(sbom3.tool, "pip")

    @patch("regscale.models.regscale_models.sbom.RegScaleModel.get_user_id")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data_with_missing_type_fields(self, mock_wiz_mixin_init, mock_get_user_id):
        """Test map_sbom_data with missing type fields falls back to name"""
        mock_wiz_mixin_init.return_value = None
        mock_get_user_id.return_value = "test-user-id"

        integration = WizSbomIntegration(
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        integration.config = {"wizProjectId": self.wiz_project_id}
        # Clear any existing SBOM data
        integration.sbom_list = []

        # SBOM data with missing type fields
        nodes_with_missing_fields = [
            {
                "id": "sbom-4",
                "name": "unknown-package",
                "type": {
                    "group": None,
                    "codeLibraryLanguage": None,
                    "osPackageManager": None,
                    "hostedTechnology": None,
                    "plugin": None,
                },
                "versions": {"nodes": [{"version": "1.0.0"}]},
            }
        ]

        integration.map_sbom_data(nodes_with_missing_fields)

        self.assertEqual(len(integration.sbom_list), 1)
        sbom = integration.sbom_list[0]
        # When codeLibraryLanguage is None, it should fall back to name
        self.assertEqual(sbom.sbomStandard, "unknown-package")
        self.assertEqual(sbom.tool, None)

    @patch("regscale.models.regscale_models.sbom.RegScaleModel.get_user_id")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data_with_empty_versions(self, mock_wiz_mixin_init, mock_get_user_id):
        """Test map_sbom_data handles empty versions gracefully"""
        mock_wiz_mixin_init.return_value = None
        mock_get_user_id.return_value = "test-user-id"

        integration = WizSbomIntegration(
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        integration.config = {"wizProjectId": self.wiz_project_id}
        # Clear any existing SBOM data
        integration.sbom_list = []

        nodes_with_no_versions = [
            {
                "id": "sbom-5",
                "name": "no-version-package",
                "type": {
                    "group": "maven",
                    "codeLibraryLanguage": "Java",
                    "osPackageManager": None,
                    "hostedTechnology": None,
                    "plugin": None,
                },
                "versions": {"nodes": []},
            }
        ]

        integration.map_sbom_data(nodes_with_no_versions)

        self.assertEqual(len(integration.sbom_list), 1)
        sbom = integration.sbom_list[0]
        self.assertEqual(sbom.standardVersion, "")

    @patch("regscale.models.regscale_models.sbom.RegScaleModel.get_user_id")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data_preserves_json_structure(self, mock_wiz_mixin_init, mock_get_user_id):
        """Test that map_sbom_data preserves the original JSON in results field"""
        mock_wiz_mixin_init.return_value = None
        mock_get_user_id.return_value = "test-user-id"

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            integration.map_sbom_data(self.sample_sbom_nodes)

            # Verify the results field contains valid JSON
            sbom = integration.sbom_list[0]
            results_data = json.loads(sbom.results)

            self.assertEqual(results_data["id"], "sbom-1")
            self.assertEqual(results_data["name"], "express")
            self.assertIn("type", results_data)
            self.assertIn("versions", results_data)

    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data_with_none_values(self, mock_wiz_mixin_init):
        """Test map_sbom_data with None values raises TypeError due to get_value returning None"""
        mock_wiz_mixin_init.return_value = None

        integration = WizSbomIntegration(
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=None,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        integration.config = {"wizProjectId": self.wiz_project_id}
        # Clear any existing SBOM data
        integration.sbom_list = []

        nodes_with_nones = [
            {
                "id": "sbom-6",
                "name": "test-package",
                "type": None,
                "versions": None,
            }
        ]

        # This should raise a TypeError since get_value returns None for versions.nodes
        # and we try to iterate over it
        with self.assertRaises(TypeError) as context:
            integration.map_sbom_data(nodes_with_nones)

        self.assertIn("'NoneType' object is not iterable", str(context.exception))

    @patch(f"{PATH}.WizMixin.__init__")
    def test_variables_structure(self, mock_wiz_mixin_init):
        """Test that variables are correctly structured for GraphQL query"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            expected_variables = {
                "first": 200,
                "filterBy": {"project": self.wiz_project_id},
                "orderBy": {"field": "NAME", "direction": "ASC"},
            }

            self.assertEqual(integration.variables, expected_variables)

    @patch(f"{PATH}.WizMixin.__init__")
    def test_filter_by_override_logging(self, mock_wiz_mixin_init):
        """Test that filterBy override is applied correctly"""
        mock_wiz_mixin_init.return_value = None
        filter_by_json = '{"custom": "filter"}'

        # Create the instance first and manually set config
        integration = WizSbomIntegration.__new__(WizSbomIntegration)
        integration.config = {"wizProjectId": self.wiz_project_id}

        # Now call __init__ with filter_by_override
        WizSbomIntegration.__init__(
            integration,
            wiz_project_id=self.wiz_project_id,
            regscale_id=self.regscale_id,
            regscale_module=self.regscale_module,
            filter_by_override=filter_by_json,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        # Verify that filter_by was set correctly
        expected_filter = {"custom": "filter"}
        self.assertEqual(integration.filter_by, expected_filter)
        self.assertEqual(integration.variables["filterBy"], expected_filter)

    @patch(f"{PATH}.Sbom")
    @patch(f"{PATH}.WizMixin.__init__")
    def test_map_sbom_data_creates_sbom_instances(self, mock_wiz_mixin_init, mock_sbom_class):
        """Test that map_sbom_data creates Sbom model instances with correct parameters"""
        mock_wiz_mixin_init.return_value = None

        with patch.object(WizSbomIntegration, "config", {"wizProjectId": self.wiz_project_id}):
            integration = WizSbomIntegration(
                wiz_project_id=self.wiz_project_id,
                regscale_id=self.regscale_id,
                regscale_module=self.regscale_module,
                filter_by_override=None,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )

            # Create a simple mock for Sbom that returns itself
            mock_sbom_instance = MagicMock(spec=Sbom)
            mock_sbom_class.return_value = mock_sbom_instance

            single_node = [self.sample_sbom_nodes[0]]
            integration.map_sbom_data(single_node)

            # Verify Sbom was instantiated with correct parameters
            mock_sbom_class.assert_called_once()
            call_kwargs = mock_sbom_class.call_args[1]

            self.assertEqual(call_kwargs["name"], "express")
            self.assertEqual(call_kwargs["sbomStandard"], "JavaScript")
            self.assertEqual(call_kwargs["standardVersion"], "4.18.0,4.18.1,4.18.2")
            self.assertEqual(call_kwargs["tool"], "npm")
            self.assertEqual(call_kwargs["parentId"], self.regscale_id)
            self.assertEqual(call_kwargs["parentModule"], self.regscale_module)
            self.assertIsNotNone(call_kwargs["results"])


if __name__ == "__main__":
    unittest.main()
