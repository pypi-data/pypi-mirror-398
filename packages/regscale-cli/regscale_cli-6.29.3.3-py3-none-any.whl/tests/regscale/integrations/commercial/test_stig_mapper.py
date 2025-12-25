import unittest
from os.path import join
from unittest.mock import patch

from regscale.integrations.commercial.stig_mapper_integration.mapping_engine import StigMappingEngine
from regscale.models.regscale_models import Component, Asset
from tests.fixtures.test_fixture import CLITestFixture


class TestStigMappingEngine(unittest.TestCase):
    test_fixture = CLITestFixture()
    SSP_ID = 123

    def setUp(self):
        """
        Setup the test case with a mapping engine and rules.
        """
        test_file_path = join(
            self.test_fixture.get_tests_dir("tests").absolute(), "test_data/test_stig_mapper_rules.json"
        )
        self.engine = StigMappingEngine(json_file=test_file_path)
        self.engine.rules = [
            {
                "stig": "Windows 2012 Configuration STIG",
                "comparators": [
                    {
                        "comparator": "startswith",
                        "value": "Windows 2012",
                        "property": "name",
                        "logical_operator": "and",
                    },
                    {
                        "comparator": "notcontains",
                        "value": "Account Access Group",
                        "property": "name",
                        "logical_operator": "and",
                    },
                ],
            },
            {
                "stig": "Network Security STIG",
                "comparators": [
                    {"comparator": "startswith", "value": "Kubernetes", "property": "name", "logical_operator": "and"},
                    {"comparator": "endswith", "value": "Security", "property": "name", "logical_operator": "or"},
                ],
            },
        ]

    def test_find_matching_stigs_with_and_operator(self):
        asset = Asset(name="Windows 2012 Server", assetType="", status="", assetCategory="")
        comparators = [
            {"comparator": "contains", "value": "Windows 2012", "property": "name", "logical_operator": "and"},
            {"comparator": "notin", "value": "Account Access Group", "property": "name", "logical_operator": "and"},
        ]
        result = self.engine.asset_matches_comparators(asset, comparators)
        self.assertTrue(result, "Expected the asset to match 'Windows 2012' with 'and' logical operator.")

    def test_find_matching_stigs_with_or_operator(self):
        asset = Asset(name="Kubernetes Security System", assetType="", status="", assetCategory="")
        comparators = [
            {"comparator": "startswith", "value": "Kubernetes", "property": "name", "logical_operator": "and"},
            {"comparator": "endswith", "value": "Security", "property": "name", "logical_operator": "or"},
        ]
        result = self.engine.asset_matches_comparators(asset, comparators)
        self.assertTrue(result, "Expected the asset to match 'Kubernetes' with 'or' logical operator.")

    def test_find_matching_stigs_failure(self):
        asset = Asset(name="Ubuntu Server", assetType="", status="", assetCategory="")
        comparators = [{"comparator": "contains", "value": "Windows", "property": "name", "logical_operator": "and"}]
        result = self.engine.asset_matches_comparators(asset, comparators)
        self.assertFalse(result, "Expected the asset not to match 'Windows'.")

    @patch("regscale.models.regscale_models.Component.get_all_by_parent")
    @patch("regscale.models.regscale_models.ComponentMapping.get_all_by_parent")
    def test_match_asset_to_stigs(self, mock_component_mapping, mock_components):
        # Mock the components and component mappings
        mock_component_mapping.return_value = []
        mock_components.return_value = [
            Component(title="Windows 2012 Configuration STIG", description="", componentType=""),
            Component(title="Network Security STIG", description="", componentType=""),
        ]

        asset = Asset(name="Windows 2012 Server", assetType="", status="", assetCategory="")

        # Run the match_asset_to_stigs method
        result = self.engine.find_matching_stigs([asset.dict()], self.engine.rules)

        # Validate that the correct STIG is matched
        self.assertEqual(1, len(result), "Expected 1 matching STIG")
        self.assertEqual(
            result[0], "Windows 2012 Configuration STIG", "Expected to match 'Windows 2012 Configuration STIG'"
        )

    @patch("regscale.models.regscale_models.Component.get_all_by_parent")
    @patch("regscale.models.regscale_models.ComponentMapping.get_all_by_parent")
    @patch("regscale.integrations.commercial.stig_mapper.mapping_engine.StigMappingEngine.get_component_dict")
    def test_match_asset_to_stigs_no_match(self, mock_get_component_dict, mock_component_mapping, mock_components):
        # Set up the component cache directly as a side effect
        mock_get_component_dict.return_value = {
            "Windows 2012 Configuration STIG": Component(
                title="Windows 2012 Configuration STIG", description="", componentType=""
            ),
            "Network Security STIG": Component(title="Network Security STIG", description="", componentType=""),
        }

        # Mock the components and component mappings
        mock_component_mapping.return_value = []
        mock_components.return_value = [
            Component(title="Windows 2012 Configuration STIG", description="", componentType=""),
            Component(title="Network Security STIG", description="", componentType=""),
        ]

        asset = Asset(name="Ubuntu Server", assetType="", status="", assetCategory="")

        # Run the match_asset_to_stigs method
        result = self.engine.match_asset_to_stigs(asset=asset, ssp_id=self.SSP_ID)

        # Validate that no STIGs are matched
        self.assertEqual(0, len(result), "Expected no matching STIGs")

    def test_find_matching_stigs_for_software_inventory(self):
        software_inventory = [
            {"name": "Windows 2012 Server", "version": "6.3", "vendor": "Microsoft"},
            {"name": "Account Access Group Tool", "version": "1.0", "vendor": "Generic"},
            {"name": "Kubernetes Security System", "version": "1.20", "vendor": "OpenSource"},
        ]

        comparators = [
            {"comparator": "startswith", "value": "Windows 2012", "property": "name", "logical_operator": "and"},
            {"comparator": "contains", "value": "Account Access Group", "property": "name", "logical_operator": "and"},
        ]

        result = self.engine.find_matching_stigs(
            software_inventory, [{"stig": "Test STIG", "comparators": comparators}]
        )
        self.assertGreater(
            len(result), 0, "Expected at least one software inventory item to match the 'Windows 2012' criteria."
        )

    def test_find_matching_stigs_for_software_inventory_no_match(self):
        software_inventory = [
            {"name": "Ubuntu Server", "version": "20.04", "vendor": "Canonical"},
            {"name": "Account Access Group Tool", "version": "1.0", "vendor": "Generic"},
        ]

        comparators = [
            {"comparator": "startswith", "value": "Windows", "property": "name", "logical_operator": "and"},
        ]

        result = self.engine.find_matching_stigs(
            software_inventory, [{"stig": "Test STIG", "comparators": comparators}]
        )
        self.assertEqual(len(result), 0, "Expected no software inventory items to match the 'Windows' criteria.")
